# OC-3 metadata-bootstrap candidate-binding implementation report

## Scope and outcome

This change implements only `OC3_METADATA_BOOTSTRAP_FINAL_AUTHORIZATION_CANDIDATE_BINDING_AMENDMENT_001.md`. It adds an offline parser and validator for the separately reviewed first-run authorization candidate, upgrades only the first-run final authorization to schema version 2, and binds that final authorization to the exact candidate path, exact candidate bytes, and exact technical proposal.

No Internet access, provider request, real candidate, final authorization, Rights Binding 002, attempt, ledger, RAW, STAGING, or provider-row observation occurred. Probe 001 was not rerun or resumed. The terminal state remains:

```text
metadata_bootstrap=NOT_STARTED
production_decode_enabled=false
redistribution=false
real_network_requests=0
real_provider_row_values=0
real_attempt_created=false
```

## Implementation

`oc3/oc3lib/metadata_bootstrap.py` now provides separate `load_authorization_candidate()` and `validate_authorization_candidate()` functions. The loader enforces the existing canonical compact sorted-key UTF-8 JSON representation, duplicate-key rejection, the input-size cap, exact canonical bytes, and exact byte SHA-256. The validator enforces the frozen 24-key closed schema, candidate type and pending-review state, local authority identities, exact resources and caps, exact negative capabilities, command vector and hash, rights binding path and SHA-256, final authorization path, implementation aggregate, environment fingerprint, and UTC candidate timestamp.

Candidate validation is transport-incapable. Its only success state is `AUTHORIZATION_CANDIDATE_VALID_FOR_HUMAN_REVIEW`. A candidate contains no authorization or human-approval semantics, cannot satisfy the final authorization schema, and cannot call or construct `RealHttpTransport`.

The first-run final authorization now requires schema version 2 and exactly two additional keys: `authorization_candidate_path` and `authorization_candidate_sha256`. Production activation requires the frozen absolute candidate path, an existing regular file inside the canonical project, canonical candidate bytes, a locally recomputed matching SHA-256, successful offline candidate validation, and exact candidate/final equality across all amendment-defined technical fields. It then validates the unchanged explicit human fields and all pre-existing execution gates before transport construction. First-run schema version 1 fails closed with no fallback.

Resume authorization remains schema version 1 with its previous closed key set and behavior. The four resources and URLs, representation and integrity rules, caps, `MODEL_B_TWO_STAGE`, PATCH restrictions, selective decoder, field firewall, transport schedule, terminal precedence, rights policy, and `redistribution=false` are unchanged.

## Files

Implementation and focused regression:

- `oc3/oc3lib/metadata_bootstrap.py`
- `oc3/tests/test_metadata_bootstrap.py`
- `oc3/tests/test_metadata_bootstrap_gate_activation.py`

Replay evidence:

- `oc3/environment_setup/METADATA_BOOTSTRAP_CANDIDATE_BINDING_SYNTHETIC_TESTS.log`
- `oc3/environment_setup/METADATA_BOOTSTRAP_CANDIDATE_BINDING_SYNTHETIC_TESTS.json`
- `oc3/environment_setup/METADATA_BOOTSTRAP_CANDIDATE_BINDING_REPLAY_RECEIPT.json`
- this report

## Verification

The focused offline regression executed both metadata-bootstrap test modules:

```text
182 tests
182 passed
0 failed
0 skipped
```

The amendment contributes 33 candidate-binding gate cases matching the complete required verification list. They prove closed-schema and canonical-byte rejection, candidate type/state separation, absence of approval fields, authority and proposal mismatches, final-path binding, candidate SHA binding, schema-v1 rejection, exact synthetic equivalence, preservation of explicit human fields, exact argv binding, and that the transport factory remains untouched until every candidate and final gate passes.

The full project replay, with socket and DNS calls disabled before test discovery, produced:

```text
595 tests
595 passed
0 failed
0 skipped
real_network_requests=0
```

All previous 562 tests remain passing. Probe 001 remains byte-exact across its frozen 13-file inventory.

The post-change implementation aggregate is:

`4676a6e85e98c4a4fe6464a2ec7c63c4f7c0ca959f7bc05b547b0de3467347c1`

Replay identities:

| Artifact | SHA-256 |
|---|---|
| `METADATA_BOOTSTRAP_CANDIDATE_BINDING_SYNTHETIC_TESTS.log` | `599b907cdc5925b185b89df9f62f831a7ee5805f3c876ff756e680e41a6703d3` |
| `METADATA_BOOTSTRAP_CANDIDATE_BINDING_SYNTHETIC_TESTS.json` | `45b3551cbd0434aeffd62fa2ed4635f2afa094f8f51a40656bd52e82931c2f21` |
| `METADATA_BOOTSTRAP_CANDIDATE_BINDING_REPLAY_RECEIPT.json` | `c0e14d4d9b4765a6cbf91d4cc6838d1bc018996913dcf4486ec985ed1ff6e03c` |

## Governance consequence

Rights Binding 001 remains immutable historical evidence for the pre-amendment aggregate and cannot authorize this implementation. No Rights Binding 002 or candidate was created. The next action is the consolidated documentary refresh required by the amendment: re-review Plan 001 against the new aggregate, create and review Rights Binding 002, and refresh the candidate specification and command identity before any real candidate can be prepared.

**NEXT STEP: CONSOLIDATED POST-AMENDMENT PLAN/RIGHTS/CANDIDATE REFRESH.**

**DO NOT CREATE FINAL AUTHORIZATION.**

**OC-3 REMAINS NOT STARTED.**
