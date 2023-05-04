#
#	ActionManager.py
#
#	(c) 2022 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#

"""	This module implements an action manager service functionality for the CSE.
"""

from __future__ import annotations
from typing import Optional, Any, cast

import sys, copy

from ..etc.Types import Result, EvalMode, EvalCriteriaOperator, JSON, CSERequest
from ..etc.ResponseStatusCodes import ResponseException, INTERNAL_SERVER_ERROR
from ..helpers.TextTools import setXPath
from ..etc.DateUtils import utcTime
from ..etc.RequestUtils import responseFromResult
from ..services import CSE
from ..services.Configuration import Configuration
from ..services.Logging import Logging as L
from ..resources.ACTR import ACTR


# TODO implement support for input attribute when the procedure is clear
# TODO dependcy resources

class ActionManager(object):
	"""	This class defines functionalities to handle action triggerings, 
		dependancies and other action related functionalities

		Attributes:
	"""

	__slots__ = (
		'ecpPeriodicDefault',
		'ecpContinuousDefault',
	)
	
	# Imported here because of circular import
	from ..resources.Resource import Resource


	def __init__(self) -> None:
		"""	Initialization of an *ActionManager* instance.
		"""

		# Get the configuration settings
		self._assignConfig()

		# Add handler for configuration updates
		CSE.event.addHandler(CSE.event.configUpdate, self.configUpdate)				# type: ignore

		# Add handler for any resource change event
		CSE.event.addHandler(CSE.event.changeResource, self.evaluateActions)	# type: ignore

		CSE.event.addHandler(CSE.event.cseReset, self.restart)		# type: ignore
		L.isInfo and L.log('ActionManager initialized')


	def shutdown(self) -> bool:
		"""	Shutdown the Action Manager.
		
			Returns:
				Boolean that indicates the success of the operation
		"""
		L.isInfo and L.log('ActionManager shut down')
		return True


	def restart(self, name:str) -> None:
		"""	Restart the ActionManager service.
		"""
		L.isDebug and L.logDebug('ActionManager restarted')


	def _assignConfig(self) -> None:
		"""	Assign default configurations.
		"""
		self.ecpPeriodicDefault = Configuration.get('resource.actr.ecp.periodic')
		self.ecpContinuousDefault = Configuration.get('resource.actr.ecp.continuous')


	def configUpdate(self, name:str, key:Optional[str] = None, value:Any = None) -> None:
		"""	Handle configuration updates.
		"""
		if key not in [ 'resource.actr.ecp.periodic', 'resource.actr.ecp.continuous' ]:
			return
		self._assignConfig()
		return

	###############################################################################################


	def evaluateActions(self, name:str, resource:Resource) -> None:
		_ri = resource.ri
		_now = utcTime()
		L.isDebug and L.logDebug(f'Looking for resource actions for: {_ri}')

		# Get actions. Remember, these are NOT <action> resources
		actions = CSE.storage.searchActionsForSubject(_ri)		
		# sort by action priority
		actions = sorted(actions, key = lambda x: x['apy'] if x['apy'] is not None else sys.maxsize)

		for action in actions:

			if self.evaluateSingleAction(resource, action, _now):
				ri = action['ri']
				L.isDebug and L.logDebug(f'Action: conditions {ri} evaluate to True')

				# retrieve the real action resource
				try:
					actr = cast(ACTR, CSE.dispatcher.retrieveLocalResource(ri))
				except ResponseException as e:
					L.logErr(e.dbg)
					raise e

				# Assign a new to (ie. the objectRecourceID)
				apv = copy.deepcopy(actr.apv)
				setXPath(apv, 'to', actr.orc)

				# build request

				# TODO exception
				try:
					resReq = CSE.request.fillAndValidateCSERequest(request := CSERequest(originalRequest = apv))
				except ResponseException as e:
					L.logWarn(f'Error handling request: {request.originalRequest} : {e.dbg}')
					continue

				# Send request
				L.isDebug and L.logDebug(f'Sending request: {resReq.originalRequest}')
				try:
					res = CSE.request.handleRequest(resReq)

					# TODO handleRequest handling


					
				except ResponseException as e:
					L.logWarn(f'Error processing request: {e.dbg}')
					continue

				# Store response in the <actr>
				res.request = request
				actr.setAttribute('air', responseFromResult(res).data)	# type: ignore[attr-defined]
				try:
					actr.dbUpdate(False)
				except ResponseException as e:
					L.logWarn(f'Error updating <actr>: {e.dbg}')
					continue

				# Update according to evalMode
				evm = action['evm']
				if evm == EvalMode.once:			# remove if only once
					L.isDebug and L.logDebug(f'Removing "once" action: {ri}')
					CSE.storage.removeAction(ri)
					continue
				if evm == EvalMode.continous:		# remove from action DB if count reaches 0
					count = action['count']
					if (count := count - 1) == 0:
						L.isDebug and L.logDebug(f'Removing "continuous" action: {ri} (count: {actr.ecp} reached)')
						CSE.storage.removeAction(ri)
					else:
						action['count'] = count
						CSE.storage.updateActionRepr(action)
					continue
				if evm == EvalMode.periodic:
					_ecp = action['ecp'] / 1000.0
					action['periodTS'] = _now + ((action['periodTS'] - _now) % _ecp)
					L.isDebug and L.logDebug(f'Setting next period start to: {action["periodTS"]} for "periodic" action: {ri}')
					CSE.storage.updateActionRepr(action)


	def evaluateSingleAction(self, resource:Resource, action:JSON, nowTS:float) -> bool:
		# TODO doc

		# If the mode is periodic, and the next timestamp for the action is greater then now,
		# then the action is not yet available.
		if action['evm'] == EvalMode.periodic:
			L.isDebug and L.logDebug(f'next action TS: {action["periodTS"]} - now: {nowTS}')
			if action['periodTS'] > nowTS:
				return False

		sbjt = action['evc']['sbjt']
		if (attr := resource.attribute(sbjt)) is None:
			return False
		optr = action['evc']['optr']
		thld = action['evc']['thld']

		if optr == EvalCriteriaOperator.equal:
			return attr == thld
		if optr == EvalCriteriaOperator.notEqual:
			return attr != thld
		if optr == EvalCriteriaOperator.lessThan:
			return attr < thld
		if optr == EvalCriteriaOperator.lessThanEqual:
			return attr <= thld
		if optr == EvalCriteriaOperator.greaterThan:
			return attr > thld
		if optr == EvalCriteriaOperator.greaterThanEqual:
			return attr >= thld
		return False


	def scheduleAction(self, action:ACTR) -> None:
		evm = action.evm
		if evm == EvalMode.off:
			L.isDebug and L.logDebug(f'evm: off for action: {action.ri} - Action inactive.')
			CSE.storage.removeAction(action.ri)	# just remove, ignore result
			return
		if evm == EvalMode.once:
			L.isDebug and L.logDebug(f'evm: once for action: {action.ri}.')
			CSE.storage.updateAction(action, 0, 0)
			return
		if evm == EvalMode.periodic:
			ecp = action.ecp if action.ecp else self.ecpPeriodicDefault
			L.isDebug and L.logDebug(f'evm: periodic for action: {action.ri}, period: {ecp}.')
			CSE.storage.updateAction(action, utcTime(), 0)
			return
		if evm == EvalMode.continous:
			ecp = action.ecp if action.ecp else self.ecpContinuousDefault
			L.isDebug and L.logDebug(f'evm: continuous for action: {action.ri}, counter: {ecp}')
			CSE.storage.updateAction(action, 0, ecp)
			return
		raise INTERNAL_SERVER_ERROR(f'unknown EvalMode: {evm}. This should not happen.')
		

	def unscheduleAction(self, action:ACTR) -> None:
		CSE.storage.removeAction(action.ri)

	#
	#	Helper 
	#
