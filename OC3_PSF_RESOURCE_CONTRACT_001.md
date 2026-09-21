# OC-3 coadd-PSF resource contract 001

**Frozen input:** the six locations sealed by selection SHA-256 `2e6f2cb070a363e9e3dbdb1f25670590c33500a293bb926d8ff94657a2ff8860`.

**Current state:** provider response structure is `SOURCE_VERIFIED`; actual availability, response bytes, output units and the exact deployed source version remain unobserved. No bounded coadd-PSF contract probe or product acquisition has been executed.

## Official and source evidence

The [official viewer URL page](https://www.legacysurvey.org/viewer/urls) documents a DR9 “PSF model for coadd” link. The official viewer repository binds `/coadd-psf/` to `views.coadd_psf` in [`map/urls.py`](https://github.com/legacysurvey/imagine/blob/main/map/urls.py#L215). The implementation in [`map/views.py`](https://github.com/legacysurvey/imagine/blob/main/map/views.py#L7164-L7444) establishes the following source behavior:

- `ra`, `dec` and `layer` are required;
- `bands` is optional and defaults to the layer’s available bands;
- requested bands are restricted to bands available in the layer;
- one successful response can contain several bands;
- each returned band is written as one FITS image HDU;
- the first header records `BANDS` and `BANDi`; each image header records `BAND`;
- successful output uses Content-Type `image/fits`;
- per-exposure PSFs are requested with `normalizePsf=True`, combined separately by band with median inverse-variance weights and divided by the summed weight;
- bands with no accumulated weight are omitted; no returned bands produce a textual no-CCDs response.

This source review does not attest which exact commit is deployed by the public service. It also does not label the units of the returned PSF pixels. Those fields remain `UNRESOLVED`; normalization is recorded as source behavior rather than a unit claim.

The public documentation and source paths were reviewed on 2026-09-21. Because the reviewed `main` URLs are mutable and did not attest the deployed revision, this date and the explicit `deployment_version=UNRESOLVED` state bound the evidential scope.

During documentary navigation, the research browser attempted to resolve the official URL page's example coadd-PSF link. That request timed out before returning a body. It did not use a frozen location, did not yield FITS or semantic evidence and is excluded from this contract. It is nevertheless recorded as one non-pipeline network attempt rather than represented as zero total network activity.

## Frozen observational identities

The machine contract is `oc3/INPUTS/OC3_PSF_RESOURCE_CONTRACT_001.json`. For each slot S1, S2, S3, N1, N2 and N3, it derives from the already validated native WCS:

- P0: center `(0,0)`;
- P1: offset `(-32,-32)` native pixels;
- P2: offset `(+32,+32)` native pixels.

This produces exactly eighteen spatial points and 54 observational identities (`slot × point × g/r/z`). Points are not moved and locations are not altered. South points bind to `ls-dr9-south`; north points bind to `ls-dr9-north`.

## Identity versus transport

The source-verified multi-band behavior permits one prospective response per spatial point when `bands` is omitted. Therefore the contract has:

- 54 observational point-band identities;
- 18 prospective HTTP responses;
- three observational identities linked to each transport identity.

Omitting the optional `bands` query is deliberate. It avoids asserting a band-specific transport that the provider source does not require. A future response must still be checked for its explicit returned-band headers. A missing band becomes `NOT_AVAILABLE` for its frozen identity; it does not move the point, create another request implicitly or collapse the identity set.

## Probe decision

No separate PSF semantics probe is prepared in this stage because the official endpoint documentation plus its public source close the response bundling structure needed for planning. This does not authorize the eighteen calls. A later acquisition authorization must bind literal URLs, caps, response validation, failure states and the unresolved deployment/units risk.

**PSF BULK ACQUISITION REMAINS NOT AUTHORIZED.**

**FROZEN LOCATIONS REMAIN UNCHANGED.**

**OC-3 MORPHOLOGICAL SCIENTIFIC PHASE REMAINS NOT STARTED.**
