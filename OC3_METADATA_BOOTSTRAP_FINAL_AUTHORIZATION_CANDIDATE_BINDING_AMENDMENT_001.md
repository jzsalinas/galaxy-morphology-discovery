# OC-3 metadata-bootstrap final-authorization candidate-binding amendment 001

## Status and scope

This is a prospective documentary amendment that closes the design gap between a separately reviewed, non-executable first-run authorization candidate and a distinct final human authorization. It changes no current runtime capability and creates no candidate, final authorization, rights binding 002, attempt, ledger, RAW, STAGING, provider-row observation, network request, or OC-3 transition.

The amendment is limited to the future first-run final-authorization schema and validator, the separate offline candidate parser/validator, and activation-gate verification of candidate provenance. It does not amend the execution plan, resources, representation identities, caps, Model B, rights decisions, selective decode, field firewall, transport schedule, terminal outcomes, resume authorization, scientific semantics, or `redistribution=false`.

## Verified current authorities

The amendment was prepared locally from a clean `main` branch at commit `a1c51d76f202b58fc5bdb5d86637312c28837e04`, with no configured remote.

| Authority or state | Verified value |
|---|---|
| Candidate specification | SHA-256 `b340a3d4a9123da0eb5cd54426eca2d6aced8089fb90f905b91f966852a250fa` |
| Rights review 001 | SHA-256 `81dc0a0ec485b7f8d9007781e9845735ec057483b45421442d112c3ad5e38d2e` |
| Rights Binding 001 | SHA-256 `51ab89dfef0cfb34f7ef8614c2dd6e3984d20cf3d2590d6e40d356091d5f10b4` |
| Execution Plan 001 | SHA-256 `0e246d5fce5d71c2aa109cba913f1eb9bd397259e492e279870c6d4ccf163b20` |
| Plan post-activation review | SHA-256 `a232a58f91705215d5322945460549b7b53789bf630503d505552f8f5fb460a0` |
| Current implementation aggregate | `d9922ad04a19a9e87b73e85439239a591aae80b1d9528d9e75310b0e88efbec7` |
| Current candidate-spec commit | `a1c51d76f202b58fc5bdb5d86637312c28837e04` |
| Canonical replay | 562/562 passed, `real_network_requests=0` |
| Probe 001 | exact and immutable 13/13 |

The candidate, final authorization, Rights Binding 002 and real attempt are absent.

## Gap and mandatory causal relation

The current final first-run authorization closed schema cannot bind the exact candidate artifact reviewed by the human. It therefore cannot yet prove that a final human authorization refers to exactly that immutable candidate.

The gap is:

```text
FINAL_AUTHORIZATION_CANDIDATE_BINDING_GAP
```

No final authorization may be created until the future implementation, replay, aggregate transition, plan review, Rights Binding 002, candidate-spec review and actual candidate creation have closed this gap.

The required causal relation is:

```text
candidate proposal
→ explicit human review
→ distinct final authorization
→ runtime candidate-binding verification
→ execution gate
```

The candidate remains non-executable and immutable. It cannot be promoted, overwritten, renamed or mutated into final authorization.

## First-run final schema version 2

The future final first-run authorization SHALL use:

```text
schema_version = 2
authorization_type = METADATA_BOOTSTRAP_FIRST_RUN_AUTHORIZATION
authorization_state = FINAL_HUMAN_AUTHORIZATION
authorized = true
```

This version applies only to first-run final authorization. Resume authorization is outside this amendment.

After adoption, first-run schema version 1 SHALL be obsolete for `OC3-METADATA-BOOTSTRAP-001` and SHALL fail before transport construction. There is no compatibility fallback, silent upgrade, permissive parsing or inference from a schema-v1 object.

## Exact candidate-provenance fields

First-run final schema version 2 adds exactly these two fields to the existing final first-run key set:

```text
authorization_candidate_path
authorization_candidate_sha256
```

The required path is exactly:

```text
/home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/METADATA_BOOTSTRAP_FIRST_RUN_AUTHORIZATION_CANDIDATE_001.json
```

