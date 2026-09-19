"""Regenerate source inventory from preserved metadata, without network."""
import hashlib
import json
import csv
from pathlib import Path
from .run import ROOT, export
from .core import Budget, atomic_json

def build():
 b=Budget(ROOT/'c0/provenance'); export(b)
 path=ROOT/'c0/provenance/raw_metadata/S2_version.raw'
 record=json.loads(path.read_text())
 reg_path=ROOT/'c0/provenance/C0_SOURCE_REGISTER.yaml'
 reg=json.loads(reg_path.read_text())
 s=next(s for s in reg['sources'] if s['source_id']=='S2')
 s.update(record_id=record['id'],concept_doi=record['conceptdoi'],version_doi=record['doi'],
          version=record['metadata'].get('version'),license=record['metadata'].get('license'),
          publication_date=record['metadata'].get('publication_date'),verification='VERSION_RESOLVED; FILE_HASH_VERIFICATION_PENDING')
 schema=ROOT/'c0/provenance/raw_metadata/S2_schema.raw'
 md5=hashlib.md5(schema.read_bytes()).hexdigest()
 declared=next(f for f in record['files'] if f['key']=='schema.md')['checksum']
 s['schema_provider_checksum_verified']=('md5:'+md5==declared)
 reg['citation_requirements']='Zenodo CC-BY-4.0: attribution and changes; cite Walmsley et al. 2022. Other providers: terms still under review; no global license approval.'
 reg['sources'].append(dict(source_id='S6-DATALAB',description='Public NOIRLab TAP metadata investigation, suggested by DR5 documentation',candidate_url='https://datalab.noirlab.edu/tap/sync',verification='NO_DECALS_DR5_TABLE_FOUND_IN_QUERIED_SCHEMA',notes='No astronomical rows retrieved. VHS DR5 is unrelated and was not substituted.'))
 # Preserve the optional, versioned normal-cutout code-source investigation.
 code_lock=ROOT/'c0/provenance/C0_NORMAL_CODE_SOURCES.json'
 if code_lock.exists():
  code_sources=json.loads(code_lock.read_text())
  for sid in sorted({e['source_id'] for e in code_sources['sources']}):
   reg['sources'].append(dict(source_id=sid,description='Normal-cutout implementation provenance investigation',
       verification='PUBLIC_SOURCE_SNAPSHOT_NOT_DEPLOYMENT_ATTESTATION',
       retrievals=[e for e in code_sources['sources'] if e['source_id']==sid],
       provenance_lock=str(code_lock.relative_to(ROOT))))
 atomic_json(reg_path,reg)
 m=ROOT/'c0/provenance/C0_REMOTE_FILE_MANIFEST.csv'
 with m.open() as f: reader=csv.DictReader(f); fields=reader.fieldnames; rows=list(reader)
 for entry in record['files']:
  algo,digest=entry['checksum'].split(':',1)
  rows.append(dict(source_id='S2',provider='Zenodo',concept_doi=record['conceptdoi'],version_doi_or_record=record['doi'],url=entry['links']['self'],declared_bytes=entry['size'],provider_checksum_algorithm=algo,provider_checksum=digest,license=record['metadata']['license']['id'],access_result='METADATA_ONLY_NOT_DOWNLOADED',notes=entry['key']))
 with m.open('w') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 print('INVENTORY_OK; schema_provider_checksum_verified='+str(s['schema_provider_checksum_verified']))
if __name__=='__main__':build()
