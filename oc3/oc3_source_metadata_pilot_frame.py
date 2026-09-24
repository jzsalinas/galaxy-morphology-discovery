#!/usr/bin/env python3
"""Permit-gated, offline derivation of the frozen source-metadata pilot frame."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True
for _key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_key] = "1"

from oc3lib.cross_observer_grouping import PROJECT, sealed, write_json_immutable
from oc3lib.source_metadata_descriptive_pilot import (
    frame_payload, read_development_identities, reconstruct_global_view_both, select_frame,
)
from oc3lib.source_metadata_descriptive_pilot_validation import (
    CANDIDATE, FrameValidationError, validate_candidate, validate_runtime_invocation,
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Offline OC3 pilot frame derivation")
    mode = result.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-candidate", action="store_true")
    mode.add_argument("--derive-pilot-frame", action="store_true")
    result.add_argument("--candidate", type=Path, default=CANDIDATE)
    result.add_argument("--permit", type=Path)
    result.add_argument("--standing-authorization", type=Path)
    result.add_argument("--autonomy-state", type=Path)
    result.add_argument("--output-directory", type=Path)
    return result


def _fits_rows(path: Path, columns: tuple[str, ...]) -> list[dict[str, object]]:
    from astropy.io import fits
    with fits.open(path, memmap=False) as hdus:
        table = hdus[1].data
        available = set(table.names)
        if not set(columns).issubset(available):
            raise FrameValidationError("BOUND_FITS_COLUMNS_MISSING")
        return [{name: (value.decode("ascii") if isinstance(value, bytes) else value.item() if hasattr(value, "item") else value)
                 for name in columns for value in [row[name]]} for row in table]


def derive(candidate: dict[str, object], output: Path) -> dict[str, object]:
    paths = [PROJECT / item["path"] for item in candidate["input_bindings"]]
    root = _fits_rows(paths[0], ("BRICKNAME", "BRICKID", "BRICKROW", "RA", "DEC", "RA1", "RA2", "DEC1", "DEC2"))
    north = _fits_rows(paths[1], ("BRICKNAME", "BRICKID"))
    south = _fits_rows(paths[2], ("BRICKNAME", "BRICKID"))
    excluded = read_development_identities(paths[3])
    geometry, eligible = reconstruct_global_view_both(root, north, south, excluded)
    selections = select_frame(eligible, geometry)
    output.mkdir(parents=True, exist_ok=False)
    payload = frame_payload(selections, geometry,
                            {item["path"]: item["sha256"] for item in candidate["input_bindings"]})
    write_json_immutable(output / "PILOT_FRAME.json", sealed(payload))
    terminal = sealed({
        "application_body_bytes_read": 0,
        "counters": {key: 0 for key in (
            "network_requests_started", "retry_requests", "PHOTSYS_reads", "TYPE_values_read",
            "DCHISQ_values_read", "Sersic_shape_values_read", "photometric_values_read",
            "photoz_values_read", "image_pixels_read", "morphology_accesses", "label_accesses",
            "model_operations", "training_operations", "embedding_operations", "clustering_operations",
            "panel_v3_operations", "p1_operations", "matching_operations", "search_bound_selections",
            "scientific_threshold_selections", "object_group_ids_created", "split_group_ids_created",
            "combined_tractor_accesses", "server_crossmatch_operations", "radius_query_operations")},
        "eligible_identity_count": len(eligible), "network_requests": 0,
        "scope": candidate["scope"], "source_rows_read": 0, "stage_id": candidate["stage_id"],
        "state": "PILOT_FRAME_DERIVED", "target_count": 2, "reserved_holdout_count": 2,
    })
    write_json_immutable(output / "TERMINAL.json", terminal)
    return terminal


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        candidate = validate_candidate(args.candidate)
        if args.validate_candidate:
            print(json.dumps({"network_requests": 0, "source_rows": 0,
                              "state": "READY_AT_OFFLINE_PILOT_FRAME_BOUNDARY"}, sort_keys=True))
            return 0
        if None in (args.permit, args.standing_authorization, args.autonomy_state, args.output_directory):
            raise FrameValidationError("GOVERNED_ARGUMENTS_REQUIRED")
        validate_runtime_invocation(candidate, executable=sys.executable, script_path=sys.argv[0], argument_vector=sys.argv[1:])
        from oc3lib.source_metadata_descriptive_pilot_governor import consume_permit, validate_permit
        validate_permit(args.permit, candidate_path=args.candidate, state_path=args.autonomy_state,
                        standing_authorization_path=args.standing_authorization)
        consume_permit(args.permit, candidate_path=args.candidate, state_path=args.autonomy_state,
                       standing_authorization_path=args.standing_authorization,
                       consumed_at_utc=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
        print(json.dumps(derive(candidate, args.output_directory), sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"error": getattr(exc, "code", str(exc)), "network_requests": 0,
                          "source_rows": 0, "state": "PILOT_FRAME_DERIVATION_BLOCKED"}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
