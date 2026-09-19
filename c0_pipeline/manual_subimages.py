"""Manual bounded DR5 subimages and brick routes; no whole bricks downloaded."""
import argparse
import contextlib
import fcntl
import json
from pathlib import Path
import sys
from .core import Budget,Stop,fetch,atomic_json,utc,MIB
from .run import ROOT


def execute(args):
 import pyarrow as pa
 import pyarrow.parquet as pq
 from .subimage_audit import audit
 report=pq.read_table(ROOT/'c0/probe/C0_PROBE_FITS_REPORT.parquet').to_pylist()
 if len(report)!=96:raise Stop('PROBE_NOT_COMPLETE')
 # Point lookup of the fixed IDs, using permitted identity fields only.
 ids=[r['galaxy_id'] for r in report]
 subjects=pq.read_table(ROOT/'c0/quarantine/SUBJECT_INDEX.parquet',columns=['galaxy_id','ra_deg','dec_deg'],filters=[('galaxy_id','in',ids)]).to_pylist()
 lookup={r['galaxy_id']:r for r in subjects}
 b=Budget(ROOT/'c0/provenance');start=b.count('bytes');out=[];routes=[]
 def get(url,path,cap):
  if b.count('bytes')-start+cap>args.max_additional_mib*MIB:raise Stop('BATCH_TRANSFER_LIMIT')
  e=fetch(b,url,path,'S7',metadata=False,max_bytes=cap,timeout_seconds=120)
  if e['access_result']!='VERIFIED':raise Stop('SUBIMAGE_OR_BRICK_ACCESS_INCONCLUSIVE')
  return e
 def save():
  for path,rows in [('C0_SUBIMAGE_REPORT.parquet',out),('C0_BRICK_ROUTES.parquet',routes)]:
   if rows:
    p=ROOT/'c0/probe'/path;t=p.with_suffix('.tmp');pq.write_table(pa.Table.from_pylist(rows),t);t.replace(p)
 for r in sorted(report,key=lambda x:x['probe_rank']):
  rank=r['probe_rank'];s=lookup[r['galaxy_id']];b.object(r['galaxy_id'])
  sub=ROOT/'c0/probe/subimages'/f'{rank:03d}.fits'
  if rank==1:sub=ROOT/'c0/probe/dr5_subimage_smoke.fits'
  get(r['url']+'&subimage',sub,8*MIB)
  a=audit(sub)
  out.append(dict(galaxy_id=r['galaxy_id'],probe_rank=rank,path=str(sub),audit_json=json.dumps(a)))
  save()
  ra=s['ra_deg'];dec=s['dec_deg']
  url=f'https://www.legacysurvey.org/viewer/bricks/?ralo={ra-0.001}&rahi={ra+0.001}&declo={dec-0.001}&dechi={dec+0.001}&layer=decals-dr5'
  path=ROOT/'c0/probe/bricks'/f'{rank:03d}.json'
  if rank==1:path=ROOT/'c0/probe/dr5_bricks_smoke.json'
  get(url,path,MIB)
  response=json.loads(path.read_text());polys=response.get('polys')
  if not isinstance(polys,list) or not polys:raise Stop('BRICK_ROUTE_MISSING')
  names=set()
  for poly in polys:
   name=poly['name']
   import re
   if not re.fullmatch(r'[0-9]{4}[pm][0-9]{3}',name):raise Stop('BRICK_NAME_INVALID')
   names.add(name)
  # Subimage can overlap more than the central query's bricks; preserve all.
  names.update(p['brick'] for p in a['products'])
  for name in sorted(names):
   routes.append(dict(galaxy_id=r['galaxy_id'],probe_rank=rank,brickname=name,association='SPATIAL_BRICK_NOT_TRACTOR_MATCH',coadd_directory=f'https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr5/coadd/{name[:3]}/{name}/',tractor_candidate_url=f'https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr5/tractor/{name[:3]}/tractor-{name}.fits',comparison_subset=rank<=12))
  save()
 atomic_json(ROOT/'c0/reports/C0_SUBIMAGE_SUMMARY.json',dict(timestamp_utc=utc(),objects=len(out),brick_associations=len(routes),unique_bricks=len({r['brickname'] for r in routes}),additional_charged_bytes=b.count('bytes')-start,notes=['Brick association is not a source match','Units and official coadd comparison pending','Mask, nexp and PSF not supplied by this response']))


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dry-run',action='store_true');p.add_argument('--max-additional-mib',type=int,default=250);args=p.parse_args()
 if args.dry_run:
  print('96 fixed objects; subimage+brick query; first two resources cached; at most 190 new requests; cap 250 MiB; no automatic retries; no full brick or Tractor download');return 0
 log=ROOT/'c0/logs/C0_MANUAL_SUBIMAGES.log';rc=2
 with open(ROOT/'c0/provenance/manual_execution.lock','w') as mutex:
  try:fcntl.flock(mutex,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:print('C0_MANUAL_BUSY');return 2
  with open(log,'a',buffering=1) as output,contextlib.redirect_stdout(output),contextlib.redirect_stderr(output):
   print('START',utc())
   try:execute(args);rc=0
   except Exception as exc:print('FAILURE',str(exc) if isinstance(exc,Stop) else type(exc).__name__)
   print('END',utc(),rc)
 from .inventory import build
 build()
 state=dict(timestamp_utc=utc(),exit_code=rc,status='C0_MANUAL_SUBIMAGES_OK' if rc==0 else 'C0_MANUAL_SUBIMAGES_FAILED',log=str(log))
 atomic_json(ROOT/'c0/reports/C0_MANUAL_SUBIMAGES_STATUS.json',state);print(state['status']);return rc
if __name__=='__main__':sys.exit(main())
