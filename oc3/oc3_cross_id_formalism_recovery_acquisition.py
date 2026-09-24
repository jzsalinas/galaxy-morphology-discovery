#!/usr/bin/env python3
"""Bounded first acquisition for the cross-ID formalism recovery mission."""
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
for _key in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS",
             "NUMEXPR_NUM_THREADS","VECLIB_MAXIMUM_THREADS"):
    os.environ[_key] = "1"

from oc3lib.cross_id_formalism_recovery import PROJECT, load_canonical_json, sealed, write_json_immutable
from oc3lib.cross_id_formalism_recovery_acquisition_validation import (
    CANDIDATE, RecoveryValidationError, validate_candidate, validate_runtime_invocation,
)

class RejectRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RecoveryValidationError("REDIRECT_FORBIDDEN")

def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Bounded cross-ID primary-evidence acquisition")
    modes = result.add_mutually_exclusive_group(required=True)
    modes.add_argument("--validate-candidate", action="store_true")
    modes.add_argument("--acquire-primary-evidence", action="store_true")
    result.add_argument("--candidate", type=Path, default=CANDIDATE)
    result.add_argument("--permit", type=Path)
    result.add_argument("--standing-authorization", type=Path)
    result.add_argument("--autonomy-state", type=Path)
    result.add_argument("--output-directory", type=Path)
    return result

def _read_bounded(response, cap: int, total_remaining: int, counters: dict[str,int]) -> bytes:
    declared = response.headers.get("Content-Length")
    if declared is not None and (not declared.isdecimal() or int(declared) > cap or int(declared) > total_remaining):
        raise RecoveryValidationError("RESOURCE_BODY_CAP_EXCEEDED")
    chunks: list[bytes] = []; count = 0
    while True:
        chunk = response.read(min(65536, cap + 1 - count))
        if not chunk: break
        chunks.append(chunk); count += len(chunk); counters["application_body_bytes"] += len(chunk)
        if count > cap or count > total_remaining:
            raise RecoveryValidationError("RESOURCE_BODY_CAP_EXCEEDED")
    return b"".join(chunks)

def _write_immutable(path: Path, body: bytes) -> None:
    with path.open("xb") as stream:
        stream.write(body); stream.flush(); os.fsync(stream.fileno())
    path.chmod(0o444)

def _acquire(candidate: dict[str,object], output: Path, counters: dict[str,int]) -> dict[str,object]:
    manifest = load_canonical_json(PROJECT / candidate["resource_manifest"]["path"])
    output.mkdir(parents=True, exist_ok=False); raw = output / "RAW_IMMUTABLE"; raw.mkdir()
    opener = urllib.request.build_opener(RejectRedirect); evidence=[]; total=0
    for resource in manifest["resources"]:
        request=urllib.request.Request(resource["url"],method="GET",headers={"User-Agent":"OC3-bounded-primary-evidence/1"})
        counters["network_requests_started"] += 1
        response=opener.open(request,timeout=30)
        try:
            if response.status != 200 or response.geturl() != resource["url"]:
                raise RecoveryValidationError("HTTP_IDENTITY_INVALID")
            ctype=response.headers.get_content_type()
            if ctype not in resource["accepted_content_types"]:
                raise RecoveryValidationError("CONTENT_TYPE_INVALID")
            body=_read_bounded(response,resource["application_body_byte_cap"],4_718_592-total,counters)
            record={"application_body_bytes":len(body),"bibliographic_identity":resource["bibliographic_identity"],
                "capture_mode":"HASHED_RESPONSE_SNAPSHOT","content_type":ctype,
                "etag":response.headers.get("ETag"),"final_url":response.geturl(),
                "last_modified":response.headers.get("Last-Modified"),"requested_url":resource["url"],
                "resource_id":resource["id"],"retrieved_at_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
                "sha256":hashlib.sha256(body).hexdigest(),"status":response.status}
        finally: response.close()
        total += len(body); _write_immutable(raw/f"{resource['id']}.body",body); evidence.append(record)
    write_json_immutable(output/"TRANSPORT_EVIDENCE.json",sealed({"application_body_bytes":total,
        "network_requests":len(evidence),"resources":evidence,
        "schema_version":"OC3_CROSS_ID_FORMALISM_RECOVERY_TRANSPORT_001"}))
    write_json_immutable(output/"OFFLINE_REVIEW_INPUT.json",sealed({"claims":[
        "CROSS_IDENTIFICATION_FORMALISM_ASSUMPTIONS","BOUNDED_PILOT_SPECIFIABLE_WITHOUT_THRESHOLD"],
        "semantic_decision_made":False,"state":"PENDING_SEPARATELY_CONTRACTED_OFFLINE_REVIEW"}))
    terminal=sealed({"application_body_bytes_read":total,"counters":{"network_requests_started":counters["network_requests_started"],
        "retry_requests":0,"PHOTSYS_reads":0,"TYPE_values_read":0,"DCHISQ_values_read":0,
        "Sersic_shape_values_read":0,"photometric_values_read":0,"photoz_values_read":0,"source_rows_read":0,
        "image_pixels_read":0,"morphology_accesses":0,"label_accesses":0,"model_operations":0,
        "training_operations":0,"embedding_operations":0,"clustering_operations":0,
        "panel_v3_operations":0,"p1_operations":0},"scope":candidate["scope"],
        "stage_id":candidate["stage_id"],"state":"PRIMARY_EVIDENCE_ACQUIRED_PENDING_OFFLINE_REVIEW"})
    write_json_immutable(output/"TERMINAL.json",terminal); return terminal

def main(argv=None) -> int:
    args=parser().parse_args(argv); counters={"application_body_bytes":0,"network_requests_started":0}
    try:
        candidate=validate_candidate(args.candidate)
        if args.validate_candidate:
            print(json.dumps({"network_requests":0,"source_rows":0,"state":"READY_AT_PRIMARY_LITERATURE_BOUNDARY"},sort_keys=True)); return 0
        if None in (args.permit,args.standing_authorization,args.autonomy_state,args.output_directory):
            raise RecoveryValidationError("GOVERNED_ARGUMENTS_REQUIRED")
        validate_runtime_invocation(candidate,executable=sys.executable,script_path=sys.argv[0],argument_vector=sys.argv[1:])
        from oc3lib.cross_id_formalism_recovery_governor import consume_permit, validate_permit
        validate_permit(args.permit,candidate_path=args.candidate,state_path=args.autonomy_state,
                        standing_authorization_path=args.standing_authorization)
        consume_permit(args.permit,candidate_path=args.candidate,state_path=args.autonomy_state,
            standing_authorization_path=args.standing_authorization,
            consumed_at_utc=datetime.now(timezone.utc).isoformat().replace("+00:00","Z"))
        print(json.dumps(_acquire(candidate,args.output_directory,counters),sort_keys=True)); return 0
    except Exception as exc:
        print(json.dumps({"application_body_bytes":counters["application_body_bytes"],
            "error":getattr(exc,"code",str(exc)),"network_requests":counters["network_requests_started"],
            "state":"PRIMARY_EVIDENCE_ACQUISITION_BLOCKED"},sort_keys=True),file=sys.stderr); return 2

if __name__ == "__main__": raise SystemExit(main())
