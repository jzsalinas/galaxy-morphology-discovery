import gzip
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from c0_pipeline.reconcile import parse_identity,reconcile
from c0_pipeline.core import Stop
try:
 import pyarrow as pa
 import pyarrow.parquet as pq
except ImportError:pa=None

def record(name,ra,dec):
 return (f'{name:19s} {ra:22.18f} {dec:23.18f}'+' PRIVATE_SYNTHETIC_PAYLOAD\n').encode('ascii')

class ParserTests(unittest.TestCase):
 def test_only_identity(self):
  self.assertEqual(parse_identity(record('J000001.00+000001.0',1.,2.)),('J000001.00+000001.0',1.,2.))
 def test_short_record(self):
  with self.assertRaises(Stop):parse_identity(b'bad')

@unittest.skipIf(pa is None,'Requires installed PyArrow')
class ReconcileTests(unittest.TestCase):
 def test_duplicate_missing_and_coordinate_difference(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'c0/quarantine').mkdir(parents=True)
   pq.write_table(pa.table({'iauname':['A','B','D'],'galaxy_id':['GZD5:A','GZD5:B','GZD5:D'],'ra_deg':[1.,3.,8.],'dec_deg':[2.,4.,9.]}),root/'c0/quarantine/SUBJECT_INDEX.parquet')
   raw=root/'synthetic.gz'
   with gzip.open(raw,'wb') as f:
    for name,ra,dec in [('A',1.,2.),('A',1.,2.),('B',3.,4.01),('C',5.,6.)]:f.write(record(name,ra,dec))
   with patch('c0_pipeline.reconcile.ROOT',root):r=reconcile(raw)
   self.assertEqual(r['cds_duplicate_rows'],2)
   self.assertEqual(r['unique_matches'],1)
   self.assertEqual(r['coordinate_differences'],1)
   self.assertEqual(r['cds_names_absent_zenodo'],1)
   self.assertEqual(r['zenodo_names_absent_cds'],1)
   self.assertNotIn('PRIVATE_SYNTHETIC_PAYLOAD',str(r))
