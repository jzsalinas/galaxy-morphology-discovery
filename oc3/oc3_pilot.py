#!/usr/bin/env python3
"""OC-3 infrastructure CLI. Offline by default; implementation is not authorization."""
import sys
sys.dont_write_bytecode=True
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
 os.environ[key]='1'
import argparse
from pathlib import Path
from oc3lib.core import *
from oc3lib.workflow import (build_final_plan,validate_plan,read_inputs,Run,artifact_path,environment)
from oc3lib.bootstrap import BootstrapRun
from oc3lib.transport import HTTPTransport

def parser():
 p=argparse.ArgumentParser(description='OC-3 infrastructure; default OFFLINE. Scientific execution requires separate authorization and sealed inputs.')
 commands=p.add_subparsers(dest='command',required=True)
 for name in ('plan','acquire-aux','select','acquire-fixed','analyze','verify','finalize'):
  s=commands.add_parser(name)
  s.add_argument('--project',type=Path,default=Path(__file__).resolve().parent.parent)
  s.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
  s.add_argument('--spec',type=Path)
  if name=='plan':
   group=s.add_mutually_exclusive_group(required=True)
   group.add_argument('--inputs',type=Path)
   group.add_argument('--bootstrap-inputs',type=Path)
  s.add_argument('--plan',type=Path,default=Path('oc3/provenance/OC3_RESOURCE_PLAN.json'))
  s.add_argument('--locations',type=Path)
  s.add_argument('--offline',action='store_true')
  s.add_argument('--dry-run',action='store_true')
  s.add_argument('--execute-network',action='store_true',help='Explicit network capability; never overrides --offline/--dry-run.')
  s.add_argument('--resolve-metadata',action='store_true')
  s.add_argument('--seal',action='store_true')
  s.add_argument('--resume',action='store_true')
  for field in MAXIMA: s.add_argument('--max-'+field.replace('_','-'),type=int,default=None)
  for field in MAXIMA: s.add_argument('--max-global-'+field.replace('_','-'),type=int,default=None)
  for field in BOOTSTRAP_MAXIMA: s.add_argument('--max-stage-'+field.replace('_','-'),type=int,default=None)
 return p

def _caps(args):
 legacy={k:getattr(args,'max_'+k) for k in MAXIMA if getattr(args,'max_'+k) is not None}
 global_caps={k:getattr(args,'max_global_'+k) for k in MAXIMA if getattr(args,'max_global_'+k) is not None}
 stage_caps={k:getattr(args,'max_stage_'+k) for k in BOOTSTRAP_MAXIMA if getattr(args,'max_stage_'+k) is not None}
 if legacy and (args.command=='plan' or args.command in ('acquire-aux','acquire-fixed')):
  raise InputError('AMBIGUOUS_LIMIT_SCOPE_USE_GLOBAL_OR_STAGE')
 if set(legacy)&set(global_caps): raise InputError('DUPLICATE_LIMIT_SCOPE')
 global_caps={**legacy,**global_caps}; limits(global_caps); stage_limits(stage_caps)
 return global_caps,stage_caps

