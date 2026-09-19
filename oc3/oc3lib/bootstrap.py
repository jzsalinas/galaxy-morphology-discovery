"""Amendment-002 metadata bootstrap. No scientific pixel product is decoded here."""
from __future__ import annotations

import csv
from io import StringIO
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from .core import (AUTHORITIES, BANDS, BOOTSTRAP_MAXIMA, MAXIMA, IntegrityError,
 InputError, LimitError, canonical, digest, file_hash, hash_object, immutable_write,
 implementation_hash, stage_limits, verify_authorities)
from .provider_schema import (TechnicalCandidate, selection_payload, synthetic_candidate_from_legacy,
 validate_provider_manifest_binding)

BOOTSTRAP_SCHEMA_VERSION=2
INITIAL_ROLES=frozenset({'release_checksum_root','release_checksum_north',
 'release_checksum_south','brick_geometry','north_coverage','south_coverage',
 'corrected_9012'})
DEPENDENT_KINDS=frozenset({'brick_index','coadd_head'})
FORBIDDEN_PRODUCTS=frozenset({'psf','tractor','model','blobmodel','depth','galdepth',
 'chi2','jpeg','individual_exposure','galaxy_zoo'})
SCIENCE_MAPS=frozenset({'image','invvar','nexp','maskbits','psfsize'})

TOP_FIELDS={'schema_version','execution_kind','authorities','implementation_sha256',
 'environment','family','selection_policy','development_policy','literal_resources',
 'dependent_roles','approved_hosts','stage_limits','global_limits','rights',
 'semantics','release_issues','human_authorization','provider_schema','sealed'}
ENV_FIELDS={'verified','fingerprint','installation_report_sha256','preparation_receipt_sha256',
 'replay_receipt_sha256','python','packages','zero_real_network','synthetic'}
FAMILY_FIELDS={'release','regions','bands'}
POLICY_FIELDS={'algorithm','south_corrected_release','north_release','no_replacement'}
DEVELOPMENT_FIELDS={'label','permanent','holdout_disjoint_by_policy','evidence_ref'}
RIGHTS_FIELDS={'scientific_local_analysis','local_preservation','public_access',
 'redistribution','evidence_refs'}
AUTH_FIELDS={'authorized','scope','evidence_ref','record_sha256'}
LITERAL_FIELDS={'id','url','method','role','host','release','generation','max_bytes',
 'size','sha256','checksum_ref','evidence_ref','decoder','projection'}
DEPENDENT_FIELDS={'id','kind','method','host','resource_type','region','product','band',
 'generation_rule','max_bytes','evidence_ref','supporting_evidence_sha256',
 'resolver','url_template','future_max_bytes','hdu'}
CANDIDATE_FIELDS={'region','brickname','survey','release','generation','grz',
 'corrected_9012','primary_bounds','evidence_refs'}
LINK_FIELDS={'role_id','region','brick','product','band','url','release','generation','method'}

def _exact(obj,fields,required=None,reason='BOOTSTRAP_SCHEMA'):
 if not isinstance(obj,dict) or set(obj)-set(fields) or set(required or fields)-set(obj):
  raise InputError(reason)
 return obj

def _pairs(pairs):
 out={}
 for key,value in pairs:
  if key in out: raise InputError('DUPLICATE_JSON_KEY')
  out[key]=value
 return out

def _nonfinite(value): raise InputError('NONFINITE_JSON_VALUE')

def seal_object(obj):
 body={k:v for k,v in obj.items() if k!='sealed'}
 return dict(body,sealed=hash_object(body))

def sealed_file_bytes(obj):
 sealed=seal_object(obj)
 return canonical(sealed)+b'\n'

def sealed_file_sha256(obj): return digest(sealed_file_bytes(obj))

def load_canonical_sealed(path):
 p=Path(path); raw=p.read_bytes()
 try: obj=json.loads(raw,object_pairs_hook=_pairs,parse_constant=_nonfinite)
 except (UnicodeDecodeError,ValueError) as exc: raise InputError('INVALID_BOOTSTRAP_JSON') from exc
 try: expected=canonical(obj)+b'\n'
 except (TypeError,ValueError) as exc: raise InputError('INVALID_BOOTSTRAP_JSON') from exc
 if raw!=expected: raise IntegrityError('NONCANONICAL_SEALED_FILE')
 if obj.get('sealed')!=hash_object({k:v for k,v in obj.items() if k!='sealed'}):
  raise IntegrityError('BOOTSTRAP_SEAL_MISMATCH')
 return obj,digest(raw)

def role_hash(role): return hash_object(role)

def _hex(value): return isinstance(value,str) and bool(re.fullmatch(r'[0-9a-f]{64}',value))

def _validate_caps(values,maximum,reason):
 if not isinstance(values,dict) or set(values)!=set(maximum): raise InputError(reason)
 for key,ceiling in maximum.items():
  value=values[key]
  if isinstance(value,bool) or not isinstance(value,(int,float)) or not 0<value<=ceiling:
   raise LimitError(reason)

