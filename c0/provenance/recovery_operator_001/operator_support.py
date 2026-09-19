"""Offline C0 operator attribution and exact compressed-tile support inventory.

No networking. All output is diagnostic, not a Gate decision.
"""
import argparse
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
    if source.count('lanczos_resample_one_, L)')!=1:raise Stop('UNEXPECTED_AUDITED_C_BOUNDARY')
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
        atomic_json(lock,dict(command=cmd,compiler=subprocess.check_output(['cc','--version'],text=True).splitlines()[0],source_sha256=sha(c),binary_sha256=sha(so),original_sha256=sha(SOURCE)))
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
    if np.any(np.abs(dx)>1.01) or np.any(np.abs(dy)>1.01):raise Stop('KERNEL_OFFSET')
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
        sx=spline_axis(gy,spline_axis(gx,sx.T,np.arange(W)).T,np.arange(H)).astype(np.float32)
        sy=spline_axis(gy,spline_axis(gx,sy.T,np.arange(W)).T,np.arange(H)).astype(np.float32)
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
    with fits.open(RangeView(total,[(0,prefix)]),memmap=False,disable_image_compression=True) as hdus:
        hdu=hdus[1];h=hdu.header.copy();loc=hdu.fileinfo()['datLoc'];size=h['NAXIS1']*h['NAXIS2']
        if loc+size>len(prefix):raise Stop('TILE_TABLE_MISSING')
        table=np.frombuffer(prefix,dtype=hdu.columns.dtype.newbyteorder('>'),count=h['NAXIS2'],offset=loc)
        heap=loc+h.get('THEAP',size);result={i:[] for i in range(h['NAXIS2'])}
        for col in hdu.columns:
            if col.name in ('COMPRESSED_DATA','GZIP_COMPRESSED_DATA'):
                if not re.fullmatch(r'1?[PQ]B(?:\(\d+\))?',str(col.format)):raise Stop('DESCRIPTOR_LAYOUT')
                for i,(count,offset) in enumerate(table[col.name]):
                    if count<0 or offset<0 or heap+offset+count>total:raise Stop('INVALID_DESCRIPTOR')
                    if count:result[i].append([int(heap+offset),int(heap+offset+count-1)])
            elif col.name not in ('ZSCALE','ZZERO'):raise Stop('UNSUPPORTED_COLUMN')
        return h,result


def stats(diff,mask):
    a=diff[mask];a=a[np.isfinite(a)]
    if not a.size:return dict(n=0)
    return dict(n=int(a.size),rms=float(np.sqrt(np.mean(a*a))),mean=float(a.mean()),max_abs=float(np.max(np.abs(a))),negative=int((a<0).sum()),zero=int((a==0).sum()),positive=int((a>0).sum()),signed_quantiles=list(map(float,np.quantile(a,[0,.01,.25,.5,.75,.99,1]))))


def stratify(diff,obs,safe,overlap):
    yy,xx=np.indices(obs.shape);edge=(xx<3)|(xx>=obs.shape[1]-3)|(yy<3)|(yy>=obs.shape[0]-3)
    masks={'all':safe,'edge3':safe&edge,'interior':safe&~edge,'overlap':safe&overlap,'single_brick':safe&~overlap}
    for a in range(2):
        for b in range(2):masks[f'quadrant_{a}_{b}']=safe&(xx//128==a)&(yy//128==b)
    q=np.quantile(obs[safe],[0,.25,.5,.75,1]) if safe.any() else np.zeros(5)
    for k in range(4):masks[f'intensity_q{k}']=safe&(obs>=q[k])&((obs<q[k+1]) if k<3 else (obs<=q[k+1]))
    return dict(groups={k:stats(diff,v) for k,v in masks.items()},intensity_edges=q.tolist())
