"""Offline C0 operator attribution and exact compressed-tile support inventory.

No networking. All output is diagnostic, not a Gate decision.
"""
import argparse
import io
import os
import base64
import platform
import contextlib
import ctypes
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import fcntl
import numpy as np
import astropy
from astropy.io import fits
from astropy.wcs import WCS
from .core import Stop,sha,atomic_json,utc
from .run import ROOT
from .ranges import RangeView
from .normal_cutout import inputs,fingerprint,interpolate_interior,kernel

BASE=ROOT/'c0/reports/operator_support'
SOURCE=ROOT/'c0/provenance/raw_metadata/ASTROMETRY_lanczos.i'


def union(intervals):
    out=[]
    for a,b in sorted(intervals):
        if b<a:raise Stop('BAD_INTERVAL')
        if out and a<=out[-1][1]+1:out[-1][1]=max(out[-1][1],b)
        else:out.append([int(a),int(b)])
    return out


def subtract(intervals,cached):
    out=[]
    for a,b in union(intervals):
        pos=a
        for c,d in union(cached):
            if d<pos:continue
            if c>b:break
            if c>pos:out.append([pos,min(b,c-1)])
            pos=max(pos,d+1)
        if pos<=b:out.append([pos,b])
    return out


def spline_axis(nodes,values,targets):
    """Independent not-a-knot cubic interpolant, first axis; not FITPACK."""
    nodes=np.asarray(nodes);values=np.asarray(values);targets=np.asarray(targets)
    n=len(nodes);h=np.diff(nodes)
    if n<4 or np.any(h<=0):raise Stop('INVALID_SPLINE_GRID')
    a=np.zeros((n,n));rhs=np.zeros_like(values,dtype=float)
    a[0,:3]=[-h[1],h[0]+h[1],-h[0]]
    a[-1,-3:]=[-h[-1],h[-2]+h[-1],-h[-2]]
    delta=np.diff(values,axis=0)/h.reshape((-1,)+(1,)*(values.ndim-1))
    for i in range(1,n-1):
        a[i,i-1:i+2]=[h[i-1],2*(h[i-1]+h[i]),h[i]]
        rhs[i]=6*(delta[i]-delta[i-1])
    m=np.linalg.solve(a,rhs.reshape(n,-1)).reshape(values.shape)
    j=np.clip(np.searchsorted(nodes,targets)-1,0,n-2)
    shape=(-1,)+(1,)*(values.ndim-1)
    hh=h[j].reshape(shape);u=((nodes[j+1]-targets)/h[j]).reshape(shape);v=1-u
    return u*values[j]+v*values[j+1]+((u**3-u)*m[j]+(v**3-v)*m[j+1])*hh**2/6


def build_kernel():
    fingerprint() # verify source lock before compiling any preserved code
    source=SOURCE.read_text().split('static PyObject*',1)[0]
    if source.count('lanczos_resample_one_, L)')!=2:raise Stop('UNEXPECTED_AUDITED_C_BOUNDARY')
    wrapper='''
void evaluate(int n,const int *ix,const int *iy,const float *dx,const float *dy,
              const float *img,int w,int h,float *out) {
 lut_init_3();
 for(int k=0;k<n;k++)out[k]=lanczos_resample_one_3(ix[k],dx[k],iy[k],dy[k],img,w,h);
}
'''
    text='#include <math.h>\n#include <stddef.h>\n#define L 3\n#define MAX(a,b) ((a)>(b)?(a):(b))\n#define MIN(a,b) ((a)<(b)?(a):(b))\ntypedef ptrdiff_t npy_intp;\n'+source+wrapper
    key=hashlib.sha256(text.encode()).hexdigest();folder=ROOT/'c0/provenance/operator_build'/key
    folder.mkdir(parents=True,exist_ok=True);c=folder/'kernel.c';so=folder/'kernel.so';lock=folder/'build.json'
    if not so.exists():
        c.write_text(text)
        cmd=['cc','-O2','-fPIC','-shared','-ffp-contract=off',str(c),'-lm','-o',str(so)]
        subprocess.run(cmd,check=True,capture_output=True,timeout=30)
        atomic_json(lock,dict(command=cmd,compiler=subprocess.check_output(['cc','--version'],text=True).splitlines()[0],source_sha256=sha(c),binary_sha256=sha(so),original_sha256=sha(SOURCE),environment=dict(platform=platform.platform(),python=sys.version,numpy=np.__version__,astropy=astropy.__version__),compiler_path=__import__('shutil').which('cc')))
    meta=json.loads(lock.read_text())
    if sha(c)!=key or sha(so)!=meta['binary_sha256'] or meta['original_sha256']!=sha(SOURCE):raise Stop('BUILD_HASH_MISMATCH')
    lib=ctypes.CDLL(str(so));fn=lib.evaluate
    arr=np.ctypeslib.ndpointer
    fn.argtypes=[ctypes.c_int,arr(np.int32,flags='C_CONTIGUOUS'),arr(np.int32,flags='C_CONTIGUOUS'),arr(np.float32,flags='C_CONTIGUOUS'),arr(np.float32,flags='C_CONTIGUOUS'),arr(np.float32,flags='C_CONTIGUOUS'),ctypes.c_int,ctypes.c_int,arr(np.float32,flags='C_CONTIGUOUS')];fn.restype=None
    return fn,meta


