"""Selection accepts auxiliary arrays only; image is not a parameter or dependency."""
from dataclasses import dataclass
import hashlib
import numpy as np
from .core import InputError,IntegrityError,SLOTS,BANDS,strict
from .arrays import crop,FLAG_SELECTION

def tie(slot,region,brick,x,y):
 return hashlib.sha256(f'OC3-v1|{slot}|{region}|{brick}|{x}|{y}'.encode()).hexdigest()
def technical_grid(shape):
 ys=sorted(set(range(0,shape[0],64))|{shape[0]-1})
 xs=sorted(set(range(0,shape[1],64))|{shape[1]-1})
 return [(x,y) for y in ys for x in xs]

def choose_bricks(bricks,allowed):
 for b in bricks: strict(b,'brick',('region','brickname','generation','release','grz','corrected_9012'))
 selected=[]
 for region in ('south','north'):
  eligible=[b for b in bricks if b['region']==region and (region,b['brickname']) in allowed and b['grz'] is True and b['release']=='DR9' and (region!='south' or b['corrected_9012'] is True and b['generation']=='9012')]
  if not eligible: raise InputError('BRICK_STRATUM_UNAVAILABLE')
  ordered=sorted(eligible,key=lambda b:(hashlib.sha256(f"OC3-v1|brick|{region}|{b['brickname']}".encode()).hexdigest(),b['brickname']))
  selected.append(ordered[0])
 return selected

@dataclass(frozen=True)
class AuxiliaryBundle:
 nexp: dict
 psfsize: dict
 maskbits: object
 def __post_init__(self):
  if set(self.nexp)!=set(BANDS) or set(self.psfsize)!=set(BANDS): raise InputError('AUXILIARY_BANDS')
  shape=np.shape(self.maskbits)
  if len(shape)!=2 or not np.issubdtype(np.asarray(self.maskbits).dtype,np.integer): raise InputError('AUXILIARY_MASK')
  if any(np.shape(a)!=shape for a in list(self.nexp.values())+list(self.psfsize.values())): raise InputError('AUXILIARY_GRID')
 @classmethod
 def from_mapping(cls,values):
  if set(values)!={'nexp','psfsize','maskbits'}: raise InputError('SELECTOR_FORBIDDEN_INPUT')
  return cls(**values)

class PixelRectangle:
 """Explicit synthetic geometry oracle. Production uses SkyRectangle."""
 def __init__(self,bounds): self.bounds=tuple(bounds)
 def inside(self,x,y):
  a,b,c,d=self.bounds; return (x>=a)&(x<=c)&(y>=b)&(y<=d)
 def distance(self,x,y):
  x=np.asarray(x); y=np.asarray(y); a,b,c,d=self.bounds
  return np.minimum.reduce([np.hypot(x-a,y-np.clip(y,b,d)),np.hypot(x-c,y-np.clip(y,b,d)),np.hypot(x-np.clip(x,a,c),y-b),np.hypot(x-np.clip(x,a,c),y-d)])
 def sky(self,x,y): return [float(x),float(y)]

