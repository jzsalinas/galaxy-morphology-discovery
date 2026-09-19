"""Offline, fixed C0 normal-cutout characterization; never assigns a Gate.

Analytic Lanczos-3 reference, NOT an execution replica of the viewer.
No spline coordinate approximation or C lookup table is used.
"""
import argparse
import contextlib
import fcntl
import json
from pathlib import Path
import sys
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from .core import Stop, sha, utc, atomic_json
from .run import ROOT

OUT = ROOT/'c0/reports/normal_cutout'
PROTOCOL = ROOT/'c0/reports/C0_NORMAL_CUTOUT_PROTOCOL.md'


def kernel(x):
    x = np.asarray(x, dtype=np.float64)
    return np.where(np.abs(x) < 3., np.sinc(x)*np.sinc(x/3.), 0.)


def interpolate_interior(img, x, y):
    """Require all 7x7 samples, even zero-weight ones; never invent edges.

    Nonfinite inputs propagate, as in the candidate C implementation.
    Returns values, known-support mask; finite mask is a separate concept.
    """
    x, y = np.asarray(x), np.asarray(y)
    if x.shape != y.shape or img.ndim != 2:
        raise Stop('INVALID_REFERENCE_SHAPES')
    coord_ok = np.isfinite(x) & np.isfinite(y)
    ix = (np.where(coord_ok, x, -100.)+.5).astype(np.int64)
    iy = (np.where(coord_ok, y, -100.)+.5).astype(np.int64)
    known = coord_ok & (ix >= 3) & (iy >= 3) & (ix < img.shape[1]-3) & (iy < img.shape[0]-3)
    values = np.full(x.shape, np.nan, dtype=np.float64)
    xx, yy, cx, cy = x[known], y[known], ix[known], iy[known]
    acc = np.zeros(xx.shape); weight = np.zeros(xx.shape)
    for dy in range(-3,4):
        ky = kernel(yy-cy-dy)
        for dx in range(-3,4):
            w = ky*kernel(xx-cx-dx)
            acc += w * img[cy+dy,cx+dx]
            weight += w
    if np.any(np.abs(weight) < 1e-12):
        raise Stop('DEGENERATE_REFERENCE_KERNEL')
    values[known] = acc/weight
    return values, known


def combine(values, known):
    """Equal weights over finite contributions; unknown support stays unknown."""
    vs, ks = np.asarray(values), np.asarray(known)
    if vs.shape != ks.shape or not len(vs):
        raise Stop('INVALID_BRICK_CONTRIBUTIONS')
    safe = np.all(ks, axis=0)
    finite = np.isfinite(vs)
    count = finite.sum(axis=0)
    result = np.where(finite,vs,0.).sum(axis=0)/np.maximum(count,1)
    # Viewer candidate emits zero with no finite contributions. This is NOT coverage.
    result[~safe] = np.nan
    return result,safe,count


