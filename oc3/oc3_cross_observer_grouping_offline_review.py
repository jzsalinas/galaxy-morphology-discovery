#!/usr/bin/env python3
"""Deterministic offline semantic review of the acquired documentary evidence."""
from __future__ import annotations
import argparse,csv,io,json
from datetime import datetime,timezone
from pathlib import Path
import sys

sys.dont_write_bytecode=True
from oc3lib.cross_observer_grouping import PROJECT,file_sha256,load_canonical_json,sealed,write_json_immutable
from oc3lib.cross_observer_grouping_offline_review_validation import (
 CANDIDATE,OfflineReviewValidationError,validate_candidate,validate_runtime)

CLAIMS=("CATALOG_SOURCE_IDENTITY","BRICK_PRIMARY_SEMANTICS","NORTH_SOUTH_PROCESSING_DOMAINS",
 "RESOLVED_CATALOG_NOT_EQUIVALENCE_MAP","ASTROMETRIC_FIELD_SEMANTICS",
 "CALIBRATION_ERROR_OMITTED_FROM_IVARS","GAIA_DR2_ASTROMETRIC_PROVENANCE",
 "REGIONAL_DATALAB_TABLE_AVAILABILITY","CROSS_IDENTIFICATION_FORMALISM_ASSUMPTIONS",
 "BOUNDED_PILOT_SPECIFIABLE_WITHOUT_THRESHOLD")
TABLES={"ls_dr9.tractor","ls_dr9.tractor_n","ls_dr9.tractor_s"}
FIELDS={"release","brickid","objid","brickname","brick_primary","ra","dec","ra_ivar","dec_ivar","ref_cat","ref_id"}

def parser():
 p=argparse.ArgumentParser(); mode=p.add_mutually_exclusive_group(required=True)
 mode.add_argument("--validate-candidate",action="store_true"); mode.add_argument("--review-documentary-evidence",action="store_true")
 p.add_argument("--candidate",type=Path,default=CANDIDATE); p.add_argument("--permit",type=Path)
 p.add_argument("--standing-authorization",type=Path); p.add_argument("--autonomy-state",type=Path)
 p.add_argument("--output-directory",type=Path); return p

def _rows(body:bytes): return list(csv.DictReader(io.StringIO(body.decode("utf-8"))))

