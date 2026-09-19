"""Four predeclared lightweight offline audit tests; no batch reconstruction."""
import io,json,hashlib,sys
from pathlib import Path
import numpy as np
from astropy.io import fits
from . import operator_support as op
from .run import ROOT
from .ranges import RangeView
from .core import utc

def main():
    sys.addaudithook(op.offline_guard);before=op.ledger_snapshot()
    budget=op.LocalIO(128*1024**2,8*1024**2);hashes={}
    def read(path,expected=None):
        path=Path(path);data=budget.read(path,expected);hashes[str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)]=hashlib.sha256(data).hexdigest();return data
    protocol=read(ROOT/'c0/reports/C0_BOUNDED_AUDIT_PROTOCOL.md')
    fn,build=op.build_kernel()
    x=np.array([-.75,-.25,.25,4.25,10.75])[None,:];y=np.full(x.shape,4.25)
    g=dict(crop=[0,0,12,12],direct=(x,y),spline=(x.astype('f4'),y.astype('f4')),emitted=np.ones(x.shape,bool))
    yy,xx=np.indices((12,12));imp=np.zeros((12,12),np.float32);imp[4,0]=1
    patterns=dict(constant=np.ones((12,12)),ramp=xx,impulse=imp,checker=(xx+yy)%2)
    synthetic={}
    for name,img in patterns.items():
        row={}
        for v in ('analytic','float_coords','direct_lut'):
            value,_,_=op.candidate_values(fn,g,img.astype('f4'),dict(brick_x0=0,brick_y0=0),v)
            translated,_,_=op.candidate_values(fn,dict(g,crop=[100,200,112,212]),img.astype('f4'),dict(brick_x0=100,brick_y0=200),v)
            assert np.array_equal(value,translated,equal_nan=True)
            row[v]=value.ravel().tolist()
        a=np.array(row['direct_lut']);b=np.array(row['analytic']);known=[np.ones(a.shape,bool)]*2
        blend,_,_=op.accumulate([a,b],known,known);rev,_,_=op.accumulate([a,b],known,known,reverse=True)
        row['two_brick_order_delta']=(blend-rev).tolist();synthetic[name]=row
    vals=[np.array([1e20]),np.array([-1e20]),np.array([1.])];k=[np.ones(1,bool)]*3
    forward=op.accumulate(vals,k,k)[0];reverse=op.accumulate(vals,k,k,reverse=True)[0]
    summary=json.loads(read(ROOT/'c0/reports/C0_CACHED_SUPPORT_BATCH_RESULTS.json'))
    jobs=op.fixed_jobs(budget);examples=[]
    for job in [j for j in jobs if j['rank'] in (3,5) and j['band']=='g']:
        normal=read(job['normal']['path'],json.loads(job['normal']['audit_json'])['sha256'])
        with fits.open(io.BytesIO(normal),memmap=False) as f:target=f[0].header.copy()
        exceptional=np.zeros((256,256),bool);edge=exceptional.copy();brickedge=edge.copy()
        for res in job['resources']:
            prefix=read(res['prefix_path'],res['prefix_sha256'])
            with fits.open(RangeView(res['total_bytes'],[(0,prefix)]),memmap=False) as f:h=f[1].header.copy()
            geom=op.geometry(target,h);a,b,ix,iy,active=op.coordinates(geom,'direct_lut')
            dx=a-ix;dy=b-iy;exceptional|=active&((dx<-.5)|(dx>.5)|(dy<-.5)|(dy>.5))
            x0,y0,x1,y1=geom['crop'];touch=active&((ix<3)|(iy<3)|(ix>=x1-x0-3)|(iy>=y1-y0-3));edge|=touch
            brickedge|=active&(((ix<3)&(x0==0))|((iy<3)&(y0==0))|((ix>=x1-x0-3)&(x1==h['NAXIS1']))|((iy>=y1-y0-3)&(y1==h['NAXIS2'])))
        folder=ROOT/f'c0/reports/cached_support/batch/{job["rank"]:03d}_g';meta=json.loads(read(folder/'checkpoint.json'))
        assert meta['provenance']==summary['provenance']
        with np.load(io.BytesIO(read(folder/meta['arrays_file'],meta['arrays_sha256']))) as arr:
            common=arr['common'];result=dict(rank=job['rank'],band='g',groups={})
            for name,m in dict(exceptional=exceptional,ordinary=~exceptional,crop_edge=edge,brick_edge=brickedge,overlap=arr['overlap']).items():
                mask=common&m;result['groups'][name]={}
                for v in ('analytic','float_coords'):
                    d=arr['prediction_'+v].astype(float)-arr['prediction_direct_lut'].astype(float)
                    result['groups'][name][v]=dict(op.stats(d,mask),energy=float(np.sum(d[mask]**2)))
            examples.append(result)
    structures=[]
    for row in summary['rows']:
        structures.append(dict(rank=row['rank'],band=row['band'],metrics=row['metrics'],masks=row['masks']))
    sources=json.loads(read(ROOT/'c0/provenance/C0_NORMAL_CODE_SOURCES.json'))
    for e in sources['sources']:read(ROOT/e['local_logical_path'],e['sha256'])
    for path in ['c0/provenance/raw_metadata/S6.raw','c0/provenance/raw_metadata/S7.raw','C0_EXECUTION_DECISION_001.md','c0/reports/C0_NORMAL_CUTOUT_PROTOCOL.md','c0_pipeline/bounded_audit.py']:
        read(ROOT/path)
    assert before==op.ledger_snapshot()
    out=dict(timestamp_utc=utc(),test_scope='T1–T4 frozen; no numerical acceptance tolerance',synthetic=synthetic,three_term_order=dict(forward=forward.tolist(),reverse=reverse.tolist()),cached_examples=examples,existing_structure=structures,input_hashes=hashes,kernel_build=build,network_requests=0,counters=before[0],read_bytes=budget.read_bytes)
    budget.json(ROOT/'c0/reports/C0_BOUNDED_AUDIT_RESULTS.json',out)
    print('C0_BOUNDED_AUDIT_TESTS_OK')
if __name__=='__main__':main()
