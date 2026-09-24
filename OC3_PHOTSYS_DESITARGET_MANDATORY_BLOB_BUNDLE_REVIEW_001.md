# OC3 exact desitarget mandatory-source review 001

The governed mandatory-blob action completed successfully for exact `desitarget` commit `dd30297f9d50fcb7bbba57d79d4b8fc86cb35701`.

- Terminal state: `DESITARGET_MANDATORY_BLOB_BUNDLE_ACQUIRED`
- Terminal SHA-256: `aa87deb10c92093ec4576f39f09c376046ed636f46ea85993e25f62225348582`
- Producer trace SHA-256: `ab512374f31cece4f44a13902ad4839d3379a397956850aef4c51bd6b47f420d`
- Search-results SHA-256: `4c63d5f1237a98518df0a1a406dffdbabb939ac3413c0ece641b8667cf4f4207`
- Exact source blobs acquired: `5`
- Requests consumed by this action: `5`
- Application-body bytes consumed by this action: `389469`
- Retries: `0`
- Remaining requests: `10`
- Remaining application-body bytes: `17072719`

## Observed producer behavior

The exact source provides the following positive evidence:

1. `bin/supplement_randoms` describes its output as random locations in missing, outside-footprint bricks, calls `desitarget.randoms.supplement_randoms`, and writes the result through `io.write_randoms(..., supp=True)`.
2. `supplement_randoms` computes the set difference between all bricks and completed bricks, then calls `select_randoms_bricks(..., zeros=True)`.
3. In `get_quantities_in_a_brick`, the ordinary `zeros=False` branch allocates `PHOTSYS` as `|S1`; its pixel-reading route assigns `S` when the observed instrument is `decam` and `N` otherwise.
4. The `zeros=True` branch allocates only `BRICKID`, `BRICKNAME`, `RA`, `DEC`, `NOBS_G`, `NOBS_R`, `NOBS_Z`, and `EBV`. It does **not** allocate `PHOTSYS`.
5. `write_randoms` passes the supplied structured array to `write_with_units` and records `SUPP` in the FITS header, but the acquired source does not show a step that adds `PHOTSYS` to the supplemental array.

## Scientific boundary

The observed zero-initialized supplemental pathway therefore does not explain the physical `PHOTSYS=0x00` bytes in `survey-bricks-dr9-randoms-0.48.0.fits`. Count coincidence, the `zeros=True` call, ordinary `N`/`S` assignment, and the `|S1` dtype remain insufficient to establish the required semantic mapping.

The complete exact commit tree contains no literal occurrence of the named summary product in the five prospectively selected mandatory source blobs, and the frozen search recorded `DESITARGET_0_48_0_NAMED_SUMMARY_GENERATOR_NOT_FOUND`. This is a negative result for the evaluated source set, not proof that no external production or aggregation code existed.

The following links remain unproven:

- the exact code that created `survey-bricks-dr9-randoms-0.48.0.fits`;
- the transformation or aggregation that introduced its `PHOTSYS` column;
- the exact outside branch that produced physical byte `0x00` in that column;
- the FITS serialization behavior for that named product.

No semantic outcome is selected by this action. All astronomical and protected-value firewall counters remain zero.
