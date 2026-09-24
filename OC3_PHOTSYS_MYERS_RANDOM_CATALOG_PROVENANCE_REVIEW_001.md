# OC3 Myers random-catalog provenance review 001

The governed action evaluated the exact Myers et al. (2023) ADS link published by the official Legacy Surveys DR9 files page.

- Literal URL: `https://ui.adsabs.harvard.edu/abs/2023AJ....165...50M/abstract`
- HTTP status: `405`
- Observed access control: AWS WAF requested a CAPTCHA
- Application-body bytes read: `0`
- Requests consumed: `1`
- Retries: `0`
- Terminal state: `MYERS_RANDOM_CATALOG_PROVENANCE_FAILED`
- Terminal reason: `PUBLIC_DOCUMENT_HTTP_STATUS_UNEXPECTED`
- Terminal SHA-256: `65b82e4117b4667a92ae1eb42237418303bde634b088729b87c657eb3f38bde0`
- Response-receipt SHA-256: `5e88a2665a35c38ba897b0aeade41dc5b9d05467a6766fe9872c50e36d879fd9`

The response body was not read because the status was outside the frozen contract. The action therefore establishes no claim from Myers et al. and discovers no new literal full-text or provenance link. The concretely identified peer-reviewed lead is inadequate in this execution environment.

The executor wrote a valid sealed terminal and receipt, then encountered a local post-terminal wrapper error because it passed the unsupported keyword `at_utc` to the offline transition helper. No network action was replayed. The existing terminal was verified and the normal governor CLI completed the transition with the observed deltas: one request, zero body bytes, zero retries. This implementation defect does not change the transport evidence or scientific result.

The official DR9 page remains the only evaluated source that names the summary product and states its three documented PHOTSYS categories. It does not expose a literal producer or aggregation link for that summary file. All astronomical and protected-value firewall counters remain zero.
