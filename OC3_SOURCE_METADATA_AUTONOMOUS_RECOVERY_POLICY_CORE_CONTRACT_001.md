# OC3 Autonomous Recovery Policy Core Contract 001

The generic Policy Core implements finite action classification, separate technical/material accounting, loop prevention, single-use permits and worker capabilities, action transition, mission finalization and stop. It contains no Data Lab endpoint, query, target, holdout or scientific criterion. Domain semantics live in immutable external manifests.

The Policy Core manifest binds the generic engine, domain governor, controller, candidate factory, supervisor, worker and this contract by SHA-256. After activation any mutation requires `STOP_REQUIRES_HUMAN`. The core cannot authorize itself, expand budgets or authority, change the Recovery Graph or Scientific Invariants Manifest, restore a consumed gate, expose credentials, push, merge main or force-push.

Candidate generation is dynamic; candidate eligibility rules are immutable. Every candidate binds its parent action terminal, recovery generation, allowed action kind, trigger class, authority manifests, remaining budgets, implementation aggregate, optional technical patch, exact argv and network reservations. Unknown action kinds and implicit fallbacks fail closed.