`authorization_candidate_path` SHALL be that exact absolute string. `authorization_candidate_sha256` SHALL be a 64-character lowercase hexadecimal SHA-256 of the exact canonical candidate file bytes. A filename without a digest, a Git identity without the file digest, a relative path, alternate path, symlink escape, missing file or noncanonical candidate is insufficient.

No other final-schema key is added by this amendment.

## Candidate load and validation before final acceptance

Future final-authorization validation SHALL complete these local steps before a final authorization can reach transport construction:

1. read `authorization_candidate_path` from the schema-v2 final object;
2. require exact equality with the frozen absolute candidate path;
3. resolve the path and require an existing regular file inside the canonical project;
4. read it locally under the candidate input-size cap;
5. run the separate strict candidate loader, including UTF-8, duplicate-key, closed-schema and canonical-byte checks;
6. recompute SHA-256 over the exact candidate bytes;
7. compare it exactly with `authorization_candidate_sha256`;
8. run the separate offline candidate validator;
9. require `candidate_type=METADATA_BOOTSTRAP_FIRST_RUN_AUTHORIZATION_CANDIDATE` and `candidate_state=PENDING_HUMAN_REVIEW`;
10. validate candidate-specific authorities and paths locally; and
11. prove exact technical equivalence between the candidate and final authorization.

These operations perform no DNS, socket, HTTP, transport construction or attempt-state mutation.

## Exact technical-equivalence contract

The schema-v2 final authorization SHALL describe the same technical proposal frozen by the candidate. The following corresponding values must be exactly equal:

| Candidate field | Final authorization field |
|---|---|
| `attempt_id` | `attempt_id` |
| `scope` | `scope` |
| `execution_mode` | `execution_mode` |
| `patch_model` | `patch_model` |
| `execution_plan_sha256` | `execution_plan_sha256` |
| `rights_binding_sha256` | `rights_binding_sha256` |
| `base_spec_sha256` | `base_spec_sha256` |
| `clarification_sha256` | `clarification_sha256` |
| `implementation_aggregate` | `implementation_aggregate` |
| `environment_fingerprint` | `environment_fingerprint` |
| `resources` | `resources` |
| `resource_caps` | `resource_caps` |
| `command_vector` | `command_argv` |
| `command_sha256` | `command_sha256` |
| `negative_capabilities` | `negative_capabilities` |

The candidate-specific values SHALL additionally validate against local authorities and actual invocation state:

- `plan_post_activation_review_sha256` must match the applicable immutable plan-review artifact selected by the later candidate-spec review;
- `rights_review_sha256` must match the applicable immutable reviewed-rights artifact;
- `rights_binding_path` must equal the actual absolute `--rights-binding` argv path;
- the recomputed digest of that rights file must equal candidate and final `rights_binding_sha256`; and
- `final_authorization_path` must equal the actual absolute `--authorization` argv path and the final file being validated.

Equality is structural and exact. No normalization, alias, order relaxation for arrays, cap widening, resource substitution, alternate path, default insertion or semantic approximation is permitted.

## Human-only final fields

Only the distinct final authorization may contain and require:

```text
authorization_state = FINAL_HUMAN_AUTHORIZATION
authorized = true
authorized_by = explicit nonempty human identity
authorized_at_utc = valid UTC time recorded after approval
```

The candidate remains free of approval semantics. Its machine provenance timestamp is not human approval.

Final creation requires explicit human input for the identity and the decision to authorize the exact candidate. Approval cannot be inferred from candidate existence or validity, rights approval, a Git commit, conversation history, elapsed time or any automated status.

## Final authorization path and command binding

Candidate `final_authorization_path` SHALL equal the actual path passed to `--authorization`:

```text
/home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/METADATA_BOOTSTRAP_FIRST_RUN_AUTHORIZATION_001.json
```

The candidate command vector always names that final path, never the candidate path. Candidate `command_vector` and final `command_argv` must be identical. Candidate and final `command_sha256` must be identical and must equal a fresh runtime calculation from the actual argv.

At activation, the runtime independently reconstructs the command vector and compares it with both objects. Any path, option, order, command-hash or argv discrepancy produces:

```text
METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE
```

