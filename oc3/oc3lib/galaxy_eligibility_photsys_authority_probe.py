"""Bounded documentary and FITS-header probe for the DR9 PHOTSYS authority.

The production entry point is inert until a canonical candidate and a separate
final human authorization bind the exact argv.  Synthetic callers may inject a
transport; importing this module never constructs network transport.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import html
from html.parser import HTMLParser
import http.client
import json
import os
from pathlib import Path
import re
from typing import Callable, Sequence
from urllib.parse import urljoin, urlsplit

from .core import canonical, implementation_hash


STAGE_ID = "OC3-GALAXY-ELIGIBILITY-PHOTSYS-AUTHORITY-PROBE-001"
SCOPE = "PHOTSYS_BRICK_AUTHORITY_ONLY"
TARGET_FILENAME = "survey-bricks-dr9-randoms-0.48.0.fits"
SUCCESS = "PHOTSYS_AUTHORITY_RESOURCE_CONTRACT_RESOLVED"
INCONCLUSIVE = "PHOTSYS_AUTHORITY_RESOURCE_CONTRACT_INCONCLUSIVE"
FAILED = "PHOTSYS_AUTHORITY_RESOURCE_CONTRACT_FAILED"
NOT_BRICK_LEVEL = "PHOTSYS_AUTHORITY_NOT_BRICK_LEVEL_STOP"
PROJECTION_UNAVAILABLE = "PHOTSYS_AUTHORITY_SELECTIVE_PROJECTION_UNAVAILABLE"

PROJECT = Path("/home/jzsalinas/Documents/galaxy-morphology-discovery")
AMENDMENT = PROJECT / "OC3_GALAXY_ELIGIBILITY_REGION_RESOLUTION_AMENDMENT_001.md"
CONTRACT = PROJECT / "OC3_GALAXY_ELIGIBILITY_PHOTSYS_AUTHORITY_CONTRACT_001.md"
HISTORICAL_REPORT = PROJECT / "OC3_GALAXY_ELIGIBILITY_RESOURCE_SCHEMA_PROBE_IMPLEMENTATION_REPORT.md"
DOCUMENTARY_MANIFEST = PROJECT / "oc3/INPUTS/OC3_PHOTSYS_AUTHORITY_DOCUMENTARY_MANIFEST.json"
CANDIDATE_PATH = PROJECT / "oc3/INPUTS/OC3_PHOTSYS_AUTHORITY_RESOURCE_CANDIDATE.json"

AMENDMENT_SHA256 = "1502bd29cab97170a6fa3c4ccddf07b49966ab65b5e0db206a9b8f010ecfbe65"
CONTRACT_SHA256 = "5a8691a4f8438914d0a29d72fa1a5c8eec64e3ad82a04c668e44692fbfdd24e1"
HISTORICAL_REPORT_SHA256 = "8905e2c2d4970cfe33bbe295c740d732529ecd2e969f9150c834aa2ea86110ca"

DOCUMENTARY_ALLOWLIST = (
    "https://www.legacysurvey.org/dr9/files/",
    "https://www.legacysurvey.org/dr9/catalogs/",
)
OFFICIAL_DATA_HOST = "portal.nersc.gov"
ALLOWED_FIELDS = ("BRICKNAME", "BRICKID", "PHOTSYS")
STRUCTURAL_ONLY_FIELD = "AREA_PER_BRICK"
EXPECTED_ROOT_ROWS = 662_174
HEADER_BLOCK = 2880
MAX_HEADER_BLOCKS = 28
MAX_REDIRECTS = 1
DOCUMENTARY_BODY_PER_RESOURCE = 512 * 1024
DOCUMENTARY_REQUEST_CAP = len(DOCUMENTARY_ALLOWLIST) * (1 + MAX_REDIRECTS)
DOCUMENTARY_BODY_CAP = len(DOCUMENTARY_ALLOWLIST) * DOCUMENTARY_BODY_PER_RESOURCE
FULL_REQUEST_CAP = DOCUMENTARY_REQUEST_CAP + (1 + MAX_REDIRECTS) + MAX_HEADER_BLOCKS * (1 + MAX_REDIRECTS)
FULL_BODY_CAP = DOCUMENTARY_BODY_CAP + MAX_HEADER_BLOCKS * HEADER_BLOCK
FULL_RANGE_CAP = MAX_HEADER_BLOCKS * HEADER_BLOCK


class PHOTSYSProbeError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_bytes(value: object) -> bytes:
    return canonical(value) + b"\n"


def object_seal(value: object) -> str:
    return sha256_bytes(canonical(value))


def sealed(value: dict[str, object]) -> dict[str, object]:
    if "sealed" in value:
        raise PHOTSYSProbeError("SEAL_INPUT_INVALID")
    result = dict(value)
    result["sealed"] = object_seal(value)
    return result


def validate_sealed(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or not isinstance(value.get("sealed"), str):
        raise PHOTSYSProbeError("SEALED_OBJECT_INVALID")
    body = {key: item for key, item in value.items() if key != "sealed"}
    if value["sealed"] != object_seal(body):
        raise PHOTSYSProbeError("SEALED_OBJECT_INVALID")
    return value


def _strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def load_canonical_json(path: Path) -> dict[str, object]:
    try:
        raw = Path(path).read_bytes()
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_strict_object)
    except (OSError, UnicodeError, ValueError) as exc:
        raise PHOTSYSProbeError("CANONICAL_JSON_INVALID") from exc
    if not isinstance(value, dict) or raw != canonical_json_bytes(value):
        raise PHOTSYSProbeError("CANONICAL_JSON_INVALID")
    return value


def write_immutable(path: Path, data: bytes) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise PHOTSYSProbeError("IMMUTABLE_OUTPUT_CONFLICT")
        return
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def write_json_immutable(path: Path, value: object) -> None:
    write_immutable(path, canonical_json_bytes(value))


def validate_authorities() -> dict[str, str]:
    expected = {
        str(AMENDMENT.relative_to(PROJECT)): AMENDMENT_SHA256,
        str(CONTRACT.relative_to(PROJECT)): CONTRACT_SHA256,
        str(HISTORICAL_REPORT.relative_to(PROJECT)): HISTORICAL_REPORT_SHA256,
    }
    for relative, digest in expected.items():
        path = PROJECT / relative
        if not path.is_file() or file_sha256(path) != digest:
            raise PHOTSYSProbeError("FROZEN_AUTHORITY_MISMATCH")
    return expected


def validate_documentary_manifest(path: Path = DOCUMENTARY_MANIFEST) -> dict[str, object]:
    value = validate_sealed(load_canonical_json(path))
    if (value.get("schema_version") != "OC3_PHOTSYS_AUTHORITY_DOCUMENTARY_MANIFEST_001" or
            value.get("stage_id") != STAGE_ID or value.get("scope") != SCOPE or
            value.get("broad_web_crawling") is not False):
        raise PHOTSYSProbeError("DOCUMENTARY_MANIFEST_INVALID")
    resources = value.get("resources")
    if not isinstance(resources, list) or len(resources) != 2:
        raise PHOTSYSProbeError("DOCUMENTARY_MANIFEST_INVALID")
    urls = tuple(row.get("literal_url") for row in resources if isinstance(row, dict))
    if urls != DOCUMENTARY_ALLOWLIST:
        raise PHOTSYSProbeError("DOCUMENTARY_RESOURCE_NOT_ALLOWLISTED")
    for row in resources:
        if (set(row) != {"document_id", "literal_url", "max_body_bytes", "provider",
                         "required_evidence", "resolution_state"} or
                row["provider"] != "Legacy Surveys DR9" or
                row["max_body_bytes"] != DOCUMENTARY_BODY_PER_RESOURCE or
                row["resolution_state"] != "PENDING_AUTHORIZED_DOCUMENTARY_RETRIEVAL"):
            raise PHOTSYSProbeError("DOCUMENTARY_MANIFEST_INVALID")
    return value


def validate_inputs() -> dict[str, object]:
    authorities = validate_authorities()
    manifest = validate_documentary_manifest()
    return {
        "authority_count": len(authorities),
        "documentary_resource_count": len(manifest["resources"]),
        "literal_official_url_bound": False,
        "network_requests": 0,
        "scope": SCOPE,
        "stage_id": STAGE_ID,
        "state": "PHOTSYS_AUTHORITY_PROBE_INPUTS_VALID",
        "target_resource": TARGET_FILENAME,
    }


def dry_run() -> dict[str, object]:
    validate_inputs()
    return {
        "body_byte_cap": DOCUMENTARY_BODY_CAP,
        "candidate_scope": "MINIMUM_DOCUMENTARY_BINDING_ONLY",
        "data_head_requests": 0,
        "data_range_requests": 0,
        "full_fits_gets": 0,
        "network_requests": 0,
        "planned_request_cap": DOCUMENTARY_REQUEST_CAP,
        "scope": SCOPE,
        "stage_id": STAGE_ID,
        "state": "PHOTSYS_AUTHORITY_PROBE_DRY_RUN_OK",
        "table_cells_decoded": 0,
    }


def build_documentary_candidate(manifest: dict[str, object], implementation_aggregate: str,
                                command_argv: Sequence[str]) -> dict[str, object]:
    validate_sealed(manifest)
    if tuple(row["literal_url"] for row in manifest["resources"]) != DOCUMENTARY_ALLOWLIST:
        raise PHOTSYSProbeError("DOCUMENTARY_RESOURCE_NOT_ALLOWLISTED")
    body = {
        "authorization_state": "FINAL_HUMAN_AUTHORIZATION_ABSENT",
        "candidate_scope": "MINIMUM_DOCUMENTARY_BINDING_ONLY",
        "command_argv": list(command_argv),
        "command_argv_sha256": sha256_bytes(canonical(list(command_argv))),
        "documentary_manifest_sha256": file_sha256(DOCUMENTARY_MANIFEST),
        "documentary_resources": manifest["resources"],
        "expected_terminals": [INCONCLUSIVE, FAILED],
        "final_authorization_path": "oc3/OC3_PHOTSYS_AUTHORITY_PROBE_FINAL_AUTHORIZATION_001.json",
        "frozen_authorities": {
            str(AMENDMENT.relative_to(PROJECT)): AMENDMENT_SHA256,
            str(CONTRACT.relative_to(PROJECT)): CONTRACT_SHA256,
            str(HISTORICAL_REPORT.relative_to(PROJECT)): HISTORICAL_REPORT_SHA256,
        },
        "implementation_aggregate": implementation_aggregate,
        "literal_official_url": None,
        "negative_capabilities": {
            "acquire_photsys_file": False,
            "decode_table_cells": False,
            "full_fits_get": False,
            "panel_v1": False,
            "panel_v2": False,
            "tractor_sdss_gaia_desi": False,
        },
        "policy": {
            "automatic_retries": 0,
            "body_bytes_cap": DOCUMENTARY_BODY_CAP,
            "concurrency": 1,
            "data_head_requests": 0,
            "header_block_cap": 0,
            "per_document_body_bytes": DOCUMENTARY_BODY_PER_RESOURCE,
            "per_resource_range_body_bytes": 0,
            "redirects_per_request": MAX_REDIRECTS,
            "request_cap": DOCUMENTARY_REQUEST_CAP,
        },
        "scope": SCOPE,
        "stage_id": STAGE_ID,
        "target_filename": TARGET_FILENAME,
        "rights_local_preservation_state": "UNRESOLVED_PENDING_DOCUMENTARY_REVIEW",
    }
    return sealed(body)


def validate_candidate(value: dict[str, object]) -> dict[str, object]:
    validate_sealed(value)
    if (value.get("stage_id") != STAGE_ID or value.get("scope") != SCOPE or
            value.get("target_filename") != TARGET_FILENAME or
            value.get("authorization_state") != "FINAL_HUMAN_AUTHORIZATION_ABSENT"):
        raise PHOTSYSProbeError("CANDIDATE_INVALID")
    scope = value.get("candidate_scope")
    policy = value.get("policy")
    if not isinstance(policy, dict) or policy.get("concurrency") != 1 or policy.get("automatic_retries") != 0:
        raise PHOTSYSProbeError("CANDIDATE_POLICY_INVALID")
    if scope == "MINIMUM_DOCUMENTARY_BINDING_ONLY":
        if (value.get("literal_official_url") is not None or
                policy != {"automatic_retries": 0, "body_bytes_cap": DOCUMENTARY_BODY_CAP,
                           "concurrency": 1, "data_head_requests": 0, "header_block_cap": 0,
                           "per_document_body_bytes": DOCUMENTARY_BODY_PER_RESOURCE,
                           "per_resource_range_body_bytes": 0,
                           "redirects_per_request": MAX_REDIRECTS,
                           "request_cap": DOCUMENTARY_REQUEST_CAP}):
            raise PHOTSYSProbeError("CANDIDATE_POLICY_INVALID")
    elif scope == "COMPLETE_HEADER_CONTRACT_PROBE":
        if (not is_official_literal_url(value.get("literal_official_url")) or
                policy.get("request_cap", 0) > FULL_REQUEST_CAP or
                policy.get("body_bytes_cap", 0) > FULL_BODY_CAP or
                policy.get("header_block_cap", 0) > MAX_HEADER_BLOCKS or
                policy.get("per_resource_range_body_bytes", 0) > FULL_RANGE_CAP or
                policy.get("data_head_requests") != 1 or
                value.get("literal_url_documentary_evidence_sha256") is None):
            raise PHOTSYSProbeError("CANDIDATE_POLICY_INVALID")
    else:
        raise PHOTSYSProbeError("CANDIDATE_INVALID")
    resources = value.get("documentary_resources")
    if (not isinstance(resources, list) or
            tuple(row.get("literal_url") for row in resources) != DOCUMENTARY_ALLOWLIST):
        raise PHOTSYSProbeError("DOCUMENTARY_RESOURCE_NOT_ALLOWLISTED")
    return value


def validate_final_authorization(candidate_path: Path, authorization_path: Path,
                                 argv_sha256: str) -> tuple[dict[str, object], dict[str, object]]:
    candidate = validate_candidate(load_canonical_json(candidate_path))
    authorization = load_canonical_json(authorization_path)
    required = {"authorization_id", "authorization_state", "authorized", "candidate_sha256",
                "command_argv_sha256", "scope", "stage_id"}
    if (set(authorization) != required or authorization.get("authorized") is not True or
            authorization.get("authorization_state") != "FINAL_HUMAN_AUTHORIZATION" or
            authorization.get("candidate_sha256") != file_sha256(candidate_path) or
            authorization.get("command_argv_sha256") != argv_sha256 or
            authorization.get("command_argv_sha256") != candidate.get("command_argv_sha256") or
            authorization.get("stage_id") != STAGE_ID or authorization.get("scope") != SCOPE):
        raise PHOTSYSProbeError("FINAL_AUTHORIZATION_INVALID")
    return candidate, authorization


def is_official_literal_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlsplit(value)
    return (parsed.scheme == "https" and parsed.hostname == OFFICIAL_DATA_HOST and
            parsed.username is None and parsed.password is None and not parsed.query and not parsed.fragment and
            parsed.path.startswith("/cfs/cosmo/data/legacysurvey/dr9/randoms/") and
            parsed.path.rsplit("/", 1)[-1] == TARGET_FILENAME)


_HREF = re.compile(r"href\s*=\s*(['\"])(.*?)\1", re.IGNORECASE | re.DOTALL)


def resolve_literal_url_from_documents(documents: Sequence[dict[str, object]]) -> str:
    matches = set()
    for document in documents:
        source_url = document.get("source_url")
        body = document.get("body")
        if source_url not in DOCUMENTARY_ALLOWLIST or not isinstance(body, bytes):
            raise PHOTSYSProbeError("DOCUMENTARY_RESOURCE_NOT_ALLOWLISTED")
        try:
            text = body.decode("utf-8")
        except UnicodeError as exc:
            raise PHOTSYSProbeError("DOCUMENTARY_BODY_INVALID") from exc
        for match in _HREF.finditer(text):
            resolved = urljoin(source_url, html.unescape(match.group(2).strip()))
            if is_official_literal_url(resolved):
                matches.add(resolved)
    if len(matches) != 1:
        raise PHOTSYSProbeError("LITERAL_URL_NOT_DOCUMENTED")
    return matches.pop()


def documentary_facts(documents: Sequence[dict[str, object]]) -> dict[str, object]:
    joined = "\n".join(document["body"].decode("utf-8", errors="strict") for document in documents)
    required = (TARGET_FILENAME, "PHOTSYS", "AREA_PER_BRICK", "survey-bricks")
    missing = [term for term in required if term not in joined]
    target = _document_section(joined, "survey-bricks-dr9-randoms-0-48-0-fits")
    bricks = _document_section(joined, "survey-bricks-fits-gz")
    target_text = target["text"] if target else ""
    bricks_text = bricks["text"] if bricks else ""
    target_rows = target["rows"] if target else ()
    bricks_rows = bricks["rows"] if bricks else ()
    same_columns = (
        target_text.startswith(TARGET_FILENAME + " ") and
        "A similar file to the survey-bricks.fits.gz file" in target_text and
        "Contains the same columns as the survey-bricks.fits.gz file, plus the additional columns:" in target_text
    )
    brick_table = (
        bricks_text.startswith("survey-bricks.fits.gz FITS binary table with the RA, Dec bounds of each geometrical \"brick\" on the sky.") and
        any(row[:2] == ("BRICKNAME", "char[8]") and row[2] == "Name of the brick."
            for row in bricks_rows if len(row) >= 3) and
        any(row[:2] == ("BRICKID", "int32") and
            re.fullmatch(r"A unique integer with 1-to-1 mapping to brickname\s*\.", row[2])
            for row in bricks_rows if len(row) >= 3)
    )
    photsys_pattern = re.compile(
        r'^"N"\s*,\s*"S"\s+or\s+" "\s+for bricks resolved to be "officially" '
        r'in the north, south, or outside of the footprint, respectively\.$')
    values = any(row[:2] == ("PHOTSYS", "char[1]") and photsys_pattern.fullmatch(row[2])
                 for row in target_rows if len(row) >= 3)
    area = any(row == ("AREA_PER_BRICK", "float64", "The area of the brick in square degrees.")
               for row in target_rows)
    overlap = "northern and southern imaging footprints overlap" in joined.lower()
    brick_level = same_columns and brick_table and area
    return {
        "brick_level_row_model_documented": brick_level,
        "missing_required_terms": missing,
        "north_south_overlap_documented": overlap,
        "photsys_exact_values_documented": values,
        "product_identity_documented": target_text.startswith(TARGET_FILENAME + " "),
    }


class _SectionParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text: list[str] = []
        self.rows: list[tuple[str, ...]] = []
        self._cells: list[str] | None = None
        self._cell_parts: list[str] | None = None

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "tr":
            self._cells = []
        elif tag.lower() in ("td", "th") and self._cells is not None:
            self._cell_parts = []

    def handle_endtag(self, tag):
        if tag.lower() in ("td", "th") and self._cell_parts is not None and self._cells is not None:
            self._cells.append(_normalize_document_text(" ".join(self._cell_parts)))
            self._cell_parts = None
        elif tag.lower() == "tr" and self._cells is not None:
            if self._cells:
                self.rows.append(tuple(self._cells))
            self._cells = None

    def handle_data(self, data):
        self.text.append(data)
        if self._cell_parts is not None:
            self._cell_parts.append(data)


def _normalize_document_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _document_section(body: str, section_id: str) -> dict[str, object] | None:
    # Exact section IDs are part of the frozen official document structure.
    match = re.search(fr'<section id="{re.escape(section_id)}">(.*?)</section>', body,
                      flags=re.DOTALL | re.IGNORECASE)
    if not match:
        return None
    parser = _SectionParser()
    parser.feed(match.group(1))
    return {"rows": tuple(parser.rows), "text": _normalize_document_text(" ".join(parser.text))}


@dataclass
class Counters:
    forbidden_value_decode_count: int = 0
    forbidden_value_materialization_count: int = 0
    forbidden_value_serialization_count: int = 0
    forbidden_value_log_count: int = 0
    random_point_row_decode_count: int = 0
    morphology_access_count: int = 0
    table_cell_values_decoded: int = 0

    def object(self) -> dict[str, int]:
        return {name: getattr(self, name) for name in self.__dataclass_fields__}

    def require_zero(self) -> None:
        if any(self.object().values()):
            raise PHOTSYSProbeError("PHOTSYS_FIREWALL_TRIPWIRE")


@dataclass
class Budget:
    request_cap: int
    body_cap: int
    range_cap: int
    requests: int = 0
    body_bytes: int = 0
    range_bytes: int = 0

    def preflight(self, *, maximum: int, is_range: bool, request_envelope: int) -> None:
        if (maximum < 0 or request_envelope < 1 or
                self.requests + request_envelope > self.request_cap or
                self.body_bytes + maximum > self.body_cap or
                is_range and self.range_bytes + maximum > self.range_cap):
            raise PHOTSYSProbeError("RESOURCE_CAP_EXCEEDED")

    def charge(self, response: dict[str, object], *, maximum: int, is_range: bool) -> None:
        body = response.get("body")
        requests = response.get("requests_started")
        if not isinstance(body, bytes) or not isinstance(requests, int) or requests < 1:
            raise PHOTSYSProbeError("TRANSPORT_RECEIPT_INVALID")
        if len(body) > maximum:
            raise PHOTSYSProbeError("RESPONSE_BODY_CAP")
        if (self.requests + requests > self.request_cap or
                self.body_bytes + len(body) > self.body_cap or
                is_range and self.range_bytes + len(body) > self.range_cap):
            raise PHOTSYSProbeError("RESOURCE_CAP_EXCEEDED")
        self.requests += requests
        self.body_bytes += len(body)
        if is_range:
            self.range_bytes += len(body)


class BoundedTransport:
    def __init__(self, *, redirect_cap: int, timeout_seconds: int = 30):
        if redirect_cap != MAX_REDIRECTS:
            raise PHOTSYSProbeError("REDIRECT_CAP_INVALID")
        self.redirect_cap = redirect_cap
        self.timeout_seconds = timeout_seconds

    def request(self, method: str, url: str, *, byte_range: tuple[int, int] | None,
                max_body_bytes: int) -> dict[str, object]:
        current = url
        for redirects in range(self.redirect_cap + 1):
            parsed = urlsplit(current)
            if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or
                    parsed.query or parsed.fragment):
                raise PHOTSYSProbeError("URL_INVALID")
            connection = http.client.HTTPSConnection(parsed.hostname, parsed.port or 443,
                                                      timeout=self.timeout_seconds)
            headers = {"Accept-Encoding": "identity", "User-Agent": "OC3-PHOTSYS-authority-probe/1"}
            if byte_range is not None:
                headers["Range"] = f"bytes={byte_range[0]}-{byte_range[1]}"
            connection.request(method, parsed.path or "/", headers=headers)
            response = connection.getresponse()
            response_headers = {key.lower(): value for key, value in response.getheaders()}
            if response.status in (301, 302, 303, 307, 308):
                location = response_headers.get("location")
                connection.close()
                if not location or redirects >= self.redirect_cap:
                    raise PHOTSYSProbeError("REDIRECT_CAP_EXCEEDED")
                current = urljoin(current, location)
                continue
            if method == "HEAD":
                body = b""
            else:
                if byte_range is not None and response.status != 206:
                    connection.close()
                    raise PHOTSYSProbeError("EXACT_RANGE_REQUIRED")
                length = response_headers.get("content-length")
                if length is None or not length.isdigit() or int(length) > max_body_bytes:
                    connection.close()
                    raise PHOTSYSProbeError("RESPONSE_BODY_CAP")
                body = response.read(max_body_bytes + 1)
                if len(body) > max_body_bytes:
                    connection.close()
                    raise PHOTSYSProbeError("RESPONSE_BODY_CAP")
            connection.close()
            return {"body": body, "final_url": current, "headers": response_headers,
                    "redirects": redirects, "requests_started": redirects + 1,
                    "status": response.status}
        raise PHOTSYSProbeError("REDIRECT_CAP_EXCEEDED")


class Checkpoints:
    def __init__(self, directory: Path):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def record(self, sequence: int, value: dict[str, object]) -> dict[str, object]:
        receipt = sealed({"sequence": sequence, "stage_id": STAGE_ID, **value})
        path = self.directory / f"{sequence:04d}.json"
        write_json_immutable(path, receipt)
        entries = [{"name": item.name, "sha256": file_sha256(item)}
                   for item in sorted(self.directory.glob("[0-9][0-9][0-9][0-9].json"))]
        index = sealed({"completed": entries, "completed_count": len(entries), "stage_id": STAGE_ID})
        temporary = self.directory / ".CHECKPOINT_INDEX.tmp"
        if temporary.exists():
            temporary.unlink()
        with temporary.open("xb") as stream:
            stream.write(canonical_json_bytes(index)); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, self.directory / "CHECKPOINT_INDEX.json")
        descriptor = os.open(self.directory, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        return receipt


@dataclass(frozen=True)
class Column:
    name: str
    tform: str
    offset: int
    width: int
    dtype: str
    shape: tuple[int, ...]
    tnull: object
    tscal: object
    tzero: object
    unit: object


_TFORM = re.compile(r"^(\d*)([LXBIJKAEDCMPQ])(?:\([^)]*\))?$")
_BITS = {"L": 8, "B": 8, "I": 16, "J": 32, "K": 64, "A": 8,
         "E": 32, "D": 64, "C": 64, "M": 128, "P": 64, "Q": 128}
_DTYPE = {"L": "bool", "X": "bit", "B": "uint8", "I": "int16", "J": "int32",
          "K": "int64", "A": "ascii", "E": "float32", "D": "float64",
          "C": "complex64", "M": "complex128", "P": "descriptor32", "Q": "descriptor64"}


def parse_tform(value: str) -> tuple[int, str, int, tuple[int, ...]]:
    match = _TFORM.fullmatch(value) if isinstance(value, str) else None
    if not match:
        raise PHOTSYSProbeError("FITS_TFORM_UNSUPPORTED")
    repeat = int(match.group(1) or "1")
    code = match.group(2)
    if repeat <= 0:
        raise PHOTSYSProbeError("FITS_TFORM_UNSUPPORTED")
    bits = repeat if code == "X" else repeat * _BITS[code]
    return repeat, code, (bits + 7) // 8, (repeat,) if repeat != 1 else ()


def parse_header(blocks: bytes) -> tuple[dict[str, object], int]:
    if not blocks or len(blocks) % HEADER_BLOCK:
        raise PHOTSYSProbeError("FITS_HEADER_BLOCK_INVALID")
    header = {}; end = None
    for index in range(0, len(blocks), 80):
        try:
            card = blocks[index:index + 80].decode("ascii")
        except UnicodeError as exc:
            raise PHOTSYSProbeError("FITS_HEADER_INVALID") from exc
        key = card[:8].strip()
        if key == "END":
            end = index // 80
            break
        if not key or card[8:10] != "= ":
            continue
        raw = card[10:80].split("/", 1)[0].strip()
        if raw.startswith("'") and raw.endswith("'"):
            parsed: object = raw[1:-1].replace("''", "'").rstrip()
        elif raw in ("T", "F"):
            parsed = raw == "T"
        else:
            try:
                parsed = int(raw)
            except ValueError:
                try:
                    parsed = float(raw.replace("D", "E"))
                except ValueError:
                    parsed = raw
        header[key] = parsed
    if end is None:
        raise PHOTSYSProbeError("FITS_HEADER_END_NOT_FOUND")
    return header, ((end + 1 + 35) // 36) * HEADER_BLOCK


def columns_from_header(header: dict[str, object]) -> tuple[Column, ...]:
    if header.get("XTENSION") != "BINTABLE" or not isinstance(header.get("TFIELDS"), int):
        raise PHOTSYSProbeError("FITS_BINTABLE_REQUIRED")
    count = header["TFIELDS"]
    if count <= 0 or not isinstance(header.get("NAXIS1"), int):
        raise PHOTSYSProbeError("FITS_SCHEMA_INVALID")
    columns = []; offset = 0; names = set()
    for index in range(1, count + 1):
        name = header.get(f"TTYPE{index}"); tform = header.get(f"TFORM{index}")
        if not isinstance(name, str) or not name or name in names or not isinstance(tform, str):
            raise PHOTSYSProbeError("FITS_SCHEMA_INVALID")
        repeat, code, width, shape = parse_tform(tform)
        columns.append(Column(name, tform, offset, width, _DTYPE[code], shape,
                              header.get(f"TNULL{index}"), header.get(f"TSCAL{index}"),
                              header.get(f"TZERO{index}"), header.get(f"TUNIT{index}")))
        names.add(name); offset += width
    if offset != header["NAXIS1"]:
        raise PHOTSYSProbeError("FITS_ROW_WIDTH_MISMATCH")
    return tuple(columns)


def _padded_data_size(header: dict[str, object]) -> int:
    bitpix = header.get("BITPIX"); naxis = header.get("NAXIS")
    if not isinstance(bitpix, int) or not isinstance(naxis, int) or naxis < 0:
        raise PHOTSYSProbeError("FITS_HEADER_GEOMETRY_INVALID")
    if header.get("XTENSION") == "BINTABLE":
        values = (header.get("NAXIS1"), header.get("NAXIS2"), header.get("PCOUNT", 0),
                  header.get("GCOUNT", 1))
        if any(not isinstance(value, int) or value < 0 for value in values):
            raise PHOTSYSProbeError("FITS_HEADER_GEOMETRY_INVALID")
        raw = (values[0] * values[1] + values[2]) * values[3]
    elif naxis == 0:
        raw = 0
    else:
        axes = [header.get(f"NAXIS{index}") for index in range(1, naxis + 1)]
        if any(not isinstance(value, int) or value < 0 for value in axes):
            raise PHOTSYSProbeError("FITS_HEADER_GEOMETRY_INVALID")
        raw = abs(bitpix) // 8
        for value in axes:
            raw *= value
        raw = (raw + header.get("PCOUNT", 0)) * header.get("GCOUNT", 1)
    return ((raw + HEADER_BLOCK - 1) // HEADER_BLOCK) * HEADER_BLOCK


def projection_plan(columns: Sequence[Column]) -> dict[str, object]:
    by_name = {column.name: column for column in columns}
    if any(name not in by_name for name in ALLOWED_FIELDS):
        raise PHOTSYSProbeError(PROJECTION_UNAVAILABLE)
    chosen = sorted((by_name[name] for name in ALLOWED_FIELDS), key=lambda item: item.offset)
    if any(column.dtype.startswith("descriptor") for column in chosen):
        raise PHOTSYSProbeError(PROJECTION_UNAVAILABLE)
    spans = []
    for column in chosen:
        if spans and spans[-1]["offset"] + spans[-1]["length"] == column.offset:
            spans[-1]["length"] += column.width
            spans[-1]["fields"].append(column.name)
        else:
            spans.append({"fields": [column.name], "length": column.width, "offset": column.offset})
    allowed_bytes = sum(column.width for column in chosen)
    if sum(span["length"] for span in spans) != allowed_bytes:
        raise PHOTSYSProbeError(PROJECTION_UNAVAILABLE)
    return {
        "allowed_fields": list(ALLOWED_FIELDS),
        "forbidden_cell_bytes_fetched_per_row": 0,
        "minimal_allowed_bytes_per_row": allowed_bytes,
        "row_relative_spans": spans,
        "state": "SELECTIVE_PROJECTION_AVAILABLE",
        "whole_row_fallback": False,
    }


def structural_contract(inventory: Sequence[dict[str, object]], facts: dict[str, object]) -> dict[str, object]:
    tables = [item for item in inventory if item["header"].get("XTENSION") == "BINTABLE"]
    if len(inventory) != 2 or len(tables) != 1 or inventory[0]["header"].get("SIMPLE") is not True:
        raise PHOTSYSProbeError("FITS_UNEXPECTED_HDU")
    table = tables[0]; header = table["header"]
    columns = columns_from_header(header)
    names = {column.name for column in columns}
    if (not set(ALLOWED_FIELDS).issubset(names) or STRUCTURAL_ONLY_FIELD not in names or
            header.get("NAXIS2") != EXPECTED_ROOT_ROWS or
            not facts.get("brick_level_row_model_documented") or
            not facts.get("product_identity_documented")):
        raise PHOTSYSProbeError(NOT_BRICK_LEVEL)
    plan = projection_plan(columns)
    schema = [{"dtype": column.dtype, "name": column.name, "offset": column.offset,
               "shape": list(column.shape), "tform": column.tform, "tnull": column.tnull,
               "tscal": column.tscal, "tzero": column.tzero, "unit": column.unit,
               "width": column.width} for column in columns]
    return {
        "area_per_brick_cell_values_observed": 0,
        "column_schema": schema,
        "data_offset": table["data_offset"],
        "representation": "ONE_DOCUMENTED_BRICK_LEVEL_ROW_PER_GLOBAL_BRICK_IDENTITY",
        "row_count": header["NAXIS2"],
        "row_width": header["NAXIS1"],
        "selective_projection": plan,
        "table_byte_extent": header["NAXIS1"] * header["NAXIS2"],
        "target_hdu_index": table["hdu_index"],
    }


def _check_content_range(headers: dict[str, str], start: int, end: int, total: int) -> None:
    expected = f"bytes {start}-{end}/{total}"
    if (headers.get("content-range") != expected or
            headers.get("content-encoding", "identity").lower() != "identity"):
        raise PHOTSYSProbeError("RANGE_MISMATCH")


def probe_hdu_inventory(transport: object, budget: Budget, checkpoints: Checkpoints,
                        raw: Path, *, url: str, file_size: int,
                        header_block_cap: int, sequence_start: int = 0,
                        hdu_checkpoint: Callable[[dict[str, object], int], int] | None = None
                        ) -> tuple[list[dict[str, object]], int]:
    inventory = []; offset = 0; sequence = sequence_start; blocks_used = 0
    while offset < file_size:
        header_bytes = bytearray(); header_start = offset
        while True:
            if blocks_used >= header_block_cap:
                raise PHOTSYSProbeError("FITS_HEADER_BLOCK_CAP")
            start = header_start + len(header_bytes); end = start + HEADER_BLOCK - 1
            if end >= file_size:
                raise PHOTSYSProbeError("FITS_HEADER_RANGE_OUTSIDE_FILE")
            budget.preflight(maximum=HEADER_BLOCK, is_range=True,
                             request_envelope=1 + MAX_REDIRECTS)
            response = transport.request("GET", url, byte_range=(start, end), max_body_bytes=HEADER_BLOCK)
            budget.charge(response, maximum=HEADER_BLOCK, is_range=True)
            body = response["body"]
            if response.get("status") != 206 or len(body) != HEADER_BLOCK:
                raise PHOTSYSProbeError("RANGE_MISMATCH")
            _check_content_range(response["headers"], start, end, file_size)
            blocks_used += 1; sequence += 1; header_bytes.extend(body)
            write_immutable(raw / f"header-block-{blocks_used:03d}.bin", body)
            checkpoints.record(sequence, {"body_bytes": len(body), "byte_range": [start, end],
                                           "content_sha256": sha256_bytes(body),
                                           "final_url": response["final_url"],
                                           "kind": "FITS_HEADER_BLOCK",
                                           "network_body_bytes": budget.body_bytes,
                                           "network_requests_started": budget.requests,
                                           "status": response["status"]})
            try:
                header, used = parse_header(bytes(header_bytes))
                break
            except PHOTSYSProbeError as exc:
                if exc.code != "FITS_HEADER_END_NOT_FOUND":
                    raise
        header_bytes = header_bytes[:used]
        data_offset = header_start + used
        padded_data_bytes = _padded_data_size(header)
        if header.get("XTENSION") == "BINTABLE":
            raw_data_bytes = ((header["NAXIS1"] * header["NAXIS2"] + header.get("PCOUNT", 0)) *
                              header.get("GCOUNT", 1))
        else:
            raw_data_bytes = padded_data_bytes
        inventory.append({"data_offset": data_offset, "data_bytes": raw_data_bytes,
                          "hdu_index": len(inventory),
                          "header": header, "header_sha256": sha256_bytes(bytes(header_bytes)),
                          "header_start": header_start, "header_bytes": used,
                          "hdu_type": "PRIMARY" if len(inventory) == 1 else header.get("XTENSION"),
                          "padded_data_bytes": padded_data_bytes})
        next_offset = data_offset + padded_data_bytes
        inventory[-1]["hdu_end"] = next_offset
        if next_offset > file_size or next_offset <= offset:
            raise PHOTSYSProbeError("FITS_FILE_EXTENT_MISMATCH")
        if hdu_checkpoint is not None:
            sequence = hdu_checkpoint(inventory[-1], sequence)
        offset = next_offset
    if offset != file_size:
        raise PHOTSYSProbeError("FITS_FILE_EXTENT_MISMATCH")
    return inventory, blocks_used


def _safe_final_document_url(value: object) -> bool:
    return isinstance(value, str) and value in DOCUMENTARY_ALLOWLIST


def persist_failure_terminal(output_directory: Path, error_code: str) -> None:
    """Close a partial authorized attempt without overwriting prior evidence."""
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    requests = 0; body_bytes = 0
    checkpoint_directory = output_directory / "CHECKPOINTS"
    if checkpoint_directory.is_dir():
        for path in sorted(checkpoint_directory.glob("[0-9][0-9][0-9][0-9].json")):
            try:
                receipt = validate_sealed(load_canonical_json(path))
            except PHOTSYSProbeError:
                continue
            value = receipt.get("network_requests_started")
            body = receipt.get("network_body_bytes")
            if isinstance(value, int):
                requests = max(requests, value)
            if isinstance(body, int):
                body_bytes = max(body_bytes, body)
    accounting_path = output_directory / "OC3_PHOTSYS_AUTHORITY_RESOURCE_ACCOUNTING.json"
    if not accounting_path.exists():
        write_json_immutable(accounting_path, sealed({
            "body_bytes": body_bytes, "forbidden_counters": Counters().object(),
            "full_fits_gets": 0, "network_requests_started": requests,
            "scope": SCOPE, "stage_id": STAGE_ID,
            "state": "PARTIAL_RECONSTRUCTED_FROM_DURABLE_CHECKPOINTS",
        }))
    terminal_path = output_directory / "OC3_PHOTSYS_AUTHORITY_PROBE_TERMINAL.json"
    if not terminal_path.exists():
        write_json_immutable(terminal_path, sealed({
            "first_error": error_code, "network_requests_started": requests,
            "scope": SCOPE, "stage_id": STAGE_ID, "state": FAILED,
            "table_cell_values_decoded": 0,
        }))


def probe_resource_contract(candidate_path: Path, authorization_path: Path, argv_sha256: str,
                            output_directory: Path, *,
                            transport_factory: Callable[..., object] = BoundedTransport) -> dict[str, object]:
    candidate, authorization = validate_final_authorization(candidate_path, authorization_path, argv_sha256)
    output_directory = Path(output_directory)
    if output_directory.exists():
        raise PHOTSYSProbeError("AUTOMATIC_RERUN_OR_RESUME_FORBIDDEN")
    policy = candidate["policy"]
    transport = transport_factory(redirect_cap=policy["redirects_per_request"])
    budget = Budget(policy["request_cap"], policy["body_bytes_cap"],
                    policy["per_resource_range_body_bytes"])
    checkpoints = Checkpoints(output_directory / "CHECKPOINTS")
    raw = output_directory / "RAW_IMMUTABLE"; raw.mkdir(parents=True, exist_ok=True)
    counters = Counters(); documents = []; sequence = 0
    for index, resource in enumerate(candidate["documentary_resources"]):
        url = resource["literal_url"]
        if url not in DOCUMENTARY_ALLOWLIST:
            raise PHOTSYSProbeError("DOCUMENTARY_RESOURCE_NOT_ALLOWLISTED")
        budget.preflight(maximum=resource["max_body_bytes"], is_range=False,
                         request_envelope=1 + policy["redirects_per_request"])
        response = transport.request("GET", url, byte_range=None,
                                     max_body_bytes=resource["max_body_bytes"])
        budget.charge(response, maximum=resource["max_body_bytes"], is_range=False)
        if response.get("status") != 200 or not _safe_final_document_url(response.get("final_url")):
            raise PHOTSYSProbeError("DOCUMENTARY_RESPONSE_INVALID")
        body = response["body"]; sequence += 1
        path = raw / f"document-{index + 1:02d}.body"; write_immutable(path, body)
        receipt = {"body_bytes": len(body), "content_sha256": sha256_bytes(body),
                   "final_url": response["final_url"], "kind": "DOCUMENT",
                   "literal_url": url, "observed_at_utc": datetime.now(timezone.utc).isoformat(),
                   "network_body_bytes": budget.body_bytes,
                   "network_requests_started": budget.requests,
                   "status": response["status"]}
        checkpoints.record(sequence, receipt)
        documents.append({"body": body, "source_url": url, **receipt})
    facts = documentary_facts(documents)
    try:
        documented_url = resolve_literal_url_from_documents(documents)
    except PHOTSYSProbeError as exc:
        if exc.code != "LITERAL_URL_NOT_DOCUMENTED":
            raise
        documented_url = None
    documentary_output = sealed({
        "documents": [{key: value for key, value in document.items() if key != "body"}
                      for document in documents],
        "facts": facts,
        "literal_official_url": documented_url,
        "rights_local_preservation_state": "UNRESOLVED_PENDING_DOCUMENTARY_REVIEW",
        "scope": SCOPE,
        "stage_id": STAGE_ID,
    })
    write_json_immutable(output_directory / "OC3_PHOTSYS_AUTHORITY_DOCUMENTARY_MANIFEST.json",
                         documentary_output)
    structural = None; head_evidence = None; blocks_used = 0
    if candidate["candidate_scope"] == "COMPLETE_HEADER_CONTRACT_PROBE":
        literal = candidate["literal_official_url"]
        if literal != documented_url:
            raise PHOTSYSProbeError("LITERAL_URL_DOCUMENTARY_BINDING_MISMATCH")
        budget.preflight(maximum=0, is_range=False,
                         request_envelope=1 + policy["redirects_per_request"])
        response = transport.request("HEAD", literal, byte_range=None, max_body_bytes=0)
        budget.charge(response, maximum=0, is_range=False)
        headers = response["headers"]
        if (response.get("status") != 200 or response.get("final_url") != literal or
                headers.get("accept-ranges", "").lower() != "bytes" or
                not headers.get("content-length", "").isdigit()):
            raise PHOTSYSProbeError("HEAD_CONTRACT_INVALID")
        file_size = int(headers["content-length"])
        sequence += 1
        head_evidence = {"accept_ranges": headers.get("accept-ranges"),
                         "content_length": file_size, "etag": headers.get("etag"),
                         "final_url": response["final_url"],
                         "last_modified": headers.get("last-modified"),
                         "observed_at_utc": datetime.now(timezone.utc).isoformat(),
                         "network_body_bytes": budget.body_bytes,
                         "network_requests_started": budget.requests,
                         "status": response["status"]}
        checkpoints.record(sequence, {"kind": "DATA_HEAD", **head_evidence})
        inventory, blocks_used = probe_hdu_inventory(
            transport, budget, checkpoints, raw, url=literal, file_size=file_size,
            header_block_cap=policy["header_block_cap"], sequence_start=sequence)
        structural = structural_contract(inventory, facts)
        write_json_immutable(output_directory / "OC3_PHOTSYS_AUTHORITY_HEADER_SCHEMA_CONTRACT.json",
                             sealed({"file_size": file_size,
                                     "hdu_inventory": [{key: value for key, value in item.items()
                                                        if key != "header"} for item in inventory],
                                     "scope": SCOPE, "stage_id": STAGE_ID,
                                     "structural_contract": structural}))
        terminal_state = SUCCESS
    else:
        terminal_state = INCONCLUSIVE
    counters.require_zero()
    accounting = sealed({"body_bytes": budget.body_bytes,
                         "forbidden_counters": counters.object(),
                         "full_fits_gets": 0, "header_blocks": blocks_used,
                         "network_requests_started": budget.requests,
                         "scope": SCOPE, "stage_id": STAGE_ID})
    write_json_immutable(output_directory / "OC3_PHOTSYS_AUTHORITY_RESOURCE_ACCOUNTING.json", accounting)
    transport_evidence = sealed({"document_count": len(documents), "head": head_evidence,
                                 "literal_official_url": documented_url,
                                 "scope": SCOPE, "stage_id": STAGE_ID})
    write_json_immutable(output_directory / "OC3_PHOTSYS_AUTHORITY_TRANSPORT_EVIDENCE.json",
                         transport_evidence)
    terminal = sealed({"authorization_id": authorization["authorization_id"],
                       "final_authorization_does_not_authorize_stage_b": True,
                       "first_error": None, "network_requests_started": budget.requests,
                       "scope": SCOPE, "stage_id": STAGE_ID, "state": terminal_state,
                       "table_cell_values_decoded": 0})
    write_json_immutable(output_directory / "OC3_PHOTSYS_AUTHORITY_PROBE_TERMINAL.json", terminal)
    write_immutable(output_directory / "OC3_PHOTSYS_AUTHORITY_PROBE_RUN.log",
                    (f"stage_id={STAGE_ID}\nstate={terminal_state}\n"
                     f"network_requests_started={budget.requests}\nbody_bytes={budget.body_bytes}\n"
                     "table_cell_values_decoded=0\n").encode("ascii"))
    return {"body_bytes": budget.body_bytes, "literal_official_url": documented_url,
            "network_requests_started": budget.requests, "scope": SCOPE,
            "stage_id": STAGE_ID, "state": terminal_state,
            "table_cell_values_decoded": 0}
