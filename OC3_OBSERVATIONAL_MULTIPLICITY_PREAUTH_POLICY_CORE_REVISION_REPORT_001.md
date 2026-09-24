# OC3 Observational Multiplicity Preauthorization Policy-Core Revision Report 001

## Result

The prospective governance revision is complete and remains inactive. Policy Core V2 obtains the first-action identity exclusively from sealed initial-state data. A future standing authorization must bind both the complete waiting-state identity and its separate first-candidate path/SHA. No standing authorization or execution permit exists, and no scientific action ran.

**FIRST ACTION IDENTITY IS NOW HUMAN-BOUND STATE DATA, NOT A POLICY-CODE CONSTANT.**

The historical STOP was correct fail-closed behavior: Policy Core V1 bound Candidate 002, so resealing state to Candidate 003 without a prospective policy revision would have violated the reviewed core. The mission had not been activated and no lifecycle transition occurred.

## Frozen identities

| Artifact | SHA-256 |
|---|---|
| Historical Policy Core Manifest 001 | `f22525fbb5d5a64ab950bee9c261f27bd95aa17500e3fa6d6fc244bd4f66b976` |
| Policy Core Manifest 002 | `b10ffe799df90398209aa32bf623bfb43528f31202a65146f10b24c4f7e3b1ff` |
| Historical Candidate 001 | `308dd5af01a4048cd6fb2a796248c324e2d9e6f01b2b44ca68262f98cf070463` |
| Historical Candidate 002 | `c0635c13762798231de582152b29ccd5a8bc58b0983acb53e02e2a76870d4ac9` |
| Candidate 003 | `0d53fba70cf2de7dd9c10b783624eb53c80a9e88dbf03f38275d2cec7a40e84b` |
| Candidate 003 command argv | `66016cb53d03cd2c9f91b11f4682f75cdeeaabc55b620e18f8112a24808b7061` |
| Candidate 003 validation receipt | `9d86e7cce64691bcd17be7cbbb9d8b0a05a61de6bdfa27ac3fac5fd5692aa4ee` |
| Mandate 002 Markdown | `1539d24cfa1cb0670fb1ab249f372598b5c6eceff5b173d2b39130548dd95e82` |
| Mandate 002 JSON | `2bdd8d7d3d0b621d40221cd7d60c868af7dbec34053c528c019a8db0491073aa` |
| Runbook 002 | `4fda6d8eaf7c7cf93dfacfea7ac02f3aa9b148f573a09322e8fec385ee7e5e2d` |
| Prospective waiting state | `78adaefb762f7a5a8a523b3ae33fabcdd3e5bdfc371ab9a2fbb995f1936d46f9` |
| Audit implementation aggregate | `136c8454f242641f0ca49d10761bb899bbf11b1af1e0e9420b60b65a25cdff13` |

Candidate 003 declares Permit 003 at `oc3/OBSERVATIONAL_MULTIPLICITY_AUTONOMY_PERMITS/OC3_GLOBAL_VIEW_RELATION_AUDIT_PERMIT_003.json`. The permit was not created.

## Validation evidence

- Focused first-action, governor, parser, executor, and scientific-strategy suite: 35/35 passed.
- Affected suite including the production-directory tripwire: 160/160 passed.
- Full guarded offline regression: 1,255/1,255 passed; 0 failures; 0 unexpected skips; `real_network_requests=0`.
- Generic multi-action replay passed: an offline first action completed synthetically, then independently contracted documentary and grouping actions registered under the unchanged policy core.
- Candidate A and Candidate B each activated in separate synthetic fixtures under the same policy implementation when their own state and authorization bindings agreed.
- Mutation after authorization failed closed; initial registration rejected a non-state-bound candidate; a different candidate registered after synthetic first-action completion.
- Exact Candidate 003 argv parsed through the production parser. Candidate 002's historical malformed argv and an alternate `--consumption-path` were rejected.
- Synthetic executor integration validated the current candidate/permit/state/authorization chain, wrote the canonical SHA-derived marker before invoking the mocked audit, rejected an invalid permit before the audit call, rejected replay, and left state completion unchanged.
- Synthetic mutation of a V2 policy member produced `POLICY_CORE_MISMATCH` and no permit.

All validation was offline. Counters and enforced boundaries remained: network 0; real local relation audits 0; real summary-value reads 0; PHOTSYS 0; Tractor/source rows 0; pixels 0; morphology and labels 0. Candidate 003 was validated but not executed.

## Prospective state

The waiting state is `WAITING_FOR_STANDING_HUMAN_AUTHORIZATION`, `active=false`, sequence 0, with 12 requests and 16,777,216 application-body bytes remaining. It binds Candidate 003 by exact relative path and full-file SHA. It has no standing authorization, registered pending action, issued permit, completed stage, terminal, or scientific outcome.

Policy Core V1 and Candidates 001/002 remain byte-identical historical evidence. Candidate 002 is superseded because its sealed command vector does not define the production execution path. Policy Core V2 becomes immutable only after future human authorization; a later policy-member change must fail closed and require human review.
