import contextlib
import csv
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from oc3lib.core import *
from oc3lib.transport import *
from oc3lib.arrays import *
from oc3lib.selection import *
from oc3lib.statistics import *
from oc3lib.workflow import *
import oc3_pilot

PROJECT=Path(__file__).resolve().parents[2]

class FakeResponse:
 def __init__(self,body,url='https://synthetic.invalid/resource',status=200,headers=None,fail_after=None):
  self.body=body;self.pos=0;self.status=status;self.final_url=url;self.fail_after=fail_after
  self.headers={'content-length':str(len(body)),'etag':'"fixture-v1"',**(headers or {})}
 def read(self,n):
  if self.fail_after is not None and self.pos>=self.fail_after: raise OSError('synthetic interruption')
  stop=min(len(self.body),self.pos+n)
  if self.fail_after is not None: stop=min(stop,self.fail_after)
  ans=self.body[self.pos:stop];self.pos=stop;return ans
 def close(self): pass

class FakeTransport:
 def __init__(self,responses):self.responses=list(responses);self.calls=[]
 def open(self,url,headers):
  self.calls.append((url,headers));return self.responses.pop(0)

def resource(body=b'abcdefgh'):
 return dict(id='SYNTHETIC_ONLY',url='https://synthetic.invalid/resource',category='product',product='image',stage='fixed',generation='fixture-v1',release='DR9',max_bytes=len(body),size=len(body),sha256=digest(body),etag='"fixture-v1"')

def header(shape=(129,129)):
 h=fits.Header();h['CTYPE1']='RA---TAN';h['CTYPE2']='DEC--TAN';h['CRPIX1']=100.;h['CRPIX2']=100.;h['CRVAL1']=25.;h['CRVAL2']=10.;h['CD1_1']=-.262/3600;h['CD1_2']=0.;h['CD2_1']=0.;h['CD2_2']=.262/3600;h['BUNIT']='synthetic'
 return h

def states_for(a):
 return pixel_states(a,np.ones(a.shape),np.full(a.shape,2),np.zeros(a.shape,dtype='uint16'),np.ones(a.shape,dtype=bool))

class Base(unittest.TestCase):
 def setUp(self): self.tmp=tempfile.TemporaryDirectory(prefix='oc3_SYNTHETIC_ONLY_');self.root=Path(self.tmp.name);self.ledgers=[]
 def tearDown(self):
  for ledger in self.ledgers:
   try:ledger.close()
   except Exception:pass
  self.tmp.cleanup()
 def ledger(self,**caps):
  ledger=Ledger(self.root/'ledger.sqlite',{'synthetic':True},caps);self.ledgers.append(ledger);return ledger

class AuthorityAndSchemaTests(Base):
 def test_frozen_authorities_match(self):self.assertEqual(len(verify_authorities(PROJECT)),7)
 def copy_authorities(self):
  for name in [*AUTHORITIES,'AGENTS.md']:shutil.copyfile(PROJECT/name,self.root/name)
 def test_hash_mismatch_stops(self):
  self.copy_authorities();(self.root/next(iter(AUTHORITIES))).write_text('SYNTHETIC CORRUPTION')
  with self.assertRaises(IntegrityError):verify_authorities(self.root)
 def test_amendment_required(self):
  self.copy_authorities();(self.root/'OC3_DR9_COADD_BOUNDED_PILOT_SPEC_AMENDMENT_001.md').unlink()
  with self.assertRaises(IntegrityError):verify_authorities(self.root)
 def test_registry_refuses_authority_mix(self):
  a=self.ledger();a.close()
  with self.assertRaises(IntegrityError):Ledger(self.root/'ledger.sqlite',{'changed':True})
 def test_extra_selection_columns_rejected(self):
  for col in ('TYPE','vote_fraction','zoobot_prediction','redshift','stellar_mass'):
   with self.assertRaises(InputError):strict({'region':'south',col:0},'brick')
 def test_lockbox_paths_and_symlinks_rejected(self):
  for name in ('INTERPRETATION_LOCKBOX','final_holdout','zoobot'):
   with self.assertRaises(InputError):safe_path(self.root/name)
  target=self.root/'final_holdout';target.mkdir();(self.root/'alias').symlink_to(target)
  with self.assertRaises(InputError):safe_path(self.root/'alias')
 def test_all_artifact_contracts_are_named(self):self.assertEqual(len(ARTIFACTS),26)
 def test_unknown_artifact_rejected(self):
  with self.assertRaises(InputError):artifact_path(self.root,'invented.json')