def validate_literal_resource(resource,hosts,execution_kind='SYNTHETIC'):
 _exact(resource,LITERAL_FIELDS,LITERAL_FIELDS-{'size','sha256','checksum_ref','projection'})
 if resource['role'] not in INITIAL_ROLES: raise InputError('BOOTSTRAP_ROLE_NOT_ALLOWED')
 if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',resource['id']): raise InputError('BOOTSTRAP_RESOURCE_ID')
 if resource['method']!='GET': raise InputError('BOOTSTRAP_METHOD_NOT_ALLOWED')
 if resource.get('decoder') not in ('OPAQUE_V1','TEXT_CHECKSUM_V1','JSON_ROWS_V1','FITS_BINTABLE_ROWS_V1','PROVIDER_FITS_ADAPTER_V1'):
  raise InputError('BOOTSTRAP_DECODER')
 if resource['decoder'] in ('JSON_ROWS_V1','FITS_BINTABLE_ROWS_V1') and not isinstance(resource.get('projection'),dict):
  raise InputError('BOOTSTRAP_PROJECTION_REQUIRED')
 if resource['decoder']=='PROVIDER_FITS_ADAPTER_V1' and resource.get('projection') is not None:
  raise InputError('PROVIDER_FREEFORM_PROJECTION_FORBIDDEN')
 if execution_kind=='PRODUCTION' and resource['decoder'] in ('JSON_ROWS_V1','FITS_BINTABLE_ROWS_V1'):
  raise InputError('LEGACY_PROVIDER_PROJECTION_FORBIDDEN')
 if resource.get('projection') and set(resource['projection'])-CANDIDATE_FIELDS:
  raise InputError('BOOTSTRAP_PROJECTION_FIELD')
 _validate_url(resource['url'],resource['host'],hosts)
 if resource['release']!='DR9' or not isinstance(resource['max_bytes'],int) or resource['max_bytes']<=0:
  raise InputError('BOOTSTRAP_RESOURCE_SCOPE')
 if resource.get('size') is not None and not 0<resource['size']<=resource['max_bytes']:
  raise LimitError('BOOTSTRAP_RESOURCE_SIZE')
 if resource.get('sha256') is not None and not _hex(resource['sha256']): raise InputError('BOOTSTRAP_SHA')
 if not resource.get('sha256') and not resource.get('checksum_ref'): raise InputError('BOOTSTRAP_CHECKSUM_REFERENCE_REQUIRED')
 if not isinstance(resource['generation'],str) or not resource['generation']: raise InputError('BOOTSTRAP_GENERATION_SCOPE')
 if not isinstance(resource['generation'],str) or not resource['generation']: raise InputError('BOOTSTRAP_GENERATION_SCOPE')
 if not resource['evidence_ref']: raise InputError('BOOTSTRAP_URL_EVIDENCE')
 return resource

def validate_dependent_role(role,hosts):
 _exact(role,DEPENDENT_FIELDS,DEPENDENT_FIELDS-{'band','future_max_bytes','hdu'})
 if role['kind'] not in DEPENDENT_KINDS or role['resolver'] not in ('CLOSED_TEMPLATE_V1','EXACT_LINK_MAP_V1'):
  raise InputError('DEPENDENT_ROLE_TYPE')
 if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',role['id']): raise InputError('DEPENDENT_ROLE_ID')
 if role['method'] not in ('GET','HEAD'): raise InputError('DEPENDENT_METHOD')
 if role['kind']=='brick_index' and role['method']!='GET': raise InputError('BRICK_INDEX_METHOD')
 if role['kind']=='coadd_head' and role['method']!='HEAD': raise InputError('COADD_HEAD_METHOD')
 if role['resource_type'] in FORBIDDEN_PRODUCTS or role['product'] in FORBIDDEN_PRODUCTS:
  raise InputError('DEPENDENT_PRODUCT_FORBIDDEN')
 if role['kind']=='brick_index' and role['resource_type']!='technical_index': raise InputError('BRICK_INDEX_TYPE')
 if role['kind']=='coadd_head' and role['product'] not in SCIENCE_MAPS: raise InputError('HEAD_PRODUCT_SCOPE')
 if role['kind']=='coadd_head' and role['resource_type']!='science_map_header': raise InputError('HEAD_RESOURCE_TYPE')
 if role['kind']=='coadd_head' and (not isinstance(role.get('future_max_bytes'),int) or role['future_max_bytes']<=0 or not isinstance(role.get('hdu'),int)):
  raise InputError('HEAD_FUTURE_RESOURCE_SCOPE')
 if role['region'] not in ('north','south') or role.get('band') not in (None,*BANDS): raise InputError('DEPENDENT_REGION_BAND')
 if role['generation_rule']!='SELECTED_BRICK': raise InputError('DEPENDENT_GENERATION_RULE')
 if role['host'] not in hosts or not role['evidence_ref'] or not _hex(role['supporting_evidence_sha256']):
  raise InputError('DEPENDENT_EVIDENCE')
 if not isinstance(role['max_bytes'],int) or role['max_bytes']<=0: raise LimitError('DEPENDENT_BODY_CAP')
 template=role['url_template']
 if not isinstance(template,str) or any(key not in ('brick','prefix','region','product','band') for key in re.findall(r'{([^}]+)}',template)):
  raise InputError('DEPENDENT_TEMPLATE')
 # Validate the non-placeholder origin without permitting scheme/host changes.
 probe=template.format(brick='B',prefix='B',region=role['region'],product=role['product'],band=role.get('band') or 'none')
 _validate_url(probe,role['host'],hosts)
 return role

