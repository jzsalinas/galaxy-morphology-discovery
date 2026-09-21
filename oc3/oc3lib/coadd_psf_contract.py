"""Bounded, semantics-only contract probe for the DR9 coadd-PSF service.

The production path is closed to two literal, pre-reviewed URLs.  It downloads
at most one small representative PSF response per DR9 region, inspects FITS
headers and byte layout without decoding array values, and persists each
regional result before continuing.
"""
from __future__ import annotations

import hashlib
import http.client
import json
import math
import os
from pathlib import Path
import re
import ssl
from urllib.parse import parse_qs, urlsplit

from .core import canonical, file_hash, implementation_hash
from .fixed_native_contract import validate_psf_contract


STAGE_ID = "OC3-COADD-PSF-CONTRACT-PROBE-001"
SUCCESS = "COADD_PSF_CONTRACT_RESOLVED"
PARTIAL = "COADD_PSF_CONTRACT_PARTIALLY_RESOLVED"
READY = "READY_FOR_HUMAN_COADD_PSF_CONTRACT_PROBE"

LOCATIONS_RELATIVE = Path("oc3/TECHNICAL_INDEX/OC3_LOCATIONS.json")
LOCATIONS_SHA256 = "33d593638c074a3ff59d32d3e4c38558e8912377ea15818ca5072087007c97d1"
SELECTION_SHA256 = "2e6f2cb070a363e9e3dbdb1f25670590c33500a293bb926d8ff94657a2ff8860"
LOCATION_TERMINAL_RELATIVE = Path(
    "oc3/location_selection/OC3-OFFLINE-LOCATION-SELECTION-001/LOCATION_SELECTION_TERMINAL.json")
BASE_CONTRACT_RELATIVE = Path("oc3/INPUTS/OC3_PSF_RESOURCE_CONTRACT_001.json")
BASE_CONTRACT_SHA256 = "1720e8ae9b77f4d5b7de9b7d28a2dbf3d1785c7005e2507e9a9ba21467dbc9f7"
FIXED_RESOLVED_RELATIVE = Path(
    "oc3/fixed_native_resource_contract/OC3-FIXED-NATIVE-RESOURCE-PROBE-001/"
    "FIXED_NATIVE_RESOURCE_CONTRACT_RESOLVED.json")
FIXED_RESOLVED_SHA256 = "8e8ac029aa61e82b2a089205aff4781123700a30ce24353dd95e5eaedd55befc"
IDENTITIES_RELATIVE = Path("oc3/TECHNICAL_INDEX/OC3_PSF_IDENTITIES.json")
BINDING_RELATIVE = Path("oc3/INPUTS/OC3_COADD_PSF_CONTRACT_PROBE_BINDING_001.json")
AUDIT_RELATIVE = Path("oc3/coadd_psf_contract_probe/OC3-COADD-PSF-CONTRACT-PROBE-001")

START_REQUESTS = 278
START_BODY_BYTES = 93_870_926
GLOBAL_BODY_CAP = 1_610_612_736
PRIMARY_REQUESTS = 2
MAX_NEW_REQUESTS = 2
MAX_RESPONSE_BYTES = 1 * 2**20
MAX_TOTAL_BODY_BYTES = PRIMARY_REQUESTS * MAX_RESPONSE_BYTES
RETRIES = 0
CONCURRENCY = 1
ALLOWED_HOST = "www.legacysurvey.org"
ENDPOINT_PATH = "/viewer/coadd-psf/"
BANDS = ("g", "r", "z")
REPRESENTATIVES = (("south", "S1", "P0"), ("north", "N1", "P0"))
HEADER_BLOCK = 2880


class CoaddPSFContractError(Exception):
    def __init__(self, code: str, region: str | None = None,
                 observed_bytes: int | None = None):
        self.code = code
        self.region = region
        self.observed_bytes = observed_bytes
        super().__init__(code)


def _seal(value: dict) -> dict:
    body = dict(value)
    body.pop("sealed", None)
    body["sealed"] = hashlib.sha256(canonical(body)).hexdigest()
    return body


def _verify_seal(value: dict) -> None:
    if not isinstance(value, dict) or not re.fullmatch(r"[0-9a-f]{64}", str(value.get("sealed", ""))):
        raise CoaddPSFContractError("SEAL_INVALID")
    if _seal(value)["sealed"] != value["sealed"]:
        raise CoaddPSFContractError("SEAL_INVALID")


def _canonical_load(path: Path) -> dict:
    try:
        raw = Path(path).read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise CoaddPSFContractError("CANONICAL_INPUT_INVALID") from exc
    if not isinstance(value, dict) or raw != canonical(value) + b"\n":
        raise CoaddPSFContractError("CANONICAL_INPUT_INVALID")
    return value


def _strict(value: dict, keys: set[str], code: str) -> None:
    if not isinstance(value, dict) or set(value) != keys:
        raise CoaddPSFContractError(code)


