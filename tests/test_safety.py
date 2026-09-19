import tempfile
import unittest
from pathlib import Path
from c0_pipeline.core import Budget, Stop, LIMIT_BYTES, check_probe_fields, validate_product

class Safety(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.b = Budget(self.temp.name)
    def tearDown(self):
        self.b.db.close()
        self.temp.cleanup()
    def test_bytes_boundary_persists(self):
        self.b.charge(LIMIT_BYTES)
        with self.assertRaises(Stop): self.b.charge(1)
        other=Budget(self.temp.name)
        self.assertEqual(other.count('bytes'), LIMIT_BYTES)
        other.db.close()
    def test_requests_and_retries(self):
        for i in range(1000): self.b.request(str(i), False)
        with self.assertRaises(Stop): self.b.request('extra', False)
        for _ in range(4): self.b.request('metadata', True)
        with self.assertRaises(Stop): self.b.request('metadata', True)
    def test_object_limit_and_dedup(self):
        for i in range(96): self.b.object(str(i))
        self.b.object('0')
        with self.assertRaises(Stop): self.b.object('96')
    def test_no_leak(self):
        check_probe_fields(['galaxy_id','ra_deg'])
        secret='synthetic_forbidden_label'
        with self.assertRaises(Stop) as e: check_probe_fields(['galaxy_id',secret])
        self.assertNotIn(secret,str(e.exception))
    def test_false_products(self):
        for kind,field in [('pixel_mask','ANYMASK_R'),('pixel_mask','ALLMASK_R'),('pixel_ivar','FLUX_IVAR_R')]:
            with self.assertRaises(Stop): validate_product(kind,field,(4,4),(4,4))
        with self.assertRaises(Stop): validate_product('pixel_ivar','INVVAR',(4,4),(3,3))

if __name__ == '__main__': unittest.main()

class IdentityTests(unittest.TestCase):
    def test_fallback_preserves_source_row(self):
        from c0_pipeline.identity import identities
        rows=[dict(iauname=None,ra_deg=1.,dec_deg=2.,source_row=7),dict(iauname='JTEST',ra_deg=3.,dec_deg=4.,source_row=8)]
        a=identities(rows,'record','sha')
        b=identities(list(reversed(rows)),'record','sha')
        self.assertEqual({r['source_row']:r['galaxy_id'] for r in a},{r['source_row']:r['galaxy_id'] for r in b})
