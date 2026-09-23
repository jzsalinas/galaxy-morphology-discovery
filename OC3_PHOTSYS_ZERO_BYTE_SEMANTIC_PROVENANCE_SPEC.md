# OC3 PHOTSYS zero-byte semantic/provenance investigation specification

## 1. Status and scope

This is the frozen prospective specification for:

- stage: `OC3-GALAXY-ELIGIBILITY-PHOTSYS-ZERO-BYTE-SEMANTIC-PROVENANCE-001`;
- scope: `PHOTSYS_ZERO_BYTE_SEMANTIC_PROVENANCE_ONLY`;
- evidence mode: documentary, source-code, and synthetic-library evidence only;
- real astronomical data observation: prohibited;
- resolver construction: prohibited;
- Panel V2 and P1: prohibited.

This document defines a future investigation. It does not perform that investigation, authorize network access, interpret `RAW_PHOTSYS_0x00`, amend PHOTSYS V1, create a resolver, select Panel V2, or unblock P1.

Implementation or execution requires a separately reviewed prospective stage. If any future operation needs network access, source acquisition, or a synthetic executable demonstration, its literal resources, caps, command, candidate, and authorization must be frozen separately before execution.

## 2. Governing scientific question

The sole scientific question is:

> Does the observed raw PHOTSYS byte `0x00` have sufficient independent provenance to be interpreted as the documented “outside of the footprint” category for `survey-bricks-dr9-randoms-0.48.0.fits`?

The investigation must keep five layers separate:

1. FITS representation semantics;
2. Legacy Survey documentation semantics;
3. `desitarget` 0.48.0 producer behavior;
4. observed DR9 file behavior;
5. inference linking those layers.

Agreement in one layer must not silently substitute for evidence in another.

## 3. Immutable observed fact

The completed historical stage is bound as follows:

| Binding | Frozen value |
|---|---|
| Stage | `OC3-GALAXY-ELIGIBILITY-PHOTSYS-BYTE-HISTOGRAM-001` |
| Terminal | `PHOTSYS_RAW_BYTE_HISTOGRAM_OBSERVED` |
| Histogram artifact | `oc3/photsys_byte_histogram/OC3-GALAXY-ELIGIBILITY-PHOTSYS-BYTE-HISTOGRAM-001/OC3_PHOTSYS_RAW_BYTE_HISTOGRAM_001.json` |
| Histogram artifact SHA-256 | `010e2c4a7465d0b08bc3c6df1e8e52a4eafa0c497a7d030038f34cc377e54510` |
| Histogram payload SHA-256 | `3ebe3094819363b152e21c9ebcd47144f665300548a878a84108b9b5e66e1e47` |
| Histogram canonical seal | `edabd5a4cc3c0eecd4003871c93f7eb32480a571f5fb4f57678bad849cc1a681` |
| Terminal artifact SHA-256 | `bb9e7a6d05560deaeba4aa11803213cc46530768071a1d942736607f280216ed` |
| V1 consistency artifact SHA-256 | `af1134cd8f57a33675ff1a5059cb90e973eaefc54a0a169acfab5b05c0a29d80` |
| Rows and histogram total | `662174` |
| Row-linked output | absent |

The only nonzero observed bins are:

| Raw unsigned byte index | Count |
|---:|---:|
| `0x00` | `330208` |
| `0x4e` | `82897` |
| `0x53` | `249069` |

All frozen V1 count checks passed. These counts are immutable observations and must not be regenerated in this investigation.

## 4. Immutable historical V1 boundary

The historical review is `OC3_PHOTSYS_SELECTIVE_VALUE_VALIDATION_POST_EXECUTION_REVIEW.md`, SHA-256 `6b689ba5aff89131d09506ce0827c2aabc59fad3935d3740db3eee019de9d772`.

Historical V1 remains closed with terminal `PHOTSYS_SELECTIVE_INVALID_PHOTSYS_FAILED`. The historical terminal name is preserved verbatim. The `330208` observations are described in current work only as `PHOTSYS_OUTSIDE_FROZEN_V1_DOMAIN`.

