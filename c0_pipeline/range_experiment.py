"""C0 Range feasibility: offline recovery or explicit human-run fixed subset.

No ordinary resampled-cutout equivalence claim, no final Gate decision.
"""
import argparse
import contextlib
import fcntl
import json
import sqlite3
import sys
from pathlib import Path
import numpy as np
from astropy.io import fits
from .core import Budget,Stop,atomic_json,sha,utc,MIB,LIMIT_BYTES
from .ranges import fetch_range
from .range_plan import plan_section,read_section
from .run import ROOT


def grid_error_pixels(official_header,subimage_header,roi):
    from astropy.wcs import WCS
    corners=np.array([[0.,0.],[roi['width']-1.,0.],[0.,roi['height']-1.],[roi['width']-1.,roi['height']-1.]])
    world=WCS(official_header,naxis=2).all_pix2world(corners+[roi['x0'],roi['y0']],0)
    recovered=WCS(subimage_header,naxis=2).all_world2pix(world,0)
    error=float(np.max(np.linalg.norm(recovered-corners,axis=1)))
    if not np.isfinite(error) or error>1e-5:raise Stop('OFFICIAL_SUBIMAGE_WCS_MISMATCH')
    return error


def offline_smoke():
    root=ROOT/'c0/probe/range_smoke'
    prefix=root/'prefix.bin';tiles=root/'tiles.bin'
    old=json.loads((root/'plan.json').read_text())
    db=sqlite3.connect(f'file:{ROOT}/c0/provenance/resource_ledger.sqlite?mode=ro',uri=True)
    events=[json.loads(r[0]) for r in db.execute('SELECT payload FROM events ORDER BY id')];db.close()
    selected=[]
    for path,start,end in [(prefix,0,262143),(tiles,old['start'],old['end'])]:
        e=next((e for e in reversed(events) if e.get('access_result')=='VERIFIED_RANGE' and e.get('range_start')==start and e.get('range_end')==end and e.get('sha256')==sha(path)),None)
        if not e or e['observed_bytes']!=path.stat().st_size:raise Stop('RECOVERED_RANGE_PROVENANCE_MISMATCH')
        selected.append(e)
    if selected[0]['url']!=selected[1]['url'] or selected[0]['etag']!=selected[1]['etag']:raise Stop('MIXED_RESOURCE_VERSIONS')
    if any(e['resource_total_bytes']!=old['total'] for e in selected):raise Stop('RESOURCE_SIZE_MISMATCH')
    p=plan_section(prefix.read_bytes(),old['total'],old['x0'],old['y0'],old['width'],old['height'])
    if p!=old:raise Stop('RECOVERED_PLAN_CHANGED')
    region,h=read_section(p['total'],[(0,prefix.read_bytes()),(p['start'],tiles.read_bytes())],p)
    with fits.open(ROOT/'c0/probe/dr5_subimage_smoke.fits',memmap=False) as hdus:
        observed=hdus[1].data
        wcs_error=grid_error_pixels(h,hdus[1].header,p)
        equal=np.array_equal(region,observed,equal_nan=True)
        if not equal:raise Stop('RECOVERED_COMPARISON_FAILED')
    result=dict(timestamp_utc=utc(),status='C0_RANGE_OFFLINE_OK',equal=True,max_abs_diff=0.0,
        official_bunit=h.get('BUNIT'),max_grid_error_pixels=wcs_error,shape=list(region.shape),range_bytes=prefix.stat().st_size+tiles.stat().st_size,
        whole_file_bytes=p['total'],url=selected[0]['url'],etag=selected[0]['etag'],events=selected,
        network_requests=0,limits=['One object, one band, one official compressed file',
        'Whole official-file checksum not verified; file was never fully acquired',
        'Whole-file equivalence tested on synthetic compressed files, not a downloaded full official coadd',
        'Ordinary resampled cutout comparison and C0-C assessment remain pending'])
    atomic_json(ROOT/'c0/reports/C0_RANGE_OFFLINE_VERIFICATION.json',result)
    return result


