"""Native slices and observational diagnostics; no image preprocessing."""
from __future__ import annotations
import math
import json
from pathlib import Path
from .core import DependencyError,InputError,IntegrityError,canonical,digest
try:
 import numpy as np
except ImportError as e:
 raise DependencyError('NUMPY_REQUIRED_NO_SEMANTIC_FALLBACK') from e

STATE_AXES=('array_present','finite_image','image_zero','weight_finite','weight_sign',
 'nexp_value','raw_optical_maskbits','known_flags','unknown_bits','geometric_primary',
 'support_evidence','quality_evidence','validity_state')
KNOWN_OPTICAL=sum(1<<i for i in list(range(8))+[10,11,12,13])
KNOWN_DR9=(1<<14)-1
FLAG_SELECTION=sum(1<<i for i in list(range(1,8))+[10,11,12,13])

def array_hash(a):
 a=np.asarray(a)
 return digest(canonical({'dtype':a.dtype.str,'shape':list(a.shape)})+a.tobytes(order='C'))

def crop(array,x,y,radius=64):
 if radius!=64: raise InputError('FROZEN_WINDOW')
 a=np.asarray(array)
 if a.ndim!=2 or not isinstance(x,int) or not isinstance(y,int): raise InputError('CROP_GEOMETRY')
 x0,y0,x1,y1=x-64,y-64,x+65,y+65
 left,right=max(0,min(a.shape[1],x0)),max(0,min(a.shape[1],x1))
 bottom,top=max(0,min(a.shape[0],y0)),max(0,min(a.shape[0],y1))
 return a[bottom:top,left:right].copy(),dict(requested=[x0,y0,x1,y1],obtained=[left,bottom,right,top],
  integer_offset=[left,bottom],offset_in_requested=[left-x0,bottom-y0],padding=False,resampling=False)

def translate_header(header,offset):
 out=header.copy()
 # Unsupported lookup distortions cannot be silently discarded.
 if any(str(k).startswith(('CPDIS','DP1','DP2','D2IM','DET2IM')) for k in out):
  raise InputError('WCS_LOOKUP_LAYOUT_NOT_SUPPORTED')
 for axis,delta in enumerate(offset,1):
  key=f'CRPIX{axis}'
  if key not in out: raise InputError('WCS_CRPIX_MISSING')
  out[key]=out[key]-int(delta)
 # SIP reference pixel is supplied by CRPIX when Astropy reconstructs this header.
 return out

def read_fits(path,hdu):
 try:
  from astropy.io import fits
  import astropy
 except ImportError as e: raise DependencyError('ASTROPY_REQUIRED') from e
 with fits.open(path,memmap=False,do_not_scale_image_data=False,uint=True) as hdus:
  if not isinstance(hdu,int) or not 0<=hdu<len(hdus): raise InputError('HDU_NOT_RESOLVED')
  obj=hdus[hdu]; a=np.array(obj.data,copy=True); header=obj.header.copy()
  if a.ndim!=2: raise InputError('ONLY_LOGICAL_2D_IMAGES_SUPPORTED')
  # Read raw logical scaling/compression cards before data scaling mutates headers.
 with fits.open(path,memmap=False,do_not_scale_image_data=True,uint=False) as hdus:
  raw=hdus[hdu].header.copy()
  compressed=isinstance(hdus[hdu],fits.CompImageHDU)
 with fits.open(path,memmap=False,disable_image_compression=True) as hdus:
  physical=hdus[hdu].header.tostring(sep='\n',endcard=True,padding=False)
 metadata=dict(hdu=hdu,logical_dtype=a.dtype.str,endian=a.dtype.byteorder,shape=list(a.shape),
  bitpix=raw.get('BITPIX'),bscale=raw.get('BSCALE'),bzero=raw.get('BZERO'),blank=raw.get('BLANK'),
  compressed=compressed,raw_header=raw.tostring(sep='\n',endcard=True,padding=False),
  physical_header=physical,decoded_header=header.tostring(sep='\n',endcard=True,padding=False),
  decoder='astropy',decoder_version=astropy.__version__,numpy_version=np.__version__)
 return a,header,metadata

