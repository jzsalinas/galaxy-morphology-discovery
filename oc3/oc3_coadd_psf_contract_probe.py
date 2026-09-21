#!/usr/bin/env python3
"""CLI for the two-response DR9 coadd-PSF semantics probe."""
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

from oc3lib.coadd_psf_contract import (
    AUDIT_RELATIVE, BINDING_RELATIVE, MAX_NEW_REQUESTS, MAX_RESPONSE_BYTES,
    MAX_TOTAL_BODY_BYTES, PARTIAL, STAGE_ID, CoaddPSFContractError,
    LiteralPSFTransport, dry_run, load_probe_binding, run_probe,
)
from oc3lib.core import canonical


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        prog="oc3_coadd_psf_contract_probe.py",
        description=("Two-response, semantics-only DR9 coadd-PSF probe; "
                     "no image/invvar or morphology access."))
    mode = result.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true",
                      help="validate the sealed binding and print a zero-network plan")
    mode.add_argument("--execute-probe", action="store_true",
                      help="run the separately human-invoked two-response probe")
    result.add_argument("--execute-network", action="store_true",
                        help="mandatory only with --execute-probe")
    result.add_argument("--project", type=Path,
                        default=Path(__file__).resolve().parent.parent)
    result.add_argument("--binding", type=Path, required=True)
    result.add_argument("--audit-directory", type=Path)
    result.add_argument("--log", type=Path)
    result.add_argument("--max-new-requests", type=int, default=MAX_NEW_REQUESTS)
    result.add_argument("--max-response-bytes", type=int, default=MAX_RESPONSE_BYTES)
    result.add_argument("--max-total-bytes", type=int, default=MAX_TOTAL_BODY_BYTES)
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
    try:
        project = args.project.resolve()
        binding_path = args.binding.resolve()
        if binding_path != project / BINDING_RELATIVE:
            raise CoaddPSFContractError("PROBE_BINDING_PATH_NOT_CANONICAL")
        binding, _, _ = load_probe_binding(binding_path, project)
        supplied_caps = (args.max_new_requests, args.max_response_bytes,
                         args.max_total_bytes)
        frozen_caps = (MAX_NEW_REQUESTS, MAX_RESPONSE_BYTES, MAX_TOTAL_BODY_BYTES)
        if supplied_caps != frozen_caps:
            raise CoaddPSFContractError("PROBE_RUNTIME_CAP_MISMATCH")
        if args.dry_run:
            if args.execute_network or args.audit_directory or args.log:
                raise CoaddPSFContractError("DRY_RUN_NETWORK_OR_OUTPUT_FORBIDDEN")
            print(json.dumps(dry_run(binding, project), sort_keys=True,
                             separators=(",", ":")))
            return 0
        if not args.execute_network:
            raise CoaddPSFContractError("EXPLICIT_NETWORK_CAPABILITY_REQUIRED")
        audit = (args.audit_directory or project / AUDIT_RELATIVE).resolve()
        if audit != project / AUDIT_RELATIVE:
            raise CoaddPSFContractError("PROBE_AUDIT_PATH_NOT_CANONICAL")
        expected_log = audit / "PROBE_RUN.log"
        if args.log is None or args.log.resolve() != expected_log:
            raise CoaddPSFContractError("PROBE_LOG_PATH_NOT_CANONICAL")
        transport = LiteralPSFTransport(
            [row["literal_url"] for row in binding["representative_requests"]])
        terminal, success = run_probe(binding, transport, audit)
        _append_log(args.log, terminal)
        print(json.dumps(terminal, sort_keys=True, separators=(",", ":")))
        return 0 if success else 2
    except CoaddPSFContractError as exc:
        terminal = {"stage_id": STAGE_ID, "state": PARTIAL, "error": exc.code,
                    "network_requests_started": 0, "network_bytes_observed": 0,
                    "image_invvar_requests": 0, "morphology_accesses": 0,
                    "array_values_decoded": 0}
        print(json.dumps(terminal, sort_keys=True, separators=(",", ":")),
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

