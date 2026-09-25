"""Offline validator for the frozen DR9 source-metadata acquisition candidate."""
from __future__ import annotations
from pathlib import Path
from typing import Sequence

from .core import canonical
from .cross_observer_grouping import PROJECT, file_sha256, load_canonical_json, sha256_bytes, validate_sealed
from . import source_metadata_acquisition_pilot as science

SPEC = PROJECT / "OC3_SOURCE_METADATA_ACQUISITION_PILOT_SPEC_001.md"
FIRST_ACTION_SPEC = PROJECT / "OC3_SOURCE_METADATA_ACQUISITION_PILOT_FIRST_ACTION_SPEC_001.md"
QUERY_MANIFEST = PROJECT / "oc3/INPUTS/OC3_SOURCE_METADATA_ACQUISITION_QUERY_MANIFEST_001.json"
DOCUMENTARY_PROVENANCE = PROJECT / "oc3/INPUTS/OC3_SOURCE_METADATA_ACQUISITION_DOCUMENTARY_PROVENANCE_001.json"
CANDIDATE = PROJECT / "oc3/INPUTS/OC3_SOURCE_METADATA_ACQUISITION_PILOT_CANDIDATE_001.json"
RECEIPT = PROJECT / "oc3/INPUTS/OC3_SOURCE_METADATA_ACQUISITION_PILOT_CANDIDATE_VALIDATION_001.json"
FRAME = PROJECT / "oc3/source_metadata_pilot_frame_schema_recovery/OC3-SOURCE-METADATA-PILOT-FRAME-SCHEMA-RECOVERY-001/PILOT_FRAME.json"
FRAME_SHA256 = "661f4d429f8fe0b6aa0104e093d79568d6f274935a7d9b0e78fb3dd45ae40292"
FINAL_REPORT = PROJECT / "OC3_SOURCE_METADATA_PILOT_FRAME_SCHEMA_RECOVERY_FINAL_REPORT_001.md"
FINAL_REPORT_SHA256 = "6002a9f901d39dabbd1c5a77255df1286ddb177981db627f4c0093cc9c698764"
CLAIM_MATRIX = PROJECT / "oc3/OC3_SOURCE_METADATA_PILOT_FRAME_SCHEMA_RECOVERY_FINAL_CLAIM_MATRIX_001.json"
CLAIM_MATRIX_SHA256 = "8b4fe975730f24174436cc21cf27c8c1ea280b0f14b6452714a9ce35a0cff65d"
EXECUTABLE = PROJECT / "oc3/.venv/bin/python"
SUPERVISOR = PROJECT / "oc3/oc3_source_metadata_acquisition_pilot_supervisor.py"
WORKER = PROJECT / "oc3/oc3_source_metadata_acquisition_pilot_worker.py"
PERMIT = PROJECT / "oc3/SOURCE_METADATA_ACQUISITION_PILOT_AUTONOMY_PERMITS/OC3_SOURCE_METADATA_ACQUISITION_PILOT_PERMIT_001.json"
AUTHORIZATION = PROJECT / "oc3/OC3_SOURCE_METADATA_ACQUISITION_PILOT_STANDING_AUTHORIZATION_001.json"
STATE = PROJECT / "oc3/OC3_SOURCE_METADATA_ACQUISITION_PILOT_AUTONOMY_STATE_001.json"
OUTPUT = PROJECT / "oc3/source_metadata_acquisition_pilot/OC3-SOURCE-METADATA-ACQUISITION-PILOT-001"
IMPLEMENTATION_FILES = (
    "OC3_SOURCE_METADATA_ACQUISITION_PILOT_SPEC_001.md",
    "OC3_SOURCE_METADATA_ACQUISITION_PILOT_FIRST_ACTION_SPEC_001.md",
    "oc3/INPUTS/OC3_SOURCE_METADATA_ACQUISITION_DOCUMENTARY_PROVENANCE_001.json",
    "oc3/INPUTS/OC3_SOURCE_METADATA_ACQUISITION_QUERY_MANIFEST_001.json",
    "oc3/oc3_source_metadata_acquisition_pilot_supervisor.py",
    "oc3/oc3_source_metadata_acquisition_pilot_worker.py",
    "oc3/oc3lib/source_metadata_acquisition_pilot.py",
    "oc3/oc3lib/source_metadata_acquisition_pilot_validation.py",
)


class AcquisitionValidationError(Exception):
    def __init__(self, code: str):
        self.code = code; super().__init__(code)


def implementation_aggregate() -> str:
    return sha256_bytes(canonical({name:file_sha256(PROJECT/name) for name in IMPLEMENTATION_FILES}))


