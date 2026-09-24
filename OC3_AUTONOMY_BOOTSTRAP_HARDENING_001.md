# OC3 bounded-autonomy bootstrap hardening 001

Recorded at `2026-09-24T00:07:14Z` on branch `autopilot/photsys-zero-byte`, from bootstrap parent commit `3a4dbb11b5987106ca8e10f0a2083b91b3e23cd7`. The containing Git commit uses message `fix: harden bounded autonomy lifecycle`; its object identity is reported after commit creation because a commit cannot contain its own SHA-256/SHA-1 identity.

## Frozen identities

- Policy-core contract SHA-256: `7c3f4b0fd13618afadca7eee327237fe078970e8d03e48d4ce67c492775f9103`
- Policy-core manifest SHA-256: `0c74f29bfc5b8167b87c14fa9e9f6b47ed2d9c337e58ff3dc7b0b75f1635407e`
- Governance amendment SHA-256, unchanged: `f255430eb8b36a7a40b71ee522d81f0664b00ebd16471324cc7f06c61a307b47`
- Mandate document SHA-256: `5148c812029a4e2cfcbe3fef53e4db7549f44a5792a1a2610a482e8a3891e3a9`
- Mandate JSON SHA-256: `40e1d87e4e40669da33f80ae7df8ae2731a28e012d72394750cc27479cf38e97`
- Runbook SHA-256: `116c9cb3c0e4d75cc17839b96ab64a6d2d8e172325f633ef1a9884bbbacfe9dc`
- Current waiting-state SHA-256: `4ab003f4d4a655628348bd86e7b3ad34b915745c964bb16cc370a301156e0b81`
- Implementation aggregate: `a3be89e0c9bf2e0b7b3d50c22e2b3debbcfa2153a2e2439279e4a2fee2e8185f`
- First autonomous Candidate 003 SHA-256: `bfd4f6da7fcfd75dff1864541bae6e61e7c01659452dfe7033029a9260051e2a`
- First autonomous command argv SHA-256: `da4346b2727e7255789ad5727c6421520349eae74995c836c6cd32166ab3d742`
- Candidate 001 historical SHA-256, unchanged: `a277a5e5b4d710650df5e89713dfd23a97c0f79ff273076273eb84835f55fc19`
- Candidate 002 historical SHA-256, unchanged: `fa631a8afe0fb2f5b7fac38e0c598c8d248485857aefa8028f3f8673cc3506cf`

## Implemented lifecycle

The universal governor now validates a closed generic action contract while action-specific validators remain responsible for scientific and transport correctness. The lifecycle includes exact-state standing authorization, deterministic one-time activation, generic action registration, policy evaluation, immutable permit issuance, consumption intent before material work, terminal-file verification, reservation-bounded accounting, governed STOP, and one of four frozen scientific terminals.

Candidate 003 preserves Candidate 002 scientific and transport semantics and adds the generic contract and action-validation receipt. It is the first registered pending action. Candidate 001 and Candidate 002 remain historical and are not executable through the autonomous path.

Permit transition rejects request, body, or retry deltas above the permit reservation. A consumed permit without a valid terminal remains consumed and cannot be replayed automatically. Policy-core mutation after synthetic activation fails closed with `POLICY_CORE_MISMATCH`.

THE ACTIVE POLICY CORE CAN NO LONGER BE MODIFIED AUTONOMOUSLY.

## Offline validation evidence

- Focused policy, activation, generic-candidate, Range, permit, transition, and transport tests: `57/57` passed.
- Affected regression: `220/220` passed.
- Full synthetic-only regression: `1220/1220` passed, `0` failures, `0` unexpected skips, `42.766` seconds.
- Synthetic two-action replay: passed. It activated from an exact synthetic authorization, completed and accounted for one action, registered a different action, and issued its second permit without policy-core modification.
- Synthetic STOP transition: passed.
- Synthetic allowed scientific-terminal transition: passed.
- Real network requests: `0`.
- Astronomical reads: `0`.
- Protected PHOTSYS/BRICKNAME/BRICKID/ROOT values observed: `0`.

## Final pre-authorization state

- Standing authorization: absent.
- Real execution permits issued: `0`.
- Mission active: `false`.
- State: `WAITING_FOR_STANDING_HUMAN_AUTHORIZATION`.
- Network execution: `0`.
- Panel V2: not started.
- P1: blocked/not started.
- V2 resolver: absent.
- Scientific outcome: not selected.
