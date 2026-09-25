#!/usr/bin/env python3
"""Bounded worker for the first technical response diagnostic."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import urllib.request

sys.dont_write_bytecode = True

from oc3lib.cross_observer_grouping import PROJECT, sealed, write_json_immutable
from oc3lib.source_metadata_acquisition_pilot import RejectRedirect, SCHEMA_QUERY, frozen_headers, query_url
from oc3lib.source_metadata_recovery_governor import (
    STATE, STANDING_AUTHORIZATION, consume_worker_capability, utc_now,
    validate_candidate, validate_worker_capability,
)
from recovery_adapters.source_metadata.technical_response_diagnostic import BODY_CAP, classify_representation


def parser():
    result = argparse.ArgumentParser()
    result.add_argument("--run-recovery-worker", action="store_true", required=True)
    result.add_argument("--candidate", type=Path, required=True)
    result.add_argument("--permit", type=Path, required=True)
    result.add_argument("--standing-authorization", type=Path, default=STANDING_AUTHORIZATION)
    result.add_argument("--state", type=Path, default=STATE)
    result.add_argument("--output", type=Path, required=True)
    result.add_argument("--execution-capability", type=Path, required=True)
    return result


def execute_diagnostic(candidate, output):
    intent = output / "REQUEST_INTENT.json"
    url = query_url(SCHEMA_QUERY)
    write_json_immutable(intent, sealed({"literal_url": url, "query_id": "schema",
        "request_class": "TECHNICAL", "schema_version": "OC3_SOURCE_METADATA_TECHNICAL_REQUEST_INTENT_001",
        "started_at_utc": utc_now()}))
    opener = urllib.request.build_opener(RejectRedirect())
    request = urllib.request.Request(url, headers=frozen_headers(), method="GET")
    body = b""; content_type = None; status = None; failure = None
    try:
        response = opener.open(request, timeout=300)
        status = response.getcode(); content_type = response.headers.get("Content-Type", "")
        body = response.read(BODY_CAP + 1)
        if len(body) > BODY_CAP:
            raise ValueError("TECHNICAL_DIAGNOSTIC_BODY_CAP_EXCEEDED")
        classification = classify_representation(content_type, body)
    except Exception as exc:
        classification = None; failure = getattr(exc, "code", type(exc).__name__)
    raw = output / "RAW_IMMUTABLE"; raw.mkdir()
    with (raw / "schema_response.body").open("xb") as stream:
        stream.write(body); stream.flush(); os.fsync(stream.fileno())
    terminal = sealed({"application_body_bytes_read": len(body), "diagnostic_class": classification,
        "failure_class": "TECHNICAL_DIAGNOSTIC_CLASSIFIED" if classification else "DATALAB_TRANSPORT_FAILURE",
        "http_status": status, "network_requests_started": 1, "request_class": "TECHNICAL",
        "response_body_sha256": hashlib.sha256(body).hexdigest(), "response_content_type": content_type,
        "schema_rows_observed": 0, "schema_version": "OC3_SOURCE_METADATA_TECHNICAL_DIAGNOSTIC_TERMINAL_001",
        "source_counts_observed": 0, "source_rows_observed": 0, "source_values_accepted": 0,
        "state": "ACTION_COMPLETED" if classification else "ACTION_RECOVERABLE_TECHNICAL_FAILURE",
        "technical_error": failure})
    write_json_immutable(output / "TERMINAL.json", terminal)
    return terminal


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        candidate = validate_candidate(args.candidate)
        if [sys.executable, sys.argv[0], *sys.argv[1:]] != candidate["worker_argv"]:
            raise ValueError("RECOVERY_WORKER_ARGV_MISMATCH")
        validate_worker_capability(capability_path=args.execution_capability,
            candidate_path=args.candidate, permit_path=args.permit,
            authorization_path=args.standing_authorization, state_path=args.state)
        consume_worker_capability(capability_path=args.execution_capability,
            candidate_path=args.candidate, consumed_at_utc=utc_now())
        terminal = execute_diagnostic(candidate, args.output)
        print(json.dumps(terminal, sort_keys=True)); return 0
    except Exception as exc:
        print(json.dumps({"error": getattr(exc, "code", str(exc)), "network_requests": 0,
            "state": "RECOVERY_WORKER_BLOCKED"}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
