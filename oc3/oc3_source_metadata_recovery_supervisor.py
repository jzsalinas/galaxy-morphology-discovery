#!/usr/bin/env python3
"""Single-action supervisor for the source-metadata recovery envelope."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True

from oc3lib.cross_observer_grouping import PROJECT, file_sha256, sealed, write_json_immutable
from oc3lib.source_metadata_recovery_governor import (
    STATE, STANDING_AUTHORIZATION, consume_permit, create_worker_capability,
    utc_now, validate_candidate, validate_permit,
)


def parser():
    result = argparse.ArgumentParser()
    result.add_argument("--execute-recovery-action", action="store_true", required=True)
    result.add_argument("--candidate", type=Path, required=True)
    result.add_argument("--permit", type=Path, required=True)
    result.add_argument("--standing-authorization", type=Path, default=STANDING_AUTHORIZATION)
    result.add_argument("--state", type=Path, default=STATE)
    result.add_argument("--output", type=Path, required=True)
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        candidate = validate_candidate(args.candidate)
        observed = [sys.executable, sys.argv[0], *sys.argv[1:]]
        if observed != candidate["command_argv"]:
            raise ValueError("RECOVERY_SUPERVISOR_ARGV_MISMATCH")
        validate_permit(permit_path=args.permit, candidate_path=args.candidate)
        permit_marker = consume_permit(permit_path=args.permit, candidate_path=args.candidate,
            consumed_at_utc=utc_now())
        args.output.mkdir(parents=True, exist_ok=False)
        write_json_immutable(args.output / "START_INTENT.json", sealed({
            "candidate_sha256": file_sha256(args.candidate), "permit_sha256": file_sha256(args.permit),
            "schema_version": "OC3_SOURCE_METADATA_RECOVERY_START_INTENT_001",
            "stage_id": candidate["stage_id"], "started_at_utc": utc_now()}))
        capability_path = PROJECT / candidate["worker_capability_path"]
        create_worker_capability(candidate_path=args.candidate, permit_path=args.permit,
            permit_marker=permit_marker, authorization_path=args.standing_authorization,
            state_path=args.state, capability_path=capability_path, issued_at_utc=utc_now())
        result = subprocess.run(candidate["worker_argv"], capture_output=True, text=True, check=False)
        write_json_immutable(args.output / "SUPERVISOR_RESULT.json", sealed({
            "return_code": result.returncode, "schema_version": "OC3_SOURCE_METADATA_RECOVERY_SUPERVISOR_RESULT_001",
            "stderr_sha256": __import__("hashlib").sha256(result.stderr.encode()).hexdigest(),
            "stdout_sha256": __import__("hashlib").sha256(result.stdout.encode()).hexdigest()}))
        if result.returncode != 0:
            raise ValueError("RECOVERY_WORKER_RUNTIME_FAILURE")
        print(result.stdout.strip()); return 0
    except Exception as exc:
        print(json.dumps({"error": getattr(exc, "code", str(exc)), "network_requests": 0,
            "state": "RECOVERY_SUPERVISOR_BLOCKED"}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