def jobs():
    import pyarrow.parquet as pq
    inventory=json.loads((ROOT/'c0/provenance/C0_DR5_RESOURCE_INVENTORY.json').read_text())
    resources={(r['brickname'],r['band']):r for r in inventory if r['product']=='comparison_image'}
    groups={}
    rows=pq.read_table(ROOT/'c0/probe/C0_SUBIMAGE_REPORT.parquet',filters=[('probe_rank','<=',12)]).to_pylist()
    if {r['probe_rank'] for r in rows}!=set(range(1,13)):raise Stop('FROZEN_COMPARISON_SUBSET_MISSING')
    for row in rows:
        a=json.loads(row['audit_json']);path=Path(row['path'])
        if sha(path)!=a['sha256']:raise Stop('SUBIMAGE_CHECKSUM_MISMATCH')
        for product in a['products']:
            if product['kind']!='image':continue
            r=resources[(product['brick'],product['band'])]
            if r['http_status']!=200 or not r['etag'] or r['etag'].startswith('W/'):raise Stop('OFFICIAL_RESOURCE_NOT_PINNED')
            group=groups.setdefault(r['url'],dict(resource=r,regions=[]))
            group['regions'].append(dict(galaxy_id=row['galaxy_id'],probe_rank=row['probe_rank'],path=str(path),hdu=product['hdu'],x0=product['brick_x0'],y0=product['brick_y0'],height=product['shape'][0],width=product['shape'][1]))
    return [groups[u] for u in sorted(groups)]


