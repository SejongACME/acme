#
#	NOD.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:Node
#

from Constants import Constants as C
from Types import ResourceTypes as T, JSON
import Utils, CSE
from Validator import constructPolicy, addPolicy
from .Resource import *
from .AnnounceableResource import AnnounceableResource


# TODO Support cmdhPolicy
# TODO Support storage

attributePolicies = constructPolicy([ 
	'ty', 'ri', 'rn', 'pi', 'acpi', 'ct', 'lt', 'et', 'lbl', 'at', 'aa', 'daci', 'hld',
])
nodPolicies = constructPolicy([
	'ni', 'hcl', 'hael', 'hsl', 'mgca', 'rms', 'nid', 'nty'
])
attributePolicies = addPolicy(attributePolicies, nodPolicies)


class NOD(AnnounceableResource):

	# Specify the allowed child-resource types
	allowedChildResourceTypes = [ T.MGMTOBJ, T.SUB ]


	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False, isRemote:bool=False) -> None:
		super().__init__(T.NOD, dct, pi, create=create, attributePolicies=attributePolicies, isRemote=isRemote)

		self.resourceAttributePolicies = nodPolicies	# only the resource type's own policies

		if self.dict is not None:
			self.setAttribute('ni', Utils.uniqueID(), overwrite=False)


	def deactivate(self, originator:str) -> None:
		super().deactivate(originator)

		# Remove self from all hosted AE's (their node links)
		if (hael := self['hael']) is None:
			return
		ri = self['ri']
		for ae in self['hael']:
			self._removeNODfromAE(ae, ri)


	def _removeNODfromAE(self, aeRI:str, ri:str) -> None:
		""" Remove NOD.ri from AE node link. """
		if (aeResource := CSE.dispatcher.retrieveResource(aeRI).resource) is not None:
			nl = aeResource['nl']
			if nl is not None and isinstance(nl, str) and ri == nl:
				aeResource.delAttribute('nl')
				aeResource.dbUpdate()

