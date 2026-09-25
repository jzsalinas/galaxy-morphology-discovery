#!/usr/bin/env python3
"""Governed supervisor for the bounded DR9 source-metadata acquisition."""
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
for _key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_key] = "1"

from oc3lib.cross_observer_grouping import file_sha256, load_canonical_json, sealed, validate_sealed, write_json_immutable
from oc3lib.source_metadata_acquisition_pilot import OUTCOMES
from oc3lib.source_metadata_acquisition_pilot_validation import (
    CANDIDATE, create_worker_capability, validate_candidate, validate_invocation,
)

STREAM_CAPTURE_CAP = 262_144


def _utc():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class Capture:
    def __init__(self):
        self.data=bytearray(); self.total=0; self.digest=hashlib.sha256()
    def drain(self, stream):
        while True:
            chunk=stream.read(65_536)
            if not chunk: break
            self.total+=len(chunk); self.digest.update(chunk)
            if len(self.data)<STREAM_CAPTURE_CAP:
                self.data.extend(chunk[:STREAM_CAPTURE_CAP-len(self.data)])
    def evidence(self):
        return {"byte_count":self.total,"capture_cap_bytes":STREAM_CAPTURE_CAP,
            "captured_byte_count":len(self.data),"sha256":self.digest.hexdigest(),
            "snippet_utf8_replacement":bytes(self.data).decode("utf-8",errors="replace"),
            "truncated":self.total>STREAM_CAPTURE_CAP}


def run_child(command):
    before=resource.getrusage(resource.RUSAGE_CHILDREN); started=time.monotonic()
    process=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    stdout,stderr=Capture(),Capture(); threads=[threading.Thread(target=stdout.drain,args=(process.stdout,),daemon=True),threading.Thread(target=stderr.drain,args=(process.stderr,),daemon=True)]
    for thread in threads: thread.start()
    code=process.wait()
    for thread in threads: thread.join()
    process.stdout.close(); process.stderr.close()
    after=resource.getrusage(resource.RUSAGE_CHILDREN)
    return {"return_code":code,"terminating_signal":-code if code<0 else None,
        "wall_clock_seconds":round(time.monotonic()-started,9),"stdout":stdout.evidence(),"stderr":stderr.evidence(),
        "child_resource_usage":{"max_rss_kib_linux":int(after.ru_maxrss),
        "user_cpu_seconds_delta":max(0.0,after.ru_utime-before.ru_utime),
        "system_cpu_seconds_delta":max(0.0,after.ru_stime-before.ru_stime),
        "max_rss_note":"ru_maxrss maximum over completed children; KiB on Linux; not an OOM inference"}}


