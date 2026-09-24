#!/usr/bin/env python3
"""Acquire the three missing documentary snapshots under an exact permit."""
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
for _key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
             "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_key] = "1"

from oc3lib.cross_observer_grouping import PROJECT, load_canonical_json, sealed, write_json_immutable
from oc3lib.cross_observer_grouping_documentary_provenance import validate_local_snapshot, validate_transport_evidence
from oc3lib.cross_observer_grouping_documentary_completion_validation import (
    CANDIDATE, CompletionValidationError, validate_candidate, validate_runtime,
)


class RejectRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise CompletionValidationError("REDIRECT_FORBIDDEN")


def parser():
    result = argparse.ArgumentParser()
    mode = result.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-candidate", action="store_true")
    mode.add_argument("--acquire-documentary-completion", action="store_true")
    result.add_argument("--candidate", type=Path, default=CANDIDATE)
    result.add_argument("--permit", type=Path)
    result.add_argument("--standing-authorization", type=Path)
    result.add_argument("--autonomy-state", type=Path)
    result.add_argument("--output-directory", type=Path)
    return result


def _read_bounded(response, cap: int, aggregate_remaining: int, counters: dict[str, int]) -> bytes:
    declared = response.headers.get("Content-Length")
    if declared is not None and (not declared.isdecimal() or int(declared) > cap or
                                 int(declared) > aggregate_remaining):
        raise CompletionValidationError("RESOURCE_BODY_CAP_EXCEEDED")
    parts, size = [], 0
    while True:
        block = response.read(min(65_536, cap + 1 - size))
        if not block:
            break
        parts.append(block); size += len(block); counters["application_body_bytes"] += len(block)
        if size > cap or size > aggregate_remaining:
            raise CompletionValidationError("RESOURCE_BODY_CAP_EXCEEDED")
    return b"".join(parts)


def _publish_raw(path: Path, body: bytes) -> None:
    with path.open("xb") as stream:
        stream.write(body); stream.flush(); os.fsync(stream.fileno())
    path.chmod(0o444)


def execute(candidate, output: Path, counters: dict[str, int]):
    manifest = load_canonical_json(PROJECT / candidate["resource_manifest"]["path"])
    output.mkdir(parents=True, exist_ok=False)
    raw = output / "RAW_IMMUTABLE"; raw.mkdir()
    opener = urllib.request.build_opener(RejectRedirect)
    evidence, aggregate = [], 0
    for resource in manifest["resources"]:
        request = urllib.request.Request(resource["url"], method="GET",
            headers={"User-Agent":"OC3-documentary-completion/1"})
        counters["network_requests_started"] += 1
        response = opener.open(request, timeout=60)
        try:
            if response.status != 200 or response.geturl() != resource["url"]:
                raise CompletionValidationError("HTTP_IDENTITY_INVALID")
            content_type = response.headers.get_content_type()
            if content_type not in resource["accepted_content_types"]:
                raise CompletionValidationError("CONTENT_TYPE_INVALID")
            body = _read_bounded(response, resource["application_body_byte_cap"],
                                 9_437_184 - aggregate, counters)
            if resource["id"] == "BUDAVARI_SZALAY_2008_PREPRINT" and not body.startswith(b"%PDF-"):
                raise CompletionValidationError("PDF_REPRESENTATION_INVALID")
            record = {"application_body_bytes":len(body),"capture_mode":resource["evidence_capture_mode"],
                "content_length":None if response.headers.get("Content-Length") is None else int(response.headers["Content-Length"]),
                "content_type":content_type,"etag":response.headers.get("ETag"),"final_url":response.geturl(),
                "last_modified":response.headers.get("Last-Modified"),"requested_url":resource["url"],
                "resource_id":resource["id"],"retrieved_at_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
                "sha256":hashlib.sha256(body).hexdigest(),"status":response.status}
            validate_transport_evidence(record)
        finally:
            response.close()
        aggregate += len(body)
        target = raw / f"{resource['id']}.body"
        _publish_raw(target, body); validate_local_snapshot(target, record["sha256"])
        evidence.append(record)
    write_json_immutable(output / "TRANSPORT_EVIDENCE.json", sealed({
        "application_body_bytes":aggregate,"network_requests":len(evidence),"resources":evidence,
        "schema_version":"OC3_CROSS_OBSERVER_DOCUMENTARY_COMPLETION_TRANSPORT_003"}))
    terminal = sealed({"application_body_bytes_read":aggregate,"counters":{
        "network_requests_started":len(evidence),"retry_requests":0,"PHOTSYS_reads":0,
        "TYPE_values_read":0,"DCHISQ_values_read":0,"Sersic_shape_values_read":0,
        "photometric_values_read":0,"photoz_values_read":0,"source_rows_read":0,
        "image_pixels_read":0,"morphology_accesses":0,"label_accesses":0,"model_operations":0,
        "training_operations":0,"embedding_operations":0,"clustering_operations":0,
        "panel_v3_operations":0,"p1_operations":0},"documentary_gate_decided":False,
        "scope":candidate["scope"],"stage_id":candidate["stage_id"],
        "state":"DOCUMENTARY_COMPLETION_ACQUIRED_PENDING_OFFLINE_SEMANTIC_REVIEW"})
    write_json_immutable(output / "TERMINAL.json", terminal)
    return terminal


def main(argv=None):
    args = parser().parse_args(argv); counters = {"network_requests_started":0,"application_body_bytes":0}
    try:
        candidate = validate_candidate(args.candidate)
        if args.validate_candidate:
            print(json.dumps({"network_requests":0,"source_rows":0,
                "state":"READY_AT_DOCUMENTARY_COMPLETION_BOUNDARY"},sort_keys=True)); return 0
        if None in (args.permit,args.standing_authorization,args.autonomy_state,args.output_directory):
            raise CompletionValidationError("GOVERNED_ARGUMENTS_REQUIRED")
        validate_runtime(candidate,sys.executable,sys.argv[0],sys.argv[1:])
        from oc3lib.cross_observer_grouping_governor import consume_permit, validate_permit
        validate_permit(args.permit,candidate_path=args.candidate,state_path=args.autonomy_state,
                        standing_authorization_path=args.standing_authorization)
        consume_permit(args.permit,candidate_path=args.candidate,state_path=args.autonomy_state,
                       standing_authorization_path=args.standing_authorization,
                       consumed_at_utc=datetime.now(timezone.utc).isoformat().replace("+00:00","Z"))
        terminal = execute(candidate,args.output_directory,counters)
        print(json.dumps(terminal,sort_keys=True)); return 0
    except Exception as exc:
        print(json.dumps({"application_body_bytes":counters["application_body_bytes"],
            "error":getattr(exc,"code",str(exc)),"network_requests":counters["network_requests_started"],
            "state":"DOCUMENTARY_COMPLETION_FAILED_CLOSED"},sort_keys=True)); return 2


if __name__ == "__main__":
    raise SystemExit(main())

