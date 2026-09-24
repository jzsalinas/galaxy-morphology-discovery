# OC3 PHOTSYS zero-byte semantic provenance report

Stage: `OC3-GALAXY-ELIGIBILITY-PHOTSYS-ZERO-BYTE-SEMANTIC-PROVENANCE-001`  
Scope: `PHOTSYS_ZERO_BYTE_SEMANTIC_PROVENANCE_ONLY`  
Outcome: `PHOTSYS_0x00_SEMANTICS_INCONCLUSIVE`

## Decision

The observed raw byte `0x00` cannot be mapped reproducibly to the documented outside-footprint PHOTSYS category. The official documentation defines that category with a literal space, while the released file contains `0x00` in 330,208 rows. FITS 4.0 explains `0x00` as the first-character null-string representation of a BINTABLE `A` field and distinguishes it from ASCII space `0x20`, but the standard assigns no survey-footprint meaning.

Exact `desitarget` 0.48.0 source establishes how ordinary random catalogs obtain `N` or `S` and how supplemental outside-brick randoms are generated. The supplemental `zeros=True` route does not contain a `PHOTSYS` field. No evaluated exact source constructs `survey-bricks-dr9-randoms-0.48.0.fits`, adds its `PHOTSYS` column, or demonstrates that outside rows are serialized as `0x00`. The missing historical producer and aggregation pathway is decisive.

This is not the conflict outcome. The documentary space and physical NUL differ at the representation layer, but the documentation does not claim a raw-byte encoding and the absent producer pathway prevents determining whether the mismatch is intentional, incidental, or erroneous.

## Frozen observation

The previously authorized single-byte histogram remains unchanged:

| Raw byte | Count |
|---|---:|
| `0x00` | 330,208 |
| `0x4e` (`N`) | 82,897 |
| `0x53` (`S`) | 249,069 |
| all other bytes, including `0x20` | 0 |

The total is 662,174. All V1 count cross-checks pass. The histogram artifact is `oc3/photsys_byte_histogram/OC3-GALAXY-ELIGIBILITY-PHOTSYS-BYTE-HISTOGRAM-001/OC3_PHOTSYS_RAW_BYTE_HISTOGRAM_001.json`, SHA-256 `010e2c4a7465d0b08bc3c6df1e8e52a4eafa0c497a7d030038f34cc377e54510`; `V1_CONSISTENCY.json` has SHA-256 `af1134cd8f57a33675ff1a5059cb90e973eaefc54a0a169acfab5b05c0a29d80`.

These are aggregate historical observations. The autonomous mission opened no real FITS table byte and observed no PHOTSYS, BRICKNAME, BRICKID, or ROOT value.

## FITS representation evidence

The preserved normative source is *Definition of the Flexible Image Transport System (FITS), Version 4.0*, from `https://fits.gsfc.nasa.gov/standard40/fits_standard40aa-le.pdf`, body SHA-256 `5624dca15659caf54c56127b4df9af05fd930c8f6d997fcb4bea2b1a5c1bc573`.

Section 7.3.3.1, printed page 25, specifies the BINTABLE `TFORMn` type `A` character field. Its bounded context states that the string may terminate at ASCII NULL, identifies code `00`, and defines a null string by ASCII NULL in the first character. The glossary independently defines ASCII NULL as all bits zero and ASCII space as decimal 32, hexadecimal 20. The bounded evidence is sealed in `oc3/OC3_PHOTSYS_FITS_LEGACY_OFFLINE_EVALUATION_002.json`, SHA-256 `ca33396821f5f95ffc6323fe21f3c7bfbcd57650db4bb6f460a9765578c038f5`.

Therefore:

- `BINTABLE_A_NULL_RULE`: supported;
- `ASCII_NULL_0x00`: supported;
- `ASCII_SPACE_0x20`: supported;
- `0x00` and `0x20` are representation-distinct: supported;
- survey-footprint semantics from FITS: unsupported and outside the standard's role.

## Official Legacy Survey documentation

The preserved official page is `https://www.legacysurvey.org/dr9/files/`, body SHA-256 `d0b51d66529cb4c62db7e8ae1df22d6976879f46dcd62b4e6993729b42674c85`.

Its named section for `survey-bricks-dr9-randoms-0.48.0.fits` documents a one-character PHOTSYS field with `N`, `S`, and a literal single space for bricks officially in the north, south, and outside the footprint. The bounded section context is sealed in the same offline-evaluation artifact. The literal space was preserved and was never normalized to NUL.

The current page was not independently proven byte-identical to its production-time historical state. The original bounded research attempt ended before publishing per-resource retrieval timestamps, so the bodies are bound by their immutable local hashes and the failed-attempt review rather than reconstructed timestamps.

## Exact producer version and source

The official GitHub metadata establishes this exact chain:

```text
tag 0.48.0
→ annotated tag object 1957b46481368c3b386a2113dc734538650c492c
→ commit dd30297f9d50fcb7bbba57d79d4b8fc86cb35701
→ root tree 514756ea86baa049a05394dbc01fdde008a87288
```