def _immutable_json(path: Path, value: dict) -> str:
    data = canonical(value) + b"\n"
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise CoaddPSFContractError("IMMUTABLE_EVIDENCE_CONFLICT")
    else:
        with path.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    return hashlib.sha256(data).hexdigest()


def _atomic_json(path: Path, value: dict) -> None:
    data = canonical(value) + b"\n"
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _verified_inputs(project: Path) -> tuple[dict, dict]:
    project = Path(project).resolve()
    locations_path = project / LOCATIONS_RELATIVE
    base_path = project / BASE_CONTRACT_RELATIVE
    fixed_path = project / FIXED_RESOLVED_RELATIVE
    terminal_path = project / LOCATION_TERMINAL_RELATIVE
    if (file_hash(locations_path) != LOCATIONS_SHA256 or
            file_hash(base_path) != BASE_CONTRACT_SHA256 or
            file_hash(fixed_path) != FIXED_RESOLVED_SHA256):
        raise CoaddPSFContractError("FROZEN_INPUT_HASH_MISMATCH")
    locations = _canonical_load(locations_path)
    terminal = _canonical_load(terminal_path)
    base = _canonical_load(base_path)
    validate_psf_contract(base)
    if (locations.get("selection_sha256") != SELECTION_SHA256 or
            terminal.get("state") != "LOCATION_SELECTION_VALIDATED" or
            terminal.get("selection_sha256") != SELECTION_SHA256):
        raise CoaddPSFContractError("LOCATION_SELECTION_AUTHORITY_INVALID")
    return locations, base


def build_identity_manifest(project: Path) -> dict:
    locations, base = _verified_inputs(project)
    location_by_slot = {row["slot"]: row for row in locations["locations"]}
    point_by_key = {(row["slot"], row["point_id"]): row
                    for row in base["spatial_points"]}
    rows = []
    for identity in base["observational_identities"]:
        point = point_by_key[(identity["slot"], identity["point_id"])]
        location = location_by_slot[identity["slot"]]
        rows.append({
            "identity_id": identity["identity_id"], "slot": identity["slot"],
            "region": point["region"], "brick": point["brick"],
            "point_id": identity["point_id"],
            "native_x": point["native_xy"][0], "native_y": point["native_xy"][1],
            "ra": point["ra_dec"][0], "dec": point["ra_dec"][1],
            "band": identity["band"], "transport_id": identity["transport_id"],
        })
        if (location["brick"] != point["brick"] or location["region"] != point["region"]):
            raise CoaddPSFContractError("PSF_IDENTITY_LOCATION_MISMATCH")
    value = _seal({
        "schema_version": "OC3_PSF_IDENTITIES_001", "stage_id": STAGE_ID,
        "locations_binding": {"path": str(LOCATIONS_RELATIVE),
                              "sha256": LOCATIONS_SHA256,
                              "selection_sha256": SELECTION_SHA256},
        "base_contract": {"path": str(BASE_CONTRACT_RELATIVE),
                          "sha256": BASE_CONTRACT_SHA256},
        "counts": {"locations": 6, "spatial_points": 18,
                   "observational_identities": 54},
        "identities": rows,
    })
    validate_identity_manifest(value, base)
    return value


def validate_identity_manifest(value: dict, base: dict) -> dict:
    _strict(value, {"schema_version", "stage_id", "locations_binding", "base_contract",
                    "counts", "identities", "sealed"}, "PSF_IDENTITIES_SCHEMA_INVALID")
    _verify_seal(value)
    if (value["schema_version"] != "OC3_PSF_IDENTITIES_001" or
            value["stage_id"] != STAGE_ID or
            value["locations_binding"] != {"path": str(LOCATIONS_RELATIVE),
                                           "sha256": LOCATIONS_SHA256,
                                           "selection_sha256": SELECTION_SHA256} or
            value["base_contract"] != {"path": str(BASE_CONTRACT_RELATIVE),
                                       "sha256": BASE_CONTRACT_SHA256} or
            value["counts"] != {"locations": 6, "spatial_points": 18,
                                "observational_identities": 54}):
        raise CoaddPSFContractError("PSF_IDENTITIES_BINDING_INVALID")
    rows = value["identities"]
    required = {"identity_id", "slot", "region", "brick", "point_id",
                "native_x", "native_y", "ra", "dec", "band", "transport_id"}
    if not isinstance(rows, list) or len(rows) != 54:
        raise CoaddPSFContractError("PSF_IDENTITY_COUNT_INVALID")
    expected = [(r["slot"], r["point_id"], r["band"])
                for r in base["observational_identities"]]
    for row in rows:
        _strict(row, required, "PSF_IDENTITY_SCHEMA_INVALID")
        if (row["band"] not in BANDS or not all(math.isfinite(float(row[k]))
                                                for k in ("native_x", "native_y", "ra", "dec"))):
            raise CoaddPSFContractError("PSF_IDENTITY_VALUE_INVALID")
    if [(r["slot"], r["point_id"], r["band"]) for r in rows] != expected:
        raise CoaddPSFContractError("PSF_IDENTITY_ORDER_INVALID")
    if len({r["identity_id"] for r in rows}) != 54:
        raise CoaddPSFContractError("PSF_IDENTITY_DUPLICATE")
    points = {(r["slot"], r["point_id"], r["native_x"], r["native_y"], r["ra"], r["dec"])
              for r in rows}
    if len(points) != 18:
        raise CoaddPSFContractError("PSF_SPATIAL_POINT_COUNT_INVALID")
    return value


