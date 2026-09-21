# OC-3 fixed native-resource contract — implementation report

**Implementation aggregate:** `2b99a3007d7581609ba16aa9e1fbd7cd23d545fbe512fb6af962bedd94d164d1`

**State:** implementation and synthetic validation complete; real header probe not executed.

## Result

- Frozen selection binding: `LOCATION_SELECTION_VALIDATED`, selection SHA-256 `2e6f2cb070a363e9e3dbdb1f25670590c33500a293bb926d8ff94657a2ff8860`.
- Image/invvar contract: exactly twelve literal DR9 resources. Directory identity reuses the observed auxiliary contract. Content-Length, ETag, physical HDU, compression mapping and dtype remain unresolved; invvar logical HDU also remains unresolved.
- PSF contract: eighteen immutable native-WCS points and 54 point-band observational identities. Official viewer source establishes one prospective multi-band FITS response per point, so the transport plan contains eighteen responses. Output units and the deployed source revision remain unresolved.
- PSF semantics probe: not required for response bundling and not prepared. No successful PSF response or product was acquired.
- Bulk acquisition: unauthorized and absent.

## Implementation boundary

- `oc3/oc3lib/fixed_native_contract.py`
- `oc3/oc3_fixed_native_resource_contract.py`
- `oc3/tests/test_fixed_native_contract.py`
- three closed JSON schemas under `oc3/schemas/`
- three canonical contracts/bindings under `oc3/INPUTS/`
- `OC3_FIXED_NATIVE_RESOURCE_CONTRACT_001.md`
- `OC3_PSF_RESOURCE_CONTRACT_001.md`
- `.gitignore`, `oc3/README.md` and the historical production-directory tripwire

The probe accepts only the twelve literal URLs in the sealed binding. It performs all HEAD requests first and then aligned FITS header ranges. It persists every HEAD and completed-resource checkpoint immediately, records immutable aggregate history, and preserves partial evidence on failure. The FITS parser handles `NAXIS=0` as a zero-byte data span, stops in the block containing `END`, skips any intervening span arithmetically and never requests the first image-data block.

## Verification

- Focused suite: **25/25 PASS**, zero skips. Log `/tmp/oc3_fixed_native_contract_focused.log`, SHA-256 `c24508789093fbbe4e71b87898cb9e31e8306c332b3eefbfa2ba5b238fb71cb0`.
- Full offline regression: **789/789 PASS**, zero failures, zero skips, `real_network_requests=0`. Log `/tmp/oc3_fixed_native_contract_full_regression.log`, SHA-256 `9cc05e8f8911cb209a9754ee17960f922edbaba3f7c06fac07f701ece9ec3f26`.
- Production dry-run: `READY_FOR_HUMAN_BOUNDED_HEADER_PROBE`; twelve resources; zero network; zero science pixel values; zero bulk GET.
- A synthetic test exposed and corrected an invalid one-block skip for a primary FITS HDU with `NAXIS=0` before the binding was sealed.

The implementation, dry-run and tests made zero real network requests. Separately, documentary browser navigation attempted to resolve the official URL page's example coadd-PSF link and timed out before returning a body. It used no frozen location, produced no artifact and is not treated as provider-contract evidence. Therefore the task-wide research activity is not represented as zero network total; the sealed executable stage remains unexecuted with zero requests.

Artifact SHA-256 values:

- fixed native contract: `9e35cab014f0cb61ef8afb065e6ea0fe42c2448074a3504b8752233c8628f834`
- PSF contract: `1720e8ae9b77f4d5b7de9b7d28a2dbf3d1785c7005e2507e9a9ba21467dbc9f7`
- probe binding: `16980484be31fcfdde5bcbc5fa8f697f86e9dc7ec6001bee7f9962fda1dee2e9`

## Exact human probe command

Run from `/home/jzsalinas/Documents/galaxy-morphology-discovery`:

```bash
/home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/.venv/bin/python \
  /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/oc3_fixed_native_resource_contract.py \
  --execute-probe --execute-network \
  --project /home/jzsalinas/Documents/galaxy-morphology-discovery \
  --binding /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/INPUTS/OC3_FIXED_NATIVE_RESOURCE_PROBE_BINDING_001.json \
  --audit-directory /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/fixed_native_resource_contract/OC3-FIXED-NATIVE-RESOURCE-PROBE-001 \
  --log /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/fixed_native_resource_contract/OC3-FIXED-NATIVE-RESOURCE-PROBE-001/PROBE_RUN.log \
  --max-new-requests 204 \
  --max-range-requests 192 \
  --max-range-bytes 552960 \
  --max-header-blocks 16
```

Expected maximum is 12 HEAD requests plus 192 aligned header Range requests, 552,960 charged Range-body bytes, concurrency one and zero retries. Expected wall time is below five minutes when the provider responds normally. Durable evidence and the compact log are written only below the audit directory shown above.

Success terminal: `FIXED_NATIVE_RESOURCE_CONTRACT_RESOLVED` with twelve resolved resources and `science_pixel_values_observed=0`.

Failure terminal: `FIXED_NATIVE_RESOURCE_CONTRACT_PARTIALLY_RESOLVED`. Do not delete, overwrite or rerun the same audit directory. Preserve all checkpoints and prepare a separately reviewed continuation only after inspecting the failure; counters never reset.

**REAL HEADER PROBE NOT EXECUTED.**

**IMAGE/INVVAR BULK ACQUISITION REMAINS NOT AUTHORIZED.**

**PSF BULK ACQUISITION REMAINS NOT AUTHORIZED.**

**FROZEN LOCATIONS REMAIN UNCHANGED.**

**OC-3 MORPHOLOGICAL SCIENTIFIC PHASE REMAINS NOT STARTED.**