class NetworkLedgerTests(Base):
 def test_offline_has_no_transport_capability(self):
  ledger=self.ledger();before=ledger.summary()
  with self.assertRaises(OfflineError):Acquisition(self.root,ledger).fetch(resource())
  self.assertEqual(before,ledger.summary())
 def test_real_socket_guard(self):
  import socket
  with self.assertRaises(AssertionError):socket.getaddrinfo('synthetic.invalid',443)
 def test_limit_increases_all_rejected(self):
  for name,maximum in MAXIMA.items():
   with self.assertRaises(LimitError):limits({name:maximum+1})
 def test_limits_may_only_lower(self):self.assertEqual(limits({'bytes':100,'retries':0})['retries'],0)
 def test_ledger_cumulative_across_reopen(self):
  a=self.ledger(bytes=40);token=a.reserve('first','metadata',10);a.received(token,7);a.finish(token,'COMPLETE');a.close()
  b=self.ledger();self.assertEqual(b.count('bytes'),7);self.assertEqual(b.count('requests'),1);self.assertEqual(b.caps['bytes'],40)
 def test_reservation_prevents_request(self):
  ledger=self.ledger(bytes=4);mock=FakeTransport([FakeResponse(b'abcdefgh')])
  with self.assertRaises(LimitError):Acquisition(self.root,ledger,mock).fetch(resource())
  self.assertEqual(mock.calls,[]);self.assertEqual(ledger.count('requests'),0)
 def test_unbounded_reservation_rejected(self):
  for size in (None,-1,0):
   with self.assertRaises(LimitError):self.ledger().reserve('x','product',size)
 def test_metadata_and_psf_subbudgets(self):
  ledger=self.ledger(metadata_bytes=2,psf_bytes=2)
  for cat in ('metadata','psf'):
   with self.assertRaises(LimitError):ledger.reserve(cat,cat,3)
 def test_partial_failure_body_counted(self):
  ledger=self.ledger();mock=FakeTransport([FakeResponse(b'12345678',status=500)])
  with self.assertRaises(InputError):Acquisition(self.root,ledger,mock).fetch(resource())
  self.assertEqual(ledger.count('bytes'),8);self.assertEqual(ledger.resource('SYNTHETIC_ONLY')['offset'],0)
 def test_interruption_resume_exact(self):
  body=b'abcdefgh';res=resource(body);ledger=self.ledger()
  first=FakeTransport([FakeResponse(body,fail_after=4)])
  with self.assertRaises(OSError):Acquisition(self.root,ledger,first).fetch(res)
  self.assertEqual(ledger.count('bytes'),4);self.assertEqual(ledger.resource(res['id'])['offset'],4)
  second=FakeTransport([FakeResponse(body[4:],status=206,headers={'content-range':'bytes 4-7/8'})])
  path=Acquisition(self.root,ledger,second).fetch(res,resume=True)
  self.assertEqual(path.read_bytes(),body);self.assertEqual(second.calls[0][1]['Range'],'bytes=4-')
  self.assertEqual(ledger.count('bytes'),8);self.assertEqual(ledger.count('requests'),2)
  before=ledger.count('requests');Acquisition(self.root,ledger,FakeTransport([])).fetch(res,True)
  self.assertEqual(ledger.count('requests'),before)
 def test_cache_conflict_not_overwritten(self):
  ledger=self.ledger();res=resource();path=Acquisition(self.root,ledger,FakeTransport([FakeResponse(b'abcdefgh')])).fetch(res)
  path.write_bytes(b'corrupted')
  with self.assertRaises(IntegrityError):Acquisition(self.root,ledger,FakeTransport([])).fetch(res,True)
  self.assertEqual(path.read_bytes(),b'corrupted')
 def test_generation_separation(self):
  ledger=self.ledger();res=resource();ledger.register(res)
  with self.assertRaises(IntegrityError):ledger.register(dict(res,generation='other'))
 def test_immutable_write_conflict(self):
  p=self.root/'evidence';immutable_write(p,b'first')
  with self.assertRaises(IntegrityError):immutable_write(p,b'other')
  self.assertEqual(p.read_bytes(),b'first')
 def test_crash_reservation_stays_charged(self):
  ledger=self.ledger();ledger.reserve('crash','metadata',10);ledger.recover()
  self.assertEqual(ledger.count('bytes'),10);self.assertEqual(ledger.summary()['attempts'][0]['state'],'CRASH_CHARGED')
 def test_retry_limit(self):
  ledger=self.ledger()
  for _ in range(3):t=ledger.reserve('same','product',1);ledger.finish(t,'FAILED')
  with self.assertRaises(LimitError):ledger.reserve('same','product',1)
 def test_concurrency_one(self):
  ledger=self.ledger();ledger.reserve('one','product',1)
  with self.assertRaises(IntegrityError):ledger.reserve('two','product',1)
 def test_unknown_size_bounded(self):
  ledger=self.ledger();res=resource();res.pop('size');res.pop('sha256')
  response=FakeResponse(b'abcdefgh');response.headers.pop('content-length')
  with self.assertRaises(LimitError):Acquisition(self.root,ledger,FakeTransport([response])).fetch(res)
  self.assertEqual(ledger.count('bytes'),8)
 def test_oversized_declared_body_aborted(self):
  ledger=self.ledger();response=FakeResponse(b'x'*100)
  with self.assertRaises(LimitError):Acquisition(self.root,ledger,FakeTransport([response])).fetch(resource())
  self.assertEqual(response.pos,0)
 def test_range_ignored_is_not_downloaded(self):
  ledger=self.ledger();res=resource()
  with self.assertRaises(OSError):Acquisition(self.root,ledger,FakeTransport([FakeResponse(b'abcdefgh',fail_after=4)])).fetch(res)
  response=FakeResponse(b'abcdefgh')
  with self.assertRaises(IntegrityError):Acquisition(self.root,ledger,FakeTransport([response])).fetch(res,True)
  self.assertEqual(response.pos,0)
 def test_resource_url_must_be_explicit(self):
  with self.assertRaises(InputError):validate_resource(resource(),['other.invalid'])
 def test_disk_and_io_limits(self):
  ledger=self.ledger(disk_bytes=10,io_bytes=10);guard=RuntimeGuard(ledger,self.root)
  with self.assertRaises(LimitError):guard.reserve_disk(11)
  with self.assertRaises(LimitError):ledger.charge('io_bytes',11)

