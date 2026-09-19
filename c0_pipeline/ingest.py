"""Manual C0.2 first step: verified Zenodo file to quarantined projections.

No morphology is displayed. Unrecognized columns default to lockbox. CDS
reconciliation and probe selection remain blocked pending this step's review.
"""
import hashlib
import json
import math
import os
from pathlib import Path
from .core import Stop, atomic_json, sha, utc
from .identity import identities
from .run import ROOT

IDENTITY=('iauname','ra','dec')
# Explicitly documented NSA fields; no vote counts used for selection.
CONFOUND=('petro_theta','petro_th50','petro_th90','elpetro_absmag_r','redshift','mag_r',
          'active_learning_on','upload_group')

def ingest(path, version, expected_md5):
    import pyarrow as pa
    import pyarrow.parquet as pq
    path=Path(path)
    if hashlib.md5(path.read_bytes()).hexdigest()!=expected_md5:
        raise Stop('PROVIDER_CHECKSUM_MISMATCH')
    digest=sha(path)
    # Reading the complete catalog is allowed only in this ingest function.
    table=pq.read_table(path)
    if not set(IDENTITY)<=set(table.column_names):
        raise Stop('IDENTITY_SCHEMA_UNRESOLVED')
    identity=table.select(IDENTITY).to_pydict()
    rows=[dict(iauname=identity['iauname'][i],ra_deg=identity['ra'][i],dec_deg=identity['dec'][i],source_row=i) for i in range(table.num_rows)]
    rows=identities(rows,version,digest)
    for r in rows:
        r.update(gzd_campaign='GZD-5',source_record_version=version,source_sha256=digest,
                 png_path=None, campaign_evidence='S2_schema.raw: volunteers_5 respective campaign')
    subject=pa.Table.from_pylist(sorted(rows,key=lambda r:r['galaxy_id']))
    gids=pa.array([r['galaxy_id'] for r in rows])
    confound_cols=[c for c in CONFOUND if c in table.column_names]
    confound=table.select(confound_cols).append_column('galaxy_id',gids).append_column('source_row',pa.array(range(table.num_rows)))
    blocked=[c for c in table.column_names if c not in IDENTITY and c not in CONFOUND]
    locked=table.select(blocked).append_column('galaxy_id',gids).append_column('source_row',pa.array(range(table.num_rows)))
    quarantine=ROOT/'c0/quarantine'
    outputs={}
    for name,t in [('SUBJECT_INDEX.parquet',subject),('CONFOUND_AUDIT_C0.parquet',confound),('INTERPRETATION_LOCKBOX/interpretation.parquet',locked)]:
        dest=quarantine/name;tmp=dest.with_suffix('.parquet.tmp')
        pq.write_table(t,tmp,compression='zstd',version='2.6')
        check=pq.read_table(tmp)
        if not check.equals(t): raise Stop('PROJECTION_ROUNDTRIP_FAILED')
        os.replace(tmp,dest);dest.chmod(0o400)
        outputs[name]=dict(sha256=sha(dest),bytes=dest.stat().st_size)
    # Names/types of blocked fields never appear outside this protected directory.
    atomic_json(quarantine/'INTERPRETATION_LOCKBOX/column_mapping.json',dict(schema_version=1,blocked_columns=blocked,source_sha256=digest))
    (quarantine/'INTERPRETATION_LOCKBOX/column_mapping.json').chmod(0o400)
    path.chmod(0o400)
    valid=0
    for r in rows:
        try: valid+=int(math.isfinite(float(r['ra_deg'])) and 0<=float(r['ra_deg'])<360 and math.isfinite(float(r['dec_deg'])) and -90<=float(r['dec_deg'])<=90)
        except (ValueError,TypeError): pass
    summary=dict(timestamp_utc=utc(),status='ZENODO_INGEST_OK_CDS_PENDING',rows=len(rows),
      unique_galaxy_ids=len({r['galaxy_id'] for r in rows}),valid_coordinates=valid,
      fallback_rows=sum(r['identity_method']=='fallback_uuid5' for r in rows),
      blocked_column_count=len(blocked),source_sha256=digest,outputs=outputs,
      limitations=['No CDS reconciliation yet','Missing or unknown confounds remain unavailable; not inferred',
                    'PNG path not reconstructed','No probe selected; no images downloaded',
                    'Raw and lockbox permissions protect routine access, not against the owning OS user'])
    atomic_json(ROOT/'c0/reports/C0_ZENODO_INGEST_SUMMARY.json',summary)
    atomic_json(ROOT/'c0/schemas/C0_SCHEMA_SNAPSHOT/zenodo_safe_schema.json',dict(identity_fields=IDENTITY,confound_fields=confound_cols,blocked_column_count=len(blocked),source_sha256=digest))
    return summary
