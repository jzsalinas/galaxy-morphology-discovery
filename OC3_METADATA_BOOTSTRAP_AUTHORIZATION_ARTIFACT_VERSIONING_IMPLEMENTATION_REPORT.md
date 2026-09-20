# OC3 Metadata Bootstrap Authorization Artifact Versioning Implementation Report

## Result

The first-run gate now derives candidate and final authorization identity from explicit canonical paths and cryptographic bindings instead of the historical `001` filenames. Versioned Candidate 002 and Final Authorization 002-style paths validate offline when their bytes, SHA-256, argv paths, rights path and candidate/final fields agree exactly.

The runtime accepts no relative path, basename-only comparison, symlink path, outside-project path, wildcard or implicit latest-artifact discovery. The candidate and final filenames must follow their versioned artifact policies. All schema-v2, closed-schema, state, digest, technical-equivalence, command, rights, implementation, environment, resource, cap, patch-model, negative-capability and human-authorization gates remain before transport construction.

## Change boundary

- `OC3_METADATA_BOOTSTRAP_AUTHORIZATION_ARTIFACT_VERSIONING_AMENDMENT_001.md`: prospective authority, SHA-256 `54d9d5a18f5dfd24ad98be4ac1f55415380a08030464637938e3161111bd256d`.
- `oc3/oc3lib/metadata_bootstrap.py`: versioned filename policies and canonical in-project path validation.
- `oc3/tests/test_metadata_bootstrap_gate_activation.py`: 13 focused cases using Rights 003, Candidate 002 and Final 002-style fixture paths.
- `oc3/tests/SYNTHETIC_TEST_RESULTS.json` and `.log`: complete offline regression.
- `oc3/environment_setup/METADATA_BOOTSTRAP_AUTHORIZATION_ARTIFACT_VERSIONING_REPLAY_RECEIPT.json`: canonical replay receipt, SHA-256 `299ed326482c025b97136b9dcd271f3542e4cbda17a90fc2a6f7627d349844e7`.

The new implementation aggregate is `432bcd449673786075938d3a290ad0ea139cc88bf1c2aae758c59d09179ef276`.

## Verification

The focused versioning cases passed 13/13. They prove acceptance of Candidate 002 and Final 002-style absolute canonical paths; exact final argv and candidate/final cross-binding; exact candidate path/SHA; rejection of wrong, relative, outside-project and symlink paths; rejection of historical Candidate 001 as a final authorization; and lack of transport before every gate passes.

The complete regression passed 623/623 with 0 failures, 0 skipped and `real_network_requests=0` in 81.592 seconds. Result SHA-256: `bd97d372239040a1b125cffcf3ee15574f274c52c151ce7c8c954d8a0bd63d0c`. Log SHA-256: `5e0098527f2668f99cc2b2fd32b876dbed5acba22070a858fd9febbecf27fc50`.

The historical artifacts remain byte-identical to HEAD before this task:

- Rights Binding 002: `372279185e4cfb73882f2acebcb9faf051e74294728f950b082563693b898d54`;
- Authorization Candidate 001: `4c377cde700c390bc2272c93d2bc6246f642719ddaa455890c14c0ecdea34c7e`;
- Final Authorization 001: `3c827c10626af16ef127f811d76b86bc82b8bdd5c3bcb5147c0c2ac31f90d561`.

No real rights, candidate, authorization, attempt, ledger, RAW or STAGING artifact was created. Post-task state remains `metadata_bootstrap=NOT_STARTED`, `real_attempt_created=false`, `real_network_requests=0`, `production_decode_enabled=false`, `redistribution=false`.
