"""Closed DR9 coadd resource contracts and bounded auxiliary acquisition.

This module never derives provider directory components.  A network-capable
operation accepts only a separately reviewed, sealed binding containing each
literal URL.  Contract probing reads FITS header blocks only; it has no array
decoder.
"""
from __future__ import annotations

import csv
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import shutil
import ssl
from typing import Callable, Iterable
from urllib.parse import urlsplit

from .core import canonical, file_hash


STAGE_ID = "OC3-RESOURCE-CONTRACT-AUXILIARY-ACQUISITION-001"
PROBE_ID = "OC3-RESOURCE-CONTRACT-PROBE-001"
SCHEMA_VERSION = "OC3_DR9_COADD_RESOURCE_CONTRACT_001"
PROBE_BINDING_VERSION = "OC3_DR9_COADD_RESOURCE_PROBE_BINDING_001"
SUCCESS_TERMINAL = "AUXILIARY_PRODUCTS_ACQUIRED"
FAILURE_TERMINAL = "AUXILIARY_ACQUISITION_FAILED"
PROBE_SUCCESS = "RESOURCE_CONTRACT_PROBE_RESOLVED"
PROBE_PARTIAL = "RESOURCE_CONTRACT_PROBE_PARTIALLY_RESOLVED"
BRICKS_SHA256 = "147c0942a5340ed18eec23a610f8afd5721390fad09c1da7ed01593deb40fab6"
SPEC_SHA256 = "dca2e5f8fe7d0783554116e042c02bcddde7bb083e05a31939fc2fd2bc9151ae"

GLOBAL_MAX_BYTES = 1_610_612_736
GLOBAL_MAX_REQUESTS = 200
IMPORTED_USED_BYTES = 89_461_646
IMPORTED_USED_REQUESTS = 8
REMAINING_BYTES = 1_521_151_090
REMAINING_REQUESTS = 192
PSF_RESERVATION_BYTES = 54 * 2**20
DISK_INCREMENTAL_MAX_BYTES = 4 * 2**30
IO_MAX_BYTES = 8 * 2**30
RAM_MAX_BYTES = 2 * 2**30
HEADER_BLOCK = 2880
PROBE_MAX_HEADER_BLOCKS_PER_RESOURCE = 6
PROBE_MAX_REQUESTS = 14 + 14 * PROBE_MAX_HEADER_BLOCKS_PER_RESOURCE
PROBE_MAX_BYTES = 14 * PROBE_MAX_HEADER_BLOCKS_PER_RESOURCE * HEADER_BLOCK
ALLOWED_HOST = "portal.nersc.gov"
PROPERTY_STATES = frozenset(("DOCUMENTED", "OBSERVED_BY_BOUNDED_PROBE", "UNRESOLVED"))
BANDS = ("g", "r", "z")
AUX_ORDER = tuple((region, product, band)
                  for region in ("south", "north")
                  for product, bands in (("nexp", BANDS), ("psfsize", BANDS), ("maskbits", (None,)))
                  for band in bands)
FUTURE_ORDER = tuple((region, product, band)
                     for region in ("south", "north")
                     for product in ("image", "invvar") for band in BANDS)


class ResourceContractError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _seal(value: dict) -> dict:
    body = dict(value)
    body.pop("sealed", None)
    body["sealed"] = hashlib.sha256(canonical(body)).hexdigest()
    return body


def _verify_seal(value: dict) -> None:
    if not isinstance(value, dict) or not re.fullmatch(r"[0-9a-f]{64}", str(value.get("sealed", ""))):
        raise ResourceContractError("CONTRACT_SEAL_INVALID")
    if _seal(value)["sealed"] != value["sealed"]:
        raise ResourceContractError("CONTRACT_SEAL_INVALID")


def _prop(state: str, value, *evidence: str) -> dict:
    if state not in PROPERTY_STATES:
        raise ResourceContractError("PROPERTY_STATE_INVALID")
    return {"state": state, "value": value, "evidence": list(evidence)}


def _strict(value: dict, keys: set[str], code: str) -> None:
    if not isinstance(value, dict) or set(value) != keys:
        raise ResourceContractError(code)


def load_frozen_bricks(path: Path) -> dict[str, str]:
    path = Path(path)
    if not path.is_file() or path.is_symlink() or file_hash(path) != BRICKS_SHA256:
        raise ResourceContractError("FROZEN_BRICKS_BINDING_FAILURE")
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
    except (OSError, UnicodeError, csv.Error) as exc:
        raise ResourceContractError("FROZEN_BRICKS_BINDING_FAILURE") from exc
    expected = ["region", "brickname", "development", "holdout_disjoint", "evidence_ref"]
    if len(rows) != 2 or list(rows[0]) != expected:
        raise ResourceContractError("FROZEN_BRICKS_BINDING_FAILURE")
    result: dict[str, str] = {}
    for row in rows:
        if (row["region"] not in ("south", "north") or row["region"] in result or
                row["development"] != "true" or row["holdout_disjoint"] != "true" or
                not re.fullmatch(r"[0-9]{4}[pm][0-9]{3}", row["brickname"]) or
                not row["evidence_ref"]):
            raise ResourceContractError("FROZEN_BRICKS_BINDING_FAILURE")
        result[row["region"]] = row["brickname"]
    if set(result) != {"south", "north"}:
        raise ResourceContractError("FROZEN_BRICKS_BINDING_FAILURE")
    return result