No finding in the prospective investigation may rewrite the V1 specification, result, terminal, candidate, authorization, execution evidence, or post-execution review. Any later V2 rule requires a separate prospective amendment after this investigation is formally closed.

## 5. Controlled terminology

The following terms are distinct until the evidence gate in section 15 passes:

- `RAW_PHOTSYS_0x00`: the observed unsigned raw byte identity at the reviewed PHOTSYS position;
- `DOCUMENTED_OUTSIDE_FOOTPRINT`: the category described by official Legacy Survey documentation;
- `FITS_NULL_STRING`: a representation-level state, if established by an authoritative FITS source.

The investigation must not use these terms as synonyms. In particular:

```text
RAW_PHOTSYS_0x00 != DOCUMENTED_OUTSIDE_FOOTPRINT   until proven
FITS_NULL_STRING != DOCUMENTED_OUTSIDE_FOOTPRINT  without producer provenance
FITS_NULL_STRING != ASCII_SPACE
```

The string `ASCII_SPACE` denotes byte `0x20` only. The present document assigns no textual, provider, astronomical, missing-value, footprint, padding, sentinel, or corruption meaning to byte `0x00`.

## 6. Evidence stream A — FITS standard

### 6.1 Required authority

The future investigation must bind an authoritative FITS standard or official NASA/HEASARC source that governs BINTABLE character fields with `TFORM='A'`. It must record:

- document title and edition/version;
- issuing organization;
- literal source URL;
- final URL after any permitted redirect;
- retrieval timestamp in UTC;
- complete acquired-document SHA-256 when legally and technically practical;
- exact section, page, paragraph, or stable anchor;
- a short relevant excerpt or faithful paraphrase;
- whether the source is normative or explanatory.

### 6.2 Questions to resolve

The source must establish, contradict, or leave unresolved each proposition:

1. whether byte `0x00` as the first character of a BINTABLE `A` field denotes an ASCII NULL or undefined string;
2. whether byte `0x20` denotes ASCII space;
3. whether a FITS representation rule assigns any survey-footprint meaning.

The expected logical separation is that a representation-level null finding, even if supported, supplies no astronomical category by itself.

### 6.3 Acceptance boundary

This stream is `SUPPORTED` only when an authoritative source explicitly covers the relevant field type and byte position. General C-string behavior, an implementation-specific display, a contemporary library convenience conversion, or current folklore is insufficient.

## 7. Evidence stream B — Legacy Survey documentation

### 7.1 Required official resource

The future investigation must bind the official DR9 Legacy Survey documentation for `survey-bricks-dr9-randoms-0.48.0.fits`. The captured evidence must preserve the documentation exactly as published, including any statement that PHOTSYS uses:

- `"N"` for north;
- `"S"` for south;
- `" "` for outside of the footprint.

The investigation must record the literal URL, final URL, UTC retrieval time, response metadata, acquired-body SHA-256, stable section or anchor, and relevant wording. If current documentation is not demonstrably the historical documentation associated with DR9 or `desitarget` 0.48.0, that temporal limitation must be explicit.

### 7.2 Non-rewrite rule

The documentation must not be normalized from space to byte `0x00`, or from byte `0x00` to space. A documented `0x20`-style space and an observed `0x00` are a physical/documentary mismatch unless independent provenance explains the serialization.

Official documentation alone can establish `DOCUMENTED_OUTSIDE_FOOTPRINT`; it cannot establish that observed `RAW_PHOTSYS_0x00` is that category.

## 8. Evidence stream C — exact `desitarget` 0.48.0 producer

### 8.1 Exact historical source binding

The authoritative producer investigation must use the exact `desitarget` `0.48.0` tag or release source. Current `main`, a later release, an unversioned installation, or behavior copied from another release is nonauthoritative for this question.

The future evidence must bind:

- repository and immutable clone/source URL;
- literal tag `0.48.0`;
- resolved commit SHA;
- signed-tag or release provenance when available;
- archive or source-tree SHA-256;
- relevant file paths;
- relevant blob hashes;
- exact line ranges in the frozen tree;
- dependency versions that materially control byte initialization or FITS serialization.

