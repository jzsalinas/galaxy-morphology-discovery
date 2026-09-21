# OC-3 infrastructure — not a scientific run

Default CLI transport is offline. No production manifest, URLs, coordinates or data are shipped.
`--help` and either explicit `plan` mode with `--dry-run --offline` work without transport.
Scientific stages require NumPy, Astropy and PyArrow; missing dependencies fail closed.
No automatic package installation, endpoint discovery or offline-to-online fallback exists.

Authoritative design: the five hashed scientific/OC-3 documents, including Amendments 001 and 002.
Implementation entry point: `oc3/oc3_pilot.py`; core modules: `oc3/oc3lib/`.
Run synthetic verification with the separately documented local interpreter in the implementation report.
Tests use isolated temporary directories and reject real sockets/DNS. They are not DR9 evidence.

Amendment 002 defines an explicit metadata-bootstrap parent before the final execution manifest.
`plan --bootstrap-inputs ... --resolve-metadata` and `plan --inputs ...` are mutually exclusive;
there is no implicit input default. The former accepts only closed technical metadata roles and
the latter requires the committed child in the same ledger. A final plan never selects bricks
again and never retrieves metadata.

Future production bootstrap and final manifests must be supplied and sealed before acquisition.
The JSON schema contracts are in `oc3lib.core.FIELDS` and
`oc3lib.workflow.REQUIRED_ARTIFACT_FIELDS`. Artifact paths are in `ARTIFACTS`.
CSV allowlists require exact columns `region,brickname,development,holdout_disjoint,evidence_ref`.
JSON canonical sealing is SHA-256 over sorted-key compact UTF-8 JSON without the `sealed` field.
These are integrity bindings, not digital signatures or permission to run.

No code automatically upgrades documentary assertions to scientific VERIFIED evidence.
The diagnostic harness records unresolved semantic tests. The four-outcome decision engine
is independently testable; automatic analysis alone cannot claim all DR9 properties verified.
Two bricks never establish representativeness of DR9; generalization remains unresolved.

The bounded coadd resource stage has a separate entry point, `oc3_resource_contract.py`.
Its dry run serializes the exact 14-resource auxiliary inventory and 12 future image/invvar
identities without network. A probe accepts only a separately reviewed sealed binding of
literal URLs; it never derives the provider directory component and reads aligned FITS header
blocks only. Bulk auxiliary acquisition remains a separately authorized future human run.

The offline location selector has the separate entry point `oc3_location_selection.py`.
It has no network mode and can decode only the frozen NEXP, PSFSIZE and optical MASKBITS
resources already published under `RAW_IMMUTABLE`. It emits six deterministic observational
locations and aggregate technical evidence; it cannot open image, invvar, PSF or catalogs.

The fixed native-resource contract uses `oc3_fixed_native_resource_contract.py`. Its dry-run
validates the sealed twelve-resource image/invvar binding without network. Its separately
human-run probe can issue only literal HEAD and aligned FITS-header Range requests, persists
per-resource checkpoints, and has no pixel decoder or bulk acquisition path. The companion
PSF contract keeps 54 point-band identities distinct from 18 prospective multi-band responses.

The coadd-PSF transport contract uses `oc3_coadd_psf_contract_probe.py`. Its dry-run validates
the sealed 54-identity manifest and the two literal representative requests without network.
The separately human-run probe performs at most one capped GET for S1/P0 and one for N1/P0,
persists each regional response structure, never accesses image/invvar products, and never
decodes PSF array values. It is a service-semantics probe, not PSF bulk acquisition.

Production input contracts (to be supplied in a later authorized task):

- `OC3_METADATA_BOOTSTRAP_MANIFEST.json`: schema version 2; frozen authorities and implementation;
  independent environment/replay, DR9 north/south grz family, deterministic brick/development
  policies, literal metadata resources, finite dependent roles, typed nested caps, reviewed rights,
  approved HTTPS hosts and human authorization. Extra fields and scientific content fail closed.
- `OC3_INPUT_MANIFEST.json`: schema version 2; execution_kind PRODUCTION; exact development CSV
  path/hash; exactly the promoted south/north pair; enumerated aux/image/invvar resources; rights,
  semantics, release issues, approved hosts and mandatory parent/receipt/selection/ledger links.
- `rights` has only analysis, local_preservation, redistribution and evidence_refs.
  Analysis and local preservation must be true with evidence before acquisition.
- Semantic rows have product, property, status, value, units, evidence_refs.
  Issue rows have issue, region, generation, status, evidence_refs. Unexpected fields fail.
- Each resource binds URL, product, stage, category, release, generation, region/brick/band,
  bounded max_bytes, optional exact size/provider SHA-256/strong ETag, logical HDU and evidence.
  Production id is `resource_identity(resource)` in transport.py; URLs are never synthesized.
- Use `deferred_psf: true` when PSF URLs require the subsequently selected coordinates.
  This reserves 54 requests and 54 MiB prospectively, in addition to the other resource caps.
  After `select`, supply `TECHNICAL_INDEX/OC3_PSF_LINKS.json` with exactly
  binding, selection_sha256, resources, unavailable, sealed. Binding is the original authority
  registry; selection_sha256 is the actual sealed selection hash. Each resource is one band,
  at most 1 MiB, and location is `[slot, native_x, native_y]`. Every frozen point/band is covered
  exactly once by a resource or unavailable record (location, band, reason, evidence_refs).
  No replacement or moving a point is allowed. Requests retain the original cumulative ledger.
  The PSF manifest hash is pinned on first use and cannot change during resume.
- Bootstrap decoders accept only sealed projections for JSON rows or FITS binary-table rows.
  Dependent URLs become usable only after closed-role materialization binds the selected brick,
  method, host, release/generation, body cap, evidence and selection hash. There is no endpoint
  search, crawling, suffix guessing, redirect allowance or science-map GET during bootstrap.

Canonical manifest sealing: SHA-256 of UTF-8 JSON with sorted keys, separators `(',', ':')`,
`ensure_ascii=False`, `allow_nan=False`, excluding only the top-level `sealed` field.
The `seal` helper in workflow.py returns the object with that field. Creating a seal is not
an authorization or a certification of provenance.

The real environment must be independent of C0 and use the versions recorded in requirements.lock.
No environment is created automatically. An unavailable decoder or unsupported logical layout
stops the stage; there is no format or survey fallback.

Probe 001 is preserved as immutable partial evidence. The corrected
`oc3_resource_contract_probe002.py` imports its cumulative counters, publishes
per-resource HEAD and FITS-structure checkpoints, and scans at most 16 aligned
header blocks per resource under a separate 136-request local/global envelope.
Its dry run is offline; its network mode requires Binding 002 and a fresh audit directory.

`oc3_resource_contract.py --validate-auxiliary-candidate` validates the sealed
`AUXILIARY_14_ONLY` technical proposal entirely offline. Future acquisition uses
the historical cumulative counters plus a mandatory 34-request stage cap and
still requires a separate final human authorization before transport exists.