class CLITests(Base):
 def call(self,args):
  with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()): return oc3_pilot.main(args)
 def test_help(self):
  with self.assertRaises(SystemExit) as c:
   with contextlib.redirect_stdout(io.StringIO()):oc3_pilot.main(['--help'])
  self.assertEqual(c.exception.code,0)
 def test_dry_run_no_mutation_or_network(self):
  before=list(self.root.rglob('*'))
  with patch.object(HTTPTransport,'open',side_effect=AssertionError('NETWORK')),patch('oc3lib.arrays.read_fits',side_effect=AssertionError('DECODE')):
   self.assertEqual(self.call(['plan','--inputs',str(self.root/'missing.json'),'--dry-run','--offline','--root',str(self.root)]),0)
  self.assertEqual(before,list(self.root.rglob('*')))
 def test_offline_acquisition_no_side_effects(self):
  self.assertEqual(self.call(['acquire-aux','--offline','--root',str(self.root)]),21)
  self.assertEqual(list(self.root.iterdir()),[])
 def test_cli_cannot_raise_budget(self):self.assertEqual(self.call(['plan','--inputs','missing.json','--dry-run','--max-global-requests','201']),22)
 def test_conflicting_network_flags(self):self.assertEqual(self.call(['plan','--inputs','missing.json','--offline','--execute-network']),21)
 def test_synthetic_integrity_cli_stop(self):
  self.assertEqual(self.call(['plan','--inputs','missing.json','--project',str(self.root),'--dry-run']),20)
 def test_no_199_cli_option(self):
  with self.assertRaises(SystemExit) as c:
   with contextlib.redirect_stderr(io.StringIO()):oc3_pilot.main(['analyze','--permutations','199'])
  self.assertEqual(c.exception.code,2)

class SelectionTests(Base):
 def fixture(self):
  shape=(385,385);y,x=np.indices(shape)
  nexp={b:np.where(x<100,0,2).astype('int16') for b in BANDS};nexp['g'][100:150]=1
  psf={b:(1+x/385+(i*.2)) for i,b in enumerate(BANDS)}
  masks=np.zeros(shape,dtype='uint16');masks[180:190,100:110]=1<<2
  bundles={r:AuxiliaryBundle(nexp,psf,masks) for r in ('south','north')}
  geo={r:PixelRectangle([64,64,320,320]) for r in bundles}
  bricks=[dict(region=r,brickname='SYNTHETIC_'+r) for r in bundles]
  return bricks,bundles,geo
 def test_technical_grid_and_window(self):
  self.assertEqual(technical_grid((130,130))[:4],[(0,0),(64,0),(128,0),(129,0)])
  self.assertEqual(crop(np.zeros((200,200)),100,100)[0].shape,(129,129))
 def test_selector_cannot_accept_image(self):
  with self.assertRaises(InputError):AuxiliaryBundle.from_mapping({'image':np.zeros((2,2))})
 def test_selection_independent_of_image(self):
  b,a,g=self.fixture();image=np.zeros((385,385));first,_=select_slots(b,a,g);image[:]=1e30;second,_=select_slots(b,a,g)
  self.assertEqual(first,second)
 def test_all_six_slots_deterministic_and_distinct(self):
  b,a,g=self.fixture();rows,flow=select_slots(b,a,g)
  self.assertEqual([r['slot'] for r in rows],list(SLOTS));self.assertTrue(all('x' in r for r in rows))
  self.assertEqual(len({(r['region'],r['x'],r['y']) for r in rows}),6)
  for row in rows:self.assertEqual(row['selection_hash'],tie(row['slot'],row['region'],row['brick'],row['x'],row['y']))
 def test_no_replacement_when_mask_absent(self):
  b,a,g=self.fixture();a={r:AuxiliaryBundle(x.nexp,x.psfsize,np.zeros_like(x.maskbits)) for r,x in a.items()}
  rows,_=select_slots(b,a,g);self.assertEqual(rows[2]['status'],'NOT_AVAILABLE');self.assertEqual(len(rows),6)
 def test_variation_not_exercised(self):
  b,a,g=self.fixture();a={r:AuxiliaryBundle(x.nexp,{band:np.ones((385,385)) for band in BANDS},x.maskbits) for r,x in a.items()}
  rows,_=select_slots(b,a,g);self.assertEqual(rows[-1]['status'],'STRATUM_NOT_EXERCISED')
 def test_brick_hash_sort_independent_of_input_order(self):
  rows=[dict(region=r,brickname=n,generation='9012' if r=='south' else '9011',release='DR9',grz=True,corrected_9012=r=='south') for r in ('south','north') for n in ('SYN_A','SYN_B')]
  allowed={(r['region'],r['brickname']) for r in rows}
  self.assertEqual(choose_bricks(rows,allowed),choose_bricks(rows[::-1],allowed))

