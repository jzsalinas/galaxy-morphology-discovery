"""Closed vocabulary and uniform lexical matcher for offline review recovery."""
from __future__ import annotations

import re
from typing import Iterable

from .cross_observer_grouping import *  # stable integrity/canonical JSON helpers

MISSION_ID = "OC3-CROSS-ID-OFFLINE-REVIEW-RECOVERY-AUTONOMY-001"
STAGE_ID = "OC3-CROSS-ID-OFFLINE-SEMANTIC-REVIEW-RECOVERY-001"
SCOPE = "OFFLINE_PRIMARY_EVIDENCE_REVIEW_RECOVERY_ONLY"
NORMALIZATION_ALGORITHM = "NORMALIZED_WHITESPACE_TEXT_V1"
TOKENIZER_ALGORITHM = "UNICODE_ALNUM_TOKEN_SEQUENCE_V1"

REOPENED_CLAIMS = (
    "CROSS_IDENTIFICATION_FORMALISM_ASSUMPTIONS",
    "BOUNDED_PILOT_SPECIFIABLE_WITHOUT_THRESHOLD",
)
FORMALISM_CLAIMS = (
    "A_BAYESIAN_PROBABILISTIC",
    "B_SAME_SOURCE_VS_SEPARATE_SOURCE",
    "C_SYMMETRY",
    "D_POSITIONAL_UNCERTAINTY_MODEL",
    "E_KNOWN_POSITIONAL_UNCERTAINTIES",
    "F_CIRCULAR_GAUSSIAN_SPHERICAL_APPROXIMATIONS",
    "G_PRIORS",
    "H_POINT_SOURCE_ASSUMPTION",
    "I_OPTIONAL_PHYSICAL_PROPERTIES",
    "J_EXTENDED_DR9_GALAXY_TRANSFER_LIMIT",
    "K_NO_ARBITRARY_MATCH_DECISION_RADIUS_REQUIREMENT",
)
EPISTEMIC_LAYERS = (
    "FORMALISM_FACT", "DR9_DATA_FACT", "PROJECT_SUITABILITY_INFERENCE",
)
BOUND_TYPES = (
    "CANDIDATE_GENERATION_SEARCH_BOUND", "SCIENTIFIC_MATCH_DECISION_THRESHOLD",
)
TERMINAL_OUTCOMES = (
    "CROSS_ID_FORMALISM_RECOVERED_PILOT_SPECIFIABLE",
    "CROSS_ID_FORMALISM_RECOVERED_PILOT_STILL_UNRESOLVED",
    "CROSS_ID_FORMALISM_EVIDENCE_INCONCLUSIVE",
    "CROSS_ID_FORMALISM_CONFLICT",
)

# Frozen action evidence strings. Every entry is evaluated through marker_occurrences.
MARKERS = (
    ("ASP_SERIES_VOLUME", "ASP Conference Series, Vol. 394"),
    ("ASP_YEAR", "2008"),
    ("ASP_FIRST_PAGE", "165"),
    ("TITLE", "Probabilistic Cross-Identification of Astronomical Sources"),
    ("AUTHOR_BUDAVARI", "Budava"),
    ("AUTHOR_NIETO_SANTISTEBAN", "Nieto-Santisteban"),
    ("POINT_SOURCES", "astronomical point sources"),
    ("BAYESIAN_APPROACH", "Bayesian approach"),
    ("NOT_SYMMETRIC", "not symmetric"),
    ("SYMMETRIC_ALGORITHMS", "algorithms that are symmetric"),
    ("SAME_SOURCE", "same source"),
    ("SEPARATE_SOURCES", "separate sources"),
    ("NORMAL_DISTRIBUTION", "normal distribution"),
    ("PROBABILITY_DENSITY", "probability density function"),
    ("SPHERICAL_NORMAL", "spherical normal distribution"),
    ("INVERSE_COVARIANCE", "inverse of the covariance matrix"),
    ("PRIOR_PROBABILITY", "prior probability"),
    ("PHYSICAL_PROPERTIES", "physical properties"),
    ("POSTERIOR_PROBABILITY", "posterior probability"),
    ("SIMPLE_RADIUS_THRESHOLDS", "simple radius thresholds"),
    ("MAXIMUM_SEARCH_RADIUS", "maximum search radius"),
    ("CUSTOM_THRESHOLDS", "custom thresholds"),
)


def normalize_whitespace(text: str) -> str:
    """Collapse every maximal Unicode whitespace sequence to one ASCII space."""
    if not isinstance(text, str):
        raise TypeError("TEXT_REQUIRED")
    return " ".join(text.split())


def lexical_tokens(text: str) -> tuple[str, ...]:
    """Return case-sensitive maximal Unicode alphanumeric sequences."""
    return tuple(re.findall(r"[^\W_]+", normalize_whitespace(text), flags=re.UNICODE))


def marker_occurrences(text: str, marker: str) -> tuple[int, ...]:
    """Find exact ordered contiguous token occurrences using one universal rule."""
    haystack, needle = lexical_tokens(text), lexical_tokens(marker)
    if not needle:
        raise ValueError("EMPTY_MARKER")
    width = len(needle)
    return tuple(i for i in range(len(haystack) - width + 1)
                 if haystack[i:i + width] == needle)


def evaluate_all_markers(text: str, markers: Iterable[tuple[str, str]] = MARKERS) -> list[dict[str, object]]:
    rows = []
    for marker_id, literal in markers:
        positions = marker_occurrences(text, literal)
        rows.append({"marker_id": marker_id, "literal": literal,
                     "match_count": len(positions), "token_positions": list(positions),
                     "matched": bool(positions)})
    return rows


def terminal_outcome(claim9: str, claim10: str) -> str:
    if "CONFLICT" in (claim9, claim10):
        return "CROSS_ID_FORMALISM_CONFLICT"
    if claim9 == "SUPPORTED" and claim10 == "SUPPORTED":
        return "CROSS_ID_FORMALISM_RECOVERED_PILOT_SPECIFIABLE"
    if claim9 == "SUPPORTED" and claim10 == "INCONCLUSIVE":
        return "CROSS_ID_FORMALISM_RECOVERED_PILOT_STILL_UNRESOLVED"
    return "CROSS_ID_FORMALISM_EVIDENCE_INCONCLUSIVE"


def validate_claim_vocabulary() -> None:
    if len(FORMALISM_CLAIMS) != 11 or len(set(FORMALISM_CLAIMS)) != 11:
        raise ValueError("FORMALISM_CLAIM_VOCABULARY_INVALID")
    if BOUND_TYPES[0] == BOUND_TYPES[1]:
        raise ValueError("SEARCH_BOUND_THRESHOLD_COLLAPSED")
    if len(MARKERS) != len({item[0] for item in MARKERS}):
        raise ValueError("MARKER_ID_DUPLICATE")