def c_values(fn,img,ix,iy,dx,dy):
    ix,iy=[np.ascontiguousarray(a,dtype=np.int32) for a in (ix,iy)]
    dx,dy=[np.ascontiguousarray(a,dtype=np.float32) for a in (dx,dy)]
    if not(ix.shape==iy.shape==dx.shape==dy.shape) or ix.ndim!=1:raise Stop('KERNEL_SHAPE')
    if np.any(ix<0)|np.any(ix>=img.shape[1])|np.any(iy<0)|np.any(iy>=img.shape[0]):raise Stop('KERNEL_INDEX')
    if not np.all(np.isfinite(dx)) or not np.all(np.isfinite(dy)):raise Stop('KERNEL_NONFINITE_COORD')
    if np.any(dx < -1.5) or np.any(dx > .5) or np.any(dy < -1.5) or np.any(dy > .5):raise Stop('KERNEL_OFFSET')
    out=np.empty(ix.size,np.float32)
    fn(ix.size,ix,iy,dx,dy,np.ascontiguousarray(img,dtype=np.float32),img.shape[1],img.shape[0],out)
    return out


def geometry(target,official):
    t=WCS(target,naxis=2);b=WCS(official,naxis=2)
    W,H=target['NAXIS1'],target['NAXIS2'];bw,bh=official['NAXIS1'],official['NAXIS2']
    # Same eight FITS 1-based edge samples and integer truncation as viewer.
    ex=np.array([1,1,1,W/2,W,W,W,W/2]);ey=np.array([1,H/2,H,H,H,H/2,1,1])
    bx,by=b.all_world2pix(*t.all_pix2world(ex,ey,1),1)
    bx,by=bx.astype(np.int32),by.astype(np.int32)
    xlo,xhi=np.clip([bx.min()-10,bx.max()+10],0,bw).astype(int)
    ylo,yhi=np.clip([by.min()-10,by.max()+10],0,bh).astype(int)
    if xlo>=xhi or ylo>=yhi:raise Stop('NO_CANDIDATE_OVERLAP')
    ch=official.copy();ch['CRPIX1']-=xlo;ch['CRPIX2']-=ylo;ch['NAXIS1']=xhi-xlo;ch['NAXIS2']=yhi-ylo
    cw=WCS(ch,naxis=2)
    cx=np.array([0,xhi-xlo-1,xhi-xlo-1,0]);cy=np.array([0,0,yhi-ylo-1,yhi-ylo-1])
    ox,oy=t.all_world2pix(*cw.all_pix2world(cx,cy,0),0)
    x0,x1=np.rint([ox.min(),ox.max()]);y0,y1=np.rint([oy.min(),oy.max()])
    left,right=max(0,x0-12),min(W-1,x1+12);bottom,top=max(0,y0-12),min(H-1,y1+12)
    if left>right or bottom>top:raise Stop('NO_SPLINE_OVERLAP')
    gx=np.linspace(left,right,int(np.ceil((right-left)/25))+1);gy=np.linspace(bottom,top,int(np.ceil((top-bottom)/25))+1)
    yy,xx=np.indices((H,W),dtype=float)
    xd,yd=cw.all_world2pix(*t.all_pix2world(xx,yy,0),0)
    spline=len(gx)>3 and len(gy)>3
    if spline:
        mx,my=np.meshgrid(gx,gy)
        sx,sy=cw.all_world2pix(*t.all_pix2world(mx,my,0),0)
        sx=spline_axis(gy,spline_axis(gx,sx.T,np.clip(np.arange(W),gx[0],gx[-1])).T,np.clip(np.arange(H),gy[0],gy[-1])).astype(np.float32)
        sy=spline_axis(gy,spline_axis(gx,sy.T,np.clip(np.arange(W),gx[0],gx[-1])).T,np.clip(np.arange(H),gy[0],gy[-1])).astype(np.float32)
        margin=12
    else:sx,sy=xd,yd;margin=0
    emitted=(xx>=max(0,x0-margin))&(xx<min(W,x1+margin+1))&(yy>=max(0,y0-margin))&(yy<min(H,y1+margin+1))
    return dict(crop=[int(xlo),int(ylo),int(xhi),int(yhi)],direct=(xd,yd),spline=(sx,sy),emitted=emitted,spline_used=spline,grid=[gx.tolist(),gy.tolist()])


def coordinates(g,variant):
    x,y=g['spline'] if variant=='spline_lut' else g['direct']
    if variant in ('float_coords','direct_lut'):x,y=x.astype(np.float32),y.astype(np.float32)
    ix=(x+.5).astype(np.int32);iy=(y+.5).astype(np.int32)
    x0,y0,x1,y1=g['crop'];active=g['emitted']&(ix>=0)&(ix<x1-x0)&(iy>=0)&(iy<y1-y0)
    return x,y,ix,iy,active


