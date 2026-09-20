# OC-3 metadata-bootstrap rights review 001

## Status and scope

This document is the local reviewed-rights governance decision for the bounded `METADATA_BOOTSTRAP_ONLY` protocol. It is based exclusively on evidence already retained in the repository. No live source was consulted and no legal opinion is asserted.

The question reviewed is whether the retained evidence supports the narrow project decision to retrieve the four already-frozen public DR9 resources, preserve their exact bytes locally in the bounded research workspace, and perform local technical/scientific validation while prohibiting redistribution of FITS and row-derived products pending a separate explicit review.

The answer is yes within that exact scope. The decision is:

```text
rights_review_outcome = METADATA_BOOTSTRAP_RIGHTS_REVIEW_001_PASS
local_scientific_acquisition = ALLOWED_FOR_THIS_PROTOCOL
local_preservation = ALLOWED_FOR_THIS_PROTOCOL
redistribution = false
FITS_OR_DERIVED_REDISTRIBUTION = DISABLED_UNRESOLVED
```

`ALLOWED_FOR_THIS_PROTOCOL` is a research-governance decision for local use of publicly released/accessibly published data. It is not a broad legal-license determination.

This review is not execution authorization. It does not authorize network access, create an authorization candidate, create final human authorization, create an attempt, or start OC-3.

## Repository and authority verification

The review began from a clean repository with no configured remote.

| Item | Verified value |
|---|---|
| Branch | `main` |
| Commit before this task | `bee1460daab76a854a00b0056faf224373950b8e` |
| Gate-activation commit | `60f937b145f8eb29be4df9352032a092b42a7ddd` |
| Baseline commit | `8e87225dfb895438e5bb73bbadc6ef35dbf6ed1e` |
| Baseline tag | `oc3-pre-metadata-bootstrap-001`, peeled to the baseline commit |
| Execution Plan 001 | SHA-256 `0e246d5fce5d71c2aa109cba913f1eb9bd397259e492e279870c6d4ccf163b20` |
| Plan post-activation review | SHA-256 `a232a58f91705215d5322945460549b7b53789bf630503d505552f8f5fb460a0` |
| Gate-activation implementation report | SHA-256 `2e34939341358ba99512b711b2e1e1f87af1b8a1095ac146a9e7737072c9ddc6` |
| Gate-activation replay receipt | SHA-256 `e696907938fabd20b907010708b06d130cd65077b7f24a2187bf2948790620dd` |
| Base metadata-bootstrap specification | SHA-256 `e42ecef50f2a4dd01dbd2d1c8acbcb24e48f30d4692d3bae19c73011fa265dbd` |
| Clarification 001 | SHA-256 `97c42b873b2700ea2155d9107217e296db441d98a24159efe173732dd4bcca4d` |
| Current implementation aggregate | `d9922ad04a19a9e87b73e85439239a591aae80b1d9528d9e75310b0e88efbec7` |
| Environment fingerprint | `b49e26767922123113707a13434821d6bf1d7711f28a2b9de7e5ce46d64e3bdf` |
| Canonical replay receipt | 562 total, 562 passed, 0 failed, 0 skipped, `real_network_requests=0` |
| Probe 001 | exact and immutable 13/13 |

Before rights creation, the rights path, first-run authorization path, and `oc3/metadata_bootstrap/` attempt root were absent. There was no ledger, RAW, STAGING, provider-row observation, or network operation.

## Implemented closed rights schema

The production implementation was inspected locally and was not changed. Its exact top-level key set is:

```text
FITS_OR_DERIVED_REDISTRIBUTION
attempt_id
base_spec_sha256
binding_type
canonicalization
clarification_sha256
environment_fingerprint
execution_plan_sha256
implementation_aggregate
local_preservation
local_scientific_acquisition
redistribution
resources
reviewed
reviewed_evidence
schema_version
scope
synthetic_only
```

The fixed schema and serialization identities are:

```text
schema_version = 1
canonicalization = CANONICAL_JSON_SORTED_KEYS_COMPACT_UTF8_LF_V1
binding_type = METADATA_BOOTSTRAP_RIGHTS_BINDING
```

The exact primitive values required by the validator are strings for identifiers, hashes and governance enums; integer `1` for `schema_version`; strict JSON booleans for `redistribution`, `reviewed`, and `synthetic_only`; an ordered resource array; and a nonempty reviewed-evidence array. The production binding uses `reviewed=true`, `synthetic_only=false`, and `redistribution=false`.

Every `reviewed_evidence` item is a closed object containing exactly:

```text
path: nonempty project-relative string
sha256: 64-character lowercase hexadecimal string
```

Validation resolves each evidence path beneath the canonical project directory, requires an existing regular file, and recomputes the exact SHA-256. Paths outside the project, nonexistent files, malformed hashes, empty evidence, duplicate JSON keys, unknown top-level keys, and noncanonical bytes are rejected.

Every resource item is supplied by the production `resource_binding_values()` function and contains exactly `accept_encoding`, `allowed_methods`, `compression`, `expected_etag`, `expected_last_modified`, `expected_length`, `expected_provider_full_file_sha256`, `provider_checksum_status`, `range_allowed`, `redirects_allowed`, `role`, and `url`, with the exact values frozen below.