def inputs():
    import pyarrow.parquet as pq
    rr = ROOT/'c0/reports/C0_RANGE_SUBSET_RESULTS.json'
    ranged = json.loads(rr.read_text())
    if ranged['status'] != 'C0_RANGE_SUBSET_OK' or ranged['objects'] != 12:
        raise Stop('RANGE_CHECKPOINT_REQUIRED')
    sub = pq.read_table(ROOT/'c0/probe/C0_SUBIMAGE_REPORT.parquet',filters=[('probe_rank','<=',12)]).to_pylist()
    normal = pq.read_table(ROOT/'c0/probe/C0_PROBE_FITS_REPORT.parquet',filters=[('probe_rank','<=',12)]).to_pylist()
    if any({r['probe_rank'] for r in rows} != set(range(1,13)) or len(rows)!=12 for rows in (sub,normal)):
        raise Stop('FROZEN_SUBSET_MISMATCH')
    unique={Path(r['path']) for r in sub+normal}
    if sum(p.stat().st_size for p in unique)>128*1024**2:raise Stop('LOCAL_INPUT_CAP')
    ns = {r['probe_rank']:r for r in normal}
    jobs=[]
    for s in sorted(sub,key=lambda r:r['probe_rank']):
        n=ns[s['probe_rank']]
        if s['galaxy_id'] != n['galaxy_id']:raise Stop('IDENTITY_MISMATCH')
        for r in (s,n):
            a=json.loads(r['audit_json'])
            if sha(r['path']) != a['sha256']:raise Stop('INPUT_HASH_MISMATCH')
        a=json.loads(s['audit_json'])
        for band in 'grz':
            products=[p for p in a['products'] if p['kind']=='image' and p['band']==band]
            if not products:raise Stop('BAND_MISSING')
            for p in products:
                matches=[(res,c) for res in ranged['resources'] for c in res['comparisons'] if c['probe_rank']==s['probe_rank'] and c['hdu']==p['hdu'] and c['path']==s['path']]
                if len(matches)!=1 or not matches[0][1]['equal']:raise Stop('NATIVE_EQUIVALENCE_MISSING')
            jobs.append(dict(rank=s['probe_rank'],band=band,normal=n,subimage=s,products=products))
    return jobs


def contrast(job):
    with fits.open(job['normal']['path'],memmap=False) as normal, fits.open(job['subimage']['path'],memmap=False) as sub:
        h=normal[0].header
        if h.get('VERSION','').strip()!='DR5' or h.get('BANDS','').strip()!='grz':raise Stop('RELEASE_OR_BANDS_MISMATCH')
        observed=normal[0].data['grz'.index(job['band'])].astype(np.float64)
        if observed.shape!=(256,256):raise Stop('FROZEN_DIMENSIONS_MISMATCH')
        yy,xx=np.indices(observed.shape,dtype=float)
        world=WCS(h,naxis=2).all_pix2world(xx,yy,0)
        values=[];known=[];bricks=[]
        for p in job['products']:
            hd=sub[p['hdu']]
            x,y=WCS(hd.header,naxis=2).all_world2pix(*world,0)
            v,k=interpolate_interior(hd.data,x,y)
            values.append(v);known.append(k)
            bricks.append(dict(brick=p['brick'],known_support_pixels=int(k.sum()),native_nonfinite_pixels=int((~np.isfinite(hd.data)).sum())))
        predicted,safe,ncontrib=combine(values,known)
        use=safe & np.isfinite(observed) & np.isfinite(predicted)
        diff=predicted[use]-observed[use]
        if not len(diff):raise Stop('NO_COMPARABLE_PIXELS')
        rms=float(np.sqrt(np.mean(diff**2)))
        denom=float(np.sqrt(np.mean(observed[use]**2)))
        return dict(timestamp_utc=utc(),probe_rank=job['rank'],band=job['band'],bricks=bricks,
            reference='analytic_lanczos3_exact_astropy_wcs_equal_finite_brick_weights',
            normal_bunit=h.get('BUNIT'),total_pixels=int(observed.size),known_support_pixels=int(safe.sum()),
            compared_pixels=int(use.sum()),excluded_unknown_support=int((~safe).sum()),
            observed_nonfinite=int((~np.isfinite(observed)).sum()),zero_finite_contributors_known=int((safe & (ncontrib==0)).sum()),
            exact_equal_pixels=int(np.count_nonzero(diff==0)),max_abs_residual=float(np.max(np.abs(diff))),
            rms_residual=rms,relative_l2_residual=rms/denom if denom else None,
            mean_signed_residual=float(np.mean(diff)),abs_residual_quantiles=dict(zip(['p50','p95','p99'],map(float,np.quantile(np.abs(diff),[.5,.95,.99])))),
            gate_assessment='NOT_ASSIGNED',equivalence_demonstrated=False,
            limits=['Analytic kernel instead of C LUT; float64 instead of viewer float32 accumulators',
                    'Exact Astropy WCS instead of deployed astrometry spline; deployment version unverified',
                    'Available subimage brick set; deployed brick availability/order not certified',
                    'Only common fully available 7x7 support; no extrapolation to excluded edges',
                    'No flux conservation, unit transfer or noise/coverage inference'])


