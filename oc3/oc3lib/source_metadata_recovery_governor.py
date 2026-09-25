"""Policy governor for the finite OC3 source-metadata recovery envelope."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import subprocess
from typing import Mapping

from .core import canonical
from .cross_observer_grouping import (
    PROJECT, file_sha256, load_canonical_json, sealed, sha256_bytes,
    validate_sealed, write_json_immutable,
)
from .autonomous_recovery_envelope import (
    FINALIZE_SCIENTIFIC, RECOVER_AUTONOMOUSLY, STOP_REQUIRES_HUMAN,
    RecoveryEnvelopeError, account_action, classify_action_terminal, validate_recovery_graph,
)
from .source_metadata_recovery_factory import (
    ACTION_FAMILIES, FIRST_CANDIDATE_RELATIVE, RUN_ID, binding,
    build_first_candidate, build_next_candidate,
)

MISSION_ID = "OC3-SOURCE-METADATA-AUTONOMOUS-RECOVERY-ENVELOPE-001"
MISSION_SCOPE = "SOURCE_METADATA_ACQUISITION_WITH_BOUNDED_TECHNICAL_RECOVERY"
AUTONOMY_BRANCH = "autopilot/source-metadata-autonomous-recovery"
STATE_WAITING = "WAITING_FOR_STANDING_HUMAN_AUTHORIZATION"
STATE_ACTIVE = "ACTIVE"
STATE_TERMINAL = "SCIENTIFIC_TERMINAL"

SPEC = PROJECT / "OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_PRODUCTION_SPEC_003.md"
POLICY_CONTRACT = PROJECT / "OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_POLICY_CORE_CONTRACT_002.md"
RUNBOOK = PROJECT / "OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_RUNBOOK_002.md"
INVARIANTS = PROJECT / "oc3/INPUTS/OC3_SOURCE_METADATA_RECOVERY_SCIENTIFIC_INVARIANTS_001.json"
RECOVERY_GRAPH = PROJECT / "oc3/INPUTS/OC3_SOURCE_METADATA_RECOVERY_GRAPH_001.json"
MUTABLE_SURFACE = PROJECT / "oc3/INPUTS/OC3_SOURCE_METADATA_MUTABLE_TECHNICAL_SURFACE_001.json"
RECOVERY_BUDGET = PROJECT / "oc3/INPUTS/OC3_SOURCE_METADATA_RECOVERY_BUDGET_001.json"
POLICY_MANIFEST = PROJECT / "oc3/INPUTS/OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_POLICY_CORE_MANIFEST_002.json"
MANDATE = PROJECT / "oc3/INPUTS/OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_MANDATE_002.json"
RUN_001_CLOSURE = PROJECT / "oc3/INPUTS/OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_RUN_001_CLOSURE_001.json"
PRODUCTION_FIRST_CANDIDATE = PROJECT / FIRST_CANDIDATE_RELATIVE
FIRST_CANDIDATE = PRODUCTION_FIRST_CANDIDATE
ACTION_REGISTRY = PROJECT / "oc3/INPUTS/OC3_SOURCE_METADATA_RECOVERY_ACTION_REGISTRY_002.json"
TECHNICAL_AUTHORITIES = PROJECT / "oc3/INPUTS/OC3_SOURCE_METADATA_RECOVERY_TECHNICAL_AUTHORITIES_002.json"
STATE = PROJECT / "oc3/OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_STATE_002.json"
STANDING_AUTHORIZATION = PROJECT / "oc3/OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_STANDING_AUTHORIZATION_002.json"
LEDGER_ROOT = PROJECT / "oc3/SOURCE_METADATA_AUTONOMOUS_RECOVERY_RUN_002_LEDGER"
PERMIT_ROOT = PROJECT / "oc3/SOURCE_METADATA_AUTONOMOUS_RECOVERY_RUN_002_PERMITS"
PERMIT_CONSUMPTION = LEDGER_ROOT / "PERMIT_CONSUMPTION"
CAPABILITY_CONSUMPTION = LEDGER_ROOT / "WORKER_CAPABILITY_CONSUMPTION"
IMPLEMENTATION_FILES = (
    "oc3/oc3lib/autonomous_recovery_envelope.py",
    "oc3/oc3lib/source_metadata_recovery_controller.py",
    "oc3/oc3lib/source_metadata_recovery_factory.py",
    "oc3/oc3lib/source_metadata_recovery_governor.py",
    "oc3/oc3lib/source_metadata_recovery_executors.py",
    "oc3/oc3_source_metadata_recovery_mission_runner.py",
    "oc3/oc3_source_metadata_recovery_supervisor.py",
    "oc3/oc3_source_metadata_recovery_worker.py",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def implementation_aggregate() -> str:
    return sha256_bytes(canonical({name: file_sha256(PROJECT / name) for name in IMPLEMENTATION_FILES}))


def _load(path: Path, code: str) -> dict[str, object]:
    try:
        return validate_sealed(load_canonical_json(path))
    except Exception as exc:
        raise RecoveryEnvelopeError(code) from exc


def _atomic_state(path: Path, value: dict[str, object]) -> None:
    data = canonical(value) + b"\n"
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    with temporary.open("xb") as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, path)


def validate_scientific_invariants(invariants: dict[str, object]) -> dict[str, object]:
    if (invariants.get("max_source_rows_per_domain") != 150_000 or invariants.get("top_hard_cap") != 150_001 or
            len(invariants.get("target_guard_bricknames", [])) != 14 or
            len(invariants.get("forbidden_holdout_bricknames", [])) != 16 or
            len(invariants.get("projection", [])) != 9 or len(invariants.get("queries", [])) != 5):
        raise RecoveryEnvelopeError("SCIENTIFIC_INVARIANTS_INVALID")
    from .source_metadata_acquisition_pilot import query_sha256
    if any(query_sha256(row.get("literal_adql", "")) != row.get("semantic_sha256") for row in invariants["queries"]):
        raise RecoveryEnvelopeError("SCIENTIFIC_QUERY_SEMANTICS_INVALID")
    if set(invariants["target_guard_bricknames"]) & set(invariants["forbidden_holdout_bricknames"]):
        raise RecoveryEnvelopeError("SCIENTIFIC_HOLDOUT_FIREWALL_INVALID")
    return invariants


def validate_recovery_budget(budget: dict[str, object]) -> dict[str, object]:
    expected = {"MAX_CODE_REPAIR_GENERATIONS": 3, "MAX_MATERIAL_BODY_BYTES": 67_108_864,
        "MAX_MATERIAL_REQUESTS": 5, "MAX_OCCURRENCES_SAME_TECHNICAL_FAILURE_CLASS": 2,
        "MAX_RECOVERY_GENERATIONS": 4, "MAX_TECHNICAL_BODY_BYTES": 2_097_152,
        "MAX_TECHNICAL_BODY_BYTES_PER_REQUEST": 262_144, "MAX_TECHNICAL_NETWORK_REQUESTS": 8,
        "MATERIAL_CONCURRENCY": 1, "MATERIAL_RETRIES_PER_ACTION": 0,
        "TECHNICAL_CONCURRENCY": 1, "TECHNICAL_RETRIES_PER_ACTION": 0}
    if any(budget.get(key) != value for key, value in expected.items()):
        raise RecoveryEnvelopeError("RECOVERY_BUDGET_INVALID")
    return budget


def validate_static_authorities() -> dict[str, dict[str, object]]:
    values = {"invariants": _load(INVARIANTS, "SCIENTIFIC_INVARIANTS_INVALID"),
        "graph": _load(RECOVERY_GRAPH, "RECOVERY_GRAPH_INVALID"),
        "surface": _load(MUTABLE_SURFACE, "MUTABLE_TECHNICAL_SURFACE_INVALID"),
        "budget": _load(RECOVERY_BUDGET, "RECOVERY_BUDGET_INVALID"),
        "policy": _load(POLICY_MANIFEST, "RECOVERY_POLICY_CORE_INVALID"),
        "mandate": _load(MANDATE, "RECOVERY_MANDATE_INVALID"),
        "run_001_closure": _load(RUN_001_CLOSURE, "RECOVERY_PREDECESSOR_RUN_INVALID"),
        "action_registry": _load(ACTION_REGISTRY, "RECOVERY_ACTION_REGISTRY_INVALID"),
        "technical_authorities": _load(TECHNICAL_AUTHORITIES, "TECHNICAL_AUTHORITIES_INVALID")}
    validate_recovery_graph(values["graph"])
    validate_recovery_budget(values["budget"])
    validate_scientific_invariants(values["invariants"])
    registry = values["action_registry"]
    if (registry.get("schema_version") != "OC3_SOURCE_METADATA_RECOVERY_ACTION_REGISTRY_002" or
            [row.get("action_kind") for row in registry.get("actions", [])] != list(ACTION_FAMILIES)):
        raise RecoveryEnvelopeError("RECOVERY_ACTION_REGISTRY_INVALID")
    required_action = {"action_kind", "active_adapter_required", "allowed_authority_classes",
        "capability_naming_template", "command_template_id", "eligible_trigger_failure_classes",
        "maximum_body_bytes_per_action", "maximum_requests_per_action", "network_capability_required",
        "output_directory_naming_template", "parent_terminal_required", "permit_naming_template",
        "request_class", "stage_id_naming_template", "supervisor_implementation",
        "technical_patch_manifest_required", "worker_implementation"}
    mandate = values["mandate"]
    for row in registry["actions"]:
        if set(row) != required_action or row["request_class"] not in ("TECHNICAL", "MATERIAL", "OFFLINE"):
            raise RecoveryEnvelopeError("RECOVERY_ACTION_REGISTRY_INVALID")
        if not set(row["allowed_authority_classes"]).issubset(set(mandate["allowed_authority_classes"])):
            raise RecoveryEnvelopeError("RECOVERY_AUTHORITY_CLASS_EXPANSION")
        for key in ("supervisor_implementation", "worker_implementation"):
            target = PROJECT / row[key]["path"]
            if row[key] != binding(target):
                raise RecoveryEnvelopeError("RECOVERY_ACTION_IMPLEMENTATION_CHANGED")
    authorities = values["technical_authorities"]
    adapters=authorities.get("adapters")
    resource_ids={row.get("id") for row in authorities.get("resources",[]) if isinstance(row,dict)}
    allowed_prefixes=tuple(values["surface"].get("allowed_path_prefixes",[]))
    if (authorities.get("schema_version") != "OC3_SOURCE_METADATA_RECOVERY_TECHNICAL_AUTHORITIES_002" or
            not isinstance(authorities.get("bootstrap_commit"),str) or
            not isinstance(authorities.get("resources"), list) or
            not isinstance(adapters, list) or
            any(set(row) != {"authority_class", "id", "purpose", "url"} for row in authorities["resources"]) or
            any(not isinstance(row,dict) or set(row) != {"adapter_id", "allowed_authority_resource_ids",
                "bootstrap_sha256", "implementation_path", "implementation_policy", "initial_state"} or
                row["initial_state"] != "AVAILABLE_UNVALIDATED" or
                row["implementation_policy"] != "MUTABLE_TECHNICAL_SURFACE_BOUND" or
                not isinstance(row["implementation_path"],str) or
                not row["implementation_path"].startswith(allowed_prefixes) or
                not isinstance(row["allowed_authority_resource_ids"],list) or
                not row["allowed_authority_resource_ids"] or
                not set(row["allowed_authority_resource_ids"]).issubset(resource_ids)
                for row in adapters) or
            authorities.get("adapter_ids") != [row["adapter_id"] for row in adapters] or
            len(set(authorities.get("adapter_ids",[]))) != len(adapters)):
        raise RecoveryEnvelopeError("TECHNICAL_AUTHORITIES_INVALID")
    for adapter in adapters:
        result=subprocess.run(["git","show",f"{authorities['bootstrap_commit']}:{adapter['implementation_path']}"],
            cwd=PROJECT,check=False,capture_output=True)
        historical=hashlib.sha256(result.stdout).hexdigest() if result.returncode == 0 else None
        if adapter["bootstrap_sha256"] != historical:
            raise RecoveryEnvelopeError("TECHNICAL_AUTHORITIES_INVALID")
    policy = values["policy"]
    if (policy.get("schema_version") != "OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_POLICY_CORE_MANIFEST_002" or
            policy.get("run_id") != RUN_ID or policy.get("generic_policy_core") is not True or
            policy.get("active_mutation_result") != STOP_REQUIRES_HUMAN or
            not isinstance(policy.get("files"), list)):
        raise RecoveryEnvelopeError("RECOVERY_POLICY_CORE_INVALID")
    for item in policy["files"]:
        path = PROJECT / str(item.get("path", ""))
        if not path.is_file() or item.get("sha256") != file_sha256(path):
            raise RecoveryEnvelopeError("RECOVERY_POLICY_CORE_CHANGED")
    closure = values["run_001_closure"]
    if (closure.get("schema_version") != "OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_RUN_001_CLOSURE_001" or
            closure.get("run_id") != "OC3-SOURCE-METADATA-AUTONOMOUS-RECOVERY-RUN-001" or
            closure.get("stop_commit") != "57b520d3d3f849b9d0c0c554984f5688fe62786a" or
            closure.get("final_state_sha256") != "364905c88a55e65d6429caadea3614b4de34b2990eea1b2cc23cde435ae784ea" or
            closure.get("ledger_aggregate_sha256") != "af2db3858b15f23a4fdf5ef2365a8ebc2da7528455eaf9a28c178528b7d1178b" or
            closure.get("contradiction_evidence_sha256") != "6f3831aa4a0e8f7ea6a5a64d08f66af0addba66996440fa693a7d0af22dcaf96" or
            closure.get("issued_permit_sha256") != "badd14e4d398ff444a361bd929cfaed32f8bb3603bcf4a28b10d73bd2eaba314" or
            closure.get("permit_consumed") is not False or closure.get("network_requests") != 0 or
            closure.get("body_bytes") != 0 or closure.get("source_rows") != 0 or
            closure.get("worker_capabilities") != 0 or
            closure.get("stop_reason") != "FIRST_CANDIDATE_EXECUTION_PATH_BINDING_CONTRADICTION" or
            closure.get("finding") != "FIRST_CANDIDATE_SELF_PATH_BINDING_DEFECT"):
        raise RecoveryEnvelopeError("RECOVERY_PREDECESSOR_RUN_INVALID")
    if (mandate.get("schema_version") != "OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_MANDATE_002" or
            mandate.get("active") is not False or mandate.get("mission_id") != MISSION_ID or
            mandate.get("run_id") != RUN_ID or
            mandate.get("mission_scope") != MISSION_SCOPE or mandate.get("autonomy_branch") != AUTONOMY_BRANCH or
            mandate.get("allowed_action_families") != list(ACTION_FAMILIES) or
            mandate.get("scientific_invariants") != binding(INVARIANTS) or
            mandate.get("recovery_graph") != binding(RECOVERY_GRAPH) or
            mandate.get("mutable_technical_surface") != binding(MUTABLE_SURFACE) or
            mandate.get("recovery_budget") != binding(RECOVERY_BUDGET) or
            mandate.get("action_registry") != binding(ACTION_REGISTRY) or
            mandate.get("technical_authorities") != binding(TECHNICAL_AUTHORITIES) or
            mandate.get("first_candidate") != binding(PRODUCTION_FIRST_CANDIDATE) or
            mandate.get("candidate_factory") != binding(PROJECT / "oc3/oc3lib/source_metadata_recovery_factory.py") or
            mandate.get("mission_runner") != binding(PROJECT / "oc3/oc3_source_metadata_recovery_mission_runner.py") or
            mandate.get("runbook") != binding(RUNBOOK) or mandate.get("specification") != binding(SPEC) or
            mandate.get("standing_authorization_path") != str(STANDING_AUTHORIZATION.relative_to(PROJECT)) or
            mandate.get("predecessor_run") != binding(RUN_001_CLOSURE) or
            mandate.get("policy_core_manifest") != binding(POLICY_MANIFEST)):
        raise RecoveryEnvelopeError("RECOVERY_MANDATE_PREMATURELY_ACTIVE")
    return values


def validate_candidate_self_binding(candidate_path: Path,
                                    candidate: Mapping[str, object]) -> None:
    """Enforce one physical candidate file and one canonical execution path."""
    try:
        actual = candidate_path if candidate_path.is_absolute() else PROJECT / candidate_path
        absolute = actual.absolute()
        resolved = actual.resolve(strict=True)
        relative = str(absolute.relative_to(PROJECT))
        if absolute != resolved or candidate.get("candidate_path") != relative:
            raise ValueError
        for key in ("command_argv", "worker_argv"):
            argv = candidate.get(key)
            if not isinstance(argv, list) or argv.count("--candidate") != 1:
                raise ValueError
            index = argv.index("--candidate")
            if index + 1 >= len(argv):
                raise ValueError
            bound = Path(str(argv[index + 1]))
            bound_absolute = bound.absolute()
            if bound_absolute != absolute or bound.resolve(strict=True) != resolved:
                raise ValueError
        if (sha256_bytes(canonical(candidate["command_argv"])) != candidate.get("command_argv_sha256") or
                sha256_bytes(canonical(candidate["worker_argv"])) != candidate.get("worker_argv_sha256")):
            raise ValueError
    except Exception as exc:
        raise RecoveryEnvelopeError("RECOVERY_CANDIDATE_SELF_PATH_MISMATCH") from exc


def validate_candidate(path: Path) -> dict[str, object]:
    value = _load(path, "RECOVERY_CANDIDATE_INVALID")
    required = {"action_kind", "active_adapter", "active_adapter_binding", "action_registry", "application_body_reservation", "authority_classes", "candidate_path", "command_argv",
        "command_argv_sha256", "implementation_aggregate", "material_budget_reservation",
        "mutable_technical_surface", "network_request_reservation", "output_directory",
        "parent_action_terminal", "permit_path", "recovery_budget", "recovery_generation",
        "recovery_graph", "remaining_budgets", "request_class", "resume", "retries", "run_id",
        "schema_version", "scientific_invariants", "sealed", "stage_id", "technical_authorities",
        "technical_budget_reservation", "technical_patch_manifest", "trigger_failure_class",
        "technical_transport_contract", "test_receipts", "worker_argv", "worker_argv_sha256", "worker_capability_path"}
    if (set(value) != required or value.get("schema_version") != "RECOVERY_ACTION_FACTORY_V3" or
            value.get("run_id") != RUN_ID or
            value.get("action_kind") not in ACTION_FAMILIES or value.get("request_class") not in ("TECHNICAL", "MATERIAL", "OFFLINE") or
            value.get("resume") is not False or value.get("retries") != 0 or
            value.get("implementation_aggregate") != implementation_aggregate()):
        raise RecoveryEnvelopeError("RECOVERY_CANDIDATE_INVALID")
    validate_candidate_self_binding(path, value)
    expected = (("scientific_invariants", INVARIANTS), ("recovery_graph", RECOVERY_GRAPH),
        ("mutable_technical_surface", MUTABLE_SURFACE), ("recovery_budget", RECOVERY_BUDGET),
        ("action_registry", ACTION_REGISTRY), ("technical_authorities", TECHNICAL_AUTHORITIES))
    if any(value[key] != binding(path_) for key, path_ in expected):
        raise RecoveryEnvelopeError("RECOVERY_CANDIDATE_AUTHORITY_MISMATCH")
    budget = _load(RECOVERY_BUDGET, "RECOVERY_BUDGET_INVALID")
    if (type(value["recovery_generation"]) is not int or value["recovery_generation"] < 1 or
            value["recovery_generation"] > budget["MAX_RECOVERY_GENERATIONS"]):
        raise RecoveryEnvelopeError("RECOVERY_GENERATION_LIMIT")
    if value["request_class"] == "TECHNICAL" and (
            value["network_request_reservation"] > budget["MAX_TECHNICAL_NETWORK_REQUESTS"] or
            value["application_body_reservation"] > budget["MAX_TECHNICAL_BODY_BYTES"] or
            value["application_body_reservation"] > budget["MAX_TECHNICAL_BODY_BYTES_PER_REQUEST"]):
        raise RecoveryEnvelopeError("TECHNICAL_BUDGET_OVERFLOW")
    registry = _load(ACTION_REGISTRY, "RECOVERY_ACTION_REGISTRY_INVALID")
    rule = next((row for row in registry["actions"] if row["action_kind"] == value["action_kind"]), None)
    mandate = _load(MANDATE, "RECOVERY_MANDATE_INVALID")
    if (rule is None or value["request_class"] != rule["request_class"] or
            value["authority_classes"] != rule["allowed_authority_classes"] or
            not set(value["authority_classes"]).issubset(set(mandate["allowed_authority_classes"])) or
            value["network_request_reservation"] != rule["maximum_requests_per_action"] or
            value["application_body_reservation"] != rule["maximum_body_bytes_per_action"]):
        raise RecoveryEnvelopeError("RECOVERY_CANDIDATE_REGISTRY_MISMATCH")
    active_binding=value["active_adapter_binding"]
    active_required=rule.get("active_adapter_required") is True
    authority_adapter=None
    if active_required:
        authorities=_load(TECHNICAL_AUTHORITIES,"TECHNICAL_AUTHORITIES_INVALID")
        authority_adapter=next((row for row in authorities["adapters"]
            if row["adapter_id"]==value["active_adapter"]),None)
    if (active_required and (not isinstance(active_binding,dict) or
            set(active_binding) != {"adapter_id","implementation_path","implementation_sha256",
                "technical_patch_manifest","technical_transport_contract","test_receipts"} or
            active_binding.get("adapter_id") != value["active_adapter"] or authority_adapter is None or
            active_binding.get("implementation_path") != authority_adapter["implementation_path"] or
            not isinstance(active_binding.get("implementation_sha256"),str) or
            len(active_binding["implementation_sha256"]) != 64 or
            any(character not in "0123456789abcdef" for character in active_binding["implementation_sha256"]))):
        raise RecoveryEnvelopeError("TECHNICAL_ADAPTER_NOT_VALIDATED")
    if not active_required and active_binding is not None:
        raise RecoveryEnvelopeError("RECOVERY_CANDIDATE_INVALID")
    return value


def validate_first_candidate(path: Path = FIRST_CANDIDATE) -> dict[str, object]:
    value = validate_candidate(path)
    if (value["action_kind"] != "TECHNICAL_RESPONSE_DIAGNOSTIC" or value["request_class"] != "TECHNICAL" or
            value["network_request_reservation"] != 1 or value["application_body_reservation"] != 65_536 or
            value["material_budget_reservation"] != {"body_bytes": 0, "requests": 0} or
            value["technical_budget_reservation"] != {"body_bytes": 65_536, "requests": 1}):
        raise RecoveryEnvelopeError("FIRST_RECOVERY_CANDIDATE_INVALID")
    parent = PROJECT / value["parent_action_terminal"]["path"]
    expected = build_first_candidate(parent_terminal_path=parent, action_registry_path=ACTION_REGISTRY,
        technical_authorities_path=TECHNICAL_AUTHORITIES, scientific_invariants_path=INVARIANTS,
        recovery_graph_path=RECOVERY_GRAPH, recovery_budget_path=RECOVERY_BUDGET,
        mutable_surface_path=MUTABLE_SURFACE, state_path=STATE,
        standing_authorization_path=STANDING_AUTHORIZATION,
        implementation_aggregate=implementation_aggregate())
    if path.resolve() == PRODUCTION_FIRST_CANDIDATE.resolve() and value != expected:
        raise RecoveryEnvelopeError("FIRST_RECOVERY_CANDIDATE_INVALID")
    return value


def expected_child(state: dict[str, object], parent_terminal_path: Path, *, state_path: Path,
                   authorization_path: Path) -> tuple[Path, dict[str, object]]:
    return build_next_candidate(state=state, parent_terminal_path=parent_terminal_path,
        action_registry_path=ACTION_REGISTRY, technical_authorities_path=TECHNICAL_AUTHORITIES,
        scientific_invariants_path=INVARIANTS, recovery_graph_path=RECOVERY_GRAPH,
        recovery_budget_path=RECOVERY_BUDGET, mutable_surface_path=MUTABLE_SURFACE,
        state_path=state_path, standing_authorization_path=authorization_path,
        implementation_aggregate=implementation_aggregate())


def validate_generated_candidate(path: Path, *, state_path: Path, parent_terminal_path: Path) -> dict[str, object]:
    value = validate_candidate(path); state = validate_state(state_path)
    auth = state.get("standing_authorization")
    if not isinstance(auth, dict):
        raise RecoveryEnvelopeError("RECOVERY_STANDING_AUTHORIZATION_INVALID")
    expected_path, expected = expected_child(state, parent_terminal_path, state_path=state_path,
        authorization_path=PROJECT / auth["path"])
    if path.resolve() != expected_path.resolve() or value != expected:
        raise RecoveryEnvelopeError("RECOVERY_CHILD_ACTION_STATE_MISMATCH")
    return value


def validate_state(path: Path = STATE) -> dict[str, object]:
    value = _load(path, "RECOVERY_STATE_INVALID")
    required = {"active", "active_adapter", "active_adapter_binding", "adapter_states", "agentic_repair_request", "body_budget_material_parent", "code_repair_generation", "current_stage",
        "first_candidate", "last_action_terminal", "last_action_terminal_sha256", "last_classification", "material_body_bytes_remaining",
        "material_requests_remaining", "mission_id", "mission_scope", "next_action_kind", "permits_issued", "predecessor_run",
        "recovery_generation", "registered_pending_action", "requests_material_parent", "schema_version", "sealed",
        "run_id", "sequence", "scientific_outcome", "standing_authorization", "state", "stop_reason",
        "technical_body_bytes_remaining", "technical_failure_occurrences", "technical_requests_remaining",
        "validated_patch_manifest", "validated_test_receipts", "validated_transport_contract"}
    if (set(value) != required or value.get("schema_version") != "OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_STATE_002" or
            value.get("mission_id") != MISSION_ID or value.get("run_id") != RUN_ID or
            value.get("mission_scope") != MISSION_SCOPE or value.get("predecessor_run") != binding(RUN_001_CLOSURE) or
            value.get("first_candidate") != binding(FIRST_CANDIDATE)):
        raise RecoveryEnvelopeError("RECOVERY_STATE_INVALID")
    if value["state"] == STATE_WAITING and (value["active"] is not False or value["standing_authorization"] is not None):
        raise RecoveryEnvelopeError("RECOVERY_WAITING_STATE_INVALID")
    if value["state"] == STATE_ACTIVE and value["active"] is not True:
        raise RecoveryEnvelopeError("RECOVERY_ACTIVE_STATE_INVALID")
    if value["state"] in (STATE_TERMINAL, STOP_REQUIRES_HUMAN) and value["active"] is not False:
        raise RecoveryEnvelopeError("RECOVERY_TERMINAL_STATE_INVALID")
    allowed_adapter_states={"AVAILABLE_UNVALIDATED","VALIDATED_FOR_MISSION","REJECTED","ACTIVE"}
    active_binding=value["active_adapter_binding"]
    if (not isinstance(value["adapter_states"],dict) or
            any(item not in allowed_adapter_states for item in value["adapter_states"].values()) or
            (value["active_adapter"] is not None and
             (value["adapter_states"].get(value["active_adapter"]) != "ACTIVE" or
              not isinstance(active_binding,dict) or
              set(active_binding) != {"adapter_id","implementation_path","implementation_sha256",
                  "technical_patch_manifest","technical_transport_contract","test_receipts"} or
              active_binding.get("adapter_id") != value["active_adapter"])) or
            (value["active_adapter"] is None and active_binding is not None) or
            (value["current_stage"] == "AWAITING_AGENTIC_TECHNICAL_REPAIR" and
             (value["active"] is not True or not isinstance(value["agentic_repair_request"],dict)))):
        raise RecoveryEnvelopeError("RECOVERY_ADAPTER_STATE_INVALID")
    return value


def activate(*, state_path: Path, authorization_path: Path, activated_at_utc: str) -> dict[str, object]:
    state = validate_state(state_path); auth = validate_standing_authorization(authorization_path, state_path=state_path)
    if state["state"] != STATE_WAITING or auth.get("authorized") is not True or auth.get("initial_state_sha256") != file_sha256(state_path):
        raise RecoveryEnvelopeError("RECOVERY_ACTIVATION_INVALID")
    body = {k: v for k, v in state.items() if k != "sealed"}
    body.update({"active": True, "current_stage": "AWAITING_NEXT_ACTION_REGISTRATION",
        "standing_authorization": binding(authorization_path), "state": STATE_ACTIVE,
        "sequence": state["sequence"] + 1})
    updated = sealed(body); _atomic_state(state_path, updated)
    return updated


def register_action(*, state_path: Path, candidate_path: Path) -> dict[str, object]:
    state = validate_state(state_path)
    if candidate_path.resolve() == FIRST_CANDIDATE.resolve() and state["recovery_generation"] == 0:
        candidate = validate_first_candidate(candidate_path)
    else:
        parent = state.get("last_action_terminal")
        if not isinstance(parent, dict):
            raise RecoveryEnvelopeError("PARENT_ACTION_TERMINAL_MISMATCH")
        candidate = validate_generated_candidate(candidate_path, state_path=state_path,
            parent_terminal_path=PROJECT / parent["path"])
    if state["state"] != STATE_ACTIVE or state["registered_pending_action"] is not None:
        raise RecoveryEnvelopeError("RECOVERY_ACTION_REGISTRATION_INVALID")
    expected_parent = state["last_action_terminal_sha256"]
    if expected_parent is not None and candidate["parent_action_terminal"]["sha256"] != expected_parent:
        raise RecoveryEnvelopeError("PARENT_ACTION_TERMINAL_MISMATCH")
    body = {k: v for k, v in state.items() if k != "sealed"}
    body.update({"current_stage": "ACTION_REGISTERED", "registered_pending_action": binding(candidate_path),
        "sequence": state["sequence"] + 1})
    updated = sealed(body); _atomic_state(state_path, updated)
    return updated


def issue_permit(*, state_path: Path, candidate_path: Path, output_path: Path,
                 issued_at_utc: str) -> dict[str, object]:
    state = validate_state(state_path); candidate = validate_candidate(candidate_path)
    if (state["registered_pending_action"] != binding(candidate_path) or
            output_path.resolve() != (PROJECT / candidate["permit_path"]).resolve() or output_path.exists()):
        raise RecoveryEnvelopeError("RECOVERY_PERMIT_ISSUANCE_INVALID")
    permit = sealed({"application_body_reservation": candidate["application_body_reservation"],
        "candidate_path": str(candidate_path.resolve().relative_to(PROJECT)),
        "candidate_sha256": file_sha256(candidate_path), "issued_at_utc": issued_at_utc,
        "network_request_reservation": candidate["network_request_reservation"],
        "permit_id": f"RECOVERY-PERMIT-{state['sequence']:06d}-{file_sha256(candidate_path)[:12]}",
        "request_class": candidate["request_class"], "run_id": RUN_ID,
        "schema_version": "OC3_AUTONOMOUS_RECOVERY_EXECUTION_PERMIT_002", "single_use": True,
        "stage_id": candidate["stage_id"], "state_before_sha256": file_sha256(state_path),
        "worker_argv_sha256": candidate["worker_argv_sha256"]})
    write_json_immutable(output_path, permit)
    return permit


def permit_consumption_path(permit_path: Path) -> Path:
    return PERMIT_CONSUMPTION / f"{file_sha256(permit_path)}.json"


def validate_permit(*, permit_path: Path, candidate_path: Path,
                    allow_consumed: bool = False) -> dict[str, object]:
    permit = _load(permit_path, "RECOVERY_PERMIT_INVALID")
    candidate = validate_candidate(candidate_path)
    required = {"application_body_reservation", "candidate_path", "candidate_sha256", "issued_at_utc",
        "network_request_reservation", "permit_id", "request_class", "schema_version", "sealed",
        "single_use", "stage_id", "state_before_sha256", "worker_argv_sha256", "run_id"}
    expected_path = str(candidate_path.resolve().relative_to(PROJECT))
    if (set(permit) != required or permit.get("schema_version") != "OC3_AUTONOMOUS_RECOVERY_EXECUTION_PERMIT_002" or
            permit.get("run_id") != RUN_ID or permit.get("candidate_path") != expected_path or
            candidate.get("candidate_path") != expected_path or
            permit.get("candidate_sha256") != file_sha256(candidate_path) or
            permit.get("network_request_reservation") != candidate["network_request_reservation"] or
            permit.get("application_body_reservation") != candidate["application_body_reservation"] or
            permit.get("request_class") != candidate["request_class"] or
            permit.get("worker_argv_sha256") != candidate["worker_argv_sha256"] or permit.get("single_use") is not True):
        raise RecoveryEnvelopeError("RECOVERY_PERMIT_INVALID")
    if permit_consumption_path(permit_path).exists() and not allow_consumed:
        raise RecoveryEnvelopeError("RECOVERY_PERMIT_ALREADY_CONSUMED")
    return permit


def consume_permit(*, permit_path: Path, candidate_path: Path, consumed_at_utc: str) -> Path:
    permit = validate_permit(permit_path=permit_path, candidate_path=candidate_path)
    marker = permit_consumption_path(permit_path)
    if marker.exists():
        raise RecoveryEnvelopeError("RECOVERY_PERMIT_ALREADY_CONSUMED")
    write_json_immutable(marker, sealed({"candidate_path": str(candidate_path.resolve().relative_to(PROJECT)),
        "candidate_sha256": file_sha256(candidate_path), "run_id": RUN_ID,
        "consumed_at_utc": consumed_at_utc, "permit_sha256": file_sha256(permit_path),
        "schema_version": "OC3_AUTONOMOUS_RECOVERY_PERMIT_CONSUMPTION_002"}))
    return marker


def capability_consumption_path(capability_path: Path) -> Path:
    return CAPABILITY_CONSUMPTION / f"{file_sha256(capability_path)}.json"


def create_worker_capability(*, candidate_path: Path, permit_path: Path,
        permit_marker: Path, authorization_path: Path, state_path: Path,
        capability_path: Path, issued_at_utc: str) -> dict[str, object]:
    candidate = validate_candidate(candidate_path)
    if (capability_path.resolve() != (PROJECT / candidate["worker_capability_path"]).resolve() or
            permit_marker.resolve() != permit_consumption_path(permit_path).resolve() or
            not permit_marker.is_file() or capability_path.exists()):
        raise RecoveryEnvelopeError("RECOVERY_WORKER_CAPABILITY_INVALID")
    capability = sealed({"application_body_reservation": candidate["application_body_reservation"],
        "authorization_sha256": file_sha256(authorization_path),
        "candidate_path": candidate["candidate_path"],
        "candidate_sha256": file_sha256(candidate_path), "issued_at_utc": issued_at_utc,
        "mission_id": MISSION_ID, "network_request_reservation": candidate["network_request_reservation"],
        "output_directory": candidate["output_directory"], "permit_sha256": file_sha256(permit_path),
        "request_class": candidate["request_class"], "run_id": RUN_ID,
        "schema_version": "OC3_AUTONOMOUS_RECOVERY_WORKER_CAPABILITY_002", "single_use": True,
        "stage_id": candidate["stage_id"], "state_sha256": file_sha256(state_path),
        "worker_argv_sha256": candidate["worker_argv_sha256"]})
    write_json_immutable(capability_path, capability)
    return capability


def validate_worker_capability(*, capability_path: Path, candidate_path: Path,
        permit_path: Path, authorization_path: Path, state_path: Path) -> dict[str, object]:
    capability = _load(capability_path, "RECOVERY_WORKER_CAPABILITY_INVALID")
    candidate = validate_candidate(candidate_path)
    required = {"application_body_reservation", "authorization_sha256", "candidate_path", "candidate_sha256", "issued_at_utc",
        "mission_id", "network_request_reservation", "output_directory", "permit_sha256", "request_class",
        "run_id", "schema_version", "sealed", "single_use", "stage_id", "state_sha256", "worker_argv_sha256"}
    expected_path = str(candidate_path.resolve().relative_to(PROJECT))
    if (set(capability) != required or capability.get("schema_version") != "OC3_AUTONOMOUS_RECOVERY_WORKER_CAPABILITY_002" or
            capability.get("run_id") != RUN_ID or capability.get("candidate_path") != expected_path or
            candidate.get("candidate_path") != expected_path or
            capability.get("candidate_sha256") != file_sha256(candidate_path) or
            capability.get("permit_sha256") != file_sha256(permit_path) or
            capability.get("authorization_sha256") != file_sha256(authorization_path) or
            capability.get("state_sha256") != file_sha256(state_path) or capability.get("mission_id") != MISSION_ID or
            capability.get("stage_id") != candidate["stage_id"] or
            capability.get("worker_argv_sha256") != candidate["worker_argv_sha256"] or
            capability.get("network_request_reservation") != candidate["network_request_reservation"] or
            capability.get("application_body_reservation") != candidate["application_body_reservation"] or
            capability.get("output_directory") != candidate["output_directory"] or capability.get("single_use") is not True):
        raise RecoveryEnvelopeError("RECOVERY_WORKER_CAPABILITY_INVALID")
    validate_permit(permit_path=permit_path, candidate_path=candidate_path, allow_consumed=True)
    if not permit_consumption_path(permit_path).is_file():
        raise RecoveryEnvelopeError("RECOVERY_WORKER_CAPABILITY_INVALID")
    if capability_consumption_path(capability_path).exists():
        raise RecoveryEnvelopeError("RECOVERY_WORKER_CAPABILITY_ALREADY_CONSUMED")
    return capability


def consume_worker_capability(*, capability_path: Path, candidate_path: Path,
                              consumed_at_utc: str) -> Path:
    capability = _load(capability_path, "RECOVERY_WORKER_CAPABILITY_INVALID")
    if (capability.get("run_id") != RUN_ID or
            capability.get("candidate_path") != str(candidate_path.resolve().relative_to(PROJECT)) or
            capability.get("candidate_sha256") != file_sha256(candidate_path)):
        raise RecoveryEnvelopeError("RECOVERY_WORKER_CAPABILITY_INVALID")
    marker = capability_consumption_path(capability_path)
    if marker.exists():
        raise RecoveryEnvelopeError("RECOVERY_WORKER_CAPABILITY_ALREADY_CONSUMED")
    write_json_immutable(marker, sealed({"candidate_path": str(candidate_path.resolve().relative_to(PROJECT)),
        "candidate_sha256": file_sha256(candidate_path), "run_id": RUN_ID,
        "capability_sha256": file_sha256(capability_path), "consumed_at_utc": consumed_at_utc,
        "schema_version": "OC3_AUTONOMOUS_RECOVERY_CAPABILITY_CONSUMPTION_002"}))
    return marker


def agentic_paths(generation: int) -> dict[str, Path]:
    return {"request": LEDGER_ROOT / f"AGENTIC_REPAIR_REQUEST_{generation:02d}.json",
        "patch": PROJECT / f"oc3/INPUTS/TECHNICAL_PATCH_MANIFEST_RUN_002_{generation:02d}.json",
        "contract": PROJECT / f"oc3/INPUTS/TECHNICAL_TRANSPORT_CONTRACT_RUN_002_{generation:02d}.json",
        "receipts": PROJECT / f"oc3/INPUTS/TECHNICAL_REPAIR_TEST_RECEIPTS_RUN_002_{generation:02d}.json"}


def begin_agentic_handoff(*, state_path: Path, candidate_path: Path, terminal_path: Path,
                          evidence: list[dict[str, str]]) -> dict[str, object]:
    state=validate_state(state_path); candidate=validate_candidate(candidate_path)
    terminal=_load(terminal_path,"RECOVERY_ACTION_TERMINAL_INVALID")
    if (candidate["action_kind"] != "OFFICIAL_SERVICE_DOCUMENTARY_PROBE" or
            candidate.get("run_id") != RUN_ID or terminal.get("run_id") != RUN_ID or
            terminal.get("failure_class") != "DOCUMENTARY_EVIDENCE_ACQUIRED" or
            state["registered_pending_action"] != binding(candidate_path) or not evidence or
            any(item != binding(PROJECT / item.get("path", "")) for item in evidence)):
        raise RecoveryEnvelopeError("AGENTIC_REPAIR_HANDOFF_INVALID")
    accounted=dict(terminal); accounted["terminal_sha256"]=file_sha256(terminal_path)
    classification={"decision":RECOVER_AUTONOMOUSLY,"failure_class":"DOCUMENTARY_EVIDENCE_ACQUIRED",
        "next_action_kind":"OFFLINE_TECHNICAL_REPAIR","reason":"AGENTIC_EXECUTION_LAYER_HANDOFF"}
    updated=account_action(state,accounted,classification,_load(RECOVERY_BUDGET,"RECOVERY_BUDGET_INVALID"))
    updated.pop("sealed",None); updated["last_action_terminal"]=binding(terminal_path)
    updated["permits_issued"]=state["permits_issued"]+1
    if updated.get("active") is not True:
        sealed_state=sealed(updated); _atomic_state(state_path,sealed_state); return sealed_state
    updated["current_stage"]="AWAITING_AGENTIC_TECHNICAL_REPAIR"
    paths=agentic_paths(updated["recovery_generation"]+1)
    request=sealed({"action_registry":binding(ACTION_REGISTRY),"active_adapter":state["active_adapter"],
        "allowed_path_prefixes":_load(MUTABLE_SURFACE,"MUTABLE_TECHNICAL_SURFACE_INVALID")["allowed_path_prefixes"],
        "current_git_head":__import__("subprocess").run(["git","rev-parse","HEAD"],cwd=PROJECT,check=True,capture_output=True,text=True).stdout.strip(),
        "diagnostic_and_documentary_evidence":evidence,"mission_id":MISSION_ID,"run_id":RUN_ID,
        "mutable_technical_surface":binding(MUTABLE_SURFACE),"parent_action_terminal":binding(terminal_path),
        "query_semantic_hashes":{r["id"]:r["semantic_sha256"] for r in _load(INVARIANTS,"SCIENTIFIC_INVARIANTS_INVALID")["queries"]},
        "recovery_generation":updated["recovery_generation"]+1,"recovery_graph":binding(RECOVERY_GRAPH),
        "required_tests":["FOCUSED_TECHNICAL","AFFECTED_RECOVERY","SOCKET_FIREWALLED_FULL_REGRESSION"],
        "schema_version":"OC3_SOURCE_METADATA_AGENTIC_REPAIR_REQUEST_001",
        "scientific_invariants":binding(INVARIANTS),"technical_contract_conclusions":[],
        "trigger_failure_class":"DOCUMENTARY_EVIDENCE_ACQUIRED"})
    write_json_immutable(paths["request"],request); updated["agentic_repair_request"]=binding(paths["request"])
    sealed_state=sealed(updated); _atomic_state(state_path,sealed_state); return sealed_state


def complete_agentic_handoff(*, state_path: Path) -> dict[str, object]:
    state=validate_state(state_path)
    if state["current_stage"] != "AWAITING_AGENTIC_TECHNICAL_REPAIR" or state["active"] is not True:
        raise RecoveryEnvelopeError("AGENTIC_REPAIR_HANDOFF_INVALID")
    paths=agentic_paths(int(state["recovery_generation"])+1)
    if not all(paths[k].is_file() for k in ("patch","contract","receipts")):
        return state
    patch=_load(paths["patch"],"TECHNICAL_PATCH_MANIFEST_INVALID")
    from .autonomous_recovery_envelope import validate_patch_manifest
    validate_patch_manifest(patch,_load(MUTABLE_SURFACE,"MUTABLE_TECHNICAL_SURFACE_INVALID"))
    request_binding=state.get("agentic_repair_request")
    if not isinstance(request_binding,dict): raise RecoveryEnvelopeError("AGENTIC_REPAIR_HANDOFF_INVALID")
    request=_load(PROJECT/request_binding["path"],"AGENTIC_REPAIR_HANDOFF_INVALID")
    invariants=_load(INVARIANTS,"SCIENTIFIC_INVARIANTS_INVALID")
    hashes={r["id"]:r["semantic_sha256"] for r in invariants["queries"]}
    if (request_binding != binding(PROJECT/request_binding["path"]) or
            request.get("run_id") != RUN_ID or patch.get("run_id") != RUN_ID or
            patch.get("base_commit") != request.get("current_git_head") or
            patch.get("parent_action_terminal") != state.get("last_action_terminal") or
            patch.get("recovery_generation") != int(state["recovery_generation"])+1 or
            patch.get("scientific_invariants_sha256_before") != file_sha256(INVARIANTS) or
            patch.get("scientific_invariants_sha256_after") != file_sha256(INVARIANTS) or
            patch.get("recovery_graph_sha256_before") != file_sha256(RECOVERY_GRAPH) or
            patch.get("recovery_graph_sha256_after") != file_sha256(RECOVERY_GRAPH) or
            patch.get("query_semantic_hashes_before") != hashes or
            patch.get("query_semantic_hashes_after") != hashes):
        raise RecoveryEnvelopeError("TECHNICAL_PATCH_IMMUTABLE_CONTRACT_CHANGED")
    contract=_load(paths["contract"],"TECHNICAL_TRANSPORT_CONTRACT_INVALID")
    required={"adapter_id","authority_resource_ids","authentication_mode","endpoint","evidence","http_method","implementation_path","parameter_serialization",
        "query_semantic_hashes","query_semantic_preservation_rule","redirect_policy","response_representation",
        "run_id","schema_version","sealed"}
    authorities=_load(TECHNICAL_AUTHORITIES,"TECHNICAL_AUTHORITIES_INVALID")
    adapter=next((row for row in authorities["adapters"] if row["adapter_id"]==contract.get("adapter_id")),None)
    if (set(contract)!=required or contract.get("run_id") != RUN_ID or adapter is None or
            contract["implementation_path"] != adapter["implementation_path"] or
            not isinstance(contract["authority_resource_ids"],list) or not contract["authority_resource_ids"] or
            not set(contract["authority_resource_ids"]).issubset(set(adapter["allowed_authority_resource_ids"])) or
            contract["query_semantic_hashes"]!=hashes or contract["query_semantic_preservation_rule"]!="BYTE_IDENTICAL_FROZEN_ADQL" or
            not isinstance(contract["endpoint"],str) or not contract["endpoint"] or
            contract["http_method"] not in ("GET","POST") or
            not isinstance(contract["parameter_serialization"],str) or not contract["parameter_serialization"] or
            not isinstance(contract["response_representation"],str) or not contract["response_representation"] or
            not isinstance(contract["authentication_mode"],str) or not contract["authentication_mode"] or
            not isinstance(contract["redirect_policy"],str) or not contract["redirect_policy"] or
            not contract["evidence"] or
            any(item not in request.get("diagnostic_and_documentary_evidence",[]) for item in contract["evidence"])):
        raise RecoveryEnvelopeError("TECHNICAL_TRANSPORT_CONTRACT_INVALID")
    for item in contract["evidence"]:
        if binding(PROJECT/item["path"]) != item: raise RecoveryEnvelopeError("TECHNICAL_TRANSPORT_CONTRACT_INVALID")
    receipts=_load(paths["receipts"],"TECHNICAL_REPAIR_TEST_RECEIPTS_INVALID")
    if (set(receipts) != {"all_required_passed","real_network_requests","run_id","schema_version","sealed","tests_executed"} or
            receipts.get("run_id") != RUN_ID or
            receipts.get("schema_version") != "OC3_SOURCE_METADATA_TECHNICAL_REPAIR_TEST_RECEIPTS_001" or
            receipts.get("all_required_passed") is not True or receipts.get("real_network_requests")!=0 or
            receipts.get("tests_executed") != request.get("required_tests")):
        raise RecoveryEnvelopeError("TECHNICAL_REPAIR_TEST_RECEIPTS_INVALID")
    body={k:v for k,v in state.items() if k!="sealed"}
    body.update({"current_stage":"AWAITING_NEXT_ACTION_REGISTRATION",
        "last_classification":{"decision":RECOVER_AUTONOMOUSLY,"failure_class":"DOCUMENTARY_TRANSPORT_CONTRACT_RESOLVED",
            "next_action_kind":"OFFLINE_TECHNICAL_REPAIR","reason":"VALIDATED_AGENTIC_TRANSPORT_CONTRACT"},
        "validated_patch_manifest":binding(paths["patch"]),"validated_transport_contract":binding(paths["contract"]),
        "validated_test_receipts":binding(paths["receipts"]),"sequence":state["sequence"]+1})
    updated=sealed(body); _atomic_state(state_path,updated); return updated


def transition_action(*, state_path: Path, candidate_path: Path, terminal_path: Path) -> tuple[dict[str, object], dict[str, object]]:
    state = validate_state(state_path); candidate = validate_candidate(candidate_path)
    if state["registered_pending_action"] != binding(candidate_path):
        raise RecoveryEnvelopeError("RECOVERY_ACTION_TRANSITION_INVALID")
    terminal = _load(terminal_path, "RECOVERY_ACTION_TERMINAL_INVALID")
    if terminal.get("run_id") != RUN_ID:
        raise RecoveryEnvelopeError("RECOVERY_RUN_ID_MISMATCH")
    terminal = dict(terminal); terminal["terminal_sha256"] = file_sha256(terminal_path)
    graph = _load(RECOVERY_GRAPH, "RECOVERY_GRAPH_INVALID")
    budget = _load(RECOVERY_BUDGET, "RECOVERY_BUDGET_INVALID")
    classification = classify_action_terminal(terminal, graph)
    if terminal.get("failure_class") == "ADAPTER_IMPLEMENTATION_DRIFT":
        classification={"decision":STOP_REQUIRES_HUMAN,"failure_class":"ADAPTER_IMPLEMENTATION_DRIFT",
            "next_action_kind":None,"reason":"ADAPTER_IMPLEMENTATION_DRIFT"}
    updated = account_action(state, terminal, classification, budget)
    updated["last_action_terminal"] = binding(terminal_path)
    if terminal.get("adapter_activated") is not None:
        authorities = _load(TECHNICAL_AUTHORITIES, "TECHNICAL_AUTHORITIES_INVALID")
        contract=candidate.get("technical_transport_contract")
        patch=candidate.get("technical_patch_manifest"); receipts=candidate.get("test_receipts")
        contract_document=_load(PROJECT/contract["path"],"TECHNICAL_TRANSPORT_CONTRACT_INVALID") if isinstance(contract,dict) else {}
        registry_adapter=next((row for row in authorities["adapters"]
            if row["adapter_id"]==terminal["adapter_activated"]),None)
        implementation=terminal.get("adapter_implementation_binding")
        actual_path=PROJECT/registry_adapter["implementation_path"] if registry_adapter else None
        actual_binding={"adapter_id":terminal["adapter_activated"],
            "implementation_path":registry_adapter["implementation_path"],
            "implementation_sha256":file_sha256(actual_path)} if actual_path and actual_path.is_file() else None
        if (candidate["action_kind"] != "OFFLINE_TECHNICAL_REPAIR" or
                terminal.get("failure_class") != "TECHNICAL_PATCH_VALIDATED" or
                registry_adapter is None or implementation != actual_binding or
                not isinstance(contract,dict) or contract != state.get("validated_transport_contract") or
                contract_document.get("implementation_path") != registry_adapter["implementation_path"] or
                patch != state.get("validated_patch_manifest") or receipts != state.get("validated_test_receipts") or
                terminal.get("technical_transport_contract") != contract or
                terminal.get("patch_manifest") != patch or terminal.get("test_receipts") != receipts or
                state.get("adapter_states",{}).get(terminal["adapter_activated"])!="AVAILABLE_UNVALIDATED"):
            raise RecoveryEnvelopeError("TECHNICAL_ADAPTER_NOT_VALIDATED")
        updated["adapter_states"]=dict(state["adapter_states"])
        if updated.get("active") is True:
            updated["active_adapter"] = terminal["adapter_activated"]
            updated["adapter_states"][terminal["adapter_activated"]]="ACTIVE"
            updated["active_adapter_binding"]={**actual_binding,
                "technical_patch_manifest":patch,"technical_transport_contract":contract,
                "test_receipts":receipts}
        else:
            updated["adapter_states"][terminal["adapter_activated"]]="VALIDATED_FOR_MISSION"
    updated["permits_issued"] = state["permits_issued"] + 1
    updated.pop("sealed", None)
    sealed_state = sealed(updated); _atomic_state(state_path, sealed_state)
    return sealed_state, sealed(classification)


def finalize_mission(*, state_path: Path, outcome: str) -> dict[str, object]:
    state = validate_state(state_path)
    if state.get("current_stage") != "AWAITING_SCIENTIFIC_FINALIZATION":
        raise RecoveryEnvelopeError("RECOVERY_MISSION_FINALIZATION_INVALID")
    body = {k: v for k, v in state.items() if k != "sealed"}
    body.update({"active": False, "current_stage": STATE_TERMINAL, "scientific_outcome": outcome,
        "state": STATE_TERMINAL, "sequence": state["sequence"] + 1})
    updated = sealed(body); _atomic_state(state_path, updated)
    return updated


def validate_standing_authorization(path: Path, *, state_path: Path,
                                    require_initial_state: bool = True) -> dict[str, object]:
    value = _load(path, "RECOVERY_STANDING_AUTHORIZATION_INVALID")
    required = {"action_registry", "authorized", "candidate_factory_sha256", "first_candidate", "initial_state_sha256",
        "mandate", "mission_id", "mission_runner_sha256", "mutable_technical_surface", "predecessor_run", "run_id",
        "policy_core_manifest", "recovery_budget", "recovery_graph", "schema_version",
        "scientific_invariants", "sealed", "technical_authorities"}
    if (set(value) != required or value.get("schema_version") != "OC3_SOURCE_METADATA_RECOVERY_STANDING_AUTHORIZATION_002" or
            value.get("authorized") is not True or value.get("mission_id") != MISSION_ID or value.get("run_id") != RUN_ID or
            (require_initial_state and value.get("initial_state_sha256") != file_sha256(state_path)) or
            value.get("first_candidate") != binding(FIRST_CANDIDATE) or
            value.get("predecessor_run") != binding(RUN_001_CLOSURE) or
            value.get("mandate") != binding(MANDATE) or value.get("policy_core_manifest") != binding(POLICY_MANIFEST) or
            value.get("scientific_invariants") != binding(INVARIANTS) or value.get("recovery_graph") != binding(RECOVERY_GRAPH) or
            value.get("recovery_budget") != binding(RECOVERY_BUDGET) or value.get("mutable_technical_surface") != binding(MUTABLE_SURFACE) or
            value.get("action_registry") != binding(ACTION_REGISTRY) or
            value.get("technical_authorities") != binding(TECHNICAL_AUTHORITIES) or
            value.get("mission_runner_sha256") != file_sha256(PROJECT / "oc3/oc3_source_metadata_recovery_mission_runner.py") or
            value.get("candidate_factory_sha256") != file_sha256(PROJECT / "oc3/oc3lib/source_metadata_recovery_factory.py")):
        raise RecoveryEnvelopeError("RECOVERY_STANDING_AUTHORIZATION_INVALID")
    return value


def write_candidate_idempotent(path: Path, candidate: dict[str, object]) -> None:
    data = canonical(candidate) + b"\n"
    if path.exists():
        if path.read_bytes() != data:
            raise RecoveryEnvelopeError("RECOVERY_CHILD_CANDIDATE_CONFLICT")
        return
    write_json_immutable(path, candidate)


def stop_mission(*, state_path: Path, reason: str) -> dict[str, object]:
    state = validate_state(state_path)
    body = {k: v for k, v in state.items() if k != "sealed"}
    body.update({"active": False, "current_stage": STOP_REQUIRES_HUMAN,
        "next_action_kind": None, "state": STOP_REQUIRES_HUMAN,
        "stop_reason": reason, "sequence": state["sequence"] + 1})
    updated = sealed(body); _atomic_state(state_path, updated)
    return updated
