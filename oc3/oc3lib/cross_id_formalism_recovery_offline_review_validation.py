"""Validator for the zero-network cross-ID formalism semantic review."""
from __future__ import annotations
from pathlib import Path
from typing import Sequence

from .core import canonical
from .cross_id_formalism_recovery import PROJECT,file_sha256,load_canonical_json,sha256_bytes,validate_sealed

STAGE_ID="OC3-CROSS-ID-FORMALISM-OFFLINE-SEMANTIC-REVIEW-001"
SCOPE="OFFLINE_PRIMARY_LITERATURE_SEMANTIC_REVIEW_ONLY"
SPEC=PROJECT/"OC3_CROSS_ID_FORMALISM_RECOVERY_OFFLINE_SEMANTIC_REVIEW_SPEC_001.md"
CANDIDATE=PROJECT/"oc3/INPUTS/OC3_CROSS_ID_FORMALISM_RECOVERY_OFFLINE_REVIEW_CANDIDATE_001.json"
RECEIPT=PROJECT/"oc3/INPUTS/OC3_CROSS_ID_FORMALISM_RECOVERY_OFFLINE_REVIEW_VALIDATION_001.json"
PERMIT=PROJECT/"oc3/CROSS_ID_FORMALISM_RECOVERY_AUTONOMY_PERMITS/OC3_CROSS_ID_FORMALISM_RECOVERY_OFFLINE_REVIEW_PERMIT_001.json"
AUTHORIZATION=PROJECT/"oc3/OC3_CROSS_ID_FORMALISM_RECOVERY_STANDING_AUTHORIZATION_001.json"
STATE=PROJECT/"oc3/OC3_CROSS_ID_FORMALISM_RECOVERY_AUTONOMY_STATE_001.json"
OUTPUT=PROJECT/"oc3/cross_id_formalism_recovery/OC3-CROSS-ID-FORMALISM-OFFLINE-SEMANTIC-REVIEW-001"
EXECUTABLE=PROJECT/"oc3/.venv/bin/python"
SCRIPT=PROJECT/"oc3/oc3_cross_id_formalism_recovery_offline_review.py"
IMPLEMENTATION_FILES=(
 "OC3_CROSS_ID_FORMALISM_RECOVERY_OFFLINE_SEMANTIC_REVIEW_SPEC_001.md",
 "oc3/oc3_cross_id_formalism_recovery_offline_review.py",
 "oc3/oc3lib/cross_id_formalism_recovery_offline_review_validation.py",
)

class OfflineReviewValidationError(Exception):
    def __init__(self,code): self.code=code; super().__init__(code)

def implementation_aggregate():
    return sha256_bytes(canonical({p:file_sha256(PROJECT/p) for p in IMPLEMENTATION_FILES}))

def expected_command_argv():
    return [str(EXECUTABLE),str(SCRIPT),"--review-primary-evidence","--candidate",str(CANDIDATE),
            "--permit",str(PERMIT),"--standing-authorization",str(AUTHORIZATION),
            "--autonomy-state",str(STATE),"--output-directory",str(OUTPUT)]

def validate_candidate(path:Path=CANDIDATE):
    value=validate_sealed(load_canonical_json(path))
    if (value.get("schema_version")!="OC3_CROSS_ID_FORMALISM_RECOVERY_OFFLINE_REVIEW_CANDIDATE_001" or
        value.get("stage_id")!=STAGE_ID or value.get("scope")!=SCOPE or
        value.get("network_requests")!=0 or value.get("source_rows_read")!=0 or
        value.get("search_bound_selected") is not False or value.get("scientific_threshold_selected") is not False):
        raise OfflineReviewValidationError("OFFLINE_REVIEW_CANDIDATE_INVALID")
    argv=expected_command_argv()
    if value.get("command_argv")!=argv or value.get("command_argv_sha256")!=sha256_bytes(canonical(argv)):
        raise OfflineReviewValidationError("COMMAND_BINDING_INVALID")
    if value.get("implementation_aggregate")!=implementation_aggregate():
        raise OfflineReviewValidationError("IMPLEMENTATION_BINDING_INVALID")
    inputs=value.get("input_bindings")
    if not isinstance(inputs,list) or len(inputs)!=4:
        raise OfflineReviewValidationError("OFFLINE_REVIEW_INPUT_INVALID")
    for binding in inputs:
        if set(binding)!={"path","sha256"}:
            raise OfflineReviewValidationError("OFFLINE_REVIEW_INPUT_INVALID")
        source=PROJECT/binding["path"]
        if not source.is_file() or file_sha256(source)!=binding["sha256"]:
            raise OfflineReviewValidationError("OFFLINE_REVIEW_INPUT_MISMATCH")
    if value.get("claim_order")!=[
        "CROSS_IDENTIFICATION_FORMALISM_ASSUMPTIONS","BOUNDED_PILOT_SPECIFIABLE_WITHOUT_THRESHOLD"]:
        raise OfflineReviewValidationError("OFFLINE_REVIEW_CLAIM_ORDER_INVALID")
    return value

def validate_runtime_invocation(candidate,*,executable:str,script_path:str,argument_vector:Sequence[str]):
    observed=[executable,script_path,*argument_vector]
    if observed!=candidate["command_argv"] or sha256_bytes(canonical(observed))!=candidate["command_argv_sha256"]:
        raise OfflineReviewValidationError("RUNTIME_COMMAND_MISMATCH")
