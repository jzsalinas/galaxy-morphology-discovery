# OC-3 coadd-PSF resource contract 001

## Scope and frozen authority

This prospective contract prepares only `OC3-COADD-PSF-CONTRACT-PROBE-001`.
The six locations remain bound to selection SHA-256
`2e6f2cb070a363e9e3dbdb1f25670590c33500a293bb926d8ff94657a2ff8860` and to
`oc3/TECHNICAL_INDEX/OC3_LOCATIONS.json` SHA-256
`33d593638c074a3ff59d32d3e4c38558e8912377ea15818ca5072087007c97d1`.
The resolved image/invvar contract is imported at cumulative counters 278 requests and
93,870,926 body bytes; it is not probed or acquired again.

## Offline provider review

| Fact | State | Frozen value |
|---|---|---|
| Endpoint | `DOCUMENTED` | `/viewer/coadd-psf/` |
| Demonstrated query | `DOCUMENTED` | `ra`, `dec`, `layer` |
| Required query in public source | `SOURCE_VERIFIED` | `ra`, `dec`, `layer` |
| Optional public-source query | `SOURCE_VERIFIED` | `bands`; deliberately omitted from this probe |
| Region layers | `DOCUMENTED` / source corroborated | `ls-dr9-south`, `ls-dr9-north` |
| Successful content type | `SOURCE_VERIFIED` | `image/fits` |
| Multi-band structure | `SOURCE_VERIFIED` | one image HDU per returned band; explicit band headers |
| Source normalization path | `SOURCE_VERIFIED` | normalized exposure PSFs, combined per band using median inverse-variance weights |
| Missing coverage | `SOURCE_VERIFIED` | bands without accumulated weight are omitted; no returned bands yields a textual response |
| Deployed response schema | `UNRESOLVED` | requires bounded observation in both regions |
| Output units | `UNRESOLVED` | accepted only if explicitly present in returned headers |
| Exact deployed source revision | `UNRESOLVED` | public source does not attest deployment commit |

The documentary authorities are the official Legacy Surveys viewer URL documentation and the
public `legacysurvey/imagine` route and `coadd_psf` implementation already frozen in
`OC3_PSF_RESOURCE_CONTRACT_001.md`. Source behavior is not promoted to observed deployment
behavior.

## Frozen identities

`oc3/TECHNICAL_INDEX/OC3_PSF_IDENTITIES.json` contains exactly 54 observational identities:
six immutable slots × three fixed native positions × `g,r,z`. Each row binds slot, region,
brick, point, native coordinates, WCS-derived sky coordinates and band. The 18 spatial points
remain P0 `(0,0)`, P1 `(-32,-32)` and P2 `(+32,+32)` relative to each selected center.

Observational identity remains independent of HTTP transport. The offline source model implies
18 prospective multi-band responses, but that count remains prospective until the deployed
service is observed.

## Minimal bounded probe

The sealed binding selects deterministically:

- south: S1/P0 with `ls-dr9-south`;
- north: N1/P0 with `ls-dr9-north`.

Both literal URLs contain only `ra`, `dec` and `layer`; no band query is added. The stage permits
exactly two GET requests, concurrency one, zero retries, 1 MiB per response and 2 MiB total.
The transport rejects redirects and non-identity content encoding. Each response identity and
regional FITS structure is checkpointed before continuing.

The parser records response headers, exact byte count and hash, HDU layout, shapes, dtypes,
band labels/order and explicit unit headers. It skips array byte regions by offsets and never
converts PSF array bytes to values. It has no image/invvar URL or morphology access path.

The real evidence must select exactly one mapping:

- `A_ONE_RESPONSE_BUNDLES_G_R_Z`: 18 future responses for 54 identities;
- `B_ONE_RESPONSE_REPRESENTS_ONE_BAND`: 54 future responses;
- `C_ANOTHER_EXPLICITLY_OBSERVED_MAPPING`: region-specific mapping and derived count.

Different north/south structures are preserved separately. A malformed or unlabeled response,
unknown representation, cap breach or missing regional result produces a partial terminal and
does not erase a completed regional checkpoint.

The probe is not executed by this preparation task. Its binding is a technical constraint, not
bulk-acquisition authorization.

**FIXED IMAGE/INVVAR CONTRACT REMAINS RESOLVED.**

**IMAGE/INVVAR BULK ACQUISITION REMAINS NOT AUTHORIZED.**

**PSF BULK ACQUISITION REMAINS NOT AUTHORIZED.**

**LOCATIONS REMAIN IMMUTABLE.**

**OC-3 MORPHOLOGICAL SCIENTIFIC PHASE REMAINS NOT STARTED.**
