"""Offline cached-support contrast. Completion is NOT a C0-C decision."""
import argparse
import contextlib
import fcntl
import hashlib
import io
import json
import math
from pathlib import Path
import sys
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from . import operator_support as op
from .core import Stop, atomic_json, utc
from .run import ROOT
from .ranges import RangeView

BASE=ROOT/'c0/reports/cached_support'
PROTOCOL='c0/reports/C0_CACHED_SUPPORT_PROTOCOL.md'

def overlay(image,available,crop,data,x,y):
    x0,y0,x1,y1=crop
    a,b=max(x,x0),min(x+data.shape[1],x1)
    c,d=max(y,y0),min(y+data.shape[0],y1)
    if a>=b or c>=d:return
    dst=image[c-y0:d-y0,a-x0:b-x0];known=available[c-y0:d-y0,a-x0:b-x0]
    src=data[c-y:d-y,a-x:b-x]
    if not np.array_equal(dst[known],src[known],equal_nan=True):raise Stop('NATIVE_TILE_OVERLAP_MISMATCH')
    dst[:]=src;known[:]=True

def decode_cached(prefix,tiles,res,g,analytic_g,native):
    h,desc,_=op.descriptor_table(prefix,res['total_bytes'])
    segments=[(e['range_start'],blob) for e,blob in zip(res['range_events'],(prefix,tiles))]
    for e,blob in zip(res['range_events'],(prefix,tiles)):
        if len(blob)!=e['range_end']-e['range_start']+1:raise Stop('RANGE_SIZE_MISMATCH')
    cached=[[a,a+len(b)-1] for a,b in segments]
    x0,y0,x1,y1=g['crop'];img=np.full((y1-y0,x1-x0),np.nan,np.float32);available=np.zeros(img.shape,bool)
    for data,x,y in native:overlay(img,available,g['crop'],data,x,y)
    tx,ty=int(h['ZTILE1']),int(h['ZTILE2']);ntx=math.ceil(h['ZNAXIS1']/tx)
    needed=set()
    for v in op.VARIANTS:
        for x,y,active in op.stencil(analytic_g if v=='analytic' else g,v):
            needed.update(map(int,np.unique(((y//ty)*ntx+x//tx)[active])))
    decoded=[]
    with fits.open(RangeView(res['total_bytes'],segments),memmap=False) as hdus:
        for tid in sorted(needed):
            if op.subtract(desc[tid],cached):continue
            x=(tid%ntx)*tx;y=(tid//ntx)*ty
            data=np.array(hdus[1].section[y:min(y+ty,h['ZNAXIS2']),x:min(x+tx,h['ZNAXIS1'])],copy=True)
            overlay(img,available,g['crop'],data,x,y);decoded.append(tid)
    return img,available,decoded

def evaluate(fn,g,img,available,variant):
    x,y,ix,iy,active=op.coordinates(g,variant);x0,y0,_,_=g['crop']
    known=active.copy()
    for xx,yy,_ in op.stencil(g,variant):known &= available[yy-y0,xx-x0]
    # Existing arithmetic, but suppress unknown stencils before evaluation.
    local=dict(g,emitted=g['emitted']&known)
    value,_,_=op.candidate_values(fn,local,img,dict(brick_x0=x0,brick_y0=y0),variant)
    return value,known|~active,active

def partitions(obs,mask,overlap,single=None):
    y,x=np.indices(obs.shape);edge=(x<3)|(y<3)|(x>=253)|(y>=253)
    out=dict(all=mask,edge3=mask&edge,interior=mask&~edge,overlap=mask&overlap,single_brick=mask&(~overlap if single is None else single))
    for a in range(2):
        for b in range(2):out[f'quadrant_{a}_{b}']=mask&(x//128==a)&(y//128==b)
    q=np.quantile(obs[mask],[0,.25,.5,.75,1]) if mask.any() else np.zeros(5)
    for k in range(4):out[f'intensity_q{k}']=mask&(obs>=q[k])&((obs<q[k+1]) if k<3 else obs<=q[k+1])
    return out,q.tolist()

def metrics(pred,obs,mask,overlap,intensity,single=None):
    excluded=int((mask&~np.isfinite(intensity)).sum())
    mask=mask&np.isfinite(intensity)
    groups,edges=partitions(intensity,mask,overlap,single);diff=pred.astype(float)-obs
    result={}
    for name,m in groups.items():
        r=op.stats(diff,m);den=float(np.sum(obs[m]**2));energy=float(np.sum(diff[m]**2))
        r.update(relative_l2=math.sqrt(energy/den) if den else None,squared_error=energy,observed_squared_norm=den)
        result[name]=r
    return dict(groups=result,intensity_edges=edges,intensity_nonfinite_exclusions=excluded)

def run_job(job,fn,budget,path_hashes,old):
    def raw(row):return budget.read(row['path'],json.loads(row['audit_json'])['sha256'])
    with fits.open(io.BytesIO(raw(job['normal'])),memmap=False) as f:
        target=f[0].header.copy();obs=f[0].data['grz'.index(job['band'])].astype(float)
    if obs.shape!=(256,256) or target.get('VERSION','').strip()!='DR5' or target.get('BANDS','').strip()!='grz':raise Stop('FROZEN_IMAGE_MISMATCH')
    values={v:[] for v in op.VARIANTS};known={v:[] for v in op.VARIANTS};active={v:[] for v in op.VARIANTS};sources=[]
    yy,xx=np.indices(obs.shape,dtype=float);world=WCS(target,naxis=2).all_pix2world(xx,yy,0)
    with fits.open(io.BytesIO(raw(job['sub'])),memmap=False) as sub:
        for p,res in zip(job['products'],job['resources']):
            prefix=budget.read(res['prefix_path'],res['prefix_sha256']);tiles=budget.read(res['tiles_path'],res['tiles_sha256'])
            with fits.open(RangeView(res['total_bytes'],[(0,prefix)]),memmap=False) as f:official=f[1].header.copy()
            g=op.geometry(target,official)
            # Preserve the analytical reference's WCS evaluation origin.
            ax,ay=WCS(sub[p['hdu']].header,naxis=2).all_world2pix(*world,0)
            ag=dict(g,direct=(ax+p['brick_x0']-g['crop'][0],ay+p['brick_y0']-g['crop'][1]))
            native=[]
            for c in res['comparisons']:
                data=budget.read(c['path'],path_hashes[c['path']])
                with fits.open(io.BytesIO(data),memmap=False) as f:native.append((np.array(f[c['hdu']].data,copy=True),c['x0'],c['y0']))
            img,available,tids=decode_cached(prefix,tiles,res,g,ag,native)
            sources.append(dict(url=res['url'],etag=res['etag'],crop=g['crop'],decoded_tiles=tids,available_native_pixels=int(available.sum())))
            for v in op.VARIANTS:
                val,k,a=evaluate(fn,ag if v=='analytic' else g,img,available,v)
                values[v].append(val);known[v].append(k);active[v].append(a)
    arrays=dict(observed=obs);predictions={};evaluated={};counts={};maskcounts={}
    for v in op.VARIANTS:
        pred,safe,n=op.accumulate(values[v],known[v],active[v],np.float64 if v in ('analytic','float_coords') else np.float32)
        act=np.any(active[v],axis=0);complete=safe&act
        ev=complete&(n>0)&np.isfinite(pred)&np.isfinite(obs)
        nonfinite=np.any([a&k&~np.isfinite(val) for a,k,val in zip(active[v],known[v],values[v])],axis=0)
        masks=dict(complete=complete,missing=act&~safe,outside=~act,evaluated=ev,excluded_rule=complete&~ev,nonfinite_contribution=nonfinite)
        for name,m in masks.items():arrays[f'{name}_{v}']=m
        arrays['prediction_'+v]=pred;arrays['residual_'+v]=pred.astype(float)-obs;arrays['finite_count_'+v]=n
        predictions[v]=pred;evaluated[v]=ev;counts[v]=n;maskcounts[v]={k:int(m.sum()) for k,m in masks.items()}
    expected=np.logical_and.reduce([op.unpacked(s['locally_supported_mask']) for s in old['support']])&np.logical_or.reduce([op.unpacked(s['active_mask']) for s in old['support']])
    if not np.array_equal(expected,arrays['complete_spline_lut']):raise Stop('SUPPORT_INVENTORY_MASK_MISMATCH')
    candidate_count=np.sum(active['spline_lut'],axis=0);overlap=candidate_count>1;single=candidate_count==1;common=np.logical_and.reduce(list(evaluated.values()))
    arrays.update(common=common,overlap=overlap,candidate_count=candidate_count)
    result={}
    for v in op.VARIANTS:
        result[v]={domain:{'observed_intensity':metrics(predictions[v],obs,m,overlap,obs,single),'reference_intensity':metrics(predictions[v],obs,m,overlap,predictions['analytic'],single)} for domain,m in [('individual',evaluated[v]),('common',common)]}
    return dict(rank=job['rank'],band=job['band'],metrics=result,masks=maskcounts,common_pixels=int(common.sum()),sources=sources,gate_c='PENDING'),arrays

def main():
    p=argparse.ArgumentParser(description=__doc__);choice=p.add_mutually_exclusive_group(required=True)
    for flag in ('dry-run','smoke','run'):choice.add_argument('--'+flag,action='store_true')
    p.add_argument('--max-read-mib',type=int,default=768);p.add_argument('--max-write-mib',type=int,default=256)
    args=p.parse_args()
    if not(1<=args.max_read_mib<=768 and 1<=args.max_write_mib<=256):p.error('Caps: read 1..768 MiB; write 1..256 MiB')
    sys.addaudithook(op.offline_guard);before=op.ledger_snapshot()
    if args.dry_run:
        print(json.dumps(dict(comparisons=36,network_requests=0,download_bytes=0,read_cap_mib=args.max_read_mib,write_cap_mib=args.max_write_mib,ram_estimate_mib=768,time_estimate_minutes='2–15',counters=before[0],gate_c='PENDING')));return 0
    budget=op.LocalIO(args.max_read_mib*1024**2,args.max_write_mib*1024**2)
    mode='smoke' if args.smoke else 'batch';folder=BASE/mode;stem=ROOT/f'c0/reports/C0_CACHED_SUPPORT_{mode.upper()}'
    log=ROOT/f'c0/logs/C0_CACHED_SUPPORT_{mode.upper()}.log';success='C0_CACHED_SUPPORT_SMOKE_OK' if args.smoke else 'C0_CACHED_SUPPORT_OK';code=0;reason=None;owned=False
    with (ROOT/'c0/provenance/manual_execution.lock').open('a') as lock,log.open('a') as stream:
        try:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);owned=True
            with contextlib.redirect_stdout(stream),contextlib.redirect_stderr(stream):
                print(utc(),'START',mode,flush=True)
                prov=op.provenance(budget)
                for path in (PROTOCOL,'c0_pipeline/cached_support.py','c0/reports/C0_OPERATOR_SUPPORT_BATCH_REVIEW.md','c0/reports/C0_OPERATOR_SUPPORT_BATCH_RESULTS.json','c0/reports/operator_support/batch/provenance.json'):
                    prov['files'][path]=hashlib.sha256(budget.read(ROOT/path)).hexdigest()
                fn,build=op.build_kernel();prov['kernel_build']=build
                if args.smoke:folder=folder/prov['files']['c0_pipeline/cached_support.py']
                oldprov=json.loads(budget.read(op.BASE/'batch/provenance.json'))
                jobs=op.fixed_jobs(budget);path_hashes={j['sub']['path']:json.loads(j['sub']['audit_json'])['sha256'] for j in jobs}
                if args.smoke:jobs=jobs[:1]
                rows=[]
                for job in jobs:
                    dest=folder/f'{job["rank"]:03d}_{job["band"]}'
                    old=op.load_checkpoint(op.BASE/'batch'/dest.name,oldprov,budget)
                    if old is None:raise Stop('PRIOR_CHECKPOINT_REQUIRED')
                    # Revalidate input payloads even on resume; never rerun a valid comparison.
                    for key in ('normal','sub'):budget.read(job[key]['path'],json.loads(job[key]['audit_json'])['sha256'])
                    for res in job['resources']:
                        for key in ('prefix','tiles'):budget.read(res[key+'_path'],res[key+'_sha256'])
                        for c in res['comparisons']:budget.read(c['path'],path_hashes[c['path']])
                    row=op.load_checkpoint(dest,prov,budget)
                    if row is None:
                        row,arrays=run_job(job,fn,budget,path_hashes,old);op.save_checkpoint(dest,prov,row,arrays,budget);action='COMMITTED'
                    else:action='REUSED'
                    rows.append(row);print(job['rank'],job['band'],action,flush=True)
                if op.ledger_snapshot()!=before:raise Stop('OFFLINE_LEDGER_CHANGED')
                budget.json(folder/'provenance.json',prov)
                budget.json(str(stem)+'_RESULTS.json',dict(status=success,timestamp_utc=utc(),rows=rows,provenance=prov,counters=before[0],network_requests=0,gate_c='PENDING'))
                print(utc(),success,flush=True)
        except (Exception,KeyboardInterrupt) as exc:
            code=2;reason=str(exc) if isinstance(exc,Stop) else type(exc).__name__;print(utc(),'FAILED',reason,file=stream,flush=True)
            import traceback;traceback.print_exc(file=stream)
    if owned:atomic_json(str(stem)+'_STATUS.json',dict(status=success if not code else 'C0_CACHED_SUPPORT_FAILED',reason=reason,exit_code=code,log=str(log),read_bytes=budget.read_bytes,write_bytes=budget.write_bytes,network_requests=0,gate_c='PENDING'))
    print(success if not code else 'C0_CACHED_SUPPORT_FAILED');return code

if __name__=='__main__':sys.exit(main())
