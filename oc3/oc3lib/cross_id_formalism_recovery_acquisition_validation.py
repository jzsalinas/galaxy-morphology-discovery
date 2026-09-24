"""Offline validator for the first formalism-recovery acquisition."""
from __future__ import annotations
from pathlib import Path
from typing import Sequence

from .core import canonical
from .cross_id_formalism_recovery import (
    PROJECT, file_sha256, load_canonical_json, sha256_bytes, validate_claim_vocabulary,
    validate_sealed,
)

STAGE_ID = "OC3-CROSS-ID-FORMALISM-PRIMARY-EVIDENCE-ACQUISITION-001"
SCOPE = "PRIMARY_LITERATURE_ACQUISITION_ONLY"
SPEC = PROJECT / "OC3_CROSS_ID_FORMALISM_RECOVERY_FIRST_ACQUISITION_SPEC_001.md"
MANIFEST = PROJECT / "oc3/INPUTS/OC3_CROSS_ID_FORMALISM_RECOVERY_RESOURCE_MANIFEST_001.json"
CANDIDATE = PROJECT / "oc3/INPUTS/OC3_CROSS_ID_FORMALISM_RECOVERY_FIRST_CANDIDATE_001.json"
RECEIPT = PROJECT / "oc3/INPUTS/OC3_CROSS_ID_FORMALISM_RECOVERY_FIRST_CANDIDATE_VALIDATION_001.json"
PERMIT = PROJECT / "oc3/CROSS_ID_FORMALISM_RECOVERY_AUTONOMY_PERMITS/OC3_CROSS_ID_FORMALISM_RECOVERY_PRIMARY_EVIDENCE_PERMIT_001.json"
AUTHORIZATION = PROJECT / "oc3/OC3_CROSS_ID_FORMALISM_RECOVERY_STANDING_AUTHORIZATION_001.json"
STATE = PROJECT / "oc3/OC3_CROSS_ID_FORMALISM_RECOVERY_AUTONOMY_STATE_001.json"
POLICY_MANIFEST = PROJECT / "oc3/INPUTS/OC3_CROSS_ID_FORMALISM_RECOVERY_POLICY_CORE_MANIFEST_001.json"
OUTPUT = PROJECT / "oc3/cross_id_formalism_recovery/OC3-CROSS-ID-FORMALISM-PRIMARY-EVIDENCE-ACQUISITION-001"
EXECUTABLE = PROJECT / "oc3/.venv/bin/python"
SCRIPT = PROJECT / "oc3/oc3_cross_id_formalism_recovery_acquisition.py"

IMPLEMENTATION_FILES = (
    "OC3_CROSS_ID_FORMALISM_RECOVERY_FIRST_ACQUISITION_SPEC_001.md",
    "oc3/oc3_cross_id_formalism_recovery_acquisition.py",
    "oc3/oc3lib/cross_id_formalism_recovery.py",
    "oc3/oc3lib/cross_id_formalism_recovery_acquisition_validation.py",
)

class RecoveryValidationError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)

def implementation_aggregate() -> str:
    return sha256_bytes(canonical({p: file_sha256(PROJECT / p) for p in IMPLEMENTATION_FILES}))

def expected_command_argv() -> list[str]:
    return [str(EXECUTABLE), str(SCRIPT), "--acquire-primary-evidence",
            "--candidate", str(CANDIDATE), "--permit", str(PERMIT),
            "--standing-authorization", str(AUTHORIZATION),
            "--autonomy-state", str(STATE), "--output-directory", str(OUTPUT)]

