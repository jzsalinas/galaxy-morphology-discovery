# OC3 Observational Multiplicity Runtime Command Binding Fix 001

## Result

The action-specific global-view executor now captures `sys.executable`, `sys.argv[0]`, and the ordered runtime argument vector before parsing. After loading the candidate and before permit validation or consumption, it requires literal equality with the candidate-sealed `command_argv`. Executable and script paths are compared exactly as supplied, without normalization or symlink resolution. Unknown or altered arguments fail before permit consumption and before the audit call.

**THE AUTONOMOUS PERMIT NOW AUTHORIZES THE EXACT EXECUTED COMMAND, NOT ONLY THE COMMAND DECLARED BY THE CANDIDATE.**

Policy Core V2 was not modified. `policy_core_unchanged = true`.

## Frozen identities

| Artifact | SHA-256 |
|---|---|
| Policy Core Manifest 002 | `b10ffe799df90398209aa32bf623bfb43528f31202a65146f10b24c4f7e3b1ff` |
| Historical Candidate 003 | `0d53fba70cf2de7dd9c10b783624eb53c80a9e88dbf03f38275d2cec7a40e84b` |
| Candidate 004 | `6e3a8c7209630b162e659322ac09ff4a8314255d3739ef1ac3c587b8cd1965df` |
| Candidate 004 command argv | `86e7f738aafae9755d21c225c17fc751454fc0ee5ccbc41b50d7f544bde24cf1` |
| Candidate 004 validation receipt | `ccc78c3b00d38938280b7f9c3cbb2a6fb25d24b21ad3d5e5b063d77f8395269d` |
| Action implementation aggregate | `84348fde51586f6747823d0fee41e80b203e3e08237552d38e89cdbd1f78c388` |
| Prospective waiting state | `93432d3df01a35542c93578292c835f2466ba1c0aca6fcaaf78a8d8a91db33b2` |
| Current Mandate 002 JSON | `b9f79076f95587a862a436471d776ed83142ac47032c6aee9308aa2b441c3279` |
| Current Runbook 002 | `b34cd67820c8a0ace57019aa08091680e4617554817e8f6c6110fdb98b00283d` |

Candidate 004 declares Permit 004 at `oc3/OBSERVATIONAL_MULTIPLICITY_AUTONOMY_PERMITS/OC3_GLOBAL_VIEW_RELATION_AUDIT_PERMIT_004.json`. No permit was created.

## Validation evidence

- Candidate 004 preserves Candidate 003's complete scientific payload.
- The exact production command parses and passes the runtime-binding validator.
- Nine mutations were rejected independently: Python executable, executor script, mode, candidate, permit, standing authorization, autonomy state, output directory, and an unknown extra argument.
- An altered runtime output directory produced `RUNTIME_COMMAND_BINDING_MISMATCH`; the canonical permit marker remained absent and the mocked audit call count remained zero.
- The exact synthetic runtime invocation consumed the permit through the canonical SHA-derived marker before one mocked audit call.
- Exact replay produced `AUTONOMOUS_PERMIT_ALREADY_CONSUMED`; the audit call count remained one.
- The executor did not perform or fabricate a state-completion transition.
- Generic Candidate A/B activation, first-action decoupling, multi-action offline/documentary/grouping replay, authority subsets, reservations, canonical consumption, accounting, STOP, scientific terminals, and policy-core mutation failure remained covered.

Focused runtime, executor, governor, and strategy tests passed 36/36. The affected suite including the production-directory tripwire passed 161/161. The full guarded offline regression passed 1,256/1,256 with zero failures and zero unexpected skips.

All validation remained offline: network 0; real relation audits 0; real summary-value reads 0; PHOTSYS 0; Tractor/source rows 0; pixels 0; morphology and labels 0.

## Prospective state

The state remains `WAITING_FOR_STANDING_HUMAN_AUTHORIZATION`, `active=false`, sequence 0, with zero issued permits, no registered action, no standing authorization, and the complete 12-request and 16,777,216-byte budgets. Its first candidate is now Candidate 004. Candidate 003 remains byte-identical historical evidence and is superseded because its action implementation did not enforce runtime argv identity.
