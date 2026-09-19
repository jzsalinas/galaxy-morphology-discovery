import tempfile
import unittest
from pathlib import Path
from c0_pipeline.core import Stop
from c0_pipeline.fits_audit import inspect
from astropy.io import fits
import numpy as np

class FITSTests(unittest.TestCase):
 def make(self,path):
  h=fits.Header({'SURVEY':'DECaLS','VERSION':'DR5','BANDS':'grz','CTYPE1':'RA---TAN','CTYPE2':'DEC--TAN','CRVAL1':1.,'CRVAL2':2.,'CRPIX1':128.5,'CRPIX2':128.5,'CD1_1':-0.262/3600,'CD1_2':0.,'CD2_1':0.,'CD2_2':0.262/3600})
  fits.writeto(path,np.ones((3,256,256),dtype='float32'),h,overwrite=True)
 def test_missing_unit_remains_inconclusive(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'x.fits';self.make(p);r=inspect(p,1.,2.)
   self.assertEqual(r['unit_status'],'INCONCLUSIVE_MISSING_BUNIT')
   self.assertLess(r['center_error_pixels'],1e-5)
   self.assertEqual(r['coverage_status'],'UNKNOWN_WITHOUT_COVERAGE_PRODUCT')
 def test_release_and_wcs_required(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'x.fits'
   for key in ['VERSION','CTYPE1']:
    self.make(p)
    with fits.open(p,mode='update') as h:del h[0].header[key]
    with self.assertRaises(Stop):inspect(p,1.,2.)
 def test_wrong_center_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'x.fits';self.make(p)
   with self.assertRaises(Stop):inspect(p,2.,3.)
