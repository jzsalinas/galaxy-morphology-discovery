# OC3 standing autonomy mandate 001 — prospective revision 002

State: `PENDING_HUMAN_AUTHORIZATION`. This document does not activate autonomy or authorize an execution.

## Mission

Close the PHOTSYS zero-byte semantic/provenance question for `survey-bricks-dr9-randoms-0.48.0.fits` with exactly one frozen scientific outcome, or stop with the exact mandate expansion required from the human reviewer.

The scientific question, four outcomes, authority classes, request/body budgets, historical accounting, no-data firewall, PHOTSYS V1 failure, absent V2 resolver, Panel V2 boundary, and P1 boundary are unchanged from revision 001.

## Frozen policy core and authorization

The canonical `OC3_AUTONOMY_POLICY_CORE_MANIFEST_001.json` binds the universal policy implementation. A future standing authorization must bind the exact mandate JSON SHA-256, policy-core manifest SHA-256, and current waiting-state SHA-256. Activation is permitted only through the deterministic governor transition. Manual state editing is not activation.

While autonomy is `ACTIVE`, policy-core mutation is forbidden and results in `STOP_REQUIRES_HUMAN`.

## Evidence envelope

Only these classes are admissible:

1. official Legacy Survey documentation directly relevant to the named DR9 product;
2. authoritative FITS standard or official NASA/HEASARC documentation;
3. exact desitarget 0.48.0 tag, release metadata, and source;
4. official DESI/Legacy Survey provenance needed to connect code to the named summary product;
5. peer-reviewed random-catalog documentation directly needed for generation provenance.

Every network action requires a literal sealed resource manifest and generic action contract. Broad crawling, redirects not frozen prospectively, mirror substitution, and evidence outside these classes are prohibited.

## Mission budgets and firewall

Parent limits remain 24 public-source requests, 33,554,432 application-body bytes, concurrency 1, and zero astronomical-data GETs. Historical consumption remains 6 requests and the conservative 16,009,494-byte maximum. The initial remaining budgets are 18 requests and 17,544,938 bytes. Default retries are zero; at most one exact-resource retry may be prospectively frozen within the parent limits.

At all times the counters for astronomical-data GETs and real PHOTSYS, BRICKNAME, BRICKID, and ROOT observations must remain zero.

## Lifecycle and terminal boundary

Actions use `OC3_AUTONOMOUS_ACTION_CONTRACT_001`, action-specific validation, deterministic registration, single-use permits, consumption-before-execution, verified terminal transitions, and append-only state evidence.

The mission ends at exactly one of:

- `PHOTSYS_0x00_OUTSIDE_SEMANTICS_PROVEN`;
- `PHOTSYS_0x00_REPRESENTATION_MISMATCH_BUT_OUTSIDE_MAPPING_SUPPORTED`;
- `PHOTSYS_0x00_SEMANTICS_INCONCLUSIVE`;
- `PHOTSYS_DOCUMENTATION_PHYSICAL_CONFLICT_UNRESOLVED`.

It also stops at `STOP_REQUIRES_HUMAN` for budget expansion, authority expansion, protected-value access, policy-core change, evidence-integrity failure, changed scientific criteria or question, new credentials/privileges, destructive evidence handling, force push/history rewrite, Panel V2, P1, morphological discovery, or V2 resolver work.