def _validate_url(url,host,hosts):
 parsed=urlsplit(url)
 if parsed.scheme!='https' or parsed.hostname!=host or host not in hosts or parsed.username or parsed.password or parsed.fragment or parsed.port not in (None,443):
  raise InputError('BOOTSTRAP_URL_NOT_APPROVED')

def validate_bootstrap_manifest(obj,project,for_network=False):
 _exact(obj,TOP_FIELDS,TOP_FIELDS-{'provider_schema'})
 if obj['schema_version']!=BOOTSTRAP_SCHEMA_VERSION or obj['execution_kind'] not in ('PRODUCTION','SYNTHETIC'):
  raise InputError('BOOTSTRAP_VERSION_KIND')
 if obj['sealed']!=hash_object({k:v for k,v in obj.items() if k!='sealed'}): raise IntegrityError('BOOTSTRAP_SEAL_MISMATCH')
 authorities=verify_authorities(project)
 if obj['authorities']!=authorities: raise IntegrityError('BOOTSTRAP_AUTHORITY_BINDING')
 if obj['implementation_sha256']!=implementation_hash(project): raise IntegrityError('BOOTSTRAP_IMPLEMENTATION_BINDING')
 _exact(obj['environment'],ENV_FIELDS)
 _exact(obj['family'],FAMILY_FIELDS)
 if obj['family']!={'release':'DR9','regions':['north','south'],'bands':['g','r','z']}:
  raise InputError('BOOTSTRAP_FAMILY')
 _exact(obj['selection_policy'],POLICY_FIELDS)
 expected_policy={'algorithm':'SHA256_OC3_V1_BRICK','south_corrected_release':'9012',
  'north_release':'DR9','no_replacement':True}
 if obj['selection_policy']!=expected_policy: raise InputError('BOOTSTRAP_SELECTION_POLICY')
 _exact(obj['development_policy'],DEVELOPMENT_FIELDS)
 if obj['development_policy']['label']!='INSTRUMENTAL_DEVELOPMENT' or obj['development_policy']['permanent'] is not True or obj['development_policy']['holdout_disjoint_by_policy'] is not True:
  raise InputError('BOOTSTRAP_DEVELOPMENT_POLICY')
 _exact(obj['rights'],RIGHTS_FIELDS)
 if obj['rights']['redistribution'] is not False: raise InputError('REDISTRIBUTION_MUST_BE_FALSE')
 from .core import strict
 for row in obj['semantics']: strict(row,'semantic',('product','property','status','evidence_refs'))
 for row in obj['release_issues']: strict(row,'issue',('issue','status','evidence_refs'))
 _exact(obj['human_authorization'],AUTH_FIELDS)
 if not isinstance(obj['approved_hosts'],list) or not obj['approved_hosts'] or not all(isinstance(h,str) and h for h in obj['approved_hosts']) or len(set(obj['approved_hosts']))!=len(obj['approved_hosts']):
  raise InputError('BOOTSTRAP_HOSTS')
 _validate_caps(obj['global_limits'],MAXIMA,'BOOTSTRAP_GLOBAL_LIMITS')
 _validate_caps(obj['stage_limits'],BOOTSTRAP_MAXIMA,'BOOTSTRAP_STAGE_LIMITS')
 ids=set()
 for resource in obj['literal_resources']:
  validate_literal_resource(resource,obj['approved_hosts'],obj['execution_kind'])
  if resource['id'] in ids: raise InputError('BOOTSTRAP_DUPLICATE_ID')
  ids.add(resource['id'])
 for role in obj['dependent_roles']:
  validate_dependent_role(role,obj['approved_hosts'])
  if role['id'] in ids: raise InputError('BOOTSTRAP_DUPLICATE_ID')
  ids.add(role['id'])
 role_counts={name:sum(r['role']==name for r in obj['literal_resources']) for name in INITIAL_ROLES}
 if any(role_counts[name]>1 for name in INITIAL_ROLES-{'release_checksum_root','release_checksum_north','release_checksum_south'}):
  raise InputError('BOOTSTRAP_ROLE_CARDINALITY')
 scientific_scope=canonical({'literal_resources':obj['literal_resources'],'dependent_roles':obj['dependent_roles']}).decode('utf-8').lower()
 forbidden=('galaxy zoo','galaxy_zoo','zoobot','morphology','source catalog','vote_fraction','redshift','stellar_mass','/tractor','tractor-','physical validation')
 if any(token in scientific_scope for token in forbidden): raise InputError('BOOTSTRAP_SCIENTIFIC_CONTENT_FORBIDDEN')
 if obj.get('provider_schema') is not None:
  validate_provider_manifest_binding(obj['provider_schema'],production=obj['execution_kind']=='PRODUCTION')
 elif obj['execution_kind']=='PRODUCTION':
  raise InputError('PROVIDER_SCHEMA_BINDING_REQUIRED')
 if for_network:
  if obj['execution_kind']!='PRODUCTION': raise InputError('SYNTHETIC_REAL_NETWORK_FORBIDDEN')
  env=obj['environment']; rights=obj['rights']; auth=obj['human_authorization']
  if not (env['verified'] is True and env['zero_real_network'] is True and _hex(env['fingerprint']) and _hex(env['installation_report_sha256']) and _hex(env['preparation_receipt_sha256']) and _hex(env['replay_receipt_sha256'])):
   raise InputError('INDEPENDENT_ENVIRONMENT_REQUIRED')
  if not isinstance(env['python'],str) or not env['python'].startswith('3.12.') or env['packages']!={'numpy':'2.5.3','astropy':'8.0.1','pyarrow':'25.0.1'}:
   raise InputError('INDEPENDENT_ENVIRONMENT_VERSION_MISMATCH')
  if not (rights['scientific_local_analysis'] is True and rights['local_preservation'] is True and rights['public_access'] is True and rights['evidence_refs']):
   raise InputError('BOOTSTRAP_RIGHTS_REQUIRED')
  if not (auth['authorized'] is True and auth['scope']=='METADATA_BOOTSTRAP_ONLY' and auth['evidence_ref'] and _hex(auth['record_sha256'])):
   raise InputError('BOOTSTRAP_HUMAN_AUTHORIZATION_REQUIRED')
 return obj

