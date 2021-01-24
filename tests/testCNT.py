#
#	testCNT.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for CNT functionality
#

import unittest, sys
sys.path.append('../acme')
from Constants import Constants as C
from Types import ResourceTypes as T, ResponseCode as RC
from init import *

# The following code must be executed before anything else because it influences
# the collection of skipped tests.
# It checks whether there actually is a CSE running.
noCSE = not connectionPossible(cseURL)

class TestCNT(unittest.TestCase):

	cse				= None
	ae 				= None
	originator 		= None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		cls.cse, rsc = RETRIEVE(cseURL, ORIGINATOR)
		assert rsc == RC.OK, f'Cannot retrieve CSEBase: {cseURL}'

		dct = 	{ 'm2m:ae' : {
					'rn': aeRN, 
					'api': 'NMyApp1Id',
				 	'rr': False,
				 	'srv': [ '3' ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.created, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		DELETE(f'{cseURL}/{cntRN}', ORIGINATOR)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNT(self) -> None:
		"""	Create <CNT> """
		self.assertIsNotNone(TestCNT.cse)
		self.assertIsNotNone(TestCNT.ae)
		dct = 	{ 'm2m:cnt' : { 
					'rn' : cntRN
				}}
		r, rsc = CREATE(aeURL, TestCNT.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.created)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNT(self) -> None:
		""" Retrieve <CNT> """
		_, rsc = RETRIEVE(cntURL, TestCNT.originator)
		self.assertEqual(rsc, RC.OK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTWithWrongOriginator(self) -> None:
		"""	Retrieve <CNT> with wrong originator -> Fail """
		_, rsc = RETRIEVE(cntURL, 'Cwrong')
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_attributesCNT(self) -> None:
		""" Test <CNT> attributes """
		r, rsc = RETRIEVE(cntURL, TestCNT.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cnt/ty'), T.CNT)
		self.assertEqual(findXPath(r, 'm2m:cnt/pi'), findXPath(TestCNT.ae,'m2m:ae/ri'))
		self.assertEqual(findXPath(r, 'm2m:cnt/rn'), cntRN)
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/et'))
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/st'))
		self.assertEqual(findXPath(r, 'm2m:cnt/cr'), TestCNT.originator)
		self.assertEqual(findXPath(r, 'm2m:cnt/cbs'), 0)
		self.assertEqual(findXPath(r, 'm2m:cnt/cni'), 0)
		self.assertGreater(findXPath(r, 'm2m:cnt/mbs'), 0)
		self.assertGreater(findXPath(r, 'm2m:cnt/mni'), 0)
		self.assertIsNone(findXPath(r, 'm2m:cnt/lbl'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNT(self) -> None:
		"""	Update <CNT> """
		dct = 	{ 'm2m:cnt' : {
					'lbl' : [ 'aTag' ],
					'mni' : 10,
					'mbs' : 9999
 				}}
		cnt, rsc = UPDATE(cntURL, TestCNT.originator, dct)
		self.assertEqual(rsc, RC.updated)
		cnt, rsc = RETRIEVE(cntURL, TestCNT.originator)		# retrieve cnt again
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(cnt, 'm2m:cnt/lbl'))
		self.assertIsInstance(findXPath(cnt, 'm2m:cnt/lbl'), list)
		self.assertGreater(len(findXPath(cnt, 'm2m:cnt/lbl')), 0)
		self.assertTrue('aTag' in findXPath(cnt, 'm2m:cnt/lbl'))
		self.assertIsNotNone(findXPath(cnt, 'm2m:cnt/mni'))
		self.assertIsInstance(findXPath(cnt, 'm2m:cnt/mni'), int)
		self.assertEqual(findXPath(cnt, 'm2m:cnt/mni'), 10)
		self.assertIsNotNone(findXPath(cnt, 'm2m:cnt/mbs'))
		self.assertIsInstance(findXPath(cnt, 'm2m:cnt/mbs'), int)
		self.assertEqual(findXPath(cnt, 'm2m:cnt/mbs'), 9999)
		self.assertIsNotNone(findXPath(cnt, 'm2m:cnt/st'))
		self.assertIsInstance(findXPath(cnt, 'm2m:cnt/st'), int)
		self.assertEqual(findXPath(cnt, 'm2m:cnt/st'), 1)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTTy(self) -> None:
		"""	Update <CNT> TY -> Fail """
		dct = 	{ 'm2m:cnt' : {
					'ty' : T.CSEBase
				}}
		r, rsc = UPDATE(cntURL, TestCNT.originator, dct)
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTPi(self) -> None:
		"""	Update <CNT> PI -> Fail """
		dct = 	{ 'm2m:cnt' : {
					'pi' : 'wrongID'
				}}
		r, rsc = UPDATE(cntURL, TestCNT.originator, dct)
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTUnknownAttribute(self) -> None:
		"""	Update <CNT> unknown attribute -> Fail """
		dct = 	{ 'm2m:cnt' : {
					'unknown' : 'unknown'
				}}
		r, rsc = UPDATE(cntURL, TestCNT.originator, dct)
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTWrongMNI(self) -> None:
		"""	Update <CNT> wrong MNI -> Fail """
		dct = 	{ 'm2m:cnt' : {
					'mni' : -1
				}}
		r, rsc = UPDATE(cntURL, TestCNT.originator, dct)
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTUnderCNT(self) -> None:
		""" Create <CNT> under <CNT> """
		self.assertIsNotNone(TestCNT.cse)
		dct = 	{ 'm2m:cnt' : { 
					'rn' : cntRN
				}}
		r, rsc = CREATE(cntURL, TestCNT.originator, T.CNT, dct) 
		self.assertEqual(rsc, RC.created)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTUnderCNT(self) -> None:
		"""	Retrieve <CNT> under <CNT> """
		_, rsc = RETRIEVE(f'{cntURL}/{cntRN}', TestCNT.originator)
		self.assertEqual(rsc, RC.OK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCNTUnderCNT(self) -> None:
		"""	Delete <CNT> under <CNT> """
		_, rsc = DELETE(f'{cntURL}/{cntRN}', TestCNT.originator)
		self.assertEqual(rsc, RC.deleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCNTByUnknownOriginator(self) -> None:
		"""	Delete <CNT> with wrong originator -> Fail """
		_, rsc = DELETE(cntURL, 'Cwrong')
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCNTByAssignedOriginator(self) -> None:
		"""	Delete <CNT> with correct originator """
		_, rsc = DELETE(cntURL, TestCNT.originator)
		self.assertEqual(rsc, RC.deleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTUnderCSE(self) -> None:
		"""	Create <CNT> under <CB> with admin Originator """
		self.assertIsNotNone(TestCNT.cse)
		dct = 	{ 'm2m:cnt' : { 
					'rn' : cntRN
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, T.CNT, dct) # With Admin originator !!
		self.assertEqual(rsc, RC.created)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTUnderCSE(self) -> None:
		"""	Retrieve <CNT> under <CB> with admin Originator """
		_, rsc = RETRIEVE(f'{cseURL}/{cntRN}', ORIGINATOR)
		self.assertEqual(rsc, RC.OK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCNTUnderCSE(self) -> None:
		"""	Delete <CNT> under <CB> with admin Originator """
		_, rsc = DELETE(f'{cseURL}/{cntRN}', ORIGINATOR)
		self.assertEqual(rsc, RC.deleted)


def run() -> Tuple[int, int, int]:
	suite = unittest.TestSuite()
	suite.addTest(TestCNT('test_createCNT'))
	suite.addTest(TestCNT('test_retrieveCNT'))
	suite.addTest(TestCNT('test_retrieveCNTWithWrongOriginator'))
	suite.addTest(TestCNT('test_attributesCNT'))
	suite.addTest(TestCNT('test_updateCNT'))
	suite.addTest(TestCNT('test_updateCNTTy'))
	suite.addTest(TestCNT('test_updateCNTPi'))
	suite.addTest(TestCNT('test_updateCNTUnknownAttribute'))
	suite.addTest(TestCNT('test_updateCNTWrongMNI'))
	suite.addTest(TestCNT('test_createCNTUnderCNT'))
	suite.addTest(TestCNT('test_retrieveCNTUnderCNT'))
	suite.addTest(TestCNT('test_deleteCNTUnderCNT'))
	suite.addTest(TestCNT('test_deleteCNTByUnknownOriginator'))
	suite.addTest(TestCNT('test_deleteCNTByAssignedOriginator'))
	suite.addTest(TestCNT('test_createCNTUnderCSE'))
	suite.addTest(TestCNT('test_retrieveCNTUnderCSE'))
	suite.addTest(TestCNT('test_deleteCNTUnderCSE'))
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)

if __name__ == '__main__':
	_, errors, _ = run()
	sys.exit(errors)
