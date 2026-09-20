"""Durable, header-only OC3 DR9 resource-contract probe 002."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
from typing import Callable

from .core import canonical, file_hash
from .resource_contract import (
    AUX_ORDER, BRICKS_SHA256, GLOBAL_MAX_BYTES, GLOBAL_MAX_REQUESTS, HEADER_BLOCK,
    PROPERTY_STATES, ResourceContractError, _padded_data_bytes, _prop, _seal,
    _verify_seal, build_contract, load_frozen_bricks, validate_contract,
)


STAGE_ID = "OC3-RESOURCE-CONTRACT-PROBE-002"
SCHEMA_VERSION = "OC3_DR9_COADD_RESOURCE_PROBE_BINDING_002"
SUCCESS = "RESOURCE_CONTRACT_PROBE_RESOLVED"
PARTIAL = "RESOURCE_CONTRACT_PROBE_PARTIALLY_RESOLVED"
USED_REQUESTS = 64
USED_BODY_BYTES = 89_582_606
REMAINING_REQUESTS = 136
REMAINING_BODY_BYTES = 1_521_030_130
MAX_NEW_REQUESTS = 136
MAX_HEAD_REQUESTS = 14
MAX_RANGE_REQUESTS = 122
MAX_RANGE_BODY_BYTES = 122 * HEADER_BLOCK
MAX_HEADER_BLOCKS_PER_RESOURCE = 16
RETRIES = 0
CONCURRENCY = 1

PARENT_BINDING_RELATIVE = Path("oc3/INPUTS/OC3_RESOURCE_CONTRACT_PROBE_BINDING_001.json")
PARENT_BINDING_SHA256 = "fd8ebd4057ddbc32b4a0f87d65cf61772c637a08b3a7ffbd76dc76f9de80c333"
PROBE001_RELATIVE = Path("oc3/resource_contract/OC3-RESOURCE-CONTRACT-PROBE-001")
PROBE001_TERMINAL_SHA256 = "a91ef41dea95928b5d76e7e9a3eff595753a64686b1d069202406e8400a56741"
PROBE001_LOG_SHA256 = PROBE001_TERMINAL_SHA256
PROBE001_EXPECTED = {
    "error": "FITS_HEADER_BLOCK_CAP", "network_bytes_observed": 120960,
    "network_requests_started": 56, "stage_id": "OC3-RESOURCE-CONTRACT-PROBE-001",
    "state": "RESOURCE_CONTRACT_PROBE_PARTIALLY_RESOLVED",
}

TOP_KEYS = {"schema_version", "stage_id", "development_bricks_sha256", "parent_binding_001",
            "historical_probe_001", "cumulative_budget", "policy", "implementation",
            "resources", "sealed"}
FILE_BINDING_KEYS = {"path", "sha256"}
HISTORICAL_KEYS = {"stage_id", "state", "terminal", "log", "requests", "body_bytes",
                   "retries", "science_pixels_decoded"}
BUDGET_KEYS = {"global_max_requests", "global_max_body_bytes", "used_requests", "used_body_bytes",
               "remaining_requests", "remaining_body_bytes"}
POLICY_KEYS = {"max_new_requests", "max_head_requests", "max_range_requests",
               "max_range_body_bytes", "header_block_bytes", "max_header_blocks_per_resource",
               "retries", "concurrency", "durable_head_checkpoints",
               "durable_resource_checkpoints", "science_pixel_decode", "bulk_get"}
IMPLEMENTATION_KEYS = {"entrypoint_path", "entrypoint_sha256", "module_path", "module_sha256",
                       "amendment_path", "amendment_sha256"}
RESOURCE_KEYS = {"resource_id", "region", "brick", "product", "band", "filename",
                 "directory_component", "literal_url", "max_bytes"}


class Probe002Error(Exception):
    def __init__(self, code: str, resource_id: str | None = None,
                 observed_header_blocks: int | None = None):
        self.code = code; self.resource_id = resource_id
        self.observed_header_blocks = observed_header_blocks
        super().__init__(code)


def _strict(value, keys, code):
    if not isinstance(value, dict) or set(value) != keys: raise Probe002Error(code)


def _read_canonical(path: Path) -> dict:
    try: raw = Path(path).read_bytes(); value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, ValueError) as exc: raise Probe002Error("CANONICAL_INPUT_INVALID") from exc
    if raw != canonical(value) + b"\n": raise Probe002Error("CANONICAL_INPUT_INVALID")
    return value


def verify_probe001_history(project: Path) -> dict:
    project = Path(project).resolve(); root = project / PROBE001_RELATIVE
    terminal = root / "RESOURCE_CONTRACT_PROBE_TERMINAL.json"
    log = root / "RESOURCE_CONTRACT_PROBE_RUN.log"
    parent = project / PARENT_BINDING_RELATIVE
    try:
        if ({p.name for p in root.iterdir() if p.is_file()} != {terminal.name, log.name} or
                any(p.is_dir() or p.is_symlink() for p in root.iterdir()) or
                file_hash(terminal) != PROBE001_TERMINAL_SHA256 or
                file_hash(log) != PROBE001_LOG_SHA256 or
                file_hash(parent) != PARENT_BINDING_SHA256 or
                _read_canonical(terminal) != PROBE001_EXPECTED or
                _read_canonical(log) != PROBE001_EXPECTED):
            raise Probe002Error("PROBE001_HISTORY_MISMATCH")
    except OSError as exc: raise Probe002Error("PROBE001_HISTORY_MISMATCH") from exc
    return {"terminal_sha256": PROBE001_TERMINAL_SHA256, "log_sha256": PROBE001_LOG_SHA256,
            "parent_binding_sha256": PARENT_BINDING_SHA256}


def _expected_budget() -> dict:
    return {"global_max_requests": GLOBAL_MAX_REQUESTS, "global_max_body_bytes": GLOBAL_MAX_BYTES,
            "used_requests": USED_REQUESTS, "used_body_bytes": USED_BODY_BYTES,
            "remaining_requests": REMAINING_REQUESTS, "remaining_body_bytes": REMAINING_BODY_BYTES}


def _expected_policy() -> dict:
    return {"max_new_requests": MAX_NEW_REQUESTS, "max_head_requests": MAX_HEAD_REQUESTS,
            "max_range_requests": MAX_RANGE_REQUESTS, "max_range_body_bytes": MAX_RANGE_BODY_BYTES,
            "header_block_bytes": HEADER_BLOCK,
            "max_header_blocks_per_resource": MAX_HEADER_BLOCKS_PER_RESOURCE,
            "retries": RETRIES, "concurrency": CONCURRENCY,
            "durable_head_checkpoints": True, "durable_resource_checkpoints": True,
            "science_pixel_decode": False, "bulk_get": False}


def load_binding002(path: Path, project: Path) -> dict:
    value = _read_canonical(path); _strict(value, TOP_KEYS, "BINDING002_SCHEMA_INVALID")
    try: _verify_seal(value)
    except ResourceContractError as exc: raise Probe002Error("BINDING002_SEAL_INVALID") from exc
    if value["schema_version"] != SCHEMA_VERSION or value["stage_id"] != STAGE_ID or value["development_bricks_sha256"] != BRICKS_SHA256:
        raise Probe002Error("BINDING002_IDENTITY_INVALID")
    _strict(value["parent_binding_001"], FILE_BINDING_KEYS, "BINDING002_SCHEMA_INVALID")
    _strict(value["historical_probe_001"], HISTORICAL_KEYS, "BINDING002_SCHEMA_INVALID")
    _strict(value["historical_probe_001"]["terminal"], FILE_BINDING_KEYS, "BINDING002_SCHEMA_INVALID")
    _strict(value["historical_probe_001"]["log"], FILE_BINDING_KEYS, "BINDING002_SCHEMA_INVALID")
    _strict(value["cumulative_budget"], BUDGET_KEYS, "BINDING002_SCHEMA_INVALID")
    _strict(value["policy"], POLICY_KEYS, "BINDING002_SCHEMA_INVALID")
    _strict(value["implementation"], IMPLEMENTATION_KEYS, "BINDING002_SCHEMA_INVALID")
    if value["cumulative_budget"] != _expected_budget(): raise Probe002Error("COUNTER_RESET_OR_MISMATCH")
    if value["policy"] != _expected_policy(): raise Probe002Error("PROBE002_POLICY_MISMATCH")
    historical = value["historical_probe_001"]
    if historical != {
        "stage_id": "OC3-RESOURCE-CONTRACT-PROBE-001", "state": PARTIAL,
        "terminal": {"path": str(PROBE001_RELATIVE / "RESOURCE_CONTRACT_PROBE_TERMINAL.json"),
                     "sha256": PROBE001_TERMINAL_SHA256},
        "log": {"path": str(PROBE001_RELATIVE / "RESOURCE_CONTRACT_PROBE_RUN.log"),
                "sha256": PROBE001_LOG_SHA256},
        "requests": 56, "body_bytes": 120960, "retries": 0, "science_pixels_decoded": 0,
    }: raise Probe002Error("PROBE001_BINDING_MISMATCH")
    if value["parent_binding_001"] != {"path": str(PARENT_BINDING_RELATIVE), "sha256": PARENT_BINDING_SHA256}:
        raise Probe002Error("PARENT_BINDING_MISMATCH")
    project = Path(project).resolve(); verify_probe001_history(project)
    parent = _read_canonical(project / PARENT_BINDING_RELATIVE)
    rows = value["resources"]
    if not isinstance(rows, list) or len(rows) != 14 or rows != parent.get("resources"):
        raise Probe002Error("RESOURCE_SET_CHANGED")
    for row, identity in zip(rows, AUX_ORDER):
        _strict(row, RESOURCE_KEYS, "BINDING002_RESOURCE_SCHEMA_INVALID")
        if (row["region"], row["product"], row["band"]) != identity:
            raise Probe002Error("RESOURCE_ORDER_CHANGED")
    implementation = value["implementation"]
    for key in ("entrypoint", "module", "amendment"):
        rel = implementation[key + "_path"]; expected = implementation[key + "_sha256"]
        candidate = project / rel
        if not candidate.is_file() or candidate.is_symlink() or file_hash(candidate) != expected:
            raise Probe002Error("IMPLEMENTATION_BINDING_MISMATCH")
    return value


def _atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); temp = path.with_suffix(path.suffix + ".tmp")
    data = canonical(value) + b"\n"
    with temp.open("wb") as handle: handle.write(data); handle.flush(); os.fsync(handle.fileno())
    os.replace(temp, path)


def _immutable_json(path: Path, value: dict) -> str:
    data = canonical(value) + b"\n"; path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data: raise Probe002Error("IMMUTABLE_EVIDENCE_CONFLICT")
    else:
        with path.open("xb") as handle: handle.write(data); handle.flush(); os.fsync(handle.fileno())
    return hashlib.sha256(data).hexdigest()


class EvidenceStore:
    def __init__(self, root: Path, binding: dict):
        self.root = Path(root)
        if self.root.exists(): raise Probe002Error("PROBE002_ATTEMPT_ALREADY_EXISTS")
        self.root.mkdir(parents=True)
        self.sequence = 0
        self.aggregate = {
            "schema_version": "OC3_RESOURCE_CONTRACT_PROBE_002_AGGREGATE_001",
            "stage_id": STAGE_ID, "binding_seal": binding["sealed"], "state": "ACTIVE",
            "counters": {**_expected_budget(), "local_requests": 0, "local_head_requests": 0,
                         "local_range_requests": 0, "local_range_body_bytes": 0,
                         "local_range_body_bytes_observed": 0,
                         "cumulative_requests": USED_REQUESTS,
                         "cumulative_body_bytes": USED_BODY_BYTES,
                         "science_pixels_decoded": 0, "bulk_get_requests": 0},
            "resources": [{"resource_id": row["resource_id"], "region": row["region"],
                           "product": row["product"], "band": row["band"], "state": "NOT_STARTED",
                           "head_checkpoint": None, "resource_checkpoint": None, "failure": None}
                          for row in binding["resources"]],
            "last_event": "INITIALIZED", "terminal": None,
        }
        _immutable_json(self.root / "PROBE_002_BINDING_COPY.json", binding)
        self._snapshot("INITIALIZED")

    def row(self, resource_id: str) -> dict:
        return next(row for row in self.aggregate["resources"] if row["resource_id"] == resource_id)

    def _snapshot(self, event: str) -> None:
        self.sequence += 1; self.aggregate["last_event"] = event
        value = _seal(self.aggregate)
        history = self.root / "AGGREGATE_HISTORY" / f"{self.sequence:04d}.json"
        _immutable_json(history, value)
        _atomic_json(self.root / "PROBE_002_AGGREGATE.json", value)

    def reserve_request(self, kind: str, resource_id: str) -> None:
        counters = self.aggregate["counters"]
        if kind not in ("HEAD", "RANGE"): raise Probe002Error("REQUEST_KIND_INVALID", resource_id)
        if counters["local_requests"] + 1 > MAX_NEW_REQUESTS:
            raise Probe002Error("PROBE002_LOCAL_REQUEST_LIMIT", resource_id)
        if counters["cumulative_requests"] + 1 > GLOBAL_MAX_REQUESTS:
            raise Probe002Error("PROBE002_GLOBAL_REQUEST_LIMIT", resource_id)
        if kind == "HEAD" and counters["local_head_requests"] + 1 > MAX_HEAD_REQUESTS:
            raise Probe002Error("PROBE002_HEAD_REQUEST_LIMIT", resource_id)
        if kind == "RANGE":
            if counters["local_range_requests"] + 1 > MAX_RANGE_REQUESTS:
                raise Probe002Error("PROBE002_RANGE_REQUEST_LIMIT", resource_id)
            if counters["local_range_body_bytes"] + HEADER_BLOCK > MAX_RANGE_BODY_BYTES:
                raise Probe002Error("PROBE002_RANGE_BYTE_LIMIT", resource_id)
            if counters["cumulative_body_bytes"] + HEADER_BLOCK > GLOBAL_MAX_BYTES:
                raise Probe002Error("PROBE002_GLOBAL_BYTE_LIMIT", resource_id)
            counters["local_range_requests"] += 1
            # Reserve and retain the complete block before transport. A crash or
            # short error response never resets cumulative accounting.
            counters["local_range_body_bytes"] += HEADER_BLOCK
            counters["cumulative_body_bytes"] += HEADER_BLOCK
        else: counters["local_head_requests"] += 1
        counters["local_requests"] += 1; counters["cumulative_requests"] += 1
        self._snapshot(f"{kind}_REQUEST_RESERVED:{resource_id}")

    def record_range_body(self, resource_id: str, size: int) -> None:
        if not 0 <= size <= HEADER_BLOCK: raise Probe002Error("RANGE_BODY_ACCOUNTING_INVALID", resource_id)
        counters = self.aggregate["counters"]
        counters["local_range_body_bytes_observed"] += size
        self._snapshot(f"RANGE_BODY_ACCOUNTED:{resource_id}")

    def publish_head(self, resource: dict, evidence: dict) -> dict:
        value = _seal({"schema_version": "OC3_PROBE_002_HEAD_CHECKPOINT_001", "stage_id": STAGE_ID,
                       "resource_id": resource["resource_id"], **evidence})
        relative = Path("HEAD_EVIDENCE") / f"{resource['resource_id']}.json"
        sha = _immutable_json(self.root / relative, value)
        row = self.row(resource["resource_id"]); row["state"] = "HEAD_VALIDATED"
        row["head_checkpoint"] = {"path": str(relative), "sha256": sha, "seal": value["sealed"]}
        self._snapshot(f"HEAD_VALIDATED:{resource['resource_id']}")
        return value

    def publish_resource(self, resource: dict, checkpoint: dict) -> dict:
        value = _seal({"schema_version": "OC3_PROBE_002_RESOURCE_CHECKPOINT_001",
                       "stage_id": STAGE_ID, "resource_id": resource["resource_id"], **checkpoint})
        relative = Path("RESOURCE_CHECKPOINTS") / f"{resource['resource_id']}.json"
        sha = _immutable_json(self.root / relative, value)
        row = self.row(resource["resource_id"]); row["state"] = "HEADER_RESOLVED"
        row["resource_checkpoint"] = {"path": str(relative), "sha256": sha, "seal": value["sealed"]}
        self._snapshot(f"HEADER_RESOLVED:{resource['resource_id']}")
        return value

    def fail(self, error: Probe002Error) -> dict:
        if error.resource_id:
            row = self.row(error.resource_id); row["state"] = "FAILED"
            row["failure"] = {"code": error.code, "observed_header_blocks": error.observed_header_blocks}
        self.aggregate["state"] = PARTIAL
        terminal = {"stage_id": STAGE_ID, "state": PARTIAL, "error": error.code,
                    "resource_id": error.resource_id,
                    "observed_header_blocks": error.observed_header_blocks,
                    "network_requests_started": self.aggregate["counters"]["local_requests"],
                    "network_bytes_observed": self.aggregate["counters"]["local_range_body_bytes_observed"],
                    "network_bytes_charged": self.aggregate["counters"]["local_range_body_bytes"],
                    "cumulative_requests": self.aggregate["counters"]["cumulative_requests"],
                    "cumulative_body_bytes": self.aggregate["counters"]["cumulative_body_bytes"],
                    "science_pixels_decoded": 0, "bulk_get_requests": 0}
        self.aggregate["terminal"] = terminal; self._snapshot("TERMINAL_PARTIAL")
        _immutable_json(self.root / "PROBE_002_TERMINAL.json", terminal)
        return terminal

    def succeed(self, resolved_contract_sha256: str) -> dict:
        self.aggregate["state"] = SUCCESS
        terminal = {"stage_id": STAGE_ID, "state": SUCCESS,
                    "network_requests_started": self.aggregate["counters"]["local_requests"],
                    "network_bytes_observed": self.aggregate["counters"]["local_range_body_bytes_observed"],
                    "network_bytes_charged": self.aggregate["counters"]["local_range_body_bytes"],
                    "cumulative_requests": self.aggregate["counters"]["cumulative_requests"],
                    "cumulative_body_bytes": self.aggregate["counters"]["cumulative_body_bytes"],
                    "resources_resolved": 14, "resolved_contract_sha256": resolved_contract_sha256,
                    "science_pixels_decoded": 0, "bulk_get_requests": 0}
        self.aggregate["terminal"] = terminal; self._snapshot("TERMINAL_RESOLVED")
        _immutable_json(self.root / "PROBE_002_TERMINAL.json", terminal)
        return terminal


TECHNICAL_KEYS = (
    "SIMPLE", "XTENSION", "BITPIX", "NAXIS", "NAXIS1", "NAXIS2", "PCOUNT", "GCOUNT",
    "ZIMAGE", "ZBITPIX", "ZNAXIS", "ZNAXIS1", "ZNAXIS2", "ZCMPTYPE", "BUNIT",
    "CTYPE1", "CTYPE2", "CRPIX1", "CRPIX2", "CRVAL1", "CRVAL2",
    "CD1_1", "CD1_2", "CD2_1", "CD2_2", "CDELT1", "CDELT2",
    "PC1_1", "PC1_2", "PC2_1", "PC2_2",
)


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


def _parse_hdu(read_block: Callable[[int, int], bytes], start: int, resource_id: str,
               counter: list[int], requested: list[list[int]]) -> tuple[dict, int]:
    cards = {}; offset = start
    while counter[0] < MAX_HEADER_BLOCKS_PER_RESOURCE:
        body = read_block(offset, offset + HEADER_BLOCK - 1)
        counter[0] += 1; requested.append([offset, offset + HEADER_BLOCK - 1])
        if len(body) != HEADER_BLOCK: raise Probe002Error("FITS_HEADER_RANGE_SHORT", resource_id, counter[0])
        for index in range(0, HEADER_BLOCK, 80):
            card = body[index:index + 80]
            key = card[:8].decode("ascii", errors="strict").strip()
            if key == "END": return cards, offset + HEADER_BLOCK
            if key and key not in cards: cards[key] = _card_value(card)
        offset += HEADER_BLOCK
    raise Probe002Error("FITS_HEADER_BLOCK_CAP", resource_id, counter[0])


def _dtype(bitpix: int) -> str:
    values = {8: "uint8", 16: "int16", 32: "int32", 64: "int64", -32: "float32", -64: "float64"}
    if bitpix not in values: raise Probe002Error("FITS_BITPIX_UNSUPPORTED")
    return values[bitpix]


def inspect_header002(resource: dict, read_block: Callable[[int, int], bytes]) -> dict:
    rid = resource["resource_id"]; count = [0]; requested: list[list[int]] = []
    primary, primary_end = _parse_hdu(read_block, 0, rid, count, requested)
    primary_data = _padded_data_bytes(primary)
    physical = [{"physical_hdu": 0, "header": {k: primary.get(k) for k in TECHNICAL_KEYS if k in primary},
                 "header_end_offset": primary_end, "data_bytes_skipped": primary_data}]
    primary_image = int(primary.get("NAXIS", 0) or 0) == 2
    if primary_image:
        image = primary; physical_hdu = 0; image_header_end = primary_end
    else:
        extension_start = primary_end + primary_data
        extension, extension_end = _parse_hdu(read_block, extension_start, rid, count, requested)
        physical.append({"physical_hdu": 1,
                         "header": {k: extension.get(k) for k in TECHNICAL_KEYS if k in extension},
                         "header_end_offset": extension_end,
                         "data_bytes_skipped": _padded_data_bytes(extension)})
        image = extension; physical_hdu = 1; image_header_end = extension_end
    compressed = image.get("ZIMAGE") is True
    if compressed:
        shape = [int(image.get("ZNAXIS2", 0)), int(image.get("ZNAXIS1", 0))]
        bitpix = int(image.get("ZBITPIX", 0))
    else:
        shape = [int(image.get("NAXIS2", 0)), int(image.get("NAXIS1", 0))]
        bitpix = int(image.get("BITPIX", 0))
    if shape != [3600, 3600]: raise Probe002Error("FITS_NOMINAL_SHAPE_MISMATCH", rid, count[0])
    ctype = [str(image.get("CTYPE1", "")), str(image.get("CTYPE2", ""))]
    if not all("TAN" in item for item in ctype): raise Probe002Error("FITS_WCS_NOT_TAN", rid, count[0])
    # Every requested interval is a header interval. The next byte after the
    # last image-header block is the first possible image-data byte.
    if requested[-1][1] >= image_header_end: raise Probe002Error("DATA_BLOCK_REQUESTED", rid, count[0])
    mapping = "logical role mapped through FITS tiled-image compression" if compressed else "uncompressed physical image HDU"
    logical_hdu = 1 if resource["product"] == "maskbits" else physical_hdu
    return {"header_blocks": count[0], "requested_header_ranges": requested,
            "physical_fits_hdus": physical, "physical_image_hdu": physical_hdu,
            "logical_image_hdu": logical_hdu, "compressed_image": compressed,
            "compression_mapping": mapping, "shape": shape, "bitpix": bitpix,
            "dtype": _dtype(bitpix), "observed_bunit": image.get("BUNIT"),
            "wcs": {k: image.get(k) for k in TECHNICAL_KEYS if k.startswith(("CTYPE", "CRPIX", "CRVAL", "CD", "CDELT", "PC")) and k in image},
            "first_data_offset": image_header_end,
            "resolved_contract_fields": ["literal_url", "directory_component", "max_bytes",
                                         "logical_hdu", "physical_hdu", "compression_mapping",
                                         "shape", "dtype", "wcs"],
            "unresolved_contract_fields": [], "science_pixels_decoded": 0}


def _resolved_contract(binding: dict, store: EvidenceStore, heads: dict, checkpoints: dict) -> dict:
    bricks = {row["region"]: row["brick"] for row in binding["resources"]}
    counters = store.aggregate["counters"]
    result = build_contract(bricks, used_bytes=counters["cumulative_body_bytes"],
                            used_requests=counters["cumulative_requests"])
    index = {row["resource_id"]: row for row in result["resources"]}
    refs = {row["resource_id"]: row for row in store.aggregate["resources"]}
    for candidate in binding["resources"]:
        rid = candidate["resource_id"]; row = index[rid]; head = heads[rid]; checkpoint = checkpoints[rid]
        evidence = f"{STAGE_ID}:{refs[rid]['resource_checkpoint']['sha256']}"
        row["literal_url"] = _prop("OBSERVED_BY_BOUNDED_PROBE", candidate["literal_url"], evidence)
        row["directory_component"] = _prop("OBSERVED_BY_BOUNDED_PROBE", candidate["directory_component"], evidence)
        row["max_bytes"] = _prop("OBSERVED_BY_BOUNDED_PROBE", head["content_length"], evidence)
        old = row["hdu_contract"]["value"] or {}
        row["hdu_contract"] = _prop("OBSERVED_BY_BOUNDED_PROBE", {
            **old, "logical_hdu": checkpoint["logical_image_hdu"],
            "logical_role": old.get("logical_role", row["expected_logical_role"]["value"]),
            "physical_image_hdu": checkpoint["physical_image_hdu"],
            "compression_mapping": checkpoint["compression_mapping"]}, evidence)
        units = row["units_dtype_contract"]["value"] or {}
        row["units_dtype_contract"] = _prop("OBSERVED_BY_BOUNDED_PROBE", {
            **units, "dtype": checkpoint["dtype"], "observed_bunit": checkpoint["observed_bunit"]}, evidence)
        representation = row["representation_constraints"]["value"]
        row["representation_constraints"] = _prop("OBSERVED_BY_BOUNDED_PROBE", {
            **representation, "logical_physical_hdu_mapping": checkpoint["compression_mapping"],
            "content_length": head["content_length"], "etag": head["etag"]}, evidence)
    result = _seal(result); validate_contract(result, require_resolved_aux=True)
    return result


def run_probe002(binding: dict, transport, audit_root: Path) -> tuple[dict, bool]:
    store = EvidenceStore(audit_root, binding); heads = {}; checkpoints = {}; current = None
    try:
        for resource in binding["resources"]:
            current = resource["resource_id"]; store.reserve_request("HEAD", current)
            status, headers, body, final_url = transport.head(resource["literal_url"])
            if body or status != 200 or final_url != resource["literal_url"] or headers.get("content-encoding", "identity") != "identity":
                raise Probe002Error("HEAD_IDENTITY_FAILURE", current)
            try: length = int(headers["content-length"])
            except (KeyError, ValueError) as exc: raise Probe002Error("HEAD_LENGTH_UNRESOLVED", current) from exc
            if length <= 0 or length > resource["max_bytes"]: raise Probe002Error("HEAD_LENGTH_OUT_OF_BOUND", current)
            evidence = {"literal_url": resource["literal_url"], "status": status,
                        "content_length": length, "etag": headers.get("etag"),
                        "last_modified": headers.get("last-modified"),
                        "content_encoding": headers.get("content-encoding", "identity"),
                        "representation_identity": True,
                        "accounting": {"local_requests": store.aggregate["counters"]["local_requests"],
                                       "cumulative_requests": store.aggregate["counters"]["cumulative_requests"],
                                       "cumulative_body_bytes": store.aggregate["counters"]["cumulative_body_bytes"]}}
            heads[current] = store.publish_head(resource, evidence)
        for resource in binding["resources"]:
            current = resource["resource_id"]; length = heads[current]["content_length"]
            def read_block(start: int, end: int, resource=resource, length=length):
                store.reserve_request("RANGE", resource["resource_id"])
                status, headers, body, final_url = transport.range(resource["literal_url"], start, end)
                store.record_range_body(resource["resource_id"], len(body))
                expected = f"bytes {start}-{end}/{length}"
                if status != 206: raise Probe002Error("RANGE_STATUS_NOT_206", resource["resource_id"])
                if headers.get("content-range") != expected: raise Probe002Error("RANGE_CONTENT_RANGE_MISMATCH", resource["resource_id"])
                if final_url != resource["literal_url"] or headers.get("content-encoding", "identity") != "identity":
                    raise Probe002Error("RANGE_IDENTITY_FAILURE", resource["resource_id"])
                if len(body) != end - start + 1: raise Probe002Error("FITS_HEADER_RANGE_SHORT", resource["resource_id"])
                return body
            structure = inspect_header002(resource, read_block)
            head_ref = store.row(current)["head_checkpoint"]
            checkpoint = {"head_checkpoint": head_ref, **structure}
            checkpoints[current] = store.publish_resource(resource, checkpoint)
        resolved = _resolved_contract(binding, store, heads, checkpoints)
        contract_path = store.root / "RESOURCE_CONTRACT_RESOLVED.json"
        contract_sha = _immutable_json(contract_path, resolved)
        terminal = store.succeed(contract_sha); return terminal, True
    except Probe002Error as error:
        if error.resource_id is None: error.resource_id = current
        return store.fail(error), False
    except ResourceContractError as error:
        return store.fail(Probe002Error(str(error), current)), False
    except (OSError, TimeoutError, UnicodeError, ValueError) as exc:
        return store.fail(Probe002Error("PROBE002_IO_OR_TRANSPORT_FAILURE", current)), False


def dry_run(binding: dict, project: Path) -> dict:
    project = Path(project).resolve()
    audit = project / "oc3/resource_contract/OC3-RESOURCE-CONTRACT-PROBE-002"
    command = (
        f"{project}/oc3/.venv/bin/python {project}/oc3/oc3_resource_contract_probe002.py "
        f"--execute-probe-002 --execute-network --project {project} "
        f"--binding {project}/oc3/INPUTS/OC3_RESOURCE_CONTRACT_PROBE_BINDING_002.json "
        f"--audit-directory {audit} --log {audit}/PROBE_002_RUN.log "
        f"--max-new-requests 136 --max-range-requests 122 --max-range-bytes 351360 "
        f"--max-header-blocks 16"
    )
    return {"stage_id": STAGE_ID, "state": "PROBE_002_DRY_RUN", "resources": len(binding["resources"]),
            "used_global_requests": USED_REQUESTS, "used_global_body_bytes": USED_BODY_BYTES,
            "remaining_global_requests": REMAINING_REQUESTS,
            "remaining_global_body_bytes": REMAINING_BODY_BYTES,
            "max_new_head_requests": MAX_HEAD_REQUESTS, "max_new_range_requests": MAX_RANGE_REQUESTS,
            "max_new_range_body_bytes": MAX_RANGE_BODY_BYTES,
            "max_header_blocks_per_resource": MAX_HEADER_BLOCKS_PER_RESOURCE,
            "retries": RETRIES, "concurrency": CONCURRENCY, "bulk_get_requests": 0,
            "science_pixels_decoded": 0, "network_requests": 0,
            "checkpoint_paths": {"heads": str(audit / "HEAD_EVIDENCE/<resource_id>.json"),
                                 "resources": str(audit / "RESOURCE_CHECKPOINTS/<resource_id>.json"),
                                 "aggregate": str(audit / "PROBE_002_AGGREGATE.json"),
                                 "history": str(audit / "AGGREGATE_HISTORY/<sequence>.json")},
            "future_command": command}