def load_bootstrap_manifest(path,project,for_network=False):
 obj,file_sha=load_canonical_sealed(path)
 validate_bootstrap_manifest(obj,project,for_network)
 return obj,file_sha

def bootstrap_parent_binding(obj,file_sha):
 return {'kind':'OC3_METADATA_BOOTSTRAP_PARENT','manifest_seal':obj['sealed'],
  'manifest_sha256':file_sha,'authorities':obj['authorities'],
  'implementation_sha256':obj['implementation_sha256'],'environment':obj['environment'],
  'rights':obj['rights'],'execution_kind':obj['execution_kind'],
  'global_limits':obj['global_limits'],'stage_limits':obj['stage_limits']}

def bootstrap_firewall(resource,manifest):
 method=resource.get('method')
 if method not in ('GET','HEAD'): raise InputError('BOOTSTRAP_METHOD_NOT_ALLOWED')
 if resource.get('host') not in manifest['approved_hosts']: raise InputError('BOOTSTRAP_HOST_NOT_ALLOWED')
 _validate_url(resource['url'],resource['host'],manifest['approved_hosts'])
 product=str(resource.get('product') or resource.get('resource_type') or '').lower()
 if product in FORBIDDEN_PRODUCTS or product=='psf': raise InputError('BOOTSTRAP_PRODUCT_FORBIDDEN')
 if method=='GET' and product in SCIENCE_MAPS: raise InputError('BOOTSTRAP_MAP_GET_FORBIDDEN')
 if method=='HEAD' and product not in SCIENCE_MAPS: raise InputError('BOOTSTRAP_HEAD_SCOPE')
 if resource.get('range') is not None: raise InputError('BOOTSTRAP_RANGE_FORBIDDEN')
 if resource.get('recursive') or resource.get('crawl'): raise InputError('BOOTSTRAP_CRAWL_FORBIDDEN')
 if resource.get('materialized') is False: raise InputError('DEPENDENT_IDENTITY_NOT_MATERIALIZED')
 return resource

def _ascii(value):
 try: value.encode('ascii')
 except UnicodeEncodeError as exc: raise InputError('BRICKNAME_NOT_ASCII') from exc
 return value

def brick_order(region,name):
 _ascii(name)
 return (digest(f'OC3-v1|brick|{region}|{name}'.encode('utf-8')),name)