def expected_command_argv() -> list[str]:
    return [str(EXECUTABLE),str(SUPERVISOR),"--acquire-source-metadata","--candidate",str(CANDIDATE),
        "--permit",str(PERMIT),"--standing-authorization",str(AUTHORIZATION),
        "--autonomy-state",str(STATE),"--output-directory",str(OUTPUT)]


def expected_worker_command() -> list[str]:
    return [str(EXECUTABLE),str(WORKER),"--run-acquisition-worker","--candidate",str(CANDIDATE),"--output",str(OUTPUT)]


def validate_documentary_provenance() -> dict[str, object]:
    value=validate_sealed(load_canonical_json(DOCUMENTARY_PROVENANCE))
    if (set(value)!={"network_requests","schema_version","sealed","sources","transport_semantics_only"} or
            value["schema_version"]!="OC3_SOURCE_METADATA_ACQUISITION_DOCUMENTARY_PROVENANCE_001" or
            value["network_requests"]!=0 or value["transport_semantics_only"] is not True or
            not isinstance(value["sources"],list) or len(value["sources"])!=6 or
            any(not row.get("url","").startswith("https://") or not row.get("identity") for row in value["sources"])):
        raise AcquisitionValidationError("DOCUMENTARY_PROVENANCE_INVALID")
    return value


def validate_query_manifest() -> dict[str, object]:
    science.validate_frozen_support(); science.frame_support(FRAME,FRAME_SHA256)
    value=validate_sealed(load_canonical_json(QUERY_MANIFEST))
    required_top={"anonymous_token_contract","application_body_byte_cap","broad_crawling","concurrency",
        "count_cap_per_domain","datatype_allowlists","forbidden_holdout_bricks","headers","mirror_substitution",
        "network_request_cap","projection","queries","query_hash_algorithm","request_order","resources",
        "response_caps","retry_redirect_resume_policy","schema_version","sealed","service_endpoint","stage_id",
        "target_guard_bricks","timeout_seconds","top_hard_cap","true_serializations"}
    expected_datatypes={key:sorted(values) for key,values in science.DATATYPE_CLASSES.items()}
    if (set(value)!=required_top or value.get("schema_version")!="OC3_SOURCE_METADATA_ACQUISITION_QUERY_MANIFEST_001" or
            value.get("stage_id")!=science.STAGE_ID or value.get("service_endpoint")!=science.SERVICE_ENDPOINT or
            value.get("network_request_cap")!=5 or value.get("application_body_byte_cap")!=67_108_864 or
            value.get("concurrency")!=1 or value.get("timeout_seconds")!=300 or
            value.get("retry_redirect_resume_policy")!={"redirects":0,"resume":False,"retries":0} or
            value.get("target_guard_bricks")!=list(science.TARGET_GUARD_UNION) or
            value.get("forbidden_holdout_bricks")!=list(science.HOLDOUT_GUARD_UNION) or
            value.get("projection")!=list(science.PROJECTION) or value.get("request_order")!=list(science.REQUEST_ORDER) or
            value.get("response_caps")!=science.RESPONSE_CAPS or value.get("count_cap_per_domain")!=150_000 or
            value.get("top_hard_cap")!=150_001 or value.get("broad_crawling") is not False or
            value.get("mirror_substitution") is not False or value.get("headers")!=science.frozen_headers() or
            value.get("query_hash_algorithm")!="ADQL_WHITESPACE_CANONICAL_SHA256_V1" or
            value.get("datatype_allowlists")!=expected_datatypes or
            value.get("true_serializations")!=sorted(science.TRUE_SERIALIZATIONS)):
        raise AcquisitionValidationError("QUERY_MANIFEST_INVALID")
    if value.get("anonymous_token_contract")!={"credential_file_reads":0,"identity":science.PUBLIC_ANONYMOUS_TOKEN,"mode":"PUBLIC_ANONYMOUS_ONLY"}:
        raise AcquisitionValidationError("QUERY_MANIFEST_AUTH_INVALID")
    queries=value.get("queries"); resources=value.get("resources")
    if not isinstance(queries,list) or not isinstance(resources,list) or len(queries)!=5 or len(resources)!=5:
        raise AcquisitionValidationError("QUERY_MANIFEST_INVALID")
    for qid,query,resource in zip(science.REQUEST_ORDER,queries,resources):
        literal=science.QUERY_LITERALS[qid]; url=science.query_url(literal)
        if query!={"canonical_sha256":science.query_sha256(literal),"id":qid,"literal_adql":literal,"literal_url":url}:
            raise AcquisitionValidationError("QUERY_LITERAL_MISMATCH")
        required={"accepted_content_types","application_body_byte_cap","bibliographic_identity","evidence_capture_mode",
            "evidence_class","expected_representation","host","id","method","purpose","redirects","retries",
            "revision_identity","url"}
        if (set(resource)!=required or resource["id"]!=qid or resource["url"]!=url or resource["method"]!="GET" or
                resource["application_body_byte_cap"]!=science.RESPONSE_CAPS[qid] or resource["redirects"]!=0 or
                resource["retries"]!=0 or resource["host"]!="datalab.noirlab.edu" or
                resource["accepted_content_types"]!=["text/csv","text/plain","application/x-csv"] or
                resource["bibliographic_identity"]!="NOIRLAB_DATALAB_QUERY_MANAGER_PUBLIC_DR9" or
                resource["evidence_capture_mode"]!="HASHED_RESPONSE_SNAPSHOT" or
                resource["evidence_class"]!="OFFICIAL_NOIRLAB_DATALAB_PUBLIC_QUERY" or
                resource["expected_representation"]!="text/csv" or resource["revision_identity"] is not None):
            raise AcquisitionValidationError("QUERY_RESOURCE_MISMATCH")
    validate_documentary_provenance()
    return value


