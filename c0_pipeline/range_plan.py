"""Exact tile-byte planning for a deliberately limited compressed FITS layout.

No remote reads. Unsupported layouts fail rather than guessing heap offsets.
"""
import math
import re
import numpy as np
from astropy.io import fits
from .ranges import RangeView
from .core import Stop


def plan_section(prefix,total,x0,y0,width,height):
    with fits.open(RangeView(total,[(0,prefix)]),memmap=False,disable_image_compression=True,lazy_load_hdus=True) as hdus:
        hdu=hdus[1];h=hdu.header;loc=hdu.fileinfo()['datLoc']
        if not h.get('ZIMAGE') or h.get('ZNAXIS')!=2 or h.get('ZCMPTYPE') not in ('RICE_ONE','RICE_1'):
            raise Stop('UNSUPPORTED_COMPRESSION_LAYOUT')
        nx,ny=int(h['ZNAXIS1']),int(h['ZNAXIS2'])
        if min(x0,y0)<0 or min(width,height)<=0 or x0+width>nx or y0+height>ny:
            raise Stop('REGION_OUTSIDE_IMAGE')
        tx,ty=int(h['ZTILE1']),int(h['ZTILE2'])
        if min(tx,ty)<=0:raise Stop('INVALID_TILE_SHAPE')
        tiles_x=math.ceil(nx/tx);tiles_y=math.ceil(ny/ty)
        if h['NAXIS2']!=tiles_x*tiles_y:raise Stop('TILE_TABLE_CARDINALITY_MISMATCH')
        size=int(h['NAXIS1'])*int(h['NAXIS2'])
        if loc+size>len(prefix):raise Stop('PREFIX_DOES_NOT_CONTAIN_TILE_TABLE')
        dtype=hdu.columns.dtype.newbyteorder('>')
        if dtype.itemsize!=h['NAXIS1']:raise Stop('TILE_ROW_LAYOUT_MISMATCH')
        table=np.frombuffer(prefix,dtype=dtype,count=h['NAXIS2'],offset=loc)
        heap=loc+int(h.get('THEAP',size))
        if heap<loc+size:raise Stop('INVALID_HEAP_OFFSET')
        ids=[iy*tiles_x+ix for iy in range(y0//ty,(y0+height-1)//ty+1) for ix in range(x0//tx,(x0+width-1)//tx+1)]
        ranges=[];recognized=[]
        for column in hdu.columns:
            if column.name in ('COMPRESSED_DATA','GZIP_COMPRESSED_DATA'):
                if not re.fullmatch(r'1?[PQ]B(?:\(\d+\))?',str(column.format)):raise Stop('UNSUPPORTED_HEAP_DESCRIPTOR')
                recognized.append(column.name)
                for count,offset in table[column.name][ids]:
                    count,offset=int(count),int(offset)
                    if count<0 or offset<0:raise Stop('NEGATIVE_HEAP_DESCRIPTOR')
                    if count:
                        end=heap+offset+count
                        if end>loc+size+int(h['PCOUNT']) or end>total:raise Stop('HEAP_DESCRIPTOR_OUTSIDE_FILE')
                        ranges.append((heap+offset,end-1))
            elif column.name not in ('ZSCALE','ZZERO'):
                raise Stop('UNSUPPORTED_TILE_COLUMN')
        if 'COMPRESSED_DATA' not in recognized or not ranges:raise Stop('NO_COMPRESSED_TILE_BYTES')
        start=min(a for a,b in ranges);end=max(b for a,b in ranges)
        # A contiguous envelope reduces requests. Gaps between selected tiles are
        # explicitly included and counted, not claimed as minimal byte transfer.
        if end-start+1>8*1024**2:raise Stop('TILE_ENVELOPE_EXCEEDS_RANGE_CAP')
        return dict(total=total,start=start,end=end,bytes=end-start+1,unit=h.get('BUNIT'),tile_shape=[ty,tx],selected_tiles=len(ids),x0=x0,y0=y0,width=width,height=height)


def read_section(total,segments,plan):
    with fits.open(RangeView(total,segments),memmap=False,lazy_load_hdus=True) as hdus:
        h=hdus[1]
        region=h.section[plan['y0']:plan['y0']+plan['height'],plan['x0']:plan['x0']+plan['width']]
        return np.array(region,copy=True),h.header.copy()
