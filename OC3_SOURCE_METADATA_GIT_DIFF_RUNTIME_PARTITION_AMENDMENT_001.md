# OC3 Source-Metadata Git-Diff / Runtime-State Partition Amendment 001

Status: **PROSPECTIVE; OFFLINE; FROZEN FOR RUN-004 REVIEW**.

## Defect and scope

Run-003 closed at `STOP_REQUIRES_HUMAN / TECHNICAL_PATCH_GIT_DIFF_STATE_PATH_BINDING_CONFLICT`.
Its repair comparison included the legitimately mutated Run-003 state, while the patch
manifest correctly prohibited that state from the mutable technical surface. Run-003,
its authorization, state, ledger, permit, capability and terminal evidence remain
immutable historical evidence.

This amendment changes only control-plane accounting. It does not alter queries,
scientific semantics, observational contracts, providers, rights, budgets, action
outcomes or self-repair limits.

## Exhaustive partition

Every path in the Git repair comparison is classified exactly once as:

1. `MUTABLE_PATCH_CHANGES`: exact members of the existing frozen mutable technical
   surface and the only paths admitted to a technical patch manifest;
2. `AUTHORIZED_RUNTIME_CHANGES`: exact mission-owned runtime artifacts whose current
   bytes, schema, seal, Run ID, authorization binding and lifecycle history validate;
3. `FORBIDDEN_CHANGES`: every other path.

The union is exhaustive and disjoint. No path is ignored. A nonempty forbidden class
fails closed. Runtime paths never enter a patch manifest and never consume a repair
episode merely because their lifecycle changes normally.

## Runtime-state authority

The state exception is an exact path identity supplied by the active run. It is not a
glob or naming heuristic. Admission requires canonical identity, the expected schema
and Run ID, a valid canonical seal, the active standing-authorization binding, an
allowed active handoff stage, a valid parent terminal binding, a valid repair-request
binding, and validation by the run-specific state validator. The partition records its
current SHA-256 and lifecycle coordinates.

A different run's state, predecessor state, tampered state, unexpected lifecycle
transition, or state placed in the patch manifest fails closed.

## Run-004 consequence

Run-004 uses a fresh state, authorization path, ledger, permit, capability and runtime
namespace. Its policy may cite exact sealed Run-003 documentary evidence read-only,
because those two public technical responses and their zero-scientific-value terminal
are preserved byte-for-byte. That reuse grants no material result and spends no
Run-004 request budget. The adapter implementation and frozen ADQL must be rehashed and
the inherited technical contract validated offline before Run-004 authorization.

Execution remains agentic after explicit human authorization. The reviewed command is
the cryptographic execution identity; the human is not required to invoke it manually.

## Drift declaration

| Domain | Drift |
|---|---:|
| scientific semantics | 0 |
| observational contract | 0 |
| provider/resource identity | 0 |
| rights | 0 |
| resource scope | 0 |
| budget | 0 |
| acceptance criteria | 0 |