def descriptor_table(prefix,total):
    """Validate entire raw tile table before making any acquisition-cost claim."""
    if total < len(prefix) or total <= 0:raise Stop('INVALID_VIRTUAL_SIZE')
    with fits.open(RangeView(total,[(0,prefix)]),memmap=False,disable_image_compression=True) as hdus:
        hdu=hdus[1];h=hdu.header.copy();loc=int(hdu.fileinfo()['datLoc'])
        if not h.get('ZIMAGE') or h.get('ZNAXIS')!=2 or h.get('ZCMPTYPE') not in ('RICE_ONE','RICE_1'):
            raise Stop('UNSUPPORTED_COMPRESSION_LAYOUT')
        nx,ny,tx,ty=[int(h[k]) for k in ('ZNAXIS1','ZNAXIS2','ZTILE1','ZTILE2')]
        if min(nx,ny,tx,ty)<=0:raise Stop('INVALID_TILE_SHAPE')
        rows=int(h['NAXIS2']);rowbytes=int(h['NAXIS1']);size=rowbytes*rows
        if rows!=math.ceil(nx/tx)*math.ceil(ny/ty):raise Stop('TILE_TABLE_CARDINALITY_MISMATCH')
        if rowbytes<=0 or loc<0 or loc+size>len(prefix):raise Stop('TILE_TABLE_MISSING')
        dtype=hdu.columns.dtype.newbyteorder('>')
        if dtype.itemsize!=rowbytes:raise Stop('TILE_ROW_LAYOUT_MISMATCH')
        end=loc+size+int(h['PCOUNT']);heap=loc+int(h.get('THEAP',size))
        if not loc+size<=heap<=end<=total:raise Stop('INVALID_HEAP_BOUNDARY')
        table=np.frombuffer(prefix,dtype=dtype,count=rows,offset=loc)
        result={i:[] for i in range(rows)};recognized=[]
        for col in hdu.columns:
            if col.name in ('COMPRESSED_DATA','GZIP_COMPRESSED_DATA'):
                if not re.fullmatch(r'1?[PQ]B(?:\(\d+\))?',str(col.format)):raise Stop('DESCRIPTOR_LAYOUT')
                recognized.append(col.name)
                for i,(count,offset) in enumerate(table[col.name]):
                    count,offset=int(count),int(offset)
                    if count<0 or offset<0 or heap+offset+count>end:raise Stop('INVALID_DESCRIPTOR')
                    if count:result[i].append([heap+offset,heap+offset+count-1])
            elif col.name not in ('ZSCALE','ZZERO'):raise Stop('UNSUPPORTED_COLUMN')
        if 'COMPRESSED_DATA' not in recognized:raise Stop('COMPRESSED_DATA_MISSING')
        # Both payloads non-empty has ambiguous decoder precedence; never overstate a minimum.
        if any(len(r)!=1 for r in result.values()):raise Stop('EMPTY_OR_AMBIGUOUS_TILE_PAYLOAD')
        return h,result,dict(table_start=loc,table_end=loc+size-1,heap_start=heap,heap_end=end-1,total=total)


def stats(diff,mask):
    a=diff[mask];nonfinite=int((~np.isfinite(a)).sum());a=a[np.isfinite(a)]
    if not a.size:return dict(n=0,nonfinite=nonfinite)
    return dict(n=int(a.size),nonfinite=nonfinite,rms=float(np.sqrt(np.mean(a*a))),mean=float(a.mean()),max_abs=float(np.max(np.abs(a))),negative=int((a<0).sum()),zero=int((a==0).sum()),positive=int((a>0).sum()),signed_quantiles=list(map(float,np.quantile(a,[0,.01,.25,.5,.75,.99,1]))))


