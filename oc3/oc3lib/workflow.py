"""Manifest-driven stage orchestration. No discovery, cohorts or implicit acquisitions."""
from __future__ import annotations
import csv
from io import StringIO
import json
import os
from pathlib import Path
import platform
import sqlite3
import sys
from .core import *
from .transport import Acquisition,OfflineNetwork,HTTPTransport,validate_resource,resource_identity

REQUIRED_ARTIFACT_FIELDS={
 'OC3_AUTHORITIES.json':{'authorities','input_sha256','allowlist_sha256','implementation_sha256'},
 'OC3_ENVIRONMENT.json':{'python','platform','dependencies','threads','gpu'},
 'OC3_RIGHTS_AND_SEMANTICS.json':{'rights','semantics'},
 'OC3_RESOURCE_PLAN.json':{'binding','resources','bricks','limits','input','sealed','execution_kind'},
 'OC3_RELEASE_ISSUES.json':{'issues'},
 'OC3_LOCATIONS.json':{'binding','locations','selection_sha256'},
 'OC3_PRODUCT_LINKS.json':{'binding','resources'},'OC3_PSF_LINKS.json':{'binding','resources'},
 'OC3_TEST_LEDGER.json':{'binding','records','execution_kind'},
 'OC3_REPRODUCIBILITY.json':{'binding','canonical_hashes','verified','scope'},
 'OC3_RESOURCE_SUMMARY.json':{'counters','limits','attempts'},
 'OC3_TERMINAL.json':{'outcome','binding','execution_kind','generalization'},
}

def seal(obj):
 return dict(obj,sealed=hash_object({k:v for k,v in obj.items() if k!='sealed'}))
def verify_seal(obj):
 if obj.get('sealed')!=hash_object({k:v for k,v in obj.items() if k!='sealed'}): raise IntegrityError('PLAN_SEAL_MISMATCH')

def artifact_path(root,name):
 if name not in ARTIFACTS: raise InputError('UNKNOWN_ARTIFACT')
 return Path(root)/ARTIFACTS[name]/name

def artifact(root,name,value,ledger=None):
 expected=REQUIRED_ARTIFACT_FIELDS.get(name)
 if expected and (not isinstance(value,dict) or expected-set(value)): raise InputError('ARTIFACT_SCHEMA')
 data=canonical(value)+b'\n'
 if ledger: ledger.charge('io_bytes',len(data))
 immutable_write(artifact_path(root,name),data)

