import unittest
import numpy as np
from c0_pipeline.normal_cutout import kernel,interpolate_interior,combine

class NormalReferenceTests(unittest.TestCase):
    def test_kernel_support(self):
        self.assertEqual(kernel(0),1)
        self.assertTrue(np.all(kernel(np.array([-4.,-3.,3.,4.]))==0))
    def test_constant_and_unknown_edges(self):
        a=np.full((20,20),7.)
        v,k=interpolate_interior(a,np.array([10.2,0.,18.]),np.array([10.4,10.,10.]))
        np.testing.assert_array_equal(k,[True,False,False])
        self.assertAlmostEqual(v[0],7.,places=12)
        self.assertTrue(np.all(np.isnan(v[1:])))
    def test_integer_impulse_and_nan_not_filled(self):
        a=np.zeros((20,20));a[10,10]=1
        v,k=interpolate_interior(a,np.array([10.]),np.array([10.]))
        self.assertAlmostEqual(v[0],1.,places=12)
        a[8,8]=np.nan
        v,k=interpolate_interior(a,np.array([10.2]),np.array([10.3]))
        self.assertTrue(k[0]);self.assertTrue(np.isnan(v[0]))
    def test_bricks_known_nan_unknown_separate(self):
        v,k,n=combine([[2.,np.nan,2.,np.nan],[4.,6.,4.,np.nan]],[[True]*4,[True,True,False,True]])
        np.testing.assert_allclose(v[[0,1,3]],[3,6,0])
        self.assertFalse(k[2]);self.assertTrue(np.isnan(v[2]));self.assertEqual(n[3],0)
    def test_nonfinite_coordinates_are_unknown(self):
        v,k=interpolate_interior(np.ones((20,20)),np.array([np.nan,np.inf]),np.array([3.,3.]))
        self.assertFalse(k.any());self.assertTrue(np.isnan(v).all())

if __name__=='__main__':unittest.main()
