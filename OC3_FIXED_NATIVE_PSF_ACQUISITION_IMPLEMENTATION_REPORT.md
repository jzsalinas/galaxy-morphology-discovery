# OC-3 fixed native products and PSF acquisition implementation report

## Outcome

The prospective `OC3-FIXED-NATIVE-PSF-ACQUISITION-001` orchestration is
implemented and validated offline. The current machine candidate is ready for
human review. No final authorization artifact was created, no network transport
was constructed and no acquisition directory exists.

The implementation imports the resolved location, fixed-native and coadd-PSF
contracts by exact SHA-256. It accepts exactly twelve native resources and
eighteen bundled PSF responses representing 54 observational identities.

## Frozen candidate

- Candidate path:
  `oc3/INPUTS/OC3_FIXED_NATIVE_PSF_ACQUISITION_CANDIDATE_001.json`.
- Candidate file SHA-256:
  `961a763e5732b38c5193764a785a3799b0a74e9e42de111fa1de08c8d4cc2951`.
- Candidate internal seal:
  `59ccb5ed3dedfa0ac9ea1b52a48a83fadda2240108d9a8bbbdf2966a44bda662`.
- Implementation aggregate:
  `18d72c7843d376f7cc70b74a5906df5ec6d2dd046859e30b9fda735c9ba91661`.
- Implementation module SHA-256:
  `f664f836ab26f2db85ed5b0848f6fed9a387164f41779ab86e3aea3984974442`.
- Entry point SHA-256:
  `00ed3728d06e4079ef63b072f9a769c2c07fe2a4200cdb0c07b13e1c7e0b639a`.

The candidate records `final_authorization_present=false`. The expected final
authorization path does not exist. The embedded acquisition argv cannot pass
the production loader without a future authorization that binds this exact
candidate file hash.

## Acquisition behavior

The initial run performs all twelve native HEAD checks first. Content length
and ETag must equal the fixed resolved contract. It then downloads native bodies
in frozen region/product/band order and PSF bodies in frozen slot/point order.
No alternative URL, reprobe or substitution exists. A closed transport router
keeps static native requests separate from dynamic PSF requests; the latter use
the audited PSF transport and preserve the complete literal query containing
`ra`, `dec` and `layer`.

Every response is charged immediately, written exclusively to `STAGING`,
hashed and validated before an atomic move to read-only `RAW_IMMUTABLE`.
Checkpoints preserve body SHA-256, response status and available
Content-Length, ETag and Last-Modified metadata. PSF responses remain bundled;
band identities refer to the same exact response.

Native validation compares the observed FITS header structure, logical and
physical HDUs, compression mapping, dtype, shape and exact WCS facts from the
header probe. PSF validation requires three `float32` image planes in `g,r,z`
order and preserves the observed region-specific shapes. It performs no array
normalization, shape homogenization, cutout extraction or morphology operation.

A partial attempt retains its ledger, completed immutable bodies, checkpoints,
hashes, staging and counters. The initial path refuses an existing audit
directory. The six-request retry pool can be used only by a future separately
specified and authorized resume; it is unavailable to the initial run.

## Frozen resources and budgets

- Fixed native resources: 12; exact body bytes: 144,766,080.
- PSF transport responses: 18; observational identities: 54.
- PSF total reservation: 56,623,104 bytes; 3,145,728 bytes per response.
- Primary body reservation: 201,389,184 bytes.
- Primary requests: 42 = 12 native HEAD + 12 native GET + 18 PSF GET.
- Retry pool: 6; stage request cap: 48; concurrency: one.
- Cumulative start: 280 requests and 93,968,846 bytes.
- Global body cap: 1,610,612,736 bytes.

## Offline verification

- Focused synthetic tests: 20/20 passed; zero skips; log SHA-256
  `e88da676b67276923958c29f684a96a21062ad599a222b38fc022e525cb1e9a1`.
- Full offline regression: 828/828 passed; zero failures; zero skips;
  `real_network_requests=0`; log SHA-256
  `40f006f979d791c6c7caac4bf6460b58602c9842290f23afed437dd80e754e9b`.
- Production candidate validation:
  `FIXED_NATIVE_PSF_ACQUISITION_CANDIDATE_VALID_FOR_HUMAN_REVIEW`, zero
  network; output SHA-256
  `2296af3b398487afe5810077c08c81c4ae56f76c576e6fae6a357f4843723785`.

No real provider request, acquisition, cutout, preprocessing or morphology
inspection occurred.

**READY FOR FIXED NATIVE + PSF ACQUISITION HUMAN REVIEW.**

**OC-3 MORPHOLOGICAL SCIENTIFIC PHASE REMAINS NOT STARTED.**
