import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from astropy.io import fits
from c0_pipeline.core import Budget,Stop
from c0_pipeline.ranges import fetch_range,RangeView
from c0_pipeline.range_plan import plan_section,read_section

class Response(io.BytesIO):
    def __init__(self,data=b'abcd',code=206,**headers):
        super().__init__(data);self.code=code
        self.headers={'Content-Range':'bytes 2-5/10','Content-Length':'4','ETag':'"fixed"',**headers}

class RangeHTTPTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.b=Budget(self.root)
    def tearDown(self):self.b.db.close();self.tmp.cleanup()
    def get(self):return fetch_range(self.b,'https://fixture.test/a',2,5,10,self.root/'part.bin','"fixed"')
    def test_valid_range_and_cache(self):
        with patch('urllib.request.OpenerDirector.open',return_value=Response()) as op:
            self.assertEqual(self.get()['access_result'],'VERIFIED_RANGE');self.get()
            self.assertEqual(op.call_count,1);self.assertEqual(self.b.count('bytes'),4)
            self.assertEqual(self.b.count('data_requests'),1)
            self.assertEqual(op.call_args.args[0].get_header('Range'),'bytes=2-5')
    def test_whole_file_fallback_rejected_without_read(self):
        response=Response(code=200)
        with patch.object(response,'read',side_effect=AssertionError('Must not read')),patch('urllib.request.OpenerDirector.open',return_value=response):
            self.assertEqual(self.get()['reason'],'EXACT_HTTP_RANGE_NOT_SUPPORTED')
        self.assertEqual(self.b.count('bytes'),0)
    def test_incompatible_headers_rejected(self):
        for headers in [{'Content-Range':'bytes 0-3/10'},{'ETag':'"changed"'},{'Content-Length':'5'},{'Content-Encoding':'gzip'}]:
            with patch('urllib.request.OpenerDirector.open',return_value=Response(**headers)):
                self.assertEqual(self.get()['access_result'],'INCONCLUSIVE')
        self.assertEqual(self.b.count('bytes'),0)
    def test_truncated_not_cached(self):
        with patch('urllib.request.OpenerDirector.open',return_value=Response(b'ab')):
            self.assertEqual(self.get()['reason'],'RANGE_TRUNCATED')
        self.assertFalse((self.root/'part.bin').exists());self.assertEqual(self.b.count('bytes'),2)
    def test_weak_etag_rejected_before_network(self):
        with self.assertRaises(Stop):fetch_range(self.b,'https://fixture.test/a',2,5,10,self.root/'x','W/"x"')
        self.assertEqual(self.b.count('data_requests'),0)
    def test_cache_does_not_mix_resource_versions(self):
        with patch('urllib.request.OpenerDirector.open',return_value=Response()):self.get()
        with self.assertRaises(Stop):fetch_range(self.b,'https://fixture.test/a',2,5,11,self.root/'part.bin','"fixed"')
        self.assertEqual(self.b.count('data_requests'),1)

class RangeViewTests(unittest.TestCase):
    def test_hole_fails_without_fabrication(self):
        view=RangeView(10,[(0,b'ab'),(8,b'ij')])
        with self.assertRaises(Stop):view.read(10)
        self.assertEqual(view.tell(),0)
        view.seek(-2,2);self.assertEqual(view.read(),b'ij')
    def test_conflicting_overlap_rejected(self):
        with self.assertRaises(Stop):RangeView(5,[(0,b'abc'),(2,b'ZZ')])
    def test_identical_overlap_allowed(self):
        self.assertEqual(RangeView(4,[(0,b'abc'),(2,b'cd')]).read(),b'abcd')

class CompressedEquivalenceTests(unittest.TestCase):
    def test_partial_equals_complete_file_regions(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'synthetic.fits.fz'
            image=np.random.default_rng(11).normal(size=(384,384)).astype('f4');image[90,100]=np.nan
            fits.HDUList([fits.PrimaryHDU(),fits.CompImageHDU(image,compression_type='RICE_1',tile_shape=(32,32))]).writeto(path)
            full=path.read_bytes()
            with fits.open(path,disable_image_compression=True) as hdus:
                h=hdus[1];prefix_end=h.fileinfo()['datLoc']+h.header['NAXIS1']*h.header['NAXIS2']
            prefix=full[:prefix_end]
            for x,y,w,h in [(75,70,90,100),(0,0,12,9),(375,371,9,13)]:
                p=plan_section(prefix,len(full),x,y,w,h)
                region,_=read_section(len(full),[(0,prefix),(p['start'],full[p['start']:p['end']+1])],p)
                with fits.open(path) as hdus:reference=hdus[1].data[y:y+h,x:x+w]
                self.assertTrue(np.array_equal(region,reference,equal_nan=True))
                self.assertEqual(region.dtype,reference.dtype)
                self.assertLess(len(prefix)+p['bytes'],len(full))
            with self.assertRaises(Stop):read_section(len(full),[(0,prefix)],p)
            with self.assertRaises(Stop):plan_section(prefix,len(full),380,380,20,20)

class GridTests(unittest.TestCase):
    def test_shifted_header_is_rejected(self):
        from c0_pipeline.range_experiment import grid_error_pixels
        h=fits.Header({'CTYPE1':'RA---TAN','CTYPE2':'DEC--TAN','CRPIX1':100.,'CRPIX2':100.,'CRVAL1':1.,'CRVAL2':2.,'CD1_1':-0.262/3600,'CD2_2':0.262/3600})
        sub=h.copy();sub['CRPIX1']-=20;sub['CRPIX2']-=30
        roi=dict(x0=20,y0=30,width=30,height=40)
        self.assertLess(grid_error_pixels(h,sub,roi),1e-5)
        sub['CRPIX1']+=1
        with self.assertRaises(Stop):grid_error_pixels(h,sub,roi)
