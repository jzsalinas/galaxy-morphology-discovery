# OC3 Source-Metadata Autonomous Recovery Production Specification 002

The production invariant is `ACTION_TERMINAL != MISSION_TERMINAL`. `NEXT_CANDIDATE` is a deterministic function of durable state, the bound parent terminal, immutable Action Registry, immutable Recovery Graph, remaining budgets and the deterministic patch-manifest location for repair actions.

The Mission Runner is the sole top-level production entry point after standing authorization. It persists every action terminal before classification, creates no child before durable transition, and returns only at `SCIENTIFIC_TERMINAL`, `STOP_REQUIRES_HUMAN`, the durable nonhuman `AWAITING_AGENTIC_TECHNICAL_REPAIR` handoff, or a safely persisted uncontracted crash. Control-plane continuation after a durable transition is allowed. Consumed network/material actions without a terminal are never replayed.

All five registered action families have a production executor. Network executors remain behind distinct single-use permits and capabilities. Documentary URLs come only from the Technical Authorities Registry. Scientific ADQL originates byte-for-byte from the Scientific Invariants Manifest. Technical adapters transport caller-owned query text and cannot select scientific fields, predicates, tables or limits.

Agentic repair may touch only the Mutable Technical Surface. The governor independently compares the Git diff with the sealed patch manifest and rejects changes to science, graph, registries, Policy Core, runner, governor, factory, pilot frame or scientific validators.

Successful documentary retrieval establishes only `DOCUMENTARY_EVIDENCE_ACQUIRED`. It cannot establish a transport contract. The runner accounts the documentary action and writes a sealed `AGENTIC_REPAIR_REQUEST_<generation>.json` before returning `AGENTIC_REPAIR_REQUIRED`. This state remains active under the same standing authorization, has no repair candidate or pending permit, and requires bounded Codex technical reasoning rather than human reauthorization.

Codex must inspect only the bound evidence and Mutable Technical Surface, then either stop the mission or create the generation-derived patch manifest, compact transport contract and complete offline test receipts. `Mission Runner --resume` validates those exact bindings before it deterministically creates an `OFFLINE_TECHNICAL_REPAIR` candidate. Missing artifacts preserve the handoff. Invalid artifacts stop closed.

An adapter begins as `AVAILABLE_UNVALIDATED`. The offline repair executor obtains its identity from the validated transport contract, proves the actual Git path and content hashes against the patch manifest, and reports that exact contract binding. Only the successful repair transition makes the adapter `ACTIVE`. Material candidate generation requires that active evidence-bound state. No executor may activate an adapter from a hard-coded default.
