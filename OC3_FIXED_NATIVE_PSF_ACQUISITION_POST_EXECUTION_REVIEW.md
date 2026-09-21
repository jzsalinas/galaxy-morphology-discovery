# OC-3 fixed native products and PSF acquisition post-execution review

## Outcome

The human-executed stage `OC3-FIXED-NATIVE-PSF-ACQUISITION-001` reached the
exact terminal `BOUNDED_NATIVE_PRODUCTS_ACQUIRED`. A subsequent local audit
validated the frozen candidate binding, request and byte accounting, immutable
publication, checkpoints, body checksums and PSF identity mappings. The audit
made zero network requests and decoded zero science array values.

## Frozen evidence

| Evidence | Value |
|---|---|
| Candidate SHA-256 | `961a763e5732b38c5193764a785a3799b0a74e9e42de111fa1de08c8d4cc2951` |
| Terminal SHA-256 | `ca55cd8cd4009b2e5af2466abf6cd08ac3e6b1c2811f3d41fbe7bea495eda875` |
| Ledger SHA-256 | `fac57a450cb263799e0940c430f730e92835d308c537a8323c3ac4e129b5476c` |
| Local audit evidence SHA-256 | `0c5743046963a1e834a1cdcf85c7ac80fb99715715922d6bb2e5a7eb01771af2` |
| Stage requests | 42 |
| Retry requests | 0 |
| Stage body bytes | 145,647,360 |
| Cumulative requests | 322 |
| Cumulative body bytes | 239,616,206 |

The stage body total consists of exactly 144,766,080 bytes in twelve native
image/inverse-variance files and 881,280 bytes in eighteen bundled PSF FITS
responses. It remains below both the prospective stage reservation and the
global body cap.

## Integrity findings

- All 12 fixed-native bodies and all 18 PSF responses are present under
  `RAW_IMMUTABLE` with mode `0444`.
- All 30 body SHA-256 values match both the acquisition ledger and their
  corresponding sealed checkpoints.
- All 30 requests that returned bodies and all 12 identity HEAD requests have
  status 200 in the ledger; acquisition order matches the frozen candidate.
- The twelve native descriptors retain `float32`, `3600×3600` and zero decoded
  science pixels.
- The eighteen PSF descriptors retain three `float32` planes in `g,r,z` order
  with the frozen south `63×63/63×63/63×63` and north
  `31×31/31×31/63×63` shapes.
- The 18 bundled responses map exactly to 54 unique observational identities.
- `STAGING` contains no files; its empty directory structure is retained.
- The location manifest retains its frozen checksum. No cutout extraction,
  preprocessing operation or morphology inspection occurred.

This review establishes local preservation and integrity of the authorized
observational products. It does not authorize extraction, preprocessing,
morphological inspection or the scientific OC-3 phase.

**FIXED NATIVE + PSF ACQUISITION AUDIT VALIDATED.**

**OC-3 MORPHOLOGICAL SCIENTIFIC PHASE REMAINS NOT STARTED.**
