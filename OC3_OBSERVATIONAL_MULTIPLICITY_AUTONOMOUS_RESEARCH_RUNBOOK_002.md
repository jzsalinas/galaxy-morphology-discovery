# OC3 Observational Multiplicity Autonomous Research Runbook 002

All commands run from the repository root with `oc3/.venv/bin/python`. Preauthorization checks are offline.

## Before activation

1. Validate Policy Core V2, Mandate 002, the waiting state, and its state-bound first candidate:
   `oc3/.venv/bin/python oc3/oc3_observational_multiplicity_governor.py --validate`
2. Inspect status:
   `oc3/.venv/bin/python oc3/oc3_observational_multiplicity_governor.py --status`
3. Stop. A separately reviewed standing authorization must bind Manifest 002, Mandate 002, the exact waiting-state SHA, and Candidate 003 path/SHA.

## Governed lifecycle

Activation derives the first candidate from state; universal code supplies no candidate identity. Each action follows strict validation, registration, generic eligibility, immutable permit issuance, canonical SHA-derived permit consumption, material execution, immutable terminal creation, and separate governed completion transition.

The first executor command is sealed in Candidate 003. It explicitly supplies candidate, Permit 003, standing authorization, autonomy state, and output directory. The executor validates and consumes the permit before one local audit call. It never performs the state completion transition.

Later documentary or grouping actions use prospective specifications, validators, candidates, and literal manifests when networked without policy-core modification. Any V2 policy mutation after authorization requires `STOP_REQUIRES_HUMAN`.

Compact governance artifacts belong in Git; runtime-heavy evidence remains local. Do not push, merge main, rewrite history, reopen PHOTSYS, create Panel V3, or run P1.