def write_crop_fits(path,a,header,offset):
 from astropy.io import fits
 from io import BytesIO
 from .core import immutable_write
 updated=translate_header(header,offset)
 # Scaling has already been decoded; writing decoded values must not apply it twice.
 for k in ('BSCALE','BZERO','BLANK','CHECKSUM','DATASUM'):
  if k in updated: del updated[k]
 buf=BytesIO(); fits.PrimaryHDU(data=a,header=updated).writeto(buf)
 immutable_write(path,buf.getvalue())
 return updated

def grid_error(headers,shape):
 from astropy.wcs import WCS
 if not headers: raise InputError('MISSING_WCS')
 ref=WCS(headers[0]); worst=0.
 # All pixel centers, processed a row at a time; and footprint corners.
 for h in headers:
  other=WCS(h)
  for y in range(shape[0]):
   xy=np.column_stack((np.arange(shape[1]),np.full(shape[1],y)))
   out=other.all_world2pix(ref.all_pix2world(xy,0),0)
   if not np.isfinite(out).all(): return math.inf
   worst=max(worst,float(np.max(np.abs(out-xy))))
  xy=np.array([[-.5,-.5],[shape[1]-.5,-.5],[-.5,shape[0]-.5],[shape[1]-.5,shape[0]-.5]])
  out=other.all_world2pix(ref.all_pix2world(xy,0),0)
  if not np.isfinite(out).all(): return math.inf
  worst=max(worst,float(np.max(np.abs(out-xy))))
 return worst

def pixel_states(image,ivar,nexp,maskbits,primary,present=None,validity_evidence=None):
 a=np.asarray(image); shape=a.shape
 for b in (ivar,nexp,maskbits,primary):
  if np.shape(b)!=shape: raise InputError('AUXILIARY_SHAPE_CONFLICT')
 if not np.issubdtype(np.asarray(maskbits).dtype,np.integer): raise InputError('MASKBITS_NOT_INTEGER')
 pres=np.ones(shape,dtype=bool) if present is None else np.asarray(present,dtype=bool)
 if pres.shape!=shape: raise InputError('PRESENCE_SHAPE')
 rows=[]
 for index in np.ndindex(shape):
  exists=bool(pres[index]); val=float(a[index]); w=float(ivar[index]); n=nexp[index]; raw=int(maskbits[index])
  if raw<0: raise InputError('NEGATIVE_MASKBITS')
  finite=bool(np.isfinite(val)) if exists else None
  wf=bool(np.isfinite(w)) if exists else None
  zero=bool(val==0) if finite else (False if exists and finite is False else None)
  sign=('positive' if w>0 else 'negative' if w<0 else 'zero') if wf else 'UNKNOWN'
  nvalue=int(n) if exists and np.isfinite(n) and n==int(n) else None
  if exists and np.isfinite(n) and (n!=int(n) or n<0): raise InputError('INVALID_NEXP')
  known=(raw&KNOWN_DR9) if exists else None; unknown=(raw&~KNOWN_DR9) if exists else None
  supported=exists and nvalue is not None and nvalue>0 and wf and w>0
  clean_candidate=supported and finite and raw==0
  evidence=None if validity_evidence is None else validity_evidence[index]
  # Independent explicit evidence is required even for an unflagged zero.
  if not exists: validity='ABSENT'
  elif not finite: validity='NONFINITE_IMAGE'
  elif zero: validity='valid_zero' if evidence=='INDEPENDENT_VALIDITY_VERIFIED' else 'zero_with_unresolved_validity'
  elif evidence=='INDEPENDENT_VALIDITY_VERIFIED': validity='VALID_BY_INDEPENDENT_EVIDENCE'
  elif clean_candidate: validity='supported_unflagged_candidate'
  else: validity='UNKNOWN'
  rows.append(dict(array_present=exists,finite_image=finite,image_zero=zero,weight_finite=wf,
   weight_sign=sign,nexp_value=nvalue,raw_optical_maskbits=raw if exists else None,
   known_flags=known,unknown_bits=unknown,geometric_primary=bool(primary[index]) if exists and primary[index] is not None else None,
   support_evidence='POSITIVE_NEXP_AND_WEIGHT' if supported else 'UNKNOWN',
   quality_evidence='UNKNOWN' if not exists or unknown else 'FLAGS_PRESENT' if raw else 'NO_RECORDED_FLAGS_NOT_CLEAN',
   validity_state=validity))
 return rows

