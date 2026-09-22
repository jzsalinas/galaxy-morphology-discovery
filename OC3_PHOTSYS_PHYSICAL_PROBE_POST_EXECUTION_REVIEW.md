# OC3 PHOTSYS physical probe — post-execution review

## Disposition

The historical attempt `OC3-GALAXY-ELIGIBILITY-PHOTSYS-AUTHORITY-PHYSICAL-PROBE-001` remains a successful, immutable observation with terminal state `PHOTSYS_AUTHORITY_RESOURCE_CONTRACT_RESOLVED`. Its tree seal is `6a4c0d06794b86a929efd68ec58908f17c8a2289c5e59fd881271c03eb93a27c`. No historical receipt, header block, checkpoint, accounting record, or terminal artifact was modified or regenerated.

An offline review found one derived-label defect. The probe emitted HDU types `[null,"PRIMARY"]`; the immutable FITS cards show `SIMPLE = true` for HDU 0 and `XTENSION = "BINTABLE"` for HDU 1. The corrected derived value is therefore `["PRIMARY","BINTABLE"]`.

This correction is `OFFLINE_DERIVED_CORRECTION_FROM_IMMUTABLE_PROBE_EVIDENCE`. It is a review layer over the original observation, not a replacement observation.

## Root cause and correction

`probe_hdu_inventory` derived the label before appending the current HDU but tested `len(inventory) == 1` to identify the primary HDU. At that point the primary has index 0 and the first extension has index 1, so the labels shifted. The code now captures `hdu_index = len(inventory)` and classifies `PRIMARY` exactly when `hdu_index == 0`; extensions retain their `XTENSION` value.

Header parsing, HDU traversal, data-size arithmetic, TFORM parsing, column offsets, projection construction, request accounting, and immutable evidence handling were not changed.

## Immutable evidence reused

The reconstruction used only these four existing 2,880-byte blocks:

| Block | SHA-256 |
|---|---|
| `header-block-001.bin` | `4586d713b5ebe02a13ae9d9750127132caae738da52a99b73263a090c09cb363` |
| `header-block-002.bin` | `fb6c0767bd8f8847686261494c41dc25410dee7b1c8156c92068cb36b5ecc286` |
| `header-block-003.bin` | `d4c2af44fb675e8395dbb90f3c65f192c7d1928581ed2807f386d5356c356e95` |
| `header-block-004.bin` | `6d24357908d3e08afbf9cea100a6740bea9490d5bb27a9b3c4bfd27b57d9393f` |

The offline correction made zero network requests, requested zero table-data bytes, and decoded zero table-cell values.

## Impact assessment

All scientific and physical-contract findings remain valid:

| Finding | Review |
|---|---|
| HTTP identity and representation | unchanged |
| HDU count | unchanged |
| `row_count = 662174` | unchanged |
| `row_width = 79` | unchanged |
| exhaustive 13-column schema | unchanged |
| `BRICKNAME`: offset 0, `8A`, bytes 0–7 | unchanged |
| `BRICKID`: offset 8, `J`, bytes 8–11 | unchanged |
| `PHOTSYS`: offset 70, `1A`, byte 70 | unchanged |
| `AREA_PER_BRICK`: offset 71, `D`, structural presence only | unchanged |
| first table-data byte 11,520 | unchanged |
| maximum requested byte 11,519 | unchanged |
| header-only boundary | unchanged |
| selective spans 0–11 and 70 | unchanged |
| no whole-row fallback | unchanged |
| firewall counters | unchanged at zero |

The historical network record remains one HEAD plus four 2,880-byte Range responses: five requests and 11,520 body bytes. It contains zero full FITS GETs and zero table-cell decodes.

## Reviewed physical contract

The authoritative review layer is `oc3/INPUTS/OC3_PHOTSYS_AUTHORITY_REVIEWED_PHYSICAL_CONTRACT_001.json`. It binds the exact literal URL, HTTP identity, 52,323,840-byte file size, complete corrected HDU inventory, exhaustive column schema, selective projection, header-only boundary, original tree seal, correction hash, and corrected implementation aggregate.

The reviewed state is `PHOTSYS_AUTHORITY_PHYSICAL_CONTRACT_REVIEWED`.

## Stage-B boundary

`oc3/INPUTS/OC3_PHOTSYS_FULL_ACQUISITION_CANDIDATE_001.json` is prospective and pending human review. No final authorization exists and no acquisition ran. The candidate preserves this boundary explicitly:

`FULL_FILE_BYTE_PRESERVATION != ALL_COLUMN_VALUE_OBSERVATION`

A future complete-body acquisition may preserve the official bytes locally. Only a later separately reviewed offline validator may decode `BRICKNAME`, `BRICKID`, and `PHOTSYS`. All other column values, including `AREA_PER_BRICK`, remain forbidden. Panel V2 remains `NOT_STARTED`; P1 remains `BLOCKED`; the OC-3 morphological-discovery phase remains not started.
