# OC-3 Amendment 002 implementation — synthetic verification only

Date: 2026-09-18. Scope: implementation and local synthetic regression authorized by the attached request. No production environment, survey access, production manifest, real brick selection, or OC-3 scientific execution occurred.

## 1. Authority and governance hashes

The following hashes were verified before implementation and again after the final synthetic replay:

| File | SHA-256 |
|---|---|
| `MORPHOLOGICAL_INFORMATION_PRESERVATION_SPEC.md` | `f7f27acbe42a0caecd1f0e4e2e86eedea6c546434d95c16143c0a7d122f38f24` |
| `OBSERVATIONAL_CANDIDATE_TRIAGE_OC2.md` | `9cbdc77943188717b1c92cf3fef64eaf03c968ce28e115df4171065e25362b93` |
| `OC3_DR9_COADD_BOUNDED_PILOT_SPEC.md` | `7fc040829847e26e6231c95b18d5debcd3785db0198915b1f93a5b45859f38bd` |
| `OC3_DR9_COADD_BOUNDED_PILOT_SPEC_AMENDMENT_001.md` | `2f87cec954167bc51ab442d1dbd803bae622bb5411a2b88642fecde8d920cd66` |
| `OC3_DR9_COADD_BOUNDED_PILOT_SPEC_AMENDMENT_002.md` | `4f6d921204645a0289c6f3c4ce4e5818419ade97d42b8b1d8def7cd2e6d723fe` |
| `OC3_IMPLEMENTATION_REPORT.md` | `bd3c3c2f30c346c8514de6056311cfdd84b61efb7bfa23cc8537ad226460b864` |
| `OC3_EXECUTION_PREFLIGHT_SPEC.md` | `6d5617ad5cc2b552d4a036a340077f4a727d06be4217e10d0f5b7408c9f6c28e` |
| `OC3_ENVIRONMENT_SETUP.md` | `fc39dba8f0d757ef0b342af01ff5710e21b56c1e6093c7969f910e02ad27c43d` |
| `AGENTS.md` | `3ac4d102494633036ed91e93c334a5cec702c877ba9daa1a67dd9803e778d222` |

Amendment 002 changes only bootstrap ordering, bootstrap/final bindings, immutable promotion, nested metadata limits, and explicit plan modes. Amendment 001 remains unchanged for T10, PSF guards, and the two-brick generalization limit.

## 2. Files changed and created

Changed:

- `oc3/oc3_pilot.py`: explicit bootstrap/final plan modes and typed budget flags.
- `oc3/oc3lib/core.py`: Amendment-002 authority, nested ledger stages, ledger identity, parent/development/receipt/child bindings, promotion events, and HTTP method accounting.
- `oc3/oc3lib/transport.py`: method-bound GET/HEAD transport and closed-role authorization after materialization.
- `oc3/oc3lib/workflow.py`: final-manifest v2 validation and same-ledger child reconstruction without brick reselection.
- `oc3/tests/test_infrastructure.py`: preserved historical tests adjusted for the amended authority/artifact inventory and explicit CLI selectors.
- `oc3/README.md`: amended interface and manifest contract.

Created:

- `oc3/oc3lib/bootstrap.py`: strict bootstrap schema, decoders, deterministic technical selection, firewall, dependent-role resolution, promotion, and resume.
- `oc3/tests/test_amendment002.py`: 42 synthetic Amendment-002 regressions, including all 35 frozen cases and the additional mandatory transport/ledger cases.
- `OC3_AMENDMENT_002_IMPLEMENTATION_REPORT.md`: this report.

Unchanged implementation/science files include `arrays.py`, `selection.py`, `statistics.py`, `run_tests.py`, `requirements.lock`, and the historical `OC3_IMPLEMENTATION_REPORT.md`. The repository has no `.git`; none was initialized or repaired. CPython bytecode caches produced by local syntax checking are non-authoritative, excluded from the aggregate implementation hash, and are not execution evidence.

## 3. Implementation identity

Historical implementation aggregate: `cf01a2774237ca98bf83dab01dda39a728f803e72e93c6796f214d20dcc6d57f`.

Amendment-002 implementation aggregate: `37d85f4ed38c0ff9fa91061eebf330c4d35065a69c249e721a8027593b4d27d4`.

The aggregate is `hash_object` over sorted relative `oc3/**/*.py` paths and each file SHA-256, excluding `.venv`. Current amended file hashes are:

| File | SHA-256 |
|---|---|
| `oc3/oc3_pilot.py` | `013bf57be3ead23ee783ace90274263c99a8071d58aff4fa6a5efeddb86af1de` |
| `oc3/oc3lib/bootstrap.py` | `10611cdf390018f29b0f14c810fff987370f7fd2186087e5ea1e6dbece74196e` |
| `oc3/oc3lib/core.py` | `58f21fedf93543bfb3e4819e8c3d53a15f1590587a23b19449110c6364958d88` |
| `oc3/oc3lib/transport.py` | `36532426ddc3fad3e376ff32855bb7592375085c3f8f249a409333edc4fa31b7` |
| `oc3/oc3lib/workflow.py` | `571b02cc0adb7c67ea34269517f27351a91a4ca7c61833107259d1497dd39bc4` |
| `oc3/tests/test_amendment002.py` | `de7d9e5a3040e40fae7031236f7a6041b58b32e2da237cedbaceabceb035eff9` |
| `oc3/tests/test_infrastructure.py` | `0397d9ae1e229b915ad3a803d11b84ce1d76d0666816434961e7cc622c6c6348` |
| `oc3/README.md` | `bdc610885864bea3c4b44cb7e4f89a9aef55f547628065f097a4682cd2a0bdad` |

## 4. Bootstrap architecture

`plan` has two explicit, mutually exclusive selectors. Bootstrap mode takes `--bootstrap-inputs` and requires `--resolve-metadata`; final mode takes `--inputs`, rejects `--resolve-metadata`, and has no transport capability. There is no argparse default that silently activates the final input. Bootstrap can operate before either final file exists. Final planning requires both final files and a committed child in the same ledger.

The bootstrap runner validates the parent and gates before constructing transport, acquires only literal metadata roles, decodes only their sealed technical projection, resolves one south and one north development brick, records permanent development assignment, materializes finite dependent roles, creates the final files, and commits exactly one parent-to-child relationship.

## 5. Bootstrap-manifest schema

`OC3_METADATA_BOOTSTRAP_MANIFEST.json` uses schema version 2 and exact-key validation. It binds authorities, implementation aggregate, independent environment/replay receipts, the DR9 north/south grz family, deterministic selection policy, permanent development-exclusion policy, literal resources, dependent roles, approved hosts, global/stage caps, reviewed rights, redistribution=false, semantics, release issues, and human authorization.

Canonical files are compact sorted-key UTF-8 JSON plus one LF. Duplicate keys, non-finite values, unknown fields, ambiguous types, noncanonical bytes, seal mismatch, and absent checksum reference fail closed. Production network validation requires Python 3.12.x, NumPy 2.5.3, Astropy 8.0.1, PyArrow 25.0.1, the environment fingerprint and receipts, zero-real-network replay evidence, affirmative local analysis/cache/public-access evidence, and the scoped human authorization binding.

## 6. Dependent-resource resolution

A dependent role is distinct from a materialized resource. Only `CLOSED_TEMPLATE_V1` and `EXACT_LINK_MAP_V1` are accepted. Before transport, an immutable resolution record binds role hash, supporting-evidence hash, selection hash, exact URL, method, host, release, selected generation, type/product/band, body cap, region, and brick. Runtime cannot change a host/method, search, crawl, follow redirects, use ranges, guess a brick/suffix, or send an unmaterialized dependent request.

The production transport begins with the literal URL/method map. A newly concrete URL is added only by `BootstrapRun` after the closed role has been validated and its resolution record written. HEAD remains HEAD and never authorizes a GET.

## 7. Deterministic brick selection

Bootstrap selection is independent of S1–N3 and accepts only sealed technical candidate fields. South eligibility requires DR9 DECaLS, grz, corrected release/generation 9012. North eligibility requires DR9 BASS/MzLS and grz without a false 9012 constraint. Each region is ordered by SHA-256 of `OC3-v1|brick|region|brickname`, with ASCII brickname as deterministic tie-breaker. Input row order does not affect the pair. Missing eligibility stops; there is no replacement, alternate release, DR9sv, survey fallback, or second pair.

## 8. Development exclusion

Selection immediately creates an immutable development record in the ledger. The deterministic CSV has exactly the frozen five columns, south then north, two rows, lowercase true values, LF endings, and a whole-file SHA-256. `holdout_disjoint=true` records prospective policy enforcement only. Holdout/lockbox paths remain rejected; selection does not open or compare a science holdout.

