"""Identity decisions independent of labels and row ordering."""
from collections import Counter
import math
import uuid

NAMESPACE=uuid.UUID('5c5845d9-51a2-5d61-a39e-477982771c5b')

def normalize_name(value):
    return str(value).strip().upper() if value is not None else ''

def normalized_coordinate(value):
    try:
        x=float(value)
        return format(x,'.15g') if math.isfinite(x) else 'INVALID'
    except (ValueError,TypeError):
        return 'INVALID'

def identities(rows, version, source_sha):
    names=Counter(normalize_name(r['iauname']) for r in rows)
    result=[]
    for row in rows:
        name=normalize_name(row['iauname'])
        if name and names[name]==1:
            gid='GZD5:'+name; method='unique_iauname'
        else:
            key='|'.join((version,source_sha,str(row['source_row']),normalized_coordinate(row['ra_deg']),normalized_coordinate(row['dec_deg'])))
            gid='GZD5:'+str(uuid.uuid5(NAMESPACE,key));method='fallback_uuid5'
        result.append(dict(row,galaxy_id=gid,identity_method=method))
    return result
