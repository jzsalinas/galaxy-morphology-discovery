# OC-3 fixed native image/invvar resource contract 001

**Prospective stage:** `OC3-FIXED-NATIVE-RESOURCE-PROBE-001`

**Frozen selection:** `LOCATION_SELECTION_VALIDATED`; selection SHA-256 `2e6f2cb070a363e9e3dbdb1f25670590c33500a293bb926d8ff94657a2ff8860`.

**Current state:** the exact twelve identities and literal URLs are closed; their HTTP and physical FITS contracts remain `UNRESOLVED` pending the bounded header probe. No image or inverse-variance body has been acquired.

## Closed inventory

The machine contract is `oc3/INPUTS/OC3_FIXED_NATIVE_RESOURCE_CONTRACT_001.json`. It contains exactly, in order, south then north:

1. image g, r, z;
2. invvar g, r, z.

The brick identities come only from the frozen locations. Directory components `344` and `247` are reused from the exact resources resolved by `OC3-RESOURCE-CONTRACT-PROBE-002`; this stage does not derive or rediscover them. Filenames use the official DR9 families:

```text
legacysurvey-<brick>-image-<filter>.fits.fz
legacysurvey-<brick>-invvar-<filter>.fits.fz
```

The literal URLs combine those documented filename families with the already observed exact coadd directories. Construction does not assert that an HTTP resource exists; existence, final URL, Content-Length and optional ETag remain probe observations.

## Documentary contract

[Official DR9 files documentation](https://www.legacysurvey.org/dr9/files/#image-stacks-region-coadd) is the documentary authority for the filename families and the following facts:

- image is the inverse-variance weighted coadded science image, documented in the logical primary role, in nanomaggies per pixel;
- invvar is the corresponding coadd inverse variance, in `1/(nanomaggies)^2` per pixel;
- the nominal native coadd grid is 3600×3600, TAN, 0.262 arcsec/pixel;
- `.fits.fz` is the published representation suffix.

The documentation does not establish the exact physical tiled-compression HDU, compression mapping, dtype, Content-Length or ETag of these twelve files. It also does not establish an invvar logical HDU. Those fields remain `UNRESOLVED`; the contract does not copy physical facts from NEXP, PSFSIZE, MASKBITS, another brick or another release.

## Bounded header probe

The sealed binding is `oc3/INPUTS/OC3_FIXED_NATIVE_RESOURCE_PROBE_BINDING_001.json`. Its operation is limited to the exact twelve URLs:

- concurrency 1, retries 0;
- twelve HEAD requests first;
- up to sixteen aligned 2880-byte FITS header ranges per resource;
- exact HTTP 206 and exact `Content-Range` required;
- at most 192 Range requests and 552,960 charged Range-body bytes;
- stage-local maximum 204 requests;
- imported cumulative state 194 requests and 93,663,566 body bytes;
- the historical value 200 is recorded but is not a future hard stop;
- the unchanged global HTTP body cap is 1,610,612,736 bytes;
- zero bulk GETs and zero science pixel values observed.

The per-resource value `1,460,326,066` is an operational upper bound derived from the remaining global body allowance after the frozen PSF reservation. It is not an observed or documented content length.

Every successful HEAD is checkpointed before advancing. Every fully parsed resource header is checkpointed before advancing. Aggregate history is immutable and a current aggregate is atomically replaced. A failure preserves all completed checkpoints and charges every started Range at its full 2880-byte bound.

The parser stops in the header block containing `END`. It may skip a primary data span arithmetically to reach the first image-bearing extension, but it never requests that span and never requests the first data block of the image HDU. It has no Astropy array access, memmap, pixel statistics, crop, rendering or visualization path.

## Stop condition

The bounded probe is required. No fixed image/invvar contract is promoted to resolved before its twelve checkpoints exist and validate. The probe is a human-run metadata/header operation and does not authorize subsequent acquisition.

**IMAGE/INVVAR BULK ACQUISITION REMAINS NOT AUTHORIZED.**

**FROZEN LOCATIONS REMAIN UNCHANGED.**

**OC-3 MORPHOLOGICAL SCIENTIFIC PHASE REMAINS NOT STARTED.**
