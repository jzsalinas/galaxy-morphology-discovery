"""Explicit transport boundary: offline object holds no transport capability."""
from __future__ import annotations
from datetime import datetime, timezone
import http.client
import json
from pathlib import Path
import re
import ssl
from urllib.parse import urlsplit
from .core import (OfflineError,InputError,IntegrityError,LimitError,canonical,
 digest,file_hash,immutable_write,strict)

class OfflineNetwork:
 def open(self,*args,**kwargs): raise OfflineError('OFFLINE_TRANSPORT_UNAVAILABLE')

class HTTPTransport:
 """Future explicit HTTPS only. Never instantiated by default; no redirects/discovery."""
 def __init__(self,approved_resources):
  if isinstance(approved_resources,dict): self.approved=dict(approved_resources)
  else: self.approved={url:'GET' for url in approved_resources}
 def authorize_materialized(self,url,method):
  """Called only after Amendment-002 closed-role materialization."""
  if method not in ('GET','HEAD'): raise InputError('UNLISTED_HTTP_METHOD')
  old=self.approved.get(url)
  if old is not None and old!=method: raise IntegrityError('URL_METHOD_AUTHORIZATION_CONFLICT')
  self.approved[url]=method
 def open(self,url,headers,method='GET'):
  if url not in self.approved or self.approved[url]!=method: raise InputError('URL_METHOD_NOT_IN_SEALED_PLAN')
  u=urlsplit(url)
  if u.scheme!='https' or u.username or u.password or u.fragment or u.port not in (None,443): raise InputError('UNSAFE_URL')
  conn=http.client.HTTPSConnection(u.hostname,timeout=30,context=ssl.create_default_context())
  try:
   conn.request(method,u.path+('?' + u.query if u.query else ''),headers={'Accept-Encoding':'identity',**headers})
   response=conn.getresponse()
  except BaseException: conn.close(); raise
  return HTTPResponse(conn,response,url)

class HTTPResponse:
 def __init__(self,conn,response,url):
  self.conn=conn; self.response=response; self.status=response.status
  self.headers={k.lower():v for k,v in response.getheaders()}; self.final_url=url
 def read(self,n): return self.response.read(n)
 def close(self): self.response.close(); self.conn.close()

def resource_identity(resource):
 from .core import hash_object
 return 'r_'+hash_object({k:resource.get(k) for k in ('url','generation','product','region','brick','band','location','psf_center','pixel_scale')})

def validate_resource(resource,hosts):
 strict(resource,'resource',('id','url','category','product','stage','generation','release','max_bytes'))
 if resource['category'] not in ('metadata','psf','product'): raise InputError('RESOURCE_CATEGORY')
 if resource['stage'] not in ('metadata','aux','fixed'): raise InputError('RESOURCE_STAGE')
 if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',resource['id']): raise InputError('RESOURCE_ID')
 u=urlsplit(resource['url'])
 if u.scheme!='https' or u.hostname not in hosts or u.username or u.password or u.fragment or u.port not in (None,443):
  raise InputError('URL_NOT_APPROVED')
 if not isinstance(resource['max_bytes'],int) or resource['max_bytes']<=0: raise LimitError('UNBOUNDED_RESPONSE')
 if resource.get('size') is not None and not 0<resource['size']<=resource['max_bytes']: raise LimitError('RESOURCE_SIZE')
 if resource['release']!='DR9': raise IntegrityError('WRONG_RELEASE')
 if resource['category']=='psf' and resource['max_bytes']>2**20: raise LimitError('PSF_RESPONSE_BOUND')
 if resource.get('band') not in (None,'g','r','z'): raise InputError('BAND_SCHEMA')
 if resource['category']=='psf' and resource.get('band') not in ('g','r','z'): raise InputError('PSF_SINGLE_LOGICAL_BAND_REQUIRED')
 allowed={'metadata':{'metadata','ccd_provenance'},'aux':{'nexp','psfsize','maskbits'},'fixed':{'image','invvar','psf'}}
 if resource['product'] not in allowed[resource['stage']]: raise InputError('PRODUCT_STAGE_NOT_ALLOWED')
 if resource['category']!=('metadata' if resource['stage']=='metadata' else 'psf' if resource['product']=='psf' else 'product'): raise InputError('PRODUCT_CATEGORY_CONFLICT')
 return resource

