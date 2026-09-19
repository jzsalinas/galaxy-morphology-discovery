"""CDS identity-only reconciliation. No branch responses are parsed."""
import gzip
import math
from pathlib import Path
from .core import Stop, atomic_json, sha, utc
from .identity import normalize_name
from .run import ROOT


def parse_identity(line):
    # S3 ReadMe byte ranges: 1–19 IAUname, 21–42 RAdeg, 44–66 DEdeg.
    if len(line)<66:
        raise Stop('CDS_SHORT_IDENTITY_RECORD')
    try:
        name=normalize_name(line[0:19].decode('ascii'))
        ra=float(line[20:42]);dec=float(line[43:66])
    except (UnicodeError,ValueError):
        raise Stop('CDS_IDENTITY_PARSE_ERROR') from None
    if not name or not math.isfinite(ra) or not math.isfinite(dec) or not 0<=ra<360 or not -90<=dec<=90:
        raise Stop('CDS_INVALID_IDENTITY')
    return name,ra,dec


def reconcile(raw):
    import pyarrow as pa
    import pyarrow.parquet as pq
    subjects=ROOT/'c0/quarantine/SUBJECT_INDEX.parquet'
    s=pq.read_table(subjects,columns=['iauname','galaxy_id','ra_deg','dec_deg']).to_pylist()
    zen={}
    for r in s:
        zen.setdefault(normalize_name(r['iauname']),[]).append(r)
    rows=[];seen={};expanded=0
    with gzip.open(raw,'rb') as f:
        for i,line in enumerate(f):
            expanded+=len(line)
            if expanded>300*1024**2 or i>=300000:
                raise Stop('CDS_EXPANSION_LIMIT')
            name,ra,dec=parse_identity(line)
            seen[name]=seen.get(name,0)+1
            candidates=zen.get(name,[])
            status='MATCHED' if len(candidates)==1 else 'MISSING_ZENODO' if not candidates else 'AMBIGUOUS_ZENODO'
            row=dict(source_row=i,iauname=name,ra_deg=ra,dec_deg=dec,match_status=status,galaxy_id=None,delta_ra_deg=None,delta_dec_deg=None)
            if len(candidates)==1:
                z=candidates[0]
                row.update(galaxy_id=z['galaxy_id'],delta_ra_deg=((ra-z['ra_deg']+180)%360)-180,delta_dec_deg=dec-z['dec_deg'])
            rows.append(row)
    for row in rows:
        if seen[row['iauname']]>1:row['match_status']='AMBIGUOUS_CDS'
    dest=ROOT/'c0/quarantine/CDS_IDENTITY_RECONCILIATION.parquet'
    tmp=dest.with_suffix('.tmp')
    pq.write_table(pa.Table.from_pylist(rows),tmp,compression='zstd')
    tmp.replace(dest);dest.chmod(0o400)
    matched=[r for r in rows if r['match_status']=='MATCHED']
    differences=[r for r in matched if r['delta_ra_deg']!=0 or r['delta_dec_deg']!=0]
    summary=dict(timestamp_utc=utc(),status='CDS_RECONCILIATION_EXECUTED',
      cds_rows=len(rows),cds_unique_names=len(seen),zenodo_rows=len(s),zenodo_unique_names=len(zen),
      unique_matches=len(matched),cds_duplicate_rows=sum(v for v in seen.values() if v>1),
      cds_names_absent_zenodo=sum(k not in zen for k in seen),zenodo_names_absent_cds=sum(k not in seen for k in zen),
      coordinate_differences=len(differences),
      max_abs_ra_difference_deg=max((abs(r['delta_ra_deg']) for r in matched),default=None),
      max_abs_dec_difference_deg=max((abs(r['delta_dec_deg']) for r in matched),default=None),
      note='Differences reported without tolerance-based acceptance; no vote comparison; not a formal Gate decision.',
      expanded_bytes=expanded,raw_sha256=sha(raw),subject_index_sha256=sha(subjects),output_sha256=sha(dest))
    atomic_json(ROOT/'c0/reports/C0_CDS_RECONCILIATION_SUMMARY.json',summary)
    return summary
