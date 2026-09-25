# OC3 Source-Metadata Acquisition Pilot Specification 001

Status: **FROZEN PROSPECTIVE DESIGN; INACTIVE**

Mission: `OC3-SOURCE-METADATA-ACQUISITION-PILOT-AUTONOMY-001`

Scope: `PROSPECTIVE_DR9_SOURCE_METADATA_ACQUISITION_ONLY`

Branch: `autopilot/source-metadata-acquisition-pilot`

Base terminal commit: `cf34a0efae274a198ac924f99da6135597a7d451`

## Scientific boundary

This mission asks whether the complete source support for the two frozen pilot targets can be acquired from the independent public DR9 north and south Tractor tables under an exact identity/astrometry projection. It is acquisition and integrity only. It does not calculate positional topology, matching, nearest neighbors, separations, radii, scientific thresholds or cross-observer equivalence.

The successful predecessor frame is bound without reinterpretation by final report SHA-256 `6002a9f901d39dabbd1c5a77255df1286ddb177981db627f4c0093cc9c698764`, final claim matrix SHA-256 `8b4fe975730f24174436cc21cf27c8c1ea280b0f14b6452714a9ce35a0cff65d`, and `PILOT_FRAME.json` SHA-256 `661f4d429f8fe0b6aa0104e093d79568d6f274935a7d9b0e78fb3dd45ae40292`.

The immutable targets are `2255p305/498957` and `1901p342/517112`. Their exact query support is the lexicographically ordered 14-brick union frozen in `QUERY_MANIFEST.json`. The reserved holdouts are `1075p337/514444` and `0381m012/323320`; all 16 bricks in their guards are forbidden source support. The two sets must remain disjoint before any transport construction.

## Public Data Lab contract

Only synchronous public-anonymous ADQL CSV requests to `https://datalab.noirlab.edu/query/query` are permitted. The public token identity is the literal `anonymous.0.0.anon_access`; local Data Lab credentials may not be read. Each GET contains the exact ordered parameters `adql`, `ofmt=csv`, `out=None`, `async=False`, `drop=False`, and `profile=default`, and exact headers `Content-Type: text/ascii`, `X-DL-TimeoutRequest: 300`, `X-DL-AuthToken: anonymous.0.0.anon_access`, plus the frozen project User-Agent.

Concurrency is one, retries and redirects are zero, resume is false, and timeout is 300 seconds. Request intent is charged before opening transport. Every body byte read is charged, including bytes preceding failure. Bodies are streamed to immutable local runtime evidence under per-response caps.

## Queries and gates

The immutable query manifest contains exactly five literal ADQL strings and their `ADQL_WHITESPACE_CANONICAL_SHA256_V1` hashes. Request order is schema, north count, south count, north rows, south rows. Schema failure stops after request one. A resource-bound count stops after both count requests. Rows are requested only after both domain totals are at most 150,000.

Allowed tables are exactly `ls_dr9.tractor_n` and `ls_dr9.tractor_s`. The combined table, later releases, sweeps, MyDB, crossmatch services, q3c and cone queries are forbidden. Schema metadata is restricted to the nine requested names. Source values are exactly, in order, `release,brickid,objid,brickname,brick_primary,ra,dec,ra_ivar,dec_ivar`.

The schema gate requires 18 unique table/column rows, exact table and column sets, and one prospectively allowlisted datatype spelling compatible with each semantic class. Count results contain exactly `brickname,source_count`; omitted target-support bricks mean zero without astronomical inference. Row requests use `TOP 150001`, exact predicates and `ORDER BY release,brickid,objid`. Returning 150001 rows is an integrity failure, never a sample.

Within each domain, source identities `(release,brickid,objid)` must be unique and strictly increasing, row counts must equal both aggregate and per-brick count evidence, `brickname` must belong only to target support, row `brickid` must equal the frame geometry mapping, and `brick_primary` must be one of the frozen true serializations. RA must be finite in `[0,360)` and DEC finite in `[-90,90]`. RA/DEC inverse variances are retained and classified only as `POSITIVE_FINITE`, `ZERO`, `MISSING` or `INVALID`; invalid values do not remove rows or invalidate acquisition.

## Budgets and outcomes

Per-response caps are 524,288 schema bytes; 65,536 for each count; and 32,505,856 for each row response. Parent limits are five requests and 67,108,864 bytes. There is no budget increase, substitution, sampling, truncation, retry or automatic resume.

Exactly one outcome is allowed: `SOURCE_METADATA_ACQUISITION_COMPLETED`, `SOURCE_METADATA_ACQUISITION_RESOURCE_BOUND`, `SOURCE_METADATA_ACQUISITION_INCONCLUSIVE`, or `SOURCE_METADATA_ACQUISITION_INTEGRITY_FAILED`. No outcome is preferred. `COMPLETED` establishes only complete bounded acquisition and integrity under the exact support; it does not establish any cross-observer association or astrophysical identity.

## Governance and firewall

The mission uses a frozen generic Policy Core, state-bound first candidate, standing human authorization, a single-use permit, exact supervisor/worker argv, actual accounting, append-only ledger, scientific terminal and `STOP_REQUIRES_HUMAN`. Bootstrap creates no authorization or permit and performs no network request.

Holdout count requests, holdout row requests and holdout source-derived cells must remain zero. Combined Tractor access, crossmatch, q3c, cone search, matching, angular separation, radii, search-bound or scientific-threshold selection, group IDs, PHOTSYS, TYPE, DCHISQ, Sersic/shape, photometry, photo-z, pixels, morphology, labels, models, training, embeddings, clustering, Panel V3 and P1 remain zero.
