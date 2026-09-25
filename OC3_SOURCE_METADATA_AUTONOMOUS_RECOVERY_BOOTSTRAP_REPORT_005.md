# OC3 Source-Metadata Autonomous Recovery Bootstrap Report 005

Status: **READY FOR AUTONOMOUS RECOVERY RUN-002 HUMAN REVIEW; INACTIVE**.

## Closed Run-001 predecessor

Run-001 remains a closed governed `STOP_REQUIRES_HUMAN` at commit
`57b520d3d3f849b9d0c0c554984f5688fe62786a`.

- Final-state SHA-256:
  `364905c88a55e65d6429caadea3614b4de34b2990eea1b2cc23cde435ae784ea`.
- Ledger aggregate:
  `af2db3858b15f23a4fdf5ef2365a8ebc2da7528455eaf9a28c178528b7d1178b`.
- Contradiction-evidence SHA-256:
  `6f3831aa4a0e8f7ea6a5a64d08f66af0addba66996440fa693a7d0af22dcaf96`.
- Issued Run-001 permit SHA-256:
  `badd14e4d398ff444a361bd929cfaed32f8bb3603bcf4a28b10d73bd2eaba314`;
  unconsumed.
- Frozen finding: `FIRST_CANDIDATE_SELF_PATH_BINDING_DEFECT`.
- Run-001 closure-binding SHA-256:
  `05597506939e6caec1193de6c650649b43182f65c087f33830a43d9028bb88d2`.

No Run-001 artifact was modified, removed, replayed, or reinterpreted. Its
standing authorization and unconsumed permit fail validation against Run-002.

## Run-002 control-plane revision

Operational identity:
`OC3-SOURCE-METADATA-AUTONOMOUS-RECOVERY-RUN-002`.

Scientific mission identity remains:
`OC3-SOURCE-METADATA-AUTONOMOUS-RECOVERY-ENVELOPE-001`.

The new `ONE_CANDIDATE_ONE_CANONICAL_PATH` invariant is implemented by
`oc3lib.source_metadata_recovery_governor.validate_candidate_self_binding`.
Every candidate now binds `run_id` and its canonical project-relative
`candidate_path`. Validation requires the actual non-symlink file path,
supervisor `--candidate`, worker `--candidate`, argv hashes, permit path/SHA,
and worker-capability path/SHA to agree exactly. Copies, moves, aliases,
symlinks, alternate permit bindings, and alternate capability bindings fail
closed before network access.

The candidate factory exposes no caller-selectable path. First Candidate 002
derives the fixed reviewed INPUT path; G02+ candidates derive deterministic
Run-002 ledger paths. Action Registry 002 changes only the control-plane schema
identity and supervisor/worker implementation bindings required by this
revision; its action families and scientific routing semantics are unchanged.

Run-002 has separate state, authorization, candidate ledger, mission ledger,
permit and consumption namespaces, capability-consumption namespace, and
runtime outputs. `RUN_ID` is required by state, authorization, candidate,
permit, capability, consumption markers, action terminals, agentic artifacts,
ledger records, and the mission final report.

## Frozen Run-002 identities

- First Candidate 002 canonical path:
  `oc3/INPUTS/OC3_SOURCE_METADATA_RECOVERY_FIRST_CANDIDATE_002.json`.
- First Candidate 002 SHA-256:
  `ea5cd023c6f31ff7eb537efc8b2ca18d401ced8b65d095d9dd08b62d40d65b7a`.
- Waiting State 002 SHA-256:
  `a737f6404bcc89627533022d5b36f568147628a310a3caadc2a1f81dbff90767`.
- Policy Core Manifest 002 SHA-256:
  `68aded93c58efc30d2708c42870b2bd69c4af253b1d0bd68334de16c321a15d7`.
- Pending Mandate 002 SHA-256:
  `3cf8692184f7e8ce091158af068e9c80193c8175f095dd6620875d7d49aa31ef`.
- Action Registry 002 SHA-256:
  `e35984d150f835b540fb69b727db9ff96f9314a4960c39d1c1fcc7b5ad94c5c2`.
