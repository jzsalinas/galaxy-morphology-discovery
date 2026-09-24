"""Offline validator for the single-resource primary-literature recovery."""
from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .core import canonical
from .cross_observer_grouping import PROJECT, file_sha256, load_canonical_json, sha256_bytes, validate_sealed

STAGE_ID = "OC3-CROSS-OBSERVER-GROUPING-PRIMARY-LITERATURE-RECOVERY-001"
SCOPE = "PRIMARY_CROSS_IDENTIFICATION_LITERATURE_RECOVERY_ONLY"
SPEC = PROJECT / "OC3_CROSS_OBSERVER_GROUPING_PRIMARY_LITERATURE_RECOVERY_SPEC_001.md"
MANIFEST = PROJECT / "oc3/INPUTS/OC3_CROSS_OBSERVER_GROUPING_PRIMARY_LITERATURE_RECOVERY_MANIFEST_001.json"
CANDIDATE = PROJECT / "oc3/INPUTS/OC3_CROSS_OBSERVER_GROUPING_PRIMARY_LITERATURE_RECOVERY_CANDIDATE_001.json"
RECEIPT = PROJECT / "oc3/INPUTS/OC3_CROSS_OBSERVER_GROUPING_PRIMARY_LITERATURE_RECOVERY_VALIDATION_001.json"
PERMIT = PROJECT / "oc3/CROSS_OBSERVER_GROUPING_AUTONOMY_PERMITS/OC3_CROSS_OBSERVER_GROUPING_PRIMARY_LITERATURE_RECOVERY_PERMIT_001.json"
AUTHORIZATION = PROJECT / "oc3/OC3_CROSS_OBSERVER_GROUPING_STANDING_AUTHORIZATION_002.json"
STATE = PROJECT / "oc3/OC3_CROSS_OBSERVER_GROUPING_AUTONOMY_STATE_002.json"
OUTPUT = PROJECT / "oc3/cross_observer_grouping/OC3-CROSS-OBSERVER-GROUPING-PRIMARY-LITERATURE-RECOVERY-001"
EXECUTABLE = PROJECT / "oc3/.venv/bin/python"
SCRIPT = PROJECT / "oc3/oc3_cross_observer_grouping_primary_literature.py"
FROZEN_USER_AGENT = "Mozilla/5.0 (compatible; OC3Research/1.0)"
IMPLEMENTATION_FILES = (
    "OC3_CROSS_OBSERVER_GROUPING_PRIMARY_LITERATURE_RECOVERY_SPEC_001.md",
    "oc3/oc3_cross_observer_grouping_primary_literature.py",
    "oc3/oc3lib/cross_observer_grouping_primary_literature_validation.py",
    "oc3/oc3lib/cross_observer_grouping_documentary_provenance.py",
)


class LiteratureValidationError(Exception):
    pass


def implementation_aggregate() -> str:
    return sha256_bytes(canonical({name:file_sha256(PROJECT/name) for name in IMPLEMENTATION_FILES}))


def expected_command_argv() -> list[str]:
    return [str(EXECUTABLE),str(SCRIPT),"--acquire-primary-literature","--candidate",str(CANDIDATE),
            "--permit",str(PERMIT),"--standing-authorization",str(AUTHORIZATION),
            "--autonomy-state",str(STATE),"--output-directory",str(OUTPUT)]


def validate_manifest() -> dict[str, object]:
    value = validate_sealed(load_canonical_json(MANIFEST)); resources = value.get("resources")
    if (value.get("schema_version") != "OC3_CROSS_OBSERVER_GROUPING_PRIMARY_LITERATURE_RECOVERY_MANIFEST_001" or
            value.get("stage_id") != STAGE_ID or value.get("network_request_cap") != 1 or
            value.get("application_body_byte_cap") != 8_388_608 or value.get("concurrency") != 1 or
            value.get("retries") != 0 or value.get("broad_crawling") is not False or
            value.get("mirror_substitution") is not False or not isinstance(resources,list) or len(resources) != 1):
        raise LiteratureValidationError("LITERATURE_MANIFEST_INVALID")
    resource = resources[0]
    if (resource.get("id") != "BUDAVARI_SZALAY_2008_PREPRINT_EXPORT" or
            resource.get("url") != "https://export.arxiv.org/pdf/0707.1611" or
            resource.get("host") != "export.arxiv.org" or resource.get("method") != "GET" or
            resource.get("accepted_content_types") != ["application/pdf"] or
            resource.get("application_body_byte_cap") != 8_388_608 or resource.get("redirects") != 0 or
            resource.get("retries") != 0 or resource.get("evidence_capture_mode") != "HASHED_RESPONSE_SNAPSHOT" or
            resource.get("revision_identity") is not None):
        raise LiteratureValidationError("LITERATURE_RESOURCE_INVALID")
    return value


def validate_candidate(path: Path = CANDIDATE) -> dict[str, object]:
    value = validate_sealed(load_canonical_json(path))
    if (value.get("schema_version") != "OC3_CROSS_OBSERVER_GROUPING_PRIMARY_LITERATURE_RECOVERY_CANDIDATE_001" or
            value.get("stage_id") != STAGE_ID or value.get("scope") != SCOPE or
            value.get("candidate_state") != "AUTONOMOUS_PROSPECTIVE_ACTION" or
            value.get("implementation_aggregate") != implementation_aggregate() or
            value.get("request_headers") != {"User-Agent":FROZEN_USER_AGENT} or
            value.get("source_rows_read") != 0 or value.get("documentary_gate_decided") is not False or
            value.get("resource_caps") != {"application_body_bytes":8_388_608,"concurrency":1,
                "network_requests":1,"retries":0}):
        raise LiteratureValidationError("LITERATURE_CANDIDATE_INVALID")
    validate_manifest()
    if value.get("resource_manifest") != {"path":str(MANIFEST.relative_to(PROJECT)),"sha256":file_sha256(MANIFEST)}:
        raise LiteratureValidationError("LITERATURE_MANIFEST_BINDING_INVALID")
    command = expected_command_argv()
    if value.get("command_argv") != command or value.get("command_argv_sha256") != sha256_bytes(canonical(command)):
        raise LiteratureValidationError("LITERATURE_COMMAND_INVALID")
    return value


def validate_runtime(candidate: dict[str, object], executable: str, script: str, argv: Sequence[str]) -> None:
    observed=[executable,script,*argv]
    if observed != candidate["command_argv"] or sha256_bytes(canonical(observed)) != candidate["command_argv_sha256"]:
        raise LiteratureValidationError("RUNTIME_COMMAND_MISMATCH")