def resolve_bootstrap_bricks(rows,*,synthetic_legacy=False):
 clean=[]
 for value in rows:
  if isinstance(value,TechnicalCandidate): candidate=value
  elif synthetic_legacy: candidate=synthetic_candidate_from_legacy(value)
  else: raise InputError('RAW_PROVIDER_TABLE_FORBIDDEN')
  row=selection_payload(candidate)
  if row['region'] not in ('north','south') or row['release_family']!='DR9' or row['grz'] is not True:
   continue
  if row['region']=='south' and not (row['survey']=='DECaLS' and row['generation']=='9012' and row['corrected_9012'] is True):
   continue
  if row['region']=='north' and not (row['survey']=='BASS_MzLS' and row['generation']=='9011' and row['corrected_9012'] is False): continue
  _ascii(row['brickname']); clean.append(row)
 selected=[]
 for region in ('south','north'):
  candidates=[r for r in clean if r['region']==region]
  if not candidates: raise InputError('BOOTSTRAP_ELIGIBLE_BRICK_MISSING')
  selected.append(dict(min(candidates,key=lambda r:brick_order(region,r['brickname']))))
 selection={'algorithm':'SHA256_OC3_V1_BRICK','bricks':selected,
  'status':'INSTRUMENTAL_DEVELOPMENT','no_replacement':True}
 selection['selection_sha256']=hash_object(selection)
 return selection

def development_csv(selection,evidence_ref):
 rows=[]
 by_region={row['region']:row for row in selection['bricks']}
 if set(by_region)!= {'south','north'}: raise InputError('DEVELOPMENT_BRICKS')
 for region in ('south','north'):
  rows.append({'region':region,'brickname':by_region[region]['brickname'],'development':'true',
   'holdout_disjoint':'true','evidence_ref':evidence_ref})
 out=StringIO(newline=''); writer=csv.DictWriter(out,fieldnames=['region','brickname','development','holdout_disjoint','evidence_ref'],lineterminator='\n')
 writer.writeheader(); writer.writerows(rows)
 return out.getvalue().encode('utf-8')

def materialize_role(role,selection,evidence_bytes,link=None):
 validate_dependent_role(role,[role['host']])
 chosen={row['region']:row for row in selection['bricks']}
 brick=chosen.get(role['region'])
 if not brick: raise InputError('ROLE_REGION_NOT_SELECTED')
 evidence_sha=digest(evidence_bytes)
 if evidence_sha!=role['supporting_evidence_sha256']: raise IntegrityError('ROLE_EVIDENCE_HASH')
 band=role.get('band')
 if role['resolver']=='CLOSED_TEMPLATE_V1':
  url=role['url_template'].format(brick=brick['brickname'],prefix=brick['brickname'][:3],region=role['region'],product=role['product'],band=band or 'none')
  method=role['method']; generation=brick['generation']
 else:
  try: document=json.loads(evidence_bytes,object_pairs_hook=_pairs)
  except (UnicodeDecodeError,ValueError) as exc: raise InputError('LINK_EVIDENCE_JSON') from exc
  if set(document)!= {'links'} or not isinstance(document['links'],list): raise InputError('LINK_EVIDENCE_SCHEMA')
  matches=[]
  for item in document['links']:
   _exact(item,LINK_FIELDS)
   if (item['role_id'],item['region'],item['brick'],item['product'],item.get('band'))==(role['id'],role['region'],brick['brickname'],role['product'],band): matches.append(item)
  if len(matches)!=1: raise InputError('DEPENDENT_LINK_NOT_UNIQUE')
  item=matches[0]; url=item['url']; method=item['method']; generation=item['generation']
  if item['release']!='DR9': raise IntegrityError('DEPENDENT_RELEASE')
 if method!=role['method']: raise IntegrityError('DEPENDENT_METHOD_CHANGED')
 _validate_url(url,role['host'],[role['host']])
 if role['generation_rule']=='SELECTED_BRICK' and generation!=brick['generation']:
  raise IntegrityError('DEPENDENT_GENERATION_CHANGED')
 record={'role_id':role['id'],'parent_role_sha256':role_hash(role),
  'supporting_evidence_sha256':evidence_sha,'selection_sha256':selection['selection_sha256'],
  'url':url,'method':method,'host':role['host'],'release':'DR9','generation':generation,
  'resource_type':role['resource_type'],'product':role['product'],'band':band,
  'region':role['region'],'brick':brick['brickname'],'max_bytes':role['max_bytes'],
  'materialized':True}
 record['resolution_sha256']=hash_object(record)
 return bootstrap_firewall(record,{'approved_hosts':[role['host']]})

def final_manifest(parent,metadata_receipt,selection,allowlist_path,allowlist_sha256,
 resources,rights,semantics,release_issues,approved_hosts,deferred_psf=True):
 bricks=[]
 for row in selection['bricks']:
  bricks.append({'region':row['region'],'brickname':row['brickname'],'brickid':row['brickid'],
   'release':row['release_family'],'generation':row['generation'],'grz':row['grz'],
   'corrected_9012':row['corrected_9012'],
   'primary_bounds':[row['primary_bounds'][k] for k in ('ra1','ra2','dec1','dec2')],
   'evidence_refs':row['evidence_refs']})
  manifest={'schema_version':2,'execution_kind':parent['execution_kind'],'allowlist_path':str(Path(allowlist_path).resolve()),
  'allowlist_sha256':allowlist_sha256,'bricks':bricks,'resources':resources,'rights':rights,
  'semantics':semantics,'release_issues':release_issues,'approved_hosts':approved_hosts,
  'deferred_psf':deferred_psf,'bootstrap':{'parent_manifest_sha256':parent['manifest_sha256'],
   'parent_manifest_seal':parent['manifest_seal'],'metadata_receipt_sha256':hash_object(metadata_receipt),
   'selection_sha256':selection['selection_sha256'],'ledger_identity':metadata_receipt['ledger_identity'],
   'development_csv_sha256':allowlist_sha256,'watermark':metadata_receipt['watermark']}}
 return seal_object(manifest)

