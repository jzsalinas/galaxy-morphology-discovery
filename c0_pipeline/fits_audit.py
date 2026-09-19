"""Observational FITS checks; no rendering or preprocessing."""
import warnings
from .core import Stop,sha


def inspect(path,ra,dec):
    import numpy as np
    from astropy.io import fits
    from astropy.wcs import WCS
    from astropy.wcs.utils import proj_plane_pixel_scales
    with fits.open(path,memmap=False) as hdus:
        hdus.verify('exception')
        h=hdus[0].header;data=hdus[0].data
        result=dict(sha256=sha(path),hdu_count=len(hdus),hdus=[dict(index=i,kind=type(x).__name__,shape=list(x.data.shape) if x.data is not None else None,bitpix=x.header.get('BITPIX')) for i,x in enumerate(hdus)],release=h.get('VERSION'),survey=h.get('SURVEY'),bands=h.get('BANDS'),unit=h.get('BUNIT'),unit_status='HEADER_PRESENT_UNCONFIRMED' if h.get('BUNIT') else 'INCONCLUSIVE_MISSING_BUNIT',coverage_status='UNKNOWN_WITHOUT_COVERAGE_PRODUCT',auxiliary_status='NOT_VERIFIED')
        if result['release']!='DR5' or result['survey']!='DECaLS':raise Stop('DR5_RELEASE_NOT_VERIFIABLE')
        if data is None or data.shape!=(3,256,256) or h.get('BANDS')!='grz':raise Stop('DR5_IMAGE_SHAPE_OR_BANDS_INVALID')
        required=['CTYPE1','CTYPE2','CRVAL1','CRVAL2','CRPIX1','CRPIX2']
        if any(k not in h for k in required):raise Stop('FITS_WCS_MISSING')
        with warnings.catch_warnings():
            warnings.simplefilter('error')
            w=WCS(h,naxis=2).celestial
        xy=w.all_world2pix([[ra,dec]],0)[0]
        error=float(np.linalg.norm(xy-np.array([127.5,127.5])))
        if not np.isfinite(error) or error>1:raise Stop('FITS_CENTER_OUTSIDE_TOLERANCE')
        scales=proj_plane_pixel_scales(w)*3600
        if not np.allclose(scales,[0.262,0.262],rtol=0,atol=1e-6):raise Stop('FITS_SCALE_MISMATCH')
        result.update(center_error_pixels=error,pixel_scales_arcsec=scales.tolist(),dtype=str(data.dtype),byteorder=data.dtype.byteorder,
          finite_fraction=[float(np.isfinite(b).mean()) for b in data],
          median=[float(np.nanmedian(b)) for b in data],
          status='REQUIRES_CALIBRATION_AND_COADD_CHECK')
        return result
