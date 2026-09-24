#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,os,sys,urllib.request
from datetime import datetime,timezone
from pathlib import Path
sys.dont_write_bytecode=True
from oc3lib.cross_observer_grouping import PROJECT,load_canonical_json,sealed,write_json_immutable
from oc3lib.cross_observer_grouping_documentary_provenance import validate_local_snapshot,validate_transport_evidence
from oc3lib.cross_observer_grouping_primary_article_validation import CANDIDATE,USER_AGENT,ArticleValidationError,validate_candidate,validate_runtime
class RejectRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl): raise ArticleValidationError("REDIRECT_FORBIDDEN")
def parser():
 p=argparse.ArgumentParser(); m=p.add_mutually_exclusive_group(required=True); m.add_argument("--validate-candidate",action="store_true"); m.add_argument("--acquire-primary-article",action="store_true")
 p.add_argument("--candidate",type=Path,default=CANDIDATE); p.add_argument("--permit",type=Path); p.add_argument("--standing-authorization",type=Path); p.add_argument("--autonomy-state",type=Path); p.add_argument("--output-directory",type=Path); return p
def execute(c,o:Path,k):
 r=load_canonical_json(PROJECT/c["resource_manifest"]["path"])["resources"][0]; o.mkdir(parents=True,exist_ok=False); raw=o/"RAW_IMMUTABLE"; raw.mkdir(); req=urllib.request.Request(r["url"],method="GET",headers={"User-Agent":USER_AGENT}); k["network_requests_started"]+=1; resp=urllib.request.build_opener(RejectRedirect).open(req,timeout=60)
 try:
  if resp.status!=200 or resp.geturl()!=r["url"]: raise ArticleValidationError("HTTP_IDENTITY_INVALID")
  ct=resp.headers.get_content_type()
  if ct!="application/pdf": raise ArticleValidationError("CONTENT_TYPE_INVALID")
  declared=resp.headers.get("Content-Length")
  if declared is not None and (not declared.isdecimal() or int(declared)>8388608): raise ArticleValidationError("RESOURCE_BODY_CAP_EXCEEDED")
  body=resp.read(8388609); k["application_body_bytes"]+=len(body)
  if len(body)>8388608: raise ArticleValidationError("RESOURCE_BODY_CAP_EXCEEDED")
  if not body.startswith(b"%PDF-"): raise ArticleValidationError("PDF_REPRESENTATION_INVALID")
  record={"application_body_bytes":len(body),"capture_mode":r["evidence_capture_mode"],"content_length":None if declared is None else int(declared),"content_type":ct,"etag":resp.headers.get("ETag"),"final_url":resp.geturl(),"last_modified":resp.headers.get("Last-Modified"),"requested_url":r["url"],"resource_id":r["id"],"retrieved_at_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),"sha256":hashlib.sha256(body).hexdigest(),"status":resp.status}; validate_transport_evidence(record)
 finally: resp.close()
 target=raw/f"{r['id']}.body"
 with target.open("xb") as f: f.write(body); f.flush(); os.fsync(f.fileno())
 target.chmod(0o444); validate_local_snapshot(target,record["sha256"]); write_json_immutable(o/"TRANSPORT_EVIDENCE.json",sealed({"resource":record,"schema_version":"OC3_CROSS_OBSERVER_PRIMARY_ARTICLE_TRANSPORT_002"}))
 terminal=sealed({"application_body_bytes_read":len(body),"counters":{"network_requests_started":1,"retry_requests":0,"PHOTSYS_reads":0,"TYPE_values_read":0,"DCHISQ_values_read":0,"Sersic_shape_values_read":0,"photometric_values_read":0,"photoz_values_read":0,"source_rows_read":0,"image_pixels_read":0,"morphology_accesses":0,"label_accesses":0,"model_operations":0,"training_operations":0,"embedding_operations":0,"clustering_operations":0,"panel_v3_operations":0,"p1_operations":0},"documentary_gate_decided":False,"scope":c["scope"],"stage_id":c["stage_id"],"state":"PRIMARY_CROSS_IDENTIFICATION_ARTICLE_ACQUIRED_PENDING_OFFLINE_REVIEW"}); write_json_immutable(o/"TERMINAL.json",terminal); return terminal
def main(argv=None):
 a=parser().parse_args(argv); k={"network_requests_started":0,"application_body_bytes":0}
 try:
  c=validate_candidate(a.candidate)
  if a.validate_candidate: print(json.dumps({"network_requests":0,"source_rows":0,"state":"READY_AT_PRIMARY_ARTICLE_BOUNDARY"},sort_keys=True)); return 0
  if None in (a.permit,a.standing_authorization,a.autonomy_state,a.output_directory): raise ArticleValidationError("GOVERNED_ARGUMENTS_REQUIRED")
  validate_runtime(c,sys.executable,sys.argv[0],sys.argv[1:]); from oc3lib.cross_observer_grouping_governor import consume_permit,validate_permit
  validate_permit(a.permit,candidate_path=a.candidate,state_path=a.autonomy_state,standing_authorization_path=a.standing_authorization); consume_permit(a.permit,candidate_path=a.candidate,state_path=a.autonomy_state,standing_authorization_path=a.standing_authorization,consumed_at_utc=datetime.now(timezone.utc).isoformat().replace("+00:00","Z")); t=execute(c,a.output_directory,k); print(json.dumps(t,sort_keys=True)); return 0
 except Exception as e: print(json.dumps({"application_body_bytes":k["application_body_bytes"],"error":getattr(e,"code",str(e)),"network_requests":k["network_requests_started"],"state":"PRIMARY_ARTICLE_RECOVERY_FAILED_CLOSED"},sort_keys=True)); return 2
if __name__=="__main__": raise SystemExit(main())

