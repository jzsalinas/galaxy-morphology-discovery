"""Manual local bulk selection; zero network, no image processing."""
import argparse
import contextlib
import fcntl
import json
import random
import sys
from .core import Budget,Stop,atomic_json,sha,utc
from .run import ROOT


def execute():
    import pyarrow as pa
    import pyarrow.parquet as pq
    from .probe import select
    subject=ROOT/'c0/quarantine/SUBJECT_INDEX.parquet'
    confound=ROOT/'c0/quarantine/CONFOUND_AUDIT_C0.parquet'
    s=pq.read_table(subject,columns=['galaxy_id','ra_deg','dec_deg','source_row']).to_pylist()
    c=pq.read_table(confound,columns=['galaxy_id','petro_theta','active_learning_on']).to_pylist()
    lookup={r['galaxy_id']:r for r in c}
    if len(lookup)!=len(c):raise Stop('DUPLICATE_CONFOUND_ID')
    if set(lookup)!={r['galaxy_id'] for r in s}:raise Stop('CONFOUND_JOIN_MISMATCH')
    rows=[dict(r,petro_radius=lookup[r['galaxy_id']]['petro_theta'],active_learning_on=lookup[r['galaxy_id']]['active_learning_on']) for r in s]
    chosen=select(rows)
    # Acceptance: a different input ordering must preserve all probe rows.
    shuffled=list(rows);random.Random(11).shuffle(shuffled)
    if select(shuffled)!=chosen:raise Stop('ROW_ORDER_INVARIANCE_FAILED')
    budget=Budget(ROOT/'c0/provenance')
    # Persist all 96 atomically; never leave a partially registered probe.
    with budget.db:
        budget.db.execute('BEGIN IMMEDIATE')
        existing={r[0] for r in budget.db.execute('SELECT id FROM objects')}
        ids={r['galaxy_id'] for r in chosen}
        if len(existing|ids)>96:raise Stop('OBJECT_LIMIT')
        budget.db.executemany('INSERT OR IGNORE INTO objects VALUES(?)',[(x,) for x in sorted(ids)])
    dest=ROOT/'c0/probe/C0_PROBE_MANIFEST.parquet';tmp=dest.with_suffix('.tmp')
    pq.write_table(pa.Table.from_pylist(chosen),tmp,compression='zstd');tmp.replace(dest)
    summary=dict(timestamp_utc=utc(),objects=96,seed=11,source_sha256=sha(subject),confound_sha256=sha(confound),probe_sha256=sha(dest),row_order_invariance=True,
      quotas_ra=[sum(r['stratum_ra']==q for r in chosen) for q in range(4)],
      active_true=sum(r['active_learning_stratum'] is True for r in chosen),active_false=sum(r['active_learning_stratum'] is False for r in chosen),
      method='Rank quartiles; RA ties by galaxy_id; size quartiles within RA, ties by galaxy_id; 6 per cell; up to 2 per active state initially then quota completion then hash fill',
      limitations=['Availability-bias comparison pending','No image recovery or morphology inspection','No physical size filter; inherited radius used only for specified stratification'])
    atomic_json(ROOT/'c0/reports/C0_PROBE_SELECTION_SUMMARY.json',summary)
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dry-run',action='store_true');args=p.parse_args()
    if args.dry_run:
        print('OFFLINE: read permitted projections; select 96; test shuffled input; persist probe; no downloads');return 0
    log=ROOT/'c0/logs/C0_MANUAL_PROBE.log';rc=2
    with open(ROOT/'c0/provenance/manual_execution.lock','w') as mutex:
        try:fcntl.flock(mutex,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:print('C0_MANUAL_BUSY');return 2
        with open(log,'a',buffering=1) as output,contextlib.redirect_stdout(output),contextlib.redirect_stderr(output):
            print('START',utc())
            try:print(json.dumps(execute()));rc=0
            except Exception as e:print('FAILURE',str(e) if isinstance(e,Stop) else type(e).__name__)
            print('END',utc(),rc)
    state=dict(timestamp_utc=utc(),exit_code=rc,status='C0_MANUAL_PROBE_OK' if rc==0 else 'C0_MANUAL_PROBE_FAILED',log=str(log))
    atomic_json(ROOT/'c0/reports/C0_MANUAL_PROBE_STATUS.json',state);print(state['status']);return rc
if __name__=='__main__':sys.exit(main())