class Acquisition:
 def __init__(self,root,ledger,network=None,guard=None):
  self.root=Path(root); self.ledger=ledger
  self.network=network if network is not None else OfflineNetwork(); self.guard=guard
 def event(self,obj):
  obj=dict(obj,utc=datetime.now(timezone.utc).isoformat())
  path=self.root/'provenance/OC3_HTTP_EVENTS.jsonl'; path.parent.mkdir(parents=True,exist_ok=True)
  data=canonical(obj)+b'\n'; self.ledger.charge('io_bytes',len(data))
  with path.open('ab') as f: f.write(data); f.flush()
 def parts(self,res,offset):
  directory=self.root/'RAW_IMMUTABLE/partials'/res['id']
  entries=[]
  if directory.exists():
   for p in directory.glob('*.part'):
    m=re.fullmatch(r'(\d+)-(\d+)\.([0-9a-f]{64})\.part',p.name)
    if not m: raise IntegrityError('PART_LAYOUT')
    start,end=int(m[1]),int(m[2])
    if end<offset:
     self.ledger.charge('io_bytes',p.stat().st_size)
     if file_hash(p)!=m[3] or p.stat().st_size!=end-start+1: raise IntegrityError('PART_HASH')
     entries.append((start,end,p))
  entries.sort(); pos=0
  for start,end,_ in entries:
   if start!=pos: raise IntegrityError('PART_RANGE_GAP_OR_OVERLAP')
   pos=end+1
  if pos!=offset: raise IntegrityError('PART_OFFSET')
  return entries
 def fetch(self,res,resume=False):
  # Offline/dry-run refusal must occur before creating reservations or evidence.
  if isinstance(self.network,OfflineNetwork): raise OfflineError('OFFLINE_TRANSPORT_UNAVAILABLE')
  self.ledger.register(res); state=self.ledger.resource(res['id'])
  if state['state']=='COMPLETE':
   if res.get('method','GET')=='HEAD': return None
   p=self.root/state['path']; self.ledger.charge('io_bytes',p.stat().st_size)
   if file_hash(p)!=state['sha']: raise IntegrityError('CACHE_CORRUPTION')
   return p
  method=res.get('method','GET'); offset=state['offset']
  if method not in ('GET','HEAD'): raise InputError('UNSUPPORTED_HTTP_METHOD')
  if method=='HEAD' and offset: raise IntegrityError('HEAD_CANNOT_RESUME_BODY')
  if offset and not resume: raise InputError('RESUME_REQUIRED')
  self.parts(res,offset)
  headers={}
  if offset:
   if not res.get('etag') or res['etag'].startswith('W/') or not res.get('size'):
    raise InputError('PARTIAL_IDENTITY_UNRESOLVED')
   headers={'Range':f'bytes={offset}-','If-Match':res['etag']}
  reserve=res['max_bytes']-offset
  if reserve<=0: raise IntegrityError('RESOURCE_NOT_COMPLETE_AT_BOUND')
  if self.guard: self.guard.reserve_disk(2*reserve); self.guard.check()
  token=self.ledger.reserve(res['id'],res['category'],reserve,method)
  response=None; received=0; start_offset=offset; success=False
  try:
   if isinstance(self.network,HTTPTransport):
    import time
    prior=self.ledger.db.execute('SELECT count(*) FROM attempts WHERE resource=? AND id<>?',(res['id'],token)).fetchone()[0]
    if prior: time.sleep((2,5)[min(prior,2)-1])
   try: response=self.network.open(res['url'],headers,method)
   except TypeError: response=self.network.open(res['url'],headers)  # Backward-compatible local fixture boundary.
   h={k.lower():v for k,v in response.headers.items()}
   self.event(dict(resource=res['id'],attempt=token,requested_url=res['url'],final_url=response.final_url,status=response.status,headers=h))
   if response.final_url!=res['url']: raise IntegrityError('UNPLANNED_REDIRECT')
   if h.get('content-encoding','identity')!='identity': raise IntegrityError('ENCODING_NOT_IDENTITY')
   if res.get('etag') and h.get('etag')!=res['etag']: raise IntegrityError('RESOURCE_GENERATION_CHANGED')
   if offset:
    expected=f"bytes {offset}-{res['size']-1}/{res['size']}"
    if response.status!=206 or h.get('content-range')!=expected: raise IntegrityError('RANGE_NOT_EXACT')
   elif response.status!=200:
    # Bounded failed response body is still charged, not cached as a product.
    while received<reserve:
     chunk=response.read(min(65536,reserve-received))
     if not chunk: break
     self.ledger.received(token,len(chunk)); received+=len(chunk)
    raise InputError('HTTP_FAILURE_NO_AUTORETRY')
   declared=int(h['content-length']) if 'content-length' in h else None
   if method=='HEAD':
    # Content-Length on HEAD describes the future GET representation, not a body to read.
    declared=0
   if declared is not None and declared>reserve: raise LimitError('BODY_EXCEEDS_RESERVATION')
   while received<reserve:
    if self.guard: self.guard.check()
    chunk=response.read(min(65536,reserve-received))
    if not chunk: break
    self.ledger.received(token,len(chunk)); received+=len(chunk)
    sh=digest(chunk); end=offset+len(chunk)-1
    part=self.root/'RAW_IMMUTABLE/partials'/res['id']/f'{offset}-{end}.{sh}.part'
    self.ledger.charge('io_bytes',len(chunk)); immutable_write(part,chunk)
    offset=end+1; self.ledger.update_resource(res['id'],'PARTIAL',offset)
   if declared is None and received==reserve: raise LimitError('UNKNOWN_BODY_REACHED_BOUND')
   if declared is not None and received!=declared: raise InputError('INTERRUPTED_BODY')
   if method=='GET' and res.get('size') is not None and offset!=res['size']: raise InputError('RESOURCE_INCOMPLETE')
   if method=='HEAD':
    checksum=digest(b'')
    self.ledger.update_resource(res['id'],'COMPLETE',0,checksum,None)
    success=True; return None
   # Streaming assembly, preserving fragments. Never read a brick into a bytes object.
   import hashlib, os
   parts=self.parts(res,offset); sh=hashlib.sha256()
   for _,_,p in parts:
    self.ledger.charge('io_bytes',p.stat().st_size)
    with p.open('rb') as f:
     for b in iter(lambda:f.read(65536),b''): sh.update(b)
   checksum=sh.hexdigest()
   if res.get('sha256') and checksum!=res['sha256']: raise IntegrityError('PROVIDER_CHECKSUM_MISMATCH')
   folder={'metadata':'metadata','psf':'psf','product':'products'}[res['category']]
   dest=self.root/'RAW_IMMUTABLE'/folder/res['id']/(checksum+'.body')
   if dest.exists():
    self.ledger.charge('io_bytes',dest.stat().st_size)
    if file_hash(dest)!=checksum: raise IntegrityError('CACHE_CONFLICT')
   else:
    dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('xb') as out:
     for _,_,p in parts:
      self.ledger.charge('io_bytes',2*p.stat().st_size)
      with p.open('rb') as f:
       for b in iter(lambda:f.read(65536),b''): out.write(b)
     out.flush(); os.fsync(out.fileno())
   self.ledger.update_resource(res['id'],'COMPLETE',offset,checksum,str(dest.relative_to(self.root)))
   success=True; return dest
  finally:
   if response is not None: response.close()
   self.ledger.finish(token,'COMPLETE' if success else 'FAILED')
   self.event(dict(resource=res['id'],attempt=token,body_bytes=received,range_start=start_offset,status='COMPLETE' if success else 'FAILED'))