## 9. Parent-to-child promotion

The bootstrap parent hash/seal initializes the one execution identity. The ledger stores parent, development, metadata receipt, prepared child, and committed child bindings plus append-only events. Publication IO is charged before the child snapshot. A pre-commit crash can commit only the exact already prepared bytes; a post-commit resume validates and returns the existing child. A different prepared child, a missing/tampered final file, or a second explicit promotion stops for integrity review.

The child binds parent, receipt, ledger identity, live budget snapshots/watermark, exact promoted bricks, selection/development CSV, final manifest hash/seal, future resource identities, authorities, implementation, environment, and rights.

## 10. Ledger identity and cache

One `OC3_LEDGER_ANCHOR.json` fixes the execution identity and SQLite filename in the execution provenance directory. Opening a second ledger beside it fails. Promotion does not copy or reset counters, attempts, retry identity, cache state, or HTTP history. Final planning reads the committed child, parent, receipt, persisted caps, and live counters read-only from that same ledger. Later execution reopens it with the parent binding and the same identity.

Complete verified bodies are reused. Partial/error bodies and crash reservations retain conservative charges. Attempts record resource, category, method, stage, reservation, received bytes, and state.

## 11. Nested budgets

METADATA_BOOTSTRAP caps are body bytes 48 MiB, requests 48, disk 256 MiB, local IO 512 MiB, active compute 300 s, wall 900 s/invocation, and concurrency 1. Every reservation checks stage body/request caps and global body/request/metadata/retry constraints in one SQLite transaction before transport. Every received byte debits both stage and global counters. Local IO and compute are also dual-charged.

Unused reservation can be released; received bytes are never refunded. Finishing bootstrap does not restore global usage. Reopening preserves lower global and stage caps. Final planning consults live global counters and persisted caps rather than the child's older JSON snapshot.

## 12. CLI changes

Bootstrap example shape:

```text
python3 oc3/oc3_pilot.py plan --bootstrap-inputs <parent.json> --resolve-metadata --execute-network --max-global-bytes ... --max-stage-bytes ... --resume
```

Final-plan example shape:

```text
python3 oc3/oc3_pilot.py plan --inputs <final.json> --offline
```

The selectors are mutually exclusive and required. `--resolve-metadata` is bootstrap-only. Stage flags are bootstrap-only. Ambiguous legacy `--max-*` flags fail closed for planning/network stages; `--max-global-*` and `--max-stage-*` can only lower their respective frozen maxima. Both plan modes support dry-run with zero ledger/evidence creation, promotion, persisted selection, FITS decoding, or transport.

## 13. Bootstrap firewall

Bootstrap rejects before transport: science-map GET for image/invvar/nexp/maskbits/psfsize, any PSF, Tractor/source catalogs, model/blobmodel/depth/galdepth/chi2/JPEG/individual exposure, Galaxy Zoo/Zoobot/morphology/physical-validation content, recursive crawl, ranges, unlisted methods/hosts/URLs, redirects, and unmaterialized dependent identities. A coadd HEAD is permitted only through a sealed `science_map_header` role; it records transport metadata and cannot assert HDU, WCS, units, or pixel semantics.

## 14. Environment and rights gates

Synthetic fixtures may use synthetic bindings. Production network mode cannot. It requires the independent environment fingerprint, install/preparation/replay receipts, frozen package versions, affirmative reviewed local-use/cache/public-access evidence, redistribution=false, and a `METADATA_BOOTSTRAP_ONLY` human authorization record. Missing or inconsistent evidence blocks before a request.

## 15. Amendment-001 regression

No scientific selection, pixel processing, PSF meaning, T01–T12 meaning, or terminal outcome was changed. The historical golden RNG values remain exact. The revised suite retains 999 permutations, seed 301, SHA-256 to eight big-endian uint32 words, SeedSequence/PCG64, fixed state classes, omnibus/IQR/p formula/Holm behavior, PSF engineering-only interpretation, and unresolved two-brick generalization.

## 16. Synthetic verification

Historical verification remains: **100 passed / 0 failed / 0 skipped**. It is not rewritten or presented as evidence for Amendment 002.

New complete revised suite: **142 passed / 0 failed / 0 skipped**. This consists of the preserved 100 tests plus 42 Amendment-002 tests. The final replay reported 20.420 s in unittest and 21.407 s including runner setup. All fixtures were synthetic/local and temporary. The runner blocked socket creation, connection, and DNS before importing tests. Reported real network requests: **0**.