def fingerprint():
    lock=json.loads((ROOT/'c0/provenance/C0_NORMAL_CODE_SOURCES.json').read_text())
    for source in lock['sources']:
        if sha(source['local_logical_path'])!=source['sha256']:raise Stop('CODE_SOURCE_HASH_MISMATCH')
    paths=[PROTOCOL,Path(__file__),ROOT/'c0/reports/C0_RANGE_SUBSET_RESULTS.json',
        ROOT/'c0/probe/C0_SUBIMAGE_REPORT.parquet',ROOT/'c0/probe/C0_PROBE_FITS_REPORT.parquet',
        ROOT/'c0/provenance/C0_NORMAL_CODE_SOURCES.json']
    return {str(p.relative_to(ROOT)):sha(p) for p in paths}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--dry-run',action='store_true')
    group.add_argument('--smoke',action='store_true',help='Rank 1, g only, offline')
    group.add_argument('--run',action='store_true',help='Human execution: all fixed 12 objects, grz, offline')
    args=parser.parse_args()
    mode='SMOKE' if args.smoke else 'BATCH'
    log=ROOT/f'c0/logs/C0_NORMAL_{mode}.log'
    if args.dry_run:
        print(json.dumps(dict(objects=12,comparisons=36,network_requests=0,additional_download_bytes=0,
           max_input_bytes=128*1024**2,estimated_seconds=120,max_output_bytes=2*1024**2,
           inputs=['C0_PROBE_FITS_REPORT.parquet','C0_SUBIMAGE_REPORT.parquet','C0_RANGE_SUBSET_RESULTS.json','existing normal and subimage FITS'],
           no_gate_decision=True),indent=2));return 0
    log.parent.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    status=ROOT/f'c0/reports/C0_NORMAL_{mode}_STATUS.json'
    code=0;sentinel=f'C0_NORMAL_{mode}_OK'
    reason=None
    with (ROOT/'c0/provenance/manual_execution.lock').open('a') as lock,log.open('a') as stream:
        try:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with contextlib.redirect_stdout(stream),contextlib.redirect_stderr(stream):
                jobs=inputs();fp=fingerprint()
                unique={Path(j[k]['path']) for j in jobs for k in ['normal','subimage']}
                if sum(p.stat().st_size for p in unique)>128*1024**2:raise Stop('LOCAL_INPUT_CAP')
                if args.smoke:jobs=jobs[:1]
                rows=[]
                for j in jobs:
                    dest=OUT/f'{mode.lower()}_{j["rank"]:03d}_{j["band"]}.json'
                    if dest.exists():
                        row=json.loads(dest.read_text())
                        if row.get('provenance')!=fp:raise Stop('EXISTING_RESULT_PROVENANCE_CHANGED')
                    else:
                        row=contrast(j);row['provenance']=fp;atomic_json(dest,row)
                    rows.append(row)
                    print(j['rank'],j['band'],'CHARACTERIZED',flush=True)
                atomic_json(ROOT/f'c0/reports/C0_NORMAL_{mode}_RESULTS.json',dict(status=sentinel,
                    timestamp_utc=utc(),rows=rows,network_requests=0,gate_assessment='NOT_ASSIGNED',
                    input_bytes=sum(p.stat().st_size for p in unique)))
        except Exception as exc:
            code=2;sentinel='C0_NORMAL_CHARACTERIZATION_FAILED'
            reason=str(exc) if isinstance(exc,Stop) else type(exc).__name__
            print(utc(),reason,file=stream)
    atomic_json(status,dict(timestamp_utc=utc(),status=sentinel,exit_code=code,reason=reason,log=str(log)))
    print(sentinel);return code

if __name__=='__main__':sys.exit(main())
