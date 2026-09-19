# OC-3 infrastructure implementation — synthetic verification only

Date: 2026-09-18. Scope: implementation authorized by the user's attached request; no authorization to execute the scientific pilot. This report records software behavior, not evidence about DR9.

## 1. Authority hashes

Verified before implementation and unchanged on completion:

| Authority | SHA-256 |
|---|---|
| MORPHOLOGICAL_INFORMATION_PRESERVATION_SPEC.md | `f7f27acbe42a0caecd1f0e4e2e86eedea6c546434d95c16143c0a7d122f38f24` |
| OBSERVATIONAL_CANDIDATE_TRIAGE_OC2.md | `9cbdc77943188717b1c92cf3fef64eaf03c968ce28e115df4171065e25362b93` |
| OC3_DR9_COADD_BOUNDED_PILOT_SPEC.md | `7fc040829847e26e6231c95b18d5debcd3785db0198915b1f93a5b45859f38bd` |
| OC3_DR9_COADD_BOUNDED_PILOT_SPEC_AMENDMENT_001.md | `2f87cec954167bc51ab442d1dbd803bae622bb5411a2b88642fecde8d920cd66` |
| AGENTS.md | `3ac4d102494633036ed91e93c334a5cec702c877ba9daa1a67dd9803e778d222` |
| E_OC1_EVIDENCE_REGISTER.json, historical only | `a00b09f82f1f5b740666e9bcece77299b64fa240ac3df22790c5f7b242572952` |
| E_OC1_SUFFICIENCY_REVIEW.md, historical only | `2f1f9fc99cebd04e3dbda56a3b5fbff30125707e8323892e6a9b72989c6786c4` |

Amendment 001 supersedes only T10 inference, engineering-guard interpretation and two-brick generalization language. The base documents were not merged or rewritten. The CLI rechecks the four frozen hashes before any stage that could create evidence. Every future run binds AGENTS, input manifest, development allowlist and implementation hashes as well.

## 2. Created/modified files

All implementation files are new. No preexisting project file was modified.

- `oc3/oc3_pilot.py`: CLI.
- `oc3/oc3lib/__init__.py`, `core.py`, `transport.py`, `selection.py`, `arrays.py`, `statistics.py`, `workflow.py`: implementation.
- `oc3/tests/run_tests.py`, `test_infrastructure.py`: synthetic suite.
- `oc3/tests/SYNTHETIC_TEST_RESULTS.log`, `SYNTHETIC_TEST_RESULTS.json`, `PRESERVATION_CHECK.json`: implementation verification, explicitly outside production evidence directories.
- `oc3/README.md`, `oc3/requirements.lock`: interface/input/dependency documentation.
- `OC3_IMPLEMENTATION_REPORT.md`: this report.

Python implementation hash, computed over sorted relative Python paths and their SHA-256 values: `cf01a2774237ca98bf83dab01dda39a728f803e72e93c6796f214d20dcc6d57f`.

Created empty production directories INPUTS, provenance, RAW_IMMUTABLE, TECHNICAL_INDEX, CONFOUND_AUDIT, reports and logs. No production manifest, URLs, brick identities, coordinates, acquisition ledger, crops or terminal result was fabricated.

## 3. Architecture and artifact contracts

The seven commands are plan, acquire-aux, select, acquire-fixed, analyze, verify and finalize. Core handles bindings, strict schemas, immutable files and budgets; transport owns all HTTP capability; selection accepts auxiliary arrays only; arrays handles native extraction and descriptors; statistics implements amended T10; workflow connects the stages.

`core.ARTIFACTS` maps all 25 required named artifacts to their frozen directories. JSON field requirements are in `workflow.REQUIRED_ARTIFACT_FIELDS`, inputs in `core.FIELDS`; SQLite contains config, counters, attempts and resources. CSVs preserve structured values as JSON cells. Parquet is dependency-gated, with no silent substitute. Missing products have state records, never fabricated files.

A deferred PSF manifest solves the dependency on locations that do not exist before selection: the original input may set `deferred_psf=true`, reserving 54 logical requests/54 MiB. After selection, a separately sealed OC3_PSF_LINKS.json must bind the same authority registry and selection hash. Every frozen point/band must be enumerated or documented unavailable; no substitutes. Its hash is pinned in the existing ledger. It cannot expand the original budget or alter the selection. URLs must be supplied through that audited manifest; code does not invent them.

## 4. Network isolation