class ArrayTests(Base):
 def test_zero_missing_unknown_distinct(self):
  a=np.zeros((1,3));present=np.array([[True,False,True]])
  rows=pixel_states(a,np.ones(a.shape),np.ones(a.shape,dtype=int),np.array([[0,0,1<<20]],dtype='uint32'),np.ones(a.shape,dtype=bool),present)
  self.assertEqual(rows[0]['validity_state'],'zero_with_unresolved_validity')
  self.assertEqual(rows[1]['validity_state'],'ABSENT');self.assertIsNone(rows[1]['image_zero'])
  self.assertEqual(rows[2]['unknown_bits'],1<<20);self.assertEqual(rows[2]['quality_evidence'],'UNKNOWN')
 def test_valid_zero_requires_independent_evidence(self):
  a=np.zeros((1,1));rows=pixel_states(a,np.ones((1,1)),np.ones((1,1)),np.zeros((1,1),dtype='int16'),np.ones((1,1),bool),validity_evidence=np.array([['INDEPENDENT_VALIDITY_VERIFIED']]))
  self.assertEqual(rows[0]['validity_state'],'valid_zero')
 def test_positive_weight_not_clean(self):
  row=states_for(np.ones((1,1)))[0]
  self.assertEqual(row['validity_state'],'supported_unflagged_candidate');self.assertEqual(row['quality_evidence'],'NO_RECORDED_FLAGS_NOT_CLEAN')
 def test_crop_exact_no_cast_or_interpolation(self):
  a=np.arange(40000,dtype='float64').reshape(200,200);a[100,100]=np.nan
  out,win=crop(a,100,100)
  self.assertEqual(out.dtype,a.dtype);self.assertEqual(out.tobytes(),a[36:165,36:165].tobytes());self.assertTrue(np.isnan(out[64,64]))
 def test_partial_no_padding(self):
  a=np.arange(400,dtype='uint16').reshape(20,20);out,win=crop(a,0,0)
  self.assertEqual(out.shape,(20,20));self.assertEqual(win['requested'],[-64,-64,65,65]);self.assertEqual(win['offset_in_requested'],[64,64]);np.testing.assert_array_equal(a,out)
 def test_wcs_translation(self):
  h=header();new=translate_header(h,[7,11]);self.assertEqual(new['CRPIX1'],93);self.assertEqual(new['CRPIX2'],89)
  np.testing.assert_allclose(WCS(h).all_pix2world([[17,31]],0),WCS(new).all_pix2world([[10,20]],0),atol=1e-12,rtol=0)
 def test_integer_maskbits_preserved(self):
  a=np.arange(40000,dtype='uint32').reshape(200,200);out,_=crop(a,100,100);np.testing.assert_array_equal(out,a[36:165,36:165]);self.assertEqual(out.dtype,a.dtype)
 def test_synthetic_fits_read_and_crop(self):
  p=self.root/'SYNTHETIC.fits';a=np.arange(40000,dtype='float64').reshape(200,200);a[50,60]=np.nan;fits.PrimaryHDU(a,header()).writeto(p)
  arr,h,meta=read_fits(p,0);out,w=crop(arr,100,100);q=self.root/'SYNTHETIC_crop.fits';write_crop_fits(q,out,h,w['integer_offset']);again,_,_=read_fits(q,0)
  self.assertEqual(array_hash(out),array_hash(again));self.assertEqual(meta['bitpix'],-64);self.assertEqual(meta['hdu'],0)
 def test_scaled_integer_fits(self):
  p=self.root/'SYNTHETIC_uint.fits';a=np.array([[0,65535]],dtype='uint16');fits.PrimaryHDU(a,header()).writeto(p)
  got,h,meta=read_fits(p,0);np.testing.assert_array_equal(got,a);self.assertEqual(meta['bzero'],32768)
 def test_state_parquet_preserves_null(self):
  rows=pixel_states(np.zeros((1,1)),np.zeros((1,1)),np.zeros((1,1)),np.zeros((1,1),dtype=int),np.zeros((1,1),bool),present=np.zeros((1,1),bool))
  p=self.root/'SYNTHETIC.parquet';save_states(p,rows)
  import pyarrow.parquet as pq
  self.assertIsNone(pq.read_table(p).to_pylist()[0]['finite_image'])
 def test_lookup_distortion_refused(self):
  h=header();h['CPDIS1']='LOOKUP'
  with self.assertRaises(InputError):translate_header(h,[1,1])
 def test_canonical_hash_reproduction(self):
  a=np.arange(40000,dtype='int32').reshape(200,200);first=crop(a,100,100)[0];second=crop(a.copy(),100,100)[0]
  self.assertEqual(array_hash(first),array_hash(second))

