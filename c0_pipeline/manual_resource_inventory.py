"""Human-executed DR5 metadata inventory. No product bodies downloaded."""
import argparse
import contextlib
import csv
import fcntl
import json
import sys
from .core import Budget,Stop,atomic_json,utc,LIMIT_BYTES
from .remote_head import head
from .run import ROOT


def plan(routes):
 result={}
 def add(url,kind,route,band=None):
  if url not in result:result[url]=dict(url=url,product=kind,brickname=route['brickname'],band=band,galaxy_ids=set(),probe_ranks=set())
  result[url]['galaxy_ids'].add(route['galaxy_id']);result[url]['probe_ranks'].add(route['probe_rank'])
 for r in routes:
  add(r['tractor_candidate_url'],'tractor',r)
  base=r['coadd_directory'];brick=r['brickname']
  for band in 'grz':
   add(base+f'legacysurvey-{brick}-nexp-{band}.fits.fz','nexp',r,band)
   if r['comparison_subset']:
    add(base+f'legacysurvey-{brick}-image-{band}.fits.fz','comparison_image',r,band)
 for r in result.values():
  r['galaxy_ids']=sorted(r['galaxy_ids']);r['probe_ranks']=sorted(r['probe_ranks'])
 return sorted(result.values(),key=lambda r:(r['product'],r['url']))


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dry-run',action='store_true');p.add_argument('--max-metadata-requests',type=int,default=600);args=p.parse_args()
 import pyarrow.parquet as pq
 items=plan(pq.read_table(ROOT/'c0/probe/C0_BRICK_ROUTES.parquet').to_pylist())
 if args.dry_run:
  from collections import Counter
  print(json.dumps(dict(resources=len(items),products=dict(Counter(r['product'] for r in items)),data_body_bytes=0,nonmetadata_requests=0,max_metadata_requests=args.max_metadata_requests),indent=2));return 0
 if len(items)>args.max_metadata_requests:print('METADATA_PLAN_EXCEEDS_LIMIT');return 2
 log=ROOT/'c0/logs/C0_MANUAL_RESOURCE_INVENTORY.log';rc=2
 with open(ROOT/'c0/provenance/manual_execution.lock','w') as mutex:
  try:fcntl.flock(mutex,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:print('C0_MANUAL_BUSY');return 2
  with open(log,'a',buffering=1) as output,contextlib.redirect_stdout(output),contextlib.redirect_stderr(output):
   print('START',utc())
   try:
    atomic_json(ROOT/'c0/provenance/C0_DR5_RESOURCE_PLAN.json',items)
    b=Budget(ROOT/'c0/provenance');rows=[];consecutive_failures=0
    for item in items:
     e=head(b,item['url'])
     row=dict(item,http_status=e.get('http_status'),declared_bytes=e.get('declared_bytes'),etag=e.get('etag'),last_modified=e.get('last_modified'),accept_ranges=e.get('accept_ranges'),access_result=e['access_result'])
     rows.append(row)
     atomic_json(ROOT/'c0/provenance/C0_DR5_RESOURCE_INVENTORY.json',rows)
     # A rate-limit is not an invitation to wait/retry automatically.
     if e.get('http_status')==429:raise Stop('SERVICE_THROTTLED_STOP')
     consecutive_failures=0 if e.get('http_status')==200 else consecutive_failures+1
     if consecutive_failures>=3:raise Stop('CONSECUTIVE_METADATA_FAILURES_STOP')
    totals={}
    for r in rows:
     t=totals.setdefault(r['product'],dict(resources=0,verified_size_resources=0,known_bytes=0,unresolved_resources=0));t['resources']+=1
     if r['http_status']==200 and r['declared_bytes'] is not None:
      t['verified_size_resources']+=1;t['known_bytes']+=int(r['declared_bytes'])
     else:t['unresolved_resources']+=1
    known=sum(t['known_bytes'] for t in totals.values())
    atomic_json(ROOT/'c0/reports/C0_DR5_RESOURCE_INVENTORY_SUMMARY.json',dict(timestamp_utc=utc(),products=totals,all_products_known_bytes=known,c0_charged_bytes=b.count('bytes'),c0_remaining_bytes=LIMIT_BYTES-b.count('bytes'),all_whole_files_fit_remaining=known<=LIMIT_BYTES-b.count('bytes') and all(t['unresolved_resources']==0 for t in totals.values()),note='HEAD sizes only; no product bodies acquired; negative fit result forbids whole-file plan, not a formal Gate F decision'))
    rc=0
   except Exception as exc:print('FAILURE',str(exc) if isinstance(exc,Stop) else type(exc).__name__)
   print('END',utc(),rc)
 from .inventory import build
 build()
 state=dict(timestamp_utc=utc(),exit_code=rc,status='C0_RESOURCE_INVENTORY_OK' if rc==0 else 'C0_RESOURCE_INVENTORY_FAILED',log=str(log))
 atomic_json(ROOT/'c0/reports/C0_RESOURCE_INVENTORY_STATUS.json',state);print(state['status']);return rc
if __name__=='__main__':sys.exit(main())