OfflineNetwork has no HTTP client capability. Acquisition defaults to this object and refuses before a reservation. Real HTTPTransport is constructed only for an explicitly requested future network stage with a reproducible sealed PRODUCTION plan; `--execute-network` is mandatory and cannot override `--offline`. Dry-run returns before transport, ledger, scientific imports or FITS decoding; it reports dependencies, missing inputs and caps.

HTTPS URLs must be individually enumerated on approved hosts; no redirects, recursive crawl, endpoint discovery or automatic online fallback. Real HTTP uses identity encoding, TLS validation and a 30-second timeout. Tests replace socket construction, DNS lookup and connection functions with failures before loading test modules; all response bodies are in-memory fixtures. No real endpoint was contacted, including documentation endpoints.

## 5. Cumulative resource ledger

One SQLite ledger is shared across stages and resumes. Transactions reserve the bounded worst-case response body and request before an HTTP attempt. Actual received bytes include partial and failed bodies; unused reservation is refunded only on recorded completion. An interrupted process conservatively retains its entire outstanding reservation until recovery marks it charged. Unknown size never permits reading past the sealed cap. Complete cached products cause no new GET or HEAD.

Frozen maxima: 2 bricks; 6 slots; 1,610,612,736 body bytes; 200 requests; 2 additional retries/resource; concurrency 1; metadata 64 MiB; PSF 54 MiB and 1 MiB per logical point/band; RAM target 2 GiB; one thread; no GPU; disk 4 GiB; local IO 8 GiB; active compute 1,800 seconds; wall time 3,600 seconds/invocation. CLI limits only decrease; decreased cumulative limits persist. RAM/disk/time checks are cooperative; allocations and writes are additionally bounded where sizes are known. This is not a kernel-level resource sandbox.

No automatic retry loop runs. Human resume consumes the remaining attempts; the production transport applies the frozen 2/5-second retry backoff. HTTP failure ends the invocation, so it never polls through a long Retry-After. No background process is used. IO accounting is deliberately conservative and can close a real run for insufficient budget before nominal transfer capacity is used.

## 6. Cache, resume and integrity

Resources bind release/generation/product/URL and technical identity. Production IDs derive from those fields. Partial immutable fragments record byte ranges and SHA-256; the ledger records the contiguous committed offset. Resume requires a strong ETag and known total size, exact 206/Content-Range and unchanged identity. Unsupported resume conditions stop rather than restart a full transfer. Cache assembly verifies optional provider SHA-256 and always records the full local SHA-256.

Conflicting cache bytes, authority bindings or generations are never overwritten. A crash between writing a fragment and committing its offset can leave an orphan fragment; it is retained, not deleted to conceal interruption. A conflicting incomplete final file stops for review. An active-run integrity failure pins a stop in the ledger and emits D; future resumes refuse that ledger. A pre-run authority failure emits the integrity sentinel without inventing an observational result.

HTTP events include UTC, requested/final URLs, status, headers, attempts, body bytes and range offset. Run logs carry UTC and stage status.

## 7. Frozen selection engine

The engine implements SHA-256 brick ordering, corrected southern 9012 eligibility, the 0-based grid with deduplicated final indices, 129×129 windows, ordered S1/S2/S3/N1/N2/N3 predicates, no replacement, fixed hash tie-breaking and distinct centers. N2 uses its frozen two-level NEXP rule. N3 computes the frozen within/across-band V and preserves STRATUM_NOT_EXERCISED below 0.10.

AuxiliaryBundle accepts only nexp, psfsize and integer maskbits; it rejects image and extra keys. Primary-region geometry uses the native WCS and published bounds, never NPRIMARY as a replacement. Supported production geometry is a small undistorted TAN RA/Dec rectangle with RA wrap; fixed numerical minimization operates on its projected boundaries. Unsupported geometry fails closed. Synthetic rectangle oracles test the predicates without a survey endpoint. No brightness-dependent selection is available.

## 8. Pixel states and no leakage

All 13 frozen axes are preserved. Null/UNKNOWN remains distinct from false. Integer masks and unknown bits are retained. A finite supported unflagged value is only supported_unflagged_candidate; a zero is zero_with_unresolved_validity unless independent validity evidence is explicitly provided. Positive IVAR/NEXP is not quality certification. Geometry unknown remains null.

Strict schemas reject unrecognized columns, including morphology TYPE, vote/prediction and physical-validation fields. Paths and resolved symlink targets reject holdout/lockbox/interpretation/label-associated inputs. Selection has no image parameter. Error messages do not print prohibited column names or values. No label, prediction, physical-validation or holdout input was opened.

## 9. FITS and exact crop