class PSFTests(Base):
 def psf(self):
  y,x=np.indices((31,31));return np.exp(-((x-15)**2+(y-15)**2)/8)
 def test_psf_not_renormalized(self):
  a=self.psf()*7;before=a.copy();r=psf_diagnostics(a,[15,15],.262)
  np.testing.assert_array_equal(a,before);self.assertAlmostEqual(r['sum_S'],a.sum());self.assertTrue(r['positive_definite']);self.assertEqual(r['status'],'INTERPRETABLE');self.assertAlmostEqual(r['F_mom'],2*np.sqrt(2*np.log(2))*2*.262,places=6)
 def test_negative_values_recorded_not_clipped(self):
  a=self.psf();a[0,0]=-.01;r=psf_diagnostics(a,[15,15],.262)
  self.assertEqual(r['negative_count'],1);self.assertEqual(r['min'],-.01);self.assertEqual(a[0,0],-.01)
 def test_ambiguous_crossings(self):
  r=half_width([0,6,0,10,0,6,0],3);self.assertIsNone(r['width']);self.assertEqual(r['status'],'AMBIGUOUS_CROSSINGS')
 def test_engineering_guards_not_morphology(self):
  d=psf_diagnostics(self.psf(),[15,15],.262);g=engineering_guards(np.ones((5,5)),[d]*3,.262)
  self.assertEqual(g['kind'],'PILOT_ENGINEERING_GUARD');self.assertEqual(g['morphology_preservation'],'NOT_ESTABLISHED');self.assertFalse(g['mip_pass'])
 def test_nonpositive_psf_sum_not_auditable(self):self.assertEqual(psf_diagnostics(-self.psf(),[15,15],.262)['status'],'NOT_AUDITABLE')