def validate_manifest() -> dict[str, object]:
    value = validate_sealed(load_canonical_json(MANIFEST))
    required = {"application_body_byte_cap","broad_crawling","concurrency",
                "mirror_substitution","network_request_cap","resources","retries",
                "schema_version","sealed","stage_id"}
    if (set(value) != required or value["schema_version"] !=
            "OC3_CROSS_ID_FORMALISM_RECOVERY_RESOURCE_MANIFEST_001" or
            value["stage_id"] != STAGE_ID or value["network_request_cap"] != 2 or
            value["application_body_byte_cap"] != 4_718_592 or value["concurrency"] != 1 or
            value["retries"] != 0 or value["broad_crawling"] is not False or
            value["mirror_substitution"] is not False):
        raise RecoveryValidationError("RESOURCE_MANIFEST_INVALID")
    resources = value["resources"]
    if not isinstance(resources, list) or len(resources) != 2:
        raise RecoveryValidationError("RESOURCE_COUNT_INVALID")
    expected = (
        ("BUDAVARI_SZALAY_ARXIV_ABSTRACT", "https://arxiv.org/abs/0707.1611",
         "arxiv.org", ["text/html","application/xhtml+xml"], 524_288, "ARXIV:0707.1611"),
        ("BUDAVARI_SZALAY_ASPC_394_165", "https://adsabs.harvard.edu/pdf/2008ASPC..394..165B",
         "adsabs.harvard.edu", ["application/pdf"], 4_194_304, "BIBCODE:2008ASPC..394..165B"),
    )
    required_resource = {"accepted_content_types","application_body_byte_cap",
        "bibliographic_identity","evidence_capture_mode","evidence_class",
        "expected_representation","host","id","method","purpose","redirects",
        "retries","revision_identity","url"}
    for item, exp in zip(resources, expected):
        if (not isinstance(item, dict) or set(item) != required_resource or
                item["id"] != exp[0] or item["url"] != exp[1] or item["host"] != exp[2] or
                item["accepted_content_types"] != exp[3] or item["application_body_byte_cap"] != exp[4] or
                item["bibliographic_identity"] != exp[5] or item["method"] != "GET" or
                item["redirects"] != 0 or item["retries"] != 0 or
                item["evidence_capture_mode"] != "HASHED_RESPONSE_SNAPSHOT" or
                item["evidence_class"] != "PRIMARY_CROSS_IDENTIFICATION_LITERATURE" or
                item["revision_identity"] is not None):
            raise RecoveryValidationError("RESOURCE_IDENTITY_INVALID")
    if "ApJ" in resources[1]["bibliographic_identity"]:
        raise RecoveryValidationError("CONFERENCE_PROCEEDING_MISIDENTIFIED")
    return value

def validate_candidate(path: Path = CANDIDATE) -> dict[str, object]:
    validate_claim_vocabulary()
    value = validate_sealed(load_canonical_json(path))
    if (value.get("schema_version") != "OC3_CROSS_ID_FORMALISM_RECOVERY_FIRST_CANDIDATE_001" or
            value.get("stage_id") != STAGE_ID or value.get("scope") != SCOPE or
            value.get("candidate_state") != "PENDING_STANDING_HUMAN_AUTHORIZATION" or
            value.get("standing_authorization_present") is not False or value.get("permit_issued") is not False):
        raise RecoveryValidationError("CANDIDATE_STATE_INVALID")
    command = expected_command_argv()
    if value.get("command_argv") != command or value.get("command_argv_sha256") != sha256_bytes(canonical(command)):
        raise RecoveryValidationError("COMMAND_BINDING_INVALID")
    if value.get("implementation_aggregate") != implementation_aggregate():
        raise RecoveryValidationError("IMPLEMENTATION_BINDING_INVALID")
    validate_manifest()
    if value.get("resource_manifest") != {"path":str(MANIFEST.relative_to(PROJECT)),"sha256":file_sha256(MANIFEST)}:
        raise RecoveryValidationError("RESOURCE_MANIFEST_BINDING_INVALID")
    if value.get("policy_core_manifest") != {"path":str(POLICY_MANIFEST.relative_to(PROJECT)),"sha256":file_sha256(POLICY_MANIFEST)}:
        raise RecoveryValidationError("POLICY_CORE_BINDING_INVALID")
    if value.get("resource_caps") != {"application_body_bytes":4_718_592,"concurrency":1,
            "network_requests":2,"retries":0}:
        raise RecoveryValidationError("RESOURCE_CAP_INVALID")
    if value.get("search_bound_selected") is not False or value.get("scientific_threshold_selected") is not False:
        raise RecoveryValidationError("THRESHOLD_PRESELECTION_FORBIDDEN")
    return value

def validate_runtime_invocation(candidate: dict[str, object], *, executable: str,
                                script_path: str, argument_vector: Sequence[str]) -> None:
    observed = [executable, script_path, *argument_vector]
    if observed != candidate["command_argv"] or sha256_bytes(canonical(observed)) != candidate["command_argv_sha256"]:
        raise RecoveryValidationError("RUNTIME_COMMAND_MISMATCH")