- Mission Runner SHA-256:
  `895ed10a988303ad4eab5648cecc62de9c317ac6bd720b190301ae603af5198d`.
- Deterministic Candidate Factory SHA-256:
  `b3e298e6abbca0f7b7bd3d15d2d91534edb7245e5dc870f7a83c646daf6c3250`.
- Governor and self-path validator implementation SHA-256:
  `e5480beea1ec2c3d1ba4e0e4a2b364463cdbb9f3ce57e37e7c5940110cb432be`.
- Supervisor SHA-256:
  `67f9d90a43237ff5722542428dde6c826d5b1fcfbaecb979d35702f32dcab99f`.
- Worker SHA-256:
  `4e43c7c90856dbc2eae3ae0492738b29d3e83053d85a0e24cb974d7730ef74a4`.
- Control-plane implementation aggregate:
  `7a12091c5017903b0c22417b3f9b725bf050e812438b4638ca58a87a7791c7bf`.

First Candidate 002 was generated through the production factory, written at
its final path, reloaded, and independently recomputed byte-for-byte. Its
`candidate_path`, supervisor argv, and worker argv all resolve to that same
INPUTS file.

## Regression evidence

The focused production suite passed 43 of 43 tests. Its real supervisor-path
regression registered a factory-generated First Candidate 002, issued a
synthetic Run-002 permit, invoked the production supervisor argv, consumed the
permit, created the production worker capability, invoked the worker path
validation, consumed the capability, and produced a synthetic terminal. The
action implementation was replaced only after all real path and gate checks;
the socket boundary remained offline.

The tampering matrix rejects a moved candidate, same-byte copy, symlink,
modified self path, modified supervisor candidate path, modified worker
candidate path, alternate permit candidate path, and alternate capability
candidate path. Separate regressions prove Run-001 permit and authorization
non-reuse.

The production Mission Runner synthetic integration passed the complete
sequence: technical diagnostic, documentary evidence, agentic handoff,
bounded repair artifacts, resume, offline repair validation, material action,
and scientific terminal. Existing finite-loop, credentials, resource-bound,
resume, mutable repair, drift, query-tampering, and candidate-tampering tests
remain passing.

The full project regression ran under the repository socket/DNS firewall:

- 1,493 passed;
- 0 failed;
- 0 skipped;
- `real_network_requests=0`.

## Scientific and execution firewall

- Scientific Invariants SHA-256:
  `0d2b304e815a949cf7f69d44cd43148eb663fadb68afb47a7e9f767635a329f3`
  (byte-identical).
- Recovery Graph SHA-256:
  `19e7d6226d6550efbd32c62a4268d682e448f15fb3c490550471286943587fb7`
  (byte-identical).
- Recovery Budget SHA-256:
  `e399cba2ece0c8a15f7c237552e13f5a5453109ad21f3c3545427c17fce0956f`
  (byte-identical).
- Technical Authorities Registry V2 SHA-256:
  `187ba6da5a85caf38a72988e1b95f2184903913ff923ba6611dacf60ebbcda36`
  (byte-identical).
- All five scientific query semantic hashes remain unchanged.
- Query Manager and TAP remain `AVAILABLE_UNVALIDATED`.
- Standing Authorization 002: absent.
- Run-002 permit root: absent.
- Run-002 mission ledger: absent.
- Run-002 runtime output root: absent.
- Real network requests, schema responses, source counts, source rows, holdout
  source accesses, and observed source values: zero.

No source data were observed. No cross-observer identity or morphology claim
is made.

READY FOR AUTONOMOUS RECOVERY RUN-002 HUMAN REVIEW.

RUN 001 remains a closed governed STOP.

RUN 002 uses a fresh operational namespace and requires a new standing authorization.

Every candidate now binds exactly one canonical execution path.

First Candidate 002 path, supervisor argv, worker argv, permit and capability are identical by construction.

RUN-001 permit and authorization cannot be reused.

Scientific Invariants remain byte-identical.

Recovery Graph remains byte-identical.

No real network occurred.

No source data were observed.