Evidence includes the tag-ref body SHA-256 `9289a01c82464f9ffe901b907e165c2c9bb7de7c3e17e454d112a3eb6ae2476d`, annotated-tag body SHA-256 `c8a62b156a83788ae395ad2d866bdc114a958f3af93984326594d0c5dabeaef8`, commit terminal SHA-256 `8ec4addc3ca604c5602a76fd46a6c6962bbbd03c7aed7f5cd29abd9eca38720e`, and complete non-truncated 336-entry tree body SHA-256 `df6d494a5cd92543f28e4f7e36758380f5223526173ec2b645cd2ec7ced424fc`.

The source evaluation covered the prospectively frozen mandatory producer set:

- `py/desitarget/randoms.py`;
- `py/desitarget/io.py`;
- `bin/select_randoms`;
- `bin/supplement_randoms`;
- `doc/changes.rst`.

It then covered every additional non-test exact-tree path whose name contains `randoms`, plus the resolver linked by the official DR9 page:

- `bin/split_randoms`;
- `bin/alt_split_randoms`;
- `py/desitarget/targets.py`.

The deterministic terms were `survey-bricks`, `survey-bricks-dr9-randoms`, `AREA_PER_BRICK`, `PHOTSYS`, `supplement_randoms`, `zeros=True`, `write_randoms`, and `resolve`.

### Observed behavior

For ordinary `zeros=False` processing, `randoms.py` allocates `PHOTSYS` as `|S1`; the pixel-reading path assigns `S` for DECam and `N` otherwise. For missing bricks, `supplement_randoms` computes all bricks minus completed bricks and calls `select_randoms_bricks(..., zeros=True)`. That route returns a structured array containing BRICKID, BRICKNAME, RA, DEC, NOBS_G/R/Z, and EBV, with no PHOTSYS field. `io.write_randoms(..., supp=True)` writes this supplemental array and records `SUPP` in the header.

`targets.resolve` resolves only north/south overlap. The two split executables shuffle and divide an existing catalog without adding PHOTSYS or AREA_PER_BRICK. None of these exact sources contains the named summary filename or constructs the brick-summary table.

The mandatory producer trace is SHA-256 `ab512374f31cece4f44a13902ad4839d3379a397956850aef4c51bd6b47f420d`; the selected-production search is SHA-256 `a12ad4403e84e520b13c38f479a48a196e82ecad36fad6a93d46d10a27fa324f`.

## Named-product provenance search

The official DR9 page exposes two concrete provenance leads. Its tagged `targets.py` resolver was acquired at the exact commit and evaluated as described above. Its Myers et al. (2023) ADS link was frozen and requested once; ADS returned HTTP 405 with an AWS WAF CAPTCHA signal. No response body was read, no full-text link was discovered, and no claim was taken from the paper. The action terminal SHA-256 is `65b82e4117b4667a92ae1eb42237418303bde634b088729b87c657eb3f38bde0`.

The exact commit archive was also tested through bounded HEAD and Range actions. HEAD supplied no usable content length; the server ignored `Range: bytes=0-0` with HTTP 200. No archive body was read by those probes. The prior full acquisition had already ended at its frozen body cap and could not be replayed.

No other literal official producer or aggregation resource is identified by the acquired official page or the deterministic exact-tree path inventory. Acquiring unspecified sources or crawling beyond those identities would violate the frozen discovery rule; replaying the consumed archive attempt lacks a prospective restart rule.

## Claim matrix and inference

The canonical completed matrix is `oc3/OC3_PHOTSYS_ZERO_BYTE_SEMANTIC_PROVENANCE_CLAIM_MATRIX_001.json`. Observation, official documentation, and FITS representation claims are supported. All three required producer claims remain unresolved. Independent footprint evidence is not applicable under the frozen stage. The final mapping inference remains unresolved.

The exact missing link is the historical generator or aggregation procedure that created `survey-bricks-dr9-randoms-0.48.0.fits`, populated its PHOTSYS column for outside-footprint bricks, and serialized that column without a later rewrite. Count coincidence, FITS null semantics, normal N/S assignments, and the supplemental `zeros=True` pathway do not replace that link.

## Budgets and firewall

The parent mission budget was 24 public-source requests and 33,554,432 application-body bytes. Final conservative accounting is:

- requests consumed: 18; remaining: 6;
- application-body bytes consumed: 16,555,485; remaining: 16,998,947;
- retries in autonomous actions: 0;
- concurrency: 1;
- astronomical-data GETs: 0;
- real PHOTSYS bytes observed by the autonomous mission: 0;
- BRICKNAME values observed: 0;
- BRICKID values observed: 0;
- ROOT values observed: 0.

## Terminal boundary

The required outcome is `PHOTSYS_0x00_SEMANTICS_INCONCLUSIVE` because the exact outside branch, named-product generation/aggregation, and physical serialization pathway cannot be proven and no direct authoritative contradiction determines the conflict outcome.

Historical PHOTSYS V1 remains failed and was not amended. No PHOTSYS V2 resolver exists. Panel V2 remains `NOT_STARTED`. P1 remains `BLOCKED`. No morphology, model, embedding, clustering, anomaly, preprocessing, or image-inspection operation was performed.