### 8.2 Required producer trace

The investigation must trace the full relevant pathway and determine:

1. PHOTSYS dtype, including exact byte width;
2. allocation and initialization behavior;
3. the condition and code location assigning `N`;
4. the condition and code location assigning `S`;
5. the value retained when neither assignment occurs;
6. the pathway that creates zero/outside/missing brick rows;
7. the code that writes the PHOTSYS field to FITS;
8. whether `survey-bricks-dr9-randoms-0.48.0.fits` is produced directly by that pathway;
9. if not direct, the exact separate aggregation, summary, or release script and its transformations;
10. whether any post-processing converts byte `0x00` to `0x20`, or the reverse.

A local or upstream file named plausibly is not enough. The investigation must connect functions and scripts to the named DR9 summary product through versioned provenance.

## 9. Synthetic zero-initialization subtest

A future synthetic-only demonstration may test the proposition:

```text
For dtype |S1, a NumPy structure created with np.zeros contains raw byte 0x00
before any N/S assignment.
```

The demonstration must:

- run in an isolated temporary directory;
- use a frozen NumPy version and record its version;
- construct only synthetic in-memory values;
- inspect no real FITS file, row, table span, BRICKNAME, BRICKID, ROOT value, coordinate, or regional record;
- emit only library/version information, dtype, raw synthetic byte, and pass/fail result;
- make zero network requests.

This subtest can support an initialization fact. It cannot prove that the exact DR9 producer used that allocation path, that a row was outside the footprint, or that the final file preserved the initial byte.

## 10. Critical outside-pathway gate

The semantic mapping gate requires affirmative evidence that the exact historical producer pathway for bricks categorized as `DOCUMENTED_OUTSIDE_FOOTPRINT` leaves PHOTSYS at raw byte `0x00` in the named released summary product.

Passing the gate requires all of the following:

1. the exact `desitarget` 0.48.0 allocation and assignment code is bound;
2. the exact outside-footprint branch or selection condition is bound;
3. that branch demonstrably leaves PHOTSYS at byte `0x00`, or an exact subsequent step assigns byte `0x00` to that category;
4. the FITS serialization path is bound and preserves that byte;
5. the generation or aggregation path to `survey-bricks-dr9-randoms-0.48.0.fits` is bound;
6. no material step that could rewrite PHOTSYS remains unresolved;
7. official documentation supplies the independent category semantics;
8. any discrepancy between documented space and physical byte `0x00` is explicitly explained by source provenance.

If the exact generation/aggregation pathway cannot be established, the investigation must conclude `PHOTSYS_0x00_SEMANTICS_INCONCLUSIVE`. Count agreement, zero initialization, FITS representation rules, or current code behavior cannot bridge that gap.

## 11. Count-coincidence boundary

The following observed equalities are supporting consistency evidence only:

```text
count(0x00) = 330208
count(0x4e) + count(0x53) + count(0x00) = 662174
```

They must not be used alone, or together with exhaustiveness, to establish `RAW_PHOTSYS_0x00 -> DOCUMENTED_OUTSIDE_FOOTPRINT`. The investigation may record whether independently proven producer semantics are consistent with the counts only after the producer mapping is established.

## 12. Optional independent structural check

An independent footprint cross-check is optional and is not authorized by this specification.

It may be proposed later only if an already frozen source can determine footprint membership without reading or using PHOTSYS. Candidate authorities may include previously preserved official north/south footprint evidence, but their admissibility and non-circularity must be reviewed before use.

Any future structural check must have its own specification and must precommit:

- the exact frozen authority and fields;
- proof that PHOTSYS is not an input;
- exact join keys and uniqueness rules;
- row-level privacy and output aggregation;
- allowed real-value reads;
- resource caps and terminal behavior;
- a separate execution candidate and authorization.

No row-level join, BRICKNAME read, BRICKID read, ROOT read, footprint computation, or structural check occurs in the present stage.

## 13. Evidence classes and claim matrix

Every future report must use exactly these evidence classes and statuses:

- classes: `Observed fact`, `Official documentation`, `FITS standard`, `Producer source`, `Independent footprint evidence`, `Inference`;
- statuses: `SUPPORTED`, `CONTRADICTED`, `UNRESOLVED`, `NOT_APPLICABLE`.

Initial state frozen by this specification:

| Evidence class | Claim | Initial status | Basis |
|---|---|---|---|
| Observed fact | The only nonzero raw bins are `0x00`, `0x4e`, and `0x53` with frozen counts | `SUPPORTED` | Sealed local histogram and terminal |
| Observed fact | V1 count cross-checks pass | `SUPPORTED` | Sealed `V1_CONSISTENCY.json` |
| Official documentation | The official DR9 resource defines north, south, and outside-footprint PHOTSYS categories with the stated encodings | `UNRESOLVED` | Exact official page/body has not been acquired and frozen by this stage |
| FITS standard | First-character `0x00` in a BINTABLE `A` field has `FITS_NULL_STRING` representation semantics | `UNRESOLVED` | Authoritative section has not been acquired and frozen by this stage |
| FITS standard | `0x20` is ASCII space and is distinct from `0x00` | `UNRESOLVED` | Authoritative section has not been acquired and frozen by this stage |
| Producer source | Exact `desitarget` 0.48.0 code zero-initializes PHOTSYS `|S1` before assignment | `UNRESOLVED` | Exact tag, commit, blobs, and pathway have not been bound |
| Producer source | Exact outside-footprint rows retain or receive byte `0x00` | `UNRESOLVED` | Critical outside-pathway gate has not been evaluated |
| Producer source | Exact generation path creates the named DR9 summary without a later PHOTSYS rewrite | `UNRESOLVED` | Release/aggregation provenance has not been bound |
| Independent footprint evidence | Non-circular footprint classification agrees with aggregate raw-byte behavior | `NOT_APPLICABLE` | Optional future check is neither specified nor authorized |
| Inference | `RAW_PHOTSYS_0x00` maps to `DOCUMENTED_OUTSIDE_FOOTPRINT` | `UNRESOLVED` | Required independent provenance is incomplete |

The matrix must not collapse documentary, representation, producer, observation, and inference claims into one status.

## 14. Documentary and source-research execution design

### 14.1 Allowed future resources

A separately authorized research execution may retrieve only:

1. official Legacy Survey documentation pages directly relevant to the named DR9 file;
2. an authoritative FITS standard or official NASA/HEASARC documentation;
3. the exact `desitarget` 0.48.0 tag/release metadata and source blobs;
4. official DESI/Legacy Survey provenance needed to connect that code to the named summary product;
5. peer-reviewed random-catalog documentation only when it directly resolves generation provenance.

No astronomical FITS data file, catalog, image, cutout, map, PSF, mask, Tractor table, or row-bearing product may be requested.

### 14.2 Required resource manifest

Before network construction, the future stage must freeze a literal resource manifest containing URL, host, purpose, evidence class, expected content type, byte cap, redirect rule, and whether an immutable revision is required. Broad crawling, search-result scraping, alternate mirrors, and silent URL substitution are prohibited.

Source-code evidence should use immutable tag/commit URLs where available. A web-rendered source page must be checked against the underlying immutable blob or archive hash.

### 14.3 Prospective caps

Any future research candidate must stay within these maxima unless a new prospective amendment is reviewed first:

- public documentary/source HTTP requests: `24`;
- cumulative response bodies: `32 MiB`;
- per-resource retries: `1` additional attempt for the exact identity;
- concurrency: `1`;
- astronomical-data GETs: `0`;
- real FITS table byte observations: `0`;
- BRICKNAME values observed: `0`;
- BRICKID values observed: `0`;
- ROOT values observed: `0`.

Search may identify candidate public sources during a future implementation review, but only literal resources admitted to the sealed manifest may become evidence.

## 15. Semantic decision gate

The future report must select exactly one outcome:

### 15.1 `PHOTSYS_0x00_OUTSIDE_SEMANTICS_PROVEN`

Allowed only when the official category semantics, exact producer pathway, exact named-product generation provenance, and physical serialization agree without a material unresolved contradiction. FITS representation evidence must be compatible but is not sufficient alone.

