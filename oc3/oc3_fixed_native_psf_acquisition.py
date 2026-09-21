#!/usr/bin/env python3
"""CLI for offline review and separately authorized native+PSF acquisition."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True
for _key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
             "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_key] = "1"

from oc3lib.core import canonical
from oc3lib.fixed_native_psf_acquisition import (
    AUDIT_RELATIVE, AUTHORIZATION_RELATIVE, CANDIDATE_RELATIVE,
    ClosedAcquisitionTransport,
    FIXED_BODY_BYTES, PARTIAL, PRIMARY_REQUESTS, PSF_TOTAL_RESERVATION,
    RETRY_POOL, STAGE_ID, STAGE_REQUEST_CAP, NativePSFAcquisitionError,
    _canonical_load, run_acquisition, validate_authorization,
    validate_candidate, validate_candidate_offline,
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        prog="oc3_fixed_native_psf_acquisition.py",
        description=("Closed acquisition of 12 fixed native products and 18 bundled PSF "
                     "responses; offline candidate validation by default."))
    mode = result.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-candidate", action="store_true",
                      help="validate the prospective candidate with zero network")
    mode.add_argument("--acquire", action="store_true",
                      help="execute only with a separate final human authorization")
    result.add_argument("--execute-network", action="store_true")
    result.add_argument("--project", type=Path,
                        default=Path(__file__).resolve().parent.parent)
    result.add_argument("--candidate", type=Path, required=True)
    result.add_argument("--authorization", type=Path)
    result.add_argument("--audit-directory", type=Path)
    result.add_argument("--log", type=Path)
    result.add_argument("--resume", action="store_true")
    result.add_argument("--primary-request-count", type=int, default=PRIMARY_REQUESTS)
    result.add_argument("--retry-pool", type=int, default=RETRY_POOL)
    result.add_argument("--stage-request-cap", type=int, default=STAGE_REQUEST_CAP)
    result.add_argument("--fixed-body-bytes", type=int, default=FIXED_BODY_BYTES)
    result.add_argument("--psf-body-cap", type=int, default=PSF_TOTAL_RESERVATION)
    return result


def _append_log(path: Path | None, value: dict) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab") as handle:
        handle.write(canonical(value) + b"\n")
        handle.flush()
        os.fsync(handle.fileno())


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    transport = None
    try:
        project = args.project.resolve()
        candidate_path = args.candidate.resolve()
        if candidate_path != project / CANDIDATE_RELATIVE:
            raise NativePSFAcquisitionError("CANDIDATE_PATH_NOT_CANONICAL")
        caps = (args.primary_request_count, args.retry_pool, args.stage_request_cap,
                args.fixed_body_bytes, args.psf_body_cap)
        expected_caps = (PRIMARY_REQUESTS, RETRY_POOL, STAGE_REQUEST_CAP,
                         FIXED_BODY_BYTES, PSF_TOTAL_RESERVATION)
        if caps != expected_caps:
            raise NativePSFAcquisitionError("RUNTIME_CAP_MISMATCH")
        if args.validate_candidate:
            if (args.execute_network or args.authorization or args.audit_directory or
                    args.log or args.resume):
                raise NativePSFAcquisitionError("OFFLINE_VALIDATION_ARGUMENT_INVALID")
            result = validate_candidate_offline(candidate_path, project)
            print(json.dumps(result, sort_keys=True, separators=(",", ":")))
            return 0
        if args.resume:
            raise NativePSFAcquisitionError("SEPARATE_RESUME_AUTHORIZATION_REQUIRED")
        if not args.execute_network:
            raise NativePSFAcquisitionError("EXPLICIT_NETWORK_CAPABILITY_REQUIRED")
        if args.authorization is None:
            raise NativePSFAcquisitionError("FINAL_AUTHORIZATION_REQUIRED")
        authorization_path = args.authorization.resolve()
        if authorization_path != project / AUTHORIZATION_RELATIVE:
            raise NativePSFAcquisitionError("AUTHORIZATION_PATH_NOT_CANONICAL")
        audit = (args.audit_directory or project / AUDIT_RELATIVE).resolve()
        if audit != project / AUDIT_RELATIVE:
            raise NativePSFAcquisitionError("AUDIT_PATH_NOT_CANONICAL")
        if args.log is None or args.log.resolve() != audit / "ACQUISITION_RUN.log":
            raise NativePSFAcquisitionError("LOG_PATH_NOT_CANONICAL")
        candidate = _canonical_load(candidate_path)
        validate_candidate(candidate, project)
        authorization = _canonical_load(authorization_path)
        validate_authorization(authorization, candidate, candidate_path)
        fixed_urls = [row["literal_url"] for row in candidate["fixed_native_resources"]]
        psf_urls = [row["literal_url"] for row in candidate["psf_transport_resources"]]
        transport = ClosedAcquisitionTransport(fixed_urls, psf_urls)
        terminal = run_acquisition(candidate, authorization, transport, audit,
                                   candidate_path=candidate_path)
        _append_log(args.log, terminal)
        print(json.dumps(terminal, sort_keys=True, separators=(",", ":")))
        return 0
    except NativePSFAcquisitionError as exc:
        terminal = {"stage_id": STAGE_ID, "state": PARTIAL, "error": exc.code,
                    "resource_id": exc.resource_id,
                    "network_requests_started": getattr(transport, "requests_started", 0),
                    "network_bytes_observed": getattr(transport, "body_bytes_observed", 0)}
        print(json.dumps(terminal, sort_keys=True, separators=(",", ":")),
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
