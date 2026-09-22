# OC3 PHOTSYS full acquisition — post-execution review

## Disposition

The real stage `OC3-GALAXY-ELIGIBILITY-PHOTSYS-AUTHORITY-ACQUISITION-001` ended in `PHOTSYS_FULL_FILE_BYTES_ACQUIRED`. This review was performed offline from the immutable publication, checkpoint, terminal, authorization, candidate, and reviewed physical contract. The execution tree was not altered.

## Acquired resource

- Literal URL: `https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/randoms/survey-bricks-dr9-randoms-0.48.0.fits`
- Publication: `oc3/photsys_authority_full_acquisition/OC3-GALAXY-ELIGIBILITY-PHOTSYS-AUTHORITY-ACQUISITION-001/RAW_IMMUTABLE/survey-bricks-dr9-randoms-0.48.0.fits`
- Size: `52323840` bytes
- SHA-256: `804d2caf327e808bb4047cc8792a5b08d01d8875149b7b7eb019ce982f6c3f8c`
- Mode: `0444`
- Provider ETag: `"31e6600-5b8a40bdace7f"`
- Provider Last-Modified: `Mon, 11 Jan 2021 18:26:36 GMT`
- HTTP status: `200`
- Stage requests: `1`
- Stage body bytes: `52323840`
- Residual partial staging: absent

The checkpoint SHA-256 is `289da27a13789682546757f74767d50dcb94c62904d668bb7c4d108758e7c51a`; the terminal SHA-256 is `a3d2a0cabc8387cffcf2f59efb81393d5aad5a802bfea26716ffa4b9914e830b`. Their canonical seals validate, the candidate binding matches, and the published file hash and byte count match both receipts.

## Firewall and contract binding

The acquisition was byte preservation only. It instantiated no FITS table-value decoder and recorded `table_cell_values_decoded = 0`. The forbidden decode, materialization, serialization, logging, random-point-row, morphology, and whole-row semantic operations were absent; their applicable counts remain zero. No table cell was inspected during acquisition or this review.

The observation is bound to `oc3/INPUTS/OC3_PHOTSYS_AUTHORITY_REVIEWED_PHYSICAL_CONTRACT_001.json`, SHA-256 `30b03a47adfc5cb1cc18b8c930dee2fa1d3f04597768558f84602d6ed2aae56f`, state `PHOTSYS_AUTHORITY_PHYSICAL_CONTRACT_REVIEWED`. The acquired representation preserved the expected size, ETag, Last-Modified value, literal URL, and identity encoding.

This review establishes complete immutable provider-byte preservation. It does **not** establish any observed `BRICKNAME`, `BRICKID`, or `PHOTSYS` value; it does not validate cardinality at the value layer, uniqueness, identity joins, PHOTSYS counts, or Panel V2 eligibility.

## Reconciled accounting

`OC3_PHOTSYS_NETWORK_ACCOUNTING_RECONCILIATION_001.json`, SHA-256 `1074bf77a0f1868dbc251c0031fd8eb8088861ab232b8ae9678b024a1a444a7e`, derives every delta once from canonical receipts:

- PHOTSYS subtotal: `9` requests and `52597726` body bytes.
- Project cumulative after this acquisition: `331` requests and `292213932` body bytes.
- Discrepancies: none.

Cumulative accounting never resets. The acquisition review executed zero network requests.

## Next boundary

The next possible stage is the separately reviewed offline specification `OC3_PHOTSYS_SELECTIVE_VALUE_VALIDATION_SPEC.md`. It may eventually authorize only the projection `BRICKNAME`, `BRICKID`, and `PHOTSYS`. No decoder, execution candidate, Panel V2 selection, or P1 operation is authorized by this review.