def exact_command(project: Path) -> list[str]:
    project = Path(project).resolve()
    audit = project / AUDIT_RELATIVE
    return [str(project / "oc3/.venv/bin/python"),
            str(project / "oc3/oc3_coadd_psf_contract_probe.py"),
            "--execute-probe", "--execute-network", "--project", str(project),
            "--binding", str(project / BINDING_RELATIVE),
            "--audit-directory", str(audit), "--log", str(audit / "PROBE_RUN.log"),
            "--max-new-requests", str(MAX_NEW_REQUESTS),
            "--max-response-bytes", str(MAX_RESPONSE_BYTES),
            "--max-total-bytes", str(MAX_TOTAL_BODY_BYTES)]


def build_probe_binding(project: Path, identities: dict) -> dict:
    project = Path(project).resolve()
    _, base = _verified_inputs(project)
    validate_identity_manifest(identities, base)
    point_by_key = {(row["slot"], row["point_id"]): row
                    for row in base["spatial_points"]}
    transport_by_key = {(row["slot"], row["point_id"]): row
                        for row in base["transport_requests"]}
    requests = []
    for region, slot, point_id in REPRESENTATIVES:
        point = point_by_key[(slot, point_id)]
        transport = transport_by_key[(slot, point_id)]
        requests.append({
            "region": region, "slot": slot, "point_id": point_id,
            "brick": point["brick"], "native_xy": point["native_xy"],
            "ra_dec": point["ra_dec"], "layer": point["layer"],
            "transport_id": transport["transport_id"],
            "literal_url": transport["literal_url"],
            "query_bands_parameter": None,
            "expected_observational_bands": list(BANDS),
            "max_response_bytes": MAX_RESPONSE_BYTES,
        })
    value = _seal({
        "schema_version": "OC3_COADD_PSF_CONTRACT_PROBE_BINDING_001",
        "stage_id": STAGE_ID,
        "locations_binding": {"path": str(LOCATIONS_RELATIVE),
                              "sha256": LOCATIONS_SHA256,
                              "selection_sha256": SELECTION_SHA256},
        "identity_manifest": {"path": str(IDENTITIES_RELATIVE),
                              "sha256": hashlib.sha256(canonical(identities) + b"\n").hexdigest()},
        "base_contract": {"path": str(BASE_CONTRACT_RELATIVE),
                          "sha256": BASE_CONTRACT_SHA256},
        "fixed_native_contract": {"path": str(FIXED_RESOLVED_RELATIVE),
                                  "sha256": FIXED_RESOLVED_SHA256,
                                  "state": "FIXED_NATIVE_RESOURCE_CONTRACT_RESOLVED"},
        "cumulative_budget": {"starting_requests": START_REQUESTS,
                              "starting_body_bytes": START_BODY_BYTES,
                              "global_body_cap": GLOBAL_BODY_CAP},
        "policy": {"primary_requests": PRIMARY_REQUESTS,
                   "max_new_requests": MAX_NEW_REQUESTS,
                   "max_response_bytes": MAX_RESPONSE_BYTES,
                   "max_total_body_bytes": MAX_TOTAL_BODY_BYTES,
                   "retries": RETRIES, "concurrency": CONCURRENCY,
                   "http_method": "GET", "redirects": False,
                   "band_query_parameter": None,
                   "image_invvar_access": False,
                   "morphology_access": False,
                   "pixel_value_decode": False,
                   "durable_regional_checkpoints": True},
        "implementation": {
            "entrypoint_path": "oc3/oc3_coadd_psf_contract_probe.py",
            "entrypoint_sha256": file_hash(project / "oc3/oc3_coadd_psf_contract_probe.py"),
            "module_path": "oc3/oc3lib/coadd_psf_contract.py",
            "module_sha256": file_hash(project / "oc3/oc3lib/coadd_psf_contract.py")},
        "representative_requests": requests,
        "bulk_psf_acquisition_authorized": False,
        "image_invvar_acquisition_authorized": False,
        "command_argv": exact_command(project),
    })
    validate_probe_binding(value, project, identities, base, compare_expected=False)
    return value