Astropy decodes only a sealed logical 2D HDU. Records include full raw, physical and decoded headers; logical dtype/endian; HDU; BITPIX/dimensions/scaling/BLANK; compression; decoder and NumPy versions. Unsupported layouts are rejected. Crops are native integer slices with exact requested/intersected domains and offsets, without padding, interpolation, resampling or convenience float32 conversion. CRPIX changes only by integer crop offset; unsupported distortion lookup tables are not silently discarded.

Independent section reading exposed an Astropy byte-order difference in synthetic tests: .data may preserve FITS endian while .section returns native endian. Equality therefore permits only reversible byte-order normalization of the comparison array, with identical logical dtype, bits and NaN payload; the saved crop is unchanged. Different precision or NaN payload fails. Both decoder dtypes are recorded. This validates extraction from a fixed decoded input, not upstream flux preservation or exposure truth.

## 10. T01–T12 and decisions

Records contain test, one of VERIFIED/CONTRADICTED/NOT_AUDITABLE/NOT_EXERCISED, reason, input references, authority hashes, metrics, evidence references and domain/unit. Missing slots retain all 12 records. Software can verify exact extraction and numerical grid bookkeeping, report PSFSIZE descriptors and reproduce canonical arrays/metrics. It cannot infer documentary identity, rights, complete mask semantics, PSF lineage or signal/noise identifiability from successful arithmetic.

The decision function has only the four frozen terminal outcomes, with integrity priority and no PENDING. Synthetic fixtures exercise all branches. Automatic production orchestration deliberately leaves unsupported semantic tests NOT_AUDITABLE and does not certify D_restricted; a future evidence review is required before A/B can be asserted. It currently closes insufficient evidence as C. It never transforms engineering guards or a T10 p-value into observational admissibility. Two bricks do not demonstrate DR9 representativeness; generalization remains unresolved even for A.

## 11. PSF descriptors

Float64 descriptor arithmetic records S, absolute edge mass in two pixels, extrema, negative weights, centroid, second moments, positive definiteness, declared-center x/y half-height crossings and ambiguity, and F_mom. Input PSF pixels are not renormalized or clipped and their original hash is retained. No Gaussian replacement is fitted.

PSFSIZE outputs include min/max/median/Q05/Q95, missing fraction and native x/y profiles. At the frozen integer points, widths and PSFSIZE differences are descriptive only; no agreement tolerance is invented. Guard outputs are explicitly PILOT_ENGINEERING_GUARD: variation≤10%, minimum width≥2 pixels and edge mass≤1%, with all three PSF points required. They never establish morphology preservation or MIP PASS.

## 12. Amendment 001 / T10

Exactly 16 original blocks and ten ordered lags are retained, including unavailable blocks in partial windows. Descriptive rows preserve finite pairs, supported-weight pairs and original optical flag strata, means, variances, covariance, counts and estimability. No source masking, clipping, intensity normalization or background image is produced.

One omnibus/slot/band uses max absolute estimable lag correlation per block and their median; linear-quantile IQR; fewer than four blocks is NOT_AUDITABLE. Exactly 999 permutations use the frozen SHA-256 eight big-endian words, SeedSequence entropy 301 and PCG64. Tests contain fixed expected raw RNG output. Every draw starts with original values and fixed canonical state classes, without retrying inconvenient draws. State class counts, singleton limitations and permutation estimability are retained. p=(1+count≥)/1000; Holm α=.05 applies only to auditable omnibus units, with prescribed ties and prefix-max adjustment. There is no 199 option or block/lag inferential test. Only the three permitted inferential labels can be emitted.

## 13. Synthetic verification

Final result: **100 passed, 0 failed, 0 skipped**, 10.528 seconds in unittest (10.96 seconds including runner setup). Reproducible command and full test names/results are in `oc3/tests/SYNTHETIC_TEST_RESULTS.log`; compact result in the adjacent JSON. All fixtures are local synthetic data in temporary directories; production evidence paths remain empty.

Coverage includes all 28 requested behaviors: authority/amendment failures; hard offline/dry-run; all budget ceilings; cumulative reservations, failed/partial bodies, crash recovery and retry limits; immutable cache/generation conflicts; all six deterministic slots and image exclusion; independent states and unknown bits; exact/edge/WCS/scaled/integer FITS crops; signed/ambiguous PSFs and guards; fixed RNG, 999 inference, hand-computed omnibus/IQR, p_min, Holm ties and no descriptive inference; canonical reproduction; prohibited fields/paths and stop state. Additional tests cover deferred PSF plans, prospective budget, binding/refinement, three-point requirement, cross-stage artifacts and a composed synthetic FITS acquisition→analysis→offline verification→synthetic C.