def csv_artifact(root,name,rows,ledger=None):
 rows=list(rows); fields=sorted(set().union(*(r.keys() for r in rows))) if rows else ['status']
 out=StringIO(); writer=csv.DictWriter(out,fieldnames=fields,lineterminator='\n'); writer.writeheader()
 for row in rows: writer.writerow({k:json.dumps(v,separators=(',',':'),ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in row.items()})
 data=out.getvalue().encode()
 if ledger: ledger.charge('io_bytes',len(data))
 immutable_write(artifact_path(root,name),data)

def environment():
 import importlib.metadata
 deps={}
 for key in ('numpy','astropy','pyarrow'):
  try: deps[key]=importlib.metadata.version(key)
  except importlib.metadata.PackageNotFoundError: deps[key]='MISSING'
 return dict(python=sys.version,platform=platform.platform(),dependencies=deps,threads=1,gpu=False,
  thread_environment={k:os.environ.get(k) for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')})

FINAL_BOOTSTRAP_FIELDS={'parent_manifest_sha256','parent_manifest_seal','metadata_receipt_sha256',
 'selection_sha256','development_csv_sha256','ledger_identity','watermark'}

def read_inputs(path):
 from .bootstrap import load_canonical_sealed
 source=safe_path(path); inp=load_json(source)
 if inp.get('schema_version')==2: inp,_=load_canonical_sealed(source)
 strict(inp,'input',('schema_version','execution_kind','allowlist_path','allowlist_sha256','bricks','resources','rights','semantics','release_issues','approved_hosts','sealed'))
 verify_seal(inp)
 if inp['schema_version'] not in (1,2) or inp['execution_kind'] not in ('PRODUCTION','SYNTHETIC'): raise InputError('INPUT_VERSION_KIND')
 if inp['schema_version']==2:
  if set(inp.get('bootstrap',{}))!=FINAL_BOOTSTRAP_FIELDS: raise InputError('FINAL_BOOTSTRAP_BINDING_SCHEMA')
  bootstrap=inp['bootstrap']
  if any(not isinstance(bootstrap[k],str) or len(bootstrap[k])!=64 or any(c not in '0123456789abcdef' for c in bootstrap[k])
         for k in FINAL_BOOTSTRAP_FIELDS-{'watermark'}): raise InputError('FINAL_BOOTSTRAP_HASH_SCHEMA')
  if not isinstance(bootstrap['watermark'],int) or bootstrap['watermark']<0: raise InputError('FINAL_BOOTSTRAP_WATERMARK_SCHEMA')
  strict(inp['rights'],'rights',('analysis','local_preservation','redistribution','evidence_refs'))
  if inp['rights']['redistribution'] is not False: raise InputError('REDISTRIBUTION_MUST_BE_FALSE')
 elif inp['execution_kind']=='PRODUCTION':
  raise InputError('FINAL_MANIFEST_V2_REQUIRED')
 else: strict(inp['rights'],'rights',('analysis','local_preservation','evidence_refs'))
 for row in inp['semantics']: strict(row,'semantic',('product','property','status','evidence_refs'))
 for row in inp['release_issues']: strict(row,'issue',('issue','status','evidence_refs'))
 if 'deferred_psf' in inp and not isinstance(inp['deferred_psf'],bool): raise InputError('DEFERRED_PSF_SCHEMA')
 allow=safe_path(inp['allowlist_path'])
 if not allow.is_file(): raise InputError('ALLOWLIST_MISSING')
 if file_hash(allow)!=inp['allowlist_sha256']: raise IntegrityError('ALLOWLIST_HASH')
 permitted=set()
 with allow.open(newline='') as f:
  rd=csv.DictReader(f)
  if rd.fieldnames!=['region','brickname','development','holdout_disjoint','evidence_ref']: raise InputError('ALLOWLIST_SCHEMA')
  rows=[]
  for row in rd:
   strict(row,'allowlist')
   if row['development']!='true' or row['holdout_disjoint']!='true' or not row['evidence_ref']: raise InputError('DEVELOPMENT_SCOPE_UNVERIFIED')
   permitted.add((row['region'],row['brickname']))
   rows.append(row)
 if inp['schema_version']==2 and (len(rows)!=2 or [r['region'] for r in rows]!=['south','north']): raise InputError('FINAL_DEVELOPMENT_CSV_ROWS')
 if len(set(inp['approved_hosts']))!=len(inp['approved_hosts']): raise InputError('HOSTS_DUPLICATED')
 for b in inp['bricks']: strict(b,'brick')
 ids=set()
 for res in inp['resources']:
  validate_resource(res,inp['approved_hosts'])
  if inp['execution_kind']=='PRODUCTION' and res['id']!=resource_identity(res): raise InputError('RESOURCE_ID_NOT_DERIVED')
  if res['id'] in ids: raise InputError('DUPLICATE_RESOURCE_ID')
  ids.add(res['id'])
 return inp,allow,permitted

def _read_promoted_child(root,expected_identity):
 ledger=artifact_path(root,'OC3_RESOURCE_LEDGER.sqlite')
 anchor=ledger.parent/'OC3_LEDGER_ANCHOR.json'
 if not ledger.is_file() or not anchor.is_file(): raise InputError('PROMOTED_LEDGER_REQUIRED')
 anchored=load_json(anchor)
 if anchored!={'execution_id':expected_identity,'ledger':ledger.name}: raise IntegrityError('LEDGER_ANCHOR_CONFLICT')
 db=sqlite3.connect(f'file:{ledger}?mode=ro',uri=True)
 try:
  identity=db.execute("SELECT v FROM config WHERE k='execution_id'").fetchone()
  row=db.execute("SELECT value FROM bindings WHERE kind='child'").fetchone()
  parent=db.execute("SELECT value FROM bindings WHERE kind='parent'").fetchone()
  receipt=db.execute("SELECT value FROM bindings WHERE kind='metadata_receipt'").fetchone()
  caps=db.execute("SELECT v FROM config WHERE k='caps'").fetchone()
  if not identity or identity[0]!=expected_identity or not row or not parent or not receipt or not caps: raise IntegrityError('PROMOTION_BINDING_MISSING')
  counters=dict(db.execute('SELECT k,v FROM counters'))
  return json.loads(row[0]),json.loads(parent[0]),json.loads(receipt[0]),json.loads(caps[0]),counters
 finally: db.close()

def build_final_plan(project,manifest,root,overrides=None):
 """Reproduce a committed child. Never resolve or reselect bricks."""
 inp,allow,allowed=read_inputs(manifest)
 if inp['schema_version']!=2: return build_plan(project,manifest,overrides)
 caps=limits(overrides)
 bootstrap=inp['bootstrap']; child,parent,receipt,persisted_caps,live_counters=_read_promoted_child(root,bootstrap['ledger_identity'])
 caps={key:min(value,persisted_caps[key]) for key,value in caps.items()}
 if child.get('kind')!='OC3_PROMOTED_CHILD': raise IntegrityError('PROMOTED_CHILD_KIND')
 checks=((child.get('parent_manifest_sha256'),bootstrap['parent_manifest_sha256']),
  (child.get('parent_manifest_seal'),bootstrap['parent_manifest_seal']),
  (child.get('metadata_receipt_sha256'),bootstrap['metadata_receipt_sha256']),
  (child.get('selection_sha256'),bootstrap['selection_sha256']),
  (child.get('development_csv_sha256'),bootstrap['development_csv_sha256']),
  (child.get('ledger_identity'),bootstrap['ledger_identity']),
  (child.get('final_manifest_sha256'),file_hash(manifest)),
  (child.get('final_manifest_seal'),inp['sealed']))
 if any(a!=b for a,b in checks): raise IntegrityError('FINAL_CHILD_BINDING_MISMATCH')
 if hash_object(receipt)!=bootstrap['metadata_receipt_sha256'] or receipt.get('ledger_identity')!=bootstrap['ledger_identity'] or receipt.get('watermark')!=bootstrap['watermark']:
  raise IntegrityError('FINAL_METADATA_RECEIPT_BINDING')
 if parent.get('manifest_sha256')!=bootstrap['parent_manifest_sha256'] or parent.get('manifest_seal')!=bootstrap['parent_manifest_seal']:
  raise IntegrityError('FINAL_PARENT_BINDING_MISMATCH')
 current_authorities=verify_authorities(project); current_implementation=implementation_hash(project)
 if child.get('authorities')!=current_authorities or child.get('implementation_sha256')!=current_implementation or parent.get('authorities')!=current_authorities or parent.get('implementation_sha256')!=current_implementation:
  raise IntegrityError('FINAL_IMPLEMENTATION_AUTHORITY_BINDING')
 if file_hash(allow)!=bootstrap['development_csv_sha256']: raise IntegrityError('FINAL_DEVELOPMENT_CSV_BINDING')
 bricks=list(inp['bricks'])
 if len(bricks)!=2 or bricks!=child.get('selected_bricks') or [b['region'] for b in bricks]!=['south','north']:
  raise IntegrityError('FINAL_BRICKS_NOT_PROMOTED')
 if any((b['region'],b['brickname']) not in allowed for b in bricks): raise InputError('FINAL_BRICK_OUTSIDE_DEVELOPMENT_CSV')
 if len(bricks)>caps['bricks'] or 6>caps['locations']: raise LimitError('FROZEN_DESIGN_EXCEEDS_LOWERED_LIMIT')
 keys={(b['region'],b['brickname']) for b in bricks}; resources=[]
 for resource in inp['resources']:
  if resource['category']!='metadata' and (resource.get('region'),resource.get('brick')) not in keys: raise InputError('RESOURCE_OUTSIDE_SELECTED_BRICKS')
  resources.append(resource)
 if inp.get('deferred_psf') and any(r['category']=='psf' for r in resources): raise InputError('PSF_PLAN_AMBIGUOUS')
 deferred=54 if inp.get('deferred_psf') else 0
 used=live_counters
 if used.get('requests',0)+len(resources)+deferred>caps['requests'] or used.get('bytes',0)+sum(r['max_bytes'] for r in resources)+deferred*2**20>caps['bytes']:
  raise LimitError('PLAN_RESERVATION_EXCEEDS_REMAINING_LIMIT')
 binding=bind_authorities(project,manifest,allow)
 binding.update(promotion_sha256=hash_object(child),parent_manifest_sha256=bootstrap['parent_manifest_sha256'],ledger_identity=bootstrap['ledger_identity'])
 return seal(dict(binding=binding,resources=resources,bricks=bricks,limits=caps,input=str(Path(manifest).resolve()),
  execution_kind=inp['execution_kind'],ledger_parent=parent,promotion_sha256=hash_object(child)))

def build_plan(project,manifest,overrides=None):
 from .selection import choose_bricks
 inp,allow,allowed=read_inputs(manifest); caps=limits(overrides)
 bricks=choose_bricks(inp['bricks'],allowed)
 if len(bricks)>caps['bricks'] or 6>caps['locations']: raise LimitError('FROZEN_DESIGN_EXCEEDS_LOWERED_LIMIT')
 keys={(b['region'],b['brickname']) for b in bricks}
 resources=[]
 for r in inp['resources']:
  if r['category']=='metadata' or (r.get('region'),r.get('brick')) in keys: resources.append(r)
  else: raise InputError('RESOURCE_OUTSIDE_SELECTED_BRICKS')
 for r in resources:
  if r['category']!='metadata':
   b=next(b for b in bricks if (b['region'],b['brickname'])==(r.get('region'),r.get('brick')))
   if r['generation']!=b['generation']: raise IntegrityError('RESOURCE_BRICK_GENERATION_CONFLICT')
 if inp.get('deferred_psf') and any(r['category']=='psf' for r in resources): raise InputError('PSF_PLAN_AMBIGUOUS')
 deferred=54 if inp.get('deferred_psf') else 0
 if len(resources)+deferred>caps['requests'] or sum(r['max_bytes'] for r in resources)+deferred*2**20>caps['bytes']: raise LimitError('PLAN_RESERVATION_EXCEEDS_LIMIT')
 for kind in ('metadata','psf'):
  if sum(r['max_bytes'] for r in resources if r['category']==kind)+(deferred*2**20 if kind=='psf' else 0)>caps[kind+'_bytes']: raise LimitError('PLAN_CATEGORY_LIMIT')
 binding=bind_authorities(project,manifest,allow)
 return seal(dict(binding=binding,resources=resources,bricks=bricks,limits=caps,input=str(Path(manifest).resolve()),execution_kind=inp['execution_kind']))

def validate_plan(project,path,root=None):
 plan=load_json(path); verify_seal(plan)
 if REQUIRED_ARTIFACT_FIELDS['OC3_RESOURCE_PLAN.json']-set(plan): raise InputError('PLAN_SCHEMA')
 inp,allow,_=read_inputs(plan['input'])
 binding=bind_authorities(project,plan['input'],allow)
 if inp['schema_version']==1 and binding!=plan['binding']: raise IntegrityError('PLAN_AUTHORITY_MISMATCH')
 rebuilt=build_final_plan(project,plan['input'],root,plan['limits']) if inp['schema_version']==2 else build_plan(project,plan['input'],plan['limits'])
 if rebuilt!=plan: raise IntegrityError('PLAN_NOT_REPRODUCIBLE')
 return plan,inp

class Run:
 def __init__(self,project,root,plan,inp,resume=False,overrides=None):
  self.project=Path(project); self.root=Path(root); self.plan=plan; self.inp=inp; self.binding=plan['binding']
  if plan['execution_kind']=='SYNTHETIC' and self.root.resolve()==(self.project/'oc3').resolve(): raise InputError('SYNTHETIC_EVIDENCE_IN_PRODUCTION')
  effective={k:min(v,limits(overrides)[k]) for k,v in plan['limits'].items()}
  if len(plan['bricks'])>effective['bricks'] or 6>effective['locations']: raise LimitError('FROZEN_DESIGN_EXCEEDS_LOWERED_LIMIT')
  execution_id=inp.get('bootstrap',{}).get('ledger_identity')
  self.ledger=Ledger(artifact_path(root,'OC3_RESOURCE_LEDGER.sqlite'),plan.get('ledger_parent',self.binding),effective,execution_id=execution_id)
  self.closed=False
  if resume: self.ledger.recover()
  self.guard=RuntimeGuard(self.ledger,root)
  artifact(root,'OC3_AUTHORITIES.json',self.binding,self.ledger)
  artifact(root,'OC3_ENVIRONMENT.json',environment(),self.ledger)
  artifact(root,'OC3_RIGHTS_AND_SEMANTICS.json',dict(rights=inp['rights'],semantics=inp['semantics']),self.ledger)
  artifact(root,'OC3_RELEASE_ISSUES.json',dict(issues=inp['release_issues']),self.ledger)
  artifact(root,'OC3_RESOURCE_PLAN.json',plan,self.ledger)
  csv_artifact(root,'OC3_BRICKS.csv',plan['bricks'],self.ledger)
  self.products=[]; self.headers=[]; self.resources=list(plan['resources'])
  psfpath=artifact_path(root,'OC3_PSF_LINKS.json')
  if inp.get('deferred_psf') and psfpath.exists(): self.load_psf_links(psfpath)
 def load_psf_links(self,path):
  obj=load_json(path); verify_seal(obj); loc=self.locations()
  if set(obj)!={'binding','selection_sha256','resources','unavailable','sealed'}: raise InputError('PSF_LINK_SCHEMA')
  if obj['binding']!=self.binding or obj['selection_sha256']!=loc['selection_sha256']: raise IntegrityError('PSF_LINK_BINDING')
  expected={}
  for row in loc['locations']:
   if 'x' in row:
    for dx,dy in ((0,0),(-32,-32),(32,32)):
     for band in BANDS: expected[(row['slot'],row['x']+dx,row['y']+dy,band)]=row
  seen=set(); ids=set(r['id'] for r in self.resources)
  for r in obj['resources']:
   validate_resource(r,self.inp['approved_hosts'])
   if self.inp['execution_kind']=='PRODUCTION' and r['id']!=resource_identity(r): raise InputError('PSF_ID_NOT_DERIVED')
   if r['category']!='psf' or r['stage']!='fixed': raise InputError('PSF_LINK_PRODUCT')
   key=tuple(r.get('location',()))+(r.get('band'),)
   if key not in expected or key in seen or r['id'] in ids: raise IntegrityError('PSF_LOCATION_IDENTITY')
   row=expected[key]; brick=next(b for b in self.plan['bricks'] if b['region']==row['region'])
   if (r.get('region'),r.get('brick'),r['generation'])!=(row['region'],row['brick'],brick['generation']): raise IntegrityError('PSF_BRICK_IDENTITY')
   seen.add(key); ids.add(r['id'])
  for row in obj['unavailable']:
   if set(row)!={'location','band','reason','evidence_refs'}: raise InputError('PSF_UNAVAILABLE_SCHEMA')
   key=tuple(row['location'])+(row['band'],)
   if key not in expected or key in seen or not row['reason'] or not row['evidence_refs']: raise InputError('PSF_UNAVAILABLE_UNVERIFIED')
   seen.add(key)
  if seen!=set(expected): raise InputError('PSF_LINKS_INCOMPLETE')
  # Immutable refinement of the pre-reserved 54 logical requests. Never modifies input/selection.
  sh=file_hash(path)
  with self.ledger.transaction():
   old=self.ledger.db.execute("SELECT v FROM config WHERE k='psf_links'").fetchone()
   if old and old[0]!=sh: raise IntegrityError('PSF_LINKS_CHANGED')
   self.ledger.db.execute("INSERT OR IGNORE INTO config VALUES('psf_links',?)",(sh,))
  self.resources.extend(obj['resources'])
 def stop_integrity(self):
  self.ledger.stop_integrity()
  path=artifact_path(self.root,'OC3_TERMINAL.json')
  if not path.exists():
   artifact(self.root,'OC3_TERMINAL.json',dict(outcome=OUTCOMES[3],binding=self.binding,execution_kind=self.plan['execution_kind'],generalization='UNRESOLVED_TWO_BRICKS_NOT_REPRESENTATIVE'))
  self.log('integrity','PILOT_INTEGRITY_FAILURE_STOP')
 def close(self):
  if self.closed: return
  try: self.guard.check()
  finally: self.ledger.close(); self.closed=True
 def log(self,stage,status):
  p=artifact_path(self.root,'OC3_RUN.log'); p.parent.mkdir(parents=True,exist_ok=True)
  from datetime import datetime,timezone
  text=canonical(dict(utc=datetime.now(timezone.utc).isoformat(),stage=stage,status=status,execution_kind=self.plan['execution_kind']))+b'\n'
  self.ledger.charge('io_bytes',len(text))
  with p.open('ab') as f: f.write(text)
 def acquire(self,stage,network=None,resume=False):
  if not (self.inp['rights'].get('analysis') is True and self.inp['rights'].get('local_preservation') is True and self.inp['rights'].get('evidence_refs')):
   raise InputError('REQUIRED_RIGHTS_NOT_DOCUMENTED')
  if stage=='fixed':
   if self.inp.get('deferred_psf') and not artifact_path(self.root,'OC3_PSF_LINKS.json').exists(): raise InputError('SEALED_PSF_LINKS_REQUIRED')
   loc=self.locations(); permitted=[]
   for row in loc['locations']:
    if 'x' in row:
     for dx,dy in ((0,0),(-32,-32),(32,32)): permitted.append((row['slot'],row['x']+dx,row['y']+dy))
   for r in self.resources:
    if r['category']=='psf' and tuple(r.get('location',())) not in permitted: raise InputError('PSF_NOT_LINKED_TO_FROZEN_LOCATION')
  client=Acquisition(self.root,self.ledger,network,self.guard)
  for res in self.resources:
   if res['stage']==stage:
    self.guard.check(); client.fetch(res,resume)
  self.log('acquire-'+stage,'TECHNICAL_COMPLETE')
 def cached(self,res):
  state=self.ledger.resource(res['id'])
  if not state or state['state']!='COMPLETE': raise InputError('RESOURCE_NOT_CACHED')
  path=safe_path(self.root/state['path'],self.root)
  self.ledger.charge('io_bytes',path.stat().st_size)
  if file_hash(path)!=state['sha']: raise IntegrityError('CACHED_RESOURCE_CORRUPT')
  return path,state['sha']
 def resource(self,region,brick,product,band=None):
  items=[r for r in self.resources if r.get('region')==region and r.get('brick')==brick and r['product']==product and r.get('band')==band]
  if len(items)!=1: raise InputError('PRODUCT_LINK_NOT_UNIQUE')
  return items[0]
 def array(self,res):
  from .arrays import read_fits
  path,sh=self.cached(res); self.ledger.charge('io_bytes',path.stat().st_size)
  if 'hdu' not in res: raise InputError('HDU_NOT_SEALED')
  a,h,meta=read_fits(path,res['hdu'])
  self.headers.append(dict(resource_id=res['id'],sha256=sh,metadata=meta))
  return a,h,meta
 def selection_inputs(self):
  from .selection import AuxiliaryBundle,SkyRectangle
  from .arrays import grid_error
  bundles={}; geometries={}
  for b in self.plan['bricks']:
   region=b['region']; name=b['brickname']; masks,h,_=self.array(self.resource(region,name,'maskbits'))
   nexp={}; psfsize={}; headers=[h]
   for band in BANDS:
    nexp[band],hn,_=self.array(self.resource(region,name,'nexp',band))
    psfsize[band],hp,_=self.array(self.resource(region,name,'psfsize',band)); headers.extend([hn,hp])
   bundles[region]=AuxiliaryBundle(nexp,psfsize,masks)
   # Cheap header agreement before selection; full crop WCS checks occur in T02.
   if any(str(k) not in h for k in ('CTYPE1','CTYPE2','CRPIX1','CRPIX2')): raise InputError('WCS_MISSING')
   if grid_error(headers,(2,2))>1e-6: raise InputError('AUXILIARY_WCS_CONFLICT')
   geometries[region]=SkyRectangle(h,b['primary_bounds'])
  return bundles,geometries
 def select(self):
  from .selection import select_slots
  bundles,geo=self.selection_inputs()
  rows,flow=select_slots(self.plan['bricks'],bundles,geo,self.guard.check)
  result=dict(binding=self.binding,locations=rows,selection_sha256=hash_object(rows))
  artifact(self.root,'OC3_LOCATIONS.json',result,self.ledger)
  csv_artifact(self.root,'OC3_SELECTION_FLOW.csv',flow,self.ledger)
  self.log('select','SEALED'); return result
 def locations(self):
  obj=load_json(artifact_path(self.root,'OC3_LOCATIONS.json'))
  if obj['binding']!=self.binding or obj['selection_sha256']!=hash_object(obj['locations']): raise IntegrityError('LOCATION_SEAL')
  if len(obj['locations'])!=6 or [r['slot'] for r in obj['locations']]!=list(SLOTS): raise IntegrityError('FROZEN_SLOTS_CHANGED')
  return obj
 def analyze(self,reproduce=False):
  from .arrays import (independent_crop_equal,psfsize_descriptors,compare_psfsize,crop,array_hash,translate_header,grid_error,write_crop_fits,pixel_states,
   psf_diagnostics,engineering_guards,save_states)
  from .statistics import t10,holm
  from .selection import SkyRectangle
  import numpy as np
  locations=self.locations(); allstates=[]; relationships=[]; psfs=[]; descriptors=[]; units=[]; records=[]; canonical_hashes={}
  for row in locations['locations']:
   self.guard.check(); slot=row['slot']
   if 'x' not in row:
    for i in range(1,13): records.append(test_result(f'T{i:02}','NOT_EXERCISED','FROZEN_SLOT_UNAVAILABLE',self.binding,unit=slot))
    continue
   brick=next(b for b in self.plan['bricks'] if b['region']==row['region']); region=row['region']; name=row['brick']
   slot_heads=[]; slot_shapes=[]
   for band in BANDS:
    self.guard.check(); cropped={}; heads=[]; sources=[]; window=None
    try:
     # Load one product at a time; no unbounded stack of complete brick images.
     for product in ('image','invvar','nexp','psfsize','maskbits'):
      res=self.resource(region,name,product,None if product=='maskbits' else band)
      arr,h,meta=self.array(res); roi,win=crop(arr,row['x'],row['y']); window=win
      # Independent Astropy section read for T03, same sealed file and decoder.
      from astropy.io import fits
      path,_=self.cached(res); l,b,r,t=win['obtained']
      self.ledger.charge('io_bytes',path.stat().st_size)
      with fits.open(path,memmap=False) as hdus: independent=np.array(hdus[res['hdu']].section[b:t,l:r],copy=True)
      if not independent_crop_equal(roi,independent): raise IntegrityError('CROP_NOT_EXACT')
      meta['independent_section_dtype']=independent.dtype.str
      meta['equality_scope']='EXACT_LOGICAL_DTYPE_VALUES_NAN_PAYLOAD_AFTER_BYTEORDER_ONLY_COMPARISON'
      crophead=translate_header(h,win['integer_offset']); cropped[product]=roi; heads.append(crophead); sources.append(res['id'])
      canonical_hashes[f'{slot}/{band}/{product}']=array_hash(roi)
      if not reproduce:
       dest=self.root/'crops'/slot/('optical_maskbits.fits' if product=='maskbits' else band+'/'+product+'.fits')
       self.guard.reserve_disk(roi.nbytes+65536); self.ledger.charge('io_bytes',roi.nbytes+65536)
       write_crop_fits(dest,roi,h,win['integer_offset'])
      del arr
     shapes={a.shape for a in cropped.values()}
     if len(shapes)!=1: raise InputError('PRODUCT_CROP_SHAPE_CONFLICT')
     shape=cropped['image'].shape; err=grid_error(heads,shape)
     slot_heads.extend(heads); slot_shapes.append(shape)
     yy,xx=np.indices(shape); geo=SkyRectangle(heads[0],brick['primary_bounds']); primary=geo.inside(xx,yy)
     states=pixel_states(cropped['image'],cropped['invvar'],cropped['nexp'],cropped['maskbits'],primary)
     for (y,x),st in zip(np.ndindex(shape),states): allstates.append(dict(slot=slot,band=band,x=x,y=y,**st))
     from collections import Counter
     counts=Counter(canonical(st).decode() for st in states)
     relationships.extend(dict(slot=slot,band=band,state=json.loads(k),count=v) for k,v in sorted(counts.items()))
     ds,unit=t10(cropped['image'],states,slot,band,tuple(window['offset_in_requested']),self.guard.check)
     descriptors.extend(ds); units.append(unit)
     diagnostics=[]
     for rsrc in self.resources:
      if rsrc['category']=='psf' and rsrc.get('band')==band and rsrc.get('location',[None])[0]==slot:
       psf,_,_=self.array(rsrc); diagnostic=psf_diagnostics(psf,rsrc.get('psf_center'),rsrc.get('pixel_scale'))
       px=rsrc['location'][1]-window['integer_offset'][0]; py=rsrc['location'][2]-window['integer_offset'][1]
       if 0<=px<shape[1] and 0<=py<shape[0]: diagnostic['psfsize_comparison']=compare_psfsize(cropped['psfsize'][py,px],diagnostic,rsrc['pixel_scale'])
       diagnostics.append(diagnostic); psfs.append(dict(slot=slot,band=band,resource=rsrc['id'],location=rsrc['location'],diagnostic=diagnostic))
     scale=float(np.sqrt(abs(np.linalg.det(geo.wcs.pixel_scale_matrix)))*3600)
     guard=engineering_guards(cropped['psfsize'],diagnostics,scale)
     psfs.append(dict(slot=slot,band=band,engineering_guard=guard,psfsize=psfsize_descriptors(cropped['psfsize'])))
     metric=dict(window=window,grid_error_pixels=err if np.isfinite(err) else None,engineering_guard=guard,T=unit['T'],states=len(states))
     # Algorithmic verifications are distinct from scientific semantic verification.
     automatic={'T02':('VERIFIED' if err<=1e-6 else 'CONTRADICTED','GRID_COMPOSITION_ONLY'),
      'T03':('VERIFIED','EXACT_NATIVE_SLICE'), 'T04':('NOT_AUDITABLE','SUPPORT_RECORDED_GEOMETRIC_SEMANTICS_REVIEW_REQUIRED'),
      'T07':('VERIFIED' if np.isfinite(cropped['psfsize']).all() and np.min(cropped['psfsize'])>0 else 'NOT_AUDITABLE','PSFSIZE_DESCRIPTORS_ONLY'),
      'T10':('NOT_AUDITABLE','EMPIRICAL_CORRELATION_RECORDED_IDENTIFIABILITY_REVIEW_REQUIRED')}
     for i in range(1,13):
      test=f'T{i:02}'; status,reason=automatic.get(test,('NOT_AUDITABLE','INDEPENDENT_SEMANTIC_EVIDENCE_REVIEW_REQUIRED'))
      records.append(test_result(test,status,reason,self.binding,sources,metric,[f'{slot}/{band}'],unit=f'{slot}/{band}'))
     if not reproduce:
      immutable_write(self.root/'crops'/slot/'OC3_WINDOW.json',canonical(window)+b'\n')
    except InputError as e:
     for i in range(1,13): records.append(test_result(f'T{i:02}','NOT_AUDITABLE',str(e),self.binding,unit=f'{slot}/{band}'))
   if slot_heads:
    joint=grid_error(slot_heads,slot_shapes[0]) if len(set(slot_shapes))==1 else float('inf')
    for record in records:
     if record['test']=='T02' and record['unit'].startswith(slot+'/'):
      record['metrics']['all_band_grid_error_pixels']=joint if np.isfinite(joint) else None
      record['status']='CONTRADICTED' if joint>1e-6 else 'VERIFIED' if len(slot_heads)==15 else 'NOT_AUDITABLE'
      record['reason']='ALL_PRODUCTS_AND_BANDS_GRID_COMPOSITION_ONLY'
  holm(units)
  canonical_hashes['correlation']=hash_object(descriptors+units)
  canonical_hashes['pixel_states']=hash_object(allstates)
  canonical_hashes['map_relationships']=hash_object(relationships)
  canonical_hashes['psf_diagnostics']=hash_object(psfs)
  canonical_hashes['test_records']=hash_object(records)
  if reproduce: return canonical_hashes
  self.ledger.charge('io_bytes',len(canonical(allstates))*2)
  if allstates: save_states(artifact_path(self.root,'OC3_PIXEL_STATES.parquet'),allstates)
  csv_artifact(self.root,'OC3_MAP_RELATIONSHIPS.csv',relationships,self.ledger)
  csv_artifact(self.root,'OC3_PSF_DIAGNOSTICS.csv',psfs,self.ledger)
  csv_artifact(self.root,'OC3_CORRELATION.csv',descriptors+units,self.ledger)
  artifact(self.root,'OC3_TEST_LEDGER.json',dict(binding=self.binding,records=records,execution_kind=self.plan['execution_kind'],canonical_hashes=canonical_hashes),self.ledger)
  links=[]; psflinks=[]
  for r in self.resources:
   state=self.ledger.resource(r['id']); item=dict(resource=r,state=state)
   (psflinks if r['category']=='psf' else links).append(item)
  artifact(self.root,'OC3_PRODUCT_LINKS.json',dict(binding=self.binding,resources=links),self.ledger)
  if not self.inp.get('deferred_psf'): artifact(self.root,'OC3_PSF_LINKS.json',dict(binding=self.binding,resources=psflinks),self.ledger)
  data=b''.join(canonical(r)+b'\n' for r in self.headers); self.ledger.charge('io_bytes',len(data)); immutable_write(artifact_path(self.root,'OC3_HEADERS.jsonl'),data)
  self.log('analyze','TECHNICAL_COMPLETE')
 def verify(self):
  expected=load_json(artifact_path(self.root,'OC3_TEST_LEDGER.json'))['canonical_hashes']
  actual=self.analyze(reproduce=True)
  if expected!=actual: raise IntegrityError('OFFLINE_REPRODUCTION_MISMATCH')
  artifact(self.root,'OC3_REPRODUCIBILITY.json',dict(binding=self.binding,canonical_hashes=actual,verified=True,scope='FIXED_INPUTS_CANONICAL_ARRAYS_AND_T10'),self.ledger)
  self.log('verify','TECHNICAL_COMPLETE')
 def finalize(self):
  path=artifact_path(self.root,'OC3_TEST_LEDGER.json'); records=load_json(path)['records'] if path.exists() else []
  locpath=artifact_path(self.root,'OC3_LOCATIONS.json'); locations=self.locations()['locations'] if locpath.exists() else []
  repro=artifact_path(self.root,'OC3_REPRODUCIBILITY.json')
  if repro.exists() and load_json(repro).get('verified'):
   records=[test_result('T12','VERIFIED','OFFLINE_HASH_REPRODUCTION',self.binding)] + [r for r in records if r['test']!='T12']
  outcome=decide(records,full_slots=len(locations)==6 and all(r['status']=='SELECTED' for r in locations),
   restricted_slots=False,rights=bool(self.inp['rights'].get('analysis') and self.inp['rights'].get('local_preservation')))
  result=dict(outcome=outcome,binding=self.binding,execution_kind=self.plan['execution_kind'],generalization='UNRESOLVED_TWO_BRICKS_NOT_REPRESENTATIVE')
  artifact(self.root,'OC3_TERMINAL.json',result,self.ledger)
  text=f"# OC-3 final\n\nOutcome: {outcome}\n\nExecution kind: {self.plan['execution_kind']}\n\nTwo bricks do not demonstrate DR9 representativeness. Generalization remains unresolved.\n\nMissing independent semantic review is not silently VERIFIED. See OC3_TEST_LEDGER.json.\n"
  immutable_write(artifact_path(self.root,'OC3_FINAL_REPORT.md'),text.encode())
  artifact(self.root,'OC3_RESOURCE_SUMMARY.json',self.ledger.summary())
  self.log('finalize','TECHNICAL_COMPLETE'); return outcome
