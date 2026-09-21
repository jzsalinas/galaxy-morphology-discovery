#!/usr/bin/env python3
"""OC-3 DR9 resource-contract probe and future auxiliary acquisition CLI."""
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
from oc3lib.resource_contract import (
    ACQUISITION_CANDIDATE_VALID, ACQUISITION_EXPECTED_BODY_BYTES,
    ACQUISITION_STAGE_REQUEST_CAP, ACQUISITION_STAGE_RETRY_POOL,
    AUXILIARY_AUDIT_RELATIVE, AUXILIARY_CANDIDATE_RELATIVE,
    BRICKS_SHA256, FAILURE_TERMINAL, PROBE_ID, PROBE_MAX_BYTES, PROBE_MAX_REQUESTS,
    PROBE_PARTIAL, PROBE_SUCCESS, ResourceContractError, STAGE_ID,
    LiteralHTTPTransport, acquire_auxiliary, build_contract, dry_run,
    load_canonical_json, load_frozen_bricks, load_probe_binding, probe_contract,
    validate_acquisition_authorization, validate_acquisition_candidate, validate_fits_files,
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        prog="oc3_resource_contract.py",
        description="Closed OC-3 DR9 resource contract. Offline unless an explicit network mode is selected.")
    mode = result.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true",
                      help="serialize the exact unresolved inventory; zero network")
    mode.add_argument("--probe-resource-contract", action="store_true",
                      help="HEAD and bounded FITS-header ranges for one sealed literal binding")
    mode.add_argument("--acquire-auxiliary", action="store_true",
                      help="future 14-resource bulk path; requires separate authorization")
    mode.add_argument("--validate-auxiliary-candidate", action="store_true",
                      help="offline validation of the sealed 14-resource human-review candidate")
    result.add_argument("--execute-network", action="store_true",
                        help="required for probe/acquisition; invalid with --dry-run")
    result.add_argument("--project", type=Path,
                        default=Path(__file__).resolve().parent.parent)
    result.add_argument("--bricks", type=Path)
    result.add_argument("--probe-binding", type=Path)
    result.add_argument("--contract-manifest", type=Path)
    result.add_argument("--candidate", type=Path)
    result.add_argument("--authorization", type=Path)
    result.add_argument("--audit-directory", type=Path)
    result.add_argument("--log", type=Path,
                        help="compact append-only run log (network modes only)")
    result.add_argument("--resume", action="store_true",
                        help="requires a separately sealed resume authorization")
    result.add_argument("--max-requests", type=int, default=PROBE_MAX_REQUESTS)
    result.add_argument("--max-bytes", type=int, default=PROBE_MAX_BYTES)
    result.add_argument("--stage-request-cap", type=int, default=ACQUISITION_STAGE_REQUEST_CAP)
    result.add_argument("--stage-retry-request-pool", type=int, default=ACQUISITION_STAGE_RETRY_POOL)
    result.add_argument("--expected-body-bytes", type=int, default=ACQUISITION_EXPECTED_BODY_BYTES)
    return result


def _write_once(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); data = canonical(value) + b"\n"
    if path.exists():
        if path.read_bytes() != data: raise ResourceContractError("IMMUTABLE_AUDIT_CONFLICT")
        return
    with path.open("xb") as handle: handle.write(data); handle.flush(); os.fsync(handle.fileno())


def _log(path: Path | None, value: dict) -> None:
    if path is None: return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab") as handle: handle.write(canonical(value) + b"\n"); handle.flush(); os.fsync(handle.fileno())


