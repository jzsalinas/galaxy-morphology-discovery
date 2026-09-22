# OC3 PHOTSYS Documentary 002 Post-Execution Review

`OC3-GALAXY-ELIGIBILITY-PHOTSYS-AUTHORITY-DOCUMENTARY-002` completed with
terminal `PHOTSYS_LITERAL_RESOURCE_URL_BOUND`.

The official directory index exposed the literal href
`survey-bricks-dr9-randoms-0.48.0.fits`, resolving exactly to:

```text
https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/randoms/survey-bricks-dr9-randoms-0.48.0.fits
```

The immutable directory-index body has SHA-256
`09928bee3a1bb5ce114cbae11d6b850c9eb8cffa4a2ee17ac8728924cb55957e`.
The complete Attempt-002 runtime tree seal is
`9ba49a4080fc4501373d3dee5c1c8821f5d2279f833f1e755c3ee562a5043c23`.
The sealed provenance-chain artifact has SHA-256
`9f1fe4de2aa33518b866d29f82c8a33eef3b3bbde1cfb76256e7b384d8fc4a2a`
and binds that body to the two preserved Attempt-001 documentary bodies and
their historical tree seal.

Attempt 002 used one request and 4683 response-body bytes. Cumulative
documentary accounting is three requests and 262366 response-body bytes. It
performed zero FITS HEAD, Range, and full GET operations, decoded zero table
cells, and left every forbidden counter at zero.

The corrected offline parser established that the documented product inherits
the brick columns of `survey-bricks.fits.gz`, adds `PHOTSYS` and
`AREA_PER_BRICK`, and documents exact `PHOTSYS` values ASCII `N`, ASCII `S`,
and ASCII space with their stated footprint meanings.

This result binds documentary provenance and the literal provider URL only.
The FITS HTTP representation, HDU inventory, row cardinality, exhaustive schema,
and selective three-field projection remain unresolved pending the distinct
header-only physical-contract probe. No full acquisition, Panel V2, or P1 is
authorized by Attempt 002.