class StatisticsTests(Base):
 def test_rng_fixed_golden_raw_output(self):
  expected=[15103153937790353826,3381533215772834288,11464804611551965358,16723861768261421164,3098731626337405311,13823982838243910342,14279926451266702186,4616443153853420997]
  self.assertEqual(rng_for('S1','g').bit_generator.random_raw(8).tolist(),expected)
 def test_substreams_order_independent(self):
  first=rng_for('S1','g').random(10);rng_for('N3','z').random(1000)
  np.testing.assert_array_equal(first,rng_for('S1','g').random(10));self.assertFalse(np.array_equal(first,rng_for('S1','r').random(10)))
 def test_omnibus_hand_calculation(self):
  m=np.array([[.1,-.2],[.3,-.4],[.5,-.6],[.7,-.8]])
  out=omnibus_summary(m);self.assertAlmostEqual(out['T'],.5);self.assertAlmostEqual(out['IQR_R'],.3);self.assertEqual(out['max_R'],.8);self.assertTrue(out['auditable'])
 def test_fewer_four_blocks(self):
  a=np.arange(32*96,dtype=float).reshape(32,96);rows,u=t10(a,states_for(a),'S1','g')
  self.assertEqual(u['inference'],NOT_AUDITABLE);self.assertIsNone(u['p_raw']);self.assertEqual(u['permutations'],0)
 def test_199_impossible(self):
  with self.assertRaises(InputError):p_value(1,np.zeros(199))
 def test_pmin_and_ties(self):
  self.assertEqual(p_value(1,np.zeros(999)),.001);self.assertEqual(p_value(1,np.ones(999)),1)
 def test_holm_ties_exact(self):
  units=[dict(row_type='omnibus',slot=s,band='g',auditable=True,p_raw=p) for s,p in [('N1',.03),('S2',.001),('S1',.001)]]
  holm(units);lookup={u['slot']:u for u in units};self.assertEqual(lookup['S1']['p_holm'],.003);self.assertEqual(lookup['S2']['p_holm'],.003);self.assertEqual(lookup['N1']['p_holm'],.03);self.assertEqual(lookup['S1']['holm_rank'],1)
 def test_no_descriptive_inference(self):
  a=np.arange(129*129,dtype=float).reshape(129,129);rows=descriptive_rows(a,states_for(a),'S1','g')
  self.assertTrue(all('p_raw' not in row and row['row_type']=='descriptive' for row in rows))
  self.assertEqual(len([r for r in rows if r['stratum']=='all_finite']),160)
  with self.assertRaises(InputError):holm(rows[:1])
 def test_block_alignment_partial_domain(self):
  a=np.zeros((100,100));blocks,ids=blocks_for(a,(29,29));self.assertEqual(ids,[5,6,7,9,10,11,13,14,15])
 def test_no_source_masking_correlation(self):
  a=np.arange(256,dtype=float);r=correlation(a,a*2+9);self.assertEqual(r['pair_count'],256);self.assertAlmostEqual(r['r'],1)
 def test_full_999_synthetic_omnibus_and_reproduction(self):
  y,x=np.indices((129,129));a=(x+y*.01).astype('float64');states=states_for(a)
  before=a.copy();rows,u=t10(a,states,'S1','g');rows2,u2=t10(a,states,'S1','g')
  np.testing.assert_array_equal(a,before);self.assertEqual(u['permutations'],999);self.assertEqual(u['p_raw'],.001)
  self.assertEqual(hash_object(rows+[u]),hash_object(rows2+[u2]));self.assertEqual(len(u['permutation_estimability']),999)
  self.assertEqual(len(u['fixed_class_partition']),16);self.assertEqual(len(u['observed_r_jl']),16)
  self.assertEqual(sum(c['coordinate_count'] for b in u['fixed_class_partition'] for c in b['classes']),16384)
  holm([u]);self.assertEqual(u['inference'],DETECTED)
 def test_state_classes_are_fixed(self):
  a=np.ones((129,129));rows=states_for(a);keys=state_keys(rows,a.shape)
  self.assertEqual(keys[0,0],json.dumps([rows[0][k] for k in STATE_AXES],separators=(',',':')))

class DecisionTests(Base):
 def records(self,domain):return [test_result(f'T{i:02}','VERIFIED','SYNTHETIC_ONLY',{'synthetic':True},domain=domain) for i in range(1,13)]
 def test_synthetic_A(self):self.assertEqual(decide(self.records('full'),full_slots=True,rights=True),OUTCOMES[0])
 def test_synthetic_B(self):self.assertEqual(decide(self.records('restricted'),restricted_slots=True,rights=True),OUTCOMES[1])
 def test_synthetic_C_unknown(self):self.assertEqual(decide([],full_slots=True,rights=True),OUTCOMES[2])
 def test_synthetic_D_integrity(self):self.assertEqual(decide(self.records('full'),integrity=True,full_slots=True,rights=True),OUTCOMES[3])
 def test_contradiction_blocks_A(self):
  records=self.records('full');records[0]['status']='CONTRADICTED';self.assertEqual(decide(records,full_slots=True,rights=True),OUTCOMES[2])
 def test_no_pending_or_unrecognized_test_status(self):
  with self.assertRaises(InputError):test_result('T10','PENDING','SYNTHETIC',{})
 def test_rights_not_assumed(self):self.assertEqual(decide(self.records('full'),full_slots=True,rights=False),OUTCOMES[2])

