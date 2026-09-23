"""Bounded public-document/source research for PHOTSYS raw byte 0x00.

All preflight functions are offline.  The only production network entry point
requires an exact sealed candidate plus a separate final human authorization.
The transport is closed to the five literal resources in the frozen manifest
and has no astronomical-data URL or FITS table reader capability.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import http.client
from io import BytesIO
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tarfile
from typing import Callable, Iterable
from urllib.parse import urlsplit

from .core import canonical, implementation_hash
from .galaxy_eligibility_photsys_authority_probe import (
    PROJECT, file_sha256, load_canonical_json, sealed, sha256_bytes,
    validate_sealed, write_json_immutable,
)


STAGE_ID = "OC3-GALAXY-ELIGIBILITY-PHOTSYS-ZERO-BYTE-SEMANTIC-PROVENANCE-001"
SCOPE = "PHOTSYS_ZERO_BYTE_SEMANTIC_PROVENANCE_ONLY"
INITIAL = "PHOTSYS_ZERO_BYTE_SEMANTIC_PROVENANCE_RESEARCH_NOT_STARTED"
READY = "READY_AT_PUBLIC_DOCUMENTARY_RESEARCH_BOUNDARY"
INTEGRITY_STOP = "PHOTSYS_ZERO_BYTE_RESEARCH_INTEGRITY_STOP"

PROVEN = "PHOTSYS_0x00_OUTSIDE_SEMANTICS_PROVEN"
MISMATCH_SUPPORTED = "PHOTSYS_0x00_REPRESENTATION_MISMATCH_BUT_OUTSIDE_MAPPING_SUPPORTED"
INCONCLUSIVE = "PHOTSYS_0x00_SEMANTICS_INCONCLUSIVE"
CONFLICT = "PHOTSYS_DOCUMENTATION_PHYSICAL_CONFLICT_UNRESOLVED"
OUTCOMES = (PROVEN, MISMATCH_SUPPORTED, INCONCLUSIVE, CONFLICT)

SPEC_PATH = PROJECT / "OC3_PHOTSYS_ZERO_BYTE_SEMANTIC_PROVENANCE_SPEC.md"
SPEC_SHA256 = "4b2db6523e9acc3add101199966e6fe372c6105d74edd59089eae1fdc09cc614"
HISTOGRAM_PATH = PROJECT / (
    "oc3/photsys_byte_histogram/"
    "OC3-GALAXY-ELIGIBILITY-PHOTSYS-BYTE-HISTOGRAM-001/"
    "OC3_PHOTSYS_RAW_BYTE_HISTOGRAM_001.json"
)
HISTOGRAM_SHA256 = "010e2c4a7465d0b08bc3c6df1e8e52a4eafa0c497a7d030038f34cc377e54510"
HISTOGRAM_PAYLOAD_SHA256 = "3ebe3094819363b152e21c9ebcd47144f665300548a878a84108b9b5e66e1e47"
HISTOGRAM_SEAL = "edabd5a4cc3c0eecd4003871c93f7eb32480a571f5fb4f57678bad849cc1a681"
HISTOGRAM_TERMINAL_PATH = HISTOGRAM_PATH.parent / "TERMINAL.json"
HISTOGRAM_TERMINAL_SHA256 = "bb9e7a6d05560deaeba4aa11803213cc46530768071a1d942736607f280216ed"
V1_CONSISTENCY_PATH = HISTOGRAM_PATH.parent / "V1_CONSISTENCY.json"
V1_CONSISTENCY_SHA256 = "af1134cd8f57a33675ff1a5059cb90e973eaefc54a0a169acfab5b05c0a29d80"
V1_REVIEW_PATH = PROJECT / "OC3_PHOTSYS_SELECTIVE_VALUE_VALIDATION_POST_EXECUTION_REVIEW.md"
V1_REVIEW_SHA256 = "6b689ba5aff89131d09506ce0827c2aabc59fad3935d3740db3eee019de9d772"

MANIFEST_PATH = PROJECT / "oc3/INPUTS/OC3_PHOTSYS_ZERO_BYTE_PROVENANCE_RESOURCE_MANIFEST_001.json"
CANDIDATE_PATH = PROJECT / "oc3/INPUTS/OC3_PHOTSYS_ZERO_BYTE_PROVENANCE_RESEARCH_CANDIDATE_001.json"
AUTHORIZATION_PATH = PROJECT / "oc3/OC3_PHOTSYS_ZERO_BYTE_PROVENANCE_RESEARCH_FINAL_AUTHORIZATION_001.json"
OUTPUT_ROOT = PROJECT / "oc3/photsys_zero_byte_provenance" / STAGE_ID

TAG = "0.48.0"
EXPECTED_TAG_OBJECT = "1957b46481368c3b386a2113dc734538650c492c"
EXPECTED_COMMIT = "dd30297f9d50fcb7bbba57d79d4b8fc86cb35701"
ARCHIVE_PREFIX = f"desitarget-{EXPECTED_COMMIT}"
ARCHIVE_URL = f"https://codeload.github.com/desihub/desitarget/tar.gz/{EXPECTED_COMMIT}"
MANDATORY_SOURCE_PATHS = (
    "py/desitarget/randoms.py", "bin/select_randoms", "bin/supplement_randoms",
    "py/desitarget/io.py", "doc/changes.rst",
)
SEARCH_TERMS = (
    "survey-bricks", "survey-bricks-dr9-randoms", "AREA_PER_BRICK", "PHOTSYS",
    "supplement_randoms", "zeros=True", "write_randoms", "resolve",
)
NAMED_GENERATOR_NOT_FOUND = "DESITARGET_0_48_0_NAMED_SUMMARY_GENERATOR_NOT_FOUND"
NAMED_PROVENANCE_UNRESOLVED = "NAMED_PRODUCT_GENERATION_PROVENANCE_UNRESOLVED"

EVIDENCE_CLASSES = (
    "Observed fact", "Official documentation", "FITS standard",
    "Producer source", "Independent footprint evidence", "Inference",
)
STATUSES = ("SUPPORTED", "CONTRADICTED", "UNRESOLVED", "NOT_APPLICABLE")

REQUEST_CAP = 5
BODY_CAP = 20 * 1024 * 1024
RETRIES_PER_RESOURCE = 0
CONCURRENCY = 1
MAX_ARCHIVE_MEMBERS = 10_000
MAX_EXTRACTED_BYTES = 96 * 1024 * 1024


class ProvenanceError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass
class FirewallCounters:
    public_documentary_source_requests: int = 0
    public_documentary_source_body_bytes: int = 0
    application_body_bytes_read: int = 0
    astronomical_data_GETs: int = 0
    real_PHOTSYS_bytes_observed: int = 0
    BRICKNAME_values_observed: int = 0
    BRICKID_values_observed: int = 0
    ROOT_values_observed: int = 0

    def object(self) -> dict[str, int]:
        return asdict(self)

    def data_clean(self) -> bool:
        return all(getattr(self, name) == 0 for name in (
            "astronomical_data_GETs", "real_PHOTSYS_bytes_observed",
            "BRICKNAME_values_observed", "BRICKID_values_observed", "ROOT_values_observed",
        ))


def _resources() -> list[dict[str, object]]:
    return [
        {
            "accepted_content_types": ["application/pdf"],
            "byte_cap": 4 * 1024 * 1024,
            "evidence_class": "FITS standard",
            "expected_content_type": "application/pdf",
            "host": "fits.gsfc.nasa.gov",
            "id": "FITS_STANDARD_4_0",
            "immutable_revision_required": True,
            "purpose": "Normative BINTABLE character representation semantics",
            "redirect_rule": "NO_REDIRECT",
            "url": "https://fits.gsfc.nasa.gov/standard40/fits_standard40aa-le.pdf",
            "version": "FITS Standard 4.0",
        },
        {
            "accepted_content_types": ["text/html"],
            "byte_cap": 1024 * 1024,
            "evidence_class": "Official documentation",
            "expected_content_type": "text/html",
            "host": "www.legacysurvey.org",
            "id": "LEGACY_SURVEY_DR9_FILES",
            "immutable_revision_required": False,
            "purpose": "Published semantics for survey-bricks-dr9-randoms-0.48.0.fits",
            "redirect_rule": "NO_REDIRECT",
            "temporal_limitation": "Current page is not yet proven identical to the DR9-production-time page",
            "url": "https://www.legacysurvey.org/dr9/files/",
        },
        {
            "accepted_content_types": ["application/json", "application/vnd.github+json"],
            "byte_cap": 128 * 1024,
            "evidence_class": "Producer source",
            "expected_content_type": "application/json",
            "host": "api.github.com",
            "id": "DESITARGET_TAG_REF",
            "immutable_revision_required": True,
            "purpose": "Independently resolve the 0.48.0 ref to its annotated tag object",
            "redirect_rule": "NO_REDIRECT",
            "url": "https://api.github.com/repos/desihub/desitarget/git/ref/tags/0.48.0",
        },
        {
            "accepted_content_types": ["application/json", "application/vnd.github+json"],
            "byte_cap": 128 * 1024,
            "evidence_class": "Producer source",
            "expected_content_type": "application/json",
            "host": "api.github.com",
            "id": "DESITARGET_TAG_OBJECT",
            "immutable_revision_required": True,
            "purpose": "Independently resolve the annotated tag object to a commit",
            "redirect_rule": "NO_REDIRECT",
            "url": "https://api.github.com/repos/desihub/desitarget/git/tags/1957b46481368c3b386a2113dc734538650c492c",
        },
        {
            "accepted_content_types": ["application/gzip", "application/x-gzip", "application/octet-stream"],
            "archive_identity": {
                "commit": EXPECTED_COMMIT,
                "repository": "desihub/desitarget",
                "top_level_prefix": ARCHIVE_PREFIX,
            },
            "byte_cap": 14 * 1024 * 1024,
            "evidence_class": "Producer source",
            "expected_content_type": "application/gzip",
            "host": "codeload.github.com",
            "id": "DESITARGET_0_48_0_ARCHIVE",
            "immutable_revision_required": True,
            "purpose": "Complete exact-commit source tree for deterministic offline search",
            "redirect_rule": "NO_REDIRECT",
            "url": ARCHIVE_URL,
        },
    ]


def build_resource_manifest() -> dict[str, object]:
    return sealed({
        "broad_crawling": False,
        "mirror_substitution": False,
        "resources": _resources(),
        "schema_version": "OC3_PHOTSYS_ZERO_BYTE_PROVENANCE_RESOURCE_MANIFEST_001",
        "scope": SCOPE,
        "stage_id": STAGE_ID,
    })


def validate_resource_manifest(path: Path = MANIFEST_PATH) -> dict[str, object]:
    try:
        value = validate_sealed(load_canonical_json(path))
    except Exception as exc:
        raise ProvenanceError("RESOURCE_MANIFEST_INVALID") from exc
    if value != build_resource_manifest():
        raise ProvenanceError("RESOURCE_MANIFEST_INVALID")
    resources = value["resources"]
    if sum(int(item["byte_cap"]) for item in resources) > BODY_CAP:
        raise ProvenanceError("RESOURCE_MANIFEST_INVALID")
    return value


def validate_frozen_inputs() -> dict[str, object]:
    expected = {
        SPEC_PATH: SPEC_SHA256, HISTOGRAM_PATH: HISTOGRAM_SHA256,
        HISTOGRAM_TERMINAL_PATH: HISTOGRAM_TERMINAL_SHA256,
        V1_CONSISTENCY_PATH: V1_CONSISTENCY_SHA256, V1_REVIEW_PATH: V1_REVIEW_SHA256,
    }
    for path, digest in expected.items():
        if not path.is_file() or file_sha256(path) != digest:
            raise ProvenanceError("FROZEN_INPUT_MISMATCH")
    histogram = validate_sealed(load_canonical_json(HISTOGRAM_PATH))
    counts = histogram.get("histogram_counts")
    if (histogram.get("sealed") != HISTOGRAM_SEAL or not isinstance(counts, list) or
            len(counts) != 256 or sha256_bytes(canonical(counts)) != HISTOGRAM_PAYLOAD_SHA256 or
            counts[0] != 330_208 or counts[0x4E] != 82_897 or
            counts[0x53] != 249_069 or sum(counts) != 662_174 or
            any(value for index, value in enumerate(counts) if index not in (0, 0x4E, 0x53))):
        raise ProvenanceError("FROZEN_INPUT_MISMATCH")
    validate_resource_manifest()
    return {
        "firewall": FirewallCounters().object(), "histogram_rows": 662_174,
        "network_requests": 0, "scope": SCOPE, "stage_id": STAGE_ID,
        "state": "PHOTSYS_ZERO_BYTE_PROVENANCE_INPUTS_VALIDATED",
    }


def initial_claim_matrix() -> list[dict[str, str]]:
    rows = [
        ("Observed fact", "The only nonzero raw bins are 0x00, 0x4e, and 0x53 with frozen counts", "SUPPORTED"),
        ("Observed fact", "V1 count cross-checks pass", "SUPPORTED"),
        ("Official documentation", "Official DR9 documentation defines N, S, and literal space outside-footprint PHOTSYS categories", "UNRESOLVED"),
        ("FITS standard", "First-character 0x00 in a BINTABLE A field has FITS_NULL_STRING representation semantics", "UNRESOLVED"),
        ("FITS standard", "0x20 is ASCII space and is distinct from 0x00", "UNRESOLVED"),
        ("Producer source", "Exact desitarget 0.48.0 zero-initializes PHOTSYS |S1 before assignment", "UNRESOLVED"),
        ("Producer source", "Exact outside-footprint rows retain or receive byte 0x00", "UNRESOLVED"),
        ("Producer source", "Exact named-product generation path has no later PHOTSYS rewrite", "UNRESOLVED"),
        ("Independent footprint evidence", "Non-circular footprint evidence agrees with aggregate behavior", "NOT_APPLICABLE"),
        ("Inference", "RAW_PHOTSYS_0x00 maps to DOCUMENTED_OUTSIDE_FOOTPRINT", "UNRESOLVED"),
    ]
    return [{"claim": claim, "evidence_class": cls, "status": status} for cls, claim, status in rows]


def validate_claim_matrix(rows: object) -> list[dict[str, str]]:
    if not isinstance(rows, list) or len(rows) != len(initial_claim_matrix()):
        raise ProvenanceError("CLAIM_MATRIX_INVALID")
    for row in rows:
        if (not isinstance(row, dict) or set(row) != {"claim", "evidence_class", "status"} or
                row["evidence_class"] not in EVIDENCE_CLASSES or row["status"] not in STATUSES):
            raise ProvenanceError("CLAIM_MATRIX_INVALID")
    if [row["claim"] for row in rows] != [row["claim"] for row in initial_claim_matrix()]:
        raise ProvenanceError("CLAIM_MATRIX_INVALID")
    return rows


def completed_claim_matrix(*, legacy: dict[str, object], fits: dict[str, object],
                           trace: dict[str, object], named_generation_proven: bool) -> list[dict[str, str]]:
    rows = initial_claim_matrix()
    if all(legacy.get("meanings", {}).values()):
        rows[2]["status"] = "SUPPORTED"
    if (fits.get("BINTABLE_A_NULL_RULE") is True and
            fits.get("ASCII_NULL_0x00") is True):
        rows[3]["status"] = "SUPPORTED"
    if (fits.get("ASCII_NULL_0x00") is True and
            fits.get("ASCII_SPACE_0x20") is True and
            fits.get("x00_distinct_from_x20") is True):
        rows[4]["status"] = "SUPPORTED"
    # A dtype and assignments do not prove initialization, the outside branch,
    # byte preservation, or the named released product.  Those claims remain
    # unresolved unless their stronger, exact provenance predicates are met.
    if trace.get("zero_initialization_before_assignment_proven") is True:
        rows[5]["status"] = "SUPPORTED"
    if trace.get("outside_rows_raw_0x00_proven") is True:
        rows[6]["status"] = "SUPPORTED"
    if named_generation_proven and trace.get("serialization_preserves_PHOTSYS_proven") is True:
        rows[7]["status"] = "SUPPORTED"
    if all(rows[index]["status"] == "SUPPORTED" for index in (2, 3, 4, 5, 6, 7)):
        rows[9]["status"] = "SUPPORTED"
    return validate_claim_matrix(rows)


def outcome_gate(*, official_categories: bool, fits_representation: bool,
                 exact_producer: bool, exact_outside_path: bool,
                 serialization_preserves: bool, named_product_generation: bool,
                 documentary_physical_mismatch: bool, unresolved_conflict: bool,
                 zero_initialization: bool = False, count_coincidence: bool = True) -> str:
    # The final two inputs are deliberately non-gating consistency evidence.
    del zero_initialization, count_coincidence
    if unresolved_conflict:
        return CONFLICT
    complete = all((official_categories, fits_representation, exact_producer,
                    exact_outside_path, serialization_preserves, named_product_generation))
    if not complete:
        return INCONCLUSIVE
    return MISMATCH_SUPPORTED if documentary_physical_mismatch else PROVEN


def exact_command(project: Path = PROJECT) -> list[str]:
    project = Path(project).resolve()
    return [
        str(project / "oc3/.venv/bin/python"),
        str(project / "oc3/oc3_photsys_zero_byte_provenance.py"),
        "--research-zero-byte-provenance", "--execute-public-documentary-research",
        "--candidate", str(project / CANDIDATE_PATH.relative_to(PROJECT)),
        "--authorization", str(project / AUTHORIZATION_PATH.relative_to(PROJECT)),
        "--output-directory", str(project / OUTPUT_ROOT.relative_to(PROJECT)),
    ]


def build_candidate(implementation_aggregate: str) -> dict[str, object]:
    validate_frozen_inputs()
    command = exact_command()
    return sealed({
        "candidate_state": "PENDING_HUMAN_REVIEW",
        "command_argv": command,
        "command_argv_sha256": sha256_bytes(canonical(command)),
        "desitarget_binding_to_verify": {
            "archive_url": ARCHIVE_URL,
            "expected_annotated_tag_object": EXPECTED_TAG_OBJECT,
            "expected_resolved_commit": EXPECTED_COMMIT,
            "repository": "desihub/desitarget", "tag": TAG,
            "status": "UNVERIFIED_UNTIL_AUTHORIZED_RESEARCH",
        },
        "evidence_classes": list(EVIDENCE_CLASSES),
        "final_authorization_path": str(AUTHORIZATION_PATH),
        "final_authorization_present": False,
        "firewall": FirewallCounters().object(),
        "frozen_observation": {
            "counts": {"0x00": 330_208, "0x4e": 82_897, "0x53": 249_069},
            "histogram_payload_sha256": HISTOGRAM_PAYLOAD_SHA256,
            "histogram_sha256": HISTOGRAM_SHA256,
            "histogram_terminal_sha256": HISTOGRAM_TERMINAL_SHA256,
            "row_level_evidence": False, "total": 662_174,
            "v1_consistency_sha256": V1_CONSISTENCY_SHA256,
        },
        "implementation_aggregate": implementation_aggregate,
        "network_caps": {
            "astronomical_data_GETs": 0, "body_bytes": BODY_CAP,
            "concurrency": CONCURRENCY, "per_resource_retries": RETRIES_PER_RESOURCE,
            "public_documentary_source_requests": REQUEST_CAP,
        },
        "outcome_gate": list(OUTCOMES),
        "resource_manifest": {
            "path": str(MANIFEST_PATH), "sha256": file_sha256(MANIFEST_PATH),
        },
        "superseded_candidate": {
            "authorization_prohibited": True,
            "sha256": "ea3052d541e92b375630c4d317a6656b79d02a5713e883f6a5ee387795d6d9c0",
        },
        "restart_rules": {
            "automatic_resume": False, "overwrite": False,
            "partial_output_requires_review_and_new_authorization": True,
        },
        "schema_version": "OC3_PHOTSYS_ZERO_BYTE_PROVENANCE_RESEARCH_CANDIDATE_001",
        "scope": SCOPE,
        "specification": {"path": str(SPEC_PATH.relative_to(PROJECT)), "sha256": SPEC_SHA256},
        "stage_id": STAGE_ID,
        "statuses": list(STATUSES),
    })


def validate_candidate(path: Path = CANDIDATE_PATH, *, authorization_absent: bool = True) -> dict[str, object]:
    try:
        value = validate_sealed(load_canonical_json(path))
    except Exception as exc:
        raise ProvenanceError("RESEARCH_CANDIDATE_INVALID") from exc
    if value != build_candidate(implementation_hash(PROJECT)):
        raise ProvenanceError("RESEARCH_CANDIDATE_INVALID")
    if authorization_absent and AUTHORIZATION_PATH.exists():
        raise ProvenanceError("PREMATURE_FINAL_AUTHORIZATION_PRESENT")
    return value


def validate_authorization(candidate_path: Path, authorization_path: Path,
                           argv_sha256: str) -> dict[str, object]:
    candidate = validate_candidate(candidate_path, authorization_absent=False)
    try:
        value = validate_sealed(load_canonical_json(authorization_path))
    except Exception as exc:
        raise ProvenanceError("FINAL_AUTHORIZATION_INVALID") from exc
    required = {"authorization_id", "authorization_state", "authorized", "candidate_sha256",
                "command_argv_sha256", "resume", "scope", "sealed", "stage_id"}
    if (set(value) != required or value.get("authorization_state") != "FINAL_HUMAN_AUTHORIZATION" or
            value.get("authorized") is not True or value.get("resume") is not False or
            value.get("candidate_sha256") != file_sha256(candidate_path) or
            value.get("command_argv_sha256") != argv_sha256 or
            value.get("command_argv_sha256") != candidate["command_argv_sha256"] or
            value.get("scope") != SCOPE or value.get("stage_id") != STAGE_ID):
        raise ProvenanceError("FINAL_AUTHORIZATION_INVALID")
    return value


def dry_run() -> dict[str, object]:
    validate_frozen_inputs()
    validate_candidate()
    return {
        "astronomical_data_GETs": 0, "firewall": FirewallCounters().object(),
        "network_requests": 0, "resource_count": len(_resources()), "scope": SCOPE,
        "stage_id": STAGE_ID, "state": READY,
    }


class _Text(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def parse_legacy_document(body: bytes) -> dict[str, object]:
    parser = _Text()
    try:
        parser.feed(body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise ProvenanceError("LEGACY_DOCUMENT_PARSE_FAILED") from exc
    text = "".join(parser.parts)
    target = "survey-bricks-dr9-randoms-0.48.0.fits"
    position = text.find(target)
    if position < 0:
        raise ProvenanceError("LEGACY_TARGET_RESOURCE_NOT_FOUND")
    excerpt = text[position:position + 8000]
    # Space is kept as a literal quoted single space; it is never mapped to NUL.
    patterns = {
        "N": re.search(r"(?:['\"]N['\"]|\bN\b).{0,100}\bnorth\b", excerpt, re.I | re.S),
        "S": re.search(r"(?:['\"]S['\"]|\bS\b).{0,100}\bsouth\b", excerpt, re.I | re.S),
        " ": re.search(r"(?:['\"] ['\"]|space).{0,160}\boutside\b", excerpt, re.I | re.S),
    }
    return {
        "documented_photsys_type": "character",
        "meanings": {key: bool(value) for key, value in patterns.items()},
        "outside_representation_literal": " ", "resource_name": target,
        "temporal_limitation": "Current page not independently frozen to DR9 production time",
    }


def _fits_section(page: str, position: int) -> tuple[str | None, str | None]:
    """Return the nearest bounded, heading-like identifier before evidence."""
    line_start = page.rfind("\n", 0, position) + 1
    line_end = page.find("\n", position)
    if line_end < 0:
        line_end = len(page)
    before = page[:line_start].splitlines()[-79:] + [page[line_start:line_end]]
    numbered = re.compile(r"^\s*(\d+(?:\.\d+)+)\s+(.{3,100}?)\s*$")
    for line in reversed(before):
        match = numbered.match(line)
        if match:
            return match.group(1), match.group(2).strip()
    for line in reversed(before):
        if re.search(r"binary\s+table|BINTABLE", line, re.I):
            return None, re.sub(r"\s+", " ", line).strip()[:120]
    return None, None


def _fits_record(claim: str, pages: list[str], page_index: int | None,
                 spans: list[tuple[int, int]]) -> dict[str, object]:
    if page_index is None or not spans:
        return {"claim": claim, "context_characters": 0, "context_sha256": None,
                "page": None, "section_identifier": None, "section_title": None,
                "supported": False}
    page = pages[page_index]
    start = max(0, min(item[0] for item in spans) - 240)
    end = min(len(page), max(item[1] for item in spans) + 240)
    context = re.sub(r"\s+", " ", page[start:end]).strip()
    identifier, heading = _fits_section(page, min(item[0] for item in spans))
    return {"claim": claim, "context_characters": len(context),
            "context_sha256": sha256_bytes(context.encode()), "page": page_index + 1,
            "section_identifier": identifier, "section_title": heading, "supported": True}


def _first_page_evidence(pages: list[str], patterns: tuple[re.Pattern[str], ...],
                         *, maximum_span: int) -> tuple[int | None, list[tuple[int, int]]]:
    for page_index, page in enumerate(pages):
        matches = [pattern.search(page) for pattern in patterns]
        if all(matches):
            spans = [(match.start(), match.end()) for match in matches if match]
            if max(item[1] for item in spans) - min(item[0] for item in spans) <= maximum_span:
                return page_index, spans
    return None, []


def parse_fits_standard_text(text: str, *, title: str, version: str,
                             normative: bool) -> dict[str, object]:
    """Extract three closed representation claims from bounded PDF text contexts.

    Generic NULL wording is insufficient: the Binary Table claim requires a
    BINTABLE context, the TFORMn character type A, its ASCII-NULL termination
    rule, and the first-character null-string rule on one text page.
    """
    pages = text.split("\f")
    flags = re.I | re.S
    bintable_patterns = (
        re.compile(r"(?:binary\s+table|BINTABLE)", flags),
        re.compile(r"TFORMn.{0,900}(?:(?:['\"]A['\"]|\bA\b).{0,180}(?:character|string)|(?:character|string).{0,180}(?:['\"]A['\"]|\bA\b))", flags),
        re.compile(r"(?:character\s+string).{0,700}(?:terminated|termination).{0,240}ASCII\s+NULL.{0,160}(?:hexadecimal\s*00|hex\s*00|0x00)", flags),
        re.compile(r"(?:null\s+string).{0,500}(?:ASCII\s+NULL).{0,240}(?:first\s+character)|(?:first\s+character).{0,240}(?:ASCII\s+NULL).{0,500}(?:null\s+string)", flags),
    )
    ascii_null_patterns = (re.compile(
        r"ASCII\s+NULL.{0,240}(?:all\s+bits\s+(?:set\s+to\s+)?zero|hexadecimal\s*00|hex\s*00|0x00)"
        r"|(?:all\s+bits\s+(?:set\s+to\s+)?zero|hexadecimal\s*00|hex\s*00|0x00).{0,240}ASCII\s+NULL",
        flags),)
    ascii_space_patterns = (re.compile(
        r"ASCII\s+space.{0,240}(?:decimal\s*32|hexadecimal\s*20|hex\s*20|0x20)"
        r"|(?:decimal\s*32|hexadecimal\s*20|hex\s*20|0x20).{0,240}ASCII\s+space",
        flags),)
    b_page, b_spans = _first_page_evidence(pages, bintable_patterns, maximum_span=6000)
    n_page, n_spans = _first_page_evidence(pages, ascii_null_patterns, maximum_span=600)
    s_page, s_spans = _first_page_evidence(pages, ascii_space_patterns, maximum_span=600)
    evidence = [
        _fits_record("BINTABLE_A_NULL_RULE", pages, b_page, b_spans),
        _fits_record("ASCII_NULL_0x00", pages, n_page, n_spans),
        _fits_record("ASCII_SPACE_0x20", pages, s_page, s_spans),
    ]
    support = {item["claim"]: item["supported"] for item in evidence}
    complete = all(support.values())
    return {
        "ASCII_NULL_0x00": support["ASCII_NULL_0x00"],
        "ASCII_SPACE_0x20": support["ASCII_SPACE_0x20"],
        "BINTABLE_A_NULL_RULE": support["BINTABLE_A_NULL_RULE"],
        "authority_kind": "normative" if normative else "explanatory",
        "bintable_A_first_character_0x00": (
            support["BINTABLE_A_NULL_RULE"] and support["ASCII_NULL_0x00"]),
        "evidence_records": evidence,
        "evidence_text_sha256": sha256_bytes(text.encode()),
        "representation_complete": complete,
        "survey_footprint_semantics_assigned": False,
        "title": title, "version": version,
        "x00_distinct_from_x20": complete,
        "x20_ascii_space": support["ASCII_SPACE_0x20"],
    }


def deterministic_tree_manifest(root: Path) -> dict[str, object]:
    root = Path(root).resolve()
    entries = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ProvenanceError("SOURCE_TREE_SYMLINK_FORBIDDEN")
        if path.is_file():
            entries.append({"path": path.relative_to(root).as_posix(),
                            "sha256": file_sha256(path), "size": path.stat().st_size})
    return {"entries": entries, "tree_sha256": sha256_bytes(canonical(entries))}


def extract_archive_safely(data: bytes, destination: Path) -> dict[str, object]:
    destination = Path(destination)
    if destination.exists():
        raise ProvenanceError("ARCHIVE_DESTINATION_EXISTS")
    with tarfile.open(fileobj=BytesIO(data), mode="r:gz") as archive:
        members = archive.getmembers()
        if not members or len(members) > MAX_ARCHIVE_MEMBERS:
            raise ProvenanceError("ARCHIVE_MEMBER_LIMIT")
        total = 0
        checked: list[tuple[tarfile.TarInfo, PurePosixPath]] = []
        for member in members:
            path = PurePosixPath(member.name)
            if (path.is_absolute() or ".." in path.parts or not path.parts or
                    path.parts[0] != ARCHIVE_PREFIX or member.issym() or member.islnk() or
                    not (member.isdir() or member.isfile())):
                raise ProvenanceError("ARCHIVE_MEMBER_UNSAFE")
            total += member.size if member.isfile() else 0
            if total > MAX_EXTRACTED_BYTES:
                raise ProvenanceError("ARCHIVE_EXTRACTED_BYTE_LIMIT")
            checked.append((member, path))
        destination.mkdir(parents=True)
        for member, path in checked:
            relative = PurePosixPath(*path.parts[1:])
            target = destination.joinpath(*relative.parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                source = archive.extractfile(member)
                if source is None:
                    raise ProvenanceError("ARCHIVE_MEMBER_UNSAFE")
                with target.open("xb") as stream:
                    stream.write(source.read())
    manifest = deterministic_tree_manifest(destination)
    present = {item["path"] for item in manifest["entries"]}
    if any(path not in present for path in MANDATORY_SOURCE_PATHS):
        raise ProvenanceError("MANDATORY_SOURCE_PATH_MISSING")
    return manifest


def search_source_tree(root: Path) -> dict[str, object]:
    root = Path(root).resolve()
    results: dict[str, list[dict[str, object]]] = {term: [] for term in SEARCH_TERMS}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink() or path.stat().st_size > 5 * 1024 * 1024:
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        relative = path.relative_to(root).as_posix()
        for number, line in enumerate(lines, 1):
            for term in SEARCH_TERMS:
                if term in line and len(results[term]) < 1000:
                    results[term].append({"line": number, "line_sha256": sha256_bytes(line.encode()),
                                          "path": relative})
    named = any(results[term] for term in ("survey-bricks-dr9-randoms",))
    return {
        "named_product_generator_status": ("CANDIDATE_REFERENCE_REQUIRES_TRACE" if named
                                            else NAMED_GENERATOR_NOT_FOUND),
        "results": results, "search_terms": list(SEARCH_TERMS),
    }


def analyze_producer_source(root: Path) -> dict[str, object]:
    root = Path(root)
    randoms = (root / "py/desitarget/randoms.py").read_text(encoding="utf-8")
    supplement = (root / "bin/supplement_randoms").read_text(encoding="utf-8")
    io_source = (root / "py/desitarget/io.py").read_text(encoding="utf-8")
    dtype = bool(re.search(r"PHOTSYS.{0,100}(?:\|S1|S1)", randoms, re.S))
    n_assign = bool(re.search(r"PHOTSYS.{0,100}(?:b?['\"]N['\"])", randoms, re.S))
    s_assign = bool(re.search(r"PHOTSYS.{0,100}(?:b?['\"]S['\"])", randoms, re.S))
    zeros_call = "zeros=True" in randoms or "zeros=True" in supplement
    supplement_found = "supplement_randoms" in randoms or "supplement_randoms" in supplement
    # Extract only the lexical suite of ``if zeros:``.  Stop at its matching
    # else/elif rather than allowing the normal allocation branch to bleed in.
    lines = randoms.splitlines()
    branches: list[str] = []
    for index, line in enumerate(lines):
        if re.match(r"^\s*if\s+zeros\s*:\s*(?:#.*)?$", line):
            indent = len(line) - len(line.lstrip())
            suite = []
            for following in lines[index + 1:]:
                stripped = following.strip()
                current = len(following) - len(following.lstrip())
                if stripped and current <= indent:
                    break
                suite.append(following)
            branches.append("\n".join(suite))
    zeros_dtype_contains = any(re.search(r"PHOTSYS.{0,100}(?:\|S1|S1)", part, re.S) for part in branches)
    serialization = bool(re.search(r"(?:write_randoms|fitsio\.write|write\()", io_source))
    def locations(path: str, text: str, pattern: str) -> list[dict[str, object]]:
        found = []
        for number, line in enumerate(text.splitlines(), 1):
            if re.search(pattern, line):
                found.append({"line": number, "line_sha256": sha256_bytes(line.encode()),
                              "path": path})
        return found
    return {
        "evidence_locations": {
            "N_assignment": locations("py/desitarget/randoms.py", randoms, r"PHOTSYS.*(?:b?['\"]N['\"])") ,
            "PHOTSYS_dtype": locations("py/desitarget/randoms.py", randoms, r"PHOTSYS.*(?:\|S1|S1)"),
            "S_assignment": locations("py/desitarget/randoms.py", randoms, r"PHOTSYS.*(?:b?['\"]S['\"])") ,
            "supplement_randoms": locations("py/desitarget/randoms.py", randoms, r"supplement_randoms") +
                                  locations("bin/supplement_randoms", supplement, r"supplement_randoms"),
            "write_path": locations("py/desitarget/io.py", io_source, r"write_randoms|fitsio\.write|write\("),
            "zeros_true": locations("py/desitarget/randoms.py", randoms, r"zeros\s*=\s*True") +
                          locations("bin/supplement_randoms", supplement, r"zeros\s*=\s*True"),
        },
        "mandatory_blob_sha256": {
            path: file_sha256(root / path) for path in MANDATORY_SOURCE_PATHS
        },
        "normal_N_assignment_detected": n_assign,
        "normal_PHOTSYS_S1_dtype_detected": dtype,
        "normal_S_assignment_detected": s_assign,
        "supplement_randoms_detected": supplement_found,
        "write_path_candidate_detected": serialization,
        "outside_rows_raw_0x00_proven": False,
        "serialization_preserves_PHOTSYS_proven": False,
        "zero_initialization_before_assignment_proven": False,
        "zeros_true_output_dtype_contains_PHOTSYS": zeros_dtype_contains,
        "zeros_true_path_detected": zeros_call,
    }


def verify_revision_metadata(ref_body: bytes, tag_body: bytes) -> dict[str, object]:
    try:
        ref = json.loads(ref_body); tag = json.loads(tag_body)
    except (UnicodeDecodeError, ValueError) as exc:
        raise ProvenanceError("REVISION_METADATA_INVALID") from exc
    if (ref.get("object", {}).get("type") != "tag" or
            ref.get("object", {}).get("sha") != EXPECTED_TAG_OBJECT or
            tag.get("sha") != EXPECTED_TAG_OBJECT or
            tag.get("object", {}).get("type") != "commit" or
            tag.get("object", {}).get("sha") != EXPECTED_COMMIT):
        raise ProvenanceError("DESITARGET_REVISION_MISMATCH")
    return {"annotated_tag_object": EXPECTED_TAG_OBJECT, "resolved_commit": EXPECTED_COMMIT,
            "tag": TAG, "verified": True}


def synthetic_zero_initialization_check() -> dict[str, object]:
    import numpy as np  # Deliberately lazy; never imported by documentary preflight.
    value = np.zeros(1, dtype="|S1")
    raw = value.tobytes()
    return {"dtype": value.dtype.str, "numpy_version": np.__version__,
            "raw_synthetic_byte": f"0x{raw[0]:02x}", "supported": raw == b"\x00"}


class DocumentaryTransport:
    """Exact-manifest HTTPS GET transport; no arbitrary URL method exists."""
    def __init__(self, manifest: dict[str, object], counters: FirewallCounters,
                 timeout_seconds: int = 30, *, receipt_directory: Path | None = None,
                 global_body_cap: int = BODY_CAP):
        self.resources = {item["id"]: item for item in manifest["resources"]}
        self.counters = counters
        self.timeout_seconds = timeout_seconds
        self.receipt_directory = Path(receipt_directory) if receipt_directory is not None else None
        self.global_body_cap = global_body_cap
        self.last_failure_receipt: dict[str, object] | None = None

    def _metadata(self, resource_id: str, url: str, status: int,
                  headers: dict[str, str]) -> dict[str, object]:
        raw_length = headers.get("content-length")
        declared = int(raw_length) if raw_length is not None and raw_length.isdigit() else None
        return {
            "application_body_bytes_read": 0,
            "content_encoding": headers.get("content-encoding", "identity"),
            "content_type": headers.get("content-type"),
            "declared_content_length": declared,
            "headers": headers,
            "literal_url": url,
            "observed_at_utc": datetime.now(timezone.utc).isoformat(),
            "resource_id": resource_id,
            "status": status,
        }

    def _fail(self, code: str, metadata: dict[str, object]) -> None:
        receipt = sealed({
            **metadata,
            "counters": self.counters.object(),
            "failure_code": code,
            "wire_or_tls_bytes_claimed": False,
        })
        self.last_failure_receipt = receipt
        if self.receipt_directory is not None:
            path = self.receipt_directory / (
                f"{self.counters.public_documentary_source_requests:04d}_"
                f"{metadata['resource_id']}_FAILURE.json")
            write_json_immutable(path, receipt)
        raise ProvenanceError(code)

    def get(self, resource_id: str) -> dict[str, object]:
        if resource_id not in self.resources:
            raise ProvenanceError("RESOURCE_NOT_ALLOWLISTED")
        resource = self.resources[resource_id]
        url = str(resource["url"])
        parsed = urlsplit(url)
        if (parsed.scheme != "https" or parsed.hostname != resource["host"] or
                parsed.query or parsed.fragment or resource["redirect_rule"] != "NO_REDIRECT" or
                parsed.path.lower().endswith(".fits")):
            raise ProvenanceError("RESOURCE_NOT_ALLOWLISTED")
        if self.counters.public_documentary_source_requests >= REQUEST_CAP:
            raise ProvenanceError("REQUEST_CAP_EXCEEDED")
        self.counters.public_documentary_source_requests += 1
        connection = http.client.HTTPSConnection(parsed.hostname, parsed.port or 443,
                                                  timeout=self.timeout_seconds)
        connection.request("GET", parsed.path, headers={"Accept-Encoding": "identity",
                           "User-Agent": "OC3-PHOTSYS-zero-byte-provenance/1"})
        response = connection.getresponse()
        headers = {key.lower(): value for key, value in response.getheaders()}
        cap = int(resource["byte_cap"])
        metadata = self._metadata(resource_id, url, response.status, headers)
        if response.status != 200 or response.status in (301, 302, 303, 307, 308):
            connection.close(); self._fail("DOCUMENTARY_HTTP_RESPONSE_INVALID", metadata)
        if headers.get("content-encoding", "identity").lower() != "identity":
            connection.close(); self._fail("DOCUMENTARY_ENCODING_INVALID", metadata)
        content_type = headers.get("content-type", "").split(";", 1)[0].strip().lower()
        accepted_content_types = resource.get("accepted_content_types")
        if (not isinstance(accepted_content_types, list) or
                content_type not in accepted_content_types):
            connection.close(); self._fail("DOCUMENTARY_CONTENT_TYPE_INVALID", metadata)
        if headers.get("content-length", "").isdigit() and int(headers["content-length"]) > cap:
            connection.close(); self._fail("RESOURCE_BODY_CAP_EXCEEDED", metadata)
        remaining = max(0, self.global_body_cap - self.counters.public_documentary_source_body_bytes)
        body = response.read(min(cap, remaining) + 1); connection.close()
        # This is an application-read quantity.  It deliberately makes no
        # assertion about physical wire, TLS, or transport overhead bytes.
        self.counters.application_body_bytes_read += len(body)
        self.counters.public_documentary_source_body_bytes += len(body)
        metadata["application_body_bytes_read"] = len(body)
        if len(body) > cap or self.counters.public_documentary_source_body_bytes > self.global_body_cap:
            self._fail("RESOURCE_BODY_CAP_EXCEEDED", metadata)
        return {"body": body, "final_url": url, "headers": headers,
                "response_metadata": metadata,
                "status": response.status, "url": url}


def _write_raw(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise ProvenanceError("IMMUTABLE_OUTPUT_CONFLICT")
    with path.open("xb") as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())


def run_research(candidate_path: Path, authorization_path: Path, argv_sha256: str,
                 output_directory: Path, *,
                 transport_factory: Callable[[dict[str, object], FirewallCounters], object] = DocumentaryTransport) -> dict[str, object]:
    candidate = validate_candidate(candidate_path, authorization_absent=False)
    validate_authorization(candidate_path, authorization_path, argv_sha256)
    validate_frozen_inputs()
    output = Path(output_directory).resolve()
    if output != OUTPUT_ROOT.resolve() or output.exists():
        raise ProvenanceError("RESEARCH_RESTART_REQUIRES_REVIEW")
    output.mkdir(parents=True)
    raw_root = output / "RAW_IMMUTABLE_PUBLIC_SOURCES"
    extract_root = output / "DESITARGET_0_48_0_SOURCE"
    counters = FirewallCounters()
    manifest = validate_resource_manifest()
    try:
        transport = transport_factory(
            manifest, counters, receipt_directory=output / "HTTP_FAILURE_RECEIPTS")
    except TypeError:
        # Synthetic legacy factories may implement the historical two-argument
        # interface; production DocumentaryTransport always takes receipts.
        transport = transport_factory(manifest, counters)
    responses: dict[str, dict[str, object]] = {}
    metadata = []
    try:
        for resource in manifest["resources"]:
            response = transport.get(resource["id"])
            responses[resource["id"]] = response
            body = response["body"]
            name = resource["id"] + (".tar.gz" if resource["id"].endswith("ARCHIVE") else ".body")
            path = raw_root / name
            _write_raw(path, body)
            metadata.append({"body_sha256": sha256_bytes(body), "body_size": len(body),
                             "final_url": response["final_url"], "headers": response["headers"],
                             "id": resource["id"], "observed_at_utc": datetime.now(timezone.utc).isoformat(),
                             "status": response["status"], "url": response["url"]})
        revision = verify_revision_metadata(responses["DESITARGET_TAG_REF"]["body"],
                                            responses["DESITARGET_TAG_OBJECT"]["body"])
        tree = extract_archive_safely(responses["DESITARGET_0_48_0_ARCHIVE"]["body"], extract_root)
        search = search_source_tree(extract_root)
        trace = analyze_producer_source(extract_root)
        legacy = parse_legacy_document(responses["LEGACY_SURVEY_DR9_FILES"]["body"])
        pdf_path = raw_root / "FITS_STANDARD_4_0.body"
        text_path = output / "FITS_STANDARD_4_0.txt"
        completed = subprocess.run(["pdftotext", "-layout", str(pdf_path), str(text_path)],
                                   check=False, capture_output=True, timeout=60)
        if completed.returncode != 0 or not text_path.is_file():
            raise ProvenanceError("FITS_DOCUMENT_TEXT_EXTRACTION_FAILED")
        fits = parse_fits_standard_text(text_path.read_text(errors="strict"),
                                        title="Definition of the Flexible Image Transport System (FITS)",
                                        version="4.0", normative=True)
        named_generation = search["named_product_generator_status"] != NAMED_GENERATOR_NOT_FOUND
        result = outcome_gate(
            official_categories=all(legacy["meanings"].values()),
            fits_representation=fits["representation_complete"],
            exact_producer=all(trace[key] for key in ("normal_PHOTSYS_S1_dtype_detected",
                               "normal_N_assignment_detected", "normal_S_assignment_detected")),
            exact_outside_path=False, serialization_preserves=False,
            named_product_generation=named_generation,
            documentary_physical_mismatch=True, unresolved_conflict=False)
        claim_matrix = completed_claim_matrix(legacy=legacy, fits=fits, trace=trace,
                                              named_generation_proven=False)
        artifacts = {
            "claim_matrix": claim_matrix, "desitarget_revision": revision,
            "fits_evidence": fits, "legacy_evidence": legacy,
            "named_product_generation_provenance": ("REQUIRES_EXACT_TRACE" if named_generation
                                                     else NAMED_PROVENANCE_UNRESOLVED),
            "outcome": result, "producer_trace": trace, "source_search": search,
            "source_tree_manifest": tree,
        }
        for name, value in artifacts.items():
            write_json_immutable(output / f"{name.upper()}.json", sealed({"stage_id": STAGE_ID, "value": value}))
        write_json_immutable(output / "RESPONSE_METADATA.json", sealed({"responses": metadata, "stage_id": STAGE_ID}))
        report = ("# OC3 PHOTSYS zero-byte semantic provenance report\n\n"
                  f"Stage: `{STAGE_ID}`  \nScope: `{SCOPE}`  \nOutcome: `{result}`\n\n"
                  "## Frozen observation\n\n"
                  f"Histogram artifact SHA-256: `{HISTOGRAM_SHA256}`. Its only nonzero bins remain "
                  "0x00=330208, 0x4e=82897, and 0x53=249069. No row-level evidence was read.\n\n"
                  "## Retrieved public sources\n\n" + "\n".join(
                      f"- `{item['id']}`: `{item['body_sha256']}` from `{item['final_url']}` at `{item['observed_at_utc']}`."
                      for item in metadata) + "\n\n"
                  "## FITS representation evidence\n\n"
                  f"Recorded parser result: `{json.dumps(fits, sort_keys=True)}`. FITS representation evidence "
                  "does not assign survey-footprint semantics.\n\n"
                  "## Official Legacy Survey documentation\n\n"
                  f"Recorded parser result: `{json.dumps(legacy, sort_keys=True)}`. The literal documentary "
                  "space is retained as byte-distinct text and is not normalized to NUL.\n\n"
                  "## Exact producer source\n\n"
                  f"Tag `{TAG}`, annotated tag object `{EXPECTED_TAG_OBJECT}`, resolved commit `{EXPECTED_COMMIT}`. "
                  f"Source-tree hash `{tree['tree_sha256']}`. Producer trace: `{json.dumps(trace, sort_keys=True)}`.\n\n"
                  "## Named-product generation provenance\n\n"
                  f"`{artifacts['named_product_generation_provenance']}`. Deterministic terms: "
                  f"`{', '.join(SEARCH_TERMS)}`. Negative search results do not fill a provenance gap.\n\n"
                  "## Claim matrix and inference\n\n"
                  "The canonical claim matrix is preserved in `CLAIM_MATRIX.json`; producer evidence and inference "
                  "remain separate. Count coincidence, FITS null semantics, and zero initialization are non-gating "
                  "unless the exact outside and named-product pathways are independently proven.\n\n"
                  "## No-data-observation firewall\n\n"
                  f"`{json.dumps(counters.object(), sort_keys=True)}`\n\n"
                  "## Unresolved assumptions and boundary\n\n"
                  "Current web documentation may not be identical to its DR9-production-time form. Any newly "
                  "suggested provenance resource requires a new human-reviewed manifest and was not retrieved here. "
                  "The optional synthetic zero-initialization check was not part of this research execution.\n\n"
                  "PHOTSYS V1 was not amended and no resolver was created. Panel V2 and P1 were not run.\n")
        _write_raw(output / "OC3_PHOTSYS_ZERO_BYTE_SEMANTIC_PROVENANCE_REPORT.md", report.encode())
        terminal = sealed({"counters": counters.object(), "outcome": result, "scope": SCOPE,
                           "stage_id": STAGE_ID, "state": result})
        write_json_immutable(output / "TERMINAL.json", terminal)
        return terminal
    except BaseException:
        # Any created tree is retained for review.  No automatic resume is permitted.
        terminal = sealed({"counters": counters.object(), "outcome": None, "scope": SCOPE,
                           "stage_id": STAGE_ID, "state": INTEGRITY_STOP})
        write_json_immutable(output / "TERMINAL.json", terminal)
        raise
