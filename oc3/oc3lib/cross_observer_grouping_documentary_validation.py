"""Offline validator for the first cross-observer documentary action."""
from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .core import canonical
from .cross_observer_grouping import (
    PROJECT, file_sha256, load_canonical_json, sha256_bytes, validate_sealed,
)

STAGE_ID = "OC3-CROSS-OBSERVER-GROUPING-DOCUMENTARY-EVIDENCE-ACQUISITION-002"
SCOPE = "PUBLIC_DOCUMENTARY_AND_SCHEMA_METADATA_ONLY"
SPEC = PROJECT / "OC3_CROSS_OBSERVER_GROUPING_DOCUMENTARY_FEASIBILITY_SPEC_002.md"
MANIFEST = PROJECT / "oc3/INPUTS/OC3_CROSS_OBSERVER_GROUPING_DOCUMENTARY_RESOURCE_MANIFEST_002.json"
CANDIDATE = PROJECT / "oc3/INPUTS/OC3_CROSS_OBSERVER_GROUPING_DOCUMENTARY_FEASIBILITY_CANDIDATE_002.json"
RECEIPT = PROJECT / "oc3/INPUTS/OC3_CROSS_OBSERVER_GROUPING_DOCUMENTARY_FEASIBILITY_CANDIDATE_VALIDATION_002.json"
PERMIT = PROJECT / "oc3/CROSS_OBSERVER_GROUPING_AUTONOMY_PERMITS/OC3_CROSS_OBSERVER_GROUPING_DOCUMENTARY_FEASIBILITY_PERMIT_002.json"
AUTHORIZATION = PROJECT / "oc3/OC3_CROSS_OBSERVER_GROUPING_STANDING_AUTHORIZATION_002.json"
STATE = PROJECT / "oc3/OC3_CROSS_OBSERVER_GROUPING_AUTONOMY_STATE_002.json"
POLICY_MANIFEST = PROJECT / "oc3/INPUTS/OC3_CROSS_OBSERVER_GROUPING_POLICY_CORE_MANIFEST_002.json"
OUTPUT = PROJECT / "oc3/cross_observer_grouping/OC3-CROSS-OBSERVER-GROUPING-DOCUMENTARY-EVIDENCE-ACQUISITION-002"
EXECUTABLE = PROJECT / "oc3/.venv/bin/python"
SCRIPT = PROJECT / "oc3/oc3_cross_observer_grouping_documentary.py"

IMPLEMENTATION_FILES = (
    "OC3_CROSS_OBSERVER_GROUPING_DOCUMENTARY_FEASIBILITY_SPEC_002.md",
    "oc3/oc3_cross_observer_grouping_documentary.py",
    "oc3/oc3lib/cross_observer_grouping.py",
    "oc3/oc3lib/cross_observer_grouping_documentary_provenance.py",
    "oc3/oc3lib/cross_observer_grouping_documentary_validation.py",
)


class DocumentaryValidationError(Exception):
    pass


def implementation_aggregate() -> str:
    return sha256_bytes(canonical({path: file_sha256(PROJECT / path) for path in IMPLEMENTATION_FILES}))


def expected_command_argv() -> list[str]:
    return [
        str(EXECUTABLE), str(SCRIPT), "--acquire-documentary-evidence",
        "--candidate", str(CANDIDATE), "--permit", str(PERMIT),
        "--standing-authorization", str(AUTHORIZATION), "--autonomy-state", str(STATE),
        "--output-directory", str(OUTPUT),
    ]