class WorkflowTests(Base):
 def manifest(self,deferred=False):
  allow=self.root/'OC3_DEVELOPMENT_BRICKS.csv'
  allow.write_text('region,brickname,development,holdout_disjoint,evidence_ref\nsouth,SYNTHETIC_S,true,true,synthetic\nnorth,SYNTHETIC_N,true,true,synthetic\n')
  bricks=[dict(region=r,brickname=n,generation='9012' if r=='south' else '9011',release='DR9',grz=True,corrected_9012=r=='south',primary_bounds=[24.99,9.99,25.01,10.01]) for r,n in [('south','SYNTHETIC_S'),('north','SYNTHETIC_N')]]
  obj=seal(dict(schema_version=1,execution_kind='SYNTHETIC',allowlist_path=str(allow),allowlist_sha256=file_hash(allow),bricks=bricks,resources=[],rights=dict(analysis=True,local_preservation=True,evidence_refs=['SYNTHETIC_ONLY']),semantics=[],release_issues=[],approved_hosts=['synthetic.invalid'],deferred_psf=deferred))
  path=self.root/'OC3_INPUT_MANIFEST.json';write_json(path,obj)
  return path,obj
 def run_fixture(self,deferred=False):
  path,inp=self.manifest(deferred);plan=build_plan(PROJECT,path)
  run=Run(PROJECT,self.root/'run',plan,inp);self.ledgers.append(run.ledger)
  rows=[dict(slot=slot,status='NOT_AVAILABLE',reason='SYNTHETIC_ONLY') for slot in SLOTS]
  artifact(run.root,'OC3_LOCATIONS.json',dict(binding=run.binding,locations=rows,selection_sha256=hash_object(rows)))
  return run
 def test_plan_reconstruction_and_binding(self):
  path,inp=self.manifest();plan=build_plan(PROJECT,path);out=self.root/'plan.json';write_json(out,plan)
  self.assertEqual(validate_plan(PROJECT,out)[0],plan)
 def test_nested_forbidden_columns_fail_closed(self):
  path,inp=self.manifest();inp['rights']['vote_fraction']=.5
  path.write_bytes(canonical(seal(inp)))
  with self.assertRaises(InputError):read_inputs(path)
 def test_deferred_psf_budget_reserved_prospectively(self):
  path,_=self.manifest(True)
  with self.assertRaises(LimitError):build_plan(PROJECT,path,{'bytes':54*2**20-1})
  with self.assertRaises(LimitError):build_plan(PROJECT,path,{'requests':53})
 def test_synthetic_root_cannot_masquerade_as_production(self):
  path,inp=self.manifest();plan=build_plan(PROJECT,path)
  with self.assertRaises(InputError):Run(PROJECT,PROJECT/'oc3',plan,inp)
 def test_all_missing_units_reproduce_and_close_C_only_synthetic(self):
  run=self.run_fixture();run.analyze();run.verify()
  report=load_json(artifact_path(run.root,'OC3_TEST_LEDGER.json'))
  self.assertEqual(len(report['records']),72)
  self.assertTrue(all(r['status']=='NOT_EXERCISED' for r in report['records']))
  self.assertEqual(run.finalize(),OUTCOMES[2]);self.assertEqual(run.ledger.count('requests'),0)
 def test_deferred_links_require_selection_binding(self):
  run=self.run_fixture(True)
  obj=seal(dict(binding=run.binding,selection_sha256='wrong',resources=[],unavailable=[]))
  path=artifact_path(run.root,'OC3_PSF_LINKS.json');write_json(path,obj)
  with self.assertRaises(IntegrityError):run.load_psf_links(path)
 def test_deferred_links_missing_blocks_before_network(self):
  run=self.run_fixture(True);mock=FakeTransport([])
  with self.assertRaises(InputError):run.acquire('fixed',mock)
  self.assertEqual(mock.calls,[])
 def test_deferred_links_replay_and_immutability(self):
  run=self.run_fixture(True);obj=seal(dict(binding=run.binding,selection_sha256=run.locations()['selection_sha256'],resources=[],unavailable=[]))
  path=artifact_path(run.root,'OC3_PSF_LINKS.json');write_json(path,obj);run.load_psf_links(path)
  run.acquire('fixed',FakeTransport([]));self.assertEqual(run.ledger.count('requests'),0)
  obj['unavailable']=[dict(location=['S1',0,0],band='g',reason='synthetic',evidence_refs=['synthetic'])]
  path.write_bytes(canonical(seal(obj)))
  with self.assertRaises(InputError):run.load_psf_links(path)
 def test_psf_exact_one_mib_limit(self):
  res=dict(resource(),category='psf',product='psf',band='g',max_bytes=2**20+1)
  with self.assertRaises(LimitError):validate_resource(res,['synthetic.invalid'])
 def test_aux_stage_cannot_open_image(self):
  with self.assertRaises(InputError):validate_resource(dict(resource(),stage='aux'),['synthetic.invalid'])
 def test_psfsize_profiles_no_smoothing(self):
  a=np.arange(1,10,dtype=float).reshape(3,3);d=psfsize_descriptors(a)
  self.assertEqual(d['profiles_x'],a.tolist());self.assertEqual(d['profiles_y'],a.T.tolist())
  self.assertEqual(d['median'],5);self.assertAlmostEqual(d['q05'],1.4)
 def test_psf_comparison_does_not_claim_agreement(self):
  d=compare_psfsize(2.,{'F_mom':3.},1.)
  self.assertEqual(d['differences']['F_mom'],{'absolute':1.,'relative':.5})
  self.assertIn('NOT_ASSUMED_EQUAL',d['interpretation'])
 def test_three_psf_positions_required_for_guard(self):
  d={'edge_absolute_fraction':0.,'status':'INTERPRETABLE'}
  self.assertFalse(engineering_guards(np.ones((3,3)),[d],.262)['satisfied'])

