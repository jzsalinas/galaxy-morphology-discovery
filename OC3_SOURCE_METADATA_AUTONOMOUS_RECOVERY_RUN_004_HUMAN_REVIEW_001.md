# OC3 Source-Metadata Autonomous Recovery Run-004 Human Review Package 001

Status: **READY FOR HUMAN REVIEW; NOT AUTHORIZED; NOT STARTED**.

## Frozen identities

| Artifact | SHA-256 |
|---|---|
| Git-diff/runtime partition Amendment 001 | `d04110def96cf7bfcc846fcae5f375d6a5523c7302ec8e33d2c14e69ab817514` |
| Policy Core 004 | `3c7222eb3090dd44a888da2358a7ed4d90b12e2e7a47bf1f0c24cd494145ba21` |
| Policy Core Manifest 004 | `58c11361b81a0ed7fb017982367e6a043adc0b704db2dbee9423d57d9738acff` |
| First Candidate 004 | `49bb2fcb19c69f8cfebf15a8f31858ccea049e8fcdc23295e46bf73264503598` |
| Candidate Validation 004 | `090e5120d1b4a68ad9b455703b21422077700d6ed596eafe3d020ee676e49277` |
| Waiting State 004 | `159b831f2214549cbf043074dadadf9d6ad22e0a371a3d090ecf9f7835bc9c98` |
| Inactive Mandate 004 | `db41cf75a54443e7bcaf61702e12af1960201b24adafb00af89e025637a34c08` |
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

