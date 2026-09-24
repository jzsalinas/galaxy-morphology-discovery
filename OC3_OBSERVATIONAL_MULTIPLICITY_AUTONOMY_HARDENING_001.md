# OC3 Observational Multiplicity Autonomy Hardening 001

## Repository binding

- Branch: `autopilot/observational-multiplicity`
- Source baseline: `99aa73e82c2b503b5e53b5343a8a161f3b1ae30a`
- Commit: the single commit containing this report, with subject `fix: harden observational multiplicity autonomy lifecycle`. Its SHA is reported by Git after creation and is intentionally not embedded in its own content.
- Policy-core manifest SHA-256: `f22525fbb5d5a64ab950bee9c261f27bd95aa17500e3fa6d6fc244bd4f66b976`
- Policy-core contract SHA-256: `2b55d91faf9bda4285a205bae6ee4c4baa0abcc25f6ee871f58df48412f84c3e`
- Mandate Markdown SHA-256: `c4741a947bf8868c00cec77ad64254ee6f05092a30ecdc881697bcf5728a652d`
- Mandate JSON SHA-256: `6d7f2e6353f732cf7d3bbc6e327064439bfaca81cf86af79a70a4c20dda7b030`
- Initial waiting-state SHA-256: `80d919df613cca96729d4f4366af91ff701da07cd31bf353d0a2accb42f636f4`
- Runbook SHA-256: `fd4078edf652c78d3ea05a602732417b41cb4dded6834543329d8be19131c645`
- Historical candidate 001 SHA-256, unchanged: `308dd5af01a4048cd6fb2a796248c324e2d9e6f01b2b44ca68262f98cf070463`
- First prospective candidate 002 SHA-256: `c0635c13762798231de582152b29ccd5a8bc58b0983acb53e02e2a76870d4ac9`
- Candidate 002 validation receipt SHA-256: `aa7d9d5d798dffe06dd2eee023560ebe14beb18e1b20b4685ded4ebd9c05adc6`
- Scientific implementation aggregate: `20f8b296751e1c9b897a63a2adb544c911eb5422a0281afa9fe639734356eba0`

## Hardening result

The universal governor now validates `OC3_OBSERVATIONAL_MULTIPLICITY_ACTION_CONTRACT_002` independently of each action-specific validator. It accepts any nonempty subset of the four mandate authorities, bounded nonnegative request/body/retry reservations, concurrency at most one, sealed literal manifests for network actions, prospectively frozen exact-resource retries, an empty `requested_prohibited_scopes` list, closed scientific firewalls, and frozen Git assertions.

Activation binds the exact waiting state, mandate, policy manifest, first candidate, standing authorization, and branch; snapshots the previous state; appends a sealed activation record; increments sequence; replaces state atomically; and consumes zero budget. Registration is generic and the first registration must match candidate 002. Permits derive from the candidate contract. Their sole consumption identity is `<permit_sha256>.json` under the frozen `PERMIT_CONSUMPTION` directory. Completion revalidates the consumed permit, candidate, authorization, policy core, actual terminal SHA, exposed counters, reservations, and mission budgets.

The production mission remains `WAITING_FOR_STANDING_HUMAN_AUTHORIZATION`, `active=false`, sequence 0, and `permits_issued=0`. The standing-authorization artifact is absent. The production permit and ledger directories contain zero files. No audit, network request, PHOTSYS read, Tractor/source-row read, image-pixel read, morphology/label access, model operation, Panel V3 materialization, or P1 execution occurred.

## Synthetic lifecycle proof

An offline synthetic replay demonstrated, without policy-core mutation:

1. waiting state to synthetic standing authorization and ACTIVE;
2. registration, permit issuance, canonical consumption, synthetic terminal, and completion for an offline local-authority action;
3. registration, eligibility, and permit issuance for a different bounded official-documentation action with positive request/body reservations and `BOUNDED_OFFICIAL_DR9_DOCUMENTATION`;
4. completion of that action followed by registration, eligibility, and permit issuance for a different `PROSPECTIVELY_CONTRACTED_GROUPING_METADATA` action.

Adversarial coverage rejects policy mutation; authority expansion; request/body overflow; concurrency above one; unfrozen retries; every nonzero scientific-firewall counter; every prohibited scope; wrong branch, force push, and main merge; candidate, command, state, and authorization mismatches; permit replay and alternate marker paths; missing consumption; terminal SHA mismatch; and terminal counter/reservation mismatch.

## Verification

- Focused scientific and governor suite: 28/28 passed.
- Affected suite including closed-input tripwires: 153/153 passed; log SHA-256 `345e66452fce657938615766e8927a5f6aea2783d65329de8a2dec9261b2e53c`.
- Full socket/DNS-blocked offline regression: 1248/1248 passed, 0 failed, 0 skipped, 70.924 seconds; `real_network_requests=0`; log SHA-256 `627c61bfa6c0588f927cefe479b038b38f9c8e3d66caa0ad90ae44dcf9de7a5e`.
- Production preflight: `AUTONOMY_HARDENING_VALIDATED`; `network_requests=0`; `permit_issued=false`.

THE ACTIVE POLICY CORE CAN GOVERN LATER DOCUMENTARY AND GROUPING ACTIONS WITHOUT SELF-MODIFICATION.