The file parser accepts at most 1,048,576 bytes, decodes UTF-8 JSON with duplicate-key rejection, requires a top-level object, and requires the file bytes to equal the production canonical JSON encoding plus one trailing LF. The canonical encoding uses sorted keys and compact separators. Validation then checks the exact top-level key set; exact binding/schema/canonicalization, attempt, scope and governance values; plan/spec/clarification/implementation/environment bindings; exact resources; `reviewed=true`; strict boolean `synthetic_only`; production-only `synthetic_only=false`; nonempty evidence; and every evidence path/hash.

## Reviewed local evidence

The following evidence is retained locally and is bound by exact path and SHA-256. This review itself is externally hashed before the binding is serialized and is included as reviewed evidence without creating a self-reference.

| Evidence | SHA-256 | Role and limitation |
|---|---|---|
| `OC3_METADATA_BOOTSTRAP_EXECUTION_PLAN_001_POST_ACTIVATION_REVIEW.md` | `a232a58f91705215d5322945460549b7b53789bf630503d505552f8f5fb460a0` | Binds the immutable plan to the activated implementation and current Git/replay state; not authorization. |
| `OC3_METADATA_BOOTSTRAP_GATE_ACTIVATION_IMPLEMENTATION_REPORT.md` | `2e34939341358ba99512b711b2e1e1f87af1b8a1095ac146a9e7737072c9ddc6` | Describes the fail-closed execution-capability boundary and exact current implementation aggregate. |
| `oc3/environment_setup/METADATA_BOOTSTRAP_GATE_ACTIVATION_REPLAY_RECEIPT.json` | `e696907938fabd20b907010708b06d130cd65077b7f24a2187bf2948790620dd` | Binds 562/562 offline replay, zero real network, zero real rows, no attempt, no rights and no authorization at replay time. |
| `OC3_DR9_BOOTSTRAP_DOCUMENTARY_EVIDENCE.md` | `07f2e20994d52783a84a176113b3f8cdf3d3ba4a0f0e0cf4fc33868e5277769b` | Preserves the human-reviewed official DR9 repository/access facts, exact resource identities, scientific-use acknowledgment context, and the narrow local-use/no-redistribution project gate. It is documentary evidence, not live HTTP observation or a universal license. |
| `OC3_EXECUTION_PREFLIGHT_SPEC.md` | `6d5617ad5cc2b552d4a036a340077f4a727d06be4217e10d0f5b7408c9f6c28e` | Separates public access, scientific use, and image reproduction; permits proposing bounded local acquisition/cache while retaining FITS/derived redistribution as disabled/unresolved. |
| `e_oc1/evidence/RIGHTS-DR5.html` | `adb1c5b41ad8aee7544a23d1b499b317d97c82222b4f69f65efa3ad13f6a9a1c` | Exact local snapshot of the official general Legacy Surveys acknowledgment and image-usage page. Its filename reflects the earlier evidence task; its acknowledgment language is general, while its image license remains limited to named rendered layers. It is not direct proof of DR9 FITS redistribution rights. |
| `E_OC1_EVIDENCE_REGISTER.json` | `a00b09f82f1f5b740666e9bcece77299b64fa240ac3df22790c5f7b242572952` | Records source authority, URL, retrieval, exact body hash, applicability and unsupported rights claims for the acknowledgment snapshot. |
| `E_OC1_SUFFICIENCY_REVIEW.md` | `2f1f9fc99cebd04e3dbda56a3b5fbff30125707e8323892e6a9b72989c6786c4` | Explicitly records that scientific-use acknowledgment and rendered-image terms do not resolve FITS/coadd or row-derived redistribution. |
| `e_oc1/evidence/retrieval.json` | `4331de4ab4bfbd2dd20cc5a58d59b082254798cbe14aafc0f01e7782be496c1f` | Preserves the exact official requested/final acknowledgment URL, UTC retrieval, HTTP 200, 21,688-byte body, headers and local body hash. |
| `e_oc1/evidence/integrity_verification.json` | `989b0f30c51e8652a05d8e54b5c2d9c719dec58bef1d6e484ac81e95b273a572` | Records the local integrity verification of the earlier evidence set. Its scope and limits remain explicit. |

The current rights review document is an additional reviewed-evidence item. Its exact SHA-256 is computed from the finished bytes and stored only in the separate rights-binding JSON.

## A. Documented fact

1. The retained DR9 documentary record identifies the NERSC Cosmology Data Repository as exposing DESI Imaging Legacy Surveys datasets as publicly available, with official DR9 root, north, and south web-access paths and individual/bulk download mechanisms.
2. The retained DR9 record identifies the three summary tables and the south patch list as official provider resources already frozen by the metadata-bootstrap protocol. Their runtime representation and integrity constraints are governed separately by the immutable plan and implementation.
3. The locally preserved official Legacy Surveys acknowledgment page supplies acknowledgment expectations for scientific publications using Legacy Surveys data.
4. That page separately discusses rendered Sky Viewer layers and states image terms for specifically named Legacy Surveys-produced layers. It also warns that hosted surveys have distinct terms and that users must ensure compliance for the relevant layer.
5. The earlier evidence register and sufficiency review explicitly leave FITS/coadd-derived and row-level redistribution unresolved. Public access and scientific acknowledgment are not represented as unrestricted redistribution permission.

