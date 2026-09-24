# OC3 autonomy policy core contract 001

## Purpose and boundary

The policy core answers one deterministic question: whether a proposed action is inside the active human mandate. It never determines scientific truth. An epistemically material execution requires both an action-specific validator and the universal autonomy policy.

The frozen policy-core manifest binds this contract, `oc3/oc3lib/autonomy_governor.py`, and `oc3/oc3_autonomy_governor.py` by path and SHA-256. A future standing authorization binds the exact manifest SHA-256. Once the mission is `ACTIVE`, any mismatch in a bound member is `POLICY_CORE_MISMATCH` and requires `STOP_REQUIRES_HUMAN`; the autonomous agent may not update or relax the policy core.

## Generic action contract

Every prospective material candidate contains one closed `autonomy_policy` object with schema `OC3_AUTONOMOUS_ACTION_CONTRACT_001`. It binds the action kind, stage, scope, canonical candidate payload hash, command hash, implementation aggregate, frozen specification, action-validation receipt, literal resource manifest when networked, authority classes, request/body/retry/concurrency reservations, resume rule, scientific firewall, prohibited-scope assertions, Git assertions, permit output path, and standing-mandate SHA.

The candidate payload hash is SHA-256 of canonical JSON for the candidate root excluding `autonomy_policy` and `sealed`. The full candidate file SHA-256 is independently bound by registration, state, permit, and ledger.

An action-validation receipt is canonical, sealed, zero-network evidence that an action-specific validator accepted the candidate payload against its frozen implementation and specification. The universal governor verifies the receipt and validator identities without replacing their action-specific checks.

## Lifecycle

A standing authorization must bind the exact mandate SHA, policy-core manifest SHA, and waiting-state file SHA. Activation is one-time, snapshots the waiting state, appends an activation record, increments sequence, consumes no budget, and atomically produces `ACTIVE`.

An active mission may register one validated pending action when no unresolved action exists. Policy evaluation may issue one immutable candidate-declared permit. The executor records immutable consumption intent before material work. A completed transition requires the consumed permit, a real sealed terminal artifact, matching stage/scope where exposed, matching counters, and deltas no greater than permit reservations.

A consumed permit without a valid terminal cannot be replayed automatically. Without a prospectively frozen restart rule the mission enters `STOP_REQUIRES_HUMAN` through the governed STOP transition.

STOP and scientific-terminal transitions preserve budgets, snapshot state, append sealed ledger evidence, set `active=false`, and prohibit further permit issuance. Scientific finalization accepts only the four mandate outcomes and validates artifact identities, not the scientific conclusion.