def state_keys(rows,shape):
 return np.array([json.dumps([r[k] for k in STATE_AXES],ensure_ascii=False,separators=(',',':'),allow_nan=False) for r in rows],dtype=object).reshape(shape)

def save_states(path,rows):
 try:
  import pyarrow as pa
  import pyarrow.parquet as pq
 except ImportError as e: raise DependencyError('PYARROW_REQUIRED_NO_FORMAT_FALLBACK') from e
 from io import BytesIO
 from .core import immutable_write
 buf=BytesIO(); pq.write_table(pa.Table.from_pylist(rows),buf,compression='NONE')
 immutable_write(path,buf.getvalue())

def half_width(line,center):
 z=np.asarray(line,dtype=float)
 if not 0<=center<len(z) or not np.isfinite(z).all() or z[center]<=0 or np.argmax(z)!=center:
  return dict(width=None,status='AMBIGUOUS_CENTER')
 half=z[center]/2; crossings=[]
 for side in (-1,1):
  vals=z[center::-1] if side<0 else z[center:]
  hits=[]
  for i in range(len(vals)-1):
   if vals[i]==half and vals[i+1]==half: return dict(width=None,status='AMBIGUOUS_PLATEAU')
   if (vals[i]>=half and vals[i+1]<half) or (vals[i]<half and vals[i+1]>=half):
    hits.append(i+(half-vals[i])/(vals[i+1]-vals[i]))
  if len(hits)!=1: return dict(width=None,status='AMBIGUOUS_CROSSINGS')
  crossings.append(float(hits[0]))
 return dict(width=sum(crossings),status='INTERPRETABLE')

def psf_diagnostics(psf,center,pixel_scale):
 a=np.asarray(psf); out=dict(kind='PROVIDER_PSF_DIAGNOSTICS',input_hash=array_hash(a),input_renormalized=False)
 if a.ndim!=2 or not np.isfinite(a).all() or not pixel_scale or pixel_scale<=0:
  return dict(out,status='NOT_AUDITABLE',reason='NONFINITE_OR_SCALE')
 a=a.astype(np.float64,copy=False)  # Descriptor arithmetic only; original PSF pixels/hash are retained.
 s=float(np.sum(a,dtype=np.float64)); mass=float(np.sum(np.abs(a),dtype=np.float64))
 edge=np.ones(a.shape,dtype=bool)
 if min(a.shape)>4: edge[2:-2,2:-2]=False
 out.update(sum_S=s,min=float(a.min()),max=float(a.max()),negative_count=int((a<0).sum()),
  negative_absolute_mass=float(np.abs(a[a<0]).sum()),absolute_mass=mass,
  edge_absolute_fraction=float(np.abs(a[edge]).sum()/mass) if mass else None)
 if s<=0 or mass==0: return dict(out,status='NOT_AUDITABLE',reason='NONPOSITIVE_SUM')
 yy,xx=np.indices(a.shape); cx=float(np.sum(a*xx)/s); cy=float(np.sum(a*yy)/s)
 m=np.array([[np.sum(a*(xx-cx)**2),np.sum(a*(xx-cx)*(yy-cy))],
  [np.sum(a*(xx-cx)*(yy-cy)),np.sum(a*(yy-cy)**2)]],dtype=np.float64)/s
 positive=bool(np.isfinite(m).all() and np.linalg.eigvalsh(m).min()>0)
 out.update(centroid=[cx,cy],second_moment_matrix=m.tolist(),positive_definite=positive,
  F_mom=float(2*np.sqrt(2*np.log(2))*np.sqrt(np.trace(m)/2)*pixel_scale) if positive else None)
 if center is None or len(center)!=2 or any(not isinstance(v,int) for v in center) or not (0<=center[0]<a.shape[1] and 0<=center[1]<a.shape[0]):
  return dict(out,status='NOT_AUDITABLE',reason='DECLARED_CENTER_MISSING')
 x,y=center; widths=[half_width(a[y,:],x),half_width(a[:,x],y)]
 peak_ok=bool(a[y,x]==a.max() and np.count_nonzero(a==a.max())==1)
 out.update(half_max_x=widths[0],half_max_y=widths[1],declared_center=center,central_unique_peak=peak_ok)
 out['status']='INTERPRETABLE' if positive and peak_ok and all(w['width'] is not None for w in widths) else 'NOT_AUDITABLE'
 return out

