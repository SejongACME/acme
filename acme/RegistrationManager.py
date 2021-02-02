#
#	RegistrationManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Managing resources and AE, CSE registrations
#

from copy import deepcopy
from Logging import Logging
from typing import List
from Constants import Constants as C
from Configuration import Configuration
from Types import ResourceTypes as T, Result, Permission, ResponseCode as RC
from resources.Resource import Resource
import CSE, Utils
from resources import ACP
from helpers.BackgroundWorker import BackgroundWorkerPool



class RegistrationManager(object):

	def __init__(self) -> None:
		self.allowedCSROriginators 	= Configuration.get('cse.registration.allowedCSROriginators')
		self.allowedAEOriginators	= Configuration.get('cse.registration.allowedAEOriginators')

		self.startExpirationWorker()
		Logging.log('RegistrationManager initialized')


	def shutdown(self) -> bool:
		self.stopExpirationWorker()
		Logging.log('RegistrationManager shut down')
		return True


	#########################################################################

	#
	#	Handle new resources in general
	#

	def checkResourceCreation(self, resource:Resource, originator:str, parentResource:Resource=None) -> Result:
		if resource.ty == T.AE:
			if (originator := self.handleAERegistration(resource, originator, parentResource).originator) is None:	# assigns new originator
				return Result(rsc=RC.badRequest, dbg='cannot register AE')
		if resource.ty == T.REQ:
			if not self.handleREQRegistration(resource, originator):
				return Result(rsc=RC.badRequest, dbg='cannot register REQ')
		if resource.ty == T.CSR:
			if CSE.cseType == 'ASN':
				return Result(rsc=RC.operationNotAllowed, dbg='cannot register to ASN CSE')
			if not self.handleCSRRegistration(resource, originator):
				return Result(rsc=RC.badRequest, dbg='cannot register CSR')

		# Test and set creator attribute.
		
		if (res := self.handleCreator(resource, originator)).rsc != RC.OK:
			return res

		# ACPI assignments 

		if T(resource.ty).isAnnounced():	# For announced resourcess
			if (acpi := resource.acpi) is None:
				acpi = []
			acpi = parentResource.acpi + acpi # local acpi at the beginning
			# acpi.extend(parentResource.acpi)
			resource['acpi'] = acpi

		elif resource.ty != T.AE:	# Don't handle AE's, this was already done already in the AE registration
			if resource.inheritACP:
				del resource['acpi']	# This should not happen bc resource rejected during validaten. But better remove acpi here

		return Result(originator=originator) # return (possibly new) originator


	# Check for (wrongly) set creator attribute as well as assign it to allowed resources.
	def handleCreator(self, resource:Resource, originator:str) -> Result:
		# Check whether cr is set. This is wrong
		if resource.cr is not None:
			Logging.logWarn('Setting "creator" attribute is not allowed.')
			return Result(rsc=RC.badRequest, dbg='setting "creator" attribute is not allowed')
		# Set cr for some of the resource types
		if resource.ty in C.creatorAllowed:
			resource['cr'] = CSE.cseOriginator if originator in ['C', 'S', '', None ] else originator
		return Result() # implicit OK


	def checkResourceUpdate(self, resource:Resource, updateDict:dict) -> Result:
		if resource.ty == T.CSR:
			if not self.handleCSRUpdate(resource, updateDict):
				return Result(status=False, dbg='cannot update CSR')
		return Result(status=True)


	def checkResourceDeletion(self, resource:Resource) -> Result:
		if resource.ty == T.AE:
			if not self.handleAEDeRegistration(resource):
				return Result(status=False, dbg='cannot deregister AE')
		if resource.ty == T.REQ:
			if not self.handleREQDeRegistration(resource):
				return Result(status=False, dbg='cannot deregister REQ')
		if resource.ty == T.CSR:
			if not self.handleCSRDeRegistration(resource):
				return Result(status=False, dbg='cannot deregister CSR')
		return Result(status=True)



	#########################################################################

	#
	#	Handle AE registration
	#

	def handleAERegistration(self, ae:Resource, originator:str, parentResource:Resource) -> Result:
		""" This method creates a new originator for the AE registration, depending on the method choosen."""

		# check for empty originator and assign something
		if originator is None or len(originator) == 0:
			originator = 'C'

		# Check for allowed orginator
		# TODO also allow when there is an ACP?
		if not Utils.isAllowedOriginator(originator, self.allowedAEOriginators):
			Logging.logDebug('Originator not allowed')
			return Result(rsc=RC.appRuleValidationFailed)

		# Assign originator for the AE
		if originator == 'C':
			originator = Utils.uniqueAEI('C')
		elif originator == 'S':
			originator = Utils.uniqueAEI('S')
		elif originator is not None:
			originator = Utils.getIdFromOriginator(originator)
		# elif originator is None or len(originator) == 0:
		# 	originator = Utils.uniqueAEI('S')
		Logging.logDebug(f'Registering AE. aei: {originator}')

		ae['aei'] = originator					# set the aei to the originator
		ae['ri'] = Utils.getIdFromOriginator(originator, idOnly=True)		# set the ri of the ae to the aei (TS-0001, 10.2.2.2)

		# Verify that parent is the CSEBase, else this is an error
		if parentResource is None or parentResource.ty != T.CSEBase:
			return Result(rsc=RC.notAcceptable)

		# Create an ACP for this AE-ID if there is none set
		# if ae.acpi is None or len(ae.acpi) == 0:
		Logging.logDebug('Adding ACP for AE')

		# Add ACP for remote CSE to access the own CSE

		# Automatically add the originator and the cseOriginator if the acpi is empty, else (if there is an ACP) only add the cseOriginator
		# and don't give the originator extra access rights
		acpOriginators = [ originator, CSE.cseOriginator ] if ae.acpi is None or len(ae.acpi) == 0 else [ CSE.cseOriginator ]
		acpResource = self._createACP(parentResource=parentResource,
								  rn=C.acpPrefix + ae.rn,
								  createdByResource=ae.ri, 
								  # originators=[ originator, CSE.cseOriginator ],
								  originators=acpOriginators,
								  permission=Configuration.get('cse.acp.pv.acop')).resource
		if acpResource is None:
			return Result(rsc=RC.notAcceptable)
		if ae.acpi is None or len(ae.acpi) == 0:
			ae['acpi'] = [ acpResource.ri ]		# Set ACPI (anew)
		else:
			ae.acpi.append(acpResource.ri)		# append to existing

		# Add the AE to the accessCSEBase ACP so that it can at least retrieve the CSEBase
		self._addToAccessCSBaseACP(ae.aei)

		return Result(originator=originator)


	#
	#	Handle AE deregistration
	#

	def handleAEDeRegistration(self, resource: Resource) -> bool:
		# remove the before created ACP, if it exist
		Logging.logDebug(f'DeRegisterung AE. aei: {resource.aei}')
		Logging.logDebug('Removing ACP for AE')

		acpSrn = f'{CSE.cseRn}/{C.acpPrefix}{resource.rn}'
		self._removeACP(srn=acpSrn, resource=resource)

		# Remove from accessCSEBaseACP
		self._removeFromAccessCSEBaseACP(resource.aei)

		return True



	#########################################################################

	#
	#	Handle CSR registration
	#

	def handleCSRRegistration(self, csr:Resource, originator:str) -> bool:
		Logging.logDebug(f'Registering CSR. csi: {csr.csi}')

		# Create an ACP for this CSR if there is none set
		Logging.logDebug('Adding ACP for CSR')
		localCSE = Utils.getCSE().resource

		# Add ACP for remote CSE to access the own CSE
		if csr.acpi is None or len(csr.acpi) == 0:
			acpResource = self._createACP(parentResource=localCSE,
								  rn=f'{C.acpPrefix}{csr.rn}',
							 	  createdByResource=csr.ri,
								  originators=[ originator, CSE.cseOriginator ],
								  permission=Permission.ALL,
								  selfOriginators=[csr.csi]).resource
			if acpResource is None:
				return False
			csr['acpi'] = [ f'{CSE.cseCsi}/{acpResource.ri}' ]	# Set ACPI (anew)

		# Allow remote CSE to access the CSE, at least to read
		self._addToAccessCSBaseACP(originator)

		# send event
		CSE.event.remoteCSEHasRegistered(csr)	# type: ignore

		return True


	#
	#	Handle CSR deregistration
	#

	def handleCSRDeRegistration(self, csr:Resource) ->  bool:
		Logging.logDebug(f'DeRegistering CSR. csi: {csr.csi}')

		# remove the before created ACP, if it exist
		Logging.logDebug('Removing ACPs for CSR')
		localCSE = Utils.getCSE().resource

		# Retrieve CSR ACP
		# This might fail (which is okay!), because the ACP was not created during
		# the registration of the CSR (identified by the rn that includes the 
		# name of the CSR)
		acpi = f'{localCSE.rn}/{C.acpPrefix}{csr.rn}'
		self._removeACP(srn=acpi, resource=csr)

		# Remove from accessCSEBaseACP
		self._removeFromAccessCSEBaseACP(csr.csi)

		if (res := CSE.dispatcher.updateResource(localCSE, doUpdateCheck=False).resource is not None): # res is bool
			# send event
			CSE.event.remoteCSEHasDeregistered(csr)	# type: ignore
		return res


	#
	#	Handle CSR Update
	#

	def handleCSRUpdate(self, csr:Resource, updateDict:dict) -> bool:
		Logging.logDebug(f'Updating CSR. csi: {csr.csi}')
		# send event
		CSE.event.remoteCSEUpdate(csr, updateDict)	# type: ignore
		return True



	#########################################################################

	#
	#	Handle REQ registration
	#

	def handleREQRegistration(self, req:Resource, originator:str) -> bool:
		Logging.logDebug(f'Registering REQ: {req.ri}')

		# Create an REQ specific ACP
		Logging.logDebug('Adding ACP for REQ')
		localCSE = Utils.getCSE().resource
		acp = self._createACP(parentResource=localCSE,
							  rn=f'{C.acpPrefix}{req.rn}',
						 	  createdByResource=req.ri,
							  originators=[ originator ],
							  permission=Permission.RETRIEVE + Permission.UPDATE + Permission.DELETE,
							  selfOriginators=[ CSE.cseOriginator ]
						  ).resource
		if acp is None:
			return False

		# add additional permissions for the originator
		acp.addPermission([ CSE.cseOriginator ], Permission.ALL)
		acp.addSelfPermission([ originator ], Permission.UPDATE)
		acp.dbUpdate()


		# add acpi to request resource
		req['acpi'] =  [ acp.ri ]	

		return True


	#
	#	Handle REQ deregistration
	#

	def handleREQDeRegistration(self, resource: Resource) -> bool:
		# remove the before created ACP, if it exist
		Logging.logDebug(f'DeRegisterung REQ. ri: {resource.ri}')
		Logging.logDebug('Removing ACP for REQ')

		acpSrn = f'{CSE.cseRn}/{C.acpPrefix}{resource.rn}'
		self._removeACP(srn=acpSrn, resource=resource)

		return True


	#########################################################################
	##
	##	Resource Expiration
	##

	def startExpirationWorker(self) -> None:
		# Start background worker to handle expired resources
		Logging.log('Starting expiration worker')
		if (interval := Configuration.get('cse.checkExpirationsInterval')) > 0:
			BackgroundWorkerPool.newWorker(interval, self.expirationDBWorker, 'expirationWorker', startWithDelay=True).start()


	def stopExpirationWorker(self) -> None:
		# Stop the expiration worker
		Logging.log('Stopping expiration worker')
		BackgroundWorkerPool.stopWorkers('expirationWorker')


	def expirationDBWorker(self) -> bool:
		Logging.logDebug('Looking for expired resources')
		now = Utils.getResourceDate()
		resources = CSE.storage.searchByFilter(lambda r: 'et' in r and (et := r['et']) is not None and et < now)
		for resource in resources:
			# try to retrieve the resource first bc it might have been deleted as a child resource
			# of an expired resource
			if not CSE.storage.hasResource(ri=resource.ri):
				continue
			Logging.logDebug(f'Expiring resource (and child resouces): {resource.ri}')
			CSE.dispatcher.deleteResource(resource, withDeregistration=True)	# ignore result
			CSE.event.expireResource(resource) # type: ignore
				
		return True




	#########################################################################


	def _createACP(self, parentResource:Resource=None, rn:str=None, createdByResource:str=None, originators:List[str]=None, permission:int=None, selfOriginators:List[str]=None, selfPermission:int=None) -> Result:
		""" Create an ACP with some given defaults. """
		if parentResource is None or rn is None or originators is None or permission is None:
			return Result(rsc=RC.badRequest, dbg='missing attribute(s)')

		# Remove existing ACP with that name first
		acpSrn = f'{CSE.cseRn}/{rn}'
		if (acpRes := CSE.dispatcher.retrieveResource(id=acpSrn)).rsc == RC.OK:
			CSE.dispatcher.deleteResource(acpRes.resource)	# ignore errors

		# Create the ACP
		selfPermission = selfPermission if selfPermission is not None else Configuration.get('cse.acp.pvs.acop')

		origs = deepcopy(originators)
		origs.append(CSE.cseOriginator)	# always append cse originator

		selfOrigs = [ CSE.cseOriginator ]
		if selfOriginators is not None:
			selfOrigs.extend(selfOriginators)


		acp = ACP.ACP(pi=parentResource.ri, rn=rn, createdInternally=createdByResource)
		acp.addPermission(origs, permission)
		acp.addSelfPermission(selfOrigs, selfPermission)

		if (res := self.checkResourceCreation(acp, CSE.cseOriginator, parentResource)).rsc != RC.OK:
			return res.errorResult()
		return CSE.dispatcher.createResource(acp, parentResource=parentResource, originator=CSE.cseOriginator)


	def _removeACP(self, srn:str, resource:Resource) -> Result:
		""" Remove an ACP created during registration before. """
		if (acpRes := CSE.dispatcher.retrieveResource(id=srn)).rsc != RC.OK:
			Logging.logWarn(f'Could not find ACP: {srn}')	# ACP not found, either not created or already deleted
		else:
			# only delete the ACP when it was created in the course of AE registration internally
			if  (ri := acpRes.resource.createdInternally()) is not None and resource.ri == ri:
				return CSE.dispatcher.deleteResource(acpRes.resource)
		return Result(rsc=RC.deleted)


	def _addToAccessCSBaseACP(self, originator: str) -> None:
		""" Add an originator to the ACP that allows at least RETRIEVE access
			to any registered CSE and AE.
		"""
		if (res := CSE.dispatcher.retrieveResource(CSE.security.csebaseAccessACPI)).resource is not None:
			res.resource.addPermission([originator], Permission.RETRIEVE)
			res.resource.dbUpdate()


	def _removeFromAccessCSEBaseACP(self, originator: str) -> None:
		"""	Remove an originator from the ACP that allows RETRIEVE access to
			any registered CSE and AE.
		"""
		if (res := CSE.dispatcher.retrieveResource(CSE.security.csebaseAccessACPI)).resource is not None:
			res.resource.removePermissionForOriginator(originator)
			res.resource.dbUpdate()