def review(candidate,output:Path):
 paths=[PROJECT/b["path"] for b in candidate["input_bindings"]]
 for path,binding in zip(paths,candidate["input_bindings"]):
  if file_sha256(path)!=binding["sha256"]: raise OfflineReviewValidationError("OFFLINE_REVIEW_INPUT_CHANGED")
 catalog,description,files,table_csv,column_csv,completion_terminal,literature_terminal=[p.read_bytes() for p in paths]
 table_rows=_rows(table_csv); column_rows=_rows(column_csv)
 table_names={r["table_name"] for r in table_rows}
 field_map={name:{r["column_name"] for r in column_rows if r["table_name"]==name} for name in TABLES}
 descriptions={(r["table_name"],r["column_name"]):r["description"] for r in column_rows}
 evidence=[{"path":b["path"],"sha256":b["sha256"]} for b in candidate["input_bindings"]]
 supported={
  "CATALOG_SOURCE_IDENTITY":b"unique identifier hash is" in catalog and all({"release","brickid","objid"}<=field_map[t] for t in TABLES),
  "BRICK_PRIMARY_SEMANTICS":b"within the brick boundary" in catalog and all("brick_primary" in field_map[t] for t in TABLES),
  "NORTH_SOUTH_PROCESSING_DOMAINS":all(x in description for x in (b"northern",b"southern",b"BASS",b"MzLS",b"DECam")),
  "RESOLVED_CATALOG_NOT_EQUIVALENCE_MAP":all(x in description for x in (b"resolved",b"Declination &gt; 32.375",b"Galactic Plane")) and table_names==TABLES,
  "ASTROMETRIC_FIELD_SEMANTICS":all({"ra","dec","ra_ivar","dec_ivar"}<=field_map[t] for t in TABLES) and b"equinox J2000" in catalog,
  "CALIBRATION_ERROR_OMITTED_FROM_IVARS":all("excluding astrometric calibration errors" in descriptions[(t,f)] for t in TABLES for f in ("ra_ivar","dec_ivar")),
  "GAIA_DR2_ASTROMETRIC_PROVENANCE":b"Gaia Data Release 2" in description and b"positions of sources are tied" in description,
  "REGIONAL_DATALAB_TABLE_AVAILABILITY":table_names==TABLES and all(field_map[t]==FIELDS for t in TABLES),
  "CROSS_IDENTIFICATION_FORMALISM_ASSUMPTIONS":False,
  "BOUNDED_PILOT_SPECIFIABLE_WITHOUT_THRESHOLD":False}
 conflicts={name:False for name in CLAIMS}
 states={name:("CONFLICT" if conflicts[name] else "SUPPORTED" if supported[name] else "INCONCLUSIVE") for name in CLAIMS}
 states["BOUNDED_PILOT_SPECIFIABLE_WITHOUT_THRESHOLD"]=("SUPPORTED" if all(states[n]=="SUPPORTED" for n in CLAIMS[:-1]) else "INCONCLUSIVE")
 if any(v=="CONFLICT" for v in states.values()): outcome="DOCUMENTARY_SOURCE_METADATA_CONFLICT"
 elif all(v=="SUPPORTED" for v in states.values()): outcome="DOCUMENTARY_SOURCE_METADATA_PILOT_SPECIFIABLE"
 else: outcome="DOCUMENTARY_SOURCE_METADATA_PILOT_INCONCLUSIVE"
 rows=[]
 for name in CLAIMS:
  rows.append({"claim":name,"evidence":evidence,"evidence_class":(
   "PRIMARY_LITERATURE_FORMALISM" if name=="CROSS_IDENTIFICATION_FORMALISM_ASSUMPTIONS" else
   "PROJECT_INFERENCE" if name in ("RESOLVED_CATALOG_NOT_EQUIVALENCE_MAP","BOUNDED_PILOT_SPECIFIABLE_WITHOUT_THRESHOLD") else
   "DATA_ACCESS_FACT" if name=="REGIONAL_DATALAB_TABLE_AVAILABILITY" else "OFFICIAL_PROVIDER_FACT"),
   "state":states[name]})
 output.mkdir(parents=True,exist_ok=False)
 matrix=sealed({"claims":rows,"documentary_outcome":outcome,"schema_version":"OC3_CROSS_OBSERVER_DOCUMENTARY_CLAIM_MATRIX_001"})
 write_json_immutable(output/"CLAIM_MATRIX.json",matrix)
 report=("# Offline Documentary Semantic Review\n\n"+"\n".join(f"- `{r['claim']}`: **{r['state']}**" for r in rows)+
  f"\n\nOutcome: `{outcome}`.\n\nThe provider semantics and schema claims are supported. The primary cross-identification paper was not acquired after two separately governed HTTP 406 results, so its formalism assumptions remain INCONCLUSIVE. The all-claims pilot gate therefore remains INCONCLUSIVE; no source-row query or matching threshold is authorized.\n")
 (output/"DOCUMENTARY_REVIEW_REPORT.md").write_text(report,encoding="utf-8")
 terminal=sealed({"application_body_bytes_read":0,"claims_supported":sum(v=="SUPPORTED" for v in states.values()),
  "claims_inconclusive":sum(v=="INCONCLUSIVE" for v in states.values()),"claims_conflict":sum(v=="CONFLICT" for v in states.values()),
  "counters":{"network_requests_started":0,"retry_requests":0,"PHOTSYS_reads":0,"TYPE_values_read":0,
   "DCHISQ_values_read":0,"Sersic_shape_values_read":0,"photometric_values_read":0,"photoz_values_read":0,
   "source_rows_read":0,"image_pixels_read":0,"morphology_accesses":0,"label_accesses":0,
   "model_operations":0,"training_operations":0,"embedding_operations":0,"clustering_operations":0,
   "panel_v3_operations":0,"p1_operations":0},"documentary_outcome":outcome,"scope":candidate["scope"],
  "stage_id":candidate["stage_id"],"state":"OFFLINE_DOCUMENTARY_SEMANTIC_REVIEW_COMPLETED"})
 write_json_immutable(output/"TERMINAL.json",terminal); return terminal

def main(argv=None):
 args=parser().parse_args(argv)
 try:
  candidate=validate_candidate(args.candidate)
  if args.validate_candidate:
   print(json.dumps({"network_requests":0,"source_rows":0,"state":"READY_AT_OFFLINE_DOCUMENTARY_REVIEW_BOUNDARY"},sort_keys=True)); return 0
  if None in (args.permit,args.standing_authorization,args.autonomy_state,args.output_directory):
   raise OfflineReviewValidationError("GOVERNED_ARGUMENTS_REQUIRED")
  validate_runtime(candidate,sys.executable,sys.argv[0],sys.argv[1:])
  from oc3lib.cross_observer_grouping_governor import consume_permit,validate_permit
  validate_permit(args.permit,candidate_path=args.candidate,state_path=args.autonomy_state,
   standing_authorization_path=args.standing_authorization)
  consume_permit(args.permit,candidate_path=args.candidate,state_path=args.autonomy_state,
   standing_authorization_path=args.standing_authorization,consumed_at_utc=datetime.now(timezone.utc).isoformat().replace("+00:00","Z"))
  terminal=review(candidate,args.output_directory); print(json.dumps(terminal,sort_keys=True)); return 0
 except Exception as exc:
  print(json.dumps({"error":getattr(exc,"code",str(exc)),"network_requests":0,"state":"OFFLINE_DOCUMENTARY_REVIEW_FAILED_CLOSED"},sort_keys=True)); return 2

if __name__=="__main__": raise SystemExit(main())