def run(args):
    groups=jobs();budget=Budget(ROOT/'c0/provenance');initial_bytes=budget.count('bytes');initial_requests=budget.count('data_requests')
    results=[]
    def acquire(resource,start,end,label):
        url=resource['url'];total=int(resource['declared_bytes']);etag=resource['etag']
        dest=ROOT/'c0/probe/range_c0'/resource['brickname']/resource['band']/f'{label}-{start}-{end}.bin'
        cached=False
        for e in reversed(budget.events()):
            if e.get('url')==url and e.get('range_start')==start and e.get('range_end')==end and e.get('resource_total_bytes')==total and e.get('etag')==etag and e.get('access_result')=='VERIFIED_RANGE':
                p=Path(e['local_logical_path']);p=p if p.is_absolute() else ROOT/p
                if p.exists() and p.stat().st_size==end-start+1 and sha(p)==e['sha256']:
                    dest=p;cached=True;break
        if not cached:
            if budget.count('bytes')-initial_bytes+(end-start+1)>args.max_additional_mib*MIB:raise Stop('RANGE_BATCH_BYTE_LIMIT')
            if budget.count('data_requests')-initial_requests>=args.max_data_requests:raise Stop('RANGE_BATCH_REQUEST_LIMIT')
        event=fetch_range(budget,url,start,end,total,dest,etag)
        if event['access_result']!='VERIFIED_RANGE':raise Stop('RANGE_FEASIBILITY_ACCESS_INCONCLUSIVE')
        return dest,event
    for group in groups:
        r=group['resource'];total=int(r['declared_bytes'])
        prefix,pe=acquire(r,0,min(262144,total)-1,'prefix')
        data=prefix.read_bytes()
        plans=[plan_section(data,total,x['x0'],x['y0'],x['width'],x['height']) for x in group['regions']]
        start=min(p['start'] for p in plans);end=max(p['end'] for p in plans)
        if end-start+1>8*MIB:raise Stop('UNION_RANGE_EXCEEDS_CAP')
        tiles,te=acquire(r,start,end,'tiles')
        comparisons=[]
        for roi,p in zip(group['regions'],plans):
            array,header=read_section(total,[(0,data),(start,tiles.read_bytes())],p)
            with fits.open(roi['path'],memmap=False) as service:
                hdu=service[roi['hdu']]
                if hdu.header.get('VERSION')!='DR5' or hdu.header.get('BRICK')!=r['brickname'] or hdu.header.get('BAND')!=r['band']:raise Stop('SUBIMAGE_IDENTITY_MISMATCH')
                grid_error=grid_error_pixels(header,hdu.header,p)
                if not np.array_equal(array,hdu.data,equal_nan=True):raise Stop('OFFICIAL_SECTION_DIFFERS_FROM_SUBIMAGE')
            comparisons.append(dict(**roi,equal=True,max_grid_error_pixels=grid_error,official_bunit=header.get('BUNIT'),section_plan=p))
        results.append(dict(url=r['url'],etag=r['etag'],total_bytes=total,prefix_sha256=sha(prefix),tiles_sha256=sha(tiles),prefix_path=str(prefix),tiles_path=str(tiles),range_events=[pe,te],comparisons=comparisons))
        atomic_json(ROOT/'c0/reports/C0_RANGE_SUBSET_RESULTS.json',dict(timestamp_utc=utc(),status='PARTIAL_PENDING_COMPLETION',resources=results))
    report=dict(timestamp_utc=utc(),provenance={p:sha(ROOT/p) for p in ['c0_pipeline/ranges.py','c0_pipeline/range_plan.py','c0_pipeline/range_experiment.py','c0/provenance/ASTROPY_DEPENDENCY_LOCK.json','c0/provenance/C0_DR5_RESOURCE_INVENTORY.json','c0/probe/C0_SUBIMAGE_REPORT.parquet']},status='C0_RANGE_SUBSET_OK',resource_count=len(results),objects=12,additional_bytes=budget.count('bytes')-initial_bytes,additional_data_requests=budget.count('data_requests')-initial_requests,resources=results,
       limitations=['Only supported RICE compressed layouts','No checksum of complete official coadd; fragment checksums and HTTP representation pinned',
       'No ordinary resampled-cutout comparison; no Gate C0-C or C0-D approval','No Tractor, nexp or SDSS acquisition'])
    atomic_json(ROOT/'c0/reports/C0_RANGE_SUBSET_RESULTS.json',report)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    modes=p.add_mutually_exclusive_group(required=True)
    modes.add_argument('--offline-smoke',action='store_true');modes.add_argument('--dry-run',action='store_true');modes.add_argument('--run',action='store_true')
    p.add_argument('--max-additional-mib',type=int,default=128);p.add_argument('--max-data-requests',type=int,default=84)
    args=p.parse_args()
    if args.dry_run:
        groups=jobs()
        print(json.dumps(dict(resources=len(groups),objects=12,whole_file_bytes=sum(int(x['resource']['declared_bytes']) for x in groups),maximum_requests_without_cache=2*len(groups),batch_byte_cap=args.max_additional_mib*MIB,expected='About 55 MiB extrapolated from one file; not a measured total',network=False),indent=2));return 0
    if args.max_additional_mib<=0 or args.max_data_requests<=0:raise SystemExit('INVALID_LIMITS')
    log=ROOT/'c0/logs'/('C0_RANGE_OFFLINE.log' if args.offline_smoke else 'C0_RANGE_SUBSET.log')
    rc=2;status='C0_RANGE_EXPERIMENT_FAILED';reason=None
    with open(ROOT/'c0/provenance/manual_execution.lock','w') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:print('C0_MANUAL_BUSY');return 2
        with open(log,'a',buffering=1) as output,contextlib.redirect_stdout(output),contextlib.redirect_stderr(output):
            print('START',utc())
            try:
                result=offline_smoke() if args.offline_smoke else run(args)
                status=result['status'];rc=0
            except Exception as exc:
                reason=str(exc) if isinstance(exc,Stop) else type(exc).__name__;print('FAILURE',reason)
            print('END',utc(),status)
    if args.run:
        from .inventory import build
        build()
    status_path=ROOT/'c0/reports'/('C0_RANGE_OFFLINE_STATUS.json' if args.offline_smoke else 'C0_RANGE_SUBSET_STATUS.json')
    atomic_json(status_path,dict(timestamp_utc=utc(),status=status,exit_code=rc,reason=reason,log=str(log)))
    print(status);return rc
if __name__=='__main__':sys.exit(main())
