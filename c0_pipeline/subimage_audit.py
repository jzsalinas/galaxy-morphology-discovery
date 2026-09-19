"""Audit raw coadd subimage structure, never substitute catalog flags for maps."""
from .core import Stop,sha


def audit(path):
 import numpy as np
 from astropy.io import fits
 from astropy.wcs import WCS
 with fits.open(path,memmap=False) as hdus:
  hdus.verify('exception')
  if hdus[0].header.get('VERSION')!='DR5':raise Stop('SUBIMAGE_RELEASE_UNVERIFIED')
  entries={};products=[]
  for i,hdu in enumerate(hdus[1:],1):
   h=hdu.header
   if h.get('VERSION')!='DR5' or h.get('SURVEY')!='DECaLS':raise Stop('SUBIMAGE_RELEASE_UNVERIFIED')
   kind=h.get('IMAGETYP');band=h.get('BAND');brick=h.get('BRICK')
   if kind not in ('image','invvar') or band not in 'grz' or not brick:raise Stop('SUBIMAGE_SEMANTICS_UNRESOLVED')
   if hdu.data is None or hdu.data.ndim!=2:raise Stop('SUBIMAGE_SHAPE_INVALID')
   if h.get('BRICK_X0') is None or h.get('BRICK_Y0') is None:raise Stop('SUBIMAGE_OFFSETS_MISSING')
   key=(brick,band,kind)
   if key in entries:raise Stop('DUPLICATE_SUBIMAGE_PRODUCT')
   entries[key]=hdu
   w=WCS(h,naxis=2)
   if not w.has_celestial:raise Stop('SUBIMAGE_WCS_MISSING')
   p=dict(hdu=i,brick=brick,band=band,kind=kind,shape=list(hdu.data.shape),brick_x0=h['BRICK_X0'],brick_y0=h['BRICK_Y0'],unit=h.get('BUNIT'),finite_fraction=float(np.isfinite(hdu.data).mean()))
   if kind=='invvar':
    if not np.isfinite(hdu.data).all() or (hdu.data<0).any():raise Stop('INVALID_IVAR_VALUES')
    p['positive_weight_fraction']=float((hdu.data>0).mean())
   products.append(p)
  if {p['band'] for p in products if p['kind']=='image'}!=set('grz'):raise Stop('SUBIMAGE_BANDS_MISSING')
  for (brick,band,kind),im in entries.items():
   if kind!='image':continue
   iv=entries.get((brick,band,'invvar'))
   if iv is None or iv.data.shape!=im.data.shape:raise Stop('SUBIMAGE_IVAR_SHAPE_MISMATCH')
   for k in ['CRPIX1','CRPIX2','CRVAL1','CRVAL2','CD1_1','CD1_2','CD2_1','CD2_2','BRICK_X0','BRICK_Y0']:
    if im.header.get(k)!=iv.header.get(k):raise Stop('SUBIMAGE_IVAR_GRID_MISMATCH')
  return dict(sha256=sha(path),hdu_count=len(hdus),products=products,status='STRUCTURE_VERIFIED_CALIBRATION_PENDING',mask_status='ABSENT_FROM_RESPONSE',nexp_status='ABSENT_FROM_RESPONSE',psf_status='ABSENT_FROM_RESPONSE',unit_status='PENDING_OFFICIAL_COADD_COMPARISON')
