"""Bounded HTTP ranges; never accept a server's whole-file fallback."""
import hashlib
import io
import os
import re
import urllib.request
import urllib.error
from pathlib import Path
from .core import Budget,Stop,NoRedirect,utc,sha,LIMIT_BYTES


def fetch_range(budget,url,start,end,total,dest,etag=None):
 dest=Path(dest);length=end-start+1
 if not 0<=start<=end<total or length>8*1024**2:raise Stop('RANGE_OUTSIDE_LIMIT')
 for e in reversed(budget.events()):
  if e.get('url')==url and e.get('range_start')==start and e.get('range_end')==end and e.get('access_result')=='VERIFIED_RANGE' and dest.exists() and sha(dest)==e['sha256']:
   return e
 if budget.count('bytes')+length>LIMIT_BYTES:raise Stop('BYTE_LIMIT')
 budget.request(url,False)
 event=dict(source_id='S6',url=url,final_url=url,retrieved_at_utc=utc(),metadata=False,range_start=start,range_end=end,resource_total_bytes=total,observed_bytes=0,local_logical_path=str(dest),access_result='INCONCLUSIVE')
 try:
  headers={'Range':f'bytes={start}-{end}','Accept-Encoding':'identity','User-Agent':'GalaxyMorphology-C0/0.1'}
  if etag:headers['If-Range']=etag
  try:r=urllib.request.build_opener(NoRedirect).open(urllib.request.Request(url,headers=headers),timeout=25)
  except urllib.error.HTTPError as exc:r=exc
  with r:
   event.update(http_status=r.code,etag=r.headers.get('ETag'),content_range=r.headers.get('Content-Range'))
   if r.code!=206:raise Stop('EXACT_HTTP_RANGE_NOT_SUPPORTED')
   if r.headers.get('Content-Range')!=f'bytes {start}-{end}/{total}':raise Stop('RANGE_RESPONSE_MISMATCH')
   if etag and r.headers.get('ETag')!=etag:raise Stop('RANGE_ETAG_CHANGED')
   dest.parent.mkdir(parents=True,exist_ok=True);tmp=dest.with_suffix('.part')
   with tmp.open('wb') as f:
    while event['observed_bytes']<length:
     n=min(65536,length-event['observed_bytes']);budget.charge(n)
     block=r.read(n)
     with budget.db:budget.db.execute("UPDATE counters SET n=n-? WHERE k='bytes'",(n-len(block),))
     f.write(block);event['observed_bytes']+=len(block)
     if not block:raise Stop('RANGE_TRUNCATED')
   os.replace(tmp,dest);dest.chmod(0o400)
   event.update(access_result='VERIFIED_RANGE',sha256=sha(dest))
 except Exception as exc:
  event['error_type']=type(exc).__name__
  if isinstance(exc,Stop):event['reason']=str(exc)
 finally:budget.event(event)
 return event


class RangeView(io.RawIOBase):
 """Read-only virtual file. Missing ranges raise; never fabricate missing bytes."""
 def __init__(self,total,segments):
  super().__init__();self.total=total;self.segments=sorted(segments);self.pos=0
 def readable(self):return True
 def seekable(self):return True
 def tell(self):return self.pos
 def seek(self,offset,whence=0):
  target=offset if whence==0 else self.pos+offset if whence==1 else self.total+offset
  if target<0:raise ValueError('Negative seek')
  self.pos=target;return target
 def read(self,size=-1):
  if self.pos>=self.total:return b''
  if size<0:size=self.total-self.pos
  end=min(self.pos+size,self.total);out=[]
  while self.pos<end:
   hits=[(start,data) for start,data in self.segments if start<=self.pos<start+len(data)]
   if not hits:raise Stop('UNFETCHED_RANGE_READ')
   start,data=hits[-1];n=min(end-self.pos,start+len(data)-self.pos)
   out.append(data[self.pos-start:self.pos-start+n]);self.pos+=n
  return b''.join(out)
 def readinto(self,b):
  data=self.read(len(b));b[:len(data)]=data;return len(data)