def validate_manifest() -> dict[str, object]:
    manifest = validate_sealed(load_canonical_json(MANIFEST))
    required = {"application_body_byte_cap", "broad_crawling", "concurrency",
                "mirror_substitution", "network_request_cap", "resources", "retries",
                "schema_version", "sealed", "stage_id"}
    if (set(manifest) != required or manifest["schema_version"] !=
            "OC3_CROSS_OBSERVER_GROUPING_DOCUMENTARY_RESOURCE_MANIFEST_002" or
            manifest["stage_id"] != STAGE_ID or manifest["network_request_cap"] != 6 or
            manifest["application_body_byte_cap"] != 12_582_912 or
            manifest["concurrency"] != 1 or manifest["retries"] != 0 or
            manifest["broad_crawling"] is not False or manifest["mirror_substitution"] is not False):
        raise DocumentaryValidationError("RESOURCE_MANIFEST_INVALID")
    resources = manifest["resources"]
    if not isinstance(resources, list) or len(resources) != 6:
        raise DocumentaryValidationError("RESOURCE_MANIFEST_INVALID")
    ids = [item.get("id") for item in resources if isinstance(item, dict)]
    if ids != ["DR9_CATALOG_FORMAT", "DR9_RELEASE_DESCRIPTION", "DR9_FILES_PRODUCTS",
               "DATALAB_DR9_TABLE_METADATA", "DATALAB_DR9_COLUMN_METADATA",
               "BUDAVARI_SZALAY_2008_PREPRINT"]:
        raise DocumentaryValidationError("RESOURCE_ORDER_INVALID")
    if any(item.get("method") != "GET" or item.get("redirects") != 0 or
           item.get("retries") != 0 for item in resources):
        raise DocumentaryValidationError("RESOURCE_TRANSPORT_INVALID")
    if any(item.get("evidence_capture_mode") != "HASHED_RESPONSE_SNAPSHOT" or
           item.get("revision_identity") is not None or
           "immutable_revision_required" in item for item in resources):
        raise DocumentaryValidationError("RESOURCE_CAPTURE_MODE_INVALID")
    if sum(item["application_body_byte_cap"] for item in resources) != 12_582_912:
        raise DocumentaryValidationError("RESOURCE_CAP_INVALID")
    datalab = resources[3:5]
    if any("TAP_SCHEMA." not in item["url"] or "ls_dr9.tractor" in item["url"]
           for item in datalab):
        raise DocumentaryValidationError("DATALAB_METADATA_BOUNDARY_INVALID")
    return manifest


def validate_candidate(path: Path = CANDIDATE) -> dict[str, object]:
    candidate = validate_sealed(load_canonical_json(path))
    if (candidate.get("schema_version") != "OC3_CROSS_OBSERVER_GROUPING_DOCUMENTARY_CANDIDATE_002" or
            candidate.get("stage_id") != STAGE_ID or candidate.get("scope") != SCOPE or
            candidate.get("candidate_state") != "PENDING_STANDING_HUMAN_AUTHORIZATION" or
            candidate.get("standing_authorization_present") is not False or
            candidate.get("permit_issued") is not False):
        raise DocumentaryValidationError("CANDIDATE_STATE_INVALID")
    command = expected_command_argv()
    if candidate.get("command_argv") != command or candidate.get("command_argv_sha256") != sha256_bytes(canonical(command)):
        raise DocumentaryValidationError("COMMAND_BINDING_INVALID")
    if candidate.get("implementation_aggregate") != implementation_aggregate():
        raise DocumentaryValidationError("IMPLEMENTATION_BINDING_INVALID")
    manifest = validate_manifest()
    if candidate.get("resource_manifest") != {"path": str(MANIFEST.relative_to(PROJECT)), "sha256": file_sha256(MANIFEST)}:
        raise DocumentaryValidationError("RESOURCE_MANIFEST_BINDING_INVALID")
    if candidate.get("policy_core_manifest") != {
            "path": str(POLICY_MANIFEST.relative_to(PROJECT)),
            "sha256": file_sha256(POLICY_MANIFEST)}:
        raise DocumentaryValidationError("POLICY_CORE_BINDING_INVALID")
    if candidate.get("resource_caps") != {"application_body_bytes": 12_582_912,
            "compute_seconds": 300, "concurrency": 1, "network_requests": 6,
            "output_bytes": 13_631_488, "ram_bytes": 536_870_912, "retries": 0,
            "threads": 1, "wall_seconds": 900}:
        raise DocumentaryValidationError("RESOURCE_CAP_INVALID")
    if manifest["network_request_cap"] != candidate["resource_caps"]["network_requests"]:
        raise DocumentaryValidationError("RESOURCE_CAP_INVALID")
    if candidate.get("documentary_transport_boundary") != {
            "acquisition_passes_semantic_gate": False,
            "offline_semantic_review_required": True,
            "photsys_documentary_token_allowed": True,
            "photsys_scientific_values_read": 0,
            "source_rows_read": 0}:
        raise DocumentaryValidationError("DOCUMENTARY_BOUNDARY_INVALID")
    return candidate


def validate_runtime_invocation(candidate: dict[str, object], *, executable: str,
                                script_path: str, argument_vector: Sequence[str]) -> None:
    observed = [executable, script_path, *argument_vector]
    if observed != candidate["command_argv"] or sha256_bytes(canonical(observed)) != candidate["command_argv_sha256"]:
        raise DocumentaryValidationError("RUNTIME_COMMAND_MISMATCH")