before `RealHttpTransport` construction.

## Separate candidate validator and runtime firewall

The future implementation SHALL provide distinct offline functions equivalent to:

```text
load_authorization_candidate()
validate_authorization_candidate()
```

They SHALL be transport-incapable. Candidate success means only:

```text
AUTHORIZATION_CANDIDATE_VALID_FOR_HUMAN_REVIEW
```

It never means `AUTHORIZED`, `EXECUTION_READY` or `TRANSPORT_ALLOWED`. Supplying candidate JSON through `--authorization` SHALL continue to fail closed because its type, state and key set do not satisfy final authorization.

The production activation path SHALL construct real transport only after candidate validation, candidate-SHA verification, candidate/final technical equivalence, final schema-v2 validation, `authorized=true`, explicit human fields, rights validation, command validation and all pre-existing gates have succeeded.

## Promotion prohibition

Final authorization is not created by:

```text
copy candidate
→ flip authorized
→ add name/time
```

It is a newly serialized, separately hashed artifact created after explicit human approval and independently validated against final schema version 2. The candidate remains immutable evidence of what the human reviewed. There is no automatic promotion or in-place mutation.

## Preserved operational contract

This amendment changes no execution-plan decision. It preserves exactly:

- the four roles and URLs;
- provider representation and integrity identities;
- aggregate 89,461,646 expected bytes;
- `METADATA_BOOTSTRAP_ONLY_RESOURCE_CAPS_V1` without widening;
- `MODEL_B_TWO_STAGE` and all PATCH limitations;
- the exact negative-capability object;
- sequential HEAD/GET scheduling and transport constraints;
- selective decode and forbidden-field firewall;
- terminal outcomes and precedence;
- manual execution and separate resume authorization; and
- `redistribution=false` and `FITS_OR_DERIVED_REDISTRIBUTION=DISABLED_UNRESOLVED`.

Resume authorization is unchanged and outside this amendment.

## Runtime fail-closed conditions

After implementation, real first-run activation SHALL fail before `RealHttpTransport` if any of these conditions occurs:

- candidate absent, non-regular, outside the canonical project or at the wrong path;
- candidate malformed, noncanonical, oversized, wrong type, wrong state, missing a key or containing an unknown key;
- candidate SHA absent, malformed or different from exact file bytes;
- offline candidate validation fails;
- candidate and final technical fields differ;
- candidate `final_authorization_path` differs from the actual final path;
- candidate command vector/hash differs from final or actual argv;
- candidate rights path/SHA differs from final or actual rights file;
- candidate implementation, environment, plan, review, resources, caps, Model B or negative capabilities differ;
- final authorization uses obsolete schema version 1;
- final `authorized` is not strict true;
- final human identity/time is missing or invalid; or
- any prior authority, rights, local-state or activation gate fails.

There is no schema-v1 fallback.

## Required future synthetic verification

The future implementation/replay SHALL test at minimum:

1. valid candidate parses and validates offline;
2. candidate unknown key is rejected;
3. candidate missing key is rejected;
4. candidate noncanonical bytes are rejected;
5. wrong `candidate_type` is rejected;
6. wrong candidate state is rejected;
7. candidate `authorized` key is rejected;
8. candidate human-approval field is rejected;
9. candidate command-hash mismatch is rejected;
10. candidate rights mismatch is rejected;
11. candidate implementation mismatch is rejected;
12. candidate resource mismatch is rejected;
13. candidate cap mismatch is rejected;
14. candidate negative-capability mismatch is rejected;
15. candidate final path mismatch is rejected;
16. candidate validation cannot construct `RealHttpTransport`;
17. candidate passed as `--authorization` is rejected;
18. first-run final schema version 1 is rejected after adoption;
19. final schema version 2 requires candidate path;
20. final schema version 2 requires candidate SHA;
21. absent candidate blocks final validation;
22. candidate SHA mismatch blocks final validation;
23. candidate/final technical mismatch blocks final validation;
24. exact candidate/final technical equivalence passes synthetically;
25. final `authorized=false` is rejected;
26. missing `authorized_by` is rejected;
27. invalid `authorized_at_utc` is rejected;
28. final command/argv mismatch is rejected;
29. transport factory remains untouched before all candidate/final checks;
30. existing scientific and transport semantics remain unchanged;
31. all prior regression remains passing;
32. `real_network_requests=0`; and
33. Probe 001 remains exact 13/13.