def main(argv=None):
 args=parser().parse_args(argv); run=None; bootstrap=None
 try:
  global_caps,stage_caps=_caps(args)
  verify_authorities(args.project); safe_path(args.root)
  if args.spec and args.spec.resolve()!=(args.project/'OC3_DR9_COADD_BOUNDED_PILOT_SPEC.md').resolve(): raise IntegrityError('WRONG_SPEC_PATH')
  if args.offline and args.execute_network: raise OfflineError('OFFLINE_CANNOT_ENABLE_NETWORK')
  bootstrap_mode=args.command=='plan' and args.bootstrap_inputs is not None
  final_mode=args.command=='plan' and args.inputs is not None
  if args.resolve_metadata and not bootstrap_mode: raise InputError('RESOLVE_METADATA_BOOTSTRAP_ONLY')
  if bootstrap_mode and not args.resolve_metadata and not args.dry_run: raise InputError('BOOTSTRAP_REQUIRES_RESOLVE_METADATA')
  if final_mode and args.execute_network: raise InputError('FINAL_PLAN_HAS_NO_NETWORK')
  if args.command!='plan' and (args.resolve_metadata or stage_caps): raise InputError('STAGE_LIMITS_BOOTSTRAP_ONLY')
  if args.dry_run:
   selected=args.bootstrap_inputs if bootstrap_mode else args.inputs if final_mode else args.plan
   safe_path(selected); missing=[] if selected.is_file() else [str(selected)]
   print(canonical(dict(status='OC3_DRY_RUN_OK',command=args.command,
    mode='BOOTSTRAP_METADATA' if bootstrap_mode else 'FINAL_PLAN' if final_mode else 'STAGE',
    network=False,evidence_mutation=False,promotion=False,selection_persisted=False,fits_decoding=False,
    missing_inputs=missing,dependencies=environment()['dependencies'],global_limits=limits(global_caps),
    stage_limits=stage_limits(stage_caps) if bootstrap_mode else None,authorities_verified=True,
    scientific_execution='NOT_STARTED')).decode())
   return 0
  if args.command in ('acquire-aux','acquire-fixed') and (args.offline or not args.execute_network):
   raise OfflineError('OFFLINE_TRANSPORT_UNAVAILABLE')
  if bootstrap_mode:
   if args.offline or not args.execute_network: raise OfflineError('OFFLINE_TRANSPORT_UNAVAILABLE')
   bootstrap=BootstrapRun(args.project,args.root,args.bootstrap_inputs,network_capable=True,
    global_overrides=global_caps,stage_overrides=stage_caps,resume=args.resume)
   approved={r['url']:r['method'] for r in bootstrap.manifest['literal_resources']}
   bootstrap.execute(HTTPTransport(approved),resume=args.resume)
   bootstrap.close(); bootstrap=None
   print('OC3_METADATA_BOOTSTRAP_OK'); return 0
  if args.command=='plan':
   plan=build_final_plan(args.project,args.inputs,args.root,global_caps); inp,_,_=read_inputs(args.inputs)
  else:
   plan,inp=validate_plan(args.project,args.plan,args.root)
   if args.locations and args.locations.resolve()!=artifact_path(args.root,'OC3_LOCATIONS.json').resolve(): raise InputError('LOCATIONS_PATH_NOT_CANONICAL')
  network_stage=args.command in ('acquire-aux','acquire-fixed')
  if network_stage and (args.offline or not args.execute_network): raise OfflineError('OFFLINE_TRANSPORT_UNAVAILABLE')
  if args.execute_network and inp['execution_kind']!='PRODUCTION': raise InputError('SYNTHETIC_CANNOT_USE_REAL_NETWORK')
  if args.command=='select' and not args.seal: raise InputError('SEAL_REQUIRED')
  run=Run(args.project,args.root,plan,inp,args.resume,global_caps)
  if network_stage:
   transport=HTTPTransport({r['url']:r.get('method','GET') for r in run.resources})
   run.acquire('aux' if args.command=='acquire-aux' else 'fixed',transport,args.resume)
  elif args.command=='select': run.select()
  elif args.command=='analyze': run.analyze()
  elif args.command=='verify': run.verify()
  elif args.command=='finalize':
   outcome=run.finalize(); run.close(); run=None; print('OC3_TECHNICAL_RUN_COMPLETE; outcome='+outcome); return 0
  run.close(); run=None
  print('OC3_'+args.command.upper().replace('-','_')+'_OK'); return 0
 except IntegrityError:
  if run is not None:
   try: run.stop_integrity()
   except (LimitError,IntegrityError,OSError): pass
  print('OC3_INTEGRITY_FAILURE_STOP',file=sys.stderr); return 20
 except OfflineError:
  print('OC3_OFFLINE_BLOCKED',file=sys.stderr); return 21
 except (InputError,DependencyError,LimitError):
  print('OC3_PREREQUISITE_OR_RESOURCE_BLOCKED',file=sys.stderr); return 22
 except (OSError,TimeoutError):
  print('OC3_INTERRUPTED_RESUME_REQUIRED',file=sys.stderr); return 75
 finally:
  if bootstrap is not None:
   try: bootstrap.close()
   except Exception: pass
  if run is not None:
   try: run.close()
   except (LimitError,IntegrityError): pass

if __name__=='__main__': raise SystemExit(main())