def validate_candidate(path: Path=CANDIDATE) -> dict[str, object]:
    value=validate_sealed(load_canonical_json(path)); manifest=validate_query_manifest()
    required={"application_body_bytes","command_argv","command_argv_sha256","documentary_provenance",
        "holdout_count_requests","holdout_row_requests","holdout_source_derived_cells_observed","implementation_aggregate",
        "network_requests","output_directory","predecessor_bindings","query_manifest","resume","schema_rows_observed",
        "schema_version","scope","sealed","source_counts_observed","source_rows_observed","stage_id","worker_command",
        "worker_command_sha256","worker_launches","autonomy_policy"}
    if (set(value)!=required or value["schema_version"]!="OC3_SOURCE_METADATA_ACQUISITION_PILOT_CANDIDATE_001" or
            value["stage_id"]!=science.STAGE_ID or value["scope"]!=science.MISSION_SCOPE or
            value["implementation_aggregate"]!=implementation_aggregate() or value["resume"] is not False or
            value["worker_launches"]!=1 or any(value[key]!=0 for key in ("application_body_bytes","network_requests",
                "schema_rows_observed","source_counts_observed","source_rows_observed","holdout_count_requests",
                "holdout_row_requests","holdout_source_derived_cells_observed"))):
        raise AcquisitionValidationError("CANDIDATE_INVALID")
    if (value["query_manifest"]!={"path":str(QUERY_MANIFEST.relative_to(PROJECT)),"sha256":file_sha256(QUERY_MANIFEST)} or
            value["documentary_provenance"]!={"path":str(DOCUMENTARY_PROVENANCE.relative_to(PROJECT)),"sha256":file_sha256(DOCUMENTARY_PROVENANCE)}):
        raise AcquisitionValidationError("CANDIDATE_AUTHORITY_MISMATCH")
    expected_predecessors={"final_claim_matrix":{"path":str(CLAIM_MATRIX.relative_to(PROJECT)),"sha256":CLAIM_MATRIX_SHA256},
        "final_report":{"path":str(FINAL_REPORT.relative_to(PROJECT)),"sha256":FINAL_REPORT_SHA256},
        "pilot_frame":{"path":str(FRAME.relative_to(PROJECT)),"sha256":FRAME_SHA256},
        "terminal_commit":"cf34a0efae274a198ac924f99da6135597a7d451"}
    if value["predecessor_bindings"]!=expected_predecessors:
        raise AcquisitionValidationError("CANDIDATE_PREDECESSOR_MISMATCH")
    command=expected_command_argv(); worker=expected_worker_command()
    if (value["command_argv"]!=command or value["command_argv_sha256"]!=sha256_bytes(canonical(command)) or
            value["worker_command"]!=worker or value["worker_command_sha256"]!=sha256_bytes(canonical(worker)) or
            value["output_directory"]!=str(OUTPUT.relative_to(PROJECT))):
        raise AcquisitionValidationError("CANDIDATE_COMMAND_MISMATCH")
    return value


def validate_invocation(candidate: dict[str, object], observed: Sequence[str]) -> None:
    if list(observed)!=candidate["command_argv"] or sha256_bytes(canonical(list(observed)))!=candidate["command_argv_sha256"]:
        raise AcquisitionValidationError("SUPERVISOR_COMMAND_MISMATCH")