def promotion_child(parent,metadata_receipt,selection,csv_bytes,manifest_obj,resources,ledger_summary):
 remaining={k:ledger_summary['limits'][k]-ledger_summary['counters'].get(k,0) for k in ledger_summary['limits'] if k in ledger_summary['counters']}
 return {'kind':'OC3_PROMOTED_CHILD','parent_manifest_sha256':parent['manifest_sha256'],
  'parent_manifest_seal':parent['manifest_seal'],'metadata_receipt_sha256':hash_object(metadata_receipt),
  'ledger_identity':ledger_summary['ledger_identity'],'global_counters':ledger_summary['counters'],
  'stage_counters':next((s['counters'] for s in ledger_summary['stages'] if s['id']=='METADATA_BOOTSTRAP'),{}),
  'watermark':ledger_summary['watermark'],'selected_bricks':manifest_obj['bricks'],
  'selection_sha256':selection['selection_sha256'],'development_record_sha256':hash_object({'selection':selection,'permanent':True}),
  'development_csv_sha256':digest(csv_bytes),'final_manifest_seal':manifest_obj['sealed'],
  'final_manifest_sha256':digest(canonical(manifest_obj)+b'\n'),
  'future_resource_identities':[hash_object(r) for r in resources],
  'remaining_global':remaining,'authorities':parent['authorities'],
  'implementation_sha256':parent['implementation_sha256'],'environment':parent['environment'],
  'rights':parent['rights']}

def promote(ledger,parent,metadata_receipt,selection,csv_path,csv_bytes,manifest_path,manifest_obj,resources,*,crash=None,resume=False):
 development={'selection':selection,'permanent':True,'policy':'INSTRUMENTAL_DEVELOPMENT'}
 ledger.record_development(development)
 manifest_bytes=canonical(manifest_obj)+b'\n'
 ledger.charge('io_bytes',len(csv_bytes)+len(manifest_bytes))
 summary=ledger.summary()
 child=promotion_child(parent,metadata_receipt,selection,csv_bytes,manifest_obj,resources,summary)
 ledger.prepare_child(child)
 immutable_write(csv_path,csv_bytes); immutable_write(manifest_path,manifest_bytes)
 if crash=='before': raise OSError('SYNTHETIC_PRE_COMMIT_CRASH')
 ledger.commit_child(child,resume=resume,crash_after=crash=='after')
 return child

def metadata_receipt(ledger,resources,selection=None):
 summary=ledger.summary()
 return {'ledger_identity':summary['ledger_identity'],'watermark':summary['watermark'],
  'global_counters':summary['counters'],'stages':summary['stages'],
  'resources':resources,'selection_sha256':selection['selection_sha256'] if selection else None}

def final_resource_from_head(role,resolution,observed_size=None):
 if role['kind']!='coadd_head' or resolution['method']!='HEAD': raise InputError('NOT_A_COADD_HEAD')
 stage='aux' if role['product'] in ('nexp','maskbits','psfsize') else 'fixed'
 value={'url':resolution['url'],'category':'product','product':role['product'],'stage':stage,
  'region':resolution['region'],'brick':resolution['brick'],'band':role.get('band'),
  'generation':resolution['generation'],'release':'DR9','max_bytes':role['future_max_bytes'],
  'hdu':role['hdu'],'evidence_refs':[resolution['resolution_sha256']]}
 if observed_size is not None:
  if not 0<observed_size<=value['max_bytes']: raise LimitError('FUTURE_RESOURCE_SIZE')
  value['size']=observed_size
 from .transport import resource_identity
 value['id']=resource_identity(value)
 return value

def transport_resource(record,role=None):
 """Translate one already-enumerated metadata identity to the generic transport contract."""
 product=record.get('product') or record.get('role') or record.get('resource_type')
 value={'id':record['id'],'url':record['url'],'category':'metadata','product':product,
  'stage':'metadata','release':record['release'],'generation':record['generation'],
  'max_bytes':record['max_bytes'],'method':record['method']}
 for key in ('size','sha256','region','brick','band'):
  if record.get(key) is not None: value[key]=record[key]
 if role is not None:
  value['id']='metadata-'+record['resolution_sha256']; value['materialized']=True
 return value

