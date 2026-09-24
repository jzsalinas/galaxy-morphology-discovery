# OC3 Cross-Observer Grouping Primary Article Recovery Specification 002

Scope: `PRIMARY_CROSS_IDENTIFICATION_ARTICLE_RECOVERY_ONLY`.

The two official arXiv endpoints returned HTTP 406 without bodies.  This new
prospective action makes one request to the Harvard ADS article service for
the exact primary-paper bibcode `2008ApJ...679..301B` at the literal URL
`https://articles.adsabs.harvard.edu/pdf/2008ApJ...679..301B`.

The action accepts only HTTP 200, the exact final URL, `application/pdf`, and a
PDF signature.  It sends the frozen header
`User-Agent: Mozilla/5.0 (compatible; OC3Research/1.0)`, has an 8,388,608-byte
cap, and permits no redirect, retry, resume, mirror fallback, or substitution.
It reads no astronomical source row or scientific value and makes no Gate
decision.  Success ends pending a new offline semantic review.

