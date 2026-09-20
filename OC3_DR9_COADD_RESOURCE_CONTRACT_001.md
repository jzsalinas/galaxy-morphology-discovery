# OC-3 DR9 coadd resource contract 001

**Stage:** `OC3-RESOURCE-CONTRACT-AUXILIARY-ACQUISITION-001`

**Authority:** `OC3_BOUNDED_AUXILIARY_PIXEL_PILOT_SPEC.md`, SHA-256 `dca2e5f8fe7d0783554116e042c02bcddde7bb083e05a31939fc2fd2bc9151ae`

**Frozen brick binding:** `oc3/INPUTS/OC3_DEVELOPMENT_BRICKS.csv`, SHA-256 `147c0942a5340ed18eec23a610f8afd5721390fad09c1da7ed01593deb40fab6`

**Status:** prospective contract infrastructure implemented; provider path and physical-layout evidence remain unresolved.

## Scope and evidence states

This contract covers only the two already frozen development bricks. It neither displays their identities in this document nor changes their selection. It defines 26 prospective native DR9 coadd resources: the first batch contains 14 auxiliary maps, while 12 image/invvar identities remain future-only. No location, source, galaxy, pixel value, PSF response, resampling, preprocessing or morphological decision belongs to this stage.

Every resource property has one of three states:

- `DOCUMENTED`: supported by the frozen specification or the supplied official DR9 file-model facts;
- `OBSERVED_BY_BOUNDED_PROBE`: observed for the exact literal resource through the bounded protocol below;
- `UNRESOLVED`: unavailable from current evidence and prohibited from silent completion.

The closed machine schema is `oc3/schemas/oc3_dr9_coadd_resource_contract_001.schema.json`. Its top-level and resource objects reject additional fields. Canonical sealing is SHA-256 over compact, sorted-key UTF-8 JSON after removing only the top-level `sealed` field. A seal binds content; it does not authorize network access or certify provider truth.

## Frozen documented properties

For both `south` and `north`, the documented filename families are:

```text
legacysurvey-<brick>-image-<filter>.fits.fz
legacysurvey-<brick>-invvar-<filter>.fits.fz
legacysurvey-<brick>-nexp-<filter>.fits.fz
legacysurvey-<brick>-psfsize-<filter>.fits.fz
legacysurvey-<brick>-maskbits.fits.fz
```

The contract marks the following as `DOCUMENTED`: DR9/coadd identity; g/r/z applicability; nominal native shape 3600×3600; TAN WCS; nominal pixel scale 0.262 arcsec/pixel; the image logical primary-HDU role; optical MASKBITS in logical HDU 1; exclusion of logical MASKBITS HDU 2/3 because they are WISE masks; NEXP as contributing-exposure count per pixel; and PSFSIZE as weighted-average PSF FWHM in arcsec per pixel. The image units are recorded as nanomaggies per pixel under the existing DR9 documentary evidence. Dtypes are not promoted without exact headers.

The `.fits.fz` suffix is a representation constraint. A documented logical HDU is kept distinct from its physical FITS tiled-compression layout. The physical image HDU and compression mapping remain `UNRESOLVED` until exact header evidence exists.

## Unresolved properties and safe URL rule

Current local documentary evidence does not prove a productive `<AAA>` rule for the selected bricks. Consequently the initial manifest has `directory_component=null` and `literal_url=null` for all 26 resources. The implementation never derives `<AAA>` from a brick prefix, never searches directory listings, never crawls the survey and never tries alternatives.

The initial auxiliary resources also retain `UNRESOLVED` for exact content length/`max_bytes`, physical compressed-HDU mapping, and the logical image HDU of NEXP and PSFSIZE. INVVAR stays unresolved and outside this acquisition batch. A real probe requires a separate canonical binding whose 14 literal URLs, exact directory components, per-resource caps and nonempty independent `<AAA>` evidence are human reviewed. The binding schema is `oc3/schemas/oc3_dr9_coadd_resource_probe_binding_001.schema.json`.

## Exact inventories

The first batch is ordered and closed as follows for `south`, then identically for `north`:

1. NEXP g, r, z;
2. PSFSIZE g, r, z;
3. optical MASKBITS.

This is exactly 14 identities. The future-only inventory contains image g/r/z and invvar g/r/z for each region, exactly 12 identities. These 12 are serialized by the contract machinery but cannot enter the auxiliary probe or acquisition.

## Bounded resource-contract probe

`--probe-resource-contract` accepts only a sealed literal binding matching the frozen CSV and exact 14-resource order. It performs all 14 HEAD requests before any Range request. HEAD must return the exact URL, status 200, identity encoding and a positive Content-Length no greater than the reviewed cap.

For FITS structure, the probe requests aligned 2880-byte header blocks only. Each request must return status 206, the exact `Content-Range`, the exact block length, the same literal URL and identity encoding. The parser follows FITS header/data offsets but never requests a data block, imports Astropy or decodes a science array. At most six header blocks per resource are allowed. Failure to reach `END`, a nonexact Range response, unexpected shape or any cap breach stops the probe without fallback.

Prospective maximum:

| Item | Bound |
|---|---:|
| HEAD requests | 14 |
| Header-block requests | 84 |
| Total requests | 98 |
| Response-body bytes | 241,920 |
| Concurrency | 1 |
| Retries | 0 |
| Science pixels decoded | 0 |

Successful evidence upgrades only the exact resources observed. It records content length, optional ETag, physical image HDU, compression mapping and header-block count. It does not generalize to other bricks, releases or product families.

## Cumulative budget

The ledger begins with 89,461,646 body bytes and 8 requests already consumed. Global maxima stay 1,610,612,736 bytes and 200 requests, leaving 1,521,151,090 bytes and 192 requests before this stage. No restart resets these numbers. The later plan reserves 56,623,104 bytes for the 54 prospective PSF responses.

Before any auxiliary GET, the resolved contract must bind all 14 exact lengths and the orchestrator must produce a sealed joint plan. Pending bodies plus the PSF reservation must fit the remaining body budget; required HEAD/GET operations must fit the request budget; staging plus immutable publication must fit both local free space and the 4 GiB incremental-disk cap; projected local I/O must fit 8 GiB; and the largest bounded response must fit 2 GiB RAM. A failed or partial request counts. Runtime caps may be tightened, never increased.

## Future auxiliary acquisition

The implemented, currently unauthorized `--acquire-auxiliary` route enforces this order:

```text
14 identity/HEAD checks
→ joint byte/request plan
→ south NEXP g,r,z
→ south PSFSIZE g,r,z
→ south MASKBITS
→ north NEXP g,r,z
→ north PSFSIZE g,r,z
→ north MASKBITS
→ immutable publication
→ FITS/HDU/grid validation
→ terminal
```

Each GET must match its literal URL and exact HEAD Content-Length, remain below its resource cap and use identity encoding. All bodies first enter staging. Publication occurs only after all 14 bodies finish, uses read-only files under `RAW_IMMUTABLE`, and never overwrites a published identity. Post-publication validation checks the bound physical image HDU, a 2D 3600×3600 native array, product-compatible dtype, TAN WCS and units when documented. All seven maps in each brick must share the same WCS vector within the frozen bookkeeping tolerance `1e-10`; there is no reprojection or resampling.

The acquisition authorization is a separate sealed object with scope `AUXILIARY_14_ONLY` and the exact resolved-contract hash. A partial state cannot run again under the original authorization: `resume=true` must be separately sealed. Already published valid resources are not downloaded again. Terminal success is `AUXILIARY_PRODUCTS_ACQUIRED`; failure or partial state is fail-closed and does not authorize location selection.

## Current decision and stop

The resource contract is not completely resolved. Exact `<AAA>` evidence/literal URLs, exact lengths and physical/logical HDU facts require the bounded probe. Bulk auxiliary acquisition remains blocked. The exact probe invocation is documented in the implementation report, but it is executable only after the closed binding file has been independently reviewed and sealed. No compliant command can synthesize that missing evidence.

**OC-3 MORPHOLOGICAL SCIENTIFIC PHASE REMAINS NOT STARTED.**