class SkyRectangle:
 """Distances to small DR9 RA/Dec rectangle projected on a native TAN plane.
 Boundary curves are minimized numerically, not replaced by MASKBITS/pixel shape.
 """
 def __init__(self,header,bounds):
  from astropy.wcs import WCS
  self.wcs=WCS(header); self.bounds=tuple(bounds)
  if list(self.wcs.wcs.ctype)!=['RA---TAN','DEC--TAN'] or self.wcs.has_distortion: raise InputError('PRIMARY_GEOMETRY_LAYOUT_UNSUPPORTED')
  ra0,dec0,ra1,dec1=self.bounds; width=(ra1-ra0)%360
  if not 0<width<1 or not 0<dec1-dec0<1: raise InputError('PRIMARY_GEOMETRY_BOUNDS')
  self.width=width
 def inside(self,x,y):
  ra,dec=self.wcs.all_pix2world(x,y,0); a,b,c,d=self.bounds
  return (((ra-a)%360)<=self.width)&(dec>=b)&(dec<=d)
 def sky(self,x,y): return [float(v) for v in self.wcs.all_pix2world(x,y,0)]
 def distance(self,x,y):
  x,y=np.broadcast_arrays(np.asarray(x,dtype=float),np.asarray(y,dtype=float)); a,b,c,d=self.bounds
  best=np.full(x.shape,np.inf)
  for edge in range(4):
   def objective(t):
    if edge<2: ra=np.full(t.shape,a if edge==0 else a+self.width); dec=b+(d-b)*t
    else: ra=a+self.width*t; dec=np.full(t.shape,b if edge==2 else d)
    px,py=self.wcs.all_world2pix(ra,dec,0)
    return (px-x)**2+(py-y)**2
   # Small (<1 degree) TAN rectangle; bracket each minimum on a fixed 16-way grid.
   coarse=np.stack([objective(np.full(x.shape,t)) for t in np.linspace(0,1,17)])
   k=np.argmin(coarse,axis=0); lo=np.maximum(0,(k-1)/16); hi=np.minimum(1,(k+1)/16)
   g=(np.sqrt(5)-1)/2
   for _ in range(48):
    p=hi-g*(hi-lo); q=lo+g*(hi-lo); left=objective(p)<objective(q)
    hi=np.where(left,q,hi); lo=np.where(left,lo,p)
   best=np.minimum(best,np.minimum(objective((lo+hi)/2),coarse.min(axis=0)))
  return np.sqrt(best)

def select_slots(bricks,bundles,geometries,check=lambda:None):
 output=[]; used=set(); flow=[]
 for slot in SLOTS:
  region='south' if slot.startswith('S') else 'north'
  brick=next(b for b in bricks if b['region']==region); name=brick['brickname']; aux=bundles[region]; geo=geometries[region]
  shape=np.shape(aux.maskbits); candidates=[]
  for x,y in technical_grid(shape):
   check()
   if (region,name,x,y) in used: continue
   masks,window=crop(aux.maskbits,x,y); complete=masks.shape==(129,129)
   key=tie(slot,region,name,x,y); score=0.; priority=0; exercised=True
   if slot in ('S1','N1'):
    if not complete or not bool(geo.inside(x,y)): continue
    dist=float(geo.distance(x,y))
    if dist<64: continue
    if dist<64+np.hypot(64,64):
     yy,xx=np.mgrid[y-64:y+65,x-64:x+65]
     if not geo.inside(xx,yy).all() or geo.distance(xx,yy).min()<64: continue
   elif slot=='S2':
    l,bot,r,top=window['obtained']; yy,xx=np.mgrid[bot:top,l:r]; inside=geo.inside(xx,yy)
    if not inside.any() or inside.all(): continue
    score=float(geo.distance(x,y))
   elif slot=='S3':
    if not complete or not np.any(masks&FLAG_SELECTION): continue
   elif slot=='N2':
    arrays=[crop(aux.nexp[b],x,y)[0] for b in BANDS]
    if any(np.any(a==0) and np.any(a>0) for a in arrays): priority=0
    elif any(np.any(a==1) for a in arrays): priority=1
    else: continue
   elif slot=='N3':
    if not complete: continue
    arrays=[crop(aux.psfsize[b],x,y)[0] for b in BANDS]
    if any(not np.isfinite(a).all() or np.min(a)<=0 for a in arrays): continue
    med=[float(np.median(a)) for a in arrays]
    v=max(max(float((a.max()-a.min())/np.median(a)) for a in arrays),max(med)/min(med)-1)
    score=-v; exercised=v>=.10
   candidates.append(((priority,score,key,y,x),dict(slot=slot,region=region,brick=name,x=x,y=y,
    ra_dec=geo.sky(x,y),window=window,selection_hash=key,status='SELECTED' if exercised else 'STRATUM_NOT_EXERCISED',
    V=-score if slot=='N3' else None)))
  flow.append(dict(slot=slot,candidates=len(candidates)))
  if not candidates:
   output.append(dict(slot=slot,status='NOT_AVAILABLE',reason='NO_FROZEN_STRATUM_CANDIDATE')); continue
  _,row=min(candidates,key=lambda c:c[0]); output.append(row); used.add((region,name,row['x'],row['y']))
 return output,flow
