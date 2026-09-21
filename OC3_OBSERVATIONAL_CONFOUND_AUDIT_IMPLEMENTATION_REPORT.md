# OC-3 observational confound audit implementation report

**Stage:** `OC3-OBSERVATIONAL-CONFOUND-AUDIT-001`

**Specification SHA-256:** `8c997a2eb4a58c50eb72604ab7d1c9a8ece61863ad2af96640bc7569580091c3`

**Implementation aggregate:** `6dbeef37006b342de10a0f7dbd58bdfe69958e63941e0f54eb086c29638c7126`

## Implementation boundary

The implementation adds `oc3/oc3lib/observational_confound_audit.py`, the
offline CLI `oc3/oc3_observational_confound_audit.py`, and the synthetic suite
`oc3/tests/test_observational_confound_audit.py`. The OC-3 README and ignore
rules identify the six-file runtime publication without versioning generated
audit evidence.

The CLI exposes only `--validate-inputs` and `--audit`. There is no network,
display, rendering, selection, crop-writing or learned-representation mode.
Input validation binds the frozen specification, extraction manifest and seal,
terminal, locations, 78 crop artifacts, 18 PSF bodies and their hashes before
an array can be opened.

## Tier ordering

`ArrayAccessGate` classifies every crop access from its frozen manifest product.
It counts exactly 60 Tier-A crop reads and refuses IMAGE while its internal
Tier-A completion sentinel is false. The sentinel can be set only after crop
metrics, 18-response/54-plane PSF metrics and geometry have completed. It then
allows exactly 18 IMAGE reads. Attempts to read Tier A afterward, IMAGE before
the sentinel, an unknown product or a structurally changed array fail closed.

The implementation rechecks every input hash after calculation and before
publication. Outputs are first created under `STAGING`, checked against the
closed six-file inventory, made read-only and promoted as a directory. A
pre-existing stage or promotion target refuses a second execution.

## Metric families

Tier A implements the frozen NEXP level histograms and four-neighbour
transitions; INVVAR finite/sign/quantile/dispersion fields and positive-only
diagnostic sigma; overlapping raw MASKBITS groups and unknown positions;
PSFSIZE summaries and exact N3 V reproduction; raw PSF representation metrics,
hashes and P0/P1/P2 descriptors; and WCS/BRICK_PRIMARY membership plus
five-point Jacobians. Tier B implements only the frozen IMAGE signal-sanity
counts, extrema, quantiles, median and IQR, all labeled
`SCENE_MIXED_OBSERVATION`.

The observer feature matrix contains Tier-A columns only. Contrasts are the
five frozen left-minus-right comparisons. The interpretation-state function
uses the frozen precedence and exact nonconstant witnesses without an observed
effect-size threshold.

## PSF boundary and tripwires

PSF bodies are read exactly once and mapped to exactly 54 native planes. Raw
sum uses `math.fsum`; peak ties use row-major order; plane hashes bind exact
dtype, shape and C-order bytes. No stored PSF is rewritten. Every identity is
assigned `PHYSICAL_PSF_SHAPE_METRICS_DEFERRED`; no normalized width, moment,
ellipticity or physical shape is implemented.

Source and output tripwires exclude network and visualization stacks and reject
prohibited analytical output fields. Required technical counters freeze zero
display, zero plots, zero preprocessing, zero morphology operations and zero
network requests. The exact output inventory excludes images, arrays and plots.

## Validation before real audit

- Focused synthetic suite: **24 passed, 0 failed, 0 skipped**.
- Complete offline regression: **869 passed, 0 failed, 0 skipped**.
- Regression network counter: **`real_network_requests=0`**.
- Frozen-input validation: `OBSERVER_AUDIT_INPUTS_VALIDATED`, 6 slots, 78 crop
  artifacts and 18 PSF mappings, with zero crop-array opens and zero PSF-plane
  decodes.
- Header-only smoke check: two manifest-bound NEXP headers, zero compressed
  data loads; all thirteen WCS/bounds records agree within each slot.
- Syntax and diff checks: passed.

The real audit has not been executed while creating this report. No production
crop array or PSF plane has been opened for analysis, no output metric has been
calculated from production values, and no network request has occurred.
