#!/usr/bin/env python3
"""Single frozen public-anonymous Data Lab acquisition worker."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True
for _key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_key] = "1"

from oc3lib.cross_observer_grouping import PROJECT, load_canonical_json, sealed, write_json_immutable
from oc3lib.source_metadata_acquisition_pilot import (
    AcquisitionError, AcquisitionSequence, Accounting, BODY_CAP, HOLDOUT_GUARD_UNION, MAX_SOURCE_ROWS_PER_DOMAIN,
    OUTCOMES, REQUEST_ORDER, RESPONSE_CAPS, TARGET_GUARD_UNION, bounded_get, frame_support,
    load_text, parse_counts, parse_schema, terminal_outcome_for, validate_source_rows,
)
from oc3lib.source_metadata_acquisition_pilot_validation import (
    CANDIDATE, FRAME, FRAME_SHA256, consume_worker_capability, validate_candidate,
    validate_worker_capability, validate_worker_invocation,
)


def _terminal(candidate, accounting, outcome, error_code, holdout_counts=0, holdout_rows=0,
              holdout_cells=0):
    counters = {key: 0 for key in (
        "combined_tractor_accesses", "crossmatch_operations", "q3c_operations", "cone_search_operations",
        "matching_operations", "angular_separation_operations", "radius_query_operations",
        "search_bound_selections", "scientific_threshold_selections", "object_group_ids_created",
        "split_group_ids_created", "PHOTSYS_reads", "TYPE_values_read", "DCHISQ_values_read",
        "Sersic_shape_values_read", "photometric_values_read", "photoz_values_read", "image_pixels_read",
        "morphology_accesses", "label_accesses", "model_operations", "training_operations",
        "embedding_operations", "clustering_operations", "panel_v3_operations", "p1_operations",
    )}
    counters.update({"holdout_count_requests": holdout_counts, "holdout_row_requests": holdout_rows,
                     "holdout_source_derived_cells_observed": holdout_cells,
                     "network_requests_started": accounting.requests_started, "retry_requests": 0})
    return sealed({"application_body_bytes_read": accounting.body_bytes_read,
        "error_code": error_code, "scope": candidate["scope"], "stage_id": candidate["stage_id"],
        "state": outcome, "counters": counters})


def _write_text_immutable(path: Path, text: str) -> None:
    data=text.encode("utf-8"); path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())


def execute(candidate: dict[str, object], output: Path) -> dict[str, object]:
    manifest = load_canonical_json(PROJECT / candidate["query_manifest"]["path"])
    resources = {row["id"]: row for row in manifest["resources"]}
    if tuple(resources) != REQUEST_ORDER:
        raise AcquisitionError("DATALAB_SCHEMA_MISMATCH")
    brick_ids, _, _ = frame_support(FRAME, FRAME_SHA256)
    raw = output / "RAW_IMMUTABLE"; raw.mkdir()
    ledger = output / "REQUEST_LEDGER"; ledger.mkdir()
    accounting = Accounting(); sequence = AcquisitionSequence()
    write_json_immutable(output / "DATALAB_SERVICE_CONTRACT.json",sealed({
        "anonymous_token_identity":"anonymous.0.0.anon_access","concurrency":1,
        "credential_file_reads":0,"redirects":0,"resume":False,"retries":0,
        "schema_version":"OC3_SOURCE_METADATA_ACQUISITION_SERVICE_CONTRACT_001",
        "service_endpoint":manifest["service_endpoint"],"timeout_seconds":300}))
    write_json_immutable(output / "QUERY_MANIFEST.json",sealed({
        "path":candidate["query_manifest"]["path"],"schema_version":"OC3_SOURCE_METADATA_ACQUISITION_QUERY_BINDING_001",
        "sha256":candidate["query_manifest"]["sha256"]}))

    def fetch(query_id: str) -> Path:
        resource = resources[query_id]
        path = raw / f"{query_id}.csv"
        bounded_get(query_id, resource["url"], RESPONSE_CAPS[query_id], path, accounting,
                    ledger_directory=ledger)
        return path

    outcome = "SOURCE_METADATA_ACQUISITION_INCONCLUSIVE"; error_code = None
    try:
        schema_path = fetch("schema")
        with load_text(schema_path) as stream:
            schema = parse_schema(stream)
        sequence.accept_schema(schema)
        schema_evidence = sealed({"row_count": 18, "schema_version":"OC3_SOURCE_METADATA_ACQUISITION_SCHEMA_EVIDENCE_001",
                                  "tables": schema})
        write_json_immutable(output / "SCHEMA_EVIDENCE.json", schema_evidence)

        counts = {}
        for domain in ("north", "south"):
            with load_text(fetch(f"{domain}_count")) as stream:
                counts[domain] = parse_counts(stream)
        totals = {domain: sum(values.values()) for domain, values in counts.items()}
        for domain in ("north", "south"):
            sequence.accept_count(domain, counts[domain])
        count_evidence = sealed({"count_cap_per_domain":MAX_SOURCE_ROWS_PER_DOMAIN,
            "per_brick":counts,"schema_version":"OC3_SOURCE_METADATA_ACQUISITION_COUNT_EVIDENCE_001",
            "totals":totals})
        write_json_immutable(output / "COUNT_EVIDENCE.json", count_evidence)
        if sequence.resource_bound:
            raise AcquisitionError("SOURCE_COUNT_RESOURCE_BOUND")
        if not sequence.rows_allowed():
            raise AcquisitionError("SOURCE_COUNT_ROW_MISMATCH")

        row_evidence = {}
        for domain in ("north", "south"):
            with load_text(fetch(f"{domain}_rows")) as stream:
                row_evidence[domain] = validate_source_rows(stream, counts[domain], brick_ids)
        row_evidence = sealed({"domains":row_evidence,
            "schema_version":"OC3_SOURCE_METADATA_ACQUISITION_ROW_INTEGRITY_001"})
        write_json_immutable(output / "SOURCE_ROW_INTEGRITY.json", row_evidence)
        outcome = "SOURCE_METADATA_ACQUISITION_COMPLETED"
    except AcquisitionError as exc:
        error_code = exc.code; outcome = terminal_outcome_for(exc.code)
    except Exception:
        error_code = "WORKER_RUNTIME_FAILURE"; outcome = terminal_outcome_for(error_code)

    transport = sealed({"application_body_bytes_read":accounting.body_bytes_read,
        "network_requests_started":accounting.requests_started,"parent_body_cap":BODY_CAP,
        "records":accounting.records,"schema_version":"OC3_SOURCE_METADATA_ACQUISITION_TRANSPORT_EVIDENCE_001"})
    write_json_immutable(output / "TRANSPORT_EVIDENCE.json", transport)
    terminal = _terminal(candidate, accounting, outcome, error_code)
    write_json_immutable(output / "TERMINAL.json", terminal)
    _write_text_immutable(output / "FINAL_REPORT.md",
        "# OC3 Source-Metadata Acquisition Pilot Final Report\n\n"
        f"Outcome: `{outcome}`\n\nError code: `{error_code}`\n\n"
        f"Requests started: {accounting.requests_started}\n\n"
        f"Application body bytes read: {accounting.body_bytes_read}\n\n"
        "This terminal describes acquisition and integrity only. It makes no positional-topology or cross-observer identity claim.\n")
    return terminal


def parser():
    result = argparse.ArgumentParser(description="Frozen DR9 source-metadata acquisition worker")
    result.add_argument("--run-acquisition-worker", action="store_true", required=True)
    result.add_argument("--candidate", type=Path, default=CANDIDATE)
    result.add_argument("--output", type=Path, required=True)
    result.add_argument("--execution-capability", type=Path)
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.execution_capability is None:
            raise AcquisitionError("WORKER_EXECUTION_CAPABILITY_REQUIRED")
        candidate = validate_candidate(args.candidate)
        validate_worker_invocation(candidate,[sys.executable,sys.argv[0],*sys.argv[1:]])
        validate_worker_capability(args.execution_capability,candidate=candidate,candidate_path=args.candidate,
            output_directory=args.output)
        consume_worker_capability(args.execution_capability,candidate=candidate,candidate_path=args.candidate,
            output_directory=args.output)
        terminal = execute(candidate, args.output)
        print(json.dumps(terminal, sort_keys=True)); return 0
    except Exception as exc:
        print(json.dumps({"error":getattr(exc,"code",type(exc).__name__),"network_requests":0,
            "state":"WORKER_BLOCKED"},sort_keys=True),file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
