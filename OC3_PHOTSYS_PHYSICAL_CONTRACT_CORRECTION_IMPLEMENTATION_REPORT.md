# OC3 PHOTSYS physical-contract correction — implementation report

## Result

The derived HDU labels are corrected from `[null,"PRIMARY"]` to `["PRIMARY","BINTABLE"]`. The defect was an index test evaluated before the current HDU was appended. The implementation now captures the current zero-based index and uses index 0 for `PRIMARY`; extension labels come from `XTENSION`.

The four immutable header blocks from the completed physical probe were reconstructed offline and verified against tree seal `6a4c0d06794b86a929efd68ec58908f17c8a2289c5e59fd881271c03eb93a27c`. The correction introduced no network request and no table-cell decode.

## Frozen outputs

- Post-execution review: `OC3_PHOTSYS_PHYSICAL_PROBE_POST_EXECUTION_REVIEW.md`, SHA-256 `9da0020660377e7ef9825b77e0ef465f4018a1716272727ccc578a439e3583cf`
- Correction artifact: `OC3_PHOTSYS_PHYSICAL_CONTRACT_CORRECTION_001.json`, SHA-256 `3a7838e89f93b309439470848bcfd932c6e758b003723dbf946de90c3c93c5dc`
- Reviewed physical contract: `oc3/INPUTS/OC3_PHOTSYS_AUTHORITY_REVIEWED_PHYSICAL_CONTRACT_001.json`, SHA-256 `30b03a47adfc5cb1cc18b8c930dee2fa1d3f04597768558f84602d6ed2aae56f`
- Corrected implementation aggregate: `800f413ee53ac2fecad66386a49ecaff04989d3ffce6b232cb52916a3c9dbbe6`
- Prospective Stage-B candidate: `oc3/INPUTS/OC3_PHOTSYS_FULL_ACQUISITION_CANDIDATE_001.json`, SHA-256 `a9a59b3cd192ab4e1904df417ffd7ceba2f17760db60c9d13c19711e44f280dd`

Every physical finding independent of the faulty label remains unchanged: HTTP representation, HDU count, 662,174 rows, 79-byte rows, 13-column schema, required offsets and types, `AREA_PER_BRICK` structural presence, table-data boundary, selective projection, and zeroed firewall counters.

## Verification

Focused offline suite: 153 tests passed, 0 failed, 0 skipped.

Complete offline regression: 1,019 tests passed, 0 failed, 0 skipped; `real_network_requests=0`.

The Stage-B candidate validates offline and binds one primary GET, zero additional HEAD requests, zero automatic retries, concurrency 1, and exactly 52,323,840 expected body bytes. It specifies immutable staging/publication, SHA-256, mode `0444`, and separate resume authorization. Final human authorization is absent, so acquisition remains blocked.

The prospective post-acquisition design limits value decoding to `BRICKNAME`, `BRICKID`, and `PHOTSYS`, verifies row and identity constraints, and produces N/S/blank/missing/invalid/conflict aggregates without panel selection.