def _filename(brick: str, product: str, band: str | None) -> str:
    suffix = f"-{band}" if band is not None else ""
    return f"legacysurvey-{brick}-{product}{suffix}.fits.fz"


def _rid(region: str, brick: str, product: str, band: str | None) -> str:
    raw = canonical({"region": region, "brick": brick, "product": product, "band": band,
                     "release": "DR9", "generation": "coadd"})
    return "oc3_" + hashlib.sha256(raw).hexdigest()[:24]


def _units_dtype(product: str) -> dict:
    values = {
        "image": {"units": "nanomaggies per pixel", "dtype": None},
        "invvar": {"units": None, "dtype": None},
        "nexp": {"units": "number of contributing exposures per pixel", "dtype": None},
        "psfsize": {"units": "arcsec FWHM per pixel", "dtype": None},
        "maskbits": {"units": "bit mask", "dtype": None},
    }
    return values[product]


def _hdu(product: str) -> tuple[str, object]:
    if product == "image":
        return "DOCUMENTED", {"logical_hdu": 0, "logical_role": "coadded image",
                              "physical_hdu": None, "compression_mapping": None}
    if product == "maskbits":
        return "DOCUMENTED", {"logical_hdu": 1, "logical_role": "optical MASKBITS",
                              "excluded_logical_hdus": [2, 3], "excluded_roles": ["WISE W1", "WISE W2"],
                              "physical_hdu": None, "compression_mapping": None}
    return "UNRESOLVED", None


def _resource(region: str, brick: str, product: str, band: str | None, batch: str) -> dict:
    doc = "official DR9 Legacy Surveys file model"
    hdu_state, hdu_value = _hdu(product)
    units = _units_dtype(product)
    units_state = "DOCUMENTED" if units["units"] is not None else "UNRESOLVED"
    role = {
        "image": "native coadded science image", "invvar": "native coadd inverse variance",
        "nexp": "native number-of-exposures map", "psfsize": "native weighted-average PSF FWHM map",
        "maskbits": "native optical mask bit map",
    }[product]
    return {
        "resource_id": _rid(region, brick, product, band), "batch": batch,
        "region": _prop("DOCUMENTED", region, "frozen development-brick row"),
        "brick": _prop("DOCUMENTED", brick, f"sha256:{BRICKS_SHA256}"),
        "product": _prop("DOCUMENTED", product, doc),
        "band": _prop("DOCUMENTED", band, doc),
        "literal_url": _prop("UNRESOLVED", None),
        "filename": _prop("DOCUMENTED", _filename(brick, product, band), doc),
        "directory_component": _prop("UNRESOLVED", None),
        "expected_logical_role": _prop("DOCUMENTED", role, doc),
        "hdu_contract": _prop(hdu_state, hdu_value, doc) if hdu_value is not None else _prop(hdu_state, None),
        "expected_shape": _prop("DOCUMENTED", [3600, 3600], doc),
        "wcs_contract": _prop("DOCUMENTED", {"projection": "TAN", "nominal_pixel_scale_arcsec": 0.262}, doc),
        "units_dtype_contract": _prop(units_state, units, doc) if units_state == "DOCUMENTED" else _prop("UNRESOLVED", units, doc),
        "representation_constraints": _prop("DOCUMENTED", {
            "filename_suffix": ".fits.fz", "content_encoding": "identity", "native_grid_only": True,
            "logical_physical_hdu_mapping": None, "no_resampling": True,
        }, doc),
        "max_bytes": _prop("UNRESOLVED", None),
        "rights_state": _prop("DOCUMENTED", {
            "analysis": True, "local_preservation": True, "redistribution": False,
        }, "OC3 metadata-bootstrap rights governance"),
        "evidence_source": _prop("DOCUMENTED", [doc, f"sha256:{SPEC_SHA256}"]),
    }


def build_contract(bricks: dict[str, str], *, used_bytes: int = IMPORTED_USED_BYTES,
                   used_requests: int = IMPORTED_USED_REQUESTS) -> dict:
    if set(bricks) != {"south", "north"}:
        raise ResourceContractError("EXACT_TWO_BRICKS_REQUIRED")
    resources = []
    for region, product, band in AUX_ORDER:
        resources.append(_resource(region, bricks[region], product, band, "AUXILIARY_FIRST"))
    for region, product, band in FUTURE_ORDER:
        resources.append(_resource(region, bricks[region], product, band, "FUTURE_IMAGE_INVVAR"))
    value = {
        "schema_version": SCHEMA_VERSION, "stage_id": STAGE_ID,
        "development_bricks_sha256": BRICKS_SHA256, "resources": resources,
        "budget": {
            "global_max_bytes": GLOBAL_MAX_BYTES, "global_max_requests": GLOBAL_MAX_REQUESTS,
            "used_bytes": used_bytes, "used_requests": used_requests,
            "remaining_bytes": GLOBAL_MAX_BYTES - used_bytes,
            "remaining_requests": GLOBAL_MAX_REQUESTS - used_requests,
            "psf_reservation_bytes": PSF_RESERVATION_BYTES,
            "disk_incremental_max_bytes": DISK_INCREMENTAL_MAX_BYTES,
            "io_max_bytes": IO_MAX_BYTES, "ram_max_bytes": RAM_MAX_BYTES,
            "concurrency": 1,
        },
    }
    validate_contract(_seal(value), require_resolved_aux=False)
    return _seal(value)


