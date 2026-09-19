import unittest
from c0_pipeline.probe import select
from c0_pipeline.core import Stop

def rows():
 return [dict(galaxy_id=f'GZD5:{i:04}',ra_deg=float(i//4),dec_deg=0.,source_row=i,petro_radius=float(i%13),active_learning_on=bool(i%2)) for i in range(512)]

class ProbeTests(unittest.TestCase):
 def test_quota_and_row_order(self):
  r=rows();a=select(r)
  self.assertEqual(a,select(list(reversed(r))))
  self.assertEqual(len(a),96)
  self.assertEqual([sum(x['stratum_ra']==q for x in a) for q in range(4)],[24]*4)
  self.assertGreaterEqual(sum(x['active_learning_stratum'] is True for x in a),24)
  self.assertGreaterEqual(sum(x['active_learning_stratum'] is False for x in a),24)
 def test_rejects_extra_column(self):
  r=rows();r[0]['synthetic_forbidden']=0
  with self.assertRaises(Stop):select(r)
 def test_no_silent_size_imputation(self):
  r=rows();r[0]['petro_radius']=None
  with self.assertRaises(Stop):select(r)
 def test_impossible_active_quota_stops(self):
  r=rows()
  for x in r:x['active_learning_on']=True
  with self.assertRaises(Stop):select(r)
 def test_absent_active_does_not_invent_values(self):
  r=rows()
  for x in r:x['active_learning_on']=None
  self.assertTrue(all(x['active_learning_stratum'] is None for x in select(r)))
