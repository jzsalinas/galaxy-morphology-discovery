# OC-3 resource contract and auxiliary acquisition — implementation report

**Stage:** `OC3-RESOURCE-CONTRACT-AUXILIARY-ACQUISITION-001`

**Implementation state:** validated offline; no real probe or bulk acquisition executed.

**Implementation aggregate:** `c244ec07f6c681180dc1a9d03368bc1dbacdd93e4984241d3b64489aee39fff2`

## Implemented boundary

- `OC3_DR9_COADD_RESOURCE_CONTRACT_001.md` freezes the documentary facts, evidence-state model, inventory, budgets, probe and future acquisition order.
- `oc3/schemas/oc3_dr9_coadd_resource_contract_001.schema.json` is the closed 26-resource contract schema.
- `oc3/schemas/oc3_dr9_coadd_resource_probe_binding_001.schema.json` is the closed input schema for a separately reviewed literal probe binding.
- `oc3/oc3_resource_contract.py` provides `--help`, `--dry-run`, `--probe-resource-contract` and the separately authorized future `--acquire-auxiliary` mode.
- `oc3/oc3lib/resource_contract.py` implements exact inventory construction, canonical sealing, literal-path validation, bounded FITS-header probing, cumulative accounting, fail-closed acquisition state, immutable publication and native-grid validation.
- `oc3/tests/test_resource_contract.py` adds 27 focused synthetic cases. One older physical-probe tripwire was narrowed to permit only the already authoritative `OC3_DEVELOPMENT_BRICKS.csv` checkpoint in `oc3/INPUTS`; all other production directories remain required empty.

The code reads the two identities only from the frozen CSV. Neither this report nor the source hard-codes or changes them. No location selector, source-catalog path, morphology input, image-pixel inspection or PSF acquisition was added.

## Resolved documentary contract

The implementation records the supplied official DR9 filename families; TAN WCS; nominal 3600×3600 shape and 0.262 arcsec/pixel scale; image logical primary-HDU role; optical MASKBITS logical HDU 1 with WISE HDUs 2/3 excluded; NEXP contributing-exposure semantics; and PSFSIZE weighted-average FWHM semantics. The first batch is exactly 14 auxiliary identities in the frozen south/north and product/band order. Exactly 12 image/invvar identities are prepared as future-only entries.

Every property is represented as `DOCUMENTED`, `OBSERVED_BY_BOUNDED_PROBE` or `UNRESOLVED`. Logical HDU role remains distinct from the physical tiled-compression HDU. The future post-GET validator requires exact length, bound HDU, 2D shape, supported dtype, TAN WCS, documented units when available and common seven-map native grid per brick; it does not resample.

## Still unresolved

Local evidence does not establish an `<AAA>` production rule for the two selected bricks. Therefore all directory components and literal URLs remain null in the generated contract, and acquisition fails before transport construction. Exact content lengths/`max_bytes`, physical compressed-HDU layout, NEXP/PSFSIZE logical image HDUs, dtypes and some units also require exact provider evidence. INVVAR representation remains future-only and outside this probe.

The implementation deliberately cannot create the missing URL binding. Before a real probe, `oc3/INPUTS/OC3_RESOURCE_CONTRACT_PROBE_BINDING_001.json` must be independently reviewed, canonical, sealed, match the 14 frozen identities exactly and cite nonempty evidence for each region's exact directory component. This is the only missing non-network precondition; guessing a brick-prefix rule is prohibited.

## Probe and acquisition behavior

The bounded probe runs all 14 HEAD checks first. It then obtains only aligned 2880-byte FITS header blocks. Each range must return an exact 206 and exact `Content-Range`; at most six blocks are allowed per resource. The code has no science-array decoder in this path. Maximum cost is **98 requests** and **241,920 response bytes**, concurrency one, no retries and zero science pixels. Any response started or body observed is recorded in a compact failure terminal even if the probe stops.

The future auxiliary route remains blocked by separate authorization. Its implemented order is 14 HEAD checks, a sealed joint resource plan, 14 GETs in frozen order, immutable publication, then FITS/HDU/grid validation. The plan must satisfy cumulative body/request limits, 4 GiB incremental disk, 8 GiB I/O, 2 GiB RAM, local free space, per-resource caps and concurrency one before the first GET. The ledger imports the cumulative counters, reserves before GET, keeps failures and retries charged, allows at most two retries per exact identity, and requires a new sealed `resume=true` authorization after a partial state. It never redownloads a published identity. The bulk success sentinel is `AUXILIARY_PRODUCTS_ACQUIRED`; it has not been produced.

## Offline verification

- Focused suite: **27/27 PASS**, 0 failures, 0 skips. Log `/tmp/oc3_resource_contract_focused.log`, SHA-256 `a6406ed2c2198cb567adc5897a3694ced82d93a5006316e0c5e227d9d30566ce`.
- Full regression: **694/694 PASS**, 0 failures, 0 skips, `real_network_requests=0`. Log `/tmp/oc3_resource_contract_full_regression.log`, SHA-256 `46d8745e36b3daed27c355963de91f96201e6efcf2bdee294f84065dbd3c2856`.
- Production dry-run: exact 14 auxiliary rows, 12 future rows, 14 rows with unresolved fields, zero network and `bulk_authorized=false`. `/tmp/oc3_resource_contract_dry_run.json`, SHA-256 `2d2209ddf3be228220735a1f3b7c910cf276180bf2283f336b91a9db67e9c9db`.
- `py_compile` and `git diff --check` pass.

No real socket, provider request, download, pixel decode, location selection or morphology operation occurred during implementation or validation.

## Exact next bounded command

After the literal binding above has been independently reviewed and sealed, run from `/home/jzsalinas/Documents/galaxy-morphology-discovery`:

```bash
./oc3/.venv/bin/python oc3/oc3_resource_contract.py --probe-resource-contract --execute-network --project /home/jzsalinas/Documents/galaxy-morphology-discovery --bricks /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/INPUTS/OC3_DEVELOPMENT_BRICKS.csv --probe-binding /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/INPUTS/OC3_RESOURCE_CONTRACT_PROBE_BINDING_001.json --audit-directory /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/resource_contract/OC3-RESOURCE-CONTRACT-PROBE-001 --log /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/resource_contract/OC3-RESOURCE-CONTRACT-PROBE-001/RESOURCE_CONTRACT_PROBE_RUN.log --max-requests 98 --max-bytes 241920
```

Expected runtime is under five minutes if the provider responds normally; network throttling can extend wall time. Incremental disk use is below 1 MiB. Inputs are the frozen CSV and sealed literal binding. Successful outputs are `RESOURCE_CONTRACT_RESOLVED.json`, `RESOURCE_CONTRACT_PROBE_EVIDENCE.json`, `RESOURCE_CONTRACT_PROBE_TERMINAL.json` and the compact log under the audit directory. The success sentinel is:

```json
{"stage_id":"OC3-RESOURCE-CONTRACT-PROBE-001","state":"RESOURCE_CONTRACT_PROBE_RESOLVED"}
```

If the command returns nonzero or terminal state `RESOURCE_CONTRACT_PROBE_PARTIALLY_RESOLVED`, preserve the directory and do not rerun it. Review the recorded request/byte counts and create a separate prospective retry authorization or corrected binding. The command never starts the 14 bulk GETs.

Because the required literal binding does not yet exist, the command is documented but is not currently executable in a compliant way. The next permitted network action remains only this bounded probe after that offline binding review. Auxiliary bulk acquisition and location selection remain unauthorized.

**OC-3 MORPHOLOGICAL SCIENTIFIC PHASE REMAINS NOT STARTED.**