def run_worker(candidate, output, *, candidate_path, permit_path, standing_authorization_path,
               autonomy_state_path, permit_consumption_marker):
    """Launch exactly one bound worker and preserve bounded failure evidence."""
    output.mkdir(parents=True,exist_ok=False)
    write_json_immutable(output/"START_INTENT.json",sealed({"candidate_sha256":file_sha256(candidate_path),
        "created_output_before_worker":True,"schema_version":"OC3_SOURCE_METADATA_ACQUISITION_START_INTENT_001",
        "stage_id":candidate["stage_id"],"started_at_utc":_utc(),"worker_command_sha256":candidate["worker_command_sha256"]}))
    create_worker_capability(candidate=candidate,candidate_path=candidate_path,permit_path=permit_path,
        standing_authorization_path=standing_authorization_path,autonomy_state_path=autonomy_state_path,
        output_directory=output,permit_consumption_marker=permit_consumption_marker,issued_at_utc=_utc())
    child=run_child(candidate["worker_command"])
    terminal_path=output/"TERMINAL.json"
    if child["return_code"] != 0 or not terminal_path.is_file():
        failure=sealed({"child":child,"failure_code":"WORKER_RUNTIME_FAILURE","finished_at_utc":_utc(),
            "schema_version":"OC3_SOURCE_METADATA_ACQUISITION_SUPERVISOR_FAILURE_001",
            "stage_id":candidate["stage_id"],"terminal_present":terminal_path.is_file(),
            "worker_command_sha256":candidate["worker_command_sha256"]})
        write_json_immutable(output/"SUPERVISOR_FAILURE.json",failure)
        raise ValueError("WORKER_RUNTIME_FAILURE")
    terminal=validate_sealed(load_canonical_json(terminal_path))
    if terminal.get("state") not in OUTCOMES or terminal.get("stage_id")!=candidate["stage_id"] or terminal.get("scope")!=candidate["scope"]:
        failure=sealed({"child":child,"failure_code":"WORKER_TERMINAL_INVALID","finished_at_utc":_utc(),
            "schema_version":"OC3_SOURCE_METADATA_ACQUISITION_SUPERVISOR_FAILURE_001",
            "stage_id":candidate["stage_id"],"terminal_present":True,
            "worker_command_sha256":candidate["worker_command_sha256"]})
        write_json_immutable(output/"SUPERVISOR_FAILURE.json",failure)
        raise ValueError("WORKER_TERMINAL_INVALID")
    diagnostic=sealed({"child":child,"finished_at_utc":_utc(),"implementation_aggregate":candidate["implementation_aggregate"],
        "schema_version":"OC3_SOURCE_METADATA_ACQUISITION_EXECUTION_DIAGNOSTIC_001",
        "terminal_sha256":file_sha256(terminal_path),"worker_command_sha256":candidate["worker_command_sha256"]})
    write_json_immutable(output/"EXECUTION_DIAGNOSTIC.json",diagnostic)
    return terminal


def parser():
    result=argparse.ArgumentParser(description="Governed DR9 source-metadata acquisition supervisor")
    modes=result.add_mutually_exclusive_group(required=True)
    modes.add_argument("--validate-candidate",action="store_true")
    modes.add_argument("--acquire-source-metadata",action="store_true")
    result.add_argument("--candidate",type=Path,default=CANDIDATE)
    result.add_argument("--permit",type=Path); result.add_argument("--standing-authorization",type=Path)
    result.add_argument("--autonomy-state",type=Path); result.add_argument("--output-directory",type=Path)
    return result


def main(argv=None):
    args=parser().parse_args(argv)
    try:
        candidate=validate_candidate(args.candidate)
        if args.validate_candidate:
            print(json.dumps({"network_requests":0,"schema_rows_observed":0,"source_counts_observed":0,
                "source_rows_observed":0,"state":"READY_AT_PUBLIC_ANONYMOUS_DATALAB_ACQUISITION_BOUNDARY"},sort_keys=True)); return 0
        if None in (args.permit,args.standing_authorization,args.autonomy_state,args.output_directory):
            raise ValueError("GOVERNED_ARGUMENTS_REQUIRED")
        validate_invocation(candidate,[sys.executable,sys.argv[0],*sys.argv[1:]])
        from oc3lib.source_metadata_acquisition_pilot_governor import consume_permit,validate_permit
        validate_permit(args.permit,candidate_path=args.candidate,state_path=args.autonomy_state,
            standing_authorization_path=args.standing_authorization)
        consumption_marker=consume_permit(args.permit,candidate_path=args.candidate,state_path=args.autonomy_state,
            standing_authorization_path=args.standing_authorization,consumed_at_utc=_utc())
        terminal=run_worker(candidate,args.output_directory,candidate_path=args.candidate,permit_path=args.permit,
            standing_authorization_path=args.standing_authorization,autonomy_state_path=args.autonomy_state,
            permit_consumption_marker=consumption_marker)
        print(json.dumps(terminal,sort_keys=True)); return 0
    except Exception as exc:
        print(json.dumps({"error":getattr(exc,"code",str(exc)),"state":"SOURCE_METADATA_ACQUISITION_SUPERVISOR_BLOCKED"},sort_keys=True),file=sys.stderr); return 2


if __name__ == "__main__":
    raise SystemExit(main())
