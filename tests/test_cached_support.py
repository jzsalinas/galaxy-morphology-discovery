import io
import unittest
import numpy as np
from astropy.io import fits
from c0_pipeline import cached_support as c
from c0_pipeline import operator_support as op
from c0_pipeline.core import Stop

class CachedTests(unittest.TestCase):
    def test_overlay_nan_is_available_hole_is_not(self):
        a=np.full((8,8),np.nan,np.float32);k=np.zeros((8,8),bool)
        c.overlay(a,k,[0,0,8,8],np.array([[np.nan,2]],np.float32),1,1)
        self.assertTrue(k[1,1]);self.assertFalse(k[0,0])
        c.overlay(a,k,[0,0,8,8],np.array([[np.nan,2]],np.float32),1,1)
        with self.assertRaises(Stop):c.overlay(a,k,[0,0,8,8],np.ones((1,2)),1,1)
    def test_cached_tiles_exact_and_hole(self):
        a=np.arange(64*64,dtype=np.float32).reshape(64,64)
        b=io.BytesIO();fits.HDUList([fits.PrimaryHDU(),fits.CompImageHDU(a,compression_type='RICE_1',tile_shape=(16,16))]).writeto(b)
        full=b.getvalue()
        with fits.open(io.BytesIO(full),disable_image_compression=True) as f:end=f[1].fileinfo()['datLoc']+f[1].header['NAXIS1']*f[1].header['NAXIS2']
        prefix=full[:end];_,desc,_=op.descriptor_table(prefix,len(full));start,stop=desc[0][0]
        z=np.full((2,2),7.,np.float32);g=dict(crop=[0,0,64,64],direct=(z,z),spline=(z,z),emitted=np.ones((2,2),bool))
        res=dict(total_bytes=len(full),range_events=[dict(range_start=0,range_end=end-1),dict(range_start=start,range_end=stop)])
        image,known,ids=c.decode_cached(prefix,full[start:stop+1],res,g,g,[])
        self.assertEqual(ids,[0]);np.testing.assert_array_equal(image[:16,:16],a[:16,:16]);self.assertEqual(known.sum(),256)
        res['range_events'][1]['range_end']-=1
        image,known,ids=c.decode_cached(prefix,full[start:stop],res,g,g,[])
        self.assertEqual(ids,[]);self.assertFalse(known.any())
    def test_unknown_never_evaluated_nan_separate(self):
        z=np.full((2,2),4.,np.float32);g=dict(crop=[0,0,9,9],direct=(z,z),spline=(z,z),emitted=np.ones((2,2),bool))
        a=np.ones((9,9),np.float32);k=np.ones_like(a,bool);k[1,1]=False
        v,known,active=c.evaluate(None,g,a,k,'analytic');self.assertFalse(known.any());self.assertTrue(active.all())
        k[:]=True;a[1,1]=np.nan
        v,known,active=c.evaluate(None,g,a,k,'analytic');self.assertTrue(known.all());self.assertTrue(np.isnan(v).all())
    def test_partition_accounting_and_norm(self):
        a=np.ones((256,256));m=np.ones(a.shape,bool);over=np.zeros_like(m);over[:,:10]=True
        r=c.metrics(a*2,a,m,over,a)['groups']
        self.assertEqual(r['all']['n'],65536);self.assertEqual(r['edge3']['n']+r['interior']['n'],65536)
        self.assertEqual(r['all']['relative_l2'],1);self.assertEqual(r['all']['positive'],65536)

if __name__=='__main__':unittest.main()