class IntegratedFixtureTests(WorkflowTests):
 # Avoid inheriting/recounting the parent tests; this class supplies one composed fixture below.
 def test_native_synthetic_bundle_acquire_analyze_verify(self):
  path,inp=self.manifest();items=[];responses=[]
  for product in ('image','invvar','nexp','psfsize','maskbits'):
   for band in ([None] if product=='maskbits' else BANDS):
    dtype='uint16' if product=='maskbits' else 'int16' if product=='nexp' else 'float32'
    a=np.full((257,257),0 if product=='maskbits' else 2,dtype=dtype)
    if product=='image': a[100,100]=np.nan
    buf=io.BytesIO();fits.PrimaryHDU(a,header=header()).writeto(buf);body=buf.getvalue()
    rid=f'SYNTHETIC_{product}_{band}';url='https://synthetic.invalid/'+rid
    res=dict(id=rid,url=url,category='product',product=product,stage='fixed' if product in ('image','invvar') else 'aux',generation='9012',release='DR9',region='south',brick='SYNTHETIC_S',band=band,hdu=0,size=len(body),max_bytes=len(body),sha256=digest(body),etag='"fixture-v1"')
    items.append(res);responses.append(FakeResponse(body,url=url))
  inp['resources']=items;path.write_bytes(canonical(seal(inp)))
  plan=build_plan(PROJECT,path);run=Run(PROJECT,self.root/'run',plan,inp);self.ledgers.append(run.ledger)
  rows=[dict(slot=slot,status='NOT_AVAILABLE',reason='SYNTHETIC_ONLY') for slot in SLOTS]
  rows[0]=dict(slot='S1',status='SELECTED',region='south',brick='SYNTHETIC_S',x=128,y=128)
  artifact(run.root,'OC3_LOCATIONS.json',dict(binding=run.binding,locations=rows,selection_sha256=hash_object(rows)))
  client=Acquisition(run.root,run.ledger,FakeTransport(responses),run.guard)
  for res in items:client.fetch(res)
  before=run.ledger.count('requests');run.analyze();run.verify()
  self.assertEqual(run.ledger.count('requests'),before)
  ledger=load_json(artifact_path(run.root,'OC3_TEST_LEDGER.json'))
  crops=[r for r in ledger['records'] if r['test']=='T03' and r['unit'].startswith('S1/')]
  self.assertEqual(len(crops),3);self.assertTrue(all(r['status']=='VERIFIED' for r in crops))
  self.assertEqual(run.finalize(),OUTCOMES[2])

# unittest normally inherits all methods; keep only the new integrated case in this class.
for _name in tuple(vars(WorkflowTests)):
 if _name.startswith('test_'):setattr(IntegratedFixtureTests,_name,None)

class EndianTests(Base):
 def test_independent_section_byteorder_only(self):
  a=np.array([0x7fc01234,0x3f800000],dtype='>u4').view('>f4')
  b=a.byteswap().view('<f4');self.assertTrue(independent_crop_equal(a,b))
  b=b.copy();b.view('u4')[0]=0x7fc05678
  self.assertFalse(independent_crop_equal(a,b))
 def test_no_precision_cast_for_comparison(self):
  self.assertFalse(independent_crop_equal(np.ones(3,dtype='f4'),np.ones(3,dtype='f8')))
 def test_unknown_geometry_remains_null(self):
  rows=pixel_states(np.ones((1,1)),np.ones((1,1)),np.ones((1,1)),np.zeros((1,1),dtype='uint16'),np.array([[None]],dtype=object))
  self.assertIsNone(rows[0]['geometric_primary'])

class PersistentStopTests(Base):
 def test_integrity_stop_survives_restart(self):
  a=self.ledger();a.stop_integrity();a.close()
  with self.assertRaises(IntegrityError):self.ledger()
 def test_identity_binds_url_generation_product(self):
  r=resource();self.assertEqual(resource_identity(r),resource_identity(dict(r)))
  self.assertNotEqual(resource_identity(r),resource_identity(dict(r,generation='changed')))
  self.assertNotEqual(resource_identity(r),resource_identity(dict(r,url='https://synthetic.invalid/other')))

class GenerationAndPrecisionTests(Base):
 def test_plan_rejects_resource_generation_mix(self):
  fixture=WorkflowTests();fixture.root=self.root;path,inp=fixture.manifest()
  inp['resources']=[dict(resource(),region='south',brick='SYNTHETIC_S',generation='wrong')]
  path.write_bytes(canonical(seal(inp)))
  with self.assertRaises(IntegrityError):build_plan(PROJECT,path)
 def test_psf_descriptor_reductions_are_float64(self):
  a=np.full((31,31),np.float32(.001),dtype='float32');a[15,15]=1
  d=psf_diagnostics(a,[15,15],.262)
  self.assertEqual(d['negative_absolute_mass'],0)
  self.assertEqual(d['absolute_mass'],float(np.sum(np.abs(a),dtype=np.float64)))
