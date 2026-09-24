# OC3 Cross-ID Formalism Recovery Authorized Execution Report 001

## Outcome

The human standing authorization was materialized and validated, and the
mission was activated through the frozen Policy Core. Candidate 002 completed
successfully. The subsequent offline semantic-review action stopped after its
single-use permit was consumed because a layout-dependent literal marker did
not survive PDF text extraction contiguously.

The governed result is `STOP_REQUIRES_HUMAN`, blocker
`OFFLINE_REVIEW_CONSUMED_PERMIT_IMPLEMENTATION_MARKER_MISMATCH`. This is not
one of the four scientific terminals. Claim 9 and Claim 10 remain undecided.

## Authorization and first acquisition

- Standing authorization SHA-256:
  `33de71db462e46b404f7980dd9c0cff33685f414bcc63fac3b9e809d6a95450e`.
- Primary-evidence permit SHA-256:
  `9afd295f67a942ccc100805ddd21e17f17c2871ea6ac673f1bd5f21e09d2fc7d`.
- Acquisition terminal SHA-256:
  `45c51244a8cf63f699464eca7d562cdfee81b401c639246a89f89ad7572a9d59`.
- Transport evidence SHA-256:
  `580a6c635ca55b34f88df7f44da29825aceb28b8d3f5956fdf954d15d7a908d7`.
- arXiv v3 snapshot SHA-256:
  `c594358824153c3ec6a64273ed852eaf22fdca5c3537f221e9e59bd9d79faec2`.
- Direct ASP publisher PDF snapshot SHA-256:
  `ff0660168aab46f78221dd2d65f004b5b4b0e2a2139a151a2907203c618c079a`.

Actual acquisition accounting was two requests, 187,590 application-body
bytes, and zero retries. Both exact URLs, content types, final URLs, timestamps,
sizes, and response hashes are retained locally in the untracked runtime
evidence tree.

## Offline review stop

- Offline-review Candidate SHA-256:
  `21d102b95e3d14e262d54b6b9d30dd8f8b249d2b8d71fec2af5e4478dc2baa82`.
- Consumed permit SHA-256:
  `2807fefd6b6e93be45aa6377fdd65ab4dbf0be26a5ab6551e23b1a9dc0e3c7df`.
- STOP report SHA-256:
  `496b21aacfc894f2f62016741ff86c0780d55be453d3d603a97fe3de398b8d2c`.
- STOP ledger SHA-256:
  `c6458dacaa066cf97444539c9539d8688fad52f9e2aa623084865c7c5b81b38a`.
- Final state SHA-256:
  `71bf4d98174f06655e256d5ea09c76743906191740acd250ca798bebd29f994f`.

The source PDF was verified visually as a four-page ASP Conference Series
proceeding. Its text contains the relevant primary discussion, but the governed
review did not classify that discussion because execution failed before the
classification step. Permit replay is forbidden.

## Budgets and firewalls

Remaining budget: two requests and 8,201,018 application-body bytes. The
offline failure used zero network requests and zero body bytes. All firewall
counters remain zero: source rows, PHOTSYS, technical or photometric values,
pixels, morphology, labels, models, training, embeddings, clustering, Panel V3,
and P1. Matching, search-radius selection, and scientific-threshold selection
remain unstarted.

## Verification

- Focused final-state and lifecycle tests: `21/21` passed.
- Historical input tripwire: passed.
- Full synthetic-only offline regression: `1322/1322` passed, zero failures,
  zero skips, in `42.711` seconds.
- Regression log:
  `/tmp/oc3_cross_id_authorized_stop_full_regression.log`, SHA-256
  `740be8dd1d30f86ca2d4fa12e213930104f38ce2aee8ae1184893f978a7b3adc`.
- Policy Core manifest remains unchanged at
  `15ea858bd145bec305d86a786b8aa2bcf03942a424f7f1b35a5312360cb98f0b`.

The minimum human decision is whether to authorize a new separately frozen
offline-review action that uses whitespace-normalized or token-based evidence
markers. It needs no additional network source or budget increase.

