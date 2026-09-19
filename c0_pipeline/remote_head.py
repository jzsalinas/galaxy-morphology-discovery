"""Auditable metadata-only requests; no response bodies or automatic retries."""
import urllib.request
import urllib.error
from .core import Stop,utc,NoRedirect


def head(budget,url,source='S6',timeout=25):
 for e in reversed(budget.events()):
  if e.get('method')=='HEAD' and e.get('url')==url and e.get('http_status')==200:
   return e
 budget.request(url,True)
 e=dict(source_id=source,url=url,final_url=url,method='HEAD',metadata=True,retrieved_at_utc=utc(),observed_bytes=0,access_result='INCONCLUSIVE')
 try:
  try:r=urllib.request.build_opener(NoRedirect).open(urllib.request.Request(url,method='HEAD',headers={'User-Agent':'GalaxyMorphology-C0/0.1'}),timeout=timeout)
  except urllib.error.HTTPError as exc:r=exc
  with r:
   e.update(http_status=r.code,declared_bytes=r.headers.get('Content-Length'),etag=r.headers.get('ETag'),last_modified=r.headers.get('Last-Modified'),accept_ranges=r.headers.get('Accept-Ranges'),location=r.headers.get('Location'),access_result='METADATA_ONLY' if r.code==200 else 'INCONCLUSIVE')
 except Exception as exc:e['error_type']=type(exc).__name__
 budget.event(e)
 return e
