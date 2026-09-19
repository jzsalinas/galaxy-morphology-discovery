"""Human-executed CDS download and identity-only comparison; no image requests."""
import argparse
import contextlib
import fcntl
import json
import sys
from .core import Budget, Stop, fetch, atomic_json, utc, MIB
from .run import ROOT


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dry-run',action='store_true')
    p.add_argument('--max-additional-mib',type=int,default=40)
    p.add_argument('--http-timeout-seconds',type=int,default=120)
    args=p.parse_args()
    lock=json.loads((ROOT/'c0/provenance/C0_CDS_RESOURCE_LOCK.json').read_text())
    size=int(lock['declared_bytes'])
    if args.dry_run:
        print(json.dumps(dict(url=lock['url'],declared_bytes=size,max_additional_bytes=args.max_additional_mib*MIB,
          max_expanded_bytes=300*MIB,requests=1,automatic_retries=0,objects=0,
          inputs=['SUBJECT_INDEX.parquet','C0_CDS_RESOURCE_LOCK.json','S3.raw'],
          outputs=['CDS_IDENTITY_RECONCILIATION.parquet','C0_CDS_RECONCILIATION_SUMMARY.json']),indent=2));return 0
    if size>args.max_additional_mib*MIB or not 1<=args.http_timeout_seconds<=120:
        print('INVALID_LIMITS');return 2
    log=ROOT/'c0/logs/C0_MANUAL_CDS.log'
    rc=2;reason=None
    with open(ROOT/'c0/provenance/manual_execution.lock','w') as mutex:
        try:fcntl.flock(mutex,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:print('C0_MANUAL_BUSY');return 2
        with open(log,'a',buffering=1) as output,contextlib.redirect_stdout(output),contextlib.redirect_stderr(output):
            print('START',utc())
            try:
                # Validate dependency before a data request.
                import pyarrow
                b=Budget(ROOT/'c0/provenance')
                dest=ROOT/'c0/quarantine/RAW_IMMUTABLE/gzdv5.dat.gz'
                e=fetch(b,lock['url'],dest,'S3',metadata=False,max_bytes=size,timeout_seconds=args.http_timeout_seconds)
                if e['access_result']!='VERIFIED':
                    print('TRANSPORT_DETAIL',json.dumps({k:e.get(k) for k in ['http_status','error_type','reason','transfer_stage']}))
                    raise Stop('CDS_FETCH_INCONCLUSIVE')
                if e['observed_bytes']!=size:raise Stop('CDS_DECLARED_SIZE_MISMATCH')
                from .reconcile import reconcile
                result=reconcile(dest)
                print('SUMMARY',json.dumps(result))
                rc=0
            except Exception as exc:
                reason=str(exc) if isinstance(exc,Stop) else type(exc).__name__
                print('FAILURE',reason)
            print('END',utc(),rc)
    from .inventory import build
    build()
    state=dict(timestamp_utc=utc(),exit_code=rc,status='C0_MANUAL_CDS_OK' if rc==0 else 'C0_MANUAL_CDS_FAILED',reason=reason,log=str(log))
    atomic_json(ROOT/'c0/reports/C0_MANUAL_CDS_STATUS.json',state)
    print(state['status']);return rc

if __name__=='__main__':sys.exit(main())