def engineering_guards(psfsize,diagnostics,pixel_scale):
 a=np.asarray(psfsize)
 variation=float((a.max()-a.min())/np.median(a)) if a.size and np.isfinite(a).all() and a.min()>0 else None
 fwhm=float(a.min()/pixel_scale) if variation is not None and pixel_scale>0 else None
 edges=[d.get('edge_absolute_fraction') for d in diagnostics]
 passed=variation is not None and variation<=.10 and fwhm>=2 and len(edges)==3 and all(e is not None and e<=.01 for e in edges) and all(d['status']=='INTERPRETABLE' for d in diagnostics)
 return dict(kind='PILOT_ENGINEERING_GUARD',satisfied=bool(passed),variation=variation,min_fwhm_pixels=fwhm,
  edge_fractions=edges,morphology_preservation='NOT_ESTABLISHED',mip_pass=False)


def psfsize_descriptors(a):
 a=np.asarray(a); finite=np.isfinite(a); usable=finite & (a>0); values=a[usable]
 def profile(axis):
  return [[float(v) if np.isfinite(v) else None for v in row] for row in (a if axis=='x' else a.T)]
 return dict(count=int(a.size),finite_count=int(finite.sum()),positive_finite_count=int(usable.sum()),
  missing_descriptor_fraction=float(1-usable.sum()/a.size) if a.size else None,
  min=float(values.min()) if values.size else None,max=float(values.max()) if values.size else None,
  median=float(np.median(values)) if values.size else None,
  q05=float(np.quantile(values,.05,method='linear')) if values.size else None,
  q95=float(np.quantile(values,.95,method='linear')) if values.size else None,
  profiles_x=profile('x'),profiles_y=profile('y'),profiles_kind='EXACT_NATIVE_VALUES_NO_SMOOTHING')

def compare_psfsize(value,diagnostic,pixel_scale):
 widths={'F_mom':diagnostic.get('F_mom')}
 for axis in ('x','y'):
  w=diagnostic.get('half_max_'+axis,{}).get('width')
  widths['half_max_'+axis]=None if w is None else w*pixel_scale
 return dict(psfsize_native=float(value) if np.isfinite(value) else None,
  widths=widths,differences={k:dict(absolute=float(v-value),relative=float((v-value)/value) if value else None)
   for k,v in widths.items() if v is not None and np.isfinite(value)},
  interpretation='DESCRIPTIVE_DIFFERENCE_ONLY_DEFINITIONS_NOT_ASSUMED_EQUAL')


def independent_crop_equal(roi,other):
 # Astropy .section can return native byte order while .data preserves FITS order.
 # Only a reversible byte-order normalization is allowed in this comparison;
 # the scientific crop remains untouched, including its dtype and NaN payload.
 a=np.asarray(roi); b=np.asarray(other)
 if a.shape!=b.shape or a.dtype.newbyteorder('=')!=b.dtype.newbyteorder('='): return False
 if a.dtype!=b.dtype: b=b.byteswap().view(a.dtype)
 return array_hash(a)==array_hash(b)