### 15.2 `PHOTSYS_0x00_REPRESENTATION_MISMATCH_BUT_OUTSIDE_MAPPING_SUPPORTED`

Allowed when official documentation specifies space for outside-footprint, the released product physically contains byte `0x00`, and exact producer plus product-generation provenance independently demonstrates that byte `0x00` represents the documented outside category. The report must retain the documentation/physical mismatch rather than normalizing it away.

### 15.3 `PHOTSYS_0x00_SEMANTICS_INCONCLUSIVE`

Required when the exact producer pathway, exact outside branch, FITS serialization, or named-product generation/aggregation pathway cannot be proven, and no direct contradiction determines the conflict outcome.

### 15.4 `PHOTSYS_DOCUMENTATION_PHYSICAL_CONFLICT_UNRESOLVED`

Required when authoritative evidence materially conflicts and the exact historical provenance cannot reconcile the conflict.

No outcome may be chosen in advance. A supported zero-initialization proposition plus matching counts is insufficient for either proven/supported mapping outcome.

If evidence integrity fails, the execution must stop without selecting a scientific outcome and require review; it must not weaken the gate or silently downgrade the affected claim.

## 16. Future report contract

The separately executed investigation must produce `OC3_PHOTSYS_ZERO_BYTE_SEMANTIC_PROVENANCE_REPORT.md` containing:

- all frozen input and source hashes;
- URLs and retrieval metadata;
- exact version/tag/commit and relevant source locations;
- the completed claim matrix;
- representation, documentation, producer, observation, and inference findings in separate sections;
- the zero-initialization result, if executed;
- the exact outside-pathway finding;
- the named-product generation-provenance finding;
- contradictions and unresolved assumptions;
- exactly one permitted semantic outcome;
- counters proving the no-data-observation boundary;
- a statement that V1 was not amended and no resolver was created.

Short source excerpts may be included only when necessary and within applicable quotation limits. Paraphrase is preferred. Every material finding must cite its exact evidence.

## 17. No-data-observation firewall

During specification, future implementation, and documentary/source execution:

```text
real PHOTSYS bytes observed = 0
BRICKNAME values observed = 0
BRICKID values observed = 0
ROOT values observed = 0
astronomical-data GETs = 0
```

The already sealed histogram may be read as aggregate evidence. The real FITS file may be hashed opaquely only if a later candidate explicitly requires an integrity preflight; no table span may be semantically read. The historical V1 executor and histogram executor must not be rerun.

Executable network tripwires and data-path tripwires are required before any future research imports or transport construction. Public documentary/source access must be counted separately from astronomical-data access.

## 18. Future V2 amendment boundary

Only outcomes `PHOTSYS_0x00_OUTSIDE_SEMANTICS_PROVEN` or `PHOTSYS_0x00_REPRESENTATION_MISMATCH_BUT_OUTSIDE_MAPPING_SUPPORTED` may justify drafting a later prospective V2 amendment.

That amendment may consider, but must independently specify and review, a mapping in which raw `0x4e` and `0x53` retain their historical categories and raw `0x00` becomes a valid technical exclusion. This document neither creates that mapping nor authorizes its use.

No V2 resolver exists. Panel V2 remains `NOT_STARTED`. P1 remains `BLOCKED`. OC-3 morphological discovery remains not started.

## 19. Present-stage result

This specification task performed no documentary network retrieval, source-code acquisition, synthetic NumPy demonstration, real FITS read, PHOTSYS observation, identity access, ROOT access, join, or semantic amendment.

The frozen administrative state is:

`PHOTSYS_ZERO_BYTE_SEMANTIC_PROVENANCE_RESEARCH_NOT_STARTED`

No semantic outcome has been selected. The next permissible action is a separately implemented and authorized bounded documentary/source investigation conforming exactly to this specification.

PHOTSYS V1 remains historically failed. No V2 resolver exists. Panel V2 remains `NOT_STARTED`; P1 remains `BLOCKED`; OC-3 morphological discovery remains not started.