def stratify(diff,obs,safe,overlap):
    yy,xx=np.indices(obs.shape);edge=(xx<3)|(xx>=obs.shape[1]-3)|(yy<3)|(yy>=obs.shape[0]-3)
    masks={'all':safe,'edge3':safe&edge,'interior':safe&~edge,'overlap':safe&overlap,'single_brick':safe&~overlap}
    for a in range(2):
        for b in range(2):masks[f'quadrant_{a}_{b}']=safe&(xx//128==a)&(yy//128==b)
    q=np.quantile(obs[safe],[0,.25,.5,.75,1]) if safe.any() else np.zeros(5)
    for k in range(4):masks[f'intensity_q{k}']=safe&(obs>=q[k])&((obs<q[k+1]) if k<3 else (obs<=q[k+1]))
    return dict(groups={k:stats(diff,v) for k,v in masks.items()},intensity_edges=q.tolist())


VARIANTS=('analytic','float_coords','direct_lut','spline_lut')
ORDER=(1,2,4,6,7,8,9,10,11,12,3,5)


def offline_guard(event,args):
    if event in ('socket.connect','socket.getaddrinfo','urllib.Request'):
        raise Stop('NETWORK_FORBIDDEN_OFFLINE_DIAGNOSTIC')


class LocalIO:
    """Payload IO caps, not OS page-cache or compiler accounting. No network methods."""
    def __init__(self,read_cap,write_cap):
        self.read_cap=read_cap;self.write_cap=write_cap;self.read_bytes=0;self.write_bytes=0
    def read(self,path,expected=None):
        path=Path(path);size=path.stat().st_size
        if self.read_bytes+size>self.read_cap:raise Stop('LOCAL_READ_LIMIT')
        self.read_bytes+=size
        data=path.read_bytes()
        if len(data)!=size:raise Stop('LOCAL_INPUT_CHANGED')
        if expected and hashlib.sha256(data).hexdigest()!=expected:raise Stop('LOCAL_HASH_MISMATCH')
        return data
    def write(self,path,data):
        path=Path(path)
        if self.write_bytes+len(data)>self.write_cap:raise Stop('LOCAL_WRITE_LIMIT')
        self.write_bytes+=len(data)
        path.parent.mkdir(parents=True,exist_ok=True)
        # Preserve an interrupted partial file, never overwrite it on restart.
        import tempfile
        with tempfile.NamedTemporaryFile(dir=path.parent,prefix=path.name+'.',suffix='.part',delete=False) as stream:
            stream.write(data);temp=Path(stream.name)
        os.replace(temp,path)
    def json(self,path,obj):
        self.write(path,(json.dumps(obj,indent=2,allow_nan=False)+'\n').encode())


def packed(mask):return base64.b64encode(np.packbits(mask.ravel()).tobytes()).decode()
def unpacked(text):return np.unpackbits(np.frombuffer(base64.b64decode(text),dtype=np.uint8)).astype(bool).reshape(256,256)


def stencil(g,variant):
    x,y,ix,iy,active=coordinates(g,variant);x0,y0,x1,y1=g['crop']
    # Coordinates in official brick, clipping to the candidate service's input crop.
    for oy in range(-3,4):
        for ox in range(-3,4):
            yield np.clip(ix+ox,0,x1-x0-1)+x0,np.clip(iy+oy,0,y1-y0-1)+y0,active


def candidate_values(fn,g,img,product,variant):
    x,y,ix,iy,active=coordinates(g,variant);x0,y0,x1,y1=g['crop']
    sx,sy=product['brick_x0'],product['brick_y0'];h,w=img.shape
    known=active.copy()
    for ax,ay,_ in stencil(g,variant):known &= (ax>=sx)&(ax<sx+w)&(ay>=sy)&(ay<sy+h)
    # Populate only actually known samples. Unknown NaNs cannot enter an accepted stencil.
    crop=np.full((y1-y0,x1-x0),np.nan,np.float32)
    xa,xb=max(sx,x0),min(sx+w,x1);ya,yb=max(sy,y0),min(sy+h,y1)
    if xa<xb and ya<yb:crop[ya-y0:yb-y0,xa-x0:xb-x0]=img[ya-sy:yb-sy,xa-sx:xb-sx]
    out=np.full(x.shape,np.nan)
    if variant.endswith('lut'):
        out[known]=c_values(fn,crop,ix[known],iy[known],(x[known]-ix[known]).astype(np.float32),(y[known]-iy[known]).astype(np.float32))
    else:
        xx,yy=x[known].astype(float),y[known].astype(float);cx,cy=ix[known],iy[known]
        acc=np.zeros(xx.shape);weight=np.zeros(xx.shape)
        for oy in range(-3,4):
            for ox in range(-3,4):
                v=kernel(xx-cx-ox)*kernel(yy-cy-oy)
                acc+=v*crop[np.clip(cy+oy,0,crop.shape[0]-1),np.clip(cx+ox,0,crop.shape[1]-1)]
                weight+=v
        out[known]=acc/weight
    return out,known|~active,active


def accumulate(values,known,active,dtype=np.float32,reverse=False):
    safe=np.all(known,axis=0);num=np.zeros(safe.shape,dtype);weight=np.zeros(safe.shape,dtype)
    order=range(len(values)-1,-1,-1) if reverse else range(len(values))
    for k in order:
        use=known[k]&active[k]&np.isfinite(values[k])
        num[use]+=values[k][use].astype(dtype);weight[use]+=1
    result=num/np.maximum(weight,np.array(1e-18,dtype=dtype));result[~safe]=np.nan
    return result,safe,weight


def support_for_resource(g,h,descriptors,resource,rectangles):
    """Minimum complete compressed-tile payloads for samples absent from native ROIs.

    Tile indices/masks are computed from actual 49 accesses, not a bounding rectangle.
    These are conditional on the local candidate coordinates, not deployed support.
    """
    cached=union([[e['range_start'],e['range_end']] for e in resource['range_events']])
    tx,ty=int(h['ZTILE1']),int(h['ZTILE2']);ntx=math.ceil(h['ZNAXIS1']/tx)
    required={};needs={} ;active=None
    for xx,yy,act in stencil(g,'spline_lut'):
        active=act
        native=np.zeros(act.shape,bool)
        for r in rectangles:
            native |= (xx>=r['x0'])&(xx<r['x0']+r['width'])&(yy>=r['y0'])&(yy<r['y0']+r['height'])
        tile=(yy//ty)*ntx+(xx//tx)
        for tid in np.unique(tile[act]):
            tid=int(tid);touch=act&(tile==tid)
            required.setdefault(tid,np.zeros(act.shape,bool));required[tid]|=touch
            unknown=touch&~native
            if unknown.any():
                needs.setdefault(tid,np.zeros(act.shape,bool));needs[tid]|=unknown
    tiles=[];local=np.ones(active.shape,bool)
    for tid in sorted(required):
        ranges=descriptors[tid]
        missing=subtract(ranges,cached) if tid in needs else []
        if missing:local &= ~needs[tid]
        tiles.append(dict(tile_id=tid,tile_xy=[tid%ntx,tid//ntx],compressed_ranges=ranges,
            missing_ranges=missing,missing_bytes=sum(b-a+1 for a,b in missing),
            samples_requiring_tile_pixels=int(needs.get(tid,np.zeros(active.shape,bool)).sum()),
            affected_pixels=int(required[tid].sum()),
            missing_dependency_mask=packed(needs[tid]) if missing else None))
    return dict(url=resource['url'],etag=resource['etag'],total_bytes=resource['total_bytes'],cached_ranges=cached,tile_shape=[ty,tx],source_shape=[int(h['ZNAXIS2']),int(h['ZNAXIS1'])],
                native_regions=rectangles,candidate_crop=g['crop'],spline_used=g['spline_used'],spline_grid=g['grid'],
                active_mask=packed(active),active_pixels=int(active.sum()),locally_supported_mask=packed(local),
                tiles=tiles,model='spline_lut_local_approximation_known_bricks_only')


def fixed_jobs(io_manager):
    import pyarrow.parquet as pq
    rows={}
    for key,name in [('normal','C0_PROBE_FITS_REPORT'),('sub','C0_SUBIMAGE_REPORT')]:
        raw=io_manager.read(ROOT/f'c0/probe/{name}.parquet')
        data=pq.read_table(io.BytesIO(raw)).to_pylist()
        rows[key]={r['probe_rank']:r for r in data if r['probe_rank']<=12}
        if set(rows[key])!=set(range(1,13)):raise Stop('FROZEN_SUBSET_MISMATCH')
    rr=json.loads(io_manager.read(ROOT/'c0/reports/C0_RANGE_SUBSET_RESULTS.json'))
    if rr['status']!='C0_RANGE_SUBSET_OK':raise Stop('RANGE_CHECKPOINT_REQUIRED')
    lookup={};rectangles={}
    for res in rr['resources']:
        if not res['etag'] or res['etag'].startswith('W/'):raise Stop('UNPINNED_RESOURCE')
        for c in res['comparisons']:
            if not c['equal']:raise Stop('NATIVE_EQUIVALENCE_REQUIRED')
            lookup[c['probe_rank'],c['hdu']]=res
            rectangles.setdefault(res['url'],[]).append({k:c[k] for k in ('x0','y0','width','height')})
    jobs=[]
    for rank in ORDER:
        sub=rows['sub'][rank];normal=rows['normal'][rank]
        if sub['galaxy_id']!=normal['galaxy_id']:raise Stop('IDENTITY_MISMATCH')
        products=json.loads(sub['audit_json'])['products']
        for band in 'grz':
            ps=[p for p in products if p['kind']=='image' and p['band']==band]
            if not ps:raise Stop('MISSING_BAND')
            resources=[lookup[rank,p['hdu']] for p in ps]
            if len({r['url'] for r in resources})!=len(resources):raise Stop('DUPLICATE_BRICK_BAND')
            # Cache metadata must describe exactly the resource representation.
            for res in resources:
                for e in res['range_events']:
                    if e['url']!=res['url'] or e['etag']!=res['etag'] or e['resource_total_bytes']!=res['total_bytes']:raise Stop('MIXED_RANGE_VERSION')
            jobs.append(dict(rank=rank,band=band,normal=normal,sub=sub,products=ps,resources=resources,rectangles=rectangles))
    return jobs


def run_job(job,fn,io_manager):
    # Each checkpoint is self-contained; preserve all old normal-cutout outputs.
    def raw(row):return io_manager.read(row['path'],json.loads(row['audit_json'])['sha256'])
    with fits.open(io.BytesIO(raw(job['normal'])),memmap=False) as hdus:
        target=hdus[0].header.copy();obs=hdus[0].data['grz'.index(job['band'])].astype(float)
    if obs.shape!=(256,256) or target.get('VERSION','').strip()!='DR5' or target.get('BANDS','').strip()!='grz':raise Stop('FROZEN_IMAGE_MISMATCH')
    vs={v:[] for v in VARIANTS};ks={v:[] for v in VARIANTS};acts={v:[] for v in VARIANTS}
    support=[];coordstats=[];yy,xx=np.indices(obs.shape,dtype=float);world=WCS(target,naxis=2).all_pix2world(xx,yy,0)
    with fits.open(io.BytesIO(raw(job['sub'])),memmap=False) as subs:
        for p,res in zip(job['products'],job['resources']):
            prefix=io_manager.read(res['prefix_path'],res['prefix_sha256'])
            # Hash existing tiles to anchor availability, without decoding new image regions.
            io_manager.read(res['tiles_path'],res['tiles_sha256'])
            for e,name in zip(res['range_events'],('prefix','tiles')):
                if Path(res[name+'_path']).stat().st_size!=e['range_end']-e['range_start']+1:raise Stop('RANGE_SIZE_MISMATCH')
            h,desc,bounds=descriptor_table(prefix,res['total_bytes'])
            with fits.open(RangeView(res['total_bytes'],[(0,prefix)]),memmap=False) as fs:official=fs[1].header.copy()
            g=geometry(target,official);img=subs[p['hdu']].data
            x,y=WCS(subs[p['hdu']].header,naxis=2).all_world2pix(*world,0)
            value,known=interpolate_interior(img,x,y)
            vs['analytic'].append(value);ks['analytic'].append(known);acts['analytic'].append(np.ones(obs.shape,bool))
            for variant in VARIANTS[1:]:
                v,k,a=candidate_values(fn,g,img,p,variant)
                vs[variant].append(v);ks[variant].append(k);acts[variant].append(a)
            sx,sy=g['spline'];dx,dy=g['direct']
            delta=np.hypot(sx.astype(float)-dx,sy.astype(float)-dy)
            coordstats.append(dict(brick=p['brick'],crop=g['crop'],spline_used=g['spline_used'],spline_grid=g['grid'],
                spline_vs_direct_pixels=stats(delta,g['emitted']),
                spline_vs_direct_float32_unequal_pixels=int(((sx!=dx.astype(np.float32))|(sy!=dy.astype(np.float32)))[g['emitted']].sum())))
            sp=support_for_resource(g,h,desc,res,job['rectangles'][res['url']]);sp['heap_bounds']=bounds;sp['brick']=p['brick']
            sp['local_fragments']=[dict(path=res[k+'_path'],sha256=res[k+'_sha256']) for k in ('prefix','tiles')]
            support.append(sp)
    predictions={};safe_masks={};counts={}
    for v in VARIANTS:
        dtype=np.float64 if v in ('analytic','float_coords') else np.float32
        predictions[v],safe_masks[v],counts[v]=accumulate(vs[v],ks[v],acts[v],dtype)
    common=np.logical_and.reduce(list(safe_masks.values()))&np.isfinite(obs)
    if not common.any():raise Stop('NO_COMMON_OPERATOR_SUPPORT')
    overlap=np.sum(acts['spline_lut'],axis=0)>1
    norm=float(np.sum(obs[common]**2));baseline=predictions['analytic'].astype(float)-obs
    old_energy=float(np.sum(baseline[common]**2))
    metrics={};arrays=dict(common=common,overlap=overlap,observed=obs)
    for v in VARIANTS:
        residual=predictions[v].astype(float)-obs;change=predictions[v].astype(float)-predictions['analytic']
        m=stratify(residual,obs,common,overlap)
        m['input_reference_intensity']=stratify(residual,predictions['analytic'],common,overlap)
        energy=float(np.sum(residual[common]**2));m.update(relative_l2=math.sqrt(energy/norm) if norm else None,
             residual_energy_vs_analytic=energy/old_energy if old_energy else None,
             predicted_change=stats(change,common),functional_exact_on_common=bool(np.all(residual[common]==0)),
             common_pixels=int(common.sum()),individual_known_pixels=int(safe_masks[v].sum()),
             zero_finite_contributions=int((common&(counts[v]==0)).sum()))
        metrics[v]=m;arrays['residual_'+v]=residual;arrays['known_'+v]=safe_masks[v]
    reverse,_,_=accumulate(vs['spline_lut'],ks['spline_lut'],acts['spline_lut'],np.float32,True)
    order=reverse.astype(float)-predictions['spline_lut'];arrays['order_delta']=order
    report=dict(rank=job['rank'],band=job['band'],tier='primary_ten' if job['rank'] not in (3,5) else 'secondary_incomplete',
        input_hashes={k:json.loads(job[k]['audit_json'])['sha256'] for k in ('normal','sub')},metrics=metrics,
        common_pixels=int(common.sum()),excluded_pixels=int((~common).sum()),coordinate_diagnostics=coordstats,
        reversed_brick_order_delta=stats(order,common),support=support,
        OBSERVED='Numerical residuals on explicitly available common support only',
        DOCUMENTED='Fixed public candidate source and frozen diagnostic variants',
        INFERRED='Implementation contributions conditional on local WCS/spline and candidate bricks',
        UNRESOLVED=['Deployed commit/configuration/order','FITPACK and astrometry.net WCS identity','Exhaustive service brick selection','Photometric/unit certification'],gate_c='PENDING')
    return report,arrays


def split_ranges(ranges,cap=8*1024**2):
    return [[start,min(end,start+cap-1)] for a,end in ranges for start in range(a,end+1,cap)]


def cost_inventory(rows,counters,attempts):
    groups={}
    for row in rows:
        for sp in row['support']:
            key=(sp['url'],sp['etag'])
            group=groups.setdefault(key,dict(url=sp['url'],etag=sp['etag'],total_bytes=sp['total_bytes'],
                cached_ranges=sp['cached_ranges'],local_fragments=sp['local_fragments'],native_regions=sp['native_regions'],
                brick=sp.get('brick'),tile_shape=sp.get('tile_shape'),source_shape=sp.get('source_shape'),
                heap_bounds=sp['heap_bounds'],required=[],jobs=[]))
            if group['total_bytes']!=sp['total_bytes'] or group['cached_ranges']!=sp['cached_ranges']:raise Stop('RESOURCE_REPRESENTATION_CHANGED')
            for tile in sp['tiles']:group['required'].extend(tile['missing_ranges'])
            group['jobs'].append(dict(rank=row['rank'],band=row['band']))
    for group in groups.values():
        ranges=split_ranges(union(group.pop('required')))
        group['ranges']=[dict(start=a,end=b,bytes=b-a+1,coverage=[],resolves='Missing native stencil samples for conditional full-cutout numerical comparison; NOT deployment or units') for a,b in ranges]
        group['minimum_payload_bytes']=sum(b-a+1 for a,b in ranges)
        group['single_range_requests_at_minimum_bytes']=len(ranges)
        group['used_url_attempts']=attempts.get(group['url'],0)
        group['remaining_url_attempts']=max(0,4-group['used_url_attempts'])
        group['single_range_plan_within_current_url_attempts']=len(ranges)<=group['remaining_url_attempts']
        group['unknown_multipart_request_lower_bound']=math.ceil(group['minimum_payload_bytes']/(8*1024**2))
    coverage=[]
    for row in rows:
        dependencies=[];active=np.zeros((256,256),bool)
        for sp in row['support']:
            active |= unpacked(sp['active_mask']);group=groups[sp['url'],sp['etag']]
            for interval in group['ranges']:
                mask=np.zeros((256,256),bool)
                for tile in sp['tiles']:
                    if any(a<=interval['end'] and b>=interval['start'] for a,b in tile['missing_ranges']):mask |= unpacked(tile['missing_dependency_mask'])
                if mask.any():dependencies.append((interval,mask))
        missing_count=np.zeros((256,256),np.uint16)
        for _,mask in dependencies:missing_count+=mask
        for interval,mask in dependencies:
            interval['coverage'].append(dict(rank=row['rank'],band=row['band'],dependent_pixels=int(mask.sum()),
                newly_complete_if_only_this_range_added=int((mask&(missing_count==1)&active).sum()),
                complete_if_other_dependencies_added=int((mask&active).sum())))
        coverage.append(dict(rank=row['rank'],band=row['band'],candidate_active_pixels=int(active.sum()),
            currently_supported_pixels=int((active&(missing_count==0)).sum()),
            missing_support_pixels=int((active&(missing_count>0)).sum()),
            supported_after_all_proposed_ranges=int(active.sum()),
            outside_all_known_candidate_bricks=int((~active).sum())))
    resources=sorted(groups.values(),key=lambda x:(x['url'],x['etag']))
    total=sum(r['minimum_payload_bytes'] for r in resources);requests=sum(r['single_range_requests_at_minimum_bytes'] for r in resources)
    return dict(resources=resources,coverage=coverage,conditional_minimum_payload_bytes=total,
        single_range_requests_at_minimum_bytes=requests,
        theoretical_request_lower_bound_unverified_multipart=sum(r['unknown_multipart_request_lower_bound'] for r in resources),
        absolute_minimum_requests='UNRESOLVED: multipart support not established; minimizing requests and bytes are distinct objectives',
        remaining_byte_budget=2*1024**3-counters['bytes'],remaining_data_requests=1000-counters['data_requests'],
        within_global_budget=total<=2*1024**3-counters['bytes'] and requests<=1000-counters['data_requests'],
        within_per_url_attempts=all(r['single_range_plan_within_current_url_attempts'] for r in resources),
        bounds='Minimum union of missing compressed payload intervals for required samples under local spline/LUT support and known bricks, reusing native ROIs and verified range fragments. Includes no unnecessary geometric-envelope gaps.',
        not_proven=['Necessity of acquisition for Gate decision','Global service brick completeness','Actual deployed stencil','Multipart capability'],
        network_requests=0,acquisition_authorized=False,gate_c='PENDING')


def ledger_snapshot():
    with sqlite3.connect(f'file:{ROOT}/c0/provenance/resource_ledger.sqlite?mode=ro',uri=True) as db:
        counters=dict(db.execute('SELECT k,n FROM counters'))
        attempts=dict(db.execute('SELECT url,n FROM attempts'))
    return counters,attempts


def provenance(io_manager):
    paths=['GALAXY_RESEARCH_SEED.md','CODEX_PHASE_C0_SPEC.md','C0_EXECUTION_DECISION_001.md','AGENTS.md',
        'c0/reports/C0_OPERATOR_SUPPORT_PLAN.md','c0/reports/C0_NORMAL_CUTOUT_PROTOCOL.md',
        'c0/reports/C0_OPERATOR_RECOVERY_001.md','c0/provenance/C0_NORMAL_CODE_SOURCES.json',
        'c0/provenance/ASTROPY_DEPENDENCY_LOCK.json','c0/provenance/PYARROW_DEPENDENCY_LOCK.json',
        'c0/reports/C0_RANGE_SUBSET_RESULTS.json','c0/probe/C0_PROBE_FITS_REPORT.parquet','c0/probe/C0_SUBIMAGE_REPORT.parquet',
        'c0_pipeline/operator_support.py','c0_pipeline/normal_cutout.py','c0_pipeline/ranges.py','c0_pipeline/core.py']
    hashes={p:hashlib.sha256(io_manager.read(ROOT/p)).hexdigest() for p in paths}
    lock=json.loads((ROOT/'c0/provenance/C0_NORMAL_CODE_SOURCES.json').read_text())
    for e in lock['sources']:
        io_manager.read(e['local_logical_path'],e['sha256']);hashes[e['local_logical_path']]=e['sha256']
    import pyarrow
    return dict(files=hashes,environment=dict(python=sys.version,numpy=np.__version__,astropy=astropy.__version__,pyarrow=pyarrow.__version__,platform=platform.platform()),
                variants=list(VARIANTS),order=list(ORDER),scientific_tolerance=None,spline='Independent not-a-knot tensor interpolation, NOT certified FITPACK',wcs='Astropy TAN, NOT certified astrometry.net')


def load_checkpoint(folder,prov,io_manager):
    manifest=folder/'checkpoint.json'
    if not manifest.exists():return None
    meta=json.loads(io_manager.read(manifest))
    if meta['provenance']!=prov:raise Stop('CHECKPOINT_PROVENANCE_CHANGED')
    data=io_manager.read(folder/meta['result_file'],meta['result_sha256'])
    io_manager.read(folder/meta['arrays_file'],meta['arrays_sha256'])
    return json.loads(data)


def save_checkpoint(folder,prov,row,arrays,io_manager):
    # Payloads are content-addressed; checkpoints committed last. Partial work preserved.
    result=(json.dumps(row,indent=2,allow_nan=False)+'\n').encode();rh=hashlib.sha256(result).hexdigest()
    buffer=io.BytesIO();np.savez_compressed(buffer,**arrays);binary=buffer.getvalue();bh=hashlib.sha256(binary).hexdigest()
    rn='result-'+rh+'.json';bn='arrays-'+bh+'.npz'
    for name,data,digest in [(rn,result,rh),(bn,binary,bh)]:
        if (folder/name).exists():io_manager.read(folder/name,digest)
        else:io_manager.write(folder/name,data)
    io_manager.json(folder/'checkpoint.json',dict(provenance=prov,result_file=rn,result_sha256=rh,arrays_file=bn,arrays_sha256=bh))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    choice=parser.add_mutually_exclusive_group(required=True)
    choice.add_argument('--dry-run',action='store_true',help='Print fixed scope and IO caps; no FITS batch or C compilation')
    choice.add_argument('--smoke',action='store_true',help='Only rank 1/g from existing files; separate checkpoints')
    choice.add_argument('--run',action='store_true',help='Human-run offline 36 diagnostics; primary ten before ranks 3/5')
    parser.add_argument('--max-read-mib',type=int,default=512)
    parser.add_argument('--max-write-mib',type=int,default=192)
    args=parser.parse_args()
    if not(1<=args.max_read_mib<=512 and 1<=args.max_write_mib<=192):parser.error('IO caps must be 1..512 MiB read and 1..192 MiB write')
    sys.addaudithook(offline_guard)
    counters,attempts=ledger_snapshot()
    if args.dry_run:
        print(json.dumps(dict(objects=12,comparisons=36,order=ORDER,variants=VARIANTS,network_requests=0,additional_download_bytes=0,
            read_cap_mib=args.max_read_mib,write_cap_mib=args.max_write_mib,estimated_ram_mib=512,
            expected_seconds='60-300; host dependent',cumulative_counters=counters,
            extra_io='Compiler/build metadata and append-only log/status overhead < 8 MiB; FITS/fragment/checkpoint payload IO metered',
            gate_c='PENDING',success_sentinel='C0_OPERATOR_SUPPORT_OK'),indent=2));return 0
    io_manager=LocalIO(args.max_read_mib*1024**2,args.max_write_mib*1024**2)
    mode='smoke' if args.smoke else 'batch';folder=BASE/mode
    log=ROOT/f'c0/logs/C0_OPERATOR_SUPPORT_{mode.upper()}.log';log.parent.mkdir(parents=True,exist_ok=True)
    status_path=ROOT/f'c0/reports/C0_OPERATOR_SUPPORT_{mode.upper()}_STATUS.json'
    success='C0_OPERATOR_SUPPORT_SMOKE_OK' if args.smoke else 'C0_OPERATOR_SUPPORT_OK'
    code=0;reason=None;owned=False
    with (ROOT/'c0/provenance/manual_execution.lock').open('a') as guard, log.open('a') as stream:
        try:
            fcntl.flock(guard,fcntl.LOCK_EX|fcntl.LOCK_NB);owned=True
            with contextlib.redirect_stdout(stream),contextlib.redirect_stderr(stream):
                print(utc(),'START',mode,flush=True)
                prov=provenance(io_manager);fn,build=build_kernel();prov['kernel_build']=build
                if args.smoke:folder=folder/prov['files']['c0_pipeline/operator_support.py']
                snapshot=folder/'implementation.py'
                if snapshot.exists():io_manager.read(snapshot,prov['files']['c0_pipeline/operator_support.py'])
                else:io_manager.write(snapshot,Path(__file__).read_bytes())
                jobs=fixed_jobs(io_manager)
                if args.smoke:jobs=jobs[:1]
                rows=[]
                for job in jobs:
                    dest=folder/f'{job["rank"]:03d}_{job["band"]}'
                    row=load_checkpoint(dest,prov,io_manager)
                    if row is None:
                        row,arrays=run_job(job,fn,io_manager);save_checkpoint(dest,prov,row,arrays,io_manager)
                        print(job['rank'],job['band'],'CHECKPOINT_COMMITTED',flush=True)
                    else:
                        for key in ('normal','sub'):io_manager.read(job[key]['path'],json.loads(job[key]['audit_json'])['sha256'])
                        for res in job['resources']:
                            for key in ('prefix','tiles'):io_manager.read(res[key+'_path'],res[key+'_sha256'])
                        print(job['rank'],job['band'],'CHECKPOINT_REUSED',flush=True)
                    rows.append(row)
                inventory=cost_inventory(rows,counters,attempts)
                stem=ROOT/f'c0/reports/C0_OPERATOR_SUPPORT_{mode.upper()}'
                # Immutable run provenance; current pointers/status regenerated without redoing jobs.
                io_manager.json(folder/'provenance.json',prov)
                io_manager.json(str(stem)+'_INVENTORY.json',inventory)
                summary=[{k:v for k,v in r.items() if k!='support'} for r in rows]
                io_manager.json(str(stem)+'_RESULTS.json',dict(timestamp_utc=utc(),status=success,rows=summary,
                    network_requests=0,gate_c='PENDING',io_read_bytes=io_manager.read_bytes,io_write_bytes=io_manager.write_bytes,
                    kernel_build=build,counters=counters,provenance=prov,inventory_path=str(stem)+'_INVENTORY.json'))
                if ledger_snapshot()!=(counters,attempts):raise Stop('OFFLINE_LEDGER_CHANGED')
                print(utc(),'COMPLETE',success,flush=True)
        except (Exception,KeyboardInterrupt) as exc:
            code=2;reason=str(exc) if isinstance(exc,Stop) else type(exc).__name__;print(utc(),'FAILED',reason,file=stream,flush=True)
    if owned:
        atomic_json(status_path,dict(timestamp_utc=utc(),status=success if code==0 else 'C0_OPERATOR_SUPPORT_FAILED',exit_code=code,reason=reason,
            log=str(log),network_requests=0,gate_c='PENDING',io_read_bytes=io_manager.read_bytes,io_write_bytes=io_manager.write_bytes))
    print(success if code==0 else 'C0_OPERATOR_SUPPORT_FAILED');return code


if __name__=='__main__':sys.exit(main())
