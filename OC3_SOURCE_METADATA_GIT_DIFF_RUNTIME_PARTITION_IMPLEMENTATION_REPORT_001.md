# OC3 Source-Metadata Git-Diff / Runtime-State Partition Implementation Report 001

Status: **OFFLINE PROSPECTIVE IMPLEMENTATION COMPLETE**.

## Defect repaired

Run-003's `_git_changed_paths` in
`oc3/oc3lib/source_metadata_recovery_executors_run003.py` lines 60–71 returned
one undifferentiated set containing every base-tracked change. Its offline
repair check at lines 106–109 then required that set to equal the technical
patch manifest. A legitimate tracked state transition therefore could neither
be declared as a technical patch nor be accounted for separately. Run-003's
result remains the immutable historical terminal
`STOP_REQUIRES_HUMAN / TECHNICAL_PATCH_GIT_DIFF_STATE_PATH_BINDING_CONFLICT`.

The prospective Run-004 implementation introduces
`oc3/oc3lib/source_metadata_git_change_partition.py`. It classifies every
comparison path exactly once as `MUTABLE_PATCH_CHANGES`,
`AUTHORIZED_RUNTIME_CHANGES`, or `FORBIDDEN_CHANGES`. The union is checked for
exhaustiveness and disjointness. A nonempty forbidden class fails closed.

## Runtime-state validation

Runtime admission uses one exact Run-004 state path, not a pattern. The state
must have a valid canonical identity, schema, seal, Run ID, standing
authorization binding, active lifecycle stage, sequence, parent terminal,
agentic repair request, recovery generation, ledger prefix and, at execution
time, registered candidate binding. The current SHA-256 and lifecycle
coordinates are recorded in partition evidence. Runtime state never enters the
patch manifest and ordinary lifecycle mutation does not consume a self-repair
episode.

The handoff and executor independently recompute the partition. Their state
hashes may differ only through the registered-action lifecycle transition; the
path classes and exact runtime identity must remain equal and each state must
validate at its own authoritative stage.

## Verification

Focused/adversarial validation: 30/30 passed, including 18 partition tests and
12 Run-004 preparation tests. The partition cases cover the 15 required
adversarial scenarios plus wrong authorization, broken history and the
registered-action runtime transition.

The full lifecycle-aware socket/DNS-firewalled regression passed 1553/1553,
with zero failures, zero skips and zero real network requests. It leaves the
historical test suite untouched and replaces four state-dependent assertions:
three Run-003 preauthorization assumptions and one exact `oc3/INPUTS`
inventory assumption. The replacement inventory test binds the closed Run-003
base commit `260abd2ab49977453176b939f07803aad0772b65` and requires exactly the
11 declared Run-004 input additions.

Logs:

- focused: `oc3/environment_setup/OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_RUN_004_FOCUSED_TESTS_001.log`, SHA-256 `94c3c45fae6d0294a3ae0feecdcd40fd807233bbebe42ea79bfacdd8de8f1c0f`;
- full: `oc3/environment_setup/OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_RUN_004_FULL_REGRESSION_001.log`, SHA-256 `285aac7f38d5904b3094f31c06fd611206813fe98f0b48cb3f7382fa65a5a25d`;
- replay receipt: `oc3/environment_setup/OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_RUN_004_OFFLINE_REPLAY_RECEIPT_001.json`, SHA-256 `a724e6898a1a79301246add529191f44bce7bba270d640805a3693aee5a4f46b`.

## Frozen identities and drift

The implementation aggregate is
`2b2fbd0e9b839613c54c9814291073fcdc37fa39872f2a752d04da5e9217bb55`.
The Run-004 control-plane aggregate is
`3b65e28012c63661fcfec6d0a45bb1a43eb30a6de26cf5cb66b36a1036643ab1`.

Scientific semantics, observational contract, provider/resource identity,
rights, resource scope, budgets and acceptance criteria each have drift zero.
The mutable technical surface remains exactly the two previously frozen
prefixes. No network request, material acquisition, permit, capability,
standing authorization or Run-004 execution occurred.