def _plain(value):
 if hasattr(value,'item'):
  try: value=value.item()
  except ValueError: pass
 if isinstance(value,bytes): value=value.decode('ascii')
 if hasattr(value,'tolist'): value=value.tolist()
 return value

def decode_candidate_rows(path,resource,*,synthetic_legacy=False):
 decoder=resource['decoder']; projection=resource.get('projection') or {}
 if decoder in ('OPAQUE_V1','TEXT_CHECKSUM_V1'): return []
 if decoder=='PROVIDER_FITS_ADAPTER_V1':
  raise InputError('PRODUCTION_PROVIDER_PHYSICAL_CONTRACT_UNAVAILABLE')
 if not synthetic_legacy:
  raise InputError('LEGACY_PROVIDER_PROJECTION_FORBIDDEN')
 if decoder=='JSON_ROWS_V1':
  try: value=json.loads(Path(path).read_bytes(),object_pairs_hook=_pairs)
  except (UnicodeDecodeError,ValueError) as exc: raise InputError('BOOTSTRAP_METADATA_DECODE') from exc
  rows=value['rows'] if isinstance(value,dict) and set(value)=={'rows'} else value
 elif decoder=='FITS_BINTABLE_ROWS_V1':
  try:
   from astropy.table import Table
   rows=Table.read(path).as_array()
  except Exception as exc: raise InputError('BOOTSTRAP_METADATA_DECODE') from exc
 else: raise InputError('BOOTSTRAP_DECODER')
 if not hasattr(rows,'__iter__'): raise InputError('BOOTSTRAP_ROWS_SCHEMA')
 out=[]
 for row in rows:
  item={}
  for target,source in projection.items():
   try: item[target]=_plain(row[source])
   except (KeyError,ValueError,TypeError,IndexError) as exc: raise InputError('BOOTSTRAP_PROJECTION_MISSING') from exc
  out.append(item)
 return out

def merge_candidate_rows(groups):
 merged={}
 for rows in groups:
  for row in rows:
   if 'region' not in row or 'brickname' not in row: raise InputError('BOOTSTRAP_CANDIDATE_KEY_MISSING')
   key=(row['region'],row['brickname']); target=merged.setdefault(key,{})
   for field,value in row.items():
    if field in target and target[field]!=value: raise IntegrityError('BOOTSTRAP_METADATA_CONFLICT')
    target[field]=value
 out=[]
 for key in sorted(merged):
  row=merged[key]
  if set(row)!=CANDIDATE_FIELDS: raise InputError('BOOTSTRAP_CANDIDATE_INCOMPLETE')
  if not isinstance(row['evidence_refs'],list) or not row['evidence_refs']: raise InputError('BOOTSTRAP_CANDIDATE_EVIDENCE')
  scope=canonical(row).decode('utf-8').lower()
  if any(token in scope for token in ('galaxy zoo','galaxy_zoo','zoobot','morphology','vote_fraction','redshift','stellar_mass')):
   raise InputError('BOOTSTRAP_SCIENTIFIC_CONTENT_FORBIDDEN')
  out.append(row)
 return out

