"""Offline validator for the non-executable Run-005 preparation package."""
from __future__ import annotations
from pathlib import Path
from .core import canonical
from .cross_observer_grouping import PROJECT, file_sha256, load_canonical_json, sha256_bytes, validate_sealed
from .manual_source_metadata_acquisition import binding_payload

CONTROL_FILES=(
    "oc3/oc3lib/source_metadata_transport_accounting.py",
    "oc3/oc3lib/source_metadata_recovery_executors_run005.py",
    "oc3/oc3lib/source_metadata_run005_preparation.py",
)
MANUAL_FILES=(
    "oc3/oc3lib/manual_source_metadata_acquisition.py",
    "oc3/oc3_manual_source_metadata_acquisition_001.py",
)
ALL_FILES=CONTROL_FILES+MANUAL_FILES

def aggregate(paths): return sha256_bytes(canonical({p:file_sha256(PROJECT/p) for p in paths}))
def control_plane_aggregate(): return aggregate(CONTROL_FILES)
def manual_implementation_aggregate(): return aggregate(MANUAL_FILES)
def implementation_aggregate(): return aggregate(ALL_FILES)

def validate_package():
    closure=validate_sealed(load_canonical_json(PROJECT/"oc3/INPUTS/OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_RUN_004_CLOSURE_001.json"))
    if (closure["authorization"]["sha256"]!="d6c9daae4ed052d24f413102e1a14e2428a05992030ba1d3be371a0c2abdc125" or
        closure["material_network_requests_started_observed"]!=2 or closure["application_body_bytes_observed"]!=2124 or
        closure["accepted_source_rows"]!=0 or closure["accepted_source_values"]!=0):
        raise ValueError("RUN_004_CLOSURE_DRIFT")
    binding=validate_sealed(load_canonical_json(PROJECT/"oc3/INPUTS/OC3_MANUAL_SOURCE_METADATA_ACQUISITION_BINDING_001.json"))
    if binding!=binding_payload(): raise ValueError("MANUAL_BINDING_DRIFT")
    drift=validate_sealed(load_canonical_json(PROJECT/"oc3/INPUTS/OC3_SOURCE_METADATA_RUN_005_DRIFT_MATRIX_001.json"))
    for key in ("scientific_semantic_drift","observational_contract_drift","provider_resource_drift","rights_drift","resource_scope_drift","budget_drift","acceptance_criteria_drift"):
        if drift.get(key)!=0: raise ValueError("RUN_005_DRIFT_NONZERO")
    state=validate_sealed(load_canonical_json(PROJECT/"oc3/OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_PREPARATION_STATE_005.json"))
    if (state.get("execution_status")!="NOT_STARTED" or state.get("authorized") is not False or
        state.get("first_candidate") is not None or state.get("standing_authorization") is not None or
        state.get("implementation_aggregate")!=implementation_aggregate() or
        state.get("control_plane_aggregate")!=control_plane_aggregate()):
        raise ValueError("RUN_005_PREPARATION_STATE_INVALID")
    if (PROJECT/"oc3/OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_STANDING_AUTHORIZATION_005.json").exists():
        raise ValueError("RUN_005_AUTHORIZATION_FORBIDDEN")
    return {"closure":closure,"binding":binding,"drift":drift,"state":state}
