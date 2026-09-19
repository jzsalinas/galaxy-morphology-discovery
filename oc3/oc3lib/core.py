"""Frozen authority, schema, immutable artifact and cumulative budget primitives."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import time
import contextlib

AUTHORITIES = {
 'MORPHOLOGICAL_INFORMATION_PRESERVATION_SPEC.md': 'f7f27acbe42a0caecd1f0e4e2e86eedea6c546434d95c16143c0a7d122f38f24',
 'OBSERVATIONAL_CANDIDATE_TRIAGE_OC2.md': '9cbdc77943188717b1c92cf3fef64eaf03c968ce28e115df4171065e25362b93',
 'OC3_DR9_COADD_BOUNDED_PILOT_SPEC.md': '7fc040829847e26e6231c95b18d5debcd3785db0198915b1f93a5b45859f38bd',
 'OC3_DR9_COADD_BOUNDED_PILOT_SPEC_AMENDMENT_001.md': '2f87cec954167bc51ab442d1dbd803bae622bb5411a2b88642fecde8d920cd66',
 'OC3_DR9_COADD_BOUNDED_PILOT_SPEC_AMENDMENT_002.md': '4f6d921204645a0289c6f3c4ce4e5818419ade97d42b8b1d8def7cd2e6d723fe',
 'OC3_DR9_PROVIDER_SCHEMA_ADAPTER_AMENDMENT_003.md': 'ca8d2884995a2f3411bc24bb7a2003752153e99ca06cca7c5ba9f2163b47aa8c',
}
MAXIMA = dict(bricks=2, locations=6, bytes=1610612736, requests=200,
 retries=2, concurrency=1, metadata_bytes=64*2**20, psf_bytes=54*2**20,
 ram_bytes=2*2**30, threads=1, disk_bytes=4*2**30, io_bytes=8*2**30,
 compute_seconds=1800, wall_seconds=3600)
BOOTSTRAP_MAXIMA = dict(bytes=48*2**20, requests=48, disk_bytes=256*2**20,
 io_bytes=512*2**20, compute_seconds=300, wall_seconds=900, concurrency=1)
SLOTS = ('S1','S2','S3','N1','N2','N3')
BANDS = ('g','r','z')
STATES = ('VERIFIED','CONTRADICTED','NOT_AUDITABLE','NOT_EXERCISED')
OUTCOMES = ('DR9_COADD_SUPPORTS_OBSERVATIONAL_CONTRACT_DRAFT',
 'DR9_COADD_REQUIRES_NARROWER_SCIENTIFIC_DOMAIN',
 'DR9_COADD_NOT_CURRENTLY_ADMISSIBLE','PILOT_INTEGRITY_FAILURE_STOP')

class IntegrityError(Exception): pass
class LimitError(Exception): pass
class OfflineError(Exception): pass
class DependencyError(Exception): pass
class InputError(Exception): pass

# No unrecognized scientific columns are ever silently projected away.
FIELDS = {
 'brick': {'region','brickname','brickid','release','generation','grz','corrected_9012','primary_bounds','wcs','evidence_refs'},
 'allowlist': {'region','brickname','development','holdout_disjoint','evidence_ref'},
 'resource': {'id','url','category','product','stage','region','brick','band','generation','release','max_bytes','size','sha256','etag','hdu','headers','location','psf_center','pixel_scale','evidence_refs'},
 'rights': {'analysis','local_preservation','redistribution','evidence_refs'},
 'semantic': {'product','property','status','value','units','evidence_refs'},
 'issue': {'issue','region','generation','status','evidence_refs'},
 'input': {'schema_version','execution_kind','allowlist_path','allowlist_sha256','bricks','resources','rights','semantics','release_issues','approved_hosts','deferred_psf','bootstrap','sealed'},
}
ARTIFACTS = {
 'OC3_METADATA_BOOTSTRAP_MANIFEST.json':'INPUTS','OC3_INPUT_MANIFEST.json':'INPUTS', 'OC3_DEVELOPMENT_BRICKS.csv':'INPUTS',
 'OC3_AUTHORITIES.json':'provenance','OC3_ENVIRONMENT.json':'provenance',
 'OC3_RIGHTS_AND_SEMANTICS.json':'provenance','OC3_RESOURCE_PLAN.json':'provenance',
 'OC3_RESOURCE_LEDGER.sqlite':'provenance','OC3_HTTP_EVENTS.jsonl':'provenance',
 'OC3_RELEASE_ISSUES.json':'provenance','OC3_HEADERS.jsonl':'provenance',
 'OC3_BRICKS.csv':'TECHNICAL_INDEX','OC3_LOCATIONS.json':'TECHNICAL_INDEX',
 'OC3_SELECTION_FLOW.csv':'TECHNICAL_INDEX','OC3_PRODUCT_LINKS.json':'TECHNICAL_INDEX',
 'OC3_PSF_LINKS.json':'TECHNICAL_INDEX','OC3_PIXEL_STATES.parquet':'CONFOUND_AUDIT',
 'OC3_MAP_RELATIONSHIPS.csv':'CONFOUND_AUDIT','OC3_PSF_DIAGNOSTICS.csv':'CONFOUND_AUDIT',
 'OC3_CORRELATION.csv':'CONFOUND_AUDIT','OC3_TEST_LEDGER.json':'reports',
 'OC3_REPRODUCIBILITY.json':'reports','OC3_RESOURCE_SUMMARY.json':'reports',
 'OC3_FINAL_REPORT.md':'reports','OC3_TERMINAL.json':'reports','OC3_RUN.log':'logs',
}

def canonical(value):
 return json.dumps(value, sort_keys=True, separators=(',',':'), ensure_ascii=False, allow_nan=False).encode('utf-8')
def digest(data): return hashlib.sha256(data).hexdigest()
def file_hash(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
 return h.hexdigest()
def hash_object(value): return digest(canonical(value))
def strict(value, kind, required=()):
 if not isinstance(value,dict) or set(value)-FIELDS[kind] or set(required)-set(value):
  raise InputError('INPUT_SCHEMA_REJECTED')  # Do not log forbidden field names.
 return value

def safe_path(path, root=None):
 p=Path(path)
 prohibited=('lockbox','holdout','interpretation','zoobot','galaxyzoo','galaxy_zoo','confound_audit_c0','subject_index')
 if any(t in str(p).lower() for t in prohibited): raise InputError('PROHIBITED_INPUT_PATH')
 resolved=p.resolve()
 if any(t in str(resolved).lower() for t in prohibited): raise InputError('PROHIBITED_INPUT_PATH')
 if root is not None and not resolved.is_relative_to(Path(root).resolve()): raise InputError('OUTSIDE_RUN_ROOT')
 return resolved

def immutable_write(path, data):
 path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists():
  if path.read_bytes()!=data: raise IntegrityError('IMMUTABLE_ARTIFACT_CONFLICT')
  return
 # Exclusive creation; interrupted files are never silently replaced.
 with path.open('xb') as f: f.write(data); f.flush(); os.fsync(f.fileno())
def write_json(path,obj): immutable_write(path,canonical(obj)+b'\n')
def load_json(path):
 try: return json.loads(safe_path(path).read_text())
 except (ValueError,OSError) as e: raise InputError('INVALID_JSON_INPUT') from e

def verify_authorities(project):
 result={}
 for name,expected in AUTHORITIES.items():
  path=Path(project)/name
  if not path.is_file() or file_hash(path)!=expected: raise IntegrityError('FROZEN_AUTHORITY_MISMATCH')
  result[name]=expected
 path=Path(project)/'AGENTS.md'
 if not path.is_file(): raise IntegrityError('AGENTS_MISSING')
 result['AGENTS.md']=file_hash(path)
 return result

def implementation_hash(project):
 base=Path(project)/'oc3'
 return hash_object({str(p.relative_to(base)):file_hash(p) for p in sorted(base.rglob('*.py')) if '.venv' not in p.parts})

def bind_authorities(project, manifest, allowlist):
 return dict(authorities=verify_authorities(project), input_sha256=file_hash(safe_path(manifest)),
  allowlist_sha256=file_hash(safe_path(allowlist)), implementation_sha256=implementation_hash(project))

def limits(overrides=None):
 out=MAXIMA.copy()
 for k,v in (overrides or {}).items():
  if k not in out or isinstance(v,bool) or not isinstance(v,(int,float)) or not (0<=v<=out[k] if k=='retries' else 0<v<=out[k]):
   raise LimitError('LIMIT_INCREASE_OR_INVALID')
  out[k]=v
 return out

def stage_limits(overrides=None):
 out=BOOTSTRAP_MAXIMA.copy()
 for k,v in (overrides or {}).items():
  if k not in out or isinstance(v,bool) or not isinstance(v,(int,float)) or not 0<v<=out[k]:
   raise LimitError('STAGE_LIMIT_INCREASE_OR_INVALID')
  out[k]=v
 return out

class Ledger:
 """SQLite transactions reserve worst-case body bytes BEFORE every HTTP attempt.
 A crash retains the entire outstanding reservation: no reset or uncharged retry.
 """
 def __init__(self,path,binding,caps=None,stage=None,stage_caps=None,execution_id=None):
  self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
  self.execution_id=execution_id or hash_object(binding)
  anchor=self.path.parent/'OC3_LEDGER_ANCHOR.json'
  anchor_value=canonical({'execution_id':self.execution_id,'ledger':self.path.name})+b'\n'
  immutable_write(anchor,anchor_value)
  self.db=sqlite3.connect(self.path,timeout=0,isolation_level=None)
  self.db.execute('PRAGMA synchronous=FULL')
  self.db.executescript('''CREATE TABLE IF NOT EXISTS config(k TEXT PRIMARY KEY,v TEXT NOT NULL);
  CREATE TABLE IF NOT EXISTS counters(k TEXT PRIMARY KEY,v REAL NOT NULL);
  CREATE TABLE IF NOT EXISTS stages(id TEXT PRIMARY KEY,caps TEXT NOT NULL,state TEXT NOT NULL DEFAULT 'ACTIVE');
  CREATE TABLE IF NOT EXISTS stage_counters(stage TEXT,k TEXT,v REAL NOT NULL,PRIMARY KEY(stage,k));
  CREATE TABLE IF NOT EXISTS attempts(id INTEGER PRIMARY KEY,resource TEXT,category TEXT,reserved INTEGER,actual INTEGER DEFAULT 0,state TEXT,stage TEXT,method TEXT DEFAULT 'GET');
  CREATE TABLE IF NOT EXISTS resources(id TEXT PRIMARY KEY,identity TEXT,state TEXT DEFAULT 'NEW',offset INTEGER DEFAULT 0,sha TEXT,path TEXT);
  CREATE TABLE IF NOT EXISTS bindings(kind TEXT PRIMARY KEY,value TEXT NOT NULL);
  CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT,kind TEXT NOT NULL,value TEXT NOT NULL);
  ''')
  # Additive migration for synthetic/historical ledgers created by the pre-002 harness.
  columns={row[1] for row in self.db.execute('PRAGMA table_info(attempts)')}
  if 'stage' not in columns: self.db.execute('ALTER TABLE attempts ADD COLUMN stage TEXT')
  if 'method' not in columns: self.db.execute("ALTER TABLE attempts ADD COLUMN method TEXT DEFAULT 'GET'")
  self.caps=limits(caps)
  self.stage=stage
  self.stage_caps=stage_limits(stage_caps) if stage else None
  with self.transaction():
   if self.db.execute("SELECT v FROM config WHERE k='integrity_stop'").fetchone(): raise IntegrityError('PREVIOUS_INTEGRITY_STOP')
   old=self.db.execute("SELECT v FROM config WHERE k='binding'").fetchone()
   if old and old[0]!=hash_object(binding): raise IntegrityError('RUN_AUTHORITY_CONFLICT')
   self.db.execute("INSERT OR IGNORE INTO config VALUES('binding',?)",(hash_object(binding),))
   old_id=self.db.execute("SELECT v FROM config WHERE k='execution_id'").fetchone()
   if old_id and old_id[0]!=self.execution_id: raise IntegrityError('LEDGER_IDENTITY_CONFLICT')
   self.db.execute("INSERT OR IGNORE INTO config VALUES('execution_id',?)",(self.execution_id,))
   old=self.db.execute("SELECT v FROM config WHERE k='caps'").fetchone()
   if old:
    previous=json.loads(old[0])
    self.caps={k:min(v,previous[k]) for k,v in self.caps.items()}
   self.db.execute("INSERT OR REPLACE INTO config VALUES('caps',?)",(canonical(self.caps).decode(),))
   for k in ('bytes','requests','metadata_bytes','psf_bytes','io_bytes','compute_seconds'):
    self.db.execute('INSERT OR IGNORE INTO counters VALUES(?,0)',(k,))
   if stage:
    row=self.db.execute('SELECT caps FROM stages WHERE id=?',(stage,)).fetchone()
    if row:
     previous=json.loads(row[0]); self.stage_caps={k:min(v,previous[k]) for k,v in self.stage_caps.items()}
    self.db.execute('INSERT OR REPLACE INTO stages(id,caps,state) VALUES(?,?,COALESCE((SELECT state FROM stages WHERE id=?),\'ACTIVE\'))',
     (stage,canonical(self.stage_caps).decode(),stage))
    for k in ('bytes','requests','io_bytes','compute_seconds'):
     self.db.execute('INSERT OR IGNORE INTO stage_counters VALUES(?,?,0)',(stage,k))
 def close(self): self.db.close()
 def stop_integrity(self):
  with self.transaction(): self.db.execute("INSERT OR IGNORE INTO config VALUES('integrity_stop','true')")
 @contextlib.contextmanager
 def transaction(self):
  self.db.execute('BEGIN IMMEDIATE')
  try: yield; self.db.execute('COMMIT')
  except BaseException: self.db.execute('ROLLBACK'); raise
 def count(self,k): return self.db.execute('SELECT v FROM counters WHERE k=?',(k,)).fetchone()[0]
 def stage_count(self,k,stage=None):
  sid=stage or self.stage
  if not sid: return 0
  row=self.db.execute('SELECT v FROM stage_counters WHERE stage=? AND k=?',(sid,k)).fetchone()
  return row[0] if row else 0
 def _add(self,k,n):
  if n<0 or self.count(k)+n>self.caps[k]: raise LimitError('CUMULATIVE_LIMIT')
  self.db.execute('UPDATE counters SET v=v+? WHERE k=?',(n,k))
 def charge(self,k,n):
  with self.transaction():
   self._add(k,n)
   if self.stage and k in ('io_bytes','compute_seconds'):
    self._stage_add(k,n)
 def _stage_add(self,k,n):
  if not self.stage or k not in self.stage_caps: return
  if n<0 or self.stage_count(k)+n>self.stage_caps[k]: raise LimitError('CUMULATIVE_STAGE_LIMIT')
  self.db.execute('UPDATE stage_counters SET v=v+? WHERE stage=? AND k=?',(n,self.stage,k))
 def register(self,res):
  ident=hash_object(res)
  with self.transaction():
   row=self.db.execute('SELECT identity FROM resources WHERE id=?',(res['id'],)).fetchone()
   if row and row[0]!=ident: raise IntegrityError('RESOURCE_GENERATION_CONFLICT')
   self.db.execute('INSERT OR IGNORE INTO resources(id,identity) VALUES(?,?)',(res['id'],ident))
 def reserve(self,resource,category,size,method='GET'):
  if not isinstance(size,int) or size<=0: raise LimitError('UNBOUNDED_RESPONSE')
  if method not in ('GET','HEAD'): raise InputError('UNLISTED_HTTP_METHOD')
  with self.transaction():
   if self.db.execute("SELECT count(*) FROM attempts WHERE state='RESERVED'").fetchone()[0]:
    raise IntegrityError('OUTSTANDING_RESERVATION_REQUIRES_RECOVERY')
   n=self.db.execute('SELECT count(*) FROM attempts WHERE resource=?',(resource,)).fetchone()[0]
   if n>=1+self.caps['retries']: raise LimitError('RETRY_LIMIT')
   if self.stage:
    if self.stage_count('requests')+1>self.stage_caps['requests'] or self.stage_count('bytes')+size>self.stage_caps['bytes']:
     raise LimitError('CUMULATIVE_STAGE_LIMIT')
   self._add('requests',1); self._add('bytes',size)
   if category in ('metadata','psf'): self._add(category+'_bytes',size)
   if self.stage:
    self._stage_add('requests',1); self._stage_add('bytes',size)
   cur=self.db.execute("INSERT INTO attempts(resource,category,reserved,state,stage,method) VALUES(?,?,?,'RESERVED',?,?)",(resource,category,size,self.stage,method))
   return cur.lastrowid
 def received(self,attempt,n):
  with self.transaction():
   row=self.db.execute('SELECT reserved,actual,state FROM attempts WHERE id=?',(attempt,)).fetchone()
   if not row or row[2]!='RESERVED' or n<0 or row[1]+n>row[0]: raise IntegrityError('RESPONSE_LIMIT_VIOLATION')
   self.db.execute('UPDATE attempts SET actual=actual+? WHERE id=?',(n,attempt))
 def finish(self,attempt,state):
  with self.transaction():
   row=self.db.execute('SELECT category,reserved,actual,state,stage FROM attempts WHERE id=?',(attempt,)).fetchone()
   if not row or row[3]!='RESERVED': raise IntegrityError('ATTEMPT_STATE_CONFLICT')
   category,reserved,actual,_,stage=row
   for key in ['bytes']+([category+'_bytes'] if category in ('metadata','psf') else []):
    self.db.execute('UPDATE counters SET v=v-? WHERE k=?',(reserved-actual,key))
   if stage:
    self.db.execute('UPDATE stage_counters SET v=v-? WHERE stage=? AND k=?',(reserved-actual,stage,'bytes'))
   self.db.execute('UPDATE attempts SET state=? WHERE id=?',(state,attempt))
 def recover(self):
  # Unknown bytes on crash are conservatively charged at the full reservation.
  with self.transaction(): self.db.execute("UPDATE attempts SET actual=reserved,state='CRASH_CHARGED' WHERE state='RESERVED'")
 def resource(self,rid):
  row=self.db.execute('SELECT state,offset,sha,path FROM resources WHERE id=?',(rid,)).fetchone()
  return dict(zip(('state','offset','sha','path'),row)) if row else None
 def update_resource(self,rid,state,offset,sha=None,path=None):
  with self.transaction(): self.db.execute('UPDATE resources SET state=?,offset=?,sha=?,path=? WHERE id=?',(state,offset,sha,path,rid))
 def summary(self):
  return dict(counters=dict(self.db.execute('SELECT k,v FROM counters')),limits=self.caps,
   ledger_identity=self.execution_id,current_stage=self.stage,
   stages=[dict(id=r[0],caps=json.loads(r[1]),state=r[2],counters=dict(self.db.execute('SELECT k,v FROM stage_counters WHERE stage=?',(r[0],)))) for r in self.db.execute('SELECT id,caps,state FROM stages ORDER BY id')],
   bindings=dict(self.db.execute('SELECT kind,value FROM bindings')),
   watermark=self.db.execute('SELECT COALESCE(MAX(seq),0) FROM events').fetchone()[0],
   attempts=[dict(zip(('id','resource','category','reserved','actual','state','stage','method'),r)) for r in self.db.execute('SELECT id,resource,category,reserved,actual,state,stage,method FROM attempts ORDER BY id')])

 def record_parent(self,parent):
  value=canonical(parent).decode()
  with self.transaction():
   old=self.db.execute("SELECT value FROM bindings WHERE kind='parent'").fetchone()
   if old and old[0]!=value: raise IntegrityError('PARENT_BINDING_CONFLICT')
   self.db.execute("INSERT OR IGNORE INTO bindings VALUES('parent',?)",(value,))
   if not old: self.db.execute("INSERT INTO events(kind,value) VALUES('PARENT',?)",(hash_object(parent),))

 def record_development(self,record):
  value=canonical(record).decode()
  with self.transaction():
   old=self.db.execute("SELECT value FROM bindings WHERE kind='development'").fetchone()
   if old and old[0]!=value: raise IntegrityError('DEVELOPMENT_SELECTION_CONFLICT')
   self.db.execute("INSERT OR IGNORE INTO bindings VALUES('development',?)",(value,))
   if not old: self.db.execute("INSERT INTO events(kind,value) VALUES('DEVELOPMENT',?)",(hash_object(record),))

 def record_receipt(self,receipt):
  value=canonical(receipt).decode()
  with self.transaction():
   old=self.db.execute("SELECT value FROM bindings WHERE kind='metadata_receipt'").fetchone()
   if old and old[0]!=value: raise IntegrityError('METADATA_RECEIPT_CONFLICT')
   self.db.execute("INSERT OR IGNORE INTO bindings VALUES('metadata_receipt',?)",(value,))
   if not old: self.db.execute("INSERT INTO events(kind,value) VALUES('METADATA_RECEIPT',?)",(hash_object(receipt),))

 def prepare_child(self,child):
  value=canonical(child).decode()
  with self.transaction():
   committed=self.db.execute("SELECT value FROM bindings WHERE kind='child'").fetchone()
   if committed: raise IntegrityError('SECOND_PROMOTION_FORBIDDEN')
   old=self.db.execute("SELECT value FROM bindings WHERE kind='prepared_child'").fetchone()
   if old and old[0]!=value: raise IntegrityError('PREPARED_CHILD_CONFLICT')
   self.db.execute("INSERT OR IGNORE INTO bindings VALUES('prepared_child',?)",(value,))
   if not old: self.db.execute("INSERT INTO events(kind,value) VALUES('PROMOTION_PREPARED',?)",(hash_object(child),))

 def commit_child(self,child,*,resume=False,crash_after=False):
  value=canonical(child).decode()
  with self.transaction():
   parent=self.db.execute("SELECT value FROM bindings WHERE kind='parent'").fetchone()
   prepared=self.db.execute("SELECT value FROM bindings WHERE kind='prepared_child'").fetchone()
   committed=self.db.execute("SELECT value FROM bindings WHERE kind='child'").fetchone()
   if not parent or not prepared or prepared[0]!=value: raise IntegrityError('PROMOTION_NOT_PREPARED')
   if committed:
    if resume and committed[0]==value: return False
    raise IntegrityError('SECOND_PROMOTION_FORBIDDEN')
   self.db.execute("INSERT INTO bindings VALUES('child',?)",(value,))
   self.db.execute("INSERT INTO events(kind,value) VALUES('PROMOTION_COMMITTED',?)",(hash_object(child),))
  if crash_after: raise OSError('SYNTHETIC_POST_COMMIT_CRASH')
  return True

 def child(self):
  row=self.db.execute("SELECT value FROM bindings WHERE kind='child'").fetchone()
  return json.loads(row[0]) if row else None

class RuntimeGuard:
 def __init__(self,ledger,root):
  self.ledger=ledger; self.root=Path(root); self.wall=time.monotonic(); self.cpu=time.process_time(); self.last=self.cpu
  self.initial_disk=sum(p.stat().st_size for p in self.root.rglob('*') if p.is_file())
 def check(self):
  now=time.process_time(); self.ledger.charge('compute_seconds',now-self.last); self.last=now
  if time.monotonic()-self.wall>self.ledger.caps['wall_seconds']: raise LimitError('WALL_LIMIT')
  if self.ledger.stage and time.monotonic()-self.wall>self.ledger.stage_caps['wall_seconds']: raise LimitError('STAGE_WALL_LIMIT')
  total=sum(p.stat().st_size for p in self.root.rglob('*') if p.is_file())
  if total>self.ledger.caps['disk_bytes']: raise IntegrityError('DISK_LIMIT_VIOLATION')
  if self.ledger.stage and total-self.initial_disk>self.ledger.stage_caps['disk_bytes']: raise LimitError('STAGE_DISK_LIMIT')
  # Linux resident memory, no network, no third-party dependency.
  stat=Path('/proc/self/statm')
  if stat.exists() and int(stat.read_text().split()[1])*os.sysconf('SC_PAGE_SIZE')>self.ledger.caps['ram_bytes']:
   raise LimitError('RAM_TARGET_EXCEEDED')
 def reserve_disk(self,n):
  total=sum(p.stat().st_size for p in self.root.rglob('*') if p.is_file())
  if n<0 or total+n>self.ledger.caps['disk_bytes']: raise LimitError('DISK_RESERVATION_LIMIT')
  if self.ledger.stage and total-self.initial_disk+n>self.ledger.stage_caps['disk_bytes']: raise LimitError('STAGE_DISK_RESERVATION_LIMIT')


def test_result(test,status,reason,binding,inputs=(),metrics=None,evidence=(),domain='full',unit='bundle'):
 if test not in tuple(f'T{i:02}' for i in range(1,13)) or status not in STATES: raise InputError('TEST_SCHEMA')
 return dict(test=test,status=status,reason=reason,applicable_inputs=list(inputs),authority_input_hashes=binding,
  metrics=metrics or {},evidence_refs=list(evidence),domain=domain,unit=unit)

def decide(records, *, integrity=False, full_slots=False, restricted_slots=False, rights=False):
 """A does NOT demonstrate DR9 representativeness. Generalization remains unresolved.
 Unknown/absent results never become VERIFIED; B requires its own explicit domain.
 """
 if integrity: return OUTCOMES[3]
 def complete(domain):
  group=[r for r in records if r.get('domain')==domain]
  return all(any(r['test']==f'T{i:02}' for r in group) for i in range(1,13)) and all(r['status']=='VERIFIED' for r in group)
 if rights and full_slots and complete('full'): return OUTCOMES[0]
 if rights and restricted_slots and complete('restricted'): return OUTCOMES[1]
 return OUTCOMES[2]