The 42 additions cover every frozen case 1–35 plus dependent-role materialization, HEAD error-body accounting, partial-body dual accounting, shared metadata allowance, retry identity across promotion, successful final planning without reselection, and preservation of a lowered global cap.

## 17. Commands actually executed

Only local read/hash/state inspection, syntax verification, and the synthetic runner were executed. The principal commands were:

```bash
sha256sum <frozen authorities and governance documents>
c0/.venv/bin/python -m py_compile oc3/oc3_pilot.py oc3/oc3lib/core.py oc3/oc3lib/bootstrap.py oc3/oc3lib/transport.py oc3/oc3lib/workflow.py
c0/.venv/bin/python oc3/tests/run_tests.py
c0/.venv/bin/python oc3/tests/run_tests.py > /tmp/oc3_amendment_002_final_test.log 2>&1
```

Development replays first exposed and then resolved stale historical expectations, one indentation error, a missing-file exception classification, and legacy-v1 canonical compatibility. After the final corrections, two complete 142-test replays passed with zero failures/skips. No failed development replay is observational evidence.

The read-only development interpreter was `/home/jzsalinas/Documents/galaxy-morphology-discovery/c0/.venv/bin/python`: Python 3.12.14, NumPy 2.5.3, Astropy 8.0.1, PyArrow 25.0.1. No package was installed or changed and no C0 pipeline was run. This is not production certification.

## 18. Network and acquisition accounting

Real DNS/socket/HTTP requests: **0**. Survey requests: **0**. Astronomical bytes downloaded: **0**. Package-index requests: **0**. Tests used injected in-memory response objects only. No DR9 metadata, FITS, pixels, maps, headers, PSFs, catalogs, or documentation URL was accessed.

## 19. Integrity and preservation

All frozen hashes in section 1 remain unchanged. `requirements.lock` remains `79228cc4d2577f7bd2d127db4d9e78a3cf1224736a8736610933f363af16205d`. The historical implementation report remains unchanged. The production `oc3/INPUTS`, `provenance`, `RAW_IMMUTABLE`, `TECHNICAL_INDEX`, and `reports` directories contain zero files. No production bootstrap/final manifest, ledger, receipt, HTTP event, resource plan, or terminal outcome was created. No real DR9 brick was selected.

## 20. Known limitations

- The independent production Python 3.12 environment does not exist and has not replayed this amended aggregate.
- `OC3_ENVIRONMENT_SETUP.md` is preserved at its frozen hash and its historical replay snippet asserts 100 tests. Amendment 002 requires the future independent replay to assert the revised complete count, 142, and bind aggregate `37d85f4ed38c0ff9fa91061eebf330c4d35065a69c249e721a8027593b4d27d4`; do not treat the old 100-test assertion as amended certification.
- No production bootstrap manifest, literal DR9 resource inventory, provider projections/checksums, rights record, environment receipt, or concrete human authorization has been reviewed or sealed.
- HEAD can bound and identify a future representation but does not verify FITS/HDU/WCS/unit/pixel semantics.
- Supported bootstrap decoders are the explicitly projected JSON-row and FITS binary-table layouts plus opaque/checksum documents. Any real provider layout outside those contracts requires a prospective reviewed change, not a fallback.
- Two selected development bricks and all subsequent OC-3 scientific outcomes remain unexecuted; representativeness remains unresolved.

## 21. Remaining preflight blockers

Current state: **PREFLIGHT_BLOCKED_ENVIRONMENT**, with production-input, rights, provider-semantics, replay-binding, and concrete human-authorization blockers still open. Software implementation and local synthetic regression do not assign `PREFLIGHT_READY_FOR_METADATA_RESOLUTION`.

The exact first human command after review is the non-mutating availability check already frozen in the environment handoff:

```bash
cd /home/jzsalinas/Documents/galaxy-morphology-discovery
python3.12 --version
```

Expected: exit 0 and Python 3.12.x. If unavailable or different, stop with `PREFLIGHT_BLOCKED_ENVIRONMENT`. This command does not authorize environment creation, package installation, survey access, or metadata resolution.

## 22. Final state

Implementation of Amendment 002 and complete local synthetic regression are complete. Production preparation and all observational stages remain blocked pending separate evidence and human handoffs.

**OC-3 REMAINS NOT STARTED.**
