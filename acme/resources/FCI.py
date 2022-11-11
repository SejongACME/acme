#
#	FCI.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: FlexContainerInstance
#

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes, Result, ResponseStatusCode, JSON
from ..resources.Resource import *


class FCI(Resource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes:list[ResourceTypes] = [ ]

	# Attributes and Attribute policies for this Resource Class
	# Assigned during startup in the Importer
	_attributes:AttributePolicyDict = {		
		# Common and universal attributes
		'rn': None,
		'ty': None,
		'ri': None,
		'pi': None,
		'ct': None,
		'et': None,
		'lbl': None,

		# Resource attributes
		'cs': None,
		'org': None
	}


	def __init__(self, dct:Optional[JSON] = None, 
					   pi:Optional[str] = None, 
					   fcntType:Optional[str] = None, 
					   create:Optional[bool] = False) -> None:
		super().__init__(ResourceTypes.FCI, dct, pi, tpe = fcntType, create = create, inheritACP = True, readOnly = True)


	# Forbidd updating
	def update(self, dct:Optional[JSON] = None, 
					 originator:Optional[str] = None,
					 doValidateAttributes:Optional[bool] = True) -> Result:
		return Result.errorResult(rsc = ResponseStatusCode.operationNotAllowed, dbg = 'updating FCIN is forbidden')

