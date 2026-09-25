# OC3 Source-Metadata Autonomous Recovery Bootstrap Report 001

Status: **READY FOR AUTONOMOUS RECOVERY ENVELOPE HUMAN REVIEW; INACTIVE**.

## Closed predecessor

- Base branch: `autopilot/source-metadata-acquisition-pilot`
- Exact terminal commit: `b356b448f170d49a03727722324ed0d6e6913c34`
- Outcome: `SOURCE_METADATA_ACQUISITION_INCONCLUSIVE`
- Error: `DATALAB_TRANSPORT_FAILURE`
- Observed transport: one request, HTTP 200, `text/html`, zero application-body bytes, zero retries
- Schema rows, source counts and source rows observed: 0
- Holdout source access and positional-topology operations: 0
- Final report SHA-256: `53e06603f44ac3aaace7ba16b6a4ad94ce3612274a0aaa4f00795a07b425dc71`
- Final state SHA-256: `c066adaeeba21c16a0bc15070c8983c8a7e9d3c9a965c3fa74a9d0a2fbaea8e8`
- Final ledger aggregate: `4618b3a1e739d554d3a8ea38aea3e9718513e4e7a4f11a693591f3af187908ee`
- Runtime terminal SHA-256: `464a165b3281f5ec5c84617880e98d653bc1171c5eaa4d9b314d5464387b7d0e`
- Frozen query-manifest SHA-256: `d25c12b9b9a8715aa8e2ae5a9d885ef88b3ece1dc62d327072c3cc305e15abf8`

The predecessor remains closed and immutable. Its standing authorization, permit and terminal are not reused.

## Architectural correction

Finding `PREMATURE_MISSION_FINALIZATION_ON_RECOVERABLE_TECHNICAL_FAILURE` is frozen prospectively. The new envelope implements `ACTION_TERMINAL != MISSION_TERMINAL`. An action always terminates; the immutable graph then chooses autonomous recovery, scientific finalization or human stop. A recoverable action leaves the mission active, clears the registered action and awaits a new generated candidate.

The Policy Core is generic and contains no Data Lab scientific semantics. Domain invariants and recovery routes are separately sealed. Technical and material requests have independent budgets. Every network action retains the single-use governor permit and supervisor-issued worker capability chain.

## Frozen identities

- Envelope specification SHA-256: `5803faabd501a3ce04824a4d4c07cae003173dd2015e74aff4a02d1e93a566f0`
- Scientific Invariants Manifest SHA-256: `0d2b304e815a949cf7f69d44cd43148eb663fadb68afb47a7e9f767635a329f3`
- Recovery Graph SHA-256: `19e7d6226d6550efbd32c62a4268d682e448f15fb3c490550471286943587fb7`
- Mutable Technical Surface SHA-256: `eb93ca5018204a14965bd148da93d4fce7fb0e97ecfe1ed7b769857b52dd878d`
- Recovery Budget SHA-256: `e399cba2ece0c8a15f7c237552e13f5a5453109ad21f3c3545427c17fce0956f`
- Policy Core contract SHA-256: `c9ea12345636a3e93f52edc1921b8ed797770eda6e4df60f7f5319d2b588b336`
- Policy Core manifest SHA-256: `91d807b956cbb1ee486c0c5fb4c669adc188c4555fb3bc48b8f10f8581a3dcb4`
- Pending mandate SHA-256: `e298d229913b03ff29de6343eeafc96f3b790adc7f5da6ba73f1d92d9d247fdb`
- Waiting-state SHA-256: `3aae657d32ad799572c5b72806ffd65262b9436b98ca444fd3f90ef8c4380a80`
- First diagnostic candidate SHA-256: `928b2ee68c6e294f610fdeb47cc8777ace486a90727f530583c9f38984a9a4f8`
- Controller implementation SHA-256: `16b087fb1919154eecf3d4965aaf8e09af6e048a047732aa5ef647a731544976`
- Candidate factory implementation SHA-256: `7f559db649beeaafdf07075cd6182bf6c8b8f8b927c60944f2aec5e915246ad6`
- Generic engine implementation SHA-256: `cc06c2360e17e75b093fbaf2b3522f59c2524311df084aadea116f20a1ece789`
- Domain governor implementation SHA-256: `d5f88b61724e8ccb304114947d9e8f558677f9505a75b55ff08de2fa29934cb8`
- Complete recovery implementation aggregate: `e19348bd4bb1febc296694c0a89def6865b5b6abbec56e8b2868bf0d45010375`

## Finite envelope

- Recovery generations: 4 maximum
- Code-repair generations: 3 maximum
- Technical requests: 8 maximum
- Technical body bytes: 2,097,152 maximum
- Technical bytes per request: 262,144 maximum
- Same technical failure class: 2 occurrences maximum
- Technical concurrency: 1; retries: 0
- Material requests: 5; material body bytes: 67,108,864
- Material concurrency: 1; retries: 0

The first candidate is `TECHNICAL_RESPONSE_DIAGNOSTIC`, generation 1. It binds the predecessor runtime terminal, exact schema-query semantics, one technical request, a 65,536-byte technical body cap, zero material reservation, exact supervisor/worker argv and unique future permit/capability paths. It remains unexecuted.

## Offline verification

- Focused Recovery Envelope tests: 22 passed
- Affected acquisition/governor tests: 149 passed
- Official socket-firewalled regression: 1,472 passed, 0 failed, 0 skipped
- Real network requests: 0
- Source rows observed: 0
- Source counts observed: 0
- Standing authorization: absent
- Execution permits: absent
- Worker capabilities: absent
- First diagnostic output directory: absent

Synthetic coverage includes current HTML-failure routing, recoverable-action continuation, scientific terminal preservation, credential stop, invariant/query/holdout/Policy Core mutation rejection, mutable-surface validation, parent binding, generation and budget limits, failure-loop stop, distinct permits/capabilities, single-use replay rejection, separate technical/material accounting, successful multi-recovery continuation and mission finalization only after material success.
