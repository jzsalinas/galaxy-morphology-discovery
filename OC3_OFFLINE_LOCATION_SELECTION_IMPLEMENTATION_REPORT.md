# OC-3 offline location selection — implementation report

**Stage:** `OC3-OFFLINE-LOCATION-SELECTION-001`

**Implementation state:** validated offline; real location selection not yet executed

**Implementation aggregate:** `7ac5535fc6b3d918fc3de28b4d0423edc3f8e18814e4b51c4db8a0a8c5ebfabf`

## Files changed

- `.gitignore`
- `oc3/README.md`
- `oc3/oc3_location_selection.py`
- `oc3/oc3lib/location_selection.py`
- `oc3/schemas/oc3_locations_001.schema.json`
- `oc3/tests/test_location_selection.py`
- `oc3/oc3lib/resource_contract.py`
- `oc3/tests/test_physical_contract_probe.py`
- `OC3_OFFLINE_LOCATION_SELECTION_IMPLEMENTATION_REPORT.md`

The resource-contract adjustment freezes the already executed auxiliary candidate's historical implementation aggregate instead of recomputing it from later unrelated Python stages. The input tripwire now recognizes the already reviewed and committed auxiliary authorization. Neither change modifies the candidate, authorization, resolved contract, acquisition evidence or acquired arrays.

## Closed observation boundary

The production selector can open exactly 14 immutable resources: NEXP g/r/z, PSFSIZE g/r/z and optical MASKBITS for each frozen development brick. The guard rejects every other product before constructing its path or calling `fits.open`. The CLI imports no socket, HTTP, URL or request transport and exposes only mandatory offline dry-run and execution modes.

The selector validates the acquisition terminal, resource plan, ledger, resource identities, sizes, checksums and read-only publication before array decoding. It then validates native 3600×3600 shape, product dtype, nonnegative integer NEXP/MASKBITS, PSFSIZE units, DR9/brick/generation headers, TAN WCS, lack of unsupported distortion and seven-map grid agreement. No resampling, padding, interpolation or image/invvar access exists in this path.

## Offline verification

- Focused location-selection suite: **32/32 PASS**, zero failures, zero skips. Log `/tmp/oc3_location_selection_focused.log`, SHA-256 `75dd23c8b3eb8f473bfd700531a1e60f026fd706685af8859cb1ca759a1fdda9`.
- Historical-stage compatibility checks: **3/3 PASS**. Log `/tmp/oc3_location_selection_historical_compatibility.log`, SHA-256 `757d13f37a4777396f1549a5e105b98c4007dced1fb8e53dd64e8c7f901745b6`.
- Complete offline regression: **764/764 PASS**, zero failures, zero skips, `real_network_requests=0`. Log `/tmp/oc3_location_selection_full_regression.log`, SHA-256 `a6d708dd3f76e67c41ef9db97e9ecba3ce5074401862277731f3b6a760ec8e63`.
- Production dry-run: `READY_FOR_OFFLINE_LOCATION_SELECTION`, 14 resources, two bricks, zero arrays decoded, zero requests and zero body bytes.
- `py_compile` and `git diff --check` pass.

The synthetic coverage fixes the 64-pixel reticle, complete 129×129 geometry, edge rejection, WCS/BRICK_PRIMARY and RA-wrap handling, every slot rule, MASKBITS optical-bit policy, N2 fallback, N3 statistic/status, ordering, no replacement, deterministic hashes, permutation invariance, tie breaks, missing-slot failure, unauthorized-product tripwire, closed canonical output, leakage boundary and success/failure terminal behavior.

## Exact real offline command after implementation commit

Run once from `/home/jzsalinas/Documents/galaxy-morphology-discovery`:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/.venv/bin/python \
  /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/oc3_location_selection.py \
  --execute --offline \
  --project /home/jzsalinas/Documents/galaxy-morphology-discovery
```

Expected success terminal: `LOCATION_SELECTION_VALIDATED`. The command performs no network operation and refuses a second materialization.

**REAL OFFLINE LOCATION SELECTION NOT YET EXECUTED.**

**IMAGE/INVVAR ACQUISITION REMAINS NOT AUTHORIZED.**

**OC-3 MORPHOLOGICAL SCIENTIFIC PHASE REMAINS NOT STARTED.**
