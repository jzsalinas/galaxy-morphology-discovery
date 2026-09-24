#!/usr/bin/env python3
"""Single-resource governed primary-literature acquisition."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import urllib.request

sys.dont_write_bytecode=True
from oc3lib.cross_observer_grouping import PROJECT, load_canonical_json, sealed, write_json_immutable
from oc3lib.cross_observer_grouping_documentary_provenance import validate_local_snapshot, validate_transport_evidence
from oc3lib.cross_observer_grouping_primary_literature_validation import (
    CANDIDATE, FROZEN_USER_AGENT, LiteratureValidationError, validate_candidate, validate_runtime,
)


class RejectRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise LiteratureValidationError("REDIRECT_FORBIDDEN")


def parser():
    result=argparse.ArgumentParser(); mode=result.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-candidate",action="store_true")
    mode.add_argument("--acquire-primary-literature",action="store_true")
    result.add_argument("--candidate",type=Path,default=CANDIDATE); result.add_argument("--permit",type=Path)
    result.add_argument("--standing-authorization",type=Path); result.add_argument("--autonomy-state",type=Path)
    result.add_argument("--output-directory",type=Path); return result


def execute(candidate, output: Path, counters: dict[str,int]):
    resource=load_canonical_json(PROJECT/candidate["resource_manifest"]["path"])["resources"][0]
    output.mkdir(parents=True,exist_ok=False); raw=output/"RAW_IMMUTABLE"; raw.mkdir()
    request=urllib.request.Request(resource["url"],method="GET",headers={"User-Agent":FROZEN_USER_AGENT})
    counters["network_requests_started"] += 1
    response=urllib.request.build_opener(RejectRedirect).open(request,timeout=60)
    try:
        if response.status != 200 or response.geturl() != resource["url"]:
            raise LiteratureValidationError("HTTP_IDENTITY_INVALID")
        content_type=response.headers.get_content_type()
        if content_type != "application/pdf": raise LiteratureValidationError("CONTENT_TYPE_INVALID")
        declared=response.headers.get("Content-Length")
        if declared is not None and (not declared.isdecimal() or int(declared)>8_388_608):
            raise LiteratureValidationError("RESOURCE_BODY_CAP_EXCEEDED")
        body=response.read(8_388_609); counters["application_body_bytes"] += len(body)
        if len(body)>8_388_608: raise LiteratureValidationError("RESOURCE_BODY_CAP_EXCEEDED")
        if not body.startswith(b"%PDF-"): raise LiteratureValidationError("PDF_REPRESENTATION_INVALID")
        record={"application_body_bytes":len(body),"capture_mode":resource["evidence_capture_mode"],
            "content_length":None if declared is None else int(declared),"content_type":content_type,
            "etag":response.headers.get("ETag"),"final_url":response.geturl(),
            "last_modified":response.headers.get("Last-Modified"),"requested_url":resource["url"],
            "resource_id":resource["id"],"retrieved_at_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
            "sha256":hashlib.sha256(body).hexdigest(),"status":response.status}
        validate_transport_evidence(record)
    finally: response.close()
    target=raw/f"{resource['id']}.body"
    with target.open("xb") as stream: stream.write(body); stream.flush(); os.fsync(stream.fileno())
    target.chmod(0o444); validate_local_snapshot(target,record["sha256"])
    write_json_immutable(output/"TRANSPORT_EVIDENCE.json",sealed({
        "resource":record,"schema_version":"OC3_CROSS_OBSERVER_PRIMARY_LITERATURE_TRANSPORT_001"}))
    terminal=sealed({"application_body_bytes_read":len(body),"counters":{
        "network_requests_started":1,"retry_requests":0,"PHOTSYS_reads":0,"TYPE_values_read":0,
        "DCHISQ_values_read":0,"Sersic_shape_values_read":0,"photometric_values_read":0,
        "photoz_values_read":0,"source_rows_read":0,"image_pixels_read":0,"morphology_accesses":0,
        "label_accesses":0,"model_operations":0,"training_operations":0,"embedding_operations":0,
        "clustering_operations":0,"panel_v3_operations":0,"p1_operations":0},
        "documentary_gate_decided":False,"scope":candidate["scope"],"stage_id":candidate["stage_id"],
        "state":"PRIMARY_CROSS_IDENTIFICATION_LITERATURE_ACQUIRED_PENDING_OFFLINE_REVIEW"})
    write_json_immutable(output/"TERMINAL.json",terminal); return terminal


def main(argv=None):
    args=parser().parse_args(argv); counters={"network_requests_started":0,"application_body_bytes":0}
    try:
        candidate=validate_candidate(args.candidate)
        if args.validate_candidate:
            print(json.dumps({"network_requests":0,"source_rows":0,"state":"READY_AT_PRIMARY_LITERATURE_BOUNDARY"},sort_keys=True)); return 0
        if None in (args.permit,args.standing_authorization,args.autonomy_state,args.output_directory):
            raise LiteratureValidationError("GOVERNED_ARGUMENTS_REQUIRED")
        validate_runtime(candidate,sys.executable,sys.argv[0],sys.argv[1:])
        from oc3lib.cross_observer_grouping_governor import consume_permit, validate_permit
        validate_permit(args.permit,candidate_path=args.candidate,state_path=args.autonomy_state,
                        standing_authorization_path=args.standing_authorization)
        consume_permit(args.permit,candidate_path=args.candidate,state_path=args.autonomy_state,
                       standing_authorization_path=args.standing_authorization,
                       consumed_at_utc=datetime.now(timezone.utc).isoformat().replace("+00:00","Z"))
        terminal=execute(candidate,args.output_directory,counters); print(json.dumps(terminal,sort_keys=True)); return 0
    except Exception as exc:
        print(json.dumps({"application_body_bytes":counters["application_body_bytes"],
            "error":getattr(exc,"code",str(exc)),"network_requests":counters["network_requests_started"],
            "state":"PRIMARY_LITERATURE_RECOVERY_FAILED_CLOSED"},sort_keys=True)); return 2


if __name__=="__main__": raise SystemExit(main())

