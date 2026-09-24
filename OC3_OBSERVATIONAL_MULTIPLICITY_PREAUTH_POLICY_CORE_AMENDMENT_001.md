# OC3 Observational Multiplicity Preauthorization Policy-Core Amendment 001

Status: prospective governance amendment before standing authorization. It authorizes no execution, permit, activation, network access, or observational-value read.

## Reason

The reviewed V1 policy core correctly failed closed because it encoded Candidate 002 as the first-action identity. Candidate 002 is historically preserved and superseded: its command vector does not parse as the production executor interface. No real state transition occurred because the mission was never active.

## Amendment

Policy Core V2 removes first-action identity from universal Python constants. The sealed waiting state supplies `first_candidate` as exactly `{path, sha256}`. State validation resolves that path inside the project, verifies the file and full-file SHA, requires canonical sealed JSON, and applies the generic autonomous-action validator.

A future standing authorization must independently bind the exact waiting-state path/SHA and the exact first-candidate path/SHA copied from that state. Activation derives the candidate only from state. Before any action has completed, registration accepts only the state-bound candidate. After completion, registration remains generic.

This amendment changes governance only. It preserves the scientific question, `GLOBAL_IDENTITY_WITH_ALL_VALID_VIEWS`, all four scientific terminals, authority classes, budgets, scientific firewall, `CROSS_OBSERVER_SOURCE_GROUPING_REQUIRES_PROSPECTIVE_CONTRACT`, and prohibitions on Panel V3, P1, PHOTSYS work, and morphology learning.

## Versioning and immutability

V1 contract and Manifest 001 remain immutable historical evidence. V2 uses Contract 002, Manifest 002, Mandate 002, Runbook 002, and the prospectively resealed waiting state. After a future authorization binds Manifest 002, any policy-member change yields `POLICY_CORE_MISMATCH` or `POLICY_CORE_CHANGE_REQUIRED` and requires `STOP_REQUIRES_HUMAN`.

The prospective waiting state starts again at sequence zero because no standing authorization, activation, permit, or real mission transition ever existed. It retains the full 12-request and 16,777,216-byte budgets, zero issued permits, no registered action, and no scientific outcome. This reset is state preparation before authorization, not a retrospective lifecycle rewrite.