RESOURCE_KEYS = {"resource_id", "batch", "region", "brick", "product", "band", "literal_url",
                 "filename", "directory_component", "expected_logical_role", "hdu_contract",
                 "expected_shape", "wcs_contract", "units_dtype_contract", "representation_constraints",
                 "max_bytes", "rights_state", "evidence_source"}
TOP_KEYS = {"schema_version", "stage_id", "development_bricks_sha256", "resources", "budget", "sealed"}
PROP_KEYS = {"state", "value", "evidence"}
BUDGET_KEYS = {"global_max_bytes", "global_max_requests", "used_bytes", "used_requests",
               "remaining_bytes", "remaining_requests", "psf_reservation_bytes",
               "disk_incremental_max_bytes", "io_max_bytes", "ram_max_bytes", "concurrency"}


def validate_contract(value: dict, *, require_resolved_aux: bool) -> dict:
    _strict(value, TOP_KEYS, "CONTRACT_SCHEMA_INVALID")
    _verify_seal(value)
    if (value["schema_version"] != SCHEMA_VERSION or value["stage_id"] != STAGE_ID or
            value["development_bricks_sha256"] != BRICKS_SHA256):
        raise ResourceContractError("CONTRACT_BINDING_INVALID")
    _strict(value["budget"], BUDGET_KEYS, "CONTRACT_BUDGET_INVALID")
    budget = value["budget"]
    if (budget["global_max_bytes"] != GLOBAL_MAX_BYTES or budget["global_max_requests"] != GLOBAL_MAX_REQUESTS or
            budget["used_bytes"] < IMPORTED_USED_BYTES or budget["used_requests"] < IMPORTED_USED_REQUESTS or
            budget["remaining_bytes"] != GLOBAL_MAX_BYTES - budget["used_bytes"] or
            budget["remaining_requests"] != GLOBAL_MAX_REQUESTS - budget["used_requests"] or
            budget["psf_reservation_bytes"] != PSF_RESERVATION_BYTES or
            budget["disk_incremental_max_bytes"] != DISK_INCREMENTAL_MAX_BYTES or
            budget["io_max_bytes"] != IO_MAX_BYTES or budget["ram_max_bytes"] != RAM_MAX_BYTES or
            budget["concurrency"] != 1):
        raise ResourceContractError("CONTRACT_BUDGET_INVALID")
    rows = value["resources"]
    if not isinstance(rows, list) or len(rows) != 26:
        raise ResourceContractError("CONTRACT_RESOURCE_COUNT_INVALID")
    identities = []
    for row in rows:
        _strict(row, RESOURCE_KEYS, "CONTRACT_RESOURCE_SCHEMA_INVALID")
        if row["batch"] not in ("AUXILIARY_FIRST", "FUTURE_IMAGE_INVVAR"):
            raise ResourceContractError("CONTRACT_BATCH_INVALID")
        for key in RESOURCE_KEYS - {"resource_id", "batch"}:
            _strict(row[key], PROP_KEYS, "CONTRACT_PROPERTY_SCHEMA_INVALID")
            if row[key]["state"] not in PROPERTY_STATES or not isinstance(row[key]["evidence"], list):
                raise ResourceContractError("CONTRACT_PROPERTY_STATE_INVALID")
        ident = (row["region"]["value"], row["product"]["value"], row["band"]["value"])
        identities.append(ident)
        if row["resource_id"] != _rid(row["region"]["value"], row["brick"]["value"],
                                      row["product"]["value"], row["band"]["value"]):
            raise ResourceContractError("CONTRACT_RESOURCE_ID_INVALID")
        if require_resolved_aux and row["batch"] == "AUXILIARY_FIRST":
            for key in ("literal_url", "directory_component", "hdu_contract", "max_bytes"):
                if row[key]["state"] == "UNRESOLVED" or row[key]["value"] is None:
                    raise ResourceContractError("AUXILIARY_CONTRACT_UNRESOLVED")
    if identities != list(AUX_ORDER) + list(FUTURE_ORDER) or len(set(identities)) != 26:
        raise ResourceContractError("CONTRACT_RESOURCE_ORDER_INVALID")
    return value


def unresolved_fields(contract: dict, batch: str = "AUXILIARY_FIRST") -> list[dict]:
    result = []
    for row in contract["resources"]:
        if row["batch"] != batch:
            continue
        fields = sorted(key for key in RESOURCE_KEYS - {"resource_id", "batch"}
                        if row[key]["state"] == "UNRESOLVED")
        if fields:
            result.append({"resource_id": row["resource_id"], "fields": fields})
    return result


def dry_run(bricks_path: Path, project: Path) -> dict:
    contract = build_contract(load_frozen_bricks(bricks_path))
    auxiliary = [row for row in contract["resources"] if row["batch"] == "AUXILIARY_FIRST"]
    return {
        "stage_id": STAGE_ID, "state": "RESOURCE_CONTRACT_DRY_RUN",
        "network_requests": 0, "science_pixels_decoded": 0,
        "inventory": auxiliary, "inventory_count": len(auxiliary),
        "future_image_invvar_count": 12,
        "unresolved": unresolved_fields(contract),
        "projected_probe_envelope": {"max_requests": PROBE_MAX_REQUESTS, "max_bytes": PROBE_MAX_BYTES,
                                     "header_block_bytes": HEADER_BLOCK},
        "max_byte_reservations": {"known_auxiliary_bytes": None, "psf_bytes": PSF_RESERVATION_BYTES,
                                  "remaining_global_bytes": REMAINING_BYTES,
                                  "disk_incremental_max_bytes": DISK_INCREMENTAL_MAX_BYTES,
                                  "io_max_bytes": IO_MAX_BYTES, "ram_max_bytes": RAM_MAX_BYTES},
        "future_bulk_command": (
            f"{project}/oc3/.venv/bin/python {project}/oc3/oc3_resource_contract.py "
            f"--acquire-auxiliary --execute-network --project {project} "
            f"--contract-manifest {project}/oc3/resource_contract/{PROBE_ID}/RESOURCE_CONTRACT_RESOLVED.json "
            f"--authorization {project}/oc3/INPUTS/OC3_AUXILIARY_ACQUISITION_AUTHORIZATION_001.json"
        ),
        "bulk_authorized": False,
    }


