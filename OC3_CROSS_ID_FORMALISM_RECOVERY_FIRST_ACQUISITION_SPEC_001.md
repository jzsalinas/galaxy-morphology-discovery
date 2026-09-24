# OC3 Cross-ID Formalism Recovery First Acquisition Specification 001

The first material action is
`OC3-CROSS-ID-FORMALISM-PRIMARY-EVIDENCE-ACQUISITION-001`, scope
`PRIMARY_LITERATURE_ACQUISITION_ONLY`. It retrieves only the two literal
resources in the sealed manifest and records immutable response bodies,
requested/final URLs, status, content type, timestamps, sizes, and SHA-256.

The frozen cap is two requests and 4,718,592 response-body bytes: 524,288 for
the arXiv abstract HTML and 4,194,304 for the conference PDF. Concurrency is
one; retries, redirects, and resume are zero. The action performs transport and
bibliographic capture only. It cannot decide either reopened claim or a mission
terminal. A separate offline semantic action must inspect acquired evidence.

The executor must consume a SHA-derived, single-use permit issued by the
governor after a future standing human authorization. Partial evidence is
preserved locally and execution stops closed. No candidate-generation bound or
scientific decision threshold is selected.

