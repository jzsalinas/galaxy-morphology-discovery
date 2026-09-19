"""Deterministic identity-only probe; seed 11, no morphological fields."""
import hashlib
import math
from collections import defaultdict
from .core import Stop,check_probe_fields


def active(value):
    if value is None:return None
    if isinstance(value,bool):return value
    if isinstance(value,(int,float)) and value in (0,1):return bool(value)
    if isinstance(value,str) and value.lower() in ('true','false'):return value.lower()=='true'
    raise Stop('ACTIVE_LEARNING_TYPE_UNRESOLVED')


def select(rows):
    if len(rows)<96:raise Stop('INSUFFICIENT_PROBE_PARENT')
    for row in rows:check_probe_fields(row.keys())
    if len({r['galaxy_id'] for r in rows})!=len(rows):raise Stop('DUPLICATE_PARENT_ID')
    for row in rows:
        if not math.isfinite(float(row['ra_deg'])):raise Stop('INVALID_RA')
        if row.get('petro_radius') is None or not math.isfinite(float(row['petro_radius'])):
            raise Stop('SIZE_STRATUM_UNRESOLVED')
    ranked=sorted(rows,key=lambda r:(r['ra_deg'],r['galaxy_id']))
    ras=defaultdict(list)
    for i,r in enumerate(ranked):ras[min(3,4*i//len(ranked))].append(r)
    cells={}
    for ra,group in sorted(ras.items()):
        ordered=sorted(group,key=lambda r:(r['petro_radius'],r['galaxy_id']))
        for i,r in enumerate(ordered):
            size=min(3,4*i//len(ordered))
            h=hashlib.sha256(('11|'+r['galaxy_id']).encode()).hexdigest()
            cells.setdefault((ra,size),[]).append(dict(r,stratum_ra=ra,stratum_size=size,selection_hash=h,active_learning_stratum=active(r.get('active_learning_on'))))
    if len(cells)!=16 or any(len(v)<6 for v in cells.values()):raise Stop('STRATUM_TOO_SMALL')
    selected={};counts=defaultdict(int)
    def add(r):
        selected[r['galaxy_id']]=r;counts[(r['stratum_ra'],r['stratum_size'])]+=1
    # Two true + two false per cell where available leaves 32 flexible slots.
    for cell,group in sorted(cells.items()):
        group.sort(key=lambda r:(r['selection_hash'],r['galaxy_id']))
        for flag in (True,False):
            for r in [r for r in group if r['active_learning_stratum'] is flag][:2]:add(r)
    pool=sorted((r for group in cells.values() for r in group),key=lambda r:(r['selection_hash'],r['galaxy_id']))
    # Enforce >=24 of each observed state where compatible with cell quotas.
    for flag in (True,False):
        needed=max(0,24-sum(r['active_learning_stratum'] is flag for r in selected.values()))
        for r in pool:
            if not needed:break
            if r['active_learning_stratum'] is flag and r['galaxy_id'] not in selected and counts[(r['stratum_ra'],r['stratum_size'])]<6:
                add(r);needed-=1
        if needed and any(r['active_learning_stratum'] is not None for r in pool):
            raise Stop('ACTIVE_QUOTA_UNRESOLVED_NO_SILENT_RELAXATION')
    for r in pool:
        if r['galaxy_id'] not in selected and counts[(r['stratum_ra'],r['stratum_size'])]<6:add(r)
    result=[]
    for rank,r in enumerate(sorted(selected.values(),key=lambda r:(r['selection_hash'],r['galaxy_id'])),1):
        result.append(dict(galaxy_id=r['galaxy_id'],probe_rank=rank,stratum_ra=r['stratum_ra'],stratum_size=r['stratum_size'],active_learning_stratum=r['active_learning_stratum'],selection_hash=r['selection_hash'],gzd_source_row=r['source_row'],decals_match_status='NOT_EVALUATED',sdss_match_status='NOT_EVALUATED',all_resources_checked=False,exclusion_reason=None))
    if len(result)!=96:raise Stop('PROBE_CARDINALITY_ERROR')
    return result