PROBE_TOP_KEYS = {"schema_version", "stage_id", "development_bricks_sha256", "aaa_evidence",
                  "resources", "sealed"}
PROBE_RESOURCE_KEYS = {"resource_id", "region", "brick", "product", "band", "filename",
                       "directory_component", "literal_url", "max_bytes"}


def load_probe_binding(path: Path, base_contract: dict) -> dict:
    try:
        raw = Path(path).read_bytes(); value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise ResourceContractError("PROBE_BINDING_INVALID") from exc
    if raw != canonical(value) + b"\n":
        raise ResourceContractError("PROBE_BINDING_NOT_CANONICAL")
    _strict(value, PROBE_TOP_KEYS, "PROBE_BINDING_INVALID"); _verify_seal(value)
    if (value["schema_version"] != PROBE_BINDING_VERSION or value["stage_id"] != PROBE_ID or
            value["development_bricks_sha256"] != BRICKS_SHA256 or
            not isinstance(value["aaa_evidence"], dict) or set(value["aaa_evidence"]) != {"south", "north"} or
            any(not isinstance(value["aaa_evidence"][r], list) or not value["aaa_evidence"][r]
                for r in ("south", "north"))):
        raise ResourceContractError("PROBE_BINDING_INVALID")
    expected = [r for r in base_contract["resources"] if r["batch"] == "AUXILIARY_FIRST"]
    if not isinstance(value["resources"], list) or len(value["resources"]) != 14:
        raise ResourceContractError("PROBE_BINDING_INVALID")
    for candidate, row in zip(value["resources"], expected):
        _strict(candidate, PROBE_RESOURCE_KEYS, "PROBE_BINDING_INVALID")
        for key in ("resource_id",):
            if candidate[key] != row[key]: raise ResourceContractError("PROBE_IDENTITY_MISMATCH")
        for key in ("region", "brick", "product", "band", "filename"):
            if candidate[key] != row[key]["value"]: raise ResourceContractError("PROBE_IDENTITY_MISMATCH")
        if (not isinstance(candidate["directory_component"], str) or
                not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", candidate["directory_component"]) or
                not isinstance(candidate["max_bytes"], int) or candidate["max_bytes"] <= 0):
            raise ResourceContractError("PROBE_BOUND_INVALID")
        url = candidate["literal_url"]; parsed = urlsplit(url)
        expected_path = (f"/cfs/cosmo/data/legacysurvey/dr9/{candidate['region']}/coadd/"
                         f"{candidate['directory_component']}/{candidate['brick']}/{candidate['filename']}")
        if (parsed.scheme != "https" or parsed.hostname != ALLOWED_HOST or parsed.port not in (None, 443) or
                parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path != expected_path):
            raise ResourceContractError("PROBE_URL_INVALID")
    return value


def _card_value(card: bytes):
    text = card.decode("ascii", errors="strict")
    if text[8:10] != "= ": return None
    raw = text[10:80].split("/", 1)[0].strip()
    if raw.startswith("'") and raw.endswith("'"): return raw[1:-1].replace("''", "'").strip()
    if raw == "T": return True
    if raw == "F": return False
    try: return int(raw)
    except ValueError:
        try: return float(raw.replace("D", "E"))
        except ValueError: return raw


def parse_header_blocks(read_block: Callable[[int, int], bytes], start: int,
                        blocks_left: list[int]) -> tuple[dict, int, int]:
    cards: dict[str, object] = {}; offset = start; consumed = 0
    while blocks_left[0] > 0:
        data = read_block(offset, offset + HEADER_BLOCK - 1)
        if len(data) != HEADER_BLOCK: raise ResourceContractError("FITS_HEADER_RANGE_SHORT")
        blocks_left[0] -= 1; consumed += 1
        for index in range(0, HEADER_BLOCK, 80):
            card = data[index:index + 80]
            key = card[:8].decode("ascii", errors="strict").strip()
            if key == "END": return cards, offset + HEADER_BLOCK, consumed
            if key and key not in cards: cards[key] = _card_value(card)
        offset += HEADER_BLOCK
    raise ResourceContractError("FITS_HEADER_BLOCK_CAP")


