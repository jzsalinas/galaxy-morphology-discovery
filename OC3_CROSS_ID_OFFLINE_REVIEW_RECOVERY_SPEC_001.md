# OC3 Cross-ID Offline Review Recovery Specification 001

## Status and question

**Mission:** `OC3-CROSS-ID-OFFLINE-REVIEW-RECOVERY-AUTONOMY-001`
**Scope:** `OFFLINE_PRIMARY_EVIDENCE_REVIEW_RECOVERY_ONLY`
**Status:** prospective, frozen, inactive; no standing authorization or permit

Can the already acquired immutable primary evidence be reviewed deterministically
with layout-invariant lexical normalization, without changing any scientific
criterion, to decide the two claims left undecided by the stopped predecessor?

The predecessor `OC3-CROSS-ID-FORMALISM-RECOVERY-AUTONOMY-001` is immutable at
commit `24e9b6d6a11a9f92b19f0af068bd98d79c4e2c02`, state
`STOP_REQUIRES_HUMAN`, blocker
`OFFLINE_REVIEW_CONSUMED_PERMIT_IMPLEMENTATION_MARKER_MISMATCH`. Its consumed
offline permit SHA-256
`2807fefd6b6e93be45aa6377fdd65ab4dbf0be26a5ab6551e23b1a9dc0e3c7df`
must never be replayed. A stopped inactive mission cannot register another action,
so this recovery is a separate mission rather than a continuation or Policy Core
amendment.

## Closed inputs and inherited status

Only these local primary-evidence bindings may be read by the future action:

- arXiv v3 body: `c594358824153c3ec6a64273ed852eaf22fdca5c3537f221e9e59bd9d79faec2`;
- ASP proceeding body: `ff0660168aab46f78221dd2d65f004b5b4b0e2a2139a151a2907203c618c079a`;
- transport evidence: `580a6c635ca55b34f88df7f44da29825aceb28b8d3f5956fdf954d15d7a908d7`;
- acquisition terminal: `45c51244a8cf63f699464eca7d562cdfee81b401c639246a89f89ad7572a9d59`.

Their acquisition used two requests, 187,590 application-body bytes and zero
retries. Reacquisition is forbidden. Both scientific claims remain `UNDECIDED`:
`CROSS_IDENTIFICATION_FORMALISM_ASSUMPTIONS` and
`BOUNDED_PILOT_SPECIFIABLE_WITHOUT_THRESHOLD`. The predecessor failure is
`LAYOUT_DEPENDENT_MARKER_MATCHING_FAILURE`, not missing evidence and not a
scientific classification.

## Unchanged scientific criteria

Criteria A-K and their decision rules are incorporated unchanged from
`OC3_CROSS_ID_FORMALISM_RECOVERY_SPEC_001.md` and
`OC3_CROSS_ID_FORMALISM_RECOVERY_OFFLINE_SEMANTIC_REVIEW_SPEC_001.md`:

- A Bayesian/probabilistic method;
- B same-source versus separate-source hypotheses;
- C symmetry;
- D positional-uncertainty model and domain;
- E known positional uncertainties;
- F circular/Gaussian/tangent-plane/spherical approximations and limits;
- G priors;
- H point-source assumption;
- I optional physical properties;
- J transfer limit for extended DR9 galaxies;
- K absence of a required arbitrary angular match-decision radius.

Claim 9 is `SUPPORTED` only when A-I and K have required primary support and the
point-source limitation is explicit. J may remain `INCONCLUSIVE` as a project
inference while Claim 9 is supported, provided the transfer limitation is retained.
Claim 10 is evaluated second and uses the unchanged five conditions in the
predecessor offline-review specification. Missing mandatory support is
`INCONCLUSIVE`; material contradiction is `CONFLICT`.

## Layout-invariant representation

`NORMALIZED_WHITESPACE_TEXT_V1` is exactly `" ".join(text.split())`: every
maximal Unicode whitespace sequence becomes one ASCII space and leading/trailing
whitespace is removed. The future action records SHA-256 for raw `pdftotext`
output and normalized output.

`UNICODE_ALNUM_TOKEN_SEQUENCE_V1` applies the same rule to every marker and both
documents: normalize whitespace, then extract every maximal nonempty sequence of
Unicode alphanumeric characters using the Python expression
`tuple(re.findall(r"[^\\W_]+", normalized_text, flags=re.UNICODE))`. Matching is
case-sensitive and requires an exact contiguous ordered token subsequence.
Punctuation, underscore and whitespace are separators. There is no stemming,
lemmatization, case folding, synonym expansion, spelling correction, semantic or
fuzzy similarity, OCR, model inference, or special-case marker rule. Hyphenated
line breaks are not silently dehyphenated. The known covariance phrase is one
ordinary regression fixture.

Bibliographic identity remains mandatory: arXiv title, identifier `0707.1611`, v3
metadata and authors; and the ASP title, authors, series, volume 394, page 165 and
year 2008.

## Authority, budgets, firewall and outcomes

Only `FROZEN_PROJECT_TERMINALS_AND_SPECIFICATIONS` and
`BOUND_LOCAL_PRIMARY_LITERATURE_SNAPSHOTS` are allowed. Network requests,
application-body bytes and retries are zero; concurrency is one. Local execution
is bounded to the two bodies, two compact records, one `pdftotext` process, and
compact outputs. No source rows, matching, radius, scientific threshold, PHOTSYS,
technical values, pixels, morphology, labels, models, training, embeddings,
clustering, Panel V3, or P1 are authorized.

The future action must produce `EXTRACTION_PROVENANCE.json`,
`MARKER_EVIDENCE.json`, `CLAIM_MATRIX.json`, `REVIEW_REPORT.md`, and
`TERMINAL.json`. Full extracted text remains untracked runtime data.

Exactly one terminal outcome is allowed:

- `CROSS_ID_FORMALISM_RECOVERED_PILOT_SPECIFIABLE`;
- `CROSS_ID_FORMALISM_RECOVERED_PILOT_STILL_UNRESOLVED`;
- `CROSS_ID_FORMALISM_EVIDENCE_INCONCLUSIVE`;
- `CROSS_ID_FORMALISM_CONFLICT`.

`CANDIDATE_GENERATION_SEARCH_BOUND` remains distinct from
`SCIENTIFIC_MATCH_DECISION_THRESHOLD`; neither is selected and no numeric value
may be produced. Any scope expansion, new authority, Policy Core mutation after
activation, integrity conflict, or unexpected observation requires
`STOP_REQUIRES_HUMAN`.
