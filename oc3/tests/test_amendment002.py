"""Amendment-002 synthetic/local regression. The runner blocks real network globally."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from oc3lib.core import *
from oc3lib.bootstrap import *
from oc3lib.transport import Acquisition,HTTPTransport
from oc3lib.workflow import build_final_plan
from oc3lib.statistics import rng_for
import oc3_pilot

PROJECT=Path(__file__).resolve().parents[2]

class Response:
 def __init__(self,body=b'',status=200,fail_after=None):
  self.body=body; self.status=status; self.pos=0; self.fail_after=fail_after
  self.headers={'content-length':str(len(body)),'content-encoding':'identity'}; self.final_url=''
 def read(self,n):
  if self.fail_after is not None and self.pos>=self.fail_after: raise OSError('SYNTHETIC_INTERRUPTION')
  end=min(len(self.body),self.pos+n,self.fail_after if self.fail_after is not None else len(self.body))
  value=self.body[self.pos:end]; self.pos=end; return value
 def close(self): pass

class Network:
 def __init__(self,bodies): self.bodies=dict(bodies); self.calls=[]; self.authorized={}
 def authorize_materialized(self,url,method): self.authorized[url]=method
 def open(self,url,headers,method='GET'):
  self.calls.append((url,dict(headers),method))
  value=self.bodies[url]
  response=value if isinstance(value,Response) else Response(value)
  response.final_url=url; return response

def candidate(region,name,generation,survey,corrected):
 return {'region':region,'brickname':name,'survey':survey,'release':'DR9','generation':generation,
  'grz':True,'corrected_9012':corrected,'primary_bounds':[1.0,2.0,3.0,4.0],
  'evidence_refs':['SYNTHETIC_TECHNICAL_METADATA']}

class Amendment002Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='oc3_A002_SYNTHETIC_'); self.root=Path(self.tmp.name)
  self.rows=[candidate('south','SYN_S_A','9012','DECaLS',True),candidate('south','SYN_S_B','9012','DECaLS',True),
   candidate('north','SYN_N_A','9011','BASS_MzLS',False),candidate('north','SYN_N_B','9011','BASS_MzLS',False)]
  self.body=canonical({'rows':self.rows})
 def tearDown(self): self.tmp.cleanup()
 def manifest(self,*,kind='SYNTHETIC',mutate=None,dependents=None):
  projection={field:field for field in CANDIDATE_FIELDS}
  obj={'schema_version':2,'execution_kind':kind,'authorities':verify_authorities(PROJECT),
   'implementation_sha256':implementation_hash(PROJECT),
   'environment':{'verified':kind=='SYNTHETIC','fingerprint':'0'*64,'installation_report_sha256':'1'*64,
    'preparation_receipt_sha256':'2'*64,'replay_receipt_sha256':'3'*64,'python':'3.12.14',
    'packages':{'numpy':'2.5.3','astropy':'8.0.1','pyarrow':'25.0.1'},'zero_real_network':True,'synthetic':kind=='SYNTHETIC'},
   'family':{'release':'DR9','regions':['north','south'],'bands':['g','r','z']},
   'selection_policy':{'algorithm':'SHA256_OC3_V1_BRICK','south_corrected_release':'9012','north_release':'DR9','no_replacement':True},
   'development_policy':{'label':'INSTRUMENTAL_DEVELOPMENT','permanent':True,'holdout_disjoint_by_policy':True,'evidence_ref':'SYNTHETIC_POLICY'},
   'literal_resources':[{'id':'synthetic_geometry','url':'https://synthetic.invalid/geometry.json','method':'GET','role':'brick_geometry',
    'host':'synthetic.invalid','release':'DR9','generation':'DR9','max_bytes':4096,'size':len(self.body),'sha256':digest(self.body),
    'evidence_ref':'SYNTHETIC_DOCUMENT','decoder':'JSON_ROWS_V1','projection':projection}],
   'dependent_roles':dependents or [],'approved_hosts':['synthetic.invalid'],'stage_limits':dict(BOOTSTRAP_MAXIMA),
   'global_limits':dict(MAXIMA),'rights':{'scientific_local_analysis':True,'local_preservation':True,
    'public_access':True,'redistribution':False,'evidence_refs':['SYNTHETIC_RIGHTS']},
   'semantics':[],'release_issues':[],
   'human_authorization':{'authorized':kind=='SYNTHETIC','scope':'METADATA_BOOTSTRAP_ONLY','evidence_ref':'SYNTHETIC_AUTH','record_sha256':'4'*64}}
  if mutate: mutate(obj)
  obj=seal_object(obj); path=self.root/'bootstrap.json'; path.write_bytes(canonical(obj)+b'\n'); return path,obj
 def complete(self,*,crash=None):
  path,_=self.manifest(); run=BootstrapRun(PROJECT,self.root/'run',path)
  try: child=run.execute(Network({'https://synthetic.invalid/geometry.json':self.body}),crash=crash)
  finally: run.close()
  return child,self.root/'run',path

 # 1-3: ordering and explicit final prerequisites.
 def test_01_bootstrap_without_final_manifest(self):
  path,_=self.manifest(); load_bootstrap_manifest(path,PROJECT); self.assertFalse((self.root/'OC3_INPUT_MANIFEST.json').exists())
 def test_02_bootstrap_without_final_csv(self):
  path,_=self.manifest(); load_bootstrap_manifest(path,PROJECT); self.assertFalse((self.root/'OC3_DEVELOPMENT_BRICKS.csv').exists())
 def test_03_final_mode_requires_manifest_and_csv(self):
  child,root,_=self.complete(); final=root/'INPUTS/OC3_INPUT_MANIFEST.json'; csvp=root/'INPUTS/OC3_DEVELOPMENT_BRICKS.csv'
  csvp.rename(root/'missing.csv')
  with self.assertRaises((InputError,IntegrityError)): build_final_plan(PROJECT,final,root)

 # 4-7: firewall and closed transport.
 def test_04_map_get_rejected(self):
  with self.assertRaises(InputError): bootstrap_firewall({'url':'https://synthetic.invalid/x','host':'synthetic.invalid','method':'GET','product':'image','materialized':True},{'approved_hosts':['synthetic.invalid']})
 def test_05_psf_rejected(self):
  with self.assertRaises(InputError): bootstrap_firewall({'url':'https://synthetic.invalid/x','host':'synthetic.invalid','method':'HEAD','product':'psf','materialized':True},{'approved_hosts':['synthetic.invalid']})
 def test_06_unenumerated_url_rejected(self):
  with self.assertRaises(InputError): HTTPTransport({'https://synthetic.invalid/a':'GET'}).open('https://synthetic.invalid/b',{},'GET')
 def test_07_crawl_rejected(self):
  with self.assertRaises(InputError): bootstrap_firewall({'url':'https://synthetic.invalid/x','host':'synthetic.invalid','method':'GET','product':'metadata','materialized':True,'crawl':True},{'approved_hosts':['synthetic.invalid']})

 # 8-12: deterministic technical selection, isolated from scientific content.
 def test_08_south_requires_corrected_9012(self): self.assertEqual(resolve_bootstrap_bricks(self.rows,synthetic_legacy=True)['bricks'][0]['generation'],'9012')
 def test_09_north_not_constrained_to_9012(self): self.assertEqual(resolve_bootstrap_bricks(self.rows,synthetic_legacy=True)['bricks'][1]['generation'],'9011')
 def test_10_row_order_stability(self): self.assertEqual(resolve_bootstrap_bricks(self.rows,synthetic_legacy=True),resolve_bootstrap_bricks(self.rows[::-1],synthetic_legacy=True))
 def test_11_morphology_source_isolation(self):
  def bad(obj): obj['literal_resources'][0]['evidence_ref']='Galaxy Zoo morphology label'
  path,obj=self.manifest(mutate=bad)
  with self.assertRaises(InputError): validate_bootstrap_manifest(obj,PROJECT)
 def test_12_no_replacement(self):
  picked=resolve_bootstrap_bricks(self.rows,synthetic_legacy=True); self.assertEqual(len({(r['region'],r['brickname']) for r in picked['bricks']}),2); self.assertTrue(picked['no_replacement'])

 # 13-22: persistent development and one immutable promotion.
 def test_13_development_marking_persists(self):
  child,root,_=self.complete(); import sqlite3
  db=sqlite3.connect(root/'provenance/OC3_RESOURCE_LEDGER.sqlite'); self.assertIsNotNone(db.execute("SELECT value FROM bindings WHERE kind='development'").fetchone()); db.close()
 def test_14_parent_hash_in_child(self):
  child,root,path=self.complete(); self.assertEqual(child['parent_manifest_sha256'],file_hash(path))
 def test_15_exactly_one_promotion(self):
  child,root,path=self.complete(); run=BootstrapRun(PROJECT,root,path)
  try:
   with self.assertRaises(IntegrityError): run.execute(Network({}))
  finally: run.close()
 def test_16_same_ledger_identity(self):
  child,root,path=self.complete(); run=BootstrapRun(PROJECT,root,path,resume=True); self.assertEqual(child['ledger_identity'],run.execution_id); run.close()
 def test_17_global_counters_preserved(self):
  child,root,path=self.complete(); self.assertGreater(child['global_counters']['bytes'],0)
 def test_18_stage_counters_preserved(self):
  child,root,path=self.complete(); self.assertEqual(child['stage_counters']['bytes'],len(self.body))
 def test_19_precommit_crash_recovery(self):
  path,_=self.manifest(); root=self.root/'run'; run=BootstrapRun(PROJECT,root,path)
  with self.assertRaises(OSError): run.execute(Network({'https://synthetic.invalid/geometry.json':self.body}),crash='before')
  run.close(); resumed=BootstrapRun(PROJECT,root,path,resume=True); child=resumed.execute(Network({}),resume=True); resumed.close(); self.assertEqual(child['kind'],'OC3_PROMOTED_CHILD')
 def test_20_postcommit_crash_recovery(self):
  path,_=self.manifest(); root=self.root/'run'; run=BootstrapRun(PROJECT,root,path)
  with self.assertRaises(OSError): run.execute(Network({'https://synthetic.invalid/geometry.json':self.body}),crash='after')
  run.close(); resumed=BootstrapRun(PROJECT,root,path,resume=True); child=resumed.execute(Network({}),resume=True); resumed.close(); self.assertEqual(child['kind'],'OC3_PROMOTED_CHILD')
 def test_21_incompatible_child_stops(self):
  ledger=Ledger(self.root/'p/ledger.sqlite',{'x':1}); ledger.record_parent({'x':1}); ledger.prepare_child({'x':2})
  with self.assertRaises(IntegrityError): ledger.commit_child({'x':3}); ledger.close()
 def test_22_second_ledger_stops(self):
  first=Ledger(self.root/'p/one.sqlite',{'x':1})
  with self.assertRaises(IntegrityError): Ledger(self.root/'p/two.sqlite',{'x':1})
  first.close()

 # 23-27: nested and typed budgets.
 def test_23_simultaneous_global_and_stage_caps(self):
  ledger=Ledger(self.root/'p/l.sqlite',{'x':1},{'bytes':10},stage='METADATA_BOOTSTRAP',stage_caps={'bytes':8})
  token=ledger.reserve('r','metadata',8); ledger.received(token,5); ledger.finish(token,'COMPLETE')
  self.assertEqual((ledger.count('bytes'),ledger.stage_count('bytes')),(5,5)); ledger.close()
 def test_24_stage_exhaustion_atomic_global(self):
  ledger=Ledger(self.root/'p/l.sqlite',{'x':1},{'bytes':100},stage='METADATA_BOOTSTRAP',stage_caps={'bytes':4})
  with self.assertRaises(LimitError): ledger.reserve('r','metadata',5)
  self.assertEqual(ledger.count('bytes'),0); ledger.close()
 def test_25_stage_completion_no_global_refund(self):
  ledger=Ledger(self.root/'p/l.sqlite',{'x':1},stage='METADATA_BOOTSTRAP'); token=ledger.reserve('r','metadata',5); ledger.received(token,5); ledger.finish(token,'COMPLETE'); self.assertEqual(ledger.count('bytes'),5); ledger.close()
 def test_26_later_stage_preserves_bootstrap_consumption(self):
  path=self.root/'p/l.sqlite'; ledger=Ledger(path,{'x':1},stage='METADATA_BOOTSTRAP'); token=ledger.reserve('r','metadata',5); ledger.received(token,5); ledger.finish(token,'COMPLETE'); ledger.close()
  later=Ledger(path,{'x':1}); self.assertEqual((later.count('bytes'),later.count('requests')),(5,1)); later.close()
 def test_27_typed_cli_budget_semantics(self):
  with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
   self.assertEqual(oc3_pilot.main(['plan','--inputs','missing','--dry-run','--max-requests','1']),22)

 # 28-35: canonical outputs, gates, dry-run and Amendment-001 regression.
 def test_28_canonical_seal_and_file_hash(self):
  path,obj=self.manifest(); loaded,sha=load_canonical_sealed(path); self.assertEqual((loaded,sha),(obj,digest(canonical(obj)+b'\n')))
 def test_29_deterministic_development_csv(self):
  selected=resolve_bootstrap_bricks(self.rows,synthetic_legacy=True); self.assertEqual(development_csv(selected,'x'),development_csv(selected,'x')); self.assertTrue(development_csv(selected,'x').endswith(b'\n'))
 def test_30_holdout_never_opened(self):
  with self.assertRaises(InputError): safe_path(self.root/'INTERPRETATION_LOCKBOX'/'holdout.parquet')
 def test_31_environment_replay_required(self):
  def invalid(obj): obj['environment']['verified']=False
  path,obj=self.manifest(kind='PRODUCTION',mutate=invalid)
  with self.assertRaises(InputError): validate_bootstrap_manifest(obj,PROJECT,for_network=True)
 def test_32_rights_evidence_required(self):
  def invalid(obj): obj['rights']['evidence_refs']=[]
  path,obj=self.manifest(kind='PRODUCTION',mutate=invalid)
  with self.assertRaises(InputError): validate_bootstrap_manifest(obj,PROJECT,for_network=True)
 def test_33_redistribution_false(self):
  def invalid(obj): obj['rights']['redistribution']=True
  path,obj=self.manifest(mutate=invalid)
  with self.assertRaises(InputError): validate_bootstrap_manifest(obj,PROJECT)
 def test_34_dryrun_zero_side_effects(self):
  before=list(self.root.rglob('*'))
  with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
   code=oc3_pilot.main(['plan','--bootstrap-inputs',str(self.root/'missing'),'--resolve-metadata','--dry-run','--offline','--root',str(self.root/'run')])
  self.assertEqual(code,0); self.assertEqual(before,list(self.root.rglob('*')))
 def test_35_amendment001_rng_regression(self):
  self.assertEqual(rng_for('S1','g').bit_generator.random_raw(2).tolist(),[15103153937790353826,3381533215772834288])

 # Additional mandatory transport/identity cases.
 def test_36_dependent_role_materialization(self):
  selection=resolve_bootstrap_bricks(self.rows,synthetic_legacy=True); evidence=b'evidence'
  role={'id':'idx','kind':'brick_index','method':'GET','host':'synthetic.invalid','resource_type':'technical_index','region':'south','product':'metadata',
   'generation_rule':'SELECTED_BRICK','max_bytes':100,'evidence_ref':'synthetic','supporting_evidence_sha256':digest(evidence),
   'resolver':'CLOSED_TEMPLATE_V1','url_template':'https://synthetic.invalid/{region}/{brick}.json'}
  value=materialize_role(role,selection,evidence); self.assertEqual(value['brick'],selection['bricks'][0]['brickname']); self.assertEqual(value['method'],'GET')
 def test_37_head_error_body_debits_both(self):
  ledger=Ledger(self.root/'p/l.sqlite',{'x':1},stage='METADATA_BOOTSTRAP'); net=Network({'https://synthetic.invalid/h':Response(b'error',500)})
  res={'id':'h','url':'https://synthetic.invalid/h','category':'metadata','product':'metadata','stage':'metadata','release':'DR9','generation':'x','max_bytes':5,'method':'HEAD'}
  with self.assertRaises(InputError): Acquisition(self.root/'p',ledger,net).fetch(res)
  self.assertEqual((ledger.count('bytes'),ledger.stage_count('bytes')),(5,5)); ledger.close()
 def test_38_partial_body_debits_both(self):
  ledger=Ledger(self.root/'p/l.sqlite',{'x':1},stage='METADATA_BOOTSTRAP'); net=Network({'https://synthetic.invalid/g':Response(b'abcdefgh',fail_after=4)})
  res={'id':'g','url':'https://synthetic.invalid/g','category':'metadata','product':'metadata','stage':'metadata','release':'DR9','generation':'x','max_bytes':8,'size':8,'sha256':digest(b'abcdefgh')}
  with self.assertRaises(OSError): Acquisition(self.root/'p',ledger,net).fetch(res)
  self.assertEqual((ledger.count('bytes'),ledger.stage_count('bytes')),(4,4)); ledger.close()
 def test_39_metadata_allowance_is_global(self):
  ledger=Ledger(self.root/'p/l.sqlite',{'x':1},{'metadata_bytes':5},stage='METADATA_BOOTSTRAP')
  token=ledger.reserve('a','metadata',5); ledger.received(token,5); ledger.finish(token,'COMPLETE')
  with self.assertRaises(LimitError): ledger.reserve('b','metadata',1)
  ledger.close()
 def test_40_retry_identity_survives_promotion(self):
  ledger=Ledger(self.root/'p/l.sqlite',{'x':1}); ledger.record_parent({'x':1})
  for _ in range(3): token=ledger.reserve('same','metadata',1); ledger.finish(token,'FAILED')
  child={'fixed':True}; ledger.prepare_child(child); ledger.commit_child(child)
  with self.assertRaises(LimitError): ledger.reserve('same','metadata',1)
  ledger.close()
 def test_41_final_plan_uses_promoted_pair_without_reselection(self):
  child,root,path=self.complete(); final=root/'INPUTS/OC3_INPUT_MANIFEST.json'
  with patch('oc3lib.selection.choose_bricks',side_effect=AssertionError('RESELECTION_FORBIDDEN')):
   plan=build_final_plan(PROJECT,final,root)
  self.assertEqual(plan['bricks'],child['selected_bricks']); self.assertEqual(plan['binding']['ledger_identity'],child['ledger_identity'])
 def test_42_lowered_global_cap_survives_promotion(self):
  path,_=self.manifest(); root=self.root/'run'; run=BootstrapRun(PROJECT,root,path,global_overrides={'requests':100})
  run.execute(Network({'https://synthetic.invalid/geometry.json':self.body})); run.close()
  plan=build_final_plan(PROJECT,root/'INPUTS/OC3_INPUT_MANIFEST.json',root)
  self.assertEqual(plan['limits']['requests'],100)

if __name__=='__main__': unittest.main()
