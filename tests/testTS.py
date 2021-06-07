 #
#	testTS.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for TS functionality
#

import unittest, sys, time
import requests
sys.path.append('../acme')
from typing import Tuple, Dict
from Constants import Constants as C
from Types import ResourceTypes as T, NotificationContentType, ResponseCode as RC, Operation, ResponseType, Permission
from init import *

# TODO set pei, no peid -> set by CSE
# TODO set to big peid

class TestTS(unittest.TestCase):

	ae 			= None
	originator 	= None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		# create other resources
		dct =	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : 'NMyAppId',
			 		'rr'  : False,
			 		'srv' : [ '3' ],
			 		'poa' : [ NOTIFICATIONSERVER ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.created, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createTS(self) -> None:
		""" Create <TS> """
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 
					'rn'	: tsRN,
					'pei'	: 1000,
					'mdd'	: True,
					'mdn'	: 10,
					'cnf'	: 'application/test'
				}}
		r, rsc = CREATE(aeURL, TestTS.originator, T.TS, dct)
		self.assertEqual(rsc, RC.created, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_attributesTS(self) -> None:
		"""	Retrieve <TS> attributes """
		r, rsc = RETRIEVE(tsURL, TestTS.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertEqual(findXPath(r, 'm2m:ts/ty'), T.TS)
		self.assertEqual(findXPath(r, 'm2m:ts/pi'), findXPath(TestTS.ae,'m2m:ae/ri'))
		self.assertEqual(findXPath(r, 'm2m:ts/cni'), 0)
		self.assertEqual(findXPath(r, 'm2m:ts/cbs'), 0)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/cnf'))
		self.assertEqual(findXPath(r, 'm2m:ts/cnf'), 'application/test')
		self.assertEqual(findXPath(r, 'm2m:ts/pei'), 1000)
		self.assertTrue(findXPath(r, 'm2m:ts/mdd'))
		self.assertEqual(findXPath(r, 'm2m:ts/mdn'), 10)
		self.assertIsNone(findXPath(r, 'm2m:ts/mdlt'))		# empty mdlt is not created by default
		self.assertEqual(findXPath(r, 'm2m:ts/mdc'), 0)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createTSunderTS(self) -> None:
		""" Create <TS> under <TS> -> Fail"""
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 
					'rn'	: tsRN,
				}}
		r, rsc = CREATE(tsURL, TestTS.originator, T.TS, dct)
		self.assertEqual(rsc, RC.invalidChildResourceType, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateTSmni(self) -> None:
		""" Update <TS> mni"""
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 
					'mni'	: 10
				}}
		r, rsc = UPDATE(tsURL, TestTS.originator, dct)
		self.assertEqual(rsc, RC.updated, r)
		self.assertIsNotNone(r)
		self.assertEqual(findXPath(r, 'm2m:ts/mni'), 10)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateTSmbs(self) -> None:
		""" Update <TS> mbs"""
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 
					'mbs'	: 1000
				}}
		r, rsc = UPDATE(tsURL, TestTS.originator, dct)
		self.assertEqual(rsc, RC.updated, r)
		self.assertIsNotNone(r)
		self.assertEqual(findXPath(r, 'm2m:ts/mbs'), 1000)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateTSpei(self) -> None:
		""" Update <TS> pei -> Fail"""
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 
					'pei'	: 1000
				}}
		r, rsc = UPDATE(tsURL, TestTS.originator, dct)
		self.assertEqual(rsc, RC.badRequest, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateTSmdd(self) -> None:
		""" Update <TS> mdd -> Fail"""
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 
					'mdd'	: False
				}}
		r, rsc = UPDATE(tsURL, TestTS.originator, dct)
		self.assertEqual(rsc, RC.badRequest, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateTSmdn(self) -> None:
		""" Update <TS> mdd"""
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 
					'mdn'	: 5
				}}
		r, rsc = UPDATE(tsURL, TestTS.originator, dct)
		self.assertEqual(rsc, RC.updated, r)
		self.assertEqual(findXPath(r, 'm2m:ts/mdn'), 5)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateTSmdc(self) -> None:
		""" Update <TS> mdc -> Fail"""
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 
					'mdc'	: 5
				}}
		r, rsc = UPDATE(tsURL, TestTS.originator, dct)
		self.assertEqual(rsc, RC.badRequest, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateTSmdlt(self) -> None:
		""" Update <TS> mdc -> Fail"""
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 			# type: ignore [var-annotated]
					'mdlt'	: [ ]
				}}
		r, rsc = UPDATE(tsURL, TestTS.originator, dct)
		self.assertEqual(rsc, RC.badRequest, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateTScnf(self) -> None:
		""" Update <TS> cnf -> Fail"""
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 
					'cnf'	: 'application/wrong'
				}}
		r, rsc = UPDATE(tsURL, TestTS.originator, dct)
		self.assertEqual(rsc, RC.badRequest, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateTSremoveMdn(self) -> None:
		""" Update <TS> remove mdn, mdlt also removed"""
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 
					'mdn'	: None
				}}
		r, rsc = UPDATE(tsURL, TestTS.originator, dct)
		self.assertEqual(rsc, RC.updated, r)
		self.assertIsNone(findXPath(r, 'm2m:ts/mdc'), r)
		self.assertIsNone(findXPath(r, 'm2m:ts/mdn'), r)
		self.assertIsNone(findXPath(r, 'm2m:ts/mdlt'), r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteTS(self) -> None:
		"""	Delete <TS> """
		_, rsc = DELETE(tsURL, TestTS.originator)
		self.assertEqual(rsc, RC.deleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createTSnoMdd(self) -> None:
		""" Create <TS> without MDD"""
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 
					'rn'	: tsRN,
					'mdd'	: False
				}}
		r, rsc = CREATE(aeURL, TestTS.originator, T.TS, dct)
		self.assertEqual(rsc, RC.created, r)
		self.assertFalse(findXPath(r, 'm2m:ts/mdd'), r)
		self.assertIsNone(findXPath(r, 'm2m:ts/mdlt'), r)
		self.assertIsNone(findXPath(r, 'm2m:ts/mdc'), r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateTSMddwrong(self) -> None:
		""" Update <TS> MDD -> Fail """
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 
					'mdd'	: True
				}}
		r, rsc = UPDATE(tsURL, TestTS.originator, dct)
		self.assertEqual(rsc, RC.badRequest, r)



def run(testVerbosity:int, testFailFast:bool) -> Tuple[int, int, int]:
	suite = unittest.TestSuite()

	suite.addTest(TestTS('test_createTS'))
	suite.addTest(TestTS('test_attributesTS'))
	suite.addTest(TestTS('test_createTSunderTS'))
	suite.addTest(TestTS('test_updateTSmni'))
	suite.addTest(TestTS('test_updateTSmbs'))
	suite.addTest(TestTS('test_updateTSpei'))
	suite.addTest(TestTS('test_updateTSmdd'))
	suite.addTest(TestTS('test_updateTSmdn'))
	suite.addTest(TestTS('test_updateTSmdc'))
	suite.addTest(TestTS('test_updateTSmdlt'))
	suite.addTest(TestTS('test_updateTSremoveMdn'))
	suite.addTest(TestTS('test_updateTScnf'))
	suite.addTest(TestTS('test_deleteTS'))
	suite.addTest(TestTS('test_createTSnoMdd'))
	suite.addTest(TestTS('test_updateTSMddwrong'))


	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)

if __name__ == '__main__':
	_, errors, _ = run(2, True)
	sys.exit(errors)

