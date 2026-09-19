# OC-3 metadata-bootstrap gate activation implementation report

## Scope and terminal state

This task activated only the local, fail-closed gate between the frozen execution plan, reviewed rights, human authorization, the exact command vector, and construction of `RealHttpTransport`. It performed synthetic and offline verification only. It did not create a rights binding, authorization, metadata-bootstrap attempt, ledger, RAW or STAGING state, provider request, or provider-row observation.

The terminal project state remains:

```text
PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS
metadata_bootstrap=NOT_STARTED
production_decode_enabled=false
redistribution=false
real_network_requests=0
real_provider_row_values=0
```

Probe 001 was neither rerun nor resumed and remains immutable 13/13. OC-3 remains not started.

## Authority and Git baseline verification

The implementation began from clean branch `main`, baseline commit `8e87225dfb895438e5bb73bbadc6ef35dbf6ed1e`, and annotated local tag `oc3-pre-metadata-bootstrap-001`. No remote was configured. The Git policy, ignore rules, attributes, execution plan, base specification, Clarification 001, previous infrastructure report, and previous replay receipt matched their required SHA-256 identities.

The pre-activation implementation aggregate was:

`084706171e4b74a13a8d2ed57ee5d61b73953d746e6aab23081ef77d78673407`

The execution-plan identity retained as the pre-activation runtime authority is:

`0e246d5fce5d71c2aa109cba913f1eb9bd397259e492e279870c6d4ccf163b20`

The plan itself was not edited. Because the implementation aggregate changed, the plan requires a separate local documentary refresh and review before any rights binding is created.

## Files changed and created

Implementation and tests:

- `oc3/oc3_metadata_bootstrap.py`;
- `oc3/oc3lib/metadata_bootstrap.py`;
- `oc3/tests/test_metadata_bootstrap.py`;
- `oc3/tests/test_metadata_bootstrap_gate_activation.py`.

Replay and review evidence:

- `oc3/environment_setup/METADATA_BOOTSTRAP_GATE_ACTIVATION_SYNTHETIC_TESTS.log`;
- `oc3/environment_setup/METADATA_BOOTSTRAP_GATE_ACTIVATION_SYNTHETIC_TESTS.json`;
- `oc3/environment_setup/METADATA_BOOTSTRAP_GATE_ACTIVATION_REPLAY_RECEIPT.json`;
- this report.

No scientific authority, execution plan, resource identity, cap, provider digest, physical contract, value-semantic rule, selector boundary, or Git versioning policy was changed.

## CLI placeholder removal and exact gate order

The unconditional `--execute-network` placeholder was replaced by `activate_network_transport`. The CLI exposes no synthetic override or injected-factory option. In a first-run invocation, the gate performs these local steps in order:

1. canonical project identity;
2. execution-plan SHA authority;
3. base specification, Clarification 001, and frozen supporting authorities;
4. locally calculated current implementation aggregate;
5. environment fingerprint;
6. exact attempt ID;
7. absence of conflicting first-run attempt state;
8. canonical rights-binding parse and validation;
9. canonical human-authorization parse and closed-schema validation;
10. authorization binding to the locally calculated rights-file SHA;
11. plan SHA in both rights and authorization;
12. exact resources and `METADATA_BOOTSTRAP_ONLY_RESOURCE_CAPS_V1`;
13. `MODEL_B_TWO_STAGE`;
14. exact command vector;
15. canonical command SHA-256;
16. `authorized=true` and final-authorization state;
17. `execution_mode=FIRST_RUN_NETWORK`;
18. absence of `--resume` for first run;
19. exact closed negative-capability object;
20. construction of `RealHttpTransport`.

The real constructor now also requires a private activation-gate token. Direct construction through the public factory without passing the complete activation path fails with `METADATA_REAL_TRANSPORT_GATE_REQUIRED`. The real HTTP implementation imports and creates its urllib opener only when a later authorized request method is called; the gate itself performs no DNS, socket, HEAD, or GET operation.

## Rights-binding validation

The runtime accepts only canonical compact sorted-key UTF-8 JSON with one trailing LF, no duplicate or unknown keys, and a size below 1 MiB. Its exact closed schema requires:

- `binding_type=METADATA_BOOTSTRAP_RIGHTS_BINDING`;
- schema and canonicalization versions;
- exact attempt and `METADATA_BOOTSTRAP_ONLY` scope;
- local acquisition and preservation allowed only for this protocol;
- `redistribution=false` and `FITS_OR_DERIVED_REDISTRIBUTION=DISABLED_UNRESOLVED`;
- execution-plan, base-specification, clarification, implementation, and environment bindings;
- the four exact roles, URLs, and lengths;
- `reviewed=true` and one or more locally resolvable reviewed-evidence paths with exact SHA-256 identities.

The rights identity is SHA-256 over the exact canonical file bytes. The object constructor independently recomputes that identity, and the authorization must bind it exactly. No legal conclusion is calculated; these checks enforce only the frozen research-governance claims.

## Authorization and command validation

The first-run authorization has a separate exact schema and requires:

- `authorization_type=METADATA_BOOTSTRAP_FIRST_RUN_AUTHORIZATION`;
- `authorization_state=FINAL_HUMAN_AUTHORIZATION` and `authorized=true`;
- a nonempty human identity and UTC authorization time;
- exact attempt, scope, `FIRST_RUN_NETWORK`, plan, specifications, implementation, environment, resources, caps, and `MODEL_B_TWO_STAGE`;
- exact rights-file SHA-256;
- exact command vector and its existing compact sorted-key JSON SHA-256;
- all frozen negative capabilities, each false;
- a real, nonsynthetic artifact for the production constructor.

An `authorized=false` candidate is rejected. First-run authorization cannot authorize `--resume`; resume retains its distinct authorization type, execution mode, ledger/counter/state bindings, and exact resume argv. A resume authorization is rejected for a first-run command and vice versa.

The first-run command vector must be exactly the absolute script path followed by `--execute-network`, `--authorization` and its absolute argv-bound path, then `--rights-binding` and its absolute argv-bound path. The interpreter and shell working-directory operation remain outside that vector. Mutation, reordering, relative paths, extra flags, overrides, `--dry-run`, `--offline`, Range, or `--resume` fail before transport construction.

## Canonical blocked-state proof

The canonical workspace contains neither a metadata-bootstrap rights binding nor authorization. Calling the canonical CLI with `--execute-network` therefore returns locally with `PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS`. The regression verifies that this path creates no attempt directory, ledger, RAW, STAGING, or transport and invokes no socket or DNS operation. `--offline` and `--dry-run` remain incapable of constructing real transport or consuming authorization.

## Synthetic replay

The project runner installed its socket and DNS firewall before test discovery. The final replay result was:

```text
562 total
562 passed
0 failed
0 skipped
real_network_requests=0
```

All previous 518 passing tests were retained. Forty-four gate-activation tests cover plan identity, rights and authorization schemas, local rights SHA, candidate/final separation, first-run/resume separation, exact resources and caps, negative capabilities, command mutation and hashing, factory ordering, canonical blocking, no attempt/ledger, no DNS/socket, offline/dry-run behavior, Model B, production decode state, selector absence, and Probe 001 integrity.

The new implementation aggregate is:

`d9922ad04a19a9e87b73e85439239a591aae80b1d9528d9e75310b0e88efbec7`

Environment fingerprint:

`b49e26767922123113707a13434821d6bf1d7711f28a2b9de7e5ce46d64e3bdf`

The replay receipt is `oc3/environment_setup/METADATA_BOOTSTRAP_GATE_ACTIVATION_REPLAY_RECEIPT.json`, SHA-256 `e696907938fabd20b907010708b06d130cd65077b7f24a2187bf2948790620dd`. It binds the result SHA-256 `567309440866eae5818c759ab04e6ea3ab431d49b752aec007e76bd6b9e7d679` and log SHA-256 `1d629cac82a63ca955b628772a90b173f0b492351d4be0a3259340dbb1403811`.

## Git disposition and remaining blocker

The intended local commit message is `feat: activate metadata bootstrap execution gates`. Its SHA is necessarily recorded by Git and the completion response after this report is part of the commit; embedding that SHA in this file would create a self-referential commit identity. The original baseline commit and tag remain unchanged. No push or tag creation is authorized for this task.

The next task is a local refresh and review of `OC3_METADATA_BOOTSTRAP_EXECUTION_PLAN_001.md` against implementation aggregate `d9922ad04a19a9e87b73e85439239a591aae80b1d9528d9e75310b0e88efbec7`. Rights binding must not be created before that review.

**EXECUTION PLAN RE-REVIEW REQUIRED BEFORE RIGHTS BINDING.**

**DO NOT RE-RUN OR RESUME PROBE 001.**

**OC-3 REMAINS NOT STARTED.**
