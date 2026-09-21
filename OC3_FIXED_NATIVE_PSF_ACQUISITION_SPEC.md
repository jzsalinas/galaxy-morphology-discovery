# OC-3 fixed native products and PSF acquisition specification

## Status and scope

This document freezes a prospective acquisition candidate for
`OC3-FIXED-NATIVE-PSF-ACQUISITION-001`. It does not authorize network execution.
The candidate is bound to:

- location selection SHA-256 `2e6f2cb070a363e9e3dbdb1f25670590c33500a293bb926d8ff94657a2ff8860`;
- fixed-native resolved-contract SHA-256
  `8e8ac029aa61e82b2a089205aff4781123700a30ce24353dd95e5eaedd55befc`;
- coadd-PSF resolved-contract SHA-256
  `8f7ba5c0f50f26f240ff08ece3a8e0afef62559cb35f4947423136a05904bf30`;
- cumulative starting state: 280 requests and 93,968,846 body bytes.

The six locations and their eighteen P0/P1/P2 points are immutable. Provider
behavior cannot trigger replacement or coordinate recomputation.

## Closed inventory

The stage may acquire exactly thirty provider responses:

1. Twelve native DR9 files in fixed order: south image `g,r,z`; south invvar
   `g,r,z`; north image `g,r,z`; north invvar `g,r,z`.
2. Eighteen coadd-PSF FITS responses in slot order S1–S3, N1–N3 and point order
   P0, P1, P2.

The PSF transport artifacts remain mapped to 54 observational identities. One
exact provider response maps to one slot/point and three identities `g,r,z`; it
is preserved whole and is not rewritten into per-band files.

## Representation contracts

Fixed native HEAD validation must match the already observed content length and
ETag exactly. A mismatch stops before GET. Each GET must match the literal URL,
length and identity encoding. FITS validation requires the observed logical and
physical HDU mapping, tiled-compression mapping, `float32`, shape `3600×3600`,
TAN WCS and the exact WCS/header facts recorded by the bounded header probe.
No alternate URL, reprobe or release substitution is allowed.

Every PSF response must be FITS with exactly three image planes in explicit
`g,r,z` order and `float32` dtype. Shapes are frozen independently:

| Region | g | r | z |
|---|---:|---:|---:|
| south | 63×63 | 63×63 | 63×63 |
| north | 31×31 | 31×31 | 63×63 |

`same_schema_north_south=false`. Padding, cropping, resizing, resampling,
interpolation and normalization are prohibited. PSF units and deployed service
version remain `UNRESOLVED`; normalization remains
`SOURCE_VERIFIED_NOT_DIRECTLY_OBSERVED`. ETag may be absent and Last-Modified
may be present.

## Budgets and request plan

- Fixed native exact body reservation: 144,766,080 bytes.
- PSF historical total envelope: 56,623,104 bytes.
- PSF per-response cap: 3,145,728 bytes.
- Primary stage body reservation: 201,389,184 bytes.
- Global body cap: 1,610,612,736 bytes.
- Disk reservation: 402,778,368 bytes.
- I/O reservation: 805,556,736 bytes.
- Concurrency: one.

The primary request plan is 12 fixed-native HEAD, 12 fixed-native GET, zero PSF
HEAD and 18 PSF GET: 42 requests. Dynamic PSF HEAD is omitted because the
resolved service contract was established through bounded GET and no useful
identity/length guarantee was observed for HEAD. A six-request pool is reserved
only for a separately reviewed resume, making the stage cap 48. There are no
automatic retries or automatic resume, and the initial execution cannot consume
the retry pool.

## Staging, publication and failure

Every complete body first enters `STAGING`, receives SHA-256 validation and
structural validation, and is then moved without rewriting into read-only
`RAW_IMMUTABLE`. Existing identities are never overwritten. Band-level PSF
indexing references the same bundled response.

The ledger, attempts, completed bodies, checkpoints, hashes, staging state and
cumulative accounting are persisted after every operation. A partial result
stops. The same audit directory cannot be reopened by the initial command; a
continuation requires a separately sealed resume authorization and must reuse
validated immutable resources.

Success is exactly `BOUNDED_NATIVE_PRODUCTS_ACQUIRED` and requires 12/12 native
resources, 18/18 PSF responses, all 54 PSF identities mapped, unchanged
locations and zero cutout extraction. It does not approve preprocessing,
morphology inspection, observer audit or the scientific OC-3 phase.

## Authorization boundary

The machine candidate is
`oc3/INPUTS/OC3_FIXED_NATIVE_PSF_ACQUISITION_CANDIDATE_001.json`. It binds the
two resolved contracts, exact resources, identities, implementation, budgets,
order and success terminal. Network execution additionally requires the absent
`oc3/INPUTS/OC3_FIXED_NATIVE_PSF_ACQUISITION_AUTHORIZATION_001.json` to bind the
current candidate file hash. Candidate sealing is not authorization.

**OC-3 MORPHOLOGICAL SCIENTIFIC PHASE REMAINS NOT STARTED.**
