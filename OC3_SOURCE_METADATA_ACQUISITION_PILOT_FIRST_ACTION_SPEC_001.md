# OC3 Source-Metadata Acquisition Pilot First Action 001

This prospective action is `BOUNDED_DR9_SOURCE_METADATA_ACQUISITION`, stage `OC3-SOURCE-METADATA-ACQUISITION-PILOT-001`, scope `PROSPECTIVE_DR9_SOURCE_METADATA_ACQUISITION_ONLY`.

It binds the successful `PILOT_FRAME.json`, the exact immutable query manifest, and a public-anonymous synchronous Data Lab transport. It may issue at most five sequential GET requests in the exact order schema, north count, south count, north rows, south rows. Counts gate rows; per-response and parent limits are enforced while streaming; retries, redirects and resume are disabled.

The only source-value projection is `release,brickid,objid,brickname,brick_primary,ra,dec,ra_ivar,dec_ivar`. Runtime raw CSV bodies remain local and untracked. Compact evidence records transport, schema, counts, row integrity, terminal state and exact accounting.

No holdout support, matching, angular separation, radius, scientific threshold, group ID, morphology, Panel V3 or P1 operation is authorized.