Earlier development runs caught (and resolved) an incorrect artifact-count assertion (27 instead of the required 25) and the decoder endian comparison. They were software failures, not observational findings. No test imported a C0 pipeline or decoded existing astronomical data. Existing `c0/.venv/bin/python` was used read-only as the available numerical interpreter, with bytecode writes disabled; no C0 process or dependency installation was run. Versions: Python 3.12.14, NumPy 2.5.3, Astropy 8.0.1, PyArrow 25.0.1. A future production environment must be independent of C0.

## 14. Commands actually executed

From the repository root:

```bash
python3 oc3/oc3_pilot.py --help
python3 oc3/oc3_pilot.py plan --spec OC3_DR9_COADD_BOUNDED_PILOT_SPEC.md --inputs oc3/INPUTS/OC3_INPUT_MANIFEST.json --dry-run --offline
python3 oc3/oc3_pilot.py acquire-aux --offline
PYTHONDONTWRITEBYTECODE=1 c0/.venv/bin/python oc3/tests/run_tests.py > /tmp/oc3_synthetic_tests_final.log 2>&1
```

Help and dry-run returned 0; offline acquisition was deliberately refused with exit 21 and OC3_OFFLINE_BLOCKED, before side effects. Dry-run reports the absent execution manifest and unavailable scientific dependencies in system Python 3.14.4; this is not a scientific plan validation or execution. Development runs, tiny synthetic endian diagnostics, file/authority hashing, inventory comparisons and local file reads/writes were also performed. No real network command was executed.

## 15. Commands explicitly NOT executed

No production plan --resolve-metadata, acquire-aux, select, acquire-fixed, analyze, verify or finalize was run. No astronomical query, header fetch, HEAD, FITS/PSF/metadata/document download, catalog operation, training, embedding, dimensional reduction, clustering, preprocessing optimization or gallery was performed. No pip installation or remote code execution occurred. The acquisition command in §14 tested refusal only; in-memory mock transfers are not real acquisitions.

## 16. Known limitations / review frontier

- No real execution manifest or authoritative technical projection has been supplied. Brick names, URLs, headers/layouts, exact transfer/IO sizes, rights and PSF service linkage remain unresolved. Sealing an assertion does not independently verify it.
- Metadata retrieval fetches only enumerated bounded resources; it does not crawl or automatically certify arbitrary survey documents/tables. Independent documentary review remains necessary. No automatic mechanism silently upgrades its assertions to VERIFIED or authorizes A/B.
- PSF responses must expose supported 2D logical HDUs and documented center/scale. Bundled 3D responses, unresolved lineage or unsupported WCS/compression layouts stop; no substitute decoder/product is assumed.
- Only fixed TAN geometry is implemented; its boundary-distance minimization is numerical, not a proof for arbitrary projection/distortion. Unsupported domains fail closed. Grid consistency is not measured astrometric registration on the sky.
- Real network behavior and real-survey resource fit have not been tested. Conservative repeated-read IO accounting may exhaust the 8 GiB cap before transfer capacity; that is insufficiency, not permission to relax the cap. Full brick reads are bounded to the two selected bricks; no claimed Range scientific equivalence is inherited from C0. HTTP Range here resumes interrupted byte streams only.
- Production science environment setup is not performed. The lock lists tested versions, not downloaded wheel hashes; deployment must fix its independently prepared environment. Missing dependencies fail, never trigger installation or format fallback.
- All production outcomes remain unassigned. Synthetic A/B/C/D fixtures prove control flow only, not observational eligibility.

## 17. Future human handoff — NOT EXECUTED

Working directory: `/home/jzsalinas/Documents/galaxy-morphology-discovery`.

**FIRST command, safe offline inspection only:**

```bash
python3 oc3/oc3_pilot.py plan --spec OC3_DR9_COADD_BOUNDED_PILOT_SPEC.md --inputs oc3/INPUTS/OC3_INPUT_MANIFEST.json --dry-run --offline
```

Expected now: OC3_DRY_RUN_OK with missing manifest/dependencies; zero network and zero evidence writes. This does not authorize or start the pilot.

The following sequence is prepared for a separately authorized human run, after an independent pinned environment makes `python3` resolve the required versions, and after a reviewed sealed INPUTS/OC3_INPUT_MANIFEST.json plus INPUTS/OC3_DEVELOPMENT_BRICKS.csv exist. Input schemas/seal procedure are documented in README and code. Do not fill placeholders with guessed URLs or brick names.

