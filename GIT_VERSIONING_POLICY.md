# Git versioning policy

## Purpose

Git records the research recipe, governance, code, and compact evidence. Large scientific and runtime bytes remain filesystem evidence and are bound through hashes and manifests. Git does not replace the project's existing SHA-based evidence model.

This baseline describes the repository immediately before rights binding or a real OC-3 metadata-bootstrap attempt. It does not authorize an acquisition, create an attempt, or change the scientific state.

## Content kept in normal Git history

Normal Git history should contain:

- source code and tests;
- authoritative Markdown specifications, amendments, and clarifications;
- implementation and audit reports;
- frozen execution plans;
- small environment and replay receipts;
- compact synthetic result JSON;
- scientifically relevant small logs that form part of frozen replay evidence;
- schemas and configuration needed for reproducibility;
- manifests that record path, size, and SHA identities;
- small immutable audit evidence when its inclusion is explicitly justified.

The closed real Provider Physical Contract Probe 001 is intentionally included. Its 13 immutable files form a small, frozen evidence package rather than an active runtime directory. This decision does not apply automatically to later attempts.

## Content kept outside normal Git history

Normal Git history should not contain:

- virtual environments and Python caches;
- downloaded dependency wheels and recreatable provider metadata caches;
- large raw observational files and C0 probe payloads;
- quarantine raw datasets and interpretation-lockbox payloads;
- large derived row-level tables whose identities and methods are already bound by compact evidence;
- large regenerated batch and smoke outputs;
- temporary or staging files;
- future real metadata-bootstrap RAW, STAGING, ledger, or other runtime directories;
- disposable caches;
- files that can be recreated from frozen code and manifests without loss of research meaning.

Ignored files remain on the local filesystem. Exclusion from Git does not weaken their existing checksum, manifest, or provenance bindings.

## Storage audit and classification

The pre-initialization audit measured approximately 1.4 GiB in the working tree. The principal review targets were `c0/` at approximately 973 MiB and `oc3/` at approximately 405 MiB. Major local classes included the two virtual environments, C0 probe data, quarantine data, downloaded dependencies, and generated C0 reports.

Across the repository before exclusions, 264 files were at least 1 MiB, 31 were at least 5 MiB, 23 were at least 10 MiB, and 13 were at least 25 MiB. The large classes named above are excluded from normal Git history.

The following generated report payloads are excluded individually because they are large and reproducible from frozen code and inputs, while their compact human-readable reports and binding manifests remain eligible for Git:

- `c0/reports/operator_support/batch/`;
- `c0/reports/cached_support/batch/`;
- the corresponding local smoke payload directories;
- `C0_OPERATOR_SUPPORT_BATCH_RESULTS.json`;
- `C0_CACHED_SUPPORT_BATCH_RESULTS.json`;
- `C0_BOUNDED_AUDIT_RESULTS.json`.

The derived quarantine tables `CDS_IDENTITY_RECONCILIATION.parquet`, `SUBJECT_INDEX.parquet`, and `CONFOUND_AUDIT_C0.parquet` also remain filesystem evidence. Their reconstruction methods and file identities are retained through the repository's specifications, reports, and manifests.

## Future OC-3 metadata bootstrap

The entire `oc3/metadata_bootstrap/` runtime tree is ignored. A future real bootstrap may contain roughly 89.5 MB of raw provider bytes plus execution state. Those bytes remain outside normal Git history. Compact reviewed summaries or manifests stored outside the attempt runtime directory may be considered in a separate reviewed versioning task.

## Safety rules

- Do not commit credentials or secret-bearing environment files.
- Do not add a remote, push, or use network access as part of baseline creation.
- Do not use Git LFS filters in this repository unless a later reviewed policy explicitly introduces them.
- Audit the staged file count, total size, largest files, binary artifacts, ignored-runtime exclusions, and Probe 001 membership before every foundational baseline commit.
- Preserve the existing scientific and observational evidence in place; ignoring a file is not permission to delete or move it.
