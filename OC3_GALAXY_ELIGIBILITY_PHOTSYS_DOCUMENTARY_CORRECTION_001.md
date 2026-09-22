# OC-3 PHOTSYS documentary correction 001

Status: prospective correction prepared for human review. No network request or
FITS operation is authorized by this document.

## Historical attempt preserved

`OC3-GALAXY-ELIGIBILITY-PHOTSYS-AUTHORITY-PROBE-001` remains an immutable,
completed documentary attempt with terminal
`PHOTSYS_AUTHORITY_RESOURCE_CONTRACT_INCONCLUSIVE`. Its observed accounting is
2 requests and 257683 body bytes. It performed no FITS request, decoded no table
cell, and recorded zero forbidden counters.

The preserved audit tree seal is
`bd0f6f78828e32261514a7c8a17951be759b3a219e1d232983a82532bacc45d8`.
The two reused documentary body hashes, in original resource order, are:

1. `d0b51d66529cb4c62db7e8ae1df22d6976879f46dcd62b4e6993729b42674c85`
2. `cebd41a5c9c0ec10e91c5956e508ab9cb7ca96d9f46bc413db63ff82c4d18e9a`

Attempt 002 is a distinct documentary attempt. It is neither a retry nor a
resume of attempt 001.

## Parser defect and correction

The previous parser used generic normalized substrings that failed to recognize
two facts in the preserved official DR9 document. The corrected parser requires
the exact documented section identities and structured table rows. It recognizes:

- `survey-bricks-dr9-randoms-0.48.0.fits` as a file similar to
  `survey-bricks.fits.gz`, with the same brick columns plus `PHOTSYS` and
  `AREA_PER_BRICK`;
- the exact `PHOTSYS` field type `char[1]` and the documented ASCII values
  `"N"`, `"S"`, and `" "`, with their north, south, and outside-footprint
  meanings.

The parser also requires the exact `survey-bricks.fits.gz` brick table section,
its `BRICKNAME` row, and the documented one-to-one `BRICKID` relation. Similar
wording outside the expected section and table structure is rejected. The
canonical offline parse evidence is
`oc3/INPUTS/OC3_PHOTSYS_DOCUMENTARY_002_HISTORICAL_PARSE_EVIDENCE.json`.

## Prospective documentary attempt 002

Stage identity:
`OC3-GALAXY-ELIGIBILITY-PHOTSYS-AUTHORITY-DOCUMENTARY-002`.

Exactly one new official documentary resource is proposed:

- URL: `https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/randoms/`
- role: `OFFICIAL_DR9_RANDOMS_DIRECTORY_INDEX`
- purpose: observe an actual hyperlink for the exact basename
  `survey-bricks-dr9-randoms-0.48.0.fits`.

The href is accepted only when it resolves over HTTPS on
`portal.nersc.gov`, remains below
`/cfs/cosmo/data/legacysurvey/dr9/randoms/`, has the exact target basename,
and has no query or fragment. Plain text, a constructed URL, mirrors, other
directories, and similar filenames or versions do not satisfy the rule.

The stage-local cap is 262144 body bytes. It permits one primary documentary
GET, at most one redirect, at most two total requests, concurrency one, and no
automatic retry. The two historical requests and 257683 bytes remain cumulative
evidence and are not reset.

The transport has no FITS HEAD, Range, or FITS GET capability. Those counters
and `table_cell_values_decoded` are fixed at zero. Access to Tractor, SDSS,
Gaia, DESI, Panel V2, location selection, cohort materialization, and
morphological discovery remains outside scope.

The only successful terminal for this attempt is
`PHOTSYS_LITERAL_RESOURCE_URL_BOUND`. It establishes the literal resource URL
from observed href evidence. It does not establish
`PHOTSYS_AUTHORITY_RESOURCE_CONTRACT_RESOLVED`; the FITS physical contract
remains unobserved.

## Offline validation

- Focused regression: 179 tests passed, 0 failed, 0 skipped.
- Full regression: 991 tests passed, 0 failed, 0 skipped.
- Full runner network accounting: `real_network_requests=0`.
- Input validation: `PHOTSYS_DOCUMENTARY_002_INPUTS_VALID`.
- Dry run: `PHOTSYS_DOCUMENTARY_002_DRY_RUN_OK` with zero network and zero FITS
  operations.

The sealed candidate is
`oc3/INPUTS/OC3_PHOTSYS_DOCUMENTARY_002_CANDIDATE.json`. Its implementation
aggregate is
`6943d4a8d50d3a6f1fdf49287601e310d4dc528aac332267b1bb8796ae17f46c`.
Its SHA-256 is
`19087fbfd6050d186e67acbe8fbf7fc273c6a19066a23dac72afb2f9945e6da7`.
The bound command argv SHA-256 is
`d1216b3165926f677ec210b83e0733caf6785c60b3feb4545182e596d232ad28`.

The required final authorization path is
`oc3/OC3_PHOTSYS_DOCUMENTARY_002_FINAL_AUTHORIZATION.json`; that file is absent.
Real execution remains unauthorized pending human review.
