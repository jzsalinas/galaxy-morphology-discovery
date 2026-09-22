# OC3 PHOTSYS Authority Probe — Final Authorization Review

## Authorization decision

| Field | Bound value |
|---|---|
| Authorized by | José Salinas |
| Decision | `AUTHORIZED` |
| Authorized at UTC | `2026-09-22T13:08:02.278798+00:00` |
| Stage | `OC3-GALAXY-ELIGIBILITY-PHOTSYS-AUTHORITY-PROBE-001` |
| Scope | `PHOTSYS_BRICK_AUTHORITY_ONLY` |
| Candidate scope | `MINIMUM_DOCUMENTARY_BINDING_ONLY` |
| Implementation aggregate | `ea621f93fef58ab059c7af62737efd02f8a356696d258ec107bb6d92b4abdb92` |

## Exact bindings

| Artifact | Path | SHA-256 |
|---|---|---|
| Candidate | `oc3/INPUTS/OC3_PHOTSYS_AUTHORITY_RESOURCE_CANDIDATE.json` | `ce44b89346b1f281f587ddf654dab562b753f09dd140c0791ce475af401e0fc0` |
| Final authorization | `oc3/OC3_PHOTSYS_AUTHORITY_PROBE_FINAL_AUTHORIZATION_001.json` | `9481d0611decce2758be1f53fa6c781f14a3fa48b191443a5651770a3f8415a8` |
| Command argv | Canonical command vector in the candidate | `2f6a1fffd7e0ac6a9b559dfc57705e59a39a65bca964487798991433a4d60403` |

The final authorization uses the exact seven-field closed schema accepted by the production validator. Human identity, timestamp, candidate path, implementation binding, candidate scope, resources, and caps are recorded here because adding them as keys to the authorization JSON would make that artifact invalid under the frozen validator.

## Authorized resources and caps

The allowlist contains exactly:

```text
https://www.legacysurvey.org/dr9/files/
https://www.legacysurvey.org/dr9/catalogs/
```

The bound limits are:

```text
requests including redirects <= 4
response body bytes <= 1,048,576
per-document body bytes <= 524,288
redirects per request <= 1
concurrency = 1
automatic retries = 0
data HEAD requests = 0
data Range requests = 0
full FITS GETs = 0
table cell values decoded = 0
```

The identity `survey-bricks-dr9-randoms-0.48.0.fits` may be discovered only through an explicit link in an allowlisted documentary body. It is not an authorized request resource in this attempt.

## Offline validation and transport boundary

The focused production validation requires exact candidate bytes, authorization bytes, command vector, implementation aggregate, documentary resources, limits, negative capabilities, and absence of wider transport authority. The preflight invokes the production entry point with an injected boundary sentinel after authorization validation and before construction of a real transport.

Observed offline result:

```text
authorization_valid = true
documentary_resource_count = 2
FITS_HEAD_authorized = false
FITS_Range_authorized = false
network_requests = 0
network_body_bytes = 0
preflight = READY_AT_REAL_TRANSPORT_BOUNDARY
```

## Human execution handoff

From `/home/jzsalinas/Documents/galaxy-morphology-discovery`, the exact authorized command is:

```bash
oc3/.venv/bin/python oc3/oc3_galaxy_eligibility_photsys_authority_probe.py --probe-resource-contract --candidate oc3/INPUTS/OC3_PHOTSYS_AUTHORITY_RESOURCE_CANDIDATE.json --authorization oc3/OC3_PHOTSYS_AUTHORITY_PROBE_FINAL_AUTHORIZATION_001.json --output-directory oc3/photsys_authority_probe/OC3-GALAXY-ELIGIBILITY-PHOTSYS-AUTHORITY-PROBE-001
```

The expected bounded terminal is `PHOTSYS_AUTHORITY_RESOURCE_CONTRACT_INCONCLUSIVE` when the documentary retrieval completes without probing the FITS resource. A failure or partial attempt must not be automatically rerun or resumed. Existing output at the bound directory blocks replay. Any follow-up requires review of the durable evidence and a new prospective authorization.

No network request, documentary retrieval, FITS request, panel execution, Tractor/SDSS/Gaia/DESI access, or full regression was performed while creating this authorization.

```text
PANEL_V1 = FAILED_CLOSED
PANEL_V2 = NOT_STARTED
P1 = BLOCKED
OC3_MORPHOLOGICAL_DISCOVERY_PHASE = NOT_STARTED
```

**PHOTSYS DOCUMENTARY PROBE FINAL AUTHORIZATION READY.**
