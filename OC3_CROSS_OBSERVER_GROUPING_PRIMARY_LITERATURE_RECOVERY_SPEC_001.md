# OC3 Cross-Observer Grouping Primary Literature Recovery Specification 001

Scope: `PRIMARY_CROSS_IDENTIFICATION_LITERATURE_RECOVERY_ONLY`.

Documentary Completion Attempt 003 acquired both corrected Data Lab schema
snapshots, then received HTTP 406 from the frozen `arxiv.org` PDF URL before
reading a response body.  That attempt is closed and is not replayed.

This new prospective action makes exactly one GET to the official arXiv export
host for the same immutable paper identifier, `0707.1611`.  The literal URL is
`https://export.arxiv.org/pdf/0707.1611`.  The executor sends the frozen request
header `User-Agent: Mozilla/5.0 (compatible; OC3Research/1.0)` and accepts only
HTTP 200, exact final URL identity, `application/pdf`, and a body beginning
with the PDF signature.  The body cap is 8,388,608 bytes.  Redirects, retries,
resume, mirrors, and substitutions are forbidden.

The action reads no astronomical source row or scientific value and makes no
semantic or grouping decision.  Success ends only at
`PRIMARY_CROSS_IDENTIFICATION_LITERATURE_ACQUIRED_PENDING_OFFLINE_REVIEW`.

