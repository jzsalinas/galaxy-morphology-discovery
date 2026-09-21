"""Frozen image/invvar and coadd-PSF contracts for the OC-3 six locations.

The only network-capable operation in this module is the separately invoked,
literal-URL FITS-header probe.  Contract construction is offline and the probe
parser never imports an array decoder or observes FITS data sections.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import re
from typing import Callable
from urllib.parse import urlsplit

from astropy.io import fits
from astropy.wcs import WCS

from .core import canonical, file_hash, implementation_hash


STAGE_ID = "OC3-FIXED-NATIVE-RESOURCE-PROBE-001"
SUCCESS = "FIXED_NATIVE_RESOURCE_CONTRACT_RESOLVED"
PARTIAL = "FIXED_NATIVE_RESOURCE_CONTRACT_PARTIALLY_RESOLVED"
LOCATIONS_RELATIVE = Path("oc3/TECHNICAL_INDEX/OC3_LOCATIONS.json")
LOCATIONS_FILE_SHA256 = "33d593638c074a3ff59d32d3e4c38558e8912377ea15818ca5072087007c97d1"
SELECTION_SHA256 = "2e6f2cb070a363e9e3dbdb1f25670590c33500a293bb926d8ff94657a2ff8860"
LOCATION_TERMINAL_RELATIVE = Path(
    "oc3/location_selection/OC3-OFFLINE-LOCATION-SELECTION-001/LOCATION_SELECTION_TERMINAL.json")
AUX_CONTRACT_RELATIVE = Path(
    "oc3/resource_contract/OC3-RESOURCE-CONTRACT-PROBE-002/RESOURCE_CONTRACT_RESOLVED.json")
AUX_CONTRACT_SHA256 = "5afff8fddbcb8a9e86ea3f55cf89288840a21ca705bca121ed1b9204c349616d"
AUX_RAW_RELATIVE = Path(
    "oc3/auxiliary_acquisition/OC3-RESOURCE-CONTRACT-AUXILIARY-ACQUISITION-001/RAW_IMMUTABLE")
CONTRACT_RELATIVE = Path("oc3/INPUTS/OC3_FIXED_NATIVE_RESOURCE_CONTRACT_001.json")
PSF_CONTRACT_RELATIVE = Path("oc3/INPUTS/OC3_PSF_RESOURCE_CONTRACT_001.json")
BINDING_RELATIVE = Path("oc3/INPUTS/OC3_FIXED_NATIVE_RESOURCE_PROBE_BINDING_001.json")
AUDIT_RELATIVE = Path("oc3/fixed_native_resource_contract/OC3-FIXED-NATIVE-RESOURCE-PROBE-001")

START_REQUESTS = 194
START_BODY_BYTES = 93_663_566
GLOBAL_BODY_CAP = 1_610_612_736
PSF_RESERVATION_BYTES = 54 * 2**20
HEADER_BLOCK = 2880
RESOURCE_COUNT = 12
MAX_HEAD_REQUESTS = RESOURCE_COUNT
MAX_HEADER_BLOCKS_PER_RESOURCE = 16
MAX_RANGE_REQUESTS = RESOURCE_COUNT * MAX_HEADER_BLOCKS_PER_RESOURCE
MAX_NEW_REQUESTS = MAX_HEAD_REQUESTS + MAX_RANGE_REQUESTS
MAX_RANGE_BODY_BYTES = MAX_RANGE_REQUESTS * HEADER_BLOCK
MAX_RESOURCE_BYTES = GLOBAL_BODY_CAP - START_BODY_BYTES - PSF_RESERVATION_BYTES
RETRIES = 0
CONCURRENCY = 1
ALLOWED_HOST = "portal.nersc.gov"
BASE_URL = "https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9"
BANDS = ("g", "r", "z")
SLOTS = ("S1", "S2", "S3", "N1", "N2", "N3")
RESOURCE_ORDER = tuple((region, product, band)
                       for region in ("south", "north")
                       for product in ("image", "invvar") for band in BANDS)
PSF_POINTS = (("P0", 0, 0), ("P1", -32, -32), ("P2", 32, 32))
PROPERTY_STATES = frozenset(("DOCUMENTED", "OBSERVED_BY_BOUNDED_PROBE", "UNRESOLVED"))
SOURCE_STATES = frozenset(("DOCUMENTED", "SOURCE_VERIFIED", "UNRESOLVED"))


class FixedNativeContractError(Exception):
    def __init__(self, code: str, resource_id: str | None = None,
                 observed_header_blocks: int | None = None):
        self.code = code
        self.resource_id = resource_id
        self.observed_header_blocks = observed_header_blocks
        super().__init__(code)


def _seal(value: dict) -> dict:
    body = dict(value)
    body.pop("sealed", None)
    body["sealed"] = hashlib.sha256(canonical(body)).hexdigest()
    return body


def _verify_seal(value: dict) -> None:
    if not isinstance(value, dict) or not isinstance(value.get("sealed"), str):
        raise FixedNativeContractError("SEAL_INVALID")
    body = dict(value)
    seal = body.pop("sealed")
    if hashlib.sha256(canonical(body)).hexdigest() != seal:
        raise FixedNativeContractError("SEAL_INVALID")


def _canonical_load(path: Path) -> dict:
    try:
        raw = Path(path).read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise FixedNativeContractError("CANONICAL_INPUT_INVALID") from exc
    if not isinstance(value, dict) or raw != canonical(value) + b"\n":
        raise FixedNativeContractError("CANONICAL_INPUT_INVALID")
    return value


def _strict(value: dict, keys: set[str], code: str) -> None:
    if not isinstance(value, dict) or set(value) != keys:
        raise FixedNativeContractError(code)


def _prop(state: str, value, evidence: list[str]) -> dict:
    if state not in PROPERTY_STATES or not isinstance(evidence, list) or not evidence:
        raise FixedNativeContractError("PROPERTY_STATE_INVALID")
    return {"state": state, "value": value, "evidence": evidence}


def _rid(region: str, brick: str, product: str, band: str) -> str:
    text = f"OC3|DR9|{region}|{brick}|{product}|{band}"
    return "oc3_" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]


def _psf_id(slot: str, point: str, band: str) -> str:
    return "oc3psf_" + hashlib.sha256(
        f"OC3|DR9|{slot}|{point}|{band}".encode("utf-8")).hexdigest()[:24]


def _transport_id(slot: str, point: str) -> str:
    return "oc3psft_" + hashlib.sha256(
        f"OC3|DR9|{slot}|{point}|grz".encode("utf-8")).hexdigest()[:24]


def verify_locations(project: Path) -> dict:
    project = Path(project).resolve()
    locations_path = project / LOCATIONS_RELATIVE
    terminal_path = project / LOCATION_TERMINAL_RELATIVE
    if file_hash(locations_path) != LOCATIONS_FILE_SHA256:
        raise FixedNativeContractError("FROZEN_LOCATIONS_FILE_MISMATCH")
    locations = _canonical_load(locations_path)
    terminal = _canonical_load(terminal_path)
    if (locations.get("selection_sha256") != SELECTION_SHA256 or
            terminal.get("state") != "LOCATION_SELECTION_VALIDATED" or
            terminal.get("selection_sha256") != SELECTION_SHA256 or
            terminal.get("selected_count") != 6 or
            [row.get("slot") for row in locations.get("locations", [])] != list(SLOTS)):
        raise FixedNativeContractError("FROZEN_LOCATIONS_BINDING_FAILURE")
    return locations


def _directory_evidence(project: Path) -> tuple[dict[str, dict], dict]:
    path = Path(project).resolve() / AUX_CONTRACT_RELATIVE
    if file_hash(path) != AUX_CONTRACT_SHA256:
        raise FixedNativeContractError("AUXILIARY_CONTRACT_MISMATCH")
    contract = _canonical_load(path)
    rows = {}
    for resource in contract.get("resources", []):
        if resource.get("product", {}).get("value") != "nexp" or resource.get("band", {}).get("value") != "g":
            continue
        region = resource["region"]["value"]
        rows[region] = {"brick": resource["brick"]["value"],
                        "directory_component": resource["directory_component"]["value"],
                        "evidence": resource["directory_component"]["evidence"]}
    if set(rows) != {"south", "north"}:
        raise FixedNativeContractError("DIRECTORY_EVIDENCE_MISSING")
    return rows, contract


RESOURCE_PROPERTY_KEYS = {
    "region", "brick", "product", "band", "literal_url", "filename",
    "directory_component", "expected_logical_role", "documented_units",
    "expected_shape", "wcs", "representation", "content_length", "etag",
    "logical_hdu", "physical_image_hdu", "compression_mapping", "dtype", "max_bytes",
}
RESOURCE_KEYS = {"resource_id", "fields", "evidence_state"}
CONTRACT_KEYS = {"schema_version", "stage_id", "locations_binding", "directory_evidence",
                 "documentary_authorities", "resources", "sealed"}


def build_fixed_native_contract(project: Path) -> dict:
    project = Path(project).resolve()
    verify_locations(project)
    directories, _ = _directory_evidence(project)
    files_doc = "https://www.legacysurvey.org/dr9/files/#image-stacks-region-coadd"
    resources = []
    for region, product, band in RESOURCE_ORDER:
        brick = directories[region]["brick"]
        component = directories[region]["directory_component"]
        filename = f"legacysurvey-{brick}-{product}-{band}.fits.fz"
        url = f"{BASE_URL}/{region}/coadd/{component}/{brick}/{filename}"
        role = "inverse_variance_weighted_coadded_science_image" if product == "image" else "corresponding_coadd_inverse_variance"
        units = "nanomaggies_per_pixel" if product == "image" else "1/(nanomaggies)^2_per_pixel"
        fields = {
            "region": _prop("DOCUMENTED", region, ["frozen-location-region"]),
            "brick": _prop("OBSERVED_BY_BOUNDED_PROBE", brick, directories[region]["evidence"]),
            "product": _prop("DOCUMENTED", product, [files_doc]),
            "band": _prop("DOCUMENTED", band, [files_doc]),
            "literal_url": _prop("DOCUMENTED", url, [files_doc, f"directory:{AUX_CONTRACT_SHA256}"]),
            "filename": _prop("DOCUMENTED", filename, [files_doc]),
            "directory_component": _prop("OBSERVED_BY_BOUNDED_PROBE", component, directories[region]["evidence"]),
            "expected_logical_role": _prop("DOCUMENTED", role, [files_doc]),
            "documented_units": _prop("DOCUMENTED", units, [files_doc]),
            "expected_shape": _prop("DOCUMENTED", [3600, 3600], [files_doc, "OC3_BOUNDED_AUXILIARY_PIXEL_PILOT_SPEC.md"]),
            "wcs": _prop("DOCUMENTED", {"projection": "TAN", "nominal_pixel_scale_arcsec": 0.262}, [files_doc]),
            "representation": _prop("DOCUMENTED", {"filename_suffix": ".fits.fz", "content_encoding": "identity", "native_grid_only": True}, [files_doc]),
            "content_length": _prop("UNRESOLVED", None, ["OBSERVED_BY_BOUNDED_PROBE_REQUIRED"]),
            "etag": _prop("UNRESOLVED", None, ["OBSERVED_BY_BOUNDED_PROBE_REQUIRED"]),
            "logical_hdu": (_prop("DOCUMENTED", "PRIMARY", [files_doc]) if product == "image"
                            else _prop("UNRESOLVED", None, ["OBSERVED_BY_BOUNDED_PROBE_REQUIRED"])),
            "physical_image_hdu": _prop("UNRESOLVED", None, ["OBSERVED_BY_BOUNDED_PROBE_REQUIRED"]),
            "compression_mapping": _prop("UNRESOLVED", None, ["OBSERVED_BY_BOUNDED_PROBE_REQUIRED"]),
            "dtype": _prop("UNRESOLVED", None, ["OBSERVED_BY_BOUNDED_PROBE_REQUIRED"]),
            "max_bytes": _prop("DOCUMENTED", MAX_RESOURCE_BYTES, ["prospective-stage-local-cap"]),
        }
        resources.append({"resource_id": _rid(region, brick, product, band),
                          "fields": fields, "evidence_state": "UNRESOLVED"})
    value = {
        "schema_version": "OC3_FIXED_NATIVE_RESOURCE_CONTRACT_001",
        "stage_id": STAGE_ID,
        "locations_binding": {"path": str(LOCATIONS_RELATIVE),
                              "file_sha256": LOCATIONS_FILE_SHA256,
                              "selection_sha256": SELECTION_SHA256},
        "directory_evidence": {"resolved_auxiliary_contract_path": str(AUX_CONTRACT_RELATIVE),
                               "resolved_auxiliary_contract_sha256": AUX_CONTRACT_SHA256},
        "documentary_authorities": [files_doc, "OC3_BOUNDED_AUXILIARY_PIXEL_PILOT_SPEC.md"],
        "resources": resources,
    }
    value = _seal(value)
    validate_fixed_native_contract(value, require_resolved=False)
    return value


def validate_fixed_native_contract(value: dict, *, require_resolved: bool) -> dict:
    _strict(value, CONTRACT_KEYS, "FIXED_CONTRACT_SCHEMA_INVALID")
    _verify_seal(value)
    if (value["schema_version"] != "OC3_FIXED_NATIVE_RESOURCE_CONTRACT_001" or
            value["stage_id"] != STAGE_ID or
            value["locations_binding"] != {"path": str(LOCATIONS_RELATIVE),
                                           "file_sha256": LOCATIONS_FILE_SHA256,
                                           "selection_sha256": SELECTION_SHA256}):
        raise FixedNativeContractError("FIXED_CONTRACT_BINDING_INVALID")
    resources = value["resources"]
    if not isinstance(resources, list) or len(resources) != RESOURCE_COUNT:
        raise FixedNativeContractError("FIXED_CONTRACT_RESOURCE_COUNT_INVALID")
    identities = []
    for row in resources:
        _strict(row, RESOURCE_KEYS, "FIXED_CONTRACT_RESOURCE_SCHEMA_INVALID")
        _strict(row["fields"], RESOURCE_PROPERTY_KEYS, "FIXED_CONTRACT_RESOURCE_SCHEMA_INVALID")
        for prop in row["fields"].values():
            _strict(prop, {"state", "value", "evidence"}, "FIXED_CONTRACT_PROPERTY_INVALID")
            if prop["state"] not in PROPERTY_STATES or not isinstance(prop["evidence"], list) or not prop["evidence"]:
                raise FixedNativeContractError("FIXED_CONTRACT_PROPERTY_INVALID")
        f = row["fields"]
        identity = (f["region"]["value"], f["product"]["value"], f["band"]["value"])
        identities.append(identity)
        if row["resource_id"] != _rid(identity[0], f["brick"]["value"], identity[1], identity[2]):
            raise FixedNativeContractError("FIXED_CONTRACT_RESOURCE_ID_INVALID")
        if (f["expected_shape"]["value"] != [3600, 3600] or
                f["wcs"]["value"] != {"projection": "TAN", "nominal_pixel_scale_arcsec": 0.262}):
            raise FixedNativeContractError("FIXED_CONTRACT_NATIVE_GRID_INVALID")
        if f["product"]["value"] == "image" and f["logical_hdu"]["value"] != "PRIMARY":
            raise FixedNativeContractError("IMAGE_LOGICAL_ROLE_INVALID")
        if require_resolved:
            for key in ("content_length", "logical_hdu", "physical_image_hdu",
                        "compression_mapping", "dtype"):
                if f[key]["state"] != "OBSERVED_BY_BOUNDED_PROBE" or f[key]["value"] is None:
                    raise FixedNativeContractError("FIXED_CONTRACT_UNRESOLVED")
            if row["evidence_state"] != "OBSERVED_BY_BOUNDED_PROBE":
                raise FixedNativeContractError("FIXED_CONTRACT_UNRESOLVED")
    if identities != list(RESOURCE_ORDER):
        raise FixedNativeContractError("FIXED_CONTRACT_RESOURCE_ORDER_INVALID")
    return value


def _reference_wcs(project: Path, region: str, brick: str) -> WCS:
    _, contract = _directory_evidence(project)
    row = next((r for r in contract["resources"]
                if r["region"]["value"] == region and r["product"]["value"] == "nexp"
                and r["band"]["value"] == "g"), None)
    if row is None:
        raise FixedNativeContractError("REFERENCE_WCS_RESOURCE_MISSING")
    rid = row["resource_id"]
    path = Path(project).resolve() / AUX_RAW_RELATIVE / f"{rid}.fits.fz"
    physical = row["hdu_contract"]["value"]["physical_image_hdu"]
    try:
        header = fits.getheader(path, physical)
    except Exception as exc:
        raise FixedNativeContractError("REFERENCE_WCS_HEADER_FAILURE") from exc
    wcs = WCS(header)
    if wcs.pixel_n_dim != 2 or wcs.world_n_dim != 2 or wcs.has_distortion:
        raise FixedNativeContractError("REFERENCE_WCS_INVALID")
    if str(header.get("BRICK")) != brick:
        raise FixedNativeContractError("REFERENCE_WCS_BRICK_MISMATCH")
    return wcs


PSF_ENDPOINT_KEYS = {"endpoint_path", "required_query_parameters", "optional_query_parameters",
                     "region_layers", "band_semantics", "response_content_type", "fits_structure",
                     "normalization", "units", "failure_behavior", "deployment_version"}


def _source_prop(state: str, value, evidence: list[str]) -> dict:
    if state not in SOURCE_STATES or not evidence:
        raise FixedNativeContractError("PSF_SOURCE_STATE_INVALID")
    return {"state": state, "value": value, "evidence": evidence}


def build_psf_contract(project: Path) -> dict:
    project = Path(project).resolve()
    manifest = verify_locations(project)
    source_urls = [
        "https://www.legacysurvey.org/viewer/urls",
        "https://github.com/legacysurvey/imagine/blob/main/map/urls.py#L215",
        "https://github.com/legacysurvey/imagine/blob/main/map/views.py#L7164-L7444",
    ]
    endpoints = {
        "endpoint_path": _source_prop("DOCUMENTED", "/viewer/coadd-psf/", source_urls[:1]),
        "required_query_parameters": _source_prop("SOURCE_VERIFIED", ["ra", "dec", "layer"], source_urls[1:]),
        "optional_query_parameters": _source_prop("SOURCE_VERIFIED", ["bands"], source_urls[2:]),
        "region_layers": _source_prop("DOCUMENTED", {"south": "ls-dr9-south", "north": "ls-dr9-north"}, source_urls),
        "band_semantics": _source_prop("SOURCE_VERIFIED", "one response may contain all available requested optical bands; omitted bands defaults to layer bands", source_urls[2:]),
        "response_content_type": _source_prop("SOURCE_VERIFIED", "image/fits on success", source_urls[2:]),
        "fits_structure": _source_prop("SOURCE_VERIFIED", "one image HDU per returned band; primary header BANDS/BANDi and each image header BAND", source_urls[2:]),
        "normalization": _source_prop("SOURCE_VERIFIED", "per-exposure PSF requested with normalizePsf=True then median-invvar weighted per band", source_urls[2:]),
        "units": _source_prop("UNRESOLVED", None, ["official source does not label output units"]),
        "failure_behavior": _source_prop("SOURCE_VERIFIED", "bands with zero accumulated inverse variance are omitted; no returned bands yields textual no-CCDs response", source_urls[2:]),
        "deployment_version": _source_prop("UNRESOLVED", None, ["public source does not attest exact deployed commit"]),
    }
    points = []
    identities = []
    transports = []
    wcs_by_region = {}
    for location in manifest["locations"]:
        slot, region, brick = location["slot"], location["region"], location["brick"]
        wcs = wcs_by_region.setdefault(region, _reference_wcs(project, region, brick))
        layer = "ls-dr9-south" if region == "south" else "ls-dr9-north"
        for point_id, dx, dy in PSF_POINTS:
            x, y = location["x"] + dx, location["y"] + dy
            ra, dec = wcs.all_pix2world(float(x), float(y), 0)
            ra, dec = float(ra) % 360.0, float(dec)
            if not (math.isfinite(ra) and math.isfinite(dec)):
                raise FixedNativeContractError("PSF_POINT_WCS_FAILURE")
            transport_id = _transport_id(slot, point_id)
            url = ("https://www.legacysurvey.org/viewer/coadd-psf/?ra="
                   f"{ra:.15g}&dec={dec:.15g}&layer={layer}")
            points.append({"slot": slot, "region": region, "brick": brick,
                           "point_id": point_id, "offset_xy": [dx, dy],
                           "native_xy": [x, y], "ra_dec": [ra, dec], "layer": layer,
                           "transport_id": transport_id})
            transports.append({"transport_id": transport_id, "slot": slot,
                               "point_id": point_id, "literal_url": url,
                               "query_bands_parameter": None,
                               "expected_observational_bands": list(BANDS),
                               "state": "PROSPECTIVE_NOT_EXECUTED"})
            for band in BANDS:
                identities.append({"identity_id": _psf_id(slot, point_id, band),
                                   "slot": slot, "point_id": point_id, "band": band,
                                   "transport_id": transport_id,
                                   "availability": "UNOBSERVED"})
    value = _seal({
        "schema_version": "OC3_PSF_RESOURCE_CONTRACT_001",
        "stage_id": "OC3-PSF-RESOURCE-CONTRACT-001",
        "locations_binding": {"path": str(LOCATIONS_RELATIVE),
                              "file_sha256": LOCATIONS_FILE_SHA256,
                              "selection_sha256": SELECTION_SHA256},
        "provider_contract": endpoints,
        "spatial_points": points,
        "observational_identities": identities,
        "transport_requests": transports,
        "counts": {"locations": 6, "spatial_points": 18,
                   "observational_identities": 54, "prospective_http_responses": 18},
    })
    validate_psf_contract(value)
    return value


def validate_psf_contract(value: dict) -> dict:
    _strict(value, {"schema_version", "stage_id", "locations_binding", "provider_contract",
                    "spatial_points", "observational_identities", "transport_requests",
                    "counts", "sealed"}, "PSF_CONTRACT_SCHEMA_INVALID")
    _verify_seal(value)
    if (value["schema_version"] != "OC3_PSF_RESOURCE_CONTRACT_001" or
            value["locations_binding"]["selection_sha256"] != SELECTION_SHA256 or
            value["counts"] != {"locations": 6, "spatial_points": 18,
                                "observational_identities": 54, "prospective_http_responses": 18}):
        raise FixedNativeContractError("PSF_CONTRACT_BINDING_INVALID")
    _strict(value["provider_contract"], PSF_ENDPOINT_KEYS, "PSF_PROVIDER_SCHEMA_INVALID")
    for prop in value["provider_contract"].values():
        _strict(prop, {"state", "value", "evidence"}, "PSF_PROVIDER_SCHEMA_INVALID")
        if prop["state"] not in SOURCE_STATES or not prop["evidence"]:
            raise FixedNativeContractError("PSF_PROVIDER_SCHEMA_INVALID")
    points, identities, transports = (value["spatial_points"], value["observational_identities"],
                                      value["transport_requests"])
    if len(points) != 18 or len(identities) != 54 or len(transports) != 18:
        raise FixedNativeContractError("PSF_CONTRACT_COUNT_INVALID")
    expected_points = [(slot, p[0]) for slot in SLOTS for p in PSF_POINTS]
    if [(p["slot"], p["point_id"]) for p in points] != expected_points:
        raise FixedNativeContractError("PSF_POINT_ORDER_INVALID")
    expected_ids = [(slot, point, band) for slot in SLOTS for point, _, _ in PSF_POINTS for band in BANDS]
    if [(r["slot"], r["point_id"], r["band"]) for r in identities] != expected_ids:
        raise FixedNativeContractError("PSF_IDENTITY_ORDER_INVALID")
    transport_ids = {r["transport_id"] for r in transports}
    if len(transport_ids) != 18 or any(r["transport_id"] not in transport_ids for r in identities):
        raise FixedNativeContractError("PSF_TRANSPORT_BINDING_INVALID")
    for p in points:
        expected_layer = "ls-dr9-south" if p["region"] == "south" else "ls-dr9-north"
        if p["layer"] != expected_layer:
            raise FixedNativeContractError("PSF_LAYER_BINDING_INVALID")
    return value


def build_probe_binding(project: Path, contract: dict) -> dict:
    project = Path(project).resolve()
    validate_fixed_native_contract(contract, require_resolved=False)
    resources = []
    for row in contract["resources"]:
        f = row["fields"]
        resources.append({"resource_id": row["resource_id"],
                          **{key: f[key]["value"] for key in
                             ("region", "brick", "product", "band", "filename",
                              "directory_component", "literal_url", "max_bytes")}})
    return _seal({
        "schema_version": "OC3_FIXED_NATIVE_RESOURCE_PROBE_BINDING_001",
        "stage_id": STAGE_ID,
        "locations_binding": {"path": str(LOCATIONS_RELATIVE),
                              "file_sha256": LOCATIONS_FILE_SHA256,
                              "selection_sha256": SELECTION_SHA256},
        "base_contract": {"path": str(CONTRACT_RELATIVE),
                          "sha256": hashlib.sha256(canonical(contract) + b"\n").hexdigest()},
        "cumulative_budget": {"starting_requests": START_REQUESTS,
                              "starting_body_bytes": START_BODY_BYTES,
                              "global_body_cap": GLOBAL_BODY_CAP,
                              "historical_request_value_is_not_a_future_hard_stop": 200},
        "policy": {"max_new_requests": MAX_NEW_REQUESTS,
                   "max_head_requests": MAX_HEAD_REQUESTS,
                   "max_range_requests": MAX_RANGE_REQUESTS,
                   "max_range_body_bytes": MAX_RANGE_BODY_BYTES,
                   "header_block_bytes": HEADER_BLOCK,
                   "max_header_blocks_per_resource": MAX_HEADER_BLOCKS_PER_RESOURCE,
                   "retries": RETRIES, "concurrency": CONCURRENCY,
                   "durable_head_checkpoints": True,
                   "durable_resource_checkpoints": True,
                   "science_pixel_decode": False, "bulk_get": False},
        "implementation": {"entrypoint_path": "oc3/oc3_fixed_native_resource_contract.py",
                           "entrypoint_sha256": file_hash(project / "oc3/oc3_fixed_native_resource_contract.py"),
                           "module_path": "oc3/oc3lib/fixed_native_contract.py",
                           "module_sha256": file_hash(project / "oc3/oc3lib/fixed_native_contract.py")},
        "resources": resources,
        "acquisition_authorized": False,
    })


def validate_probe_binding(binding: dict, project: Path, contract: dict) -> dict:
    _verify_seal(binding)
    expected = build_probe_binding(project, contract)
    if binding != expected:
        raise FixedNativeContractError("PROBE_BINDING_MISMATCH")
    if len(binding["resources"]) != 12 or binding["acquisition_authorized"] is not False:
        raise FixedNativeContractError("PROBE_BINDING_MISMATCH")
    for resource in binding["resources"]:
        parsed = urlsplit(resource["literal_url"])
        expected_path = (f"/cfs/cosmo/data/legacysurvey/dr9/{resource['region']}/coadd/"
                         f"{resource['directory_component']}/{resource['brick']}/{resource['filename']}")
        if (parsed.scheme != "https" or parsed.hostname != ALLOWED_HOST or
                parsed.port not in (None, 443) or parsed.query or parsed.fragment or
                parsed.path != expected_path or resource["max_bytes"] != MAX_RESOURCE_BYTES):
            raise FixedNativeContractError("PROBE_LITERAL_RESOURCE_INVALID")
    return binding


def load_probe_binding(path: Path, project: Path) -> tuple[dict, dict]:
    contract = _canonical_load(Path(project).resolve() / CONTRACT_RELATIVE)
    validate_fixed_native_contract(contract, require_resolved=False)
    binding = _canonical_load(path)
    validate_probe_binding(binding, project, contract)
    return binding, contract


def _immutable_json(path: Path, value: dict) -> str:
    data = canonical(value) + b"\n"
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise FixedNativeContractError("IMMUTABLE_EVIDENCE_CONFLICT")
    else:
        with path.open("xb") as handle:
            handle.write(data); handle.flush(); os.fsync(handle.fileno())
    return hashlib.sha256(data).hexdigest()


def _atomic_json(path: Path, value: dict) -> None:
    data = canonical(value) + b"\n"
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("wb") as handle:
        handle.write(data); handle.flush(); os.fsync(handle.fileno())
    os.replace(temporary, path)


class EvidenceStore:
    def __init__(self, root: Path, binding: dict):
        self.root = Path(root)
        if self.root.exists():
            raise FixedNativeContractError("PROBE_LOCAL_STATE_CONFLICT")
        self.root.mkdir(parents=True)
        self.sequence = 0
        self.aggregate = {
            "schema_version": "OC3_FIXED_NATIVE_PROBE_AGGREGATE_001",
            "stage_id": STAGE_ID, "binding_seal": binding["sealed"], "state": "ACTIVE",
            "counters": {"local_requests": 0, "local_head_requests": 0,
                         "local_range_requests": 0, "local_range_body_bytes": 0,
                         "local_range_body_bytes_observed": 0,
                         "cumulative_requests": START_REQUESTS,
                         "cumulative_body_bytes": START_BODY_BYTES,
                         "science_pixel_values_observed": 0, "bulk_get_requests": 0},
            "resources": [{"resource_id": row["resource_id"], "state": "NOT_STARTED",
                           "head_checkpoint": None, "resource_checkpoint": None,
                           "failure": None} for row in binding["resources"]],
            "last_event": "INITIALIZED", "terminal": None,
        }
        _immutable_json(self.root / "PROBE_BINDING_COPY.json", binding)
        self._snapshot("INITIALIZED")

    def row(self, rid: str) -> dict:
        return next(row for row in self.aggregate["resources"] if row["resource_id"] == rid)

    def _snapshot(self, event: str) -> None:
        self.sequence += 1
        self.aggregate["last_event"] = event
        value = _seal(self.aggregate)
        _immutable_json(self.root / "AGGREGATE_HISTORY" / f"{self.sequence:04d}.json", value)
        _atomic_json(self.root / "PROBE_AGGREGATE.json", value)

    def reserve(self, kind: str, rid: str) -> None:
        c = self.aggregate["counters"]
        if c["local_requests"] + 1 > MAX_NEW_REQUESTS:
            raise FixedNativeContractError("PROBE_LOCAL_REQUEST_LIMIT", rid)
        if kind == "HEAD":
            if c["local_head_requests"] + 1 > MAX_HEAD_REQUESTS:
                raise FixedNativeContractError("PROBE_HEAD_REQUEST_LIMIT", rid)
            c["local_head_requests"] += 1
        elif kind == "RANGE":
            if c["local_range_requests"] + 1 > MAX_RANGE_REQUESTS:
                raise FixedNativeContractError("PROBE_RANGE_REQUEST_LIMIT", rid)
            if c["local_range_body_bytes"] + HEADER_BLOCK > MAX_RANGE_BODY_BYTES:
                raise FixedNativeContractError("PROBE_RANGE_BYTE_LIMIT", rid)
            if c["cumulative_body_bytes"] + HEADER_BLOCK > GLOBAL_BODY_CAP:
                raise FixedNativeContractError("PROBE_GLOBAL_BODY_LIMIT", rid)
            c["local_range_requests"] += 1
            c["local_range_body_bytes"] += HEADER_BLOCK
            c["cumulative_body_bytes"] += HEADER_BLOCK
        else:
            raise FixedNativeContractError("PROBE_REQUEST_KIND_INVALID", rid)
        c["local_requests"] += 1
        c["cumulative_requests"] += 1
        self._snapshot(f"{kind}_REQUEST_RESERVED:{rid}")

    def record_body(self, rid: str, size: int) -> None:
        if not 0 <= size <= HEADER_BLOCK:
            raise FixedNativeContractError("PROBE_BODY_ACCOUNTING_INVALID", rid)
        self.aggregate["counters"]["local_range_body_bytes_observed"] += size
        self._snapshot(f"RANGE_BODY_ACCOUNTED:{rid}")

    def publish_head(self, resource: dict, evidence: dict) -> dict:
        value = _seal({"schema_version": "OC3_FIXED_NATIVE_HEAD_CHECKPOINT_001",
                       "stage_id": STAGE_ID, "resource_id": resource["resource_id"], **evidence})
        relative = Path("HEAD_EVIDENCE") / f"{resource['resource_id']}.json"
        sha = _immutable_json(self.root / relative, value)
        row = self.row(resource["resource_id"])
        row["state"] = "HEAD_VALIDATED"
        row["head_checkpoint"] = {"path": str(relative), "sha256": sha,
                                  "seal": value["sealed"]}
        self._snapshot(f"HEAD_VALIDATED:{resource['resource_id']}")
        return value

    def publish_resource(self, resource: dict, evidence: dict) -> dict:
        value = _seal({"schema_version": "OC3_FIXED_NATIVE_RESOURCE_CHECKPOINT_001",
                       "stage_id": STAGE_ID, "resource_id": resource["resource_id"], **evidence})
        relative = Path("RESOURCE_CHECKPOINTS") / f"{resource['resource_id']}.json"
        sha = _immutable_json(self.root / relative, value)
        row = self.row(resource["resource_id"])
        row["state"] = "HEADER_RESOLVED"
        row["resource_checkpoint"] = {"path": str(relative), "sha256": sha,
                                      "seal": value["sealed"]}
        self._snapshot(f"HEADER_RESOLVED:{resource['resource_id']}")
        return value

    def terminal(self, state: str, error: FixedNativeContractError | None = None,
                 contract_sha256: str | None = None) -> dict:
        c = self.aggregate["counters"]
        value = {"stage_id": STAGE_ID, "state": state,
                 "error": error.code if error else None,
                 "resource_id": error.resource_id if error else None,
                 "observed_header_blocks": error.observed_header_blocks if error else None,
                 "network_requests_started": c["local_requests"],
                 "network_bytes_observed": c["local_range_body_bytes_observed"],
                 "network_bytes_charged": c["local_range_body_bytes"],
                 "cumulative_requests": c["cumulative_requests"],
                 "cumulative_body_bytes": c["cumulative_body_bytes"],
                 "resources_resolved": sum(r["state"] == "HEADER_RESOLVED" for r in self.aggregate["resources"]),
                 "resolved_contract_sha256": contract_sha256,
                 "science_pixel_values_observed": 0, "bulk_get_requests": 0}
        self.aggregate["state"] = state
        self.aggregate["terminal"] = value
        self._snapshot(f"TERMINAL:{state}")
        _immutable_json(self.root / "PROBE_TERMINAL.json", value)
        return value


def _card_value(card: bytes):
    text = card.decode("ascii", errors="strict")
    if text[8:10] != "= ":
        return None
    raw = text[10:80].split("/", 1)[0].strip()
    if raw.startswith("'") and raw.endswith("'"):
        return raw[1:-1].replace("''", "'").strip()
    if raw == "T": return True
    if raw == "F": return False
    try: return int(raw)
    except ValueError:
        try: return float(raw.replace("D", "E"))
        except ValueError: return raw


def _padded_data_bytes(header: dict) -> int:
    bitpix = abs(int(header.get("BITPIX", 0) or 0))
    naxis = int(header.get("NAXIS", 0) or 0)
    elements = 0 if naxis == 0 else 1
    for axis in range(1, naxis + 1):
        elements *= int(header.get(f"NAXIS{axis}", 0) or 0)
    raw = (bitpix // 8) * elements + int(header.get("PCOUNT", 0) or 0)
    raw *= int(header.get("GCOUNT", 1) or 1)
    return ((raw + HEADER_BLOCK - 1) // HEADER_BLOCK) * HEADER_BLOCK


def _parse_hdu(read_block: Callable[[int, int], bytes], start: int, rid: str,
               count: list[int], requested: list[list[int]]) -> tuple[dict, int]:
    cards = {}
    offset = start
    while count[0] < MAX_HEADER_BLOCKS_PER_RESOURCE:
        body = read_block(offset, offset + HEADER_BLOCK - 1)
        count[0] += 1
        requested.append([offset, offset + HEADER_BLOCK - 1])
        if len(body) != HEADER_BLOCK:
            raise FixedNativeContractError("FITS_HEADER_RANGE_SHORT", rid, count[0])
        for index in range(0, HEADER_BLOCK, 80):
            card = body[index:index + 80]
            key = card[:8].decode("ascii", errors="strict").strip()
            if key == "END":
                return cards, offset + HEADER_BLOCK
            if key and key not in cards:
                cards[key] = _card_value(card)
        offset += HEADER_BLOCK
    raise FixedNativeContractError("FITS_HEADER_BLOCK_CAP", rid, count[0])


def _dtype(bitpix: int) -> str:
    values = {8: "uint8", 16: "int16", 32: "int32", 64: "int64",
              -32: "float32", -64: "float64"}
    if bitpix not in values:
        raise FixedNativeContractError("FITS_BITPIX_UNSUPPORTED")
    return values[bitpix]


def inspect_header(resource: dict, read_block: Callable[[int, int], bytes]) -> dict:
    rid = resource["resource_id"]
    count = [0]
    requested = []
    primary, primary_end = _parse_hdu(read_block, 0, rid, count, requested)
    physical = [{"physical_hdu": 0, "header_end_offset": primary_end,
                 "data_bytes_skipped": _padded_data_bytes(primary)}]
    primary_image = int(primary.get("NAXIS", 0) or 0) == 2
    if primary_image:
        image, physical_hdu, image_end = primary, 0, primary_end
    else:
        extension_start = primary_end + _padded_data_bytes(primary)
        image, image_end = _parse_hdu(read_block, extension_start, rid, count, requested)
        physical_hdu = 1
        physical.append({"physical_hdu": 1, "header_end_offset": image_end,
                         "data_bytes_skipped": _padded_data_bytes(image)})
    compressed = image.get("ZIMAGE") is True
    if compressed:
        shape = [int(image.get("ZNAXIS2", 0)), int(image.get("ZNAXIS1", 0))]
        bitpix = int(image.get("ZBITPIX", 0))
    else:
        shape = [int(image.get("NAXIS2", 0)), int(image.get("NAXIS1", 0))]
        bitpix = int(image.get("BITPIX", 0))
    if shape != [3600, 3600]:
        raise FixedNativeContractError("FITS_NOMINAL_SHAPE_MISMATCH", rid, count[0])
    ctype = [str(image.get("CTYPE1", "")), str(image.get("CTYPE2", ""))]
    if not all("TAN" in item for item in ctype):
        raise FixedNativeContractError("FITS_WCS_NOT_TAN", rid, count[0])
    observed_product = str(image.get("IMTYPE", ""))
    if observed_product and observed_product != resource["product"]:
        raise FixedNativeContractError("FITS_PRODUCT_MISMATCH", rid, count[0])
    if requested[-1][1] >= image_end:
        raise FixedNativeContractError("FIRST_DATA_BLOCK_REQUESTED", rid, count[0])
    logical_hdu = "PRIMARY" if resource["product"] == "image" else physical_hdu
    mapping = ("logical image mapped through FITS tiled-image compression"
               if compressed else "uncompressed physical image HDU")
    return {"header_blocks": count[0], "requested_header_ranges": requested,
            "physical_hdus": physical, "logical_hdu": logical_hdu,
            "physical_image_hdu": physical_hdu, "compressed_image": compressed,
            "compression_mapping": mapping, "shape": shape, "dtype": _dtype(bitpix),
            "observed_bunit": image.get("BUNIT"), "observed_imtype": image.get("IMTYPE"),
            "wcs": {key: image.get(key) for key in
                    ("CTYPE1", "CTYPE2", "CRPIX1", "CRPIX2", "CRVAL1", "CRVAL2",
                     "CD1_1", "CD1_2", "CD2_1", "CD2_2") if key in image},
            "first_data_offset": image_end, "science_pixel_values_observed": 0}


def _resolved_contract(base: dict, store: EvidenceStore, heads: dict, checkpoints: dict) -> dict:
    result = json.loads(json.dumps(base))
    refs = {row["resource_id"]: row for row in store.aggregate["resources"]}
    for row in result["resources"]:
        rid = row["resource_id"]
        head, checkpoint = heads[rid], checkpoints[rid]
        evidence = [f"{STAGE_ID}:{refs[rid]['resource_checkpoint']['sha256']}"]
        f = row["fields"]
        f["content_length"] = _prop("OBSERVED_BY_BOUNDED_PROBE", head["content_length"], evidence)
        f["etag"] = _prop("OBSERVED_BY_BOUNDED_PROBE", head["etag"], evidence)
        f["logical_hdu"] = _prop("OBSERVED_BY_BOUNDED_PROBE", checkpoint["logical_hdu"], evidence)
        f["physical_image_hdu"] = _prop("OBSERVED_BY_BOUNDED_PROBE", checkpoint["physical_image_hdu"], evidence)
        f["compression_mapping"] = _prop("OBSERVED_BY_BOUNDED_PROBE", checkpoint["compression_mapping"], evidence)
        f["dtype"] = _prop("OBSERVED_BY_BOUNDED_PROBE", checkpoint["dtype"], evidence)
        row["evidence_state"] = "OBSERVED_BY_BOUNDED_PROBE"
    result = _seal(result)
    validate_fixed_native_contract(result, require_resolved=True)
    return result


def run_probe(binding: dict, base_contract: dict, transport, audit_root: Path) -> tuple[dict, bool]:
    store = EvidenceStore(audit_root, binding)
    heads = {}
    checkpoints = {}
    current = None
    try:
        for resource in binding["resources"]:
            current = resource["resource_id"]
            store.reserve("HEAD", current)
            status, headers, body, final_url = transport.head(resource["literal_url"])
            if body or status != 200 or final_url != resource["literal_url"] or headers.get("content-encoding", "identity") != "identity":
                raise FixedNativeContractError("HEAD_IDENTITY_FAILURE", current)
            try:
                length = int(headers["content-length"])
            except (KeyError, ValueError) as exc:
                raise FixedNativeContractError("HEAD_LENGTH_UNRESOLVED", current) from exc
            if length <= 0 or length > resource["max_bytes"]:
                raise FixedNativeContractError("HEAD_LENGTH_OUT_OF_BOUND", current)
            evidence = {"literal_url": resource["literal_url"], "status": status,
                        "content_length": length, "etag": headers.get("etag"),
                        "last_modified": headers.get("last-modified"),
                        "content_encoding": headers.get("content-encoding", "identity")}
            heads[current] = store.publish_head(resource, evidence)
        for resource in binding["resources"]:
            current = resource["resource_id"]
            length = heads[current]["content_length"]

            def read_block(start: int, end: int, resource=resource, length=length):
                store.reserve("RANGE", resource["resource_id"])
                status, headers, body, final_url = transport.range(resource["literal_url"], start, end)
                store.record_body(resource["resource_id"], len(body))
                if status != 206:
                    raise FixedNativeContractError("RANGE_STATUS_NOT_206", resource["resource_id"])
                if headers.get("content-range") != f"bytes {start}-{end}/{length}":
                    raise FixedNativeContractError("RANGE_CONTENT_RANGE_MISMATCH", resource["resource_id"])
                if final_url != resource["literal_url"] or headers.get("content-encoding", "identity") != "identity":
                    raise FixedNativeContractError("RANGE_IDENTITY_FAILURE", resource["resource_id"])
                if len(body) != end - start + 1:
                    raise FixedNativeContractError("FITS_HEADER_RANGE_SHORT", resource["resource_id"])
                return body

            structure = inspect_header(resource, read_block)
            checkpoints[current] = store.publish_resource(resource, {
                "head_checkpoint": store.row(current)["head_checkpoint"], **structure})
        resolved = _resolved_contract(base_contract, store, heads, checkpoints)
        output = store.root / "FIXED_NATIVE_RESOURCE_CONTRACT_RESOLVED.json"
        contract_sha = _immutable_json(output, resolved)
        return store.terminal(SUCCESS, contract_sha256=contract_sha), True
    except FixedNativeContractError as error:
        if error.resource_id is None:
            error.resource_id = current
        if current is not None:
            row = store.row(current)
            row["state"] = "FAILED"
            row["failure"] = {"code": error.code,
                              "observed_header_blocks": error.observed_header_blocks}
        return store.terminal(PARTIAL, error=error), False
    except (OSError, TimeoutError, UnicodeError, ValueError):
        error = FixedNativeContractError("PROBE_IO_OR_TRANSPORT_FAILURE", current)
        return store.terminal(PARTIAL, error=error), False


def exact_command(project: Path) -> list[str]:
    project = Path(project).resolve()
    audit = project / AUDIT_RELATIVE
    return [str(project / "oc3/.venv/bin/python"),
            str(project / "oc3/oc3_fixed_native_resource_contract.py"),
            "--execute-probe", "--execute-network", "--project", str(project),
            "--binding", str(project / BINDING_RELATIVE),
            "--audit-directory", str(audit), "--log", str(audit / "PROBE_RUN.log"),
            "--max-new-requests", str(MAX_NEW_REQUESTS),
            "--max-range-requests", str(MAX_RANGE_REQUESTS),
            "--max-range-bytes", str(MAX_RANGE_BODY_BYTES),
            "--max-header-blocks", str(MAX_HEADER_BLOCKS_PER_RESOURCE)]


def dry_run(binding: dict, project: Path) -> dict:
    return {"stage_id": STAGE_ID, "state": "READY_FOR_HUMAN_BOUNDED_HEADER_PROBE",
            "resources": len(binding["resources"]), "starting_cumulative_requests": START_REQUESTS,
            "starting_cumulative_body_bytes": START_BODY_BYTES,
            "max_new_requests": MAX_NEW_REQUESTS, "max_head_requests": MAX_HEAD_REQUESTS,
            "max_range_requests": MAX_RANGE_REQUESTS,
            "max_range_body_bytes": MAX_RANGE_BODY_BYTES,
            "max_header_blocks_per_resource": MAX_HEADER_BLOCKS_PER_RESOURCE,
            "retries": RETRIES, "concurrency": CONCURRENCY,
            "science_pixel_values_observed": 0, "bulk_get_requests": 0,
            "network_requests": 0, "command_argv": exact_command(project),
            "implementation_aggregate": implementation_hash(project)}
