"""T10 Amendment 001 only: 999 permutations, one omnibus per slot/band."""
import hashlib
import json
import numpy as np
from .core import InputError,SLOTS,BANDS

LAGS=((1,0),(0,1),(1,1),(1,-1),(2,0),(0,2),(4,0),(0,4),(8,0),(0,8))
PERMUTATIONS=999
DETECTED='EMPIRICAL_SPATIAL_DEPENDENCE_DETECTED_AT_PILOT_SENSITIVITY'
NOT_DETECTED='NOT_DETECTED_AT_PILOT_SENSITIVITY'
NOT_AUDITABLE='NOT_AUDITABLE'

def rng_for(slot,band):
 if slot not in SLOTS or band not in BANDS: raise InputError('RNG_UNIT')
 h=hashlib.sha256(f'OC3-v1|{slot}|{band}'.encode('utf-8')).digest()
 words=tuple(int.from_bytes(h[i:i+4],'big') for i in range(0,32,4))
 return np.random.Generator(np.random.PCG64(np.random.SeedSequence(entropy=301,spawn_key=words)))

def pairs(a,dx,dy):
 # Input shape (...,32,32), x is column, y is row.
 y0=max(0,-dy); y1=a.shape[-2]-max(0,dy)
 x0=max(0,-dx); x1=a.shape[-1]-max(0,dx)
 return a[...,y0:y1,x0:x1], a[...,y0+dy:y1+dy,x0+dx:x1+dx]

def correlation(a,b,valid=None):
 a=np.asarray(a,dtype=np.float64); b=np.asarray(b,dtype=np.float64)
 keep=np.isfinite(a)&np.isfinite(b)
 if valid is not None: keep&=valid
 x=a[keep]; y=b[keep]; n=len(x)
 row=dict(pair_count=n,mean_x=None,mean_y=None,variance_x=None,variance_y=None,covariance=None,r=None,estimability='NOT_ESTIMABLE')
 if not n: return row
 mx=float(x.mean()); my=float(y.mean()); row.update(mean_x=mx,mean_y=my)
 if n<2: return row
 xx=x-mx; yy=y-my
 vx=float(np.dot(xx,xx)/(n-1)); vy=float(np.dot(yy,yy)/(n-1)); cv=float(np.dot(xx,yy)/(n-1))
 row.update(variance_x=vx,variance_y=vy,covariance=cv)
 if n>=128 and vx>0 and vy>0:
  r=float(cv/np.sqrt(vx*vy))
  if np.isfinite(r): row.update(r=r,estimability='ESTIMABLE')
 return row

def blocks_for(array,offset=(0,0)):
 a=np.asarray(array); out=[]; ids=[]
 # Offset is obtained origin relative to the requested 129x129 domain.
 for by in range(4):
  for bx in range(4):
   x=bx*32-offset[0]; y=by*32-offset[1]
   if x>=0 and y>=0 and x+32<=a.shape[1] and y+32<=a.shape[0]:
    out.append(a[y:y+32,x:x+32]); ids.append(by*4+bx)
 return (np.stack(out) if out else np.empty((0,32,32),dtype=a.dtype)),ids

def r_matrix(blocks):
 """Float64 centered pair covariance, batched over original blocks."""
 out=np.full((len(blocks),len(LAGS)),np.nan)
 for k,(dx,dy) in enumerate(LAGS):
  a,b=pairs(blocks,dx,dy); a=a.reshape(len(blocks),-1).astype(np.float64); b=b.reshape(len(blocks),-1).astype(np.float64)
  mask=np.isfinite(a)&np.isfinite(b); n=mask.sum(axis=1); den=np.maximum(n,1)
  mx=np.where(mask,a,0).sum(axis=1)/den; my=np.where(mask,b,0).sum(axis=1)/den
  x=np.where(mask,a-mx[:,None],0); y=np.where(mask,b-my[:,None],0)
  vx=(x*x).sum(axis=1); vy=(y*y).sum(axis=1); cv=(x*y).sum(axis=1)
  good=(n>=128)&(vx>0)&(vy>0)
  out[good,k]=cv[good]/np.sqrt(vx[good]*vy[good])
 return out

def omnibus_summary(matrix):
 matrix=np.asarray(matrix,dtype=float); rj=[]; indices=[]
 for j,row in enumerate(matrix):
  vals=row[np.isfinite(row)]
  if vals.size: rj.append(float(np.max(np.abs(vals)))); indices.append(j)
 return dict(T=float(np.median(rj)) if rj else None,max_R=float(max(rj)) if rj else None,
  IQR_R=float(np.quantile(rj,.75,method='linear')-np.quantile(rj,.25,method='linear')) if rj else None,
  R_j=rj,estimable_block_indices=indices,estimable_blocks=len(rj),auditable=len(rj)>=4)

def p_value(observed,permuted):
 if len(permuted)!=999: raise InputError('AMENDMENT_REQUIRES_999_PERMUTATIONS')
 if not np.isfinite(observed) or not np.isfinite(permuted).all(): raise InputError('NONFINITE_PERMUTATION_STATISTIC')
 return (1+int(np.count_nonzero(np.asarray(permuted)>=observed)))/1000

