import unittest
from c0_pipeline.gates import global_decision

class GateTests(unittest.TestCase):
 def test_critical_inconclusive_stops(self):
  for key in 'ABC':
   s=dict.fromkeys('ABCDEF','PASS');s[key]='INCONCLUSIVE'
   self.assertEqual(global_decision(s),'STOP')
 def test_o3_failure_does_not_kill_core(self):
  s=dict.fromkeys('ABCDEF','PASS');s['E']='FAIL'
  self.assertEqual(global_decision(s),'GO_WITH_REVISION')
 def test_d_requires_verified_revision(self):
  s=dict.fromkeys('ABCDEF','PASS');s['D']='FAIL'
  self.assertEqual(global_decision(s),'STOP')
  self.assertEqual(global_decision(s,d_revision_verified=True),'GO_WITH_REVISION')
 def test_f_requires_verified_pilot(self):
  s=dict.fromkeys('ABCDEF','PASS');s['F']='INCONCLUSIVE'
  self.assertEqual(global_decision(s),'STOP')
  self.assertEqual(global_decision(s,pilot_verified=True),'GO_WITH_REVISION')
 def test_legal_stop(self):
  self.assertEqual(global_decision(dict.fromkeys('ABCDEF','PASS'),legal_incompatibility=True),'STOP')
