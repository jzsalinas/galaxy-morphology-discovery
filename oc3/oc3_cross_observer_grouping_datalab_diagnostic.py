#!/usr/bin/env python3
"""One-request Data Lab schema-response diagnostic."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import urllib.request

sys.dont_write_bytecode = True

from oc3lib.cross_observer_grouping import PROJECT, load_canonical_json, sealed, write_json_immutable
from oc3lib.cross_observer_grouping_documentary_provenance import validate_local_snapshot, validate_transport_evidence
from oc3lib.cross_observer_grouping_datalab_diagnostic_validation import (
    CANDIDATE, DiagnosticValidationError, validate_candidate, validate_runtime,
)


class RejectRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise DiagnosticValidationError("REDIRECT_FORBIDDEN")


def parser():
    result = argparse.ArgumentParser()
    mode = result.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-candidate", action="store_true")
    mode.add_argument("--execute-diagnostic", action="store_true")
    result.add_argument("--candidate", type=Path, default=CANDIDATE)
    result.add_argument("--permit", type=Path)
    result.add_argument("--standing-authorization", type=Path)
    result.add_argument("--autonomy-state", type=Path)
    result.add_argument("--output-directory", type=Path)
    return result


def execute(candidate, output, counters):
    manifest = load_canonical_json(PROJECT / candidate["resource_manifest"]["path"])
    resource = manifest["resources"][0]
    output.mkdir(parents=True, exist_ok=False)
    raw = output / "RAW_IMMUTABLE"; raw.mkdir()
    request = urllib.request.Request(resource["url"], method="GET",
                                     headers={"User-Agent":"OC3-datalab-diagnostic/1"})
    counters["network_requests_started"] += 1
    response = urllib.request.build_opener(RejectRedirect).open(request, timeout=30)
    try:
        if response.status != 200 or response.geturl() != resource["url"]:
            raise DiagnosticValidationError("HTTP_IDENTITY_INVALID")
        content_type = response.headers.get_content_type()
        if content_type not in resource["accepted_content_types"]:
            raise DiagnosticValidationError("CONTENT_TYPE_INVALID")
        body = response.read(65_537)
        counters["application_body_bytes"] += len(body)
        if len(body) > 65_536:
            raise DiagnosticValidationError("RESOURCE_BODY_CAP_EXCEEDED")
        declared = response.headers.get("Content-Length")
        if declared is not None and (not declared.isdecimal() or int(declared) != len(body)):
            raise DiagnosticValidationError("CONTENT_LENGTH_INVALID")
        record = {"application_body_bytes":len(body),"capture_mode":resource["evidence_capture_mode"],
            "content_length":None if declared is None else int(declared),"content_type":content_type,
            "etag":response.headers.get("ETag"),"final_url":response.geturl(),
            "last_modified":response.headers.get("Last-Modified"),"requested_url":resource["url"],
            "resource_id":resource["id"],"retrieved_at_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
            "sha256":hashlib.sha256(body).hexdigest(),"status":response.status}
        validate_transport_evidence(record)
    finally:
        response.close()
    target=raw/f"{resource['id']}.body"
    with target.open("xb") as stream:
        stream.write(body); stream.flush(); os.fsync(stream.fileno())
    target.chmod(0o444); validate_local_snapshot(target,record["sha256"])
    write_json_immutable(output/"TRANSPORT_EVIDENCE.json",sealed({
        "resource":record,"schema_version":"OC3_CROSS_OBSERVER_DATALAB_DIAGNOSTIC_TRANSPORT_001"}))
    terminal=sealed({"application_body_bytes_read":len(body),"counters":{
        "network_requests_started":1,"retry_requests":0,"PHOTSYS_reads":0,"TYPE_values_read":0,
        "DCHISQ_values_read":0,"Sersic_shape_values_read":0,"photometric_values_read":0,
        "photoz_values_read":0,"source_rows_read":0,"image_pixels_read":0,"morphology_accesses":0,
        "label_accesses":0,"model_operations":0,"training_operations":0,"embedding_operations":0,
        "clustering_operations":0,"panel_v3_operations":0,"p1_operations":0},
        "documentary_gate_decided":False,"scope":candidate["scope"],"stage_id":candidate["stage_id"],
        "state":"DATALAB_COLUMN_METADATA_RESPONSE_CAPTURED_FOR_OFFLINE_DIAGNOSIS"})
    write_json_immutable(output/"TERMINAL.json",terminal)
    return terminal


def main(argv=None):
    args=parser().parse_args(argv); counters={"network_requests_started":0,"application_body_bytes":0}
    try:
        candidate=validate_candidate(args.candidate)
        if args.validate_candidate:
            print(json.dumps({"network_requests":0,"source_rows":0,"state":"READY_AT_DATALAB_DIAGNOSTIC_BOUNDARY"},sort_keys=True)); return 0
        if None in (args.permit,args.standing_authorization,args.autonomy_state,args.output_directory):
            raise DiagnosticValidationError("GOVERNED_ARGUMENTS_REQUIRED")
        validate_runtime(candidate,sys.executable,sys.argv[0],sys.argv[1:])
        from oc3lib.cross_observer_grouping_governor import consume_permit, validate_permit
        validate_permit(args.permit,candidate_path=args.candidate,state_path=args.autonomy_state,
                        standing_authorization_path=args.standing_authorization)
        consume_permit(args.permit,candidate_path=args.candidate,state_path=args.autonomy_state,
                       standing_authorization_path=args.standing_authorization,
                       consumed_at_utc=datetime.now(timezone.utc).isoformat().replace("+00:00","Z"))
        terminal=execute(candidate,args.output_directory,counters)
        print(json.dumps(terminal,sort_keys=True)); return 0
    except Exception as exc:
        print(json.dumps({"application_body_bytes":counters["application_body_bytes"],
            "error":getattr(exc,"code",str(exc)),"network_requests":counters["network_requests_started"],
            "state":"DATALAB_DIAGNOSTIC_FAILED_CLOSED"},sort_keys=True)); return 2


if __name__ == "__main__":
    raise SystemExit(main())
