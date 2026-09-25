"""Mission-level controller that separates action and mission terminals."""
from __future__ import annotations

from copy import deepcopy

from .autonomous_recovery_envelope import (
    FINALIZE_SCIENTIFIC, RECOVER_AUTONOMOUSLY, STOP_REQUIRES_HUMAN,
    account_action, classify_action_terminal,
)


def controller_step(state: dict[str, object], terminal: dict[str, object],
                    graph: dict[str, object], budget: dict[str, object]) -> dict[str, object]:
    """Advance one action and return a mission-level directive."""
    classification = classify_action_terminal(terminal, graph)
    updated = account_action(state, terminal, classification, budget)
    decision = updated["last_classification"]["decision"]
    if decision == RECOVER_AUTONOMOUSLY:
        directive = "GENERATE_AND_REGISTER_NEXT_ACTION"
    elif decision == FINALIZE_SCIENTIFIC:
        directive = "FINALIZE_SCIENTIFIC_MISSION"
    else:
        directive = STOP_REQUIRES_HUMAN
    return {"classification": updated["last_classification"], "directive": directive,
        "state": updated}


def synthetic_replay(initial_state: dict[str, object], terminals: list[dict[str, object]],
                     graph: dict[str, object], budget: dict[str, object]) -> dict[str, object]:
    """Deterministic offline controller replay used by regression tests."""
    state = deepcopy(initial_state); trace = []
    for terminal in terminals:
        step = controller_step(state, terminal, graph, budget)
        trace.append({"directive": step["directive"],
            "failure_class": step["classification"]["failure_class"]})
        state = step["state"]
        if step["directive"] != "GENERATE_AND_REGISTER_NEXT_ACTION":
            return {"state": state, "trace": trace, "terminal_directive": step["directive"]}
        state["registered_pending_action"] = {"synthetic": True}
        state["registered_pending_action"] = None
    return {"state": state, "trace": trace, "terminal_directive": trace[-1]["directive"] if trace else None}