```bash
python3 oc3/oc3_pilot.py plan --spec OC3_DR9_COADD_BOUNDED_PILOT_SPEC.md --inputs oc3/INPUTS/OC3_INPUT_MANIFEST.json --resolve-metadata --execute-network --max-bytes 1610612736 --max-requests 200 --max-bricks 2 --max-locations 6 --resume
python3 oc3/oc3_pilot.py acquire-aux --plan oc3/provenance/OC3_RESOURCE_PLAN.json --execute-network --max-bytes 1610612736 --max-requests 200 --resume
python3 oc3/oc3_pilot.py select --plan oc3/provenance/OC3_RESOURCE_PLAN.json --offline --seal --resume
```

Stop at this boundary until the audited, sealed TECHNICAL_INDEX/OC3_PSF_LINKS.json has been supplied for the exact selected coordinates if using deferred_psf. Its schema, all missing-point records and fixed budget must be checked; no new selection or general resource-plan replacement is permitted. Then, only under that future authorization:

```bash
python3 oc3/oc3_pilot.py acquire-fixed --plan oc3/provenance/OC3_RESOURCE_PLAN.json --locations oc3/TECHNICAL_INDEX/OC3_LOCATIONS.json --execute-network --max-bytes 1610612736 --max-requests 200 --resume
python3 oc3/oc3_pilot.py analyze --locations oc3/TECHNICAL_INDEX/OC3_LOCATIONS.json --offline --resume
python3 oc3/oc3_pilot.py verify --offline
python3 oc3/oc3_pilot.py finalize --offline
```

All network/acquisition commands above are **NOT EXECUTED**. Each shares the same ledger. The future real workload is human-only under AGENTS: estimated 10–60 minutes depending on transport/layout and 2–4 GiB incremental disk, subject to all hard caps. Exact stage estimates must come from the later resource plan; these figures are not measured for DR9. Any >5-minute, >250-MiB, intensive >1-GiB-IO or bulk operation remains human-only. No such production workload was started here.

Inputs: sealed authorities, execution manifest, allowlist, plan, location manifest, deferred PSF links if applicable, and only the authorized cached products. Outputs: the 25 frozen named artifacts, immutable resource/partial cache and native crops. Main log: oc3/logs/OC3_RUN.log; HTTP provenance: oc3/provenance/OC3_HTTP_EVENTS.jsonl; cumulative ledger: oc3/provenance/OC3_RESOURCE_LEDGER.sqlite. Technical stage sentinels are OC3_PLAN_OK, OC3_ACQUIRE_AUX_OK, OC3_SELECT_OK, OC3_ACQUIRE_FIXED_OK, OC3_ANALYZE_OK and OC3_VERIFY_OK. Finalize emits OC3_TECHNICAL_RUN_COMPLETE; outcome=<frozen outcome>. A technical sentinel is not MIP PASS.

Resume only the same command/inputs with --resume, preserving all files and counters. Exit 75 denotes transport/OS interruption; HTTP/prerequisite/budget refusal uses 22, offline refusal 21. Inspect the ledger/events before retrying; two additional attempts/resource maximum. Exit 20 and OC3_INTEGRITY_FAILURE_STOP are a stop, never a retry by altering hashes or deleting the ledger. If the budget cannot safely support completion, close for insufficiency with finalize --offline; do not acquire alternatives. Do not proceed beyond a failed stage merely because a later command exists in this report.

## 18. Integrity and preservation

Baseline inventory: 6,587 preexisting files. Completion comparison found zero missing or changed sizes/mtimes at the baseline's JavaScript Number precision; this is a metadata preservation check, not a rehash of all astronomical files. Eleven document/historical-register SHA-256 checks were unchanged. All frozen authority hashes in §1 match. No C0/E-OC1 process was repeated, counter reset, historical report modified or data file decoded. Git status reports that this directory is not a Git repository; .git was not initialized, repaired or deleted.

Production OC3 INPUTS, provenance, RAW_IMMUTABLE, TECHNICAL_INDEX, CONFOUND_AUDIT, reports, logs and crops contain zero files. Only infrastructure/test verification artifacts exist. The final synthetic test log and preservation check are under tests, never presented as survey evidence.

## 19. Final project state

**OC-3 remains NOT STARTED.**

**No astronomical data were acquired.**

**No observational outcome A/B/C/D has been assigned.**

**The implementation is infrastructure only.**

Zero real network requests. Frozen authorities remain unchanged. C0 remains CLOSED/STOP and E-OC1 remains CLOSED with its prior result; neither was reopened.