The local acknowledgment snapshot is general evidence about scientific-use expectations and the limited rendered-image statement. It is not used as DR5-specific proof of DR9 product semantics or as a license for the four DR9 FITS resources.

## B. Protocol governance decision

For this one bounded research protocol, the evidence supports retrieval and local immutable preservation of the four exact publicly exposed provider resources for private/local technical and scientific validation. Therefore:

```text
local_scientific_acquisition = ALLOWED_FOR_THIS_PROTOCOL
local_preservation = ALLOWED_FOR_THIS_PROTOCOL
redistribution = false
FITS_OR_DERIVED_REDISTRIBUTION = DISABLED_UNRESOLVED
```

This decision applies only to the four resources and the `OC3-METADATA-BOOTSTRAP-001` technical bootstrap scope. It does not authorize another DR9 product, another release, images, catalogs, bulk acquisition, publication, redistribution, selection, or OC-3 execution. Local preservation means exact bytes inside the bounded research workspace as required for reproducibility and integrity validation.

The decision is project governance for research use of publicly released/accessibly published data. It does not assert a universal copyright or database-license conclusion. Any eventual scientific publication using the data must follow the applicable acknowledgment expectations.

## C. Unresolved rights questions

1. No broad license for redistribution of the four original FITS/table resources is asserted.
2. No permission for redistribution of derived rows, joined tables, row-level metadata, or other FITS-derived products is inferred.
3. The rendered-image terms are not generalized to FITS table bytes, scientific tables, auxiliary products, or row-derived data.
4. Public web access is not treated as equivalent to unlimited redistribution rights.
5. Future publication or redistribution requires a separate explicit review of the exact products and intended use, where applicable.
6. This decision makes no claim about future image products, third-party catalogs, hosted layers from other surveys, or any resource outside the four exact bindings.

## Image-license distinction

Any Creative Commons attribution language documented for rendered Legacy Surveys/Sky Viewer image layers must not be generalized by this binding into a universal FITS-table or row-product redistribution license. The image-layer statement and scientific acknowledgment provide useful but distinct evidence. They do not resolve rights for redistributing original table bytes or derived row products.

Consequently, `redistribution=false` and `FITS_OR_DERIVED_REDISTRIBUTION=DISABLED_UNRESOLVED` are mandatory and fail-closed.

## Exact bounded resources

The governance decision applies to exactly these four resources and no others:

| Role | Exact URL | Expected bytes | Integrity state |
|---|---|---:|---|
| `ROOT_SUMMARY` | `https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/survey-bricks.fits.gz` | 13,147,987 | Provider SHA-256 expected and frozen by the implementation |
| `NORTH_SUMMARY` | `https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/north/survey-bricks-dr9-north.fits.gz` | 20,882,100 | Provider SHA-256 expected and frozen by the implementation |
| `SOUTH_SUMMARY` | `https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/south/survey-bricks-dr9-south.fits.gz` | 55,399,879 | Provider SHA-256 expected and frozen by the implementation |
| `SOUTH_PATCH_LIST` | `https://www.legacysurvey.org/files/dr9-south-patched-bricks.fits` | 31,680 | Provider checksum absent; exact ETag, Last-Modified and acquisition-bound digest protocol retained |

There is no mirror, fallback, Range request, redirect permission, inferred permission for other DR9 products, or release substitution.

## Artifact and command state

After successful creation and production validation of the binding:

```text
/home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/METADATA_BOOTSTRAP_RIGHTS_BINDING_001.json = FROZEN
/home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/METADATA_BOOTSTRAP_FIRST_RUN_AUTHORIZATION_001.json = PROSPECTIVE_PENDING_ARTIFACT
command_hash = COMMAND_HASH_PENDING_AUTHORIZATION_FREEZE
```

The rights path is frozen by this task. The authorization path is not frozen and no command hash is created, because not all command-vector literals and governing artifact identities are yet legitimately frozen.

## Current boundary

Rights review and rights binding resolve only the rights component of `PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS`. Execution remains blocked because no first-run authorization artifact exists. The next permissible task is creation of a distinct first-run authorization candidate with `authorized=false`.

```text
metadata_bootstrap=NOT_STARTED
production_decode_enabled=false
redistribution=false
real_network_requests=0
real_provider_row_values=0
real_attempt_created=false
authorization_created=false
```

Probe 001 remains immutable 13/13.

THIS RIGHTS REVIEW IS NOT EXECUTION AUTHORIZATION.

THIS RIGHTS BINDING IS NOT EXECUTION AUTHORIZATION.

NEXT STEP: FIRST-RUN AUTHORIZATION CANDIDATE WITH `authorized=false`.

DO NOT RE-RUN OR RESUME PROBE 001.

OC-3 REMAINS NOT STARTED.
