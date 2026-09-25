# OC3 Source-Metadata Autonomous Recovery Production Specification 002

The production invariant is `ACTION_TERMINAL != MISSION_TERMINAL`. `NEXT_CANDIDATE` is a deterministic function of durable state, the bound parent terminal, immutable Action Registry, immutable Recovery Graph, remaining budgets and the deterministic patch-manifest location for repair actions.

The Mission Runner is the sole top-level production entry point after standing authorization. It persists every action terminal before classification, creates no child before durable transition, and returns only at `SCIENTIFIC_TERMINAL`, `STOP_REQUIRES_HUMAN`, or a safely persisted uncontracted crash. Control-plane continuation after a durable transition is allowed. Consumed network/material actions without a terminal are never replayed.

All five registered action families have a production executor. Network executors remain behind distinct single-use permits and capabilities. Documentary URLs come only from the Technical Authorities Registry. Scientific ADQL originates byte-for-byte from the Scientific Invariants Manifest. Technical adapters transport caller-owned query text and cannot select scientific fields, predicates, tables or limits.

Agentic repair may touch only the Mutable Technical Surface. The governor independently compares the Git diff with the sealed patch manifest and rejects changes to science, graph, registries, Policy Core, runner, governor, factory, pilot frame or scientific validators.