def validate_probe_binding(binding: dict, project: Path, identities: dict, base: dict,
                           *, compare_expected: bool = True) -> dict:
    _verify_seal(binding)
    if compare_expected and binding != build_probe_binding(project, identities):
        raise CoaddPSFContractError("PROBE_BINDING_MISMATCH")
    if (binding.get("schema_version") != "OC3_COADD_PSF_CONTRACT_PROBE_BINDING_001" or
            binding.get("stage_id") != STAGE_ID or
            binding.get("bulk_psf_acquisition_authorized") is not False or
            binding.get("image_invvar_acquisition_authorized") is not False or
            binding.get("policy") != {
                "primary_requests": 2, "max_new_requests": 2,
                "max_response_bytes": MAX_RESPONSE_BYTES,
                "max_total_body_bytes": MAX_TOTAL_BODY_BYTES,
                "retries": 0, "concurrency": 1, "http_method": "GET",
                "redirects": False, "band_query_parameter": None,
                "image_invvar_access": False, "morphology_access": False,
                "pixel_value_decode": False, "durable_regional_checkpoints": True}):
        raise CoaddPSFContractError("PROBE_BINDING_POLICY_INVALID")
    requests = binding.get("representative_requests")
    if not isinstance(requests, list) or len(requests) != 2:
        raise CoaddPSFContractError("PROBE_REPRESENTATIVE_COUNT_INVALID")
    if [(r["region"], r["slot"], r["point_id"]) for r in requests] != list(REPRESENTATIVES):
        raise CoaddPSFContractError("PROBE_REPRESENTATIVE_IDENTITY_INVALID")
    for row in requests:
        parsed = urlsplit(row["literal_url"])
        query = parse_qs(parsed.query, keep_blank_values=True)
        if (parsed.scheme != "https" or parsed.hostname != ALLOWED_HOST or
                parsed.port not in (None, 443) or parsed.path != ENDPOINT_PATH or
                parsed.fragment or set(query) != {"ra", "dec", "layer"} or
                query["layer"] != [f"ls-dr9-{row['region']}"] or
                "bands" in query or row["query_bands_parameter"] is not None or
                row["max_response_bytes"] != MAX_RESPONSE_BYTES):
            raise CoaddPSFContractError("PROBE_LITERAL_URL_INVALID")
    return binding


def load_probe_binding(path: Path, project: Path) -> tuple[dict, dict, dict]:
    _, base = _verified_inputs(project)
    identities = _canonical_load(Path(project).resolve() / IDENTITIES_RELATIVE)
    validate_identity_manifest(identities, base)
    binding = _canonical_load(path)
    validate_probe_binding(binding, project, identities, base)
    return binding, identities, base


def _card_value(card: bytes):
    text = card.decode("ascii", errors="strict")
    if text[8:10] != "= ":
        return None
    raw = text[10:80].split("/", 1)[0].strip()
    if raw.startswith("'") and raw.endswith("'"):
        return raw[1:-1].replace("''", "'").strip()
    if raw == "T":
        return True
    if raw == "F":
        return False
    try:
        return int(raw)
    except ValueError:
        try:
            return float(raw.replace("D", "E"))
        except ValueError:
            return raw


def _parse_header(body: bytes, start: int) -> tuple[dict, int]:
    cards = {}
    offset = start
    while offset + HEADER_BLOCK <= len(body):
        block = body[offset:offset + HEADER_BLOCK]
        for index in range(0, HEADER_BLOCK, 80):
            card = block[index:index + 80]
            key = card[:8].decode("ascii", errors="strict").strip()
            if key == "END":
                return cards, offset + HEADER_BLOCK
            if key and key not in cards:
                cards[key] = _card_value(card)
        offset += HEADER_BLOCK
    raise CoaddPSFContractError("FITS_HEADER_INCOMPLETE")


