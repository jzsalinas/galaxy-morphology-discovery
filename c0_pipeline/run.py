"""Bounded C0 preflight and source discovery."""
import argparse
import csv
import importlib.util
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from .core import Budget, fetch, atomic_json, sha, utc, MIB

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [
 ('S1','Galaxy Zoo official discovery','https://data.galaxyzoo.org/'),
 ('S2','Zenodo record metadata','https://zenodo.org/api/records/4196266'),
 ('S3','CDS byte dictionary','https://cdsarc.cds.unistra.fr/ftp/J/MNRAS/509/3966/ReadMe'),
 ('S4','Walmsley 2022 v2','https://arxiv.org/html/2102.08414v2'),
 ('S5','DR5 description','https://www.legacysurvey.org/dr5/description/'),
 ('S6','DR5 files','https://www.legacysurvey.org/dr5/files/'),
 ('S7','Viewer URL documentation','https://www.legacysurvey.org/viewer/urls'),
 ('S8','NSA official model candidate','https://data.sdss.org/datamodel/files/ATLAS_DATA/ATLAS_MAJOR_VERSION/nsa.html'),
 ('S9','SDSS DR8','https://www.sdss3.org/dr8/'),
]

def preflight():
    for d in ['provenance/raw_metadata','schemas/C0_SCHEMA_SNAPSHOT','quarantine/RAW_IMMUTABLE',
              'quarantine/INTERPRETATION_LOCKBOX','probe','reports','logs']:
        (ROOT/'c0'/d).mkdir(parents=True,exist_ok=True)
    (ROOT/'c0/quarantine/INTERPRETATION_LOCKBOX').chmod(0o700)
    (ROOT/'c0/quarantine/RAW_IMMUTABLE').chmod(0o700)
    policy=dict(addendum='C0_EXECUTION_DECISION_001.md', max_download_bytes=2*1024**3,
      max_objects=96,max_nonmetadata_requests=1000,max_retries=3,concurrency=1,
      manual=dict(seconds=300,download_bytes=250*MIB,intensive_io_bytes=1024**3,bulk=True),
      zones=dict(RAW_IMMUTABLE='c0/quarantine/RAW_IMMUTABLE', SUBJECT_INDEX='c0/quarantine/SUBJECT_INDEX.parquet',
      CONFOUND_AUDIT='c0/quarantine/CONFOUND_AUDIT_C0.parquet',INTERPRETATION_LOCKBOX='c0/quarantine/INTERPRETATION_LOCKBOX'),
      lockbox='0700 directory; ingest process only; original catalogs 0400 after projections; same OS user is not a security boundary',
      logs='No blocked column names or values; unknown columns rejected by selector',
      network='Sequential; no automatic retries; every HTTP hop counted; persistent SQLite accounting; interrupted block reservations retained',
      gates='Addendum overrides original global policy; dependent work stops on failure; no automatic rescue')
    atomic_json(ROOT/'c0/provenance/C0_ACCESS_POLICY.yaml',policy)
    snap=dict(timestamp_utc=utc(),python=sys.version,platform=platform.platform(),
       hash_algorithm='SHA-256',http_client='urllib.request standard library',
       fits_library='NOT_INSTALLED',parquet_library='NOT_INSTALLED',
       dependencies={m: bool(importlib.util.find_spec(m)) for m in ['astropy','pyarrow','numpy']},
       disk_free_bytes=shutil.disk_usage(ROOT).free,
       git='Directory .git exists but is empty; not a functional repository. No repair authorized.',
       authority_checksums={p:sha(ROOT/p) for p in ['GALAXY_RESEARCH_SEED.md','CODEX_PHASE_C0_SPEC.md','C0_EXECUTION_DECISION_001.md','AGENTS.md']})
    atomic_json(ROOT/'c0/provenance/C0_ENVIRONMENT_SNAPSHOT.txt',snap)
    Budget(ROOT/'c0/provenance').db.close()


def export(b):
    events=b.events()
    fields=['source_id','provider','concept_doi','version_doi_or_record','url','final_url','retrieved_at_utc','http_status','etag','last_modified','declared_bytes','observed_bytes','provider_checksum_algorithm','provider_checksum','sha256','license','local_logical_path','access_result','notes','metadata','error_type','reason','method','range_start','range_end','resource_total_bytes','content_range','transfer_stage']
    with open(ROOT/'c0/provenance/C0_REMOTE_FILE_MANIFEST.csv','w') as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore'); writer.writeheader(); writer.writerows(events)
    register=[]
    for sid,name,url in SOURCES:
        es=[e for e in events if e['source_id']==sid]
        register.append(dict(source_id=sid,description=name,candidate_url=url,verification='PENDING_SEMANTIC_REVIEW',retrieval=es[-1] if es else None))
    atomic_json(ROOT/'c0/provenance/C0_SOURCE_REGISTER.yaml',dict(format='JSON is valid YAML 1.2',sources=register))
    summary=dict(timestamp_utc=utc(),charged_download_bytes=b.count('bytes'),all_http_requests=b.count('all_requests'),nonmetadata_requests=b.count('data_requests'),resources=len(events),verified_responses=sum(e['access_result']=='VERIFIED' for e in events),verified_ranges=sum(e['access_result']=='VERIFIED_RANGE' for e in events))
    atomic_json(ROOT/'c0/reports/C0_LIGHT_NETWORK_SUMMARY.json',summary)
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['preflight','sources','summary'])
    parser.add_argument('--dry-run',action='store_true')
    parser.add_argument('--source',choices=[s[0] for s in SOURCES],action='append')
    args=parser.parse_args()
    if args.dry_run:
        print(json.dumps(dict(stage=args.stage,sources=[s for s in SOURCES if not args.source or s[0] in args.source],max_per_response_bytes=8*MIB,concurrency=1),indent=2)); return 0
    if args.stage=='preflight': preflight(); print('C0.0 PREFLIGHT_OK'); return 0
    b=Budget(ROOT/'c0/provenance')
    if args.stage=='sources':
        for sid,name,url in SOURCES:
            if args.source and sid not in args.source: continue
            e=fetch(b,url,ROOT/'c0/provenance/raw_metadata'/f'{sid}.raw',sid)
            print(sid,e['access_result'],e.get('http_status'),e['observed_bytes'])
            export(b)
            if e.get('reason') in ['BYTE_LIMIT','INSUFFICIENT_RESERVED_BUDGET','DATA_REQUEST_LIMIT','RESOURCE_RETRIES_EXHAUSTED']:
                print('HARD_STOP'); return 2
    print(json.dumps(export(b))); return 0

if __name__=='__main__': sys.exit(main())