class BootstrapRun:
 """One-ledger metadata bootstrap; unit tests may inject only local fake transports."""
 def __init__(self,project,root,manifest_path,*,network_capable=False,global_overrides=None,stage_overrides=None,resume=False):
  from .core import Ledger, RuntimeGuard
  self.project=Path(project); self.root=Path(root); self.manifest_path=Path(manifest_path)
  self.manifest,self.file_sha=load_bootstrap_manifest(manifest_path,project,for_network=network_capable)
  if self.manifest['execution_kind']=='SYNTHETIC' and self.root.resolve()==(self.project/'oc3').resolve():
   raise InputError('SYNTHETIC_EVIDENCE_IN_PRODUCTION')
  self.parent=bootstrap_parent_binding(self.manifest,self.file_sha)
  global_caps=dict(self.manifest['global_limits'])
  for k,v in (global_overrides or {}).items(): global_caps[k]=min(global_caps[k],v)
  stage_caps=dict(self.manifest['stage_limits'])
  for k,v in (stage_overrides or {}).items(): stage_caps[k]=min(stage_caps[k],v)
  self.execution_id=hash_object(self.parent)
  self.ledger=Ledger(self.root/'provenance/OC3_RESOURCE_LEDGER.sqlite',self.parent,
   global_caps,stage='METADATA_BOOTSTRAP',stage_caps=stage_caps,execution_id=self.execution_id)
  self.ledger.record_parent(self.parent)
  if resume: self.ledger.recover()
  self.guard=RuntimeGuard(self.ledger,self.root)
 def close(self): self.ledger.close()
 def _cached_bytes(self,sha):
  row=self.ledger.db.execute("SELECT path FROM resources WHERE state='COMPLETE' AND sha=?",(sha,)).fetchone()
  if not row or not row[0]: raise InputError('SUPPORTING_EVIDENCE_NOT_CACHED')
  path=self.root/row[0]; self.ledger.charge('io_bytes',path.stat().st_size)
  if file_hash(path)!=sha: raise IntegrityError('SUPPORTING_EVIDENCE_CORRUPT')
  return path.read_bytes()
 def execute(self,network,*,resume=False,crash=None):
  from .transport import Acquisition
  existing=self.ledger.child()
  if existing:
   if not resume: raise IntegrityError('SECOND_PROMOTION_FORBIDDEN')
   for path,key in ((self.root/'INPUTS/OC3_INPUT_MANIFEST.json','final_manifest_sha256'),
                    (self.root/'INPUTS/OC3_DEVELOPMENT_BRICKS.csv','development_csv_sha256')):
    if not path.is_file() or file_hash(path)!=existing[key]: raise IntegrityError('PROMOTED_CHILD_FILES_MISSING')
   return existing
  prepared=self.ledger.db.execute("SELECT value FROM bindings WHERE kind='prepared_child'").fetchone()
  if prepared:
   if not resume: raise IntegrityError('PROMOTION_ALREADY_PREPARED')
   child=json.loads(prepared[0])
   for path,key in ((self.root/'INPUTS/OC3_INPUT_MANIFEST.json','final_manifest_sha256'),
                    (self.root/'INPUTS/OC3_DEVELOPMENT_BRICKS.csv','development_csv_sha256')):
    if not path.is_file() or file_hash(path)!=child[key]: raise IntegrityError('PREPARED_CHILD_FILES_MISSING')
   self.ledger.commit_child(child,resume=True,crash_after=crash=='after')
   return child
  acquire=Acquisition(self.root,self.ledger,network,self.guard); decoded=[]; receipt_resources=[]
  for literal in self.manifest['literal_resources']:
   transport=transport_resource(literal); transport['host']=literal['host']
   bootstrap_firewall(transport,self.manifest)
   path=acquire.fetch(transport,resume=resume)
   state=self.ledger.resource(transport['id'])
   receipt_resources.append({'kind':'literal','id':literal['id'],'role':literal['role'],
    'url':literal['url'],'method':literal['method'],'state':state['state'],
    'body_bytes':state['offset'],'sha256':state['sha']})
   if path is not None:
    self.ledger.charge('io_bytes',path.stat().st_size)
    decoded.append(decode_candidate_rows(path,literal,synthetic_legacy=self.manifest['execution_kind']=='SYNTHETIC'))
  selection=resolve_bootstrap_bricks(merge_candidate_rows(decoded),synthetic_legacy=self.manifest['execution_kind']=='SYNTHETIC')
  development={'selection':selection,'permanent':True,'policy':'INSTRUMENTAL_DEVELOPMENT'}
  self.ledger.record_development(development)
  final_resources=[]
  for role in self.manifest['dependent_roles']:
   evidence=self._cached_bytes(role['supporting_evidence_sha256'])
   resolution=materialize_role(role,selection,evidence)
   resolution_bytes=canonical(resolution)+b'\n'
   self.ledger.charge('io_bytes',len(resolution_bytes))
   immutable_write(self.root/'TECHNICAL_INDEX/metadata_resolutions'/(role['id']+'.json'),resolution_bytes)
   transport=transport_resource(dict(resolution,id=role['id']),role); transport['host']=role['host']
   bootstrap_firewall(transport,self.manifest)
   if hasattr(network,'authorize_materialized'): network.authorize_materialized(transport['url'],transport['method'])
   acquire.fetch(transport,resume=resume)
   state=self.ledger.resource(transport['id'])
   receipt_resources.append({'kind':'dependent','role_id':role['id'],'resolution_sha256':resolution['resolution_sha256'],
    'url':resolution['url'],'method':resolution['method'],'state':state['state'],
    'body_bytes':state['offset'],'sha256':state['sha']})
   if role['kind']=='coadd_head': final_resources.append(final_resource_from_head(role,resolution))
  receipt=metadata_receipt(self.ledger,receipt_resources,selection)
  self.ledger.record_receipt(receipt)
  csv_bytes=development_csv(selection,self.manifest['development_policy']['evidence_ref'])
  allow=self.root/'INPUTS/OC3_DEVELOPMENT_BRICKS.csv'; allow_sha=digest(csv_bytes)
  rights={'analysis':self.manifest['rights']['scientific_local_analysis'],
   'local_preservation':self.manifest['rights']['local_preservation'],'redistribution':False,
   'evidence_refs':self.manifest['rights']['evidence_refs']}
  final=final_manifest(self.parent,receipt,selection,allow,allow_sha,final_resources,rights,
   self.manifest['semantics'],self.manifest['release_issues'],self.manifest['approved_hosts'])
  return promote(self.ledger,self.parent,receipt,selection,allow,csv_bytes,
   self.root/'INPUTS/OC3_INPUT_MANIFEST.json',final,final_resources,crash=crash,resume=resume)
