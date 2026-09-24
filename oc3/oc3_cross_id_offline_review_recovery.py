#!/usr/bin/env python3
"""Permit-gated offline review of already bound cross-ID primary evidence."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
for _key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
             "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_key] = "1"

from oc3lib.core import canonical
from oc3lib.cross_id_offline_review_recovery import (
    MARKERS, NORMALIZATION_ALGORITHM, PROJECT, SCOPE, STAGE_ID,
    TOKENIZER_ALGORITHM, evaluate_all_markers, normalize_whitespace, sealed,
    sha256_bytes, terminal_outcome, write_json_immutable,
)
from oc3lib.cross_id_offline_review_recovery_validation import (
    CANDIDATE, RecoveryValidationError, validate_candidate,
    validate_runtime_invocation,
)


class CitationParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.values: dict[str, list[str]] = {}

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag != "meta":
            return
        item = dict(attrs)
        name = item.get("name", "")
        if name.startswith("citation_"):
            self.values.setdefault(name, []).append(item.get("content", ""))


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Offline cross-ID review recovery")
    modes = result.add_mutually_exclusive_group(required=True)
    modes.add_argument("--validate-candidate", action="store_true")
    modes.add_argument("--review-primary-evidence", action="store_true")
    result.add_argument("--candidate", type=Path, default=CANDIDATE)
    result.add_argument("--permit", type=Path)
    result.add_argument("--standing-authorization", type=Path)
    result.add_argument("--autonomy-state", type=Path)
    result.add_argument("--output-directory", type=Path)
    return result


def _bound_paths(candidate: dict[str, object]) -> dict[str, Path]:
    return {Path(item["path"]).name: PROJECT / item["path"]
            for item in candidate["input_bindings"]}


def _extract(candidate: dict[str, object]) -> tuple[dict[str, list[str]], str, str, str]:
    paths = _bound_paths(candidate)
    html = paths["BUDAVARI_SZALAY_ARXIV_ABSTRACT_V3.body"].read_text(errors="strict")
    citations = CitationParser()
    citations.feed(html)
    required = {
        "citation_title": "Probabilistic Cross-Identification of Astronomical Sources",
        "citation_arxiv_id": "0707.1611",
        "citation_online_date": "2008/02/11",
    }
    for key, expected in required.items():
        if expected not in citations.values.get(key, []):
            raise RecoveryValidationError("ARXIV_IDENTITY_MISMATCH")
    if citations.values.get("citation_author", []) != ["Budavari, Tamas", "Szalay, Alexander S."]:
        raise RecoveryValidationError("ARXIV_AUTHORSHIP_MISMATCH")
    pdf = paths["BUDAVARI_SZALAY_ASPC_394_165_DIRECT_PUBLISHER.body"]
    run = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], check=True,
                         capture_output=True, text=True)
    raw = run.stdout
    normalized = normalize_whitespace(raw)
    version = subprocess.run(["pdftotext", "-v"], check=True, capture_output=True,
                             text=True).stderr.splitlines()[0]
    return citations.values, raw, normalized, version


def _claims(marker_rows: list[dict[str, object]]) -> tuple[list[dict[str, str]], str, str]:
    if not all(row["matched"] for row in marker_rows):
        claim9 = claim10 = "INCONCLUSIVE"
    else:
        claim9 = claim10 = "SUPPORTED"
    claims = [
        ("A_BAYESIAN_PROBABILISTIC", "FORMALISM_FACT", "Bayesian and probabilistic markers."),
        ("B_SAME_SOURCE_VS_SEPARATE_SOURCE", "FORMALISM_FACT", "Same-source and separate-source hypotheses."),
        ("C_SYMMETRY", "FORMALISM_FACT", "Order dependence is criticized and symmetric algorithms are required."),
        ("D_POSITIONAL_UNCERTAINTY_MODEL", "FORMALISM_FACT", "Probability-density and covariance evidence."),
        ("E_KNOWN_POSITIONAL_UNCERTAINTIES", "FORMALISM_FACT", "Quoted positional precision enters the formalism."),
        ("F_CIRCULAR_GAUSSIAN_SPHERICAL_APPROXIMATIONS", "FORMALISM_FACT", "Normal and spherical-normal evidence."),
        ("G_PRIORS", "FORMALISM_FACT", "Prior and posterior probability evidence."),
        ("H_POINT_SOURCE_ASSUMPTION", "FORMALISM_FACT", "Explicit astronomical point-source scope."),
        ("I_OPTIONAL_PHYSICAL_PROPERTIES", "FORMALISM_FACT", "Optional physical-properties evidence."),
        ("J_EXTENDED_DR9_GALAXY_TRANSFER_LIMIT", "PROJECT_SUITABILITY_INFERENCE", "Direct transfer to extended DR9 galaxies is not demonstrated."),
        ("K_NO_ARBITRARY_MATCH_DECISION_RADIUS_REQUIREMENT", "FORMALISM_FACT", "Search-radius mechanics remain distinct from a universal match-decision radius."),
    ]
    rows = [{"claim_id": ident,
             "decision": "INCONCLUSIVE" if ident == "J_EXTENDED_DR9_GALAXY_TRANSFER_LIMIT" else claim9,
             "epistemic_layer": layer, "evidence": evidence}
            for ident, layer, evidence in claims]
    return rows, claim9, claim10


def review(candidate: dict[str, object], output: Path) -> dict[str, object]:
    metadata, raw, normalized, tool = _extract(candidate)
    marker_rows = evaluate_all_markers(raw, MARKERS)
    subclaims, claim9, claim10 = _claims(marker_rows)
    outcome = terminal_outcome(claim9, claim10)
    output.mkdir(parents=True, exist_ok=False)
    write_json_immutable(output / "EXTRACTION_PROVENANCE.json", sealed({
        "normalization_algorithm": NORMALIZATION_ALGORITHM,
        "normalized_whitespace_sha256": sha256_bytes(normalized.encode("utf-8")),
        "pdftotext_command": ["pdftotext", "-layout", "BOUND_ASP_PDF", "-"],
        "pdftotext_version": tool,
        "raw_pdftotext_sha256": sha256_bytes(raw.encode("utf-8")),
        "schema_version": "OC3_CROSS_ID_OFFLINE_REVIEW_RECOVERY_EXTRACTION_PROVENANCE_001",
        "tokenizer_algorithm": TOKENIZER_ALGORITHM,
    }))
    write_json_immutable(output / "MARKER_EVIDENCE.json", sealed({
        "all_required_markers_matched": all(row["matched"] for row in marker_rows),
        "arxiv_identity": {"arxiv_id": "0707.1611", "version": "v3",
                           "authors": metadata["citation_author"],
                           "title": metadata["citation_title"][0]},
        "bibliographic_identity": {"series": "ASP Conference Series", "volume": 394,
                                   "first_page": 165, "year": 2008},
        "markers": marker_rows,
        "matcher": TOKENIZER_ALGORITHM,
        "schema_version": "OC3_CROSS_ID_OFFLINE_REVIEW_RECOVERY_MARKER_EVIDENCE_001",
    }))
    matrix = sealed({
        "claim_order": ["CROSS_IDENTIFICATION_FORMALISM_ASSUMPTIONS",
                        "BOUNDED_PILOT_SPECIFIABLE_WITHOUT_THRESHOLD"],
        "claims": [
            {"claim_id": "CROSS_IDENTIFICATION_FORMALISM_ASSUMPTIONS", "decision": claim9,
             "epistemic_layer": "FORMALISM_FACT",
             "reason": "A-I and K require all frozen lexical evidence; the point-source scope and unresolved extended-source transfer are retained."},
            {"claim_id": "BOUNDED_PILOT_SPECIFIABLE_WITHOUT_THRESHOLD", "decision": claim10,
             "epistemic_layer": "PROJECT_SUITABILITY_INFERENCE",
             "reason": "Evaluated after Claim 9; a future descriptive pilot would not declare equivalence and selects neither bound nor threshold."},
        ],
        "extended_source_transfer": "NOT_DEMONSTRATED",
        "formalism_subclaims": subclaims,
        "schema_version": "OC3_CROSS_ID_OFFLINE_REVIEW_RECOVERY_CLAIM_MATRIX_001",
        "search_bound_selected": False,
        "scientific_threshold_selected": False,
    })
    write_json_immutable(output / "CLAIM_MATRIX.json", matrix)
    (output / "REVIEW_REPORT.md").write_text(
        "# Cross-ID Offline Review Recovery\n\n"
        f"Claim 9: `{claim9}`. Claim 10: `{claim10}`. Terminal recommendation: `{outcome}`.\n\n"
        "The review used only the four bound local inputs and one uniform exact lexical-token matcher. "
        "Direct transfer from a point-source formalism to extended DR9 galaxies remains unproven. "
        "No matching, search bound, scientific threshold, source row, network request, morphology, Panel V3 or P1 operation occurred.\n"
    )
    counters = {key: 0 for key in (
        "network_requests_started", "retry_requests", "PHOTSYS_reads", "TYPE_values_read",
        "DCHISQ_values_read", "Sersic_shape_values_read", "photometric_values_read",
        "photoz_values_read", "source_rows_read", "image_pixels_read", "morphology_accesses",
        "label_accesses", "model_operations", "training_operations", "embedding_operations",
        "clustering_operations", "panel_v3_operations", "p1_operations", "network_requests",
        "matching_operations", "search_bound_selections", "scientific_threshold_selections")}
    terminal = sealed({"application_body_bytes_read": 0, "claim_9_decision": claim9,
                       "claim_10_decision": claim10, "counters": counters, "scope": SCOPE,
                       "stage_id": STAGE_ID, "state": "OFFLINE_REVIEW_RECOVERY_COMPLETED",
                       "terminal_recommendation": outcome})
    write_json_immutable(output / "TERMINAL.json", terminal)
    return terminal


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        candidate = validate_candidate(args.candidate)
        if args.validate_candidate:
            print(json.dumps({"body_bytes": 0, "network_requests": 0, "source_rows": 0,
                              "state": "READY_AT_OFFLINE_REVIEW_RECOVERY_BOUNDARY"}, sort_keys=True))
            return 0
        if None in (args.permit, args.standing_authorization, args.autonomy_state, args.output_directory):
            raise RecoveryValidationError("GOVERNED_ARGUMENTS_REQUIRED")
        validate_runtime_invocation(candidate, executable=sys.executable, script_path=sys.argv[0],
                                    argument_vector=sys.argv[1:])
        from oc3lib.cross_id_offline_review_recovery_governor import consume_permit, validate_permit
        validate_permit(args.permit, candidate_path=args.candidate, state_path=args.autonomy_state,
                        standing_authorization_path=args.standing_authorization)
        consume_permit(args.permit, candidate_path=args.candidate, state_path=args.autonomy_state,
                       standing_authorization_path=args.standing_authorization,
                       consumed_at_utc=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
        print(json.dumps(review(candidate, args.output_directory), sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"error": getattr(exc, "code", str(exc)), "network_requests": 0,
                          "source_rows": 0, "state": "OFFLINE_REVIEW_RECOVERY_BLOCKED"},
                         sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
