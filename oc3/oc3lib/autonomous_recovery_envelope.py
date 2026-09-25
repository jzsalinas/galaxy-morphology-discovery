"""Generic finite recovery-policy engine with no domain or network dependency."""
from __future__ import annotations

from copy import deepcopy
import re


RECOVER_AUTONOMOUSLY = "RECOVER_AUTONOMOUSLY"
FINALIZE_SCIENTIFIC = "FINALIZE_SCIENTIFIC"
STOP_REQUIRES_HUMAN = "STOP_REQUIRES_HUMAN"
DECISIONS = (RECOVER_AUTONOMOUSLY, FINALIZE_SCIENTIFIC, STOP_REQUIRES_HUMAN)

ACTION_COMPLETED = "ACTION_COMPLETED"
ACTION_RECOVERABLE_TECHNICAL_FAILURE = "ACTION_RECOVERABLE_TECHNICAL_FAILURE"
ACTION_RESOURCE_BOUND = "ACTION_RESOURCE_BOUND"
ACTION_INTEGRITY_FAILURE = "ACTION_INTEGRITY_FAILURE"
ACTION_STOP_REQUIRED = "ACTION_STOP_REQUIRED"


class RecoveryEnvelopeError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _sha(value: object, code: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise RecoveryEnvelopeError(code)
    return value


def validate_recovery_graph(graph: dict[str, object]) -> dict[str, object]:
    required = {"action_families", "failure_routes", "human_required_classes",
        "nonrecoverable_scientific_classes", "schema_version", "unmapped_policy"}
    if (set(graph) - {"sealed"} != required or
            graph.get("schema_version") != "OC3_SOURCE_METADATA_RECOVERY_GRAPH_001" or
            graph.get("unmapped_policy") != STOP_REQUIRES_HUMAN):
        raise RecoveryEnvelopeError("RECOVERY_GRAPH_INVALID")
    families = graph.get("action_families")
    if not isinstance(families, list) or len(families) != len(set(families)) or not families:
        raise RecoveryEnvelopeError("RECOVERY_GRAPH_INVALID")
    routes = graph.get("failure_routes")
    if not isinstance(routes, list) or not routes:
        raise RecoveryEnvelopeError("RECOVERY_GRAPH_INVALID")
    seen = set()
    for route in routes:
        if (not isinstance(route, dict) or set(route) !=
                {"decision", "failure_class", "guard", "next_action_kind"}):
            raise RecoveryEnvelopeError("RECOVERY_GRAPH_INVALID")
        key = route["failure_class"]
        if key in seen or route["decision"] not in DECISIONS:
            raise RecoveryEnvelopeError("RECOVERY_GRAPH_INVALID")
        seen.add(key)
        next_kind = route["next_action_kind"]
        if route["decision"] == RECOVER_AUTONOMOUSLY and next_kind not in families:
            raise RecoveryEnvelopeError("RECOVERY_GRAPH_INVALID")
        if route["decision"] != RECOVER_AUTONOMOUSLY and next_kind is not None:
            raise RecoveryEnvelopeError("RECOVERY_GRAPH_INVALID")
    return graph


def classify_action_terminal(terminal: dict[str, object], graph: dict[str, object]) -> dict[str, object]:
    """Classify an action terminal without converting it into a mission terminal."""
    validate_recovery_graph(graph)
    failure = terminal.get("failure_class") or terminal.get("error_code") or terminal.get("state")
    for route in graph["failure_routes"]:
        if route["failure_class"] != failure:
            continue
        guard = route["guard"]
        if guard == "BEFORE_SOURCE_VALUES" and terminal.get("source_values_accepted", 0) != 0:
            return {"decision": STOP_REQUIRES_HUMAN, "failure_class": failure,
                "next_action_kind": None, "reason": "RECOVERY_GUARD_FAILED"}
        if guard == "REPRESENTATION_LEVEL_PROVEN" and terminal.get("representation_level_proven") is not True:
            return {"decision": STOP_REQUIRES_HUMAN, "failure_class": failure,
                "next_action_kind": None, "reason": "RECOVERY_GUARD_FAILED"}
        return {"decision": route["decision"], "failure_class": failure,
            "next_action_kind": route["next_action_kind"], "reason": "EXPLICIT_RECOVERY_GRAPH_ROUTE"}
    return {"decision": graph["unmapped_policy"], "failure_class": failure,
        "next_action_kind": None, "reason": "NO_EXPLICIT_RECOVERY_GRAPH_ROUTE"}


def account_action(state: dict[str, object], terminal: dict[str, object],
                   classification: dict[str, object], budget: dict[str, object]) -> dict[str, object]:
    """Apply actual action deltas and finite-loop rules to an active mission state."""
    if state.get("active") is not True or state.get("state") != "ACTIVE":
        raise RecoveryEnvelopeError("RECOVERY_MISSION_NOT_ACTIVE")
    result = deepcopy(state)
    request_class = terminal.get("request_class")
    requests = terminal.get("network_requests_started", 0)
    body = terminal.get("application_body_bytes_read", 0)
    if type(requests) is not int or requests < 0 or type(body) is not int or body < 0:
        raise RecoveryEnvelopeError("ACTION_ACCOUNTING_INVALID")
    if request_class == "TECHNICAL":
        result["technical_requests_remaining"] -= requests
        result["technical_body_bytes_remaining"] -= body
    elif request_class == "MATERIAL":
        result["material_requests_remaining"] -= requests
        result["material_body_bytes_remaining"] -= body
    elif requests or body:
        raise RecoveryEnvelopeError("ACTION_REQUEST_CLASS_INVALID")
    if min(result["technical_requests_remaining"], result["technical_body_bytes_remaining"],
           result["material_requests_remaining"], result["material_body_bytes_remaining"]) < 0:
        classification = {"decision": STOP_REQUIRES_HUMAN,
            "failure_class": classification.get("failure_class"), "next_action_kind": None,
            "reason": "RECOVERY_BUDGET_EXHAUSTED"}
    result["registered_pending_action"] = None
    result["last_action_terminal_sha256"] = _sha(
        terminal.get("terminal_sha256"), "ACTION_TERMINAL_SHA_INVALID")
    decision = classification["decision"]
    if terminal.get("action_kind") == "OFFLINE_TECHNICAL_REPAIR":
        result["code_repair_generation"] += 1
        if result["code_repair_generation"] > budget["MAX_CODE_REPAIR_GENERATIONS"]:
            decision = STOP_REQUIRES_HUMAN
            classification = {**classification, "decision": decision, "next_action_kind": None,
                "reason": "CODE_REPAIR_GENERATION_LIMIT_REACHED"}
    if decision == RECOVER_AUTONOMOUSLY:
        failure = str(classification["failure_class"])
        occurrences = dict(result.get("technical_failure_occurrences", {}))
        occurrences[failure] = occurrences.get(failure, 0) + 1
        result["technical_failure_occurrences"] = occurrences
        result["recovery_generation"] += 1
        if (result["recovery_generation"] > budget["MAX_RECOVERY_GENERATIONS"] or
                occurrences[failure] > budget["MAX_OCCURRENCES_SAME_TECHNICAL_FAILURE_CLASS"] or
                result["technical_requests_remaining"] < 0 or result["technical_body_bytes_remaining"] < 0):
            decision = STOP_REQUIRES_HUMAN
            classification = {**classification, "decision": decision, "next_action_kind": None,
                "reason": "FINITE_RECOVERY_LIMIT_REACHED"}
        else:
            result.update({"active": True, "state": "ACTIVE",
                "current_stage": "AWAITING_NEXT_ACTION_REGISTRATION",
                "next_action_kind": classification["next_action_kind"]})
    if decision == FINALIZE_SCIENTIFIC:
        result.update({"current_stage": "AWAITING_SCIENTIFIC_FINALIZATION",
            "next_action_kind": None})
    elif decision == STOP_REQUIRES_HUMAN:
        result.update({"active": False, "state": STOP_REQUIRES_HUMAN,
            "current_stage": STOP_REQUIRES_HUMAN, "next_action_kind": None,
            "stop_reason": classification["reason"]})
    result["last_classification"] = classification
    result["sequence"] += 1
    return result


def validate_patch_manifest(manifest: dict[str, object], mutable_surface: dict[str, object]) -> None:
    """Fail closed unless a repair changes only the frozen technical surface."""
    required = {"base_commit", "changed_paths", "claimed_repair_scope", "firewall_hash_after",
        "firewall_hash_before", "parent_action_terminal", "patch_diff_sha256", "recovery_generation",
        "recovery_graph_sha256_after", "recovery_graph_sha256_before", "schema_version",
        "scientific_invariants_sha256_after", "scientific_invariants_sha256_before",
        "technical_failure_class", "tests_executed", "query_semantic_hashes_after",
        "query_semantic_hashes_before"}
    observed = set(manifest) - {"sealed"}
    if observed not in (required, required | {"run_id"}):
        raise RecoveryEnvelopeError("TECHNICAL_PATCH_MANIFEST_INVALID")
    allowed = tuple(mutable_surface.get("allowed_path_prefixes", []))
    changed = manifest.get("changed_paths")
    if not allowed or not isinstance(changed, list) or not changed or any(
            not isinstance(row, dict) or set(row) != {"after_sha256", "before_sha256", "path"} or
            not str(row["path"]).startswith(allowed) for row in changed):
        raise RecoveryEnvelopeError("TECHNICAL_PATCH_OUTSIDE_MUTABLE_SURFACE")
    immutable_pairs = (
        ("scientific_invariants_sha256_before", "scientific_invariants_sha256_after"),
        ("recovery_graph_sha256_before", "recovery_graph_sha256_after"),
        ("query_semantic_hashes_before", "query_semantic_hashes_after"),
        ("firewall_hash_before", "firewall_hash_after"),
    )
    if any(manifest[a] != manifest[b] for a, b in immutable_pairs):
        raise RecoveryEnvelopeError("TECHNICAL_PATCH_IMMUTABLE_CONTRACT_CHANGED")
