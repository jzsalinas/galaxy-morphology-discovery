# OC3 Cross-Observer Grouping Documentary Completion Specification 003

Scope: `PUBLIC_DOCUMENTARY_AND_SCHEMA_METADATA_COMPLETION_ONLY`.

This prospective action responds to the immutable Candidate 002 failure and
the completed Data Lab response diagnostic.  It does not replay Candidate 002.
The diagnostic body establishes that `TAP_SCHEMA.columns` rejects the
nonexistent `schema_name` column.  The corrected metadata queries therefore
use fully qualified `table_name` identities and the columns query omits
`schema_name`.

The action acquires exactly three hashed response snapshots: corrected
`TAP_SCHEMA.tables` metadata, corrected `TAP_SCHEMA.columns` metadata, and the
previously unattempted primary cross-identification preprint.  The three
Legacy Survey DR9 documentation snapshots already acquired by Candidate 002
remain separate immutable inputs for the later review and are not downloaded
again.

The action is sequential, uses at most three requests and 9,437,184 body
bytes, and permits no redirects, retries, resume, source rows, scientific
values, matching, threshold selection, or grouping decision.  Successful
transport ends only at
`DOCUMENTARY_COMPLETION_ACQUIRED_PENDING_OFFLINE_SEMANTIC_REVIEW`.

Success requires exact URL identity, HTTP 200, an allowlisted content type,
per-resource and aggregate byte caps, immutable local publication, and
post-publication SHA-256 verification.  Acquisition does not pass the
documentary Gate.  A separately contracted offline review must combine these
three snapshots with the four preserved Candidate 002 snapshots and the
diagnostic provenance, then classify all ten frozen claims.

