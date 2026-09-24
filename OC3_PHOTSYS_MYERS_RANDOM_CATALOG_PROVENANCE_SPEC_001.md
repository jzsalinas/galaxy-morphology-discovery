# OC3 Myers random-catalog provenance specification 001

## Prospective resource

The already acquired official Legacy Surveys DR9 files page directs work using its random catalogs to cite Myers et al. (2023) through the literal URL:

`https://ui.adsabs.harvard.edu/abs/2023AJ....165...50M/abstract`

This action evaluates exactly that peer-reviewed random-catalog provenance lead. It performs one sequential unauthenticated GET, forbids redirects and retries, accepts only HTML, and reads at most 1 MiB plus one cap-detection byte. No link discovered in the response is followed by this action.

## Offline analysis

After transport validation, the immutable body is searched offline for the named DR9 brick summary product, its version, the PHOTSYS field, outside-footprint wording, `desitarget`, supplemental-random terminology, and generation/aggregation terms. Bibliographic or full-text links embedded literally in the acquired page may be recorded as prospective leads. Presence of terms is discovery evidence only; it does not establish a producer pathway.

## Scientific boundary

This source can contribute only as `PEER_REVIEWED_RANDOM_CATALOG_GENERATION_PROVENANCE`. An abstract or landing page that does not trace the exact named product is inadequate for the required mapping. The action reads no astronomical product, PHOTSYS byte, BRICKNAME, BRICKID, or ROOT value. It cannot select a scientific outcome, create a resolver, or start Panel V2, P1, or morphological discovery.
