import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from astropy.io import fits
from c0_pipeline.core import Stop
from c0_pipeline.operator_support import (union,subtract,spline_axis,build_kernel,c_values,descriptor_table,
    LocalIO,save_checkpoint,load_checkpoint,geometry,coordinates,candidate_values,accumulate,
    packed,unpacked,cost_inventory,support_for_resource,offline_guard)

class IntervalTests(unittest.TestCase):
    def test_dedup_and_subtract(self):
        self.assertEqual(union([[8,10],[1,4],[3,8]]),[[1,10]])
        self.assertEqual(subtract([[1,10]],[[0,2],[5,7],[10,12]]),[[3,4],[8,9]])
        self.assertEqual(subtract([[1,3]],[[0,4]]),[])
    def test_invalid(self):
        with self.assertRaises(Stop):union([[4,1]])

class SplineTests(unittest.TestCase):
    def test_polynomial_tensor_axes(self):
        x=np.array([0.,.4,1.3,2.,3.1,4.]);t=np.linspace(0,4,41)
        for degree in range(4):np.testing.assert_allclose(spline_axis(x,x**degree,t),t**degree,atol=1e-12,rtol=1e-12)
        y=np.array([0.,.2,.8,1.7,2.]);z=x[:,None]**3+y[None,:]**2
        out=spline_axis(y,spline_axis(x,z,t).T,t[:10]).T
        np.testing.assert_allclose(out,t[:,None]**3+t[None,:10]**2,atol=1e-12,rtol=1e-12)
    def test_bad_nodes(self):
        with self.assertRaises(Stop):spline_axis([0,0,1,2],np.ones(4),[.2])

class DescriptorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        b=io.BytesIO();a=np.random.default_rng(11).normal(size=(64,64)).astype('f4');a[20,20]=np.nan
        fits.HDUList([fits.PrimaryHDU(),fits.CompImageHDU(a,compression_type='RICE_1',tile_shape=(16,16))]).writeto(b)
        cls.full=b.getvalue()
        with fits.open(io.BytesIO(cls.full),disable_image_compression=True) as hs:
            cls.header=hs[1].header.copy();cls.loc=hs[1].fileinfo()['datLoc'];cls.hloc=hs[1].fileinfo()['hdrLoc']
            cls.end=cls.loc+cls.header['NAXIS1']*cls.header['NAXIS2']
        cls.prefix=cls.full[:cls.end]
    def altered(self,key,value):
        h=self.header.copy();h[key]=value;prefix=bytearray(self.prefix)
        raw=h.tostring().encode('ascii');self.assertEqual(len(raw),self.loc-self.hloc)
        prefix[self.hloc:self.loc]=raw;return bytes(prefix)
    def test_bounds_and_exact_union(self):
        h,d,b=descriptor_table(self.prefix,len(self.full))
        self.assertEqual(len(d),16)
        for rr in d.values():
            for a,z in rr:self.assertGreaterEqual(a,b['heap_start']);self.assertLessEqual(z,b['heap_end'])
    def test_reject_corrupt_header(self):
        for key,value in [('THEAP',0),('PCOUNT',1),('PCOUNT',len(self.full)*2),('ZTILE1',0),('ZNAXIS1',99),('ZCMPTYPE','GZIP_1')]:
            with self.subTest(key=key,value=value),self.assertRaises(Stop):descriptor_table(self.altered(key,value),len(self.full))
    def test_incomplete_prefix(self):
        with self.assertRaises(Stop):descriptor_table(self.prefix[:-1],len(self.full))
    def test_heap_descriptor_cannot_point_into_padding_or_past_file(self):
        with fits.open(io.BytesIO(self.full),disable_image_compression=True) as hs:dt=hs[1].columns.dtype.newbyteorder('>')
        for val in [-1,2**30]:
            a=bytearray(self.prefix);table=np.frombuffer(a,dtype=dt,count=16,offset=self.loc)
            table['COMPRESSED_DATA'][0][1]=val
            with self.assertRaises(Stop):descriptor_table(bytes(a),len(self.full))

class CheckpointTests(unittest.TestCase):
    def test_roundtrip_changed_provenance_corruption_and_caps(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);budget=LocalIO(100000,100000);prov={'variants':['a']}
            save_checkpoint(folder,prov,{'value':1},{'v':np.ones(10)},budget)
            self.assertEqual(load_checkpoint(folder,prov,budget),{'value':1})
            with self.assertRaises(Stop):load_checkpoint(folder,{'variants':['b']},budget)
            meta=json.loads((folder/'checkpoint.json').read_text());(folder/meta['arrays_file']).write_bytes(b'corrupted')
            with self.assertRaises(Stop):load_checkpoint(folder,prov,budget)
            with self.assertRaises(Stop):LocalIO(1,1).read(folder/'checkpoint.json')
            with self.assertRaises(Stop):LocalIO(1,1).write(folder/'fail',b'xx')
            self.assertFalse((folder/'fail').exists())
    def test_network_guard(self):
        for event in ['socket.connect','socket.getaddrinfo','urllib.Request']:
            with self.assertRaises(Stop):offline_guard(event,())

class KernelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.fn,cls.build=build_kernel()
    def test_constant_identity_nan_and_edge_clipping(self):
        a=np.full((12,12),2.,np.float32)
        out=c_values(self.fn,a,[0,5,11],[0,5,11],[-.25,.25,.25],[.2,.3,.1])
        np.testing.assert_allclose(out,2,atol=64*np.finfo('f4').eps,rtol=0)
        a[:]=0;a[5,5]=1
        self.assertEqual(c_values(self.fn,a,[5],[5],[0],[0])[0],1)
        a[2,2]=np.nan
        self.assertTrue(np.isnan(c_values(self.fn,a,[5],[5],[.2],[.3])[0]))
    def test_lut_vs_direct_formula_synthetic_only(self):
        from c0_pipeline.normal_cutout import interpolate_interior
        a=np.random.default_rng(11).normal(size=(20,20)).astype('f4')
        x=np.linspace(6,12,41);y=np.linspace(7.125,11.375,41)
        ix=(x+.5).astype('i4');iy=(y+.5).astype('i4')
        c=c_values(self.fn,a,ix,iy,x-ix,y-iy)
        direct,_=interpolate_interior(a,x,y)
        # Smoke bound for a smooth LUT approximation; not a scientific acceptance tolerance.
        self.assertLess(float(np.max(np.abs(c-direct))),1e-5)
    def test_invalid_index(self):
        with self.assertRaises(Stop):c_values(self.fn,np.ones((4,4)),[4],[0],[0],[0])
    def test_known_vs_unknown_and_physical_clipping(self):
        shape=(2,2);g={'crop':[0,0,8,8],'direct':(np.zeros(shape,dtype='f4'),np.zeros(shape,dtype='f4')),'spline':(np.zeros(shape,dtype='f4'),np.zeros(shape,dtype='f4')),'emitted':np.ones(shape,bool)}
        p={'brick_x0':0,'brick_y0':0}
        v,k,a=candidate_values(self.fn,g,np.ones((4,4)),p,'direct_lut')
        self.assertTrue(k.all());np.testing.assert_allclose(v,1,atol=1e-6)
        v,k,a=candidate_values(self.fn,g,np.ones((3,3)),p,'direct_lut')
        self.assertFalse(k.any())

class AccumulationTests(unittest.TestCase):
    def test_finite_rejection_zero_unknown_and_order(self):
        vs=np.array([[2,np.nan,2],[4,np.nan,4.]])
        ks=np.array([[True,True,True],[True,True,False]]);act=np.ones_like(ks)
        r,s,w=accumulate(vs,ks,act)
        self.assertEqual(r[0],3);self.assertEqual(r[1],0);self.assertTrue(np.isnan(r[2]));self.assertEqual(w[1],0)
        vals=[np.array([1e20]),np.array([-1e20]),np.array([1.])];known=[np.array([True])]*3
        a,_,_=accumulate(vals,known,known);b,_,_=accumulate(vals,known,known,reverse=True)
        self.assertNotEqual(a[0],b[0])

class GeometryTests(unittest.TestCase):
    def test_same_tan_center(self):
        h=fits.Header({'NAXIS1':256,'NAXIS2':256,'CTYPE1':'RA---TAN','CTYPE2':'DEC--TAN','CRPIX1':128.5,'CRPIX2':128.5,'CRVAL1':185.,'CRVAL2':16.,'CD1_1':-.262/3600,'CD2_2':.262/3600})
        g=geometry(h,h);x,y,ix,iy,a=coordinates(g,'spline_lut')
        yy,xx=np.indices((256,256));np.testing.assert_allclose(x,xx,atol=1e-5);np.testing.assert_allclose(y,yy,atol=1e-5)
        self.assertTrue(a.all())

class CostTests(unittest.TestCase):
    def test_dedup_and_joint_coverage(self):
        m=np.zeros((256,256),bool);m[0,0]=True
        other=m.copy();other[0,1]=True
        sp=dict(url='https://example.invalid/f',etag='"fixed"',total_bytes=100,cached_ranges=[[0,19]],local_fragments=[],native_regions=[],heap_bounds={},active_mask=packed(other),
                tiles=[dict(missing_ranges=[[20,24],[30,34]],missing_dependency_mask=packed(m))])
        rows=[dict(rank=1,band='g',support=[sp]),dict(rank=2,band='g',support=[sp])]
        cost=cost_inventory(rows,dict(bytes=0,data_requests=0),{sp['url']:3})
        self.assertEqual(cost['conditional_minimum_payload_bytes'],10);self.assertEqual(cost['single_range_requests_at_minimum_bytes'],2)
        self.assertFalse(cost['within_per_url_attempts'])
        for interval in cost['resources'][0]['ranges']:
            self.assertTrue(all(r['newly_complete_if_only_this_range_added']==0 for r in interval['coverage']))
        self.assertEqual(cost['coverage'][0]['currently_supported_pixels'],1)
    def test_native_roi_prevents_unnecessary_tile_request(self):
        shape=(2,2);zero=np.zeros(shape,dtype='f4');g=dict(crop=[0,0,8,8],direct=(zero,zero),spline=(zero,zero),emitted=np.ones(shape,bool),spline_used=False,grid=[])
        h={'ZTILE1':8,'ZTILE2':8,'ZNAXIS1':8,'ZNAXIS2':8};res={'url':'u','etag':'e','total_bytes':100,'range_events':[{'range_start':0,'range_end':19}]}
        r=support_for_resource(g,h,{0:[[20,29]]},res,[dict(x0=0,y0=0,width=4,height=4)])
        self.assertEqual(r['tiles'][0]['missing_bytes'],0)
        r=support_for_resource(g,h,{0:[[20,29]]},res,[])
        self.assertEqual(r['tiles'][0]['missing_bytes'],10)

if __name__=='__main__':unittest.main()
