#!/usr/bin/env python3
"""Permit-gated supervisor for one bounded pilot-frame recovery worker."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import threading
import time

sys.dont_write_bytecode = True
for _key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_key] = "1"

from oc3lib.core import canonical
from oc3lib.cross_observer_grouping import (
    file_sha256, load_canonical_json, sealed, sha256_bytes, validate_sealed, write_json_immutable,
)
from oc3lib.source_metadata_pilot_frame_recovery import (
    DIAGNOSTIC_SCHEMA, SCOPE, STAGE_ID, STREAM_CAPTURE_CAP, validate_frame_payload,
)
from oc3lib.source_metadata_pilot_frame_recovery_validation import (
    CANDIDATE, RecoveryValidationError, validate_candidate, validate_invocation,
)


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class BoundedCapture:
    def __init__(self, cap: int):
        self.cap = cap
        self.buffer = bytearray()
        self.total = 0
        self.digest = hashlib.sha256()

    def drain(self, stream) -> None:
        while True:
            chunk = stream.read(65536)
            if not chunk:
                break
            self.total += len(chunk)
            self.digest.update(chunk)
            if len(self.buffer) < self.cap:
                self.buffer.extend(chunk[:self.cap-len(self.buffer)])

    def evidence(self) -> dict[str, object]:
        return {"byte_count": self.total, "capture_cap_bytes": self.cap,
                "captured_byte_count": len(self.buffer), "sha256": self.digest.hexdigest(),
                "snippet_utf8_replacement": bytes(self.buffer).decode("utf-8", errors="replace"),
                "truncated": self.total > self.cap}


def run_child_once(command: list[str], *, cap: int = STREAM_CAPTURE_CAP) -> dict[str, object]:
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    started = time.monotonic()
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = BoundedCapture(cap), BoundedCapture(cap)
    threads = [threading.Thread(target=stdout.drain, args=(process.stdout,), daemon=True),
               threading.Thread(target=stderr.drain, args=(process.stderr,), daemon=True)]
    for thread in threads: thread.start()
    returncode = process.wait()
    for thread in threads: thread.join()
    process.stdout.close()
    process.stderr.close()
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    return {"return_code": returncode, "terminating_signal": -returncode if returncode < 0 else None,
            "wall_clock_seconds": round(time.monotonic()-started, 9),
            "child_resource_usage": {"max_rss_kib_linux": int(after.ru_maxrss),
                "user_cpu_seconds_delta": max(0.0, after.ru_utime-before.ru_utime),
                "system_cpu_seconds_delta": max(0.0, after.ru_stime-before.ru_stime),
                "max_rss_note": "ru_maxrss maximum over completed children; KiB on Linux; not an OOM inference"},
            "stdout": stdout.evidence(), "stderr": stderr.evidence()}


def _terminal(state: str, candidate: dict[str, object], diagnostic_sha: str) -> dict[str, object]:
    counters = {key: 0 for key in (
        "network_requests_started", "retry_requests", "network_requests", "source_rows_read", "datalab_accesses",
        "PHOTSYS_reads", "TYPE_values_read", "DCHISQ_values_read", "Sersic_shape_values_read",
        "photometric_values_read", "photoz_values_read", "image_pixels_read", "morphology_accesses",
        "label_accesses", "model_operations", "training_operations", "embedding_operations",
        "clustering_operations", "panel_v3_operations", "p1_operations", "matching_operations",
        "search_bound_selections", "scientific_threshold_selections", "object_group_ids_created",
        "split_group_ids_created", "combined_tractor_accesses", "server_crossmatch_operations",
        "radius_query_operations")}
    return sealed({"application_body_bytes_read": 0, "counters": counters,
        "diagnostic_sha256": diagnostic_sha, "scope": candidate["scope"],
        "stage_id": candidate["stage_id"], "state": state})


def supervise(candidate: dict[str, object], output: Path) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=False)
    started_at = _utc()
    write_json_immutable(output / "START_INTENT.json", sealed({
        "candidate_sha256": file_sha256(CANDIDATE), "created_output_before_worker": True,
        "schema_version": "OC3_FRAME_RECOVERY_START_INTENT_001", "stage_id": STAGE_ID,
        "started_at_utc": started_at, "worker_command_sha256": candidate["worker_command_sha256"]}))
    checkpoint = "START_INTENT_WRITTEN"
    child = run_child_once(list(candidate["worker_command"]), cap=candidate["stream_capture_cap_bytes"])
    checkpoint = "WORKER_COMPLETED"
    frame = output / "PILOT_FRAME.json"
    state = "PILOT_FRAME_WORKER_FAILED"
    validation_error = None
    if child["return_code"] == 0:
        try:
            value = validate_sealed(load_canonical_json(frame))
            validate_frame_payload(value, {item["path"]: item["sha256"] for item in candidate["input_bindings"]},
                                   candidate["implementation_aggregate"])
            state, checkpoint = "PILOT_FRAME_RECOVERED", "FRAME_VALIDATED"
        except Exception as exc:
            state = "PILOT_FRAME_OUTPUT_INVALID"
            validation_error = getattr(exc, "code", type(exc).__name__)
            checkpoint = "FRAME_VALIDATION_FAILED"
    diagnostic = sealed({"child": child, "diagnostic_schema": DIAGNOSTIC_SCHEMA,
        "finished_at_utc": _utc(), "implementation_aggregate": candidate["implementation_aggregate"],
        "phase_checkpoint_reached": checkpoint, "pilot_frame_exists": frame.is_file(),
        "schema_version": DIAGNOSTIC_SCHEMA, "started_at_utc": started_at,
        "terminal_exists_at_diagnostic_write": (output / "TERMINAL.json").is_file(),
        "validation_error": validation_error, "worker_command_sha256": candidate["worker_command_sha256"],
        "worker_implementation_aggregate": candidate["implementation_aggregate"]})
    write_json_immutable(output / "EXECUTION_DIAGNOSTIC.json", diagnostic)
    terminal = _terminal(state, candidate, file_sha256(output / "EXECUTION_DIAGNOSTIC.json"))
    write_json_immutable(output / "TERMINAL.json", terminal)
    return terminal


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Supervised offline pilot-frame recovery")
    modes = result.add_mutually_exclusive_group(required=True)
    modes.add_argument("--validate-candidate", action="store_true")
    modes.add_argument("--recover-pilot-frame", action="store_true")
    result.add_argument("--candidate", type=Path, default=CANDIDATE)
    result.add_argument("--permit", type=Path)
    result.add_argument("--standing-authorization", type=Path)
    result.add_argument("--autonomy-state", type=Path)
    result.add_argument("--output-directory", type=Path)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        candidate = validate_candidate(args.candidate)
        if args.validate_candidate:
            print(json.dumps({"network_requests":0, "real_frame_reads":0,
                              "state":"READY_AT_SUPERVISED_FRAME_RECOVERY_BOUNDARY"}, sort_keys=True))
            return 0
        if None in (args.permit, args.standing_authorization, args.autonomy_state, args.output_directory):
            raise RecoveryValidationError("GOVERNED_ARGUMENTS_REQUIRED")
        validate_invocation(candidate, [sys.executable, sys.argv[0], *sys.argv[1:]])
        from oc3lib.source_metadata_pilot_frame_recovery_governor import consume_permit, validate_permit
        validate_permit(args.permit, candidate_path=args.candidate, state_path=args.autonomy_state,
                        standing_authorization_path=args.standing_authorization)
        consume_permit(args.permit, candidate_path=args.candidate, state_path=args.autonomy_state,
                       standing_authorization_path=args.standing_authorization, consumed_at_utc=_utc())
        terminal = supervise(candidate, args.output_directory)
        print(json.dumps(terminal, sort_keys=True))
        return 0 if terminal["state"] == "PILOT_FRAME_RECOVERED" else 2
    except Exception as exc:
        print(json.dumps({"error":getattr(exc,"code",type(exc).__name__), "network_requests":0,
                          "state":"PILOT_FRAME_RECOVERY_SUPERVISOR_BLOCKED"}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
