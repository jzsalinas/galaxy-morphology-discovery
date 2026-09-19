"""Manual bounded DR5 cutout probe, not complete C0.3 or a Gate decision."""
import argparse
import contextlib
import fcntl
import json
import sys
from pathlib import Path
from .core import Budget,Stop,fetch,atomic_json,utc,MIB
from .run import ROOT


def execute(args):
 import pyarrow as pa
 import pyarrow.parquet as pq
 from .fits_audit import inspect
 # 96 chosen IDs only; read permitted identity columns with a predicate.
 probe=pq.read_table(ROOT/'c0/probe/C0_PROBE_MANIFEST.parquet').to_pylist()
 if len(probe)!=96 or len({r['galaxy_id'] for r in probe})!=96:raise Stop('INVALID_PROBE')
 ids=[r['galaxy_id'] for r in probe]
 subjects=pq.read_table(ROOT/'c0/quarantine/SUBJECT_INDEX.parquet',columns=['galaxy_id','ra_deg','dec_deg'],filters=[('galaxy_id','in',ids)]).to_pylist()
 lookup={r['galaxy_id']:r for r in subjects}
 if set(lookup)!=set(ids):raise Stop('PROBE_IDENTITY_JOIN_FAILED')
 budget=Budget(ROOT/'c0/provenance');start=budget.count('bytes');rows=[];failures=0
 for chosen in sorted(probe,key=lambda r:r['probe_rank']):
  r=lookup[chosen['galaxy_id']];budget.object(r['galaxy_id'])
  url=f"https://www.legacysurvey.org/viewer/fits-cutout?ra={r['ra_deg']:.15g}&dec={r['dec_deg']:.15g}&layer=decals-dr5&pixscale=0.262&size=256&bands=grz"
  path=ROOT/'c0/probe/dr5'/f"{chosen['probe_rank']:03d}.fits"
  # Reuse the existing smoke-test response without acquiring it again.
  if chosen['probe_rank']==1:
   smoke=json.loads((ROOT/'c0/probe/C0_DR5_SMOKE_REQUEST.json').read_text())
   if smoke['galaxy_id']==r['galaxy_id'] and smoke['url']==url:path=ROOT/'c0/probe/dr5_smoke.fits'
  if budget.count('bytes')-start+2*MIB>args.max_additional_mib*MIB:raise Stop('BATCH_TRANSFER_LIMIT')
  e=fetch(budget,url,path,'S7',metadata=False,max_bytes=2*MIB,timeout_seconds=120)
  row=dict(galaxy_id=r['galaxy_id'],probe_rank=chosen['probe_rank'],url=url,path=str(path),http_status=e.get('http_status'),retrieval_status=e['access_result'],technical_status='NOT_INSPECTED',audit_json=None)
  if e['access_result']=='VERIFIED':
   try:
    audit=inspect(path,r['ra_deg'],r['dec_deg']);row.update(technical_status='HEADER_GEOMETRY_CHECKED',audit_json=json.dumps(audit))
   except Exception as exc:
    row['technical_status']=str(exc) if isinstance(exc,Stop) else type(exc).__name__
    rows.append(row);write(rows)
    raise Stop('DR5_TECHNICAL_FAILURE_REVIEW_REQUIRED') from None
  else:
   if e.get('reason') in ('BYTE_LIMIT','INSUFFICIENT_RESERVED_BUDGET','DATA_REQUEST_LIMIT','RESOURCE_RETRIES_EXHAUSTED'):
    rows.append(row);write(rows);raise Stop(e['reason'])
   failures+=1
  rows.append(row);write(rows)
  if failures>=7:raise Stop('DR5_SEVEN_RETRIEVAL_FAILURES_STOP')
 summary=dict(timestamp_utc=utc(),objects=len(rows),retrieved=sum(r['retrieval_status']=='VERIFIED' for r in rows),failures=failures,additional_charged_bytes=budget.count('bytes')-start,
  status='CUTOUT_STAGE_COMPLETE_NOT_C0_3_COMPLETE',pending=['Tractor matches and ambiguity audit','Documented flux calibration and 12 coadd comparisons','Auxiliary products','C0-C and C0-D formal evaluation'])
 atomic_json(ROOT/'c0/reports/C0_DR5_CUTOUT_SUMMARY.json',summary)


def write(rows):
 import pyarrow as pa
 import pyarrow.parquet as pq
 path=ROOT/'c0/probe/C0_PROBE_FITS_REPORT.parquet';tmp=path.with_suffix('.tmp')
 pq.write_table(pa.Table.from_pylist(rows),tmp);tmp.replace(path)


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dry-run',action='store_true');p.add_argument('--max-additional-mib',type=int,default=200);args=p.parse_args()
 if args.dry_run:
  print('96 fixed IDs; existing first cutout cached; at most 95 new files; 2 MiB/resource; batch 200 MiB default; no automatic retries; no final Gate assessment');return 0
 log=ROOT/'c0/logs/C0_MANUAL_DR5.log';rc=2
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
 state=dict(timestamp_utc=utc(),exit_code=rc,status='C0_MANUAL_DR5_OK' if rc==0 else 'C0_MANUAL_DR5_FAILED',log=str(log))
 atomic_json(ROOT/'c0/reports/C0_MANUAL_DR5_STATUS.json',state);print(state['status']);return rc
if __name__=='__main__':sys.exit(main())
