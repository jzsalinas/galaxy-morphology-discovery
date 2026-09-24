"""Offline validator for the bounded documentary completion action."""
from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .core import canonical
from .cross_observer_grouping import (
    PROJECT, file_sha256, load_canonical_json, sha256_bytes, validate_sealed,
)

STAGE_ID = "OC3-CROSS-OBSERVER-GROUPING-DOCUMENTARY-EVIDENCE-COMPLETION-003"
SCOPE = "PUBLIC_DOCUMENTARY_AND_SCHEMA_METADATA_COMPLETION_ONLY"
SPEC = PROJECT / "OC3_CROSS_OBSERVER_GROUPING_DOCUMENTARY_COMPLETION_SPEC_003.md"
MANIFEST = PROJECT / "oc3/INPUTS/OC3_CROSS_OBSERVER_GROUPING_DOCUMENTARY_COMPLETION_MANIFEST_003.json"
CANDIDATE = PROJECT / "oc3/INPUTS/OC3_CROSS_OBSERVER_GROUPING_DOCUMENTARY_COMPLETION_CANDIDATE_003.json"
RECEIPT = PROJECT / "oc3/INPUTS/OC3_CROSS_OBSERVER_GROUPING_DOCUMENTARY_COMPLETION_VALIDATION_003.json"
PERMIT = PROJECT / "oc3/CROSS_OBSERVER_GROUPING_AUTONOMY_PERMITS/OC3_CROSS_OBSERVER_GROUPING_DOCUMENTARY_COMPLETION_PERMIT_003.json"
AUTHORIZATION = PROJECT / "oc3/OC3_CROSS_OBSERVER_GROUPING_STANDING_AUTHORIZATION_002.json"
STATE = PROJECT / "oc3/OC3_CROSS_OBSERVER_GROUPING_AUTONOMY_STATE_002.json"
OUTPUT = PROJECT / "oc3/cross_observer_grouping/OC3-CROSS-OBSERVER-GROUPING-DOCUMENTARY-EVIDENCE-COMPLETION-003"
EXECUTABLE = PROJECT / "oc3/.venv/bin/python"
SCRIPT = PROJECT / "oc3/oc3_cross_observer_grouping_documentary_completion.py"
IMPLEMENTATION_FILES = (
    "OC3_CROSS_OBSERVER_GROUPING_DOCUMENTARY_COMPLETION_SPEC_003.md",
    "oc3/oc3_cross_observer_grouping_documentary_completion.py",
    "oc3/oc3lib/cross_observer_grouping_documentary_completion_validation.py",
    "oc3/oc3lib/cross_observer_grouping_documentary_provenance.py",
)


class CompletionValidationError(Exception):
    pass


def implementation_aggregate() -> str:
    return sha256_bytes(canonical({name: file_sha256(PROJECT / name) for name in IMPLEMENTATION_FILES}))


def expected_command_argv() -> list[str]:
    return [str(EXECUTABLE), str(SCRIPT), "--acquire-documentary-completion",
            "--candidate", str(CANDIDATE), "--permit", str(PERMIT),
            "--standing-authorization", str(AUTHORIZATION), "--autonomy-state", str(STATE),
            "--output-directory", str(OUTPUT)]


def validate_manifest() -> dict[str, object]:
    value = validate_sealed(load_canonical_json(MANIFEST))
    resources = value.get("resources")
    if (value.get("schema_version") != "OC3_CROSS_OBSERVER_GROUPING_DOCUMENTARY_COMPLETION_MANIFEST_003" or
            value.get("stage_id") != STAGE_ID or value.get("network_request_cap") != 3 or
            value.get("application_body_byte_cap") != 9_437_184 or value.get("concurrency") != 1 or
            value.get("retries") != 0 or value.get("broad_crawling") is not False or
            value.get("mirror_substitution") is not False or not isinstance(resources, list) or
            len(resources) != 3):
        raise CompletionValidationError("COMPLETION_MANIFEST_INVALID")
    if [r.get("id") for r in resources] != ["DATALAB_DR9_TABLE_METADATA_CORRECTED",
            "DATALAB_DR9_COLUMN_METADATA_CORRECTED", "BUDAVARI_SZALAY_2008_PREPRINT"]:
        raise CompletionValidationError("COMPLETION_RESOURCE_ORDER_INVALID")
    if sum(r.get("application_body_byte_cap", -1) for r in resources) != 9_437_184:
        raise CompletionValidationError("COMPLETION_RESOURCE_CAP_INVALID")
    for resource in resources:
        if (resource.get("method") != "GET" or resource.get("redirects") != 0 or
                resource.get("retries") != 0 or resource.get("evidence_capture_mode") !=
                "HASHED_RESPONSE_SNAPSHOT" or resource.get("revision_identity") is not None):
            raise CompletionValidationError("COMPLETION_RESOURCE_INVALID")
    tables, columns, paper = resources
    if ("TAP_SCHEMA.tables" not in tables.get("url", "") or
            "%27ls_dr9.tractor_n%27" not in tables["url"] or
            "%27tractor_n%27" in tables["url"]):
        raise CompletionValidationError("CORRECTED_TABLE_QUERY_INVALID")
    if ("TAP_SCHEMA.columns" not in columns.get("url", "") or
            "schema_name" in columns["url"] or "%27ls_dr9.tractor_n%27" not in columns["url"] or
            "%27tractor_n%27" in columns["url"]):
        raise CompletionValidationError("CORRECTED_COLUMN_QUERY_INVALID")
    if paper.get("url") != "https://arxiv.org/pdf/0707.1611.pdf":
        raise CompletionValidationError("PRIMARY_LITERATURE_RESOURCE_INVALID")
    return value


def validate_candidate(path: Path = CANDIDATE) -> dict[str, object]:
    value = validate_sealed(load_canonical_json(path))
    if (value.get("schema_version") != "OC3_CROSS_OBSERVER_GROUPING_DOCUMENTARY_COMPLETION_CANDIDATE_003" or
            value.get("stage_id") != STAGE_ID or value.get("scope") != SCOPE or
            value.get("implementation_aggregate") != implementation_aggregate() or
            value.get("candidate_state") != "AUTONOMOUS_PROSPECTIVE_ACTION" or
            value.get("documentary_gate_decided") is not False or value.get("source_rows_read") != 0 or
            value.get("resource_caps") != {"application_body_bytes":9_437_184,"concurrency":1,
                "network_requests":3,"retries":0}):
        raise CompletionValidationError("COMPLETION_CANDIDATE_INVALID")
    validate_manifest()
    if value.get("resource_manifest") != {"path":str(MANIFEST.relative_to(PROJECT)),
            "sha256":file_sha256(MANIFEST)}:
        raise CompletionValidationError("COMPLETION_MANIFEST_BINDING_INVALID")
    command = expected_command_argv()
    if value.get("command_argv") != command or value.get("command_argv_sha256") != sha256_bytes(canonical(command)):
        raise CompletionValidationError("COMPLETION_COMMAND_INVALID")
    return value


def validate_runtime(candidate: dict[str, object], executable: str, script: str,
                     argv: Sequence[str]) -> None:
    observed = [executable, script, *argv]
    if observed != candidate["command_argv"] or sha256_bytes(canonical(observed)) != candidate["command_argv_sha256"]:
        raise CompletionValidationError("RUNTIME_COMMAND_MISMATCH")

