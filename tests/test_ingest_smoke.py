import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
try:
 import pyarrow as pa
 import pyarrow.parquet as pq
except ImportError:
 pa=None

@unittest.skipIf(pa is None,'Requires manually installed PyArrow')
class IngestSmoke(unittest.TestCase):
 def test_synthetic_quarantine_and_repeat(self):
  from c0_pipeline.ingest import ingest
  from c0_pipeline.core import sha
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)
   (root/'c0/quarantine/INTERPRETATION_LOCKBOX').mkdir(parents=True)
   raw=root/'synthetic.parquet'
   pq.write_table(pa.table({'iauname':['J000001.00+000001.0','J000002.00+000002.0'], 'ra':[1.,2.], 'dec':[3.,4.], 'redshift':[0.01,0.02], 'synthetic_blocked':[0.2,0.8]}),raw)
   md5=hashlib.md5(raw.read_bytes()).hexdigest()
   with patch('c0_pipeline.ingest.ROOT',root):
    first=ingest(raw,'synthetic-record',md5)
    second=ingest(raw,'synthetic-record',md5)
   self.assertEqual(first['outputs'],second['outputs'])
   subject=pq.read_table(root/'c0/quarantine/SUBJECT_INDEX.parquet')
   self.assertNotIn('synthetic_blocked',subject.column_names)
   self.assertEqual(first['blocked_column_count'],1)
   self.assertEqual(first['rows'],2)