No fixed future test total is prescribed.

## Implementation-aggregate and rights consequence

Implementing this amendment will modify Python and necessarily produce a new implementation aggregate.

Consequently:

1. Rights Binding 001 remains immutable historical evidence for the current pre-amendment aggregate;
2. Rights Binding 001 will not match the post-amendment implementation aggregate and SHALL NOT be edited or reused as if current;
3. another narrow review of immutable Plan 001 against the new implementation is required;
4. only if that review confirms `operational_drift_count=0` may the rights workflow proceed; and
5. a new reviewed rights binding is required for the new aggregate.

The future rights path is prospectively reserved as:

```text
/home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/METADATA_BOOTSTRAP_RIGHTS_BINDING_002.json
```

Rights Binding 002 is not created by this amendment.

## Command and candidate-spec consequence

The command hash frozen by the immutable original candidate specification is:

```text
4985668400a14bab02675f203712f0909a9e09f084f9222e994e6d10f5a3eab8
```

After implementation, because the final command must point to the distinct Rights Binding 002 path, that hash SHALL be classified:

```text
HISTORICAL_PRE_CANDIDATE_BINDING_AMENDMENT_COMMAND_HASH
```

It must not be used as the eventual execution-command identity. The future command vector and hash SHALL be recomputed with the frozen Rights Binding 002 path.

`OC3_METADATA_BOOTSTRAP_FIRST_RUN_AUTHORIZATION_CANDIDATE_SPEC.md` remains immutable. After implementation/replay, the new aggregate, the plan review and Rights Binding 002, a separate candidate-spec post-amendment review or amendment must refresh:

- current implementation aggregate;
- rights-binding path and SHA-256;
- final command vector; and
- final command SHA-256.

The original candidate specification must not be silently rewritten. No post-amendment review is created now.

## Execution Plan 001 consequence

Execution Plan 001 remains immutable and does not require replacement if the implementation changes only candidate provenance binding while preserving the operational execution contract. After implementation, a narrow post-implementation review SHALL compare the plan with the new aggregate and require:

```text
operational_drift_count = 0
```

That review must precede Rights Binding 002. A changed implementation identity is not by itself operational drift and does not justify rewriting Plan 001.

## Required future sequence

The post-amendment sequence is frozen as:

1. implement this amendment offline;
2. run the full synthetic replay;
3. compute the new implementation aggregate;
4. commit the implementation and replay evidence;
5. review immutable Plan 001 against the new implementation and require zero operational drift;
6. create and review Rights Binding 002 against the new aggregate;
7. review immutable candidate specification against the new aggregate and Rights Binding 002;
8. compute the new final command vector and hash using the Rights Binding 002 path;
9. create actual candidate JSON 001 with no human approval fields;
10. conduct human review of the exact candidate;
11. obtain explicit human approval;
12. create distinct final authorization 001 under first-run schema version 2;
13. perform final local preflight;
14. have the responsible human manually execute the exact CLI; and
15. perform the local read-only post-execution audit.

No network is permitted before step 14.

## Current state

This documentary amendment changes no capability:

```text
rights_component=RESOLVED_FOR_CURRENT_PRE_AMENDMENT_IMPLEMENTATION
authorization_candidate=ABSENT
final_authorization=ABSENT
metadata_bootstrap=NOT_STARTED
production_decode_enabled=false
redistribution=false
real_network_requests=0
real_provider_row_values=0
real_attempt_created=false
```

Probe 001 remains immutable 13/13.

THIS AMENDMENT DOES NOT CREATE A CANDIDATE.

THIS AMENDMENT DOES NOT CREATE FINAL AUTHORIZATION.

THIS AMENDMENT DOES NOT AUTHORIZE EXECUTION.

DO NOT RE-RUN OR RESUME PROBE 001.

OC-3 REMAINS NOT STARTED.
