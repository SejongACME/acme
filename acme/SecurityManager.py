#
#	SecurityManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	This entity handles access to resources
#


from Logging import Logging
from Constants import Constants as C
from Types import ResourceTypes as T, Permission, Operation
import CSE, Utils
from Configuration import Configuration
from resources.Resource import Resource


class SecurityManager(object):

	def __init__(self) -> None:
		self.enableACPChecks 		= Configuration.get('cse.security.enableACPChecks')
		self.csebaseAccessACPI		= Configuration.get('cse.security.csebaseAccessACPI')

		Logging.log('SecurityManager initialized')
		if self.enableACPChecks:
			Logging.log('ACP checking ENABLED')
		else:
			Logging.log('ACP checking DISABLED')


	def shutdown(self) -> bool:
		Logging.log('SecurityManager shut down')
		return True


	def hasAccess(self, originator:str, resource:Resource, requestedPermission:Permission, checkSelf:bool=False, ty:int=None, isCreateRequest:bool=False, parentResource:Resource=None) -> bool:
		if not self.enableACPChecks:	# check or ignore the check
			return True
		

		if ty is not None:

			# Checking for AE	
			if ty == T.AE and isCreateRequest:
				# originator may be None or empty or C or S. 
				# That is okay if type is AE and this is a create request
				if originator is None or len(originator) == 0 or Utils.isAllowedOriginator(originator, CSE.registration.allowedAEOriginators):
					Logging.logDebug('Originator for AE CREATE. OK.')
					return True

			# Checking for remoteCSE
			if ty == T.CSR and isCreateRequest:
				if Utils.isAllowedOriginator(originator, CSE.registration.allowedCSROriginators):
					Logging.logDebug('Originator for CSR CREATE. OK.')
					return True
				else:
					Logging.logWarn('Originator for CSR CREATE not found.')
					return False

			if T(ty).isAnnounced():
				if Utils.isAllowedOriginator(originator, CSE.registration.allowedCSROriginators) or originator[1:] == parentResource.ri:
					Logging.logDebug('Originator for Announcement. OK.')
					return True
				else:
					Logging.logWarn('Originator for Announcement not found.')
					return False

		# Check parameters
		if resource is None:
			Logging.logWarn('Resource must not be None')
			return False
		if requestedPermission is None or not (0 <= requestedPermission <= Permission.ALL):
			Logging.logWarn('RequestedPermission must not be None, and between 0 and 63')
			return False

		Logging.logDebug(f'Checking permission for originator: {originator}, ri: {resource.ri}, permission: {requestedPermission:d}, selfPrivileges: {checkSelf}')


		if resource.ty == T.GRP: # target is a group resource
			# Check membersAccessControlPolicyIDs if provided, otherwise accessControlPolicyIDs to be used
			
			if (macp := resource.macp) is None or len(macp) == 0:
				Logging.logDebug("MembersAccessControlPolicyIDs not provided, using AccessControlPolicyIDs")
				# FALLTHROUGH to the permission checks below
			
			else: # handle the permission checks here
				for a in macp:
					if (acp := CSE.dispatcher.retrieveResource(a).resource) is None:
						Logging.logDebug(f'ACP resource not found: {a}')
						continue
					else:
						if acp.checkPermission(originator, requestedPermission):
							Logging.logDebug('Permission granted')
							return True
				Logging.logDebug('Permission NOT granted')
				return False


		if resource.ty in [T.ACP, T.ACPAnnc]:	# target is an ACP or ACPAnnc resource
			if resource.checkSelfPermission(originator, requestedPermission):
				Logging.logDebug('Permission granted')
				return True
			# fall-through

		else:		# target is any other resource type
			
			# If subscription, check whether originator has retrieve permissions on the subscribed-to resource (parent)	
			if ty == T.SUB and parentResource is not None:
				if self.hasAccess(originator, parentResource, Permission.RETRIEVE) == False:
					return False


			# When no acpi is configured for the resource
			if (acpi := resource.acpi) is None or len(acpi) == 0:
				Logging.logDebug('Handle with missing acpi in resource')
				Logging.logWarn(str(resource))

				# if the resource *may* have an acpi
				if 'acpi' in resource.attributePolicies:
					# Check holder attribute
					if (holder := resource.hld) is not None:
						if holder == originator:	# resource.holder == originator -> all access
							Logging.logDebug('Allow access for holder')
							return True
						# When holder is set, but doesn't match the originator then fall-through to fail
						
					# Check resource creator
					elif (creator := resource[resource._originator]) is not None and creator == originator:
						Logging.logDebug('Allow access for creator')
						return True
					
					# Fall-through to fail

				# resource doesn't support acpi attribute
				else:
					if resource.inheritACP:
						Logging.logDebug('Checking parent\'s permission')
						parentResource = CSE.dispatcher.retrieveResource(resource.pi).resource
						return self.hasAccess(originator, parentResource, requestedPermission, checkSelf, ty, isCreateRequest)

				Logging.logDebug('Permission NOT granted for resource w/o acpi')
				return False

			for a in acpi:
				if (acp := CSE.dispatcher.retrieveResource(a).resource) is None:
					Logging.logDebug(f'ACP resource not found: {a}')
					continue
				if checkSelf:	# forced check for self permissions
					if acp.checkSelfPermission(originator, requestedPermission):
						Logging.logDebug('Permission granted')
						return True				
				else:
					if acp.checkPermission(originator, requestedPermission):
						Logging.logDebug('Permission granted')
						return True

		# no fitting permission identified
		Logging.logDebug('Permission NOT granted')
		return False