def descriptive_rows(image,states,slot,band,offset=(0,0)):
 blocks,ids=blocks_for(image,offset); rows=[]
 shape=np.shape(image)
 support=np.array([r['support_evidence']=='POSITIVE_NEXP_AND_WEIGHT' for r in states]).reshape(shape)
 raw=np.array([r['raw_optical_maskbits'] if r['raw_optical_maskbits'] is not None else -1 for r in states]).reshape(shape)
 supports,_=blocks_for(support,offset); masks,_=blocks_for(raw,offset)
 for block,j in zip(blocks,range(len(blocks))):
  for dx,dy in LAGS:
   a,b=pairs(block,dx,dy); sa,sb=pairs(supports[j],dx,dy); ma,mb=pairs(masks[j],dx,dy)
   strata=[('all_finite',None),('positive_nexp_and_ivar',sa&sb)]
   flag_pairs=np.unique(np.column_stack((ma.ravel(),mb.ravel())),axis=0)
   for fa,fb in flag_pairs:
    mask=(ma==fa)&(mb==fb)
    strata.extend([(f'maskpair:{int(fa)},{int(fb)}',mask), (f'supported_maskpair:{int(fa)},{int(fb)}',mask&sa&sb)])
   for name,valid in strata:
    rows.append(dict(row_type='descriptive',slot=slot,band=band,block=ids[j],lag=[dx,dy],stratum=name,**correlation(a,b,valid)))
 # Missing blocks explicitly represented, never replaced.
 for block in sorted(set(range(16))-set(ids)):
  for lag in LAGS:
   rows.append(dict(row_type='descriptive',slot=slot,band=band,block=block,lag=list(lag),stratum='all_finite',pair_count=0,mean_x=None,mean_y=None,variance_x=None,variance_y=None,covariance=None,r=None,estimability='BLOCK_UNAVAILABLE'))
 return rows

def t10(image,states,slot,band,offset=(0,0),check=lambda:None):
 from .arrays import state_keys
 a=np.asarray(image); original,ids=blocks_for(a,offset)
 rows=descriptive_rows(a,states,slot,band,offset)
 observed=r_matrix(original) if len(original) else np.empty((0,10))
 summary=omnibus_summary(observed)
 unit=dict(row_type='omnibus',slot=slot,band=band,block_ids=ids,**summary,p_raw=None,p_holm=None,
  observed_r_jl=[[float(v) if np.isfinite(v) else None for v in row] for row in observed],
  observed_estimable_lags=[[k for k,v in enumerate(row) if np.isfinite(v)] for row in observed],
  inference=NOT_AUDITABLE,permutations=0,permutation_T=[],permutation_estimability=[],reason='FEWER_THAN_FOUR_ESTIMABLE_BLOCKS')
 if not summary['auditable']: return rows,unit
 keys,_=blocks_for(state_keys(states,a.shape),offset); groups=[]; partitions=[]
 for j in range(len(original)):
  flat=original[j].ravel(); kk=keys[j].ravel()
  ordered=sorted(set(kk)); classes=[np.flatnonzero((kk==key)&np.isfinite(flat)) for key in ordered]
  groups.append(classes)
  partitions.append(dict(block=ids[j],classes=[dict(key=key,coordinate_count=int((kk==key).sum()),finite_count=len(indices)) for key,indices in zip(ordered,classes)],singleton_finite_pixels=sum(len(ix) for ix in classes if len(ix)==1),permutable_finite_pixels=sum(len(ix) for ix in classes if len(ix)>1)))
 unit['fixed_class_partition']=partitions
 rng=rng_for(slot,band); ts=[]; estimability=[]; bad=False
 for iteration in range(999):
  check(); simulated=original.copy()
  for j,classes in enumerate(groups):
   src=original[j].ravel(); dst=simulated[j].ravel()
   for indices in classes:
    # Singleton classes remain fixed without consuming a new random selection.
    if len(indices)>1: dst[indices]=rng.permutation(src[indices])
  mat=r_matrix(simulated); stat=omnibus_summary(mat)
  estimability.append(dict(blocks=stat['estimable_blocks'],lags_per_block=np.isfinite(mat).sum(axis=1).tolist()))
  ts.append(stat['T']); bad|=not stat['auditable']
 unit.update(permutations=999,permutation_T=ts,permutation_estimability=estimability,
  random_substream=f'OC3-v1|{slot}|{band}',rng='PCG64',numpy_version=np.__version__,master_seed=301)
 if bad:
  unit.update(auditable=False,reason='PERMUTATION_NOT_AUDITABLE'); return rows,unit
 unit.update(p_raw=p_value(unit['T'],ts),reason='OMNIBUS_AWAITING_FAMILY_HOLM',null_degenerate=bool(np.ptp(ts)==0))
 return rows,unit

def holm(units):
 if len(units)>18 or len({(u['slot'],u['band']) for u in units})!=len(units): raise InputError('OMNIBUS_FAMILY')
 for u in units:
  if u.get('row_type')!='omnibus' or u['slot'] not in SLOTS or u['band'] not in BANDS: raise InputError('NOT_AN_OMNIBUS')
 active=[u for u in units if u.get('auditable') and u.get('p_raw') is not None]
 active.sort(key=lambda u:(u['p_raw'],SLOTS.index(u['slot']),BANDS.index(u['band'])))
 m=len(active); previous=0.
 for i,u in enumerate(active):
  if not 0.001<=u['p_raw']<=1: raise InputError('P_VALUE_RANGE')
  previous=max(previous,(m-i)*u['p_raw']); adjusted=min(1.,previous)
  u.update(p_holm=adjusted,holm_rank=i+1,holm_m=m,inference=DETECTED if adjusted<=.05 else NOT_DETECTED,reason='CONDITIONAL_EXCHANGEABILITY_ONLY')
 for u in units:
  u['holm_m']=m
  if u not in active: u.update(p_holm=None,p_raw=None,inference=NOT_AUDITABLE)
 return units
