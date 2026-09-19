import unittest
import tempfile
from unittest.mock import patch
from c0_pipeline.core import Budget
from c0_pipeline.remote_head import head
from c0_pipeline.manual_resource_inventory import plan

class NoBodyResponse:
 code=200
 headers={'Content-Length':'9999999999','Accept-Ranges':'bytes'}
 def __enter__(self):return self
 def __exit__(self,*args):pass
 def read(self,*args):raise AssertionError('HEAD must not read body')

class InventoryTests(unittest.TestCase):
 def test_head_never_downloads_large_resource(self):
  with tempfile.TemporaryDirectory() as t:
   b=Budget(t)
   with patch('urllib.request.OpenerDirector.open',return_value=NoBodyResponse()) as op:
    e=head(b,'https://fixture.test/large');head(b,'https://fixture.test/large')
    self.assertEqual(op.call_count,1)
    self.assertEqual(op.call_args.args[0].get_method(),'HEAD')
    self.assertEqual(b.count('bytes'),0);self.assertEqual(b.count('data_requests'),0)
    self.assertEqual(e['declared_bytes'],'9999999999')
   b.db.close()
 def test_dedup_preserves_all_object_links(self):
  r=dict(brickname='1853p160',galaxy_id='A',probe_rank=1,tractor_candidate_url='https://x/tractor.fits',coadd_directory='https://x/',comparison_subset=True)
  p=plan([r,dict(r,galaxy_id='B',probe_rank=2)])
  self.assertEqual(len(p),7)
  self.assertTrue(all(v['galaxy_ids']==['A','B'] for v in p))
