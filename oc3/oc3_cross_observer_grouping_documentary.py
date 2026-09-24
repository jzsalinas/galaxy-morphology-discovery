#!/usr/bin/env python3
"""Bounded documentary executor; import and validation perform zero network."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import urllib.request

sys.dont_write_bytecode = True
for _key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
             "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_key] = "1"

from oc3lib.cross_observer_grouping import PROJECT, load_canonical_json, sealed, write_json_immutable
from oc3lib.cross_observer_grouping_documentary_validation import (
    CANDIDATE, DocumentaryValidationError, validate_candidate, validate_runtime_invocation,
)


class RejectRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise DocumentaryValidationError("REDIRECT_FORBIDDEN")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Bounded OC3 cross-observer documentary feasibility action")
    modes = result.add_mutually_exclusive_group(required=True)
    modes.add_argument("--validate-candidate", action="store_true")
    modes.add_argument("--research-documentary-feasibility", action="store_true")
    result.add_argument("--candidate", type=Path, default=CANDIDATE)
    result.add_argument("--permit", type=Path)
    result.add_argument("--standing-authorization", type=Path)
    result.add_argument("--autonomy-state", type=Path)
    result.add_argument("--output-directory", type=Path)
    return result


def _read_bounded(response, cap: int, total_remaining: int,
                  counters: dict[str, int]) -> bytes:
    declared = response.headers.get("Content-Length")
    if declared is not None and (not declared.isdecimal() or int(declared) > cap or int(declared) > total_remaining):
        raise DocumentaryValidationError("RESOURCE_BODY_CAP_EXCEEDED")
    chunks, count = [], 0
    while True:
        chunk = response.read(min(65536, cap + 1 - count))
        if not chunk:
            break
        chunks.append(chunk); count += len(chunk)
        counters["application_body_bytes"] += len(chunk)
        if count > cap or count > total_remaining:
            raise DocumentaryValidationError("RESOURCE_BODY_CAP_EXCEEDED")
    return b"".join(chunks)


def _acquire(candidate: dict[str, object], output: Path,
             counters: dict[str, int]) -> dict[str, object]:
    manifest = load_canonical_json((PROJECT / candidate["resource_manifest"]["path"]).resolve())
    opener = urllib.request.build_opener(RejectRedirect)
    output.mkdir(parents=True, exist_ok=False)
    raw = output / "RAW_IMMUTABLE"; raw.mkdir()
    evidence, total = [], 0
    for resource in manifest["resources"]:
        request = urllib.request.Request(resource["url"], method="GET", headers={"User-Agent": "OC3-bounded-documentary/1"})
        counters["network_requests_started"] += 1
        response = opener.open(request, timeout=30)
        try:
            if response.status != 200 or response.geturl() != resource["url"]:
                raise DocumentaryValidationError("HTTP_IDENTITY_INVALID")
            content_type = response.headers.get_content_type()
            if content_type not in resource["accepted_content_types"]:
                raise DocumentaryValidationError("CONTENT_TYPE_INVALID")
            body = _read_bounded(response, resource["application_body_byte_cap"],
                                 12_582_912 - total, counters)
        finally:
            response.close()
        total += len(body)
        target = raw / f"{resource['id']}.body"
        target.write_bytes(body)
        evidence.append({"application_body_bytes": len(body), "content_type": content_type,
                         "final_url": resource["url"], "id": resource["id"],
                         "sha256": hashlib.sha256(body).hexdigest(), "status": 200})
    transport = sealed({"application_body_bytes": total, "network_requests": len(evidence),
                        "resources": evidence, "schema_version": "OC3_CROSS_OBSERVER_DOCUMENTARY_TRANSPORT_001"})
    write_json_immutable(output / "TRANSPORT_EVIDENCE.json", transport)
    claims = sealed({"claims": [{"claim": name, "classification": classification,
                    "status": "EVIDENCE_ACQUIRED_REQUIRES_EXACT_SEMANTIC_REVIEW"} for name, classification in (
                        ("CATALOG_SOURCE_IDENTITY", "OFFICIAL_PROVIDER_FACT"),
                        ("RESOLVED_CATALOG_SEMANTICS", "OFFICIAL_PROVIDER_FACT"),
                        ("REGIONAL_DATALAB_TABLES", "DATA_ACCESS_FACT"),
                        ("ASTROMETRIC_FIELD_SEMANTICS", "OFFICIAL_PROVIDER_FACT"),
                        ("CROSS_IDENTIFICATION_ASSUMPTIONS", "PRIMARY_LITERATURE_FORMALISM"),
                        ("BOUNDED_PILOT_WITHOUT_THRESHOLD", "UNRESOLVED"),
                    )], "schema_version": "OC3_CROSS_OBSERVER_DOCUMENTARY_CLAIM_MATRIX_001"})
    write_json_immutable(output / "CLAIM_MATRIX.json", claims)
    report = ("# Cross-Observer Grouping Documentary Feasibility\n\n"
              f"Acquired {len(evidence)} exact documentary/schema resources ({total} body bytes).\n\n"
              "The acquired bodies require a separate exact semantic review before a source-level pilot "
              "or matcher threshold can be specified. No source rows were read and no radius was selected.\n")
    report_path = output / "DOCUMENTARY_FEASIBILITY_REPORT.md"
    with report_path.open("x", encoding="utf-8") as stream:
        stream.write(report)
        stream.flush(); os.fsync(stream.fileno())
    terminal = sealed({"application_body_bytes_read": total,
                       "counters": {"network_requests_started": counters["network_requests_started"], "retry_requests": 0,
                           "PHOTSYS_reads": 0, "TYPE_values_read": 0, "DCHISQ_values_read": 0,
                           "Sersic_shape_values_read": 0, "photometric_values_read": 0,
                           "photoz_values_read": 0, "source_rows_read": 0, "image_pixels_read": 0,
                           "morphology_accesses": 0, "label_accesses": 0, "model_operations": 0,
                           "training_operations": 0, "embedding_operations": 0,
                           "clustering_operations": 0, "panel_v3_operations": 0, "p1_operations": 0},
                       "scope": candidate["scope"], "stage_id": candidate["stage_id"],
                       "state": "DOCUMENTARY_EVIDENCE_ACQUIRED_PENDING_OFFLINE_SEMANTIC_REVIEW"})
    write_json_immutable(output / "TERMINAL.json", terminal)
    return terminal


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    counters = {"application_body_bytes": 0, "network_requests_started": 0}
    try:
        candidate = validate_candidate(args.candidate)
        if args.validate_candidate:
            print(json.dumps({"network_requests": 0, "source_rows": 0,
                              "state": "READY_AT_DOCUMENTARY_RESEARCH_BOUNDARY"}, sort_keys=True))
            return 0
        if None in (args.permit, args.standing_authorization, args.autonomy_state, args.output_directory):
            raise DocumentaryValidationError("GOVERNED_ARGUMENTS_REQUIRED")
        validate_runtime_invocation(candidate, executable=sys.executable, script_path=sys.argv[0], argument_vector=sys.argv[1:])
        from oc3lib.cross_observer_grouping_governor import consume_permit, validate_permit
        validate_permit(args.permit, candidate_path=args.candidate, state_path=args.autonomy_state,
                        standing_authorization_path=args.standing_authorization)
        from datetime import datetime, timezone
        consume_permit(args.permit, candidate_path=args.candidate, state_path=args.autonomy_state,
                       standing_authorization_path=args.standing_authorization,
                       consumed_at_utc=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
        terminal = _acquire(candidate, args.output_directory, counters)
        print(json.dumps(terminal, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"application_body_bytes": counters["application_body_bytes"],
                          "error": getattr(exc, "code", str(exc)),
                          "network_requests": counters["network_requests_started"],
                          "state": "DOCUMENTARY_FEASIBILITY_BLOCKED"}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
