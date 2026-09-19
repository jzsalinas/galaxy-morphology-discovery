"""Human-executed C0.2 batch. Dry-run is offline; no bulk runs by the agent."""
import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from .core import Budget, Stop, fetch, sha, atomic_json, utc, MIB
from .run import ROOT, export


def plan():
    dep=json.loads((ROOT/'c0/provenance/PYARROW_DEPENDENCY_LOCK.json').read_text())
    record=json.loads((ROOT/'c0/provenance/raw_metadata/S2_version.raw').read_text())
    resource=next(f for f in record['files'] if f['key']=='gz_decals_volunteers_5.parquet')
    return dep,record,resource


def execute(args):
    dep,record,resource=plan()
    expected=dep['size']+resource['size']
    if args.dry_run:
        print(json.dumps(dict(action='manual dependency installation and Zenodo GZD-5 quarantine ingestion',
          declared_download_bytes=expected,max_additional_bytes=args.max_additional_mib*MIB,
          max_data_requests=2,automatic_retries=0,objects=0,http_timeout_seconds=args.http_timeout_seconds,
          dependency=dep['filename'],catalog=resource['key'],
          outputs=['SUBJECT_INDEX.parquet','CONFOUND_AUDIT_C0.parquet','INTERPRETATION_LOCKBOX','C0_ZENODO_INGEST_SUMMARY.json'],
          next='Stop for human confirmation and artifact inspection. No CDS or image acquisition.'),indent=2)); return 0
    b=Budget(ROOT/'c0/provenance');before=b.count('bytes')
    if expected>args.max_additional_mib*MIB: raise Stop('BATCH_BYTE_LIMIT')
    if sys.version_info[:2]!=(3,12): raise Stop('USE_PINNED_PYTHON_312')
    wheel=ROOT/'c0/dependencies'/dep['filename']
    e=fetch(b,dep['url'],wheel,'ENV-PYARROW',metadata=False,max_bytes=dep['size'])
    if e['access_result']!='VERIFIED':raise Stop('DEPENDENCY_FETCH_INCONCLUSIVE')
    if sha(wheel)!=dep['sha256']:raise Stop('DEPENDENCY_CHECKSUM_FAILED')
    env=ROOT/'c0/.venv'
    if not (env/'bin/python').exists():
        subprocess.run([sys.executable,'-m','venv',str(env)],check=True)
    py=str(env/'bin/python')
    subprocess.run([py,'-m','pip','install','--no-index','--no-deps','--disable-pip-version-check',str(wheel)],check=True)
    # Runtime identity and exact dependency version are recorded outside lockbox.
    installed=subprocess.check_output([py,'-c','import pyarrow;print(pyarrow.__version__)'],text=True).strip()
    if installed!=dep['version']:raise Stop('DEPENDENCY_VERSION_MISMATCH')
    atomic_json(ROOT/'c0/provenance/C0_INGEST_ENVIRONMENT.json',dict(python=py,pyarrow=installed,wheel_sha256=dep['sha256']))
    dest=ROOT/'c0/quarantine/RAW_IMMUTABLE'/resource['key']
    e=fetch(b,resource['links']['self'],dest,'S2',metadata=False,max_bytes=resource['size'],timeout_seconds=args.http_timeout_seconds)
    if e['access_result']!='VERIFIED':raise Stop('CATALOG_FETCH_INCONCLUSIVE')
    if b.count('bytes')-before>args.max_additional_mib*MIB:raise Stop('BATCH_BYTE_LIMIT')
    if hashlib.md5(dest.read_bytes()).hexdigest()!=resource['checksum'].split(':')[1]:raise Stop('PROVIDER_CHECKSUM_MISMATCH')
    # Ingest automatically in the same operation; never expose catalog values.
    result=subprocess.run([py,'-m','c0_pipeline.manual_ingest','--ingest-only'],cwd=ROOT,check=False)
    if result.returncode:raise Stop('QUARANTINE_INGEST_FAILED')
    return 0


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dry-run',action='store_true')
    p.add_argument('--max-additional-mib',type=int,default=100)
    p.add_argument('--http-timeout-seconds',type=int,choices=range(1,121),metavar='1..120',default=120,help='Timeout por operación HTTP del catálogo; sin reintentos automáticos')
    p.add_argument('--ingest-only',action='store_true',help=argparse.SUPPRESS)
    args=p.parse_args()
    if args.ingest_only:
        try:
            from .ingest import ingest
            dep,record,r=plan()
            ingest(ROOT/'c0/quarantine/RAW_IMMUTABLE'/r['key'],record['doi'],r['checksum'].split(':')[1])
            return 0
        except Exception as e:
            print('INGEST_FAILURE_TYPE='+type(e).__name__);return 2
    if args.dry_run:return execute(args)
    log=ROOT/'c0/logs/C0_MANUAL_INGEST.log'
    with open(ROOT/'c0/provenance/manual_execution.lock','w') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:print('C0_MANUAL_BUSY');return 2
        with open(log,'a',buffering=1) as output:
            try:
                with contextlib.redirect_stdout(output),contextlib.redirect_stderr(output):
                    print('START',utc())
                    # Subprocesses inherit terminal FDs unless explicitly redirected.
                    with open(os.devnull,'r') as unused:
                        saved1=os.dup(1);saved2=os.dup(2)
                        try:
                            os.dup2(output.fileno(),1);os.dup2(output.fileno(),2)
                            rc=execute(args)
                        finally:
                            os.dup2(saved1,1);os.dup2(saved2,2);os.close(saved1);os.close(saved2)
                    print('END',utc(),rc)
            except Exception as exc:
                output.write('FAILURE_TYPE='+type(exc).__name__+'\n')
                if isinstance(exc,Stop):output.write('REASON='+str(exc)+'\n')
                rc=2
    from .inventory import build
    build()
    state=dict(timestamp_utc=utc(),exit_code=rc,status='C0_MANUAL_INGEST_OK' if rc==0 else 'C0_MANUAL_INGEST_FAILED',log=str(log))
    if rc:
        ledger=Budget(ROOT/'c0/provenance')
        recent=ledger.events()
        if recent and recent[-1].get('access_result')!='VERIFIED':
            failure=recent[-1]
            state['transport_failure']={key:failure.get(key) for key in ('http_status','error_type','reason','transfer_stage','observed_bytes')}
        ledger.db.close()
    atomic_json(ROOT/'c0/reports/C0_MANUAL_STATUS.json',state)
    print(state['status'])
    if state.get('transport_failure'):
        print('TRANSPORT_DETAIL='+json.dumps(state['transport_failure']))
    return rc

if __name__=='__main__':sys.exit(main())
