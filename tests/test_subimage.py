import tempfile
import unittest
from pathlib import Path
import numpy as np
from astropy.io import fits
from c0_pipeline.subimage_audit import audit
from c0_pipeline.core import Stop

class SubimageTests(unittest.TestCase):
 def fixture(self,path,mismatch=False,negative=False):
  hdus=[fits.PrimaryHDU(header=fits.Header({'VERSION':'DR5'}))]
  for band in 'grz':
   for kind in ['image','invvar']:
    h=fits.Header({'VERSION':'DR5','SURVEY':'DECaLS','BAND':band,'BRICK':'1853p160','IMAGETYP':kind,'BRICK_X0':0,'BRICK_Y0':0,'CTYPE1':'RA---TAN','CTYPE2':'DEC--TAN','CRPIX1':2.,'CRPIX2':2.,'CRVAL1':1.,'CRVAL2':2.,'CD1_1':0.001,'CD2_2':0.001})
    data=np.ones((3,3) if mismatch and kind=='invvar' else (4,4),dtype='f4')
    if negative and kind=='invvar':data[0,0]=-1
    hdus.append(fits.ImageHDU(data,header=h))
  fits.HDUList(hdus).writeto(path)
 def test_maps_are_not_calibration_proof(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'x.fits';self.fixture(p);a=audit(p)
   self.assertEqual(len(a['products']),6);self.assertEqual(a['unit_status'],'PENDING_OFFICIAL_COADD_COMPARISON')
 def test_bad_ivar_rejected(self):
  for kwargs in [{'mismatch':True},{'negative':True}]:
   with tempfile.TemporaryDirectory() as t:
    p=Path(t)/'x.fits';self.fixture(p,**kwargs)
    with self.assertRaises(Stop):audit(p)
