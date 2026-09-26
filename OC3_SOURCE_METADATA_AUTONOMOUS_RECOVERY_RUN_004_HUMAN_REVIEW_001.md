# OC3 Source-Metadata Autonomous Recovery Run-004 Human Review Package 001

Status: **READY FOR HUMAN REVIEW; NOT AUTHORIZED; NOT STARTED**.

## Frozen identities

| Artifact | SHA-256 |
|---|---|
| Git-diff/runtime partition Amendment 001 | `340a7fb03c284324dc66cd80da829de9a80722a3c210b9a72b35696c97b3cf29` |
| Policy Core 004 | `b55ad28e1be138426d7075da21c4ceb8463541f53cd4fb8ace6edad887d248b8` |
| Policy Core Manifest 004 | `8f44f15d2fba98c235a67357c68f064af8c05de0361299f370ed61f7080e3a10` |
| First Candidate 004 | `df44cae128aa55528358bed426e2e16373a253799f02617a1383cae01588201c` |
| Candidate Validation 004 | `f472ded65385f6ece0961bd7a54c2096252e493c4e4fc7a51d565170ddf00e5a` |
| Waiting State 004 | `290965c7487d58a205d9cc343b499c8cbe9bb8f139eda682efa6499e29b4247f` |
| Inactive Mandate 004 | `2be1b280ac8af762b721ee0df3d16f6df165be5b7694bd6a2cdf84833f417ec7` |
| Partition implementation aggregate | `2b2fbd0e9b839613c54c9814291073fcdc37fa39872f2a752d04da5e9217bb55` |
| Run-004 control-plane aggregate | `3b65e28012c63661fcfec6d0a45bb1a43eb30a6de26cf5cb66b36a1036643ab1` |

The reserved standing-authorization path is
`oc3/OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_STANDING_AUTHORIZATION_004.json`.
It is absent. No candidate, mandate, review document or waiting state grants
execution authority.

## Exact proposed agent execution identity

```text
/home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/.venv/bin/python /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/oc3_source_metadata_recovery_mission_runner_run004.py --run-mission --state /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_STATE_004.json --standing-authorization /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_STANDING_AUTHORIZATION_004.json
```

`mission_execution_argv_sha256 = c5812946f6c4d28a6582bec0a333924feec59253deb514b58f9a6e2842a9878a`.

After a distinct explicit human authorization and materialization of the bound
Standing Authorization 004, the authorized agent executes this identity. The
human role is review and explicit authorization; the human is not required to
invoke the CLI manually.

## First action and inherited evidence

Run-004 prospectively reuses the exact sealed Run-003 documentary evidence as
read-only technical provenance. This is valid because the inherited authority
binds the exact evidence, adapter bytes, test receipts and frozen query hashes,
and records zero scientific rows, zero source values and zero material actions.
It grants no Run-003 runtime authority and spends no Run-004 budget.

The first candidate is therefore
`MATERIAL_SOURCE_METADATA_ACQUISITION`, using the already validated
`query_manager_public_anonymous_v1` adapter. It reserves at most five material
requests and 67,108,864 body bytes. No material action has been executed.

## Independent Run-004 budgets

| Class | Requests | Body bytes | Per-request cap | Concurrency | Retries/action |
|---|---:|---:|---:|---:|---:|
| Technical | 8 | 2,097,152 | 262,144 | 1 | 0 |
| Material | 5 | 67,108,864 | frozen per-resource caps | 1 | 0 |

All counters are zero and all budgets are unspent. Historical Run-003 traffic
is bound as provenance and is not charged to Run-004.

## Isolation and drift

Run-004 has fresh `*_004` state, authorization, candidate, ledger, permit,
capability, runtime and output identities. It reuses none of the Run-003
authorization, permit, capability, state, ledger or ephemeral identities.

`scientific_semantic_drift`, `observational_contract_drift`,
`provider_resource_drift`, `rights_drift`, `resource_scope_drift`,
`budget_drift` and `acceptance_criteria_drift` are all zero.

## Offline gates

- focused/adversarial tests: 30/30 PASS;
- full socket/DNS-firewalled regression: 1553/1553 PASS;
- real network requests: 0;
- Run-004 material actions: 0;
- final authorization created: false;
- Run-004 execution: `NOT_STARTED`.

Terminal package state:

- `POLICY_CORE_004_FROZEN`;
- `RUN_004_CANDIDATE_READY_FOR_HUMAN_REVIEW`;
- `RUN_004_WAITING_FOR_HUMAN_AUTHORIZATION`;
- `RUN_004_EXECUTION = NOT_STARTED`;
- `RUN_004_NETWORK_REQUESTS = 0`;
- `RUN_004_MATERIAL_ACTIONS = 0`.

No governance ambiguity remains in the partition contract or the agentic
execution actor. A future human decision must still review the exact identities
above and explicitly authorize or reject Run-004.