def _padded_data_bytes(header: dict) -> int:
    bitpix = abs(int(header.get("BITPIX", 0) or 0))
    naxis = int(header.get("NAXIS", 0) or 0)
    elements = 0 if naxis == 0 else 1
    for axis in range(1, naxis + 1):
        length = int(header.get(f"NAXIS{axis}", 0) or 0)
        if length < 0:
            raise CoaddPSFContractError("FITS_AXIS_INVALID")
        elements *= length
    raw = ((bitpix // 8) * elements + int(header.get("PCOUNT", 0) or 0))
    raw *= int(header.get("GCOUNT", 1) or 1)
    return ((raw + HEADER_BLOCK - 1) // HEADER_BLOCK) * HEADER_BLOCK


def _dtype(bitpix: int) -> str:
    values = {8: "uint8", 16: "int16", 32: "int32", 64: "int64",
              -32: "float32", -64: "float64"}
    if bitpix not in values:
        raise CoaddPSFContractError("FITS_BITPIX_UNSUPPORTED")
    return values[bitpix]


def _bands_from_primary(header: dict) -> list[str]:
    numbered = []
    for index in range(10):
        value = header.get(f"BAND{index}")
        if value is not None:
            numbered.append(str(value).strip().lower())
    if numbered:
        return numbered
    value = header.get("BANDS")
    if not isinstance(value, str):
        return []
    compact = value.strip().lower()
    if re.fullmatch(r"[grz]+", compact):
        return list(compact)
    return [item for item in re.split(r"[\s,]+", compact) if item]


def inspect_response(body: bytes) -> dict:
    """Inspect FITS structure without converting any array bytes to values."""
    if not body or len(body) > MAX_RESPONSE_BYTES or len(body) % HEADER_BLOCK:
        raise CoaddPSFContractError("FITS_RESPONSE_SIZE_INVALID")
    offset = 0
    hdus = []
    primary_bands = []
    while offset < len(body):
        if all(byte in (0, 32) for byte in body[offset:]):
            break
        header, header_end = _parse_header(body, offset)
        index = len(hdus)
        if index == 0 and header.get("SIMPLE") is not True:
            raise CoaddPSFContractError("FITS_PRIMARY_INVALID")
        if index > 0 and not header.get("XTENSION"):
            raise CoaddPSFContractError("FITS_EXTENSION_INVALID")
        naxis = int(header.get("NAXIS", 0) or 0)
        shape = [int(header.get(f"NAXIS{axis}", 0) or 0)
                 for axis in range(naxis, 0, -1)]
        data_bytes = _padded_data_bytes(header)
        data_end = header_end + data_bytes
        if data_end > len(body):
            raise CoaddPSFContractError("FITS_DATA_TRUNCATED")
        is_image = naxis > 0 and str(header.get("XTENSION", "IMAGE")).strip() != "BINTABLE"
        band = str(header.get("BAND", "")).strip().lower() or None
        if index == 0:
            primary_bands = _bands_from_primary(header)
        hdus.append({"physical_hdu": index, "xtension": header.get("XTENSION"),
                     "is_image": is_image, "shape": shape,
                     "dtype": _dtype(int(header.get("BITPIX", 0))) if is_image else None,
                     "band": band, "bunit": header.get("BUNIT"),
                     "normalization_headers": {key: value for key, value in header.items()
                                               if "NORM" in key.upper()},
                     "header_end": header_end, "data_offset": header_end,
                     "data_bytes_padded": data_bytes})
        offset = data_end
    image_hdus = [row for row in hdus if row["is_image"]]
    if not image_hdus:
        raise CoaddPSFContractError("FITS_IMAGE_HDU_MISSING")
    labelled = [row["band"] for row in image_hdus]
    if any(item is None for item in labelled):
        if len(primary_bands) != len(image_hdus):
            raise CoaddPSFContractError("FITS_BAND_LABELS_MISSING")
        labelled = primary_bands
    if (len(set(labelled)) != len(labelled) or
            any(item not in BANDS for item in labelled)):
        raise CoaddPSFContractError("FITS_BAND_LABELS_INVALID")
    if primary_bands and primary_bands != labelled:
        raise CoaddPSFContractError("FITS_BAND_HEADER_CONFLICT")
    for row, band in zip(image_hdus, labelled):
        row["band"] = band
    units = {row["band"]: row["bunit"] for row in image_hdus}
    normalization = {str(row["physical_hdu"]): row["normalization_headers"]
                     for row in hdus if row["normalization_headers"]}
    return {"representation_format": "FITS", "hdu_count": len(hdus),
            "image_hdu_count": len(image_hdus), "bands": labelled,
            "hdus": hdus, "units_by_band": units,
            "normalization_headers": normalization or None,
            "array_values_decoded": 0, "galaxy_pixels_accessed": 0,
            "image_invvar_accessed": 0, "morphology_accessed": 0}


def classify_mapping(regional: dict[str, dict]) -> dict:
    if set(regional) != {"south", "north"}:
        raise CoaddPSFContractError("REGIONAL_CONTRACT_INCOMPLETE")
    bands = {region: value["structure"]["bands"] for region, value in regional.items()}
    if all(value == list(BANDS) for value in bands.values()):
        decision, count = "A_ONE_RESPONSE_BUNDLES_G_R_Z", 18
    elif all(len(value) == 1 for value in bands.values()):
        decision, count = "B_ONE_RESPONSE_REPRESENTS_ONE_BAND", 54
    elif all(value and set(value).issubset(BANDS) for value in bands.values()):
        decision = "C_ANOTHER_EXPLICITLY_OBSERVED_MAPPING"
        count = sum(9 * (3 if len(value) == 1 else 1) for value in bands.values())
    else:
        raise CoaddPSFContractError("BAND_MAPPING_UNRESOLVED")
    signatures = {region: {"hdu_count": value["structure"]["hdu_count"],
                           "image_hdu_count": value["structure"]["image_hdu_count"],
                           "bands": value["structure"]["bands"],
                           "shapes": [r["shape"] for r in value["structure"]["hdus"]
                                      if r["is_image"]],
                           "dtypes": [r["dtype"] for r in value["structure"]["hdus"]
                                      if r["is_image"]]}
                  for region, value in regional.items()}
    return {"decision": decision, "future_http_response_count": count,
            "observational_identity_count": 54, "spatial_point_count": 18,
            "regional_returned_bands": bands,
            "same_schema_north_south": signatures["south"] == signatures["north"],
            "regional_schemas": signatures}


class LiteralPSFTransport:
    def __init__(self, urls: list[str]):
        self.urls = frozenset(urls)
        self.requests_started = 0
        self.body_bytes_observed = 0

    def get(self, url: str, max_bytes: int):
        if url not in self.urls:
            raise CoaddPSFContractError("URL_NOT_IN_REVIEWED_BINDING")
        parsed = urlsplit(url)
        conn = http.client.HTTPSConnection(parsed.hostname, timeout=30,
                                           context=ssl.create_default_context())
        try:
            self.requests_started += 1
            conn.request("GET", parsed.path + "?" + parsed.query,
                         headers={"Accept": "image/fits", "Accept-Encoding": "identity"})
            response = conn.getresponse()
            body = response.read(max_bytes + 1)
            self.body_bytes_observed += len(body)
            headers = {key.lower(): value for key, value in response.getheaders()}
            status = response.status
            response.close()
            return status, headers, body, url
        finally:
            conn.close()


class EvidenceStore:
    def __init__(self, root: Path, binding: dict):
        self.root = Path(root)
        if self.root.exists():
            raise CoaddPSFContractError("PROBE_LOCAL_STATE_CONFLICT")
        self.root.mkdir(parents=True)
        self.sequence = 0
        self.aggregate = {
            "schema_version": "OC3_COADD_PSF_PROBE_AGGREGATE_001",
            "stage_id": STAGE_ID, "binding_seal": binding["sealed"], "state": "ACTIVE",
            "counters": {"local_requests": 0, "local_body_bytes": 0,
                         "reserved_body_capacity": 0,
                         "cumulative_requests": START_REQUESTS,
                         "cumulative_body_bytes": START_BODY_BYTES,
                         "image_invvar_requests": 0, "morphology_accesses": 0,
                         "array_values_decoded": 0},
            "regions": [{"region": row["region"], "state": "NOT_STARTED",
                         "request_evidence": None, "regional_checkpoint": None,
                         "failure": None} for row in binding["representative_requests"]],
            "last_event": "INITIALIZED", "terminal": None,
        }
        _immutable_json(self.root / "PROBE_BINDING_COPY.json", binding)
        self._snapshot("INITIALIZED")

    def row(self, region: str) -> dict:
        return next(row for row in self.aggregate["regions"] if row["region"] == region)

    def _snapshot(self, event: str) -> None:
        self.sequence += 1
        self.aggregate["last_event"] = event
        value = _seal(self.aggregate)
        _immutable_json(self.root / "AGGREGATE_HISTORY" / f"{self.sequence:04d}.json", value)
        _atomic_json(self.root / "PROBE_AGGREGATE.json", value)

    def reserve(self, region: str, cap: int) -> None:
        counters = self.aggregate["counters"]
        if (counters["local_requests"] + 1 > MAX_NEW_REQUESTS or
                counters["reserved_body_capacity"] + cap > MAX_TOTAL_BODY_BYTES or
                counters["cumulative_body_bytes"] + cap > GLOBAL_BODY_CAP):
            raise CoaddPSFContractError("PROBE_BUDGET_EXCEEDED", region)
        counters["local_requests"] += 1
        counters["cumulative_requests"] += 1
        counters["reserved_body_capacity"] += cap
        self.row(region)["state"] = "REQUEST_RESERVED"
        self._snapshot(f"REQUEST_RESERVED:{region}")

    def record_body(self, region: str, size: int) -> None:
        counters = self.aggregate["counters"]
        if size < 0 or counters["local_body_bytes"] + size > MAX_TOTAL_BODY_BYTES:
            raise CoaddPSFContractError("PROBE_BODY_ACCOUNTING_INVALID", region)
        counters["local_body_bytes"] += size
        counters["cumulative_body_bytes"] += size
        self._snapshot(f"BODY_ACCOUNTED:{region}")

    def publish_request(self, request: dict, evidence: dict) -> dict:
        region = request["region"]
        value = _seal({"schema_version": "OC3_COADD_PSF_REQUEST_EVIDENCE_001",
                       "stage_id": STAGE_ID, "region": region,
                       "slot": request["slot"], "point_id": request["point_id"],
                       **evidence})
        relative = Path("REQUEST_EVIDENCE") / f"{region}.json"
        sha = _immutable_json(self.root / relative, value)
        row = self.row(region)
        row["state"] = "RESPONSE_IDENTITY_VALIDATED"
        row["request_evidence"] = {"path": str(relative), "sha256": sha,
                                   "seal": value["sealed"]}
        self._snapshot(f"RESPONSE_IDENTITY_VALIDATED:{region}")
        return value

    def publish_region(self, request: dict, evidence: dict) -> dict:
        region = request["region"]
        value = _seal({"schema_version": "OC3_COADD_PSF_REGIONAL_CHECKPOINT_001",
                       "stage_id": STAGE_ID, "region": region,
                       "slot": request["slot"], "point_id": request["point_id"],
                       "request_evidence": self.row(region)["request_evidence"],
                       **evidence})
        relative = Path("REGIONAL_CHECKPOINTS") / f"{region}.json"
        sha = _immutable_json(self.root / relative, value)
        row = self.row(region)
        row["state"] = "REGIONAL_CONTRACT_RESOLVED"
        row["regional_checkpoint"] = {"path": str(relative), "sha256": sha,
                                      "seal": value["sealed"]}
        self._snapshot(f"REGIONAL_CONTRACT_RESOLVED:{region}")
        return value

    def terminal(self, state: str, error: CoaddPSFContractError | None = None,
                 contract_sha256: str | None = None, mapping: dict | None = None) -> dict:
        counters = self.aggregate["counters"]
        value = {"stage_id": STAGE_ID, "state": state,
                 "error": error.code if error else None,
                 "region": error.region if error else None,
                 "network_requests_started": counters["local_requests"],
                 "network_bytes_observed": counters["local_body_bytes"],
                 "network_bytes_charged": counters["local_body_bytes"],
                 "cumulative_requests": counters["cumulative_requests"],
                 "cumulative_body_bytes": counters["cumulative_body_bytes"],
                 "regions_resolved": sum(r["state"] == "REGIONAL_CONTRACT_RESOLVED"
                                         for r in self.aggregate["regions"]),
                 "observational_identities": 54, "spatial_points": 18,
                 "future_http_response_count": (mapping or {}).get("future_http_response_count"),
                 "band_mapping_decision": (mapping or {}).get("decision"),
                 "resolved_contract_sha256": contract_sha256,
                 "image_invvar_requests": 0, "morphology_accesses": 0,
                 "array_values_decoded": 0}
        self.aggregate["state"] = state
        self.aggregate["terminal"] = value
        self._snapshot(f"TERMINAL:{state}")
        _immutable_json(self.root / "PROBE_TERMINAL.json", value)
        return value


def _resolved_contract(binding: dict, regional: dict[str, dict]) -> tuple[dict, dict]:
    mapping = classify_mapping(regional)
    unit_values = {region: checkpoint["structure"]["units_by_band"]
                   for region, checkpoint in regional.items()}
    units_observed = any(any(value is not None for value in values.values())
                         for values in unit_values.values())
    value = _seal({
        "schema_version": "OC3_COADD_PSF_RESOURCE_CONTRACT_RESOLVED_001",
        "stage_id": STAGE_ID,
        "binding_seal": binding["sealed"],
        "provider_contract": {
            "endpoint": {"state": "DOCUMENTED", "value": ENDPOINT_PATH},
            "required_query_parameters": {"state": "SOURCE_VERIFIED",
                                           "value": ["ra", "dec", "layer"]},
            "band_query_parameter": {"state": "SOURCE_VERIFIED_OPTIONAL_NOT_USED",
                                     "value": None},
            "response_content_type": {"state": "OBSERVED_BY_BOUNDED_PROBE",
                                      "value": "image/fits"},
            "representation": {"state": "OBSERVED_BY_BOUNDED_PROBE", "value": "FITS"},
            "band_mapping": {"state": "OBSERVED_BY_BOUNDED_PROBE",
                             "value": mapping},
            "normalization": {"state": "SOURCE_VERIFIED",
                              "value": "normalizePsf=True; median-invvar weighted per band"},
            "units": {"state": "OBSERVED_BY_BOUNDED_PROBE" if units_observed else "UNRESOLVED",
                      "value": unit_values if units_observed else None},
            "deployment_version": {"state": "UNRESOLVED", "value": None},
        },
        "regional_contracts": regional,
        "counts": {"observational_identities": 54, "spatial_points": 18,
                   "representative_probe_requests": 2,
                   "future_http_responses": mapping["future_http_response_count"]},
        "negative_evidence": {"image_invvar_requests": 0, "morphology_accesses": 0,
                              "array_values_decoded": 0},
    })
    return value, mapping


def run_probe(binding: dict, transport, audit_root: Path) -> tuple[dict, bool]:
    store = EvidenceStore(audit_root, binding)
    regional = {}
    current = None
    try:
        for request in binding["representative_requests"]:
            current = request["region"]
            before_bytes = getattr(transport, "body_bytes_observed", 0)
            store.reserve(current, request["max_response_bytes"])
            try:
                status, headers, body, final_url = transport.get(
                    request["literal_url"], request["max_response_bytes"])
            except CoaddPSFContractError:
                delta = getattr(transport, "body_bytes_observed", before_bytes) - before_bytes
                if delta:
                    store.record_body(current, delta)
                raise
            store.record_body(current, len(body))
            content_type = headers.get("content-type", "").split(";", 1)[0].strip().lower()
            raw_content_length = headers.get("content-length")
            try:
                parsed_content_length = (int(raw_content_length)
                                         if raw_content_length is not None else None)
            except ValueError:
                parsed_content_length = None
            request_evidence = store.publish_request(request, {
                "literal_url": request["literal_url"], "status": status,
                "content_type": content_type,
                "content_length_header": raw_content_length,
                "content_length": parsed_content_length,
                "etag": headers.get("etag"), "last_modified": headers.get("last-modified"),
                "exact_byte_count": len(body),
                "response_sha256": hashlib.sha256(body).hexdigest(),
            })
            if len(body) > request["max_response_bytes"]:
                raise CoaddPSFContractError("HTTP_BODY_EXCEEDS_BOUND", current,
                                            observed_bytes=len(body))
            if status != 200:
                raise CoaddPSFContractError("HTTP_STATUS_NOT_200", current)
            if final_url != request["literal_url"]:
                raise CoaddPSFContractError("HTTP_REDIRECT_OR_IDENTITY_CHANGE", current)
            if headers.get("content-encoding", "identity").lower() != "identity":
                raise CoaddPSFContractError("HTTP_CONTENT_ENCODING_INVALID", current)
            if content_type != "image/fits":
                raise CoaddPSFContractError("HTTP_CONTENT_TYPE_INVALID", current)
            if raw_content_length is not None and parsed_content_length is None:
                raise CoaddPSFContractError("HTTP_CONTENT_LENGTH_INVALID", current)
            if parsed_content_length is not None and parsed_content_length != len(body):
                raise CoaddPSFContractError("HTTP_CONTENT_LENGTH_MISMATCH", current)
            structure = inspect_response(body)
            checkpoint = store.publish_region(request, {
                "request_evidence_seal": request_evidence["sealed"],
                "structure": structure})
            regional[current] = {"request": {"literal_url": request["literal_url"],
                                              "slot": request["slot"],
                                              "point_id": request["point_id"],
                                              "layer": request["layer"]},
                                 "response": {"status": status,
                                              "content_type": content_type,
                                              "exact_byte_count": len(body),
                                              "response_sha256": hashlib.sha256(body).hexdigest(),
                                              "etag": headers.get("etag"),
                                              "last_modified": headers.get("last-modified")},
                                 "structure": structure,
                                 "checkpoint_sha256": store.row(current)["regional_checkpoint"]["sha256"]}
        resolved, mapping = _resolved_contract(binding, regional)
        path = store.root / "COADD_PSF_RESOURCE_CONTRACT_RESOLVED.json"
        sha = _immutable_json(path, resolved)
        return store.terminal(SUCCESS, contract_sha256=sha, mapping=mapping), True
    except CoaddPSFContractError as error:
        if error.region is None:
            error.region = current
        if current is not None:
            row = store.row(current)
            row["state"] = "FAILED"
            row["failure"] = {"code": error.code}
        return store.terminal(PARTIAL, error=error), False
    except (OSError, TimeoutError, UnicodeError, ValueError):
        error = CoaddPSFContractError("PROBE_IO_OR_TRANSPORT_FAILURE", current)
        if current is not None:
            row = store.row(current)
            row["state"] = "FAILED"
            row["failure"] = {"code": error.code}
        return store.terminal(PARTIAL, error=error), False


def dry_run(binding: dict, project: Path) -> dict:
    return {"stage_id": STAGE_ID, "state": READY,
            "representative_requests": len(binding["representative_requests"]),
            "regions": [r["region"] for r in binding["representative_requests"]],
            "observational_identities": 54, "spatial_points": 18,
            "starting_cumulative_requests": START_REQUESTS,
            "starting_cumulative_body_bytes": START_BODY_BYTES,
            "max_new_requests": MAX_NEW_REQUESTS,
            "max_response_bytes": MAX_RESPONSE_BYTES,
            "max_total_body_bytes": MAX_TOTAL_BODY_BYTES,
            "retries": RETRIES, "concurrency": CONCURRENCY,
            "image_invvar_requests": 0, "morphology_accesses": 0,
            "array_values_decoded": 0, "network_requests": 0,
            "command_argv": exact_command(project),
            "implementation_aggregate": implementation_hash(project)}