def _padded_data_bytes(header: dict) -> int:
    if header.get("XTENSION") == "BINTABLE":
        size = int(header.get("NAXIS1", 0)) * int(header.get("NAXIS2", 0)) + int(header.get("PCOUNT", 0))
    else:
        bitpix = abs(int(header.get("BITPIX", 0))); axes = int(header.get("NAXIS", 0))
        size = 0 if axes == 0 else bitpix // 8
        for axis in range(1, axes + 1): size *= int(header.get(f"NAXIS{axis}", 0))
        if axes: size += int(header.get("PCOUNT", 0))
    return ((size + HEADER_BLOCK - 1) // HEADER_BLOCK) * HEADER_BLOCK


def inspect_fits_header_structure(read_block: Callable[[int, int], bytes], product: str) -> dict:
    """Inspect only FITS header blocks; no data offset is ever requested."""
    blocks = [PROBE_MAX_HEADER_BLOCKS_PER_RESOURCE]
    primary, next_offset, used = parse_header_blocks(read_block, 0, blocks)
    records = [{"physical_hdu": 0, "xtension": primary.get("XTENSION"), "naxis": primary.get("NAXIS"),
                "zimage": primary.get("ZIMAGE"), "znaxis1": primary.get("ZNAXIS1"),
                "znaxis2": primary.get("ZNAXIS2"), "zbitpix": primary.get("ZBITPIX")}]
    primary_image = int(primary.get("NAXIS", 0) or 0) == 2
    if not primary_image:
        extension_start = next_offset + _padded_data_bytes(primary)
        extension, _, extra = parse_header_blocks(read_block, extension_start, blocks); used += extra
        records.append({"physical_hdu": 1, "xtension": extension.get("XTENSION"),
                        "naxis": extension.get("NAXIS"), "zimage": extension.get("ZIMAGE"),
                        "znaxis1": extension.get("ZNAXIS1"), "znaxis2": extension.get("ZNAXIS2"),
                        "zbitpix": extension.get("ZBITPIX")})
    logical_physical = 0 if primary_image else 1
    image_header = primary if primary_image else extension
    compressed = image_header.get("ZIMAGE") is True
    shape = ([int(image_header.get("ZNAXIS2")), int(image_header.get("ZNAXIS1"))]
             if compressed and image_header.get("ZNAXIS1") and image_header.get("ZNAXIS2")
             else [int(image_header.get("NAXIS2", 0)), int(image_header.get("NAXIS1", 0))])
    if shape != [3600, 3600]: raise ResourceContractError("FITS_NOMINAL_SHAPE_MISMATCH")
    return {"physical_headers": records, "physical_image_hdu": logical_physical,
            "compressed_image": compressed, "shape": shape, "header_blocks_read": used,
            "science_pixels_decoded": 0, "product": product}


class LiteralHTTPTransport:
    """HTTPS transport closed to the exact URLs of one reviewed binding."""
    def __init__(self, urls: Iterable[str]):
        self.urls = frozenset(urls); self.requests_started = 0; self.body_bytes_observed = 0
    def _request(self, url: str, method: str, headers: dict[str, str], body_cap: int = 0) -> tuple[int, dict, bytes, str]:
        if url not in self.urls: raise ResourceContractError("URL_NOT_IN_REVIEWED_BINDING")
        parsed = urlsplit(url)
        conn = http.client.HTTPSConnection(parsed.hostname, timeout=30, context=ssl.create_default_context())
        try:
            self.requests_started += 1
            conn.request(method, parsed.path, headers={"Accept-Encoding": "identity", **headers})
            response = conn.getresponse()
            body = response.read(body_cap + 1) if method == "GET" else b""
            self.body_bytes_observed += len(body)
            if method == "GET" and len(body) > body_cap:
                raise ResourceContractError("HTTP_BODY_EXCEEDS_BOUND")
            result = (response.status, {k.lower(): v for k, v in response.getheaders()}, body, url)
            response.close(); return result
        finally: conn.close()
    def head(self, url: str): return self._request(url, "HEAD", {})
    def range(self, url: str, start: int, end: int):
        return self._request(url, "GET", {"Range": f"bytes={start}-{end}"}, end - start + 1)
    def get(self, url: str, max_bytes: int): return self._request(url, "GET", {}, max_bytes)


def _head(transport, row: dict) -> dict:
    status, headers, body, final_url = transport.head(row["literal_url"])
    if body or status != 200 or final_url != row["literal_url"] or headers.get("content-encoding", "identity") != "identity":
        raise ResourceContractError("HEAD_IDENTITY_FAILURE")
    try: length = int(headers["content-length"])
    except (KeyError, ValueError) as exc: raise ResourceContractError("HEAD_LENGTH_UNRESOLVED") from exc
    if length <= 0 or length > row["max_bytes"]: raise ResourceContractError("HEAD_LENGTH_OUT_OF_BOUND")
    return {"status": 200, "content_length": length, "etag": headers.get("etag"),
            "last_modified": headers.get("last-modified")}


def probe_contract(base_contract: dict, binding: dict, transport, *,
                   max_requests: int = PROBE_MAX_REQUESTS,
                   max_bytes: int = PROBE_MAX_BYTES) -> tuple[dict, dict]:
    validate_contract(base_contract, require_resolved_aux=False); _verify_seal(binding)
    if max_requests <= 0 or max_requests > PROBE_MAX_REQUESTS or max_bytes <= 0 or max_bytes > PROBE_MAX_BYTES:
        raise ResourceContractError("PROBE_BUDGET_INVALID")
    candidates = binding["resources"]
    observations = {}; request_count = 0; byte_count = 0
    # All identity/size checks precede every range request.
    for row in candidates:
        if request_count + 1 > max_requests: raise ResourceContractError("PROBE_BUDGET_EXCEEDED")
        observations[row["resource_id"]] = {"head": _head(transport, row)}; request_count += 1
    for row in candidates:
        def read_block(start: int, end: int, row=row) -> bytes:
            nonlocal request_count, byte_count
            expected_bytes = end - start + 1
            if request_count + 1 > max_requests or byte_count + expected_bytes > max_bytes:
                raise ResourceContractError("PROBE_BUDGET_EXCEEDED")
            status, headers, body, final_url = transport.range(row["literal_url"], start, end)
            expected = f"bytes {start}-{end}/{observations[row['resource_id']]['head']['content_length']}"
            if (status != 206 or final_url != row["literal_url"] or headers.get("content-range") != expected or
                    headers.get("content-encoding", "identity") != "identity" or len(body) != end - start + 1):
                raise ResourceContractError("RANGE_NOT_EXACT")
            request_count += 1; byte_count += len(body)
            return body
        observations[row["resource_id"]]["fits"] = inspect_fits_header_structure(read_block, row["product"])
    result = json.loads(json.dumps(base_contract))
    index = {r["resource_id"]: r for r in result["resources"]}
    evidence = f"{PROBE_ID}:sealed:{binding['sealed']}"
    for candidate in candidates:
        row = index[candidate["resource_id"]]; obs = observations[candidate["resource_id"]]
        row["literal_url"] = _prop("OBSERVED_BY_BOUNDED_PROBE", candidate["literal_url"], evidence)
        row["directory_component"] = _prop("OBSERVED_BY_BOUNDED_PROBE", candidate["directory_component"], evidence)
        row["max_bytes"] = _prop("OBSERVED_BY_BOUNDED_PROBE", obs["head"]["content_length"], evidence)
        old = row["hdu_contract"]["value"] or {}
        row["hdu_contract"] = _prop("OBSERVED_BY_BOUNDED_PROBE", {
            **old, "logical_hdu": old.get("logical_hdu", obs["fits"]["physical_image_hdu"]),
            "logical_role": old.get("logical_role", row["expected_logical_role"]["value"]),
            "physical_image_hdu": obs["fits"]["physical_image_hdu"],
            "compression_mapping": "logical role mapped through FITS tiled-image compression"
                if obs["fits"]["compressed_image"] else "uncompressed physical image HDU",
        }, evidence)
        rep = row["representation_constraints"]["value"]
        row["representation_constraints"] = _prop("OBSERVED_BY_BOUNDED_PROBE", {
            **rep, "logical_physical_hdu_mapping": row["hdu_contract"]["value"]["compression_mapping"],
            "content_length": obs["head"]["content_length"], "etag": obs["head"]["etag"],
        }, evidence)
    result["budget"]["used_bytes"] += byte_count
    result["budget"]["used_requests"] += request_count
    result["budget"]["remaining_bytes"] -= byte_count
    result["budget"]["remaining_requests"] -= request_count
    result = _seal(result); validate_contract(result, require_resolved_aux=True)
    summary = {"stage_id": PROBE_ID, "state": PROBE_SUCCESS, "network_requests": request_count,
               "network_bytes": byte_count, "science_pixels_decoded": 0,
               "resources_observed": 14, "observations": observations,
               "resolved_contract_sha256": result["sealed"]}
    return result, summary


def _append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab") as handle:
        handle.write(canonical(row) + b"\n"); handle.flush(); os.fsync(handle.fileno())


def _load_state(path: Path) -> dict:
    if not path.exists():
        return {"state": "NEW", "completed": [], "attempts": [], "published": [],
                "checksums": {}, "used_bytes": IMPORTED_USED_BYTES,
                "used_requests": IMPORTED_USED_REQUESTS}
    try: value = json.loads(path.read_text())
    except (OSError, ValueError) as exc: raise ResourceContractError("LEDGER_INVALID") from exc
    _strict(value, {"state", "completed", "attempts", "published", "checksums",
                    "used_bytes", "used_requests"}, "LEDGER_INVALID")
    return value


def _write_state(path: Path, value: dict) -> None:
    temporary = path.with_suffix(".tmp"); temporary.parent.mkdir(parents=True, exist_ok=True)
    data = canonical(value) + b"\n"
    with temporary.open("wb") as handle: handle.write(data); handle.flush(); os.fsync(handle.fileno())
    os.replace(temporary, path)


def _write_immutable_json(path: Path, value: dict) -> None:
    data = canonical(value) + b"\n"; path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data: raise ResourceContractError("IMMUTABLE_RESOURCE_PLAN_CONFLICT")
        return
    with path.open("xb") as handle: handle.write(data); handle.flush(); os.fsync(handle.fileno())


def validate_native_grids(descriptors: list[dict], tolerance: float = 1e-10) -> None:
    if len(descriptors) != 14: raise ResourceContractError("AUXILIARY_DESCRIPTOR_COUNT")
    for region in ("south", "north"):
        rows = [r for r in descriptors if r["region"] == region]
        if len(rows) != 7: raise ResourceContractError("AUXILIARY_DESCRIPTOR_COUNT")
        reference = rows[0]
        for row in rows:
            if row["shape"] != [3600, 3600] or len(row["wcs_vector"]) != len(reference["wcs_vector"]):
                raise ResourceContractError("AUXILIARY_GRID_MISMATCH")
            if any(abs(float(a) - float(b)) > tolerance for a, b in zip(row["wcs_vector"], reference["wcs_vector"])):
                raise ResourceContractError("AUXILIARY_GRID_MISMATCH")
            if row["ndim"] != 2 or row["resampled"] is not False:
                raise ResourceContractError("AUXILIARY_ARRAY_CONTRACT_FAILURE")


def validate_fits_files(paths: list[Path], contract: dict) -> list[dict]:
    """Post-acquisition validation. This is intentionally absent from probe mode."""
    try:
        import numpy as np
        from astropy.io import fits
    except ImportError as exc:
        raise ResourceContractError("FITS_VALIDATOR_DEPENDENCY_MISSING") from exc
    resources = [r for r in contract["resources"] if r["batch"] == "AUXILIARY_FIRST"]
    if len(paths) != len(resources): raise ResourceContractError("AUXILIARY_DESCRIPTOR_COUNT")
    output = []
    for path, row in zip(paths, resources):
        expected_hdu = row["hdu_contract"]["value"].get("physical_image_hdu")
        if not isinstance(expected_hdu, int): raise ResourceContractError("AUXILIARY_HDU_UNRESOLVED")
        try:
            with fits.open(path, mode="readonly", memmap=True, do_not_scale_image_data=True,
                           uint=False, lazy_load_hdus=False) as hdus:
                if expected_hdu >= len(hdus) or hdus[expected_hdu].data is None:
                    raise ResourceContractError("AUXILIARY_HDU_MISMATCH")
                data = hdus[expected_hdu].data; header = hdus[expected_hdu].header
                shape = list(data.shape); ndim = int(data.ndim); dtype = str(data.dtype)
                product = row["product"]["value"]
                if product in ("nexp", "maskbits") and not np.issubdtype(data.dtype, np.integer):
                    raise ResourceContractError("AUXILIARY_DTYPE_MISMATCH")
                if product == "psfsize" and not np.issubdtype(data.dtype, np.floating):
                    raise ResourceContractError("AUXILIARY_DTYPE_MISMATCH")
                ctype1, ctype2 = str(header.get("CTYPE1", "")), str(header.get("CTYPE2", ""))
                if "TAN" not in ctype1 or "TAN" not in ctype2:
                    raise ResourceContractError("AUXILIARY_WCS_MISMATCH")
                from astropy.wcs import WCS
                wcs = WCS(header)
                matrix = wcs.pixel_scale_matrix
                wcs_vector = [float(header[key]) for key in ("CRPIX1", "CRPIX2", "CRVAL1", "CRVAL2")]
                wcs_vector += [float(matrix[0, 0]), float(matrix[0, 1]),
                               float(matrix[1, 0]), float(matrix[1, 1])]
                output.append({"resource_id": row["resource_id"], "region": row["region"]["value"],
                               "product": product, "band": row["band"]["value"], "shape": shape,
                               "ndim": ndim, "dtype": dtype, "wcs_vector": wcs_vector,
                               "bunit": header.get("BUNIT"), "resampled": False})
        except ResourceContractError: raise
        except Exception as exc: raise ResourceContractError("AUXILIARY_FITS_VALIDATION_FAILURE") from exc
    return output


def acquire_auxiliary(contract: dict, authorization: dict, transport, output_root: Path,
                      validator: Callable[[list[Path], dict], list[dict]], *, resume: bool = False) -> dict:
    """Future bulk path. The caller must provide explicit transport and authorization."""
    validate_contract(contract, require_resolved_aux=True); _verify_seal(authorization)
    required = {"schema_version", "stage_id", "contract_sha256", "scope", "resume", "sealed"}
    _strict(authorization, required, "ACQUISITION_AUTHORIZATION_INVALID")
    if (authorization["schema_version"] != "OC3_AUXILIARY_ACQUISITION_AUTHORIZATION_001" or
            authorization["stage_id"] != STAGE_ID or authorization["contract_sha256"] != contract["sealed"] or
            authorization["scope"] != "AUXILIARY_14_ONLY" or authorization["resume"] is not resume):
        raise ResourceContractError("ACQUISITION_AUTHORIZATION_INVALID")
    root = Path(output_root); state_path = root / "AUXILIARY_LEDGER.json"
    state = _load_state(state_path)
    if state["state"] in ("PARTIAL", "FAILED") and not resume:
        raise ResourceContractError("SEPARATE_RESUME_AUTHORIZATION_REQUIRED")
    if state["state"] == "COMPLETE": raise ResourceContractError("ACQUISITION_ALREADY_COMPLETE")
    resources = [r for r in contract["resources"] if r["batch"] == "AUXILIARY_FIRST"]
    if any(r["rights_state"]["value"].get("analysis") is not True or
           r["rights_state"]["value"].get("local_preservation") is not True for r in resources):
        raise ResourceContractError("AUXILIARY_RIGHTS_UNRESOLVED")
    rows = [{"resource_id": r["resource_id"], "region": r["region"]["value"],
             "product": r["product"]["value"], "band": r["band"]["value"],
             "url": r["literal_url"]["value"], "max_bytes": r["max_bytes"]["value"]} for r in resources]
    # HEAD for every pending identity first. No GET occurs before the joint plan passes.
    heads = {}
    if state["state"] == "NEW":
        state["used_requests"] = contract["budget"]["used_requests"]
        state["used_bytes"] = contract["budget"]["used_bytes"]
        _write_state(state_path, state)
    try:
        for row in rows:
            if state["used_requests"] + 1 > GLOBAL_MAX_REQUESTS:
                raise ResourceContractError("INSUFFICIENT_GLOBAL_BUDGET_BEFORE_GET")
            attempt = {"resource_id": row["resource_id"], "method": "HEAD", "state": "STARTED",
                       "reserved_bytes": 0, "status": None}
            state["attempts"].append(attempt); state["used_requests"] += 1; _write_state(state_path, state)
            candidate = {"literal_url": row["url"], "max_bytes": row["max_bytes"]}
            heads[row["resource_id"]] = _head(transport, candidate)
            attempt["state"] = "COMPLETE"; attempt["status"] = 200; _write_state(state_path, state)
        pending = [r for r in rows if r["resource_id"] not in state["published"]]
        reservation = sum(heads[r["resource_id"]]["content_length"] for r in pending)
        peak_resource = max((heads[r["resource_id"]]["content_length"] for r in pending), default=0)
        disk_reservation = 2 * reservation
        io_reservation = 4 * reservation
        if (state["used_bytes"] + reservation + PSF_RESERVATION_BYTES > GLOBAL_MAX_BYTES or
                state["used_requests"] + len(pending) > GLOBAL_MAX_REQUESTS or
                disk_reservation > DISK_INCREMENTAL_MAX_BYTES or io_reservation > IO_MAX_BYTES or
                peak_resource > RAM_MAX_BYTES):
            raise ResourceContractError("INSUFFICIENT_GLOBAL_BUDGET_BEFORE_GET")
        root.mkdir(parents=True, exist_ok=True)
        if shutil.disk_usage(root).free < disk_reservation:
            raise ResourceContractError("INSUFFICIENT_DISK_BEFORE_GET")
        plan = _seal({"schema_version": "OC3_AUXILIARY_RESOURCE_PLAN_001", "stage_id": STAGE_ID,
                      "contract_sha256": contract["sealed"], "pending_resource_ids": [r["resource_id"] for r in pending],
                      "content_lengths": {r["resource_id"]: heads[r["resource_id"]]["content_length"] for r in pending},
                      "projected_body_bytes": reservation, "projected_requests": len(pending),
                      "psf_reservation_bytes": PSF_RESERVATION_BYTES,
                      "disk_reservation_bytes": disk_reservation, "io_reservation_bytes": io_reservation,
                      "peak_ram_bytes": peak_resource, "concurrency": 1})
        _write_immutable_json(root / "AUXILIARY_RESOURCE_PLAN.json", plan)
        state["state"] = "ACTIVE"; _write_state(state_path, state)
        staging = root / "STAGING"; staging.mkdir(parents=True, exist_ok=True)
        for row in pending:
            rid = row["resource_id"]; expected = heads[rid]["content_length"]
            prior_gets = sum(a["method"] == "GET" and a["resource_id"] == rid for a in state["attempts"])
            if prior_gets >= 3: raise ResourceContractError("RETRY_LIMIT")
            attempt = {"resource_id": rid, "method": "GET", "state": "STARTED",
                       "reserved_bytes": expected, "status": None}
            state["attempts"].append(attempt); state["used_requests"] += 1; state["used_bytes"] += expected
            _write_state(state_path, state)
            status, headers, body, final_url = transport.get(row["url"], row["max_bytes"])
            if (status != 200 or final_url != row["url"] or headers.get("content-encoding", "identity") != "identity" or
                    len(body) != expected or len(body) > row["max_bytes"]):
                state["state"] = "PARTIAL"; _write_state(state_path, state)
                raise ResourceContractError("AUXILIARY_GET_FAILURE")
            attempt["state"] = "COMPLETE"; attempt["status"] = status
            path = staging / (rid + ".fits.fz")
            if path.exists() and path.read_bytes() != body: raise ResourceContractError("STAGING_CONFLICT")
            if not path.exists():
                with path.open("xb") as handle: handle.write(body); handle.flush(); os.fsync(handle.fileno())
            state["completed"].append(rid); _write_state(state_path, state)
        published_paths = []
        for row in rows:
            rid = row["resource_id"]; source = staging / (rid + ".fits.fz")
            destination = root / "RAW_IMMUTABLE" / (rid + ".fits.fz")
            if rid in state["published"]:
                if (not destination.is_file() or rid not in state["checksums"] or
                        file_hash(destination) != state["checksums"][rid]):
                    raise ResourceContractError("IMMUTABLE_PUBLICATION_MISSING")
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                if destination.exists(): raise ResourceContractError("IMMUTABLE_PUBLICATION_CONFLICT")
                shutil.copyfile(source, destination)
                os.chmod(destination, 0o444); state["published"].append(rid)
                state["checksums"][rid] = file_hash(destination); _write_state(state_path, state)
            published_paths.append(destination)
        descriptors = validator(published_paths, contract); validate_native_grids(descriptors)
        state["state"] = "COMPLETE"; _write_state(state_path, state)
        terminal = {"stage_id": STAGE_ID, "state": SUCCESS_TERMINAL,
                    "network_requests_total": state["used_requests"],
                    "network_bytes_total": state["used_bytes"], "published_count": 14,
                    "location_selection": False}
        (root / "AUXILIARY_TERMINAL.json").write_bytes(canonical(terminal) + b"\n")
        return terminal
    except Exception:
        if state.get("attempts") and state["attempts"][-1].get("state") == "STARTED":
            state["attempts"][-1]["state"] = "FAILED"
        if state.get("state") != "COMPLETE": state["state"] = "PARTIAL"; _write_state(state_path, state)
        raise


def load_canonical_json(path: Path) -> dict:
    raw = Path(path).read_bytes(); value = json.loads(raw.decode("utf-8"))
    if raw != canonical(value) + b"\n": raise ResourceContractError("NONCANONICAL_JSON")
    return value
