"""Offline validator for the frozen DR9 source-metadata acquisition candidate."""
from __future__ import annotations
from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Sequence

from .core import canonical
from .cross_observer_grouping import PROJECT, file_sha256, load_canonical_json, sealed, sha256_bytes, validate_sealed
from . import source_metadata_acquisition_pilot as science

SPEC = PROJECT / "OC3_SOURCE_METADATA_ACQUISITION_PILOT_SPEC_001.md"
FIRST_ACTION_SPEC = PROJECT / "OC3_SOURCE_METADATA_ACQUISITION_PILOT_FIRST_ACTION_SPEC_001.md"
QUERY_MANIFEST = PROJECT / "oc3/INPUTS/OC3_SOURCE_METADATA_ACQUISITION_QUERY_MANIFEST_001.json"
DOCUMENTARY_PROVENANCE = PROJECT / "oc3/INPUTS/OC3_SOURCE_METADATA_ACQUISITION_DOCUMENTARY_PROVENANCE_002.json"
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
WORKER_CAPABILITY = OUTPUT / "OC3_SOURCE_METADATA_ACQUISITION_WORKER_CAPABILITY_001.json"
WORKER_CAPABILITY_CONSUMPTION_ROOT = PROJECT / "oc3/SOURCE_METADATA_ACQUISITION_PILOT_AUTONOMY_LEDGER/WORKER_CAPABILITY_CONSUMPTION"
IMPLEMENTATION_FILES = (
    "OC3_SOURCE_METADATA_ACQUISITION_PILOT_SPEC_001.md",
    "OC3_SOURCE_METADATA_ACQUISITION_PILOT_FIRST_ACTION_SPEC_001.md",
    "OC3_SOURCE_METADATA_ACQUISITION_PILOT_GOVERNANCE_BYPASS_REVIEW_001.md",
    "oc3/INPUTS/OC3_SOURCE_METADATA_ACQUISITION_DOCUMENTARY_PROVENANCE_001.json",
    "oc3/INPUTS/OC3_SOURCE_METADATA_ACQUISITION_DOCUMENTARY_PROVENANCE_002.json",
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
    return [str(EXECUTABLE),str(WORKER),"--run-acquisition-worker","--candidate",str(CANDIDATE),"--output",str(OUTPUT),
        "--execution-capability",str(WORKER_CAPABILITY)]


def _relative(path: Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(PROJECT))
    except ValueError as exc:
        raise AcquisitionValidationError("WORKER_EXECUTION_CAPABILITY_INVALID") from exc


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")


def worker_capability_consumption_path(capability_path: Path) -> Path:
    return WORKER_CAPABILITY_CONSUMPTION_ROOT / f"{file_sha256(capability_path)}.json"


def create_worker_capability(*, candidate: dict[str,object], candidate_path: Path, permit_path: Path,
        standing_authorization_path: Path, autonomy_state_path: Path, output_directory: Path,
        permit_consumption_marker: Path, issued_at_utc: str) -> dict[str,object]:
    capability_path=PROJECT/str(candidate.get("worker_capability_path",""))
    if (Path(output_directory).resolve()!=(PROJECT/str(candidate.get("output_directory",""))).resolve() or
            not Path(permit_path).is_file() or not Path(standing_authorization_path).is_file() or
            not Path(autonomy_state_path).is_file() or not Path(permit_consumption_marker).is_file() or
            capability_path.exists()):
        raise AcquisitionValidationError("WORKER_EXECUTION_CAPABILITY_INVALID")
    try:
        from . import source_metadata_acquisition_pilot_governor as governor
        expected_marker=governor._consumption_marker_path(permit_path)
        if Path(permit_consumption_marker).resolve()!=expected_marker.resolve():
            raise AcquisitionValidationError("WORKER_EXECUTION_CAPABILITY_INVALID")
        marker=governor.validate_consumption_marker(permit_path,candidate_path=candidate_path)
    except AcquisitionValidationError:
        raise
    except Exception as exc:
        raise AcquisitionValidationError("WORKER_EXECUTION_CAPABILITY_INVALID") from exc
    candidate_sha=file_sha256(candidate_path); permit_sha=file_sha256(permit_path)
    if (marker.get("candidate_sha256")!=candidate_sha or marker.get("permit_sha256")!=permit_sha or
            marker.get("state")!="PERMIT_CONSUMPTION_INTENT_RECORDED"):
        raise AcquisitionValidationError("WORKER_EXECUTION_CAPABILITY_INVALID")
    try:
        if not isinstance(issued_at_utc,str) or not issued_at_utc.endswith("Z"):
            raise ValueError
        datetime.fromisoformat(issued_at_utc[:-1]+"+00:00")
    except (TypeError,ValueError) as exc: raise AcquisitionValidationError("WORKER_EXECUTION_CAPABILITY_INVALID") from exc
    identity=sha256_bytes(canonical({"candidate_sha256":candidate_sha,"issued_at_utc":issued_at_utc,
        "permit_sha256":permit_sha,"worker_command_sha256":candidate["worker_command_sha256"]}))
    capability=sealed({"application_body_reservation":science.BODY_CAP,
        "autonomy_state_path":_relative(autonomy_state_path),
        "candidate_path":_relative(candidate_path),"candidate_sha256":candidate_sha,
        "capability_id":f"OC3-WORKER-CAPABILITY-{identity[:24]}","issued_at_utc":issued_at_utc,
        "mission_id":science.MISSION_ID,"network_request_reservation":science.REQUEST_CAP,
        "output_directory":_relative(output_directory),"permit_path":_relative(permit_path),
        "permit_sha256":permit_sha,"query_manifest_path":candidate["query_manifest"]["path"],
        "query_manifest_sha256":candidate["query_manifest"]["sha256"],
        "schema_version":"OC3_SOURCE_METADATA_ACQUISITION_WORKER_CAPABILITY_001",
        "single_use":True,"stage_id":science.STAGE_ID,
        "standing_authorization_path":_relative(standing_authorization_path),
        "standing_authorization_sha256":file_sha256(standing_authorization_path),
        "worker_command_sha256":candidate["worker_command_sha256"]})
    from .cross_observer_grouping import write_json_immutable
    write_json_immutable(capability_path,capability)
    return capability


def validate_worker_invocation(candidate: dict[str,object], observed: Sequence[str]) -> None:
    expected=candidate.get("worker_command")
    if (not isinstance(expected,list) or list(observed)!=expected or
            sha256_bytes(canonical(list(observed)))!=candidate.get("worker_command_sha256")):
        raise AcquisitionValidationError("WORKER_EXECUTION_CAPABILITY_INVALID")


def validate_worker_capability(path: Path, *, candidate: dict[str,object], candidate_path: Path,
        output_directory: Path) -> dict[str,object]:
    try: value=validate_sealed(load_canonical_json(path))
    except Exception as exc: raise AcquisitionValidationError("WORKER_EXECUTION_CAPABILITY_INVALID") from exc
    required={"application_body_reservation","autonomy_state_path","candidate_path","candidate_sha256",
        "capability_id","issued_at_utc","mission_id","network_request_reservation","output_directory",
        "permit_path","permit_sha256","query_manifest_path","query_manifest_sha256","schema_version","sealed",
        "single_use","stage_id","standing_authorization_path","standing_authorization_sha256","worker_command_sha256"}
    expected_identity=sha256_bytes(canonical({"candidate_sha256":file_sha256(candidate_path),
        "issued_at_utc":value.get("issued_at_utc"),"permit_sha256":value.get("permit_sha256"),
        "worker_command_sha256":candidate.get("worker_command_sha256")}))
    if (set(value)!=required or Path(path).resolve()!=(PROJECT/str(candidate.get("worker_capability_path",""))).resolve() or
            value.get("schema_version")!="OC3_SOURCE_METADATA_ACQUISITION_WORKER_CAPABILITY_001" or
            value.get("mission_id")!=science.MISSION_ID or value.get("stage_id")!=science.STAGE_ID or
            value.get("candidate_path")!=_relative(candidate_path) or
            value.get("candidate_sha256")!=file_sha256(candidate_path) or
            value.get("worker_command_sha256")!=candidate.get("worker_command_sha256") or
            value.get("query_manifest_path")!=candidate["query_manifest"]["path"] or
            value.get("query_manifest_sha256")!=candidate["query_manifest"]["sha256"] or
            value.get("output_directory")!=_relative(output_directory) or
            value.get("network_request_reservation")!=science.REQUEST_CAP or
            value.get("application_body_reservation")!=science.BODY_CAP or value.get("single_use") is not True or
            value.get("autonomy_state_path")!=_relative(STATE) or
            value.get("permit_path")!=candidate.get("autonomy_policy",{}).get("permit_output_path") or
            value.get("capability_id")!=f"OC3-WORKER-CAPABILITY-{expected_identity[:24]}" or
            not isinstance(value.get("issued_at_utc"),str) or not value["issued_at_utc"].endswith("Z")):
        raise AcquisitionValidationError("WORKER_EXECUTION_CAPABILITY_INVALID")
    try:
        datetime.fromisoformat(value["issued_at_utc"][:-1]+"+00:00")
    except ValueError as exc:
        raise AcquisitionValidationError("WORKER_EXECUTION_CAPABILITY_INVALID") from exc
    for path_key,sha_key in (("permit_path","permit_sha256"),("standing_authorization_path","standing_authorization_sha256")):
        bound=PROJECT/str(value[path_key])
        if not bound.is_file() or value[sha_key]!=file_sha256(bound):
            raise AcquisitionValidationError("WORKER_EXECUTION_CAPABILITY_INVALID")
    if (value["standing_authorization_path"]!=_relative(AUTHORIZATION) or
            worker_capability_consumption_path(path).exists()):
        raise AcquisitionValidationError("WORKER_EXECUTION_CAPABILITY_ALREADY_CONSUMED" if worker_capability_consumption_path(path).exists()
            else "WORKER_EXECUTION_CAPABILITY_INVALID")
    try:
        from . import source_metadata_acquisition_pilot_governor as governor
        permit=PROJECT/str(value["permit_path"]); authorization=PROJECT/str(value["standing_authorization_path"])
        governor.validate_permit(permit,candidate_path=candidate_path,state_path=STATE,
            standing_authorization_path=authorization,allow_consumed=True)
        governor.validate_consumption_marker(permit,candidate_path=candidate_path)
    except Exception as exc:
        raise AcquisitionValidationError("WORKER_EXECUTION_CAPABILITY_INVALID") from exc
    return value


def consume_worker_capability(path: Path, *, candidate: dict[str,object], candidate_path: Path,
        output_directory: Path, consumed_at_utc: str|None=None) -> Path:
    value=validate_worker_capability(path,candidate=candidate,candidate_path=candidate_path,
        output_directory=output_directory)
    marker_path=worker_capability_consumption_path(path); marker_path.parent.mkdir(parents=True,exist_ok=True)
    marker=sealed({"candidate_sha256":value["candidate_sha256"],"capability_sha256":file_sha256(path),
        "consumed_at_utc":consumed_at_utc or _utc(),"permit_sha256":value["permit_sha256"],
        "schema_version":"OC3_SOURCE_METADATA_ACQUISITION_WORKER_CAPABILITY_CONSUMPTION_001",
        "worker_command_sha256":value["worker_command_sha256"]})
    data=canonical(marker)+b"\n"
    try:
        with marker_path.open("xb") as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
    except FileExistsError as exc:
        raise AcquisitionValidationError("WORKER_EXECUTION_CAPABILITY_ALREADY_CONSUMED") from exc
    return marker_path


def validate_documentary_provenance() -> dict[str, object]:
    value=validate_sealed(load_canonical_json(DOCUMENTARY_PROVENANCE))
    if (set(value)!={"network_requests","schema_version","sealed","sources","transport_semantics_only"} or
            value["schema_version"]!="OC3_SOURCE_METADATA_ACQUISITION_DOCUMENTARY_PROVENANCE_002" or
            value["network_requests"]!=0 or value["transport_semantics_only"] is not True or
            not isinstance(value["sources"],list) or len(value["sources"])!=6 or
            any(not row.get("url","").startswith("https://") or not row.get("identity") for row in value["sources"])):
        raise AcquisitionValidationError("DOCUMENTARY_PROVENANCE_INVALID")
    source=next((row for row in value["sources"] if row.get("id")=="ASTRO_DATALAB_QUERY_CLIENT_SOURCE"),None)
    if (not isinstance(source,dict) or source.get("repository")!="astro-datalab/datalab" or
            source.get("file")!="dl/queryClient.py" or source.get("exact_commit") is not None or
            source.get("retrieval_basis")!="HUMAN_REVIEWED_EXTERNAL_EVIDENCE_CORRECTION_NO_NETWORK_REPLAY"):
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
        "schema_version","scope","sealed","source_counts_observed","source_rows_observed","stage_id",
        "worker_capability_path","worker_command","worker_command_sha256","worker_launches","autonomy_policy"}
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
            value["worker_capability_path"]!=str(WORKER_CAPABILITY.relative_to(PROJECT)) or
            value["worker_command"]!=worker or value["worker_command_sha256"]!=sha256_bytes(canonical(worker)) or
            value["output_directory"]!=str(OUTPUT.relative_to(PROJECT))):
        raise AcquisitionValidationError("CANDIDATE_COMMAND_MISMATCH")
    return value


def validate_invocation(candidate: dict[str, object], observed: Sequence[str]) -> None:
    if list(observed)!=candidate["command_argv"] or sha256_bytes(canonical(list(observed)))!=candidate["command_argv_sha256"]:
        raise AcquisitionValidationError("SUPERVISOR_COMMAND_MISMATCH")