def _production_paths(args):
    project = args.project.resolve()
    bricks = args.bricks or project / "oc3/INPUTS/OC3_DEVELOPMENT_BRICKS.csv"
    default_audit = (project / AUXILIARY_AUDIT_RELATIVE if args.acquire_auxiliary
                     else project / f"oc3/resource_contract/{PROBE_ID}")
    audit = args.audit_directory or default_audit
    return project, bricks.resolve(), audit.resolve()


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    transport = None
    try:
        project, bricks_path, audit = _production_paths(args)
        if args.dry_run:
            if (args.execute_network or args.resume or args.probe_binding or args.candidate or
                    args.authorization or args.log):
                raise ResourceContractError("DRY_RUN_NETWORK_OR_AUTHORIZATION_FORBIDDEN")
            print(json.dumps(dry_run(bricks_path, project), sort_keys=True, separators=(",", ":")))
            return 0
        if args.validate_auxiliary_candidate:
            if (args.execute_network or args.resume or args.probe_binding or args.authorization or args.log or
                    args.contract_manifest is None or args.candidate is None):
                raise ResourceContractError("CANDIDATE_VALIDATION_ARGUMENTS_INVALID")
            contract_path = args.contract_manifest.resolve()
            candidate_path = args.candidate.resolve()
            if (contract_path != project / "oc3/resource_contract/OC3-RESOURCE-CONTRACT-PROBE-002/RESOURCE_CONTRACT_RESOLVED.json" or
                    candidate_path != project / AUXILIARY_CANDIDATE_RELATIVE):
                raise ResourceContractError("CANDIDATE_VALIDATION_PATH_INVALID")
            contract = load_canonical_json(contract_path)
            candidate = load_canonical_json(candidate_path)
            validate_acquisition_candidate(candidate, contract, project)
            result = {"stage_id": STAGE_ID, "state": ACQUISITION_CANDIDATE_VALID,
                      "resource_count": 14, "expected_body_bytes": ACQUISITION_EXPECTED_BODY_BYTES,
                      "primary_requests": 28, "stage_retry_request_pool": ACQUISITION_STAGE_RETRY_POOL,
                      "stage_request_cap": ACQUISITION_STAGE_REQUEST_CAP, "network_requests": 0}
            print(json.dumps(result, sort_keys=True, separators=(",", ":")))
            return 0
        if not args.execute_network: raise ResourceContractError("EXPLICIT_NETWORK_CAPABILITY_REQUIRED")
        if args.probe_resource_contract:
            if args.max_requests <= 0 or args.max_requests > PROBE_MAX_REQUESTS or args.max_bytes <= 0 or args.max_bytes > PROBE_MAX_BYTES:
                raise ResourceContractError("RUNTIME_CAP_INCREASE_OR_INVALID")
            if args.resume: raise ResourceContractError("PROBE_HAS_NO_AUTOMATIC_RESUME")
            if args.probe_binding is None or args.contract_manifest or args.candidate or args.authorization:
                raise ResourceContractError("PROBE_ARGUMENTS_INVALID")
            base = build_contract(load_frozen_bricks(bricks_path))
            binding = load_probe_binding(args.probe_binding, base)
            transport = LiteralHTTPTransport(row["literal_url"] for row in binding["resources"])
            resolved, summary = probe_contract(base, binding, transport,
                                               max_requests=args.max_requests,
                                               max_bytes=args.max_bytes)
            if summary["network_requests"] > args.max_requests or summary["network_bytes"] > args.max_bytes:
                raise ResourceContractError("RUNTIME_CAP_EXCEEDED")
            _write_once(audit / "RESOURCE_CONTRACT_RESOLVED.json", resolved)
            _write_once(audit / "RESOURCE_CONTRACT_PROBE_EVIDENCE.json", summary)
            terminal = {"stage_id": PROBE_ID, "state": PROBE_SUCCESS,
                        "network_requests": summary["network_requests"],
                        "network_bytes": summary["network_bytes"], "science_pixels_decoded": 0}
            _write_once(audit / "RESOURCE_CONTRACT_PROBE_TERMINAL.json", terminal)
            _log(args.log, terminal)
            print(json.dumps(terminal, sort_keys=True, separators=(",", ":"))); return 0
        if args.acquire_auxiliary:
            if (args.contract_manifest is None or args.candidate is None or
                    args.authorization is None or args.probe_binding):
                raise ResourceContractError("ACQUISITION_ARGUMENTS_INVALID")
            if ((args.stage_request_cap, args.stage_retry_request_pool, args.expected_body_bytes) !=
                    (ACQUISITION_STAGE_REQUEST_CAP, ACQUISITION_STAGE_RETRY_POOL,
                     ACQUISITION_EXPECTED_BODY_BYTES)):
                raise ResourceContractError("ACQUISITION_STAGE_CAP_MISMATCH")
            contract_path = args.contract_manifest.resolve(); candidate_path = args.candidate.resolve()
            if (contract_path != project / "oc3/resource_contract/OC3-RESOURCE-CONTRACT-PROBE-002/RESOURCE_CONTRACT_RESOLVED.json" or
                    candidate_path != project / AUXILIARY_CANDIDATE_RELATIVE or
                    audit != project / AUXILIARY_AUDIT_RELATIVE or
                    args.log is None or args.log.resolve() != audit / "AUXILIARY_RUN.log"):
                raise ResourceContractError("ACQUISITION_PATH_BINDING_INVALID")
            contract = load_canonical_json(contract_path)
            candidate = load_canonical_json(candidate_path)
            validate_acquisition_candidate(candidate, contract, project)
            authorization_path = args.authorization.resolve()
            expected_first_authorization = Path(candidate["final_authorization_path"])
            if ((not args.resume and authorization_path != expected_first_authorization) or
                    (args.resume and authorization_path == expected_first_authorization)):
                raise ResourceContractError("ACQUISITION_AUTHORIZATION_PATH_INVALID")
            authorization = load_canonical_json(authorization_path)
            validate_acquisition_authorization(
                authorization, candidate, candidate_path=candidate_path, resume=args.resume)
            urls = [r["literal_url"] for r in candidate["resources"]]
            transport = LiteralHTTPTransport(urls)
            terminal = acquire_auxiliary(
                contract, candidate, authorization, transport, audit, validate_fits_files,
                project=project, candidate_path=candidate_path, resume=args.resume)
            _log(args.log, terminal)
            print(json.dumps(terminal, sort_keys=True, separators=(",", ":"))); return 0
        raise ResourceContractError("MODE_INVALID")
    except ResourceContractError as exc:
        state = PROBE_PARTIAL if args.probe_resource_contract else FAILURE_TERMINAL
        terminal = {"error": exc.code, "stage_id": PROBE_ID if args.probe_resource_contract else STAGE_ID,
                    "state": state}
        if transport is not None:
            terminal["network_requests_started"] = transport.requests_started
            terminal["network_bytes_observed"] = transport.body_bytes_observed
        try:
            if args.probe_resource_contract:
                _, _, audit = _production_paths(args)
                _write_once(audit / "RESOURCE_CONTRACT_PROBE_TERMINAL.json", terminal)
            _log(args.log, terminal)
        except (OSError, ResourceContractError):
            pass
        print(json.dumps(terminal, sort_keys=True, separators=(",", ":")), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
