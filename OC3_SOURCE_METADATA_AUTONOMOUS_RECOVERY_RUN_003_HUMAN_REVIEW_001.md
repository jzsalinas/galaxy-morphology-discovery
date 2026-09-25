# OC3 Source-Metadata Autonomous Recovery Run-003 Human Review Package 001

Status: **READY FOR HUMAN REVIEW; NOT AUTHORIZED; NOT STARTED**.

## Frozen identities

| Artifact | SHA-256 |
|---|---|
| Policy Core 003 | `6d19ae1732b12863cb8e9d83b174d90ae114e72f0e10133568e48f28161cbfdd` |
| Policy Core Manifest 003 | `c9a10c82ac019bd14c9a0f925c28411ede638b0f1eca686e5dd55b98af9839cb` |
| First Candidate 003 | `b1c270b5a490400e35f509563b214cb56ee9780ed4cbcdeb058c6f1c4aff8eb3` |
| Candidate Validation 003 | `9dc00e87fdd82383ea6ea9bccd794af2b85b567efe65d0e3cf3af2c1923f9d77` |
| Waiting State 003 | `60e5c95601e2968e1024a0fda896a7918be528f02b90eae61b6b9c408a9a5a5e` |
| Inactive Mandate 003 | `6fdf0088326a5b8cd66672f51f0daceabaa6b752b8e14223a3382ca96aba402d` |
| Self-repair implementation aggregate | `d6c4680b7e861baffce27dee14a4270c1304b1e3c841eb6c9977502b2f7d0348` |
| Run-003 control-plane aggregate | `8fc7628e4aaf07c0cf3c9ccb420abd3ffd672243f2eb20aac0b61ef8d329ccf3` |

The standing authorization path is reserved at
`oc3/OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_STANDING_AUTHORIZATION_003.json`
and is absent. Candidate 003 is a technical proposal and grants no execution
or network authority.

## Exact proposed human execution identity

```text
/home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/.venv/bin/python /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/oc3_source_metadata_recovery_mission_runner_run003.py --run-mission --state /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_STATE_003.json --standing-authorization /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_STANDING_AUTHORIZATION_003.json
```

`mission_execution_argv_sha256 = 8a9e1fdc617cce8f6c5a3544279425335e67371c9f15f4c312b164cc7eb7f2b8`

This command is proposed for a later, separately authorized execution. It was
not run during package preparation.

## Scope and first action

Mission scope is
`SOURCE_METADATA_ACQUISITION_WITH_BOUNDED_TECHNICAL_RECOVERY`. The first
Run-003 action is `OFFICIAL_SERVICE_DOCUMENTARY_PROBE`, derived from the
immutable Run-002 G01 diagnostic terminal. It reserves 2 technical requests
and 262,144 technical body bytes. It does not repeat G01.

Run-003 namespaces are exclusively:

- candidate ledger: `oc3/SOURCE_METADATA_AUTONOMOUS_RECOVERY_RUN_003_LEDGER/`;
- permits: `oc3/SOURCE_METADATA_AUTONOMOUS_RECOVERY_RUN_003_PERMITS/`;
- runtime: `oc3/source_metadata_autonomous_recovery_run_003/`;
- state: `oc3/OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_STATE_003.json`;
- authorization: `oc3/OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_STANDING_AUTHORIZATION_003.json`.

None existed as an execution namespace at validation time; only the frozen
waiting-state file exists.

## Resource accounting

The frozen budget is mission-local. Run-003 starts with:

| Class | Requests | Body bytes | Per-request cap | Concurrency | Retries/action |
|---|---:|---:|---:|---:|---:|
| Technical | 8 | 2,097,152 | 262,144 | 1 | 0 |
| Material | 5 | 67,108,864 | frozen per-resource caps | 1 | 0 |

Run-002's one real technical request and 2,124 bytes remain historical
provenance. They are not silently discarded or charged against the new
mission-local counters. The frozen source-metadata authorities define no
additional cumulative cross-mission global cap.

## Self-repair authority

After a valid standing authorization, a qualifying technical self-repair may
continue without a new human decision only under Amendment 001: at most 2
episodes per mission and 1 per defect class; all scientific, observational,
provider/resource, rights/permission, resource/cap and acceptance-criterion
drift values must be zero. Repair of the repair policy, ambiguous behavior,
new scientific assumptions and historical mutation are forbidden. Any
implementation identity change invalidates the old pending technical artifacts
and requires fresh downstream candidate and derived authorization bindings.

## Negative capabilities

Credentials, secrets, redirects outside existing contracts, new authorities,
new resources, changed query semantics, budget expansion, PHOTSYS/BRICKNAME/
BRICKID/ROOT reads, holdout access, image pixels, morphology, labels, matching,
embeddings, clustering, Panel V2, P1 and redistribution are not authorized.

## Historical diagnostic evidence

Run-002 G01 observed HTTP 200 and a 2,124-byte structurally CSV body while the
server declared `Content-Type: text/html; charset=utf-8`. Its frozen
classification is `CSV_BODY_WITH_WRONG_CONTENT_TYPE`. It accepted zero
scientific rows and zero source values, performed zero material actions and
activated no adapter. This package preserves the observation without assigning
scientific meaning or selecting an adapter.

## Scientifically unresolved

The source metadata contract, stable explanation for the Content-Type
behavior, adapter selection, north and south source counts, accepted source
rows/values and material acquisition outcome remain unresolved.

## Mandatory human stops

`STOP_REQUIRES_HUMAN` retains precedence for scope or budget expansion, new
scientific assumptions or observational equivalences, provider/resource or
rights changes, credentials, acceptance/failure-criterion changes, ambiguous
repair, recursive policy mutation, exhausted repair limits, historical
mutation, or any unresolved identity/integrity conflict.

## Offline preparation result

- `POLICY_CORE_003_FROZEN`
- `RUN_003_CANDIDATE_READY_FOR_HUMAN_REVIEW`
- `RUN_003_WAITING_FOR_HUMAN_AUTHORIZATION`
- `RUN_003_NETWORK_REQUESTS = 0`
- `RUN_003_MATERIAL_ACTIONS = 0`
- `RUN_003_EXECUTION = NOT_STARTED`

No provider query, source fetch, material acquisition, adapter activation,
final authorization, permit, capability, ledger or Run-003 runtime output was
created.

## Validation receipts

Focused Run-003 plus closed-input inventory validation: 21/21 PASS, zero real
network requests. Complete socket/DNS-firewalled regression required by the
new integration: 1,523/1,523 PASS, zero failures, zero skips and zero real
network requests. The canonical replay receipt is
`oc3/environment_setup/OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_RUN_003_OFFLINE_REPLAY_RECEIPT_001.json`.
