"""Exact bounded native extraction with no network or scientific interpretation."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Any

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

from .core import canonical, file_hash, implementation_hash


STAGE_ID = "OC3-OFFLINE-NATIVE-EXTRACTION-001"
SUCCESS = "NATIVE_EXTRACTION_VALIDATED"
FAILURE = "NATIVE_EXTRACTION_FAILED"
SPEC_RELATIVE = Path("OC3_OFFLINE_NATIVE_EXTRACTION_SPEC.md")
SPEC_SHA256 = "e5a86e69b97ca1daff42e44e9abfd823a5bb37ccf181f1aec4650dd88264c6d2"
MIP_RELATIVE = Path("MORPHOLOGICAL_INFORMATION_PRESERVATION_SPEC.md")
MIP_SHA256 = "f7f27acbe42a0caecd1f0e4e2e86eedea6c546434d95c16143c0a7d122f38f24"

LOCATIONS_RELATIVE = Path("oc3/TECHNICAL_INDEX/OC3_LOCATIONS.json")
LOCATIONS_SHA256 = "33d593638c074a3ff59d32d3e4c38558e8912377ea15818ca5072087007c97d1"
SELECTION_SHA256 = "2e6f2cb070a363e9e3dbdb1f25670590c33500a293bb926d8ff94657a2ff8860"
LOCATION_TERMINAL_RELATIVE = Path(
    "oc3/location_selection/OC3-OFFLINE-LOCATION-SELECTION-001/LOCATION_SELECTION_TERMINAL.json")

AUX_CONTRACT_RELATIVE = Path(
    "oc3/resource_contract/OC3-RESOURCE-CONTRACT-PROBE-002/RESOURCE_CONTRACT_RESOLVED.json")
AUX_CONTRACT_SHA256 = "5afff8fddbcb8a9e86ea3f55cf89288840a21ca705bca121ed1b9204c349616d"
AUX_ROOT_RELATIVE = Path(
    "oc3/auxiliary_acquisition/OC3-RESOURCE-CONTRACT-AUXILIARY-ACQUISITION-001")
AUX_TERMINAL_SHA256 = "0f39b8f24d2dd2b13590a153f30f7050d5c6f44b3d1d39bc38725b0353eda75b"
AUX_LEDGER_SHA256 = "2fa6121a5ee08f8150c723d2069bcf357f25b67f6a02d14375d84c4265e94ee6"

FIXED_CANDIDATE_RELATIVE = Path(
    "oc3/INPUTS/OC3_FIXED_NATIVE_PSF_ACQUISITION_CANDIDATE_001.json")
FIXED_CANDIDATE_SHA256 = "961a763e5732b38c5193764a785a3799b0a74e9e42de111fa1de08c8d4cc2951"
FIXED_ROOT_RELATIVE = Path(
    "oc3/fixed_native_psf_acquisition/OC3-FIXED-NATIVE-PSF-ACQUISITION-001")
FIXED_TERMINAL_SHA256 = "ca55cd8cd4009b2e5af2466abf6cd08ac3e6b1c2811f3d41fbe7bea495eda875"
FIXED_LEDGER_SHA256 = "fac57a450cb263799e0940c430f730e92835d308c537a8323c3ac4e129b5476c"

PSF_IDENTITIES_RELATIVE = Path("oc3/TECHNICAL_INDEX/OC3_PSF_IDENTITIES.json")
PSF_IDENTITIES_SHA256 = "8c8ec5a14169154fce82f6b7a6de147d08e749ba5b410974fd920411b8fe9036"
STAGE_ROOT_RELATIVE = Path("oc3/NATIVE_EXTRACTION/OC3-OFFLINE-NATIVE-EXTRACTION-001")
MANIFEST_RELATIVE = Path("oc3/TECHNICAL_INDEX/OC3_NATIVE_EXTRACTION_MANIFEST.json")

SLOTS = ("S1", "S2", "S3", "N1", "N2", "N3")
BANDS = ("g", "r", "z")
PRODUCT_ORDER = (("image", "g"), ("image", "r"), ("image", "z"),
                 ("invvar", "g"), ("invvar", "r"), ("invvar", "z"),
                 ("nexp", "g"), ("nexp", "r"), ("nexp", "z"),
                 ("psfsize", "g"), ("psfsize", "r"), ("psfsize", "z"),
                 ("maskbits", None))
EXPECTED_DTYPES = {"image": "float32", "invvar": "float32", "nexp": "int16",
                   "psfsize": "float32", "maskbits": "int16"}
ARRAY_SHAPE = (129, 129)
PARENT_SHAPE = (3600, 3600)
WCS_TOLERANCE_PIXELS = 1e-6
ARRAY_HASH_PREFIX = b"OC3_ARRAY_CONTENT_V1\n"
FORBIDDEN_ARTIFACT_KEYS = frozenset({
    "min", "max", "mean", "median", "std", "percentile", "percentiles",
    "histogram", "histograms", "finite_fraction", "flux", "snr", "moments",
    "centroid", "centroids", "detections", "segmentation", "source_count",
    "source_counts", "morphology", "quality_score", "rgb", "thumbnail",
})


class NativeExtractionError(Exception):
    def __init__(self, code: str, identity: str | None = None):
        self.code = code
        self.identity = identity
        super().__init__(code)


def _canonical_load(path: Path) -> dict:
    try:
        raw = Path(path).read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise NativeExtractionError("CANONICAL_INPUT_INVALID") from exc
    if not isinstance(value, dict) or raw != canonical(value) + b"\n":
        raise NativeExtractionError("CANONICAL_INPUT_INVALID")
    return value


def _seal(value: dict) -> dict:
    body = dict(value)
    body.pop("sealed", None)
    body["sealed"] = hashlib.sha256(canonical(body)).hexdigest()
    return body


def _verify_seal(value: dict) -> None:
    if not isinstance(value, dict) or _seal(value).get("sealed") != value.get("sealed"):
        raise NativeExtractionError("SEAL_INVALID")


def _write_exclusive(path: Path, data: bytes, *, readonly: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise NativeExtractionError("ARTIFACT_ALREADY_EXISTS")
    with path.open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    if readonly:
        os.chmod(path, 0o444)


def _json_exclusive(path: Path, value: dict, *, readonly: bool = False) -> str:
    data = canonical(value) + b"\n"
    _write_exclusive(path, data, readonly=readonly)
    return hashlib.sha256(data).hexdigest()


def _exact_file(project: Path, relative: Path, digest: str) -> Path:
    path = project / relative
    if not path.is_file() or path.is_symlink() or file_hash(path) != digest:
        raise NativeExtractionError("FROZEN_INPUT_HASH_MISMATCH", str(relative))
    return path


def _prop(row: dict, key: str):
    value = row.get(key)
    if not isinstance(value, dict) or "value" not in value:
        raise NativeExtractionError("RESOLVED_CONTRACT_FIELD_MISSING", row.get("resource_id"))
    return value["value"]


def _source_path(project: Path, root: Path, rid: str, nested: str | None = None) -> Path:
    base = (project / root / "RAW_IMMUTABLE").resolve()
    path = base / (nested or "") / (rid + (".fits" if nested == "psf" else ".fits.fz"))
    path = path.resolve()
    if not path.is_relative_to(base) or not path.is_file() or path.is_symlink():
        raise NativeExtractionError("RAW_IMMUTABLE_SOURCE_MISSING", rid)
    if stat.S_IMODE(path.stat().st_mode) & 0o222:
        raise NativeExtractionError("RAW_IMMUTABLE_SOURCE_WRITABLE", rid)
    return path


def _authority_bindings(project: Path) -> dict[str, Any]:
    _exact_file(project, SPEC_RELATIVE, SPEC_SHA256)
    _exact_file(project, MIP_RELATIVE, MIP_SHA256)
    locations_path = _exact_file(project, LOCATIONS_RELATIVE, LOCATIONS_SHA256)
    aux_contract_path = _exact_file(project, AUX_CONTRACT_RELATIVE, AUX_CONTRACT_SHA256)
    fixed_candidate_path = _exact_file(project, FIXED_CANDIDATE_RELATIVE,
                                       FIXED_CANDIDATE_SHA256)
    psf_identities_path = _exact_file(project, PSF_IDENTITIES_RELATIVE,
                                      PSF_IDENTITIES_SHA256)
    aux_terminal_path = _exact_file(project, AUX_ROOT_RELATIVE / "AUXILIARY_TERMINAL.json",
                                    AUX_TERMINAL_SHA256)
    aux_ledger_path = _exact_file(project, AUX_ROOT_RELATIVE / "AUXILIARY_LEDGER.json",
                                  AUX_LEDGER_SHA256)
    fixed_terminal_path = _exact_file(project, FIXED_ROOT_RELATIVE / "ACQUISITION_TERMINAL.json",
                                      FIXED_TERMINAL_SHA256)
    fixed_ledger_path = _exact_file(project, FIXED_ROOT_RELATIVE / "ACQUISITION_LEDGER.json",
                                    FIXED_LEDGER_SHA256)
    location_terminal = _canonical_load(project / LOCATION_TERMINAL_RELATIVE)
    locations = _canonical_load(locations_path)
    aux_contract = _canonical_load(aux_contract_path)
    aux_terminal = _canonical_load(aux_terminal_path)
    aux_ledger = _canonical_load(aux_ledger_path)
    fixed_candidate = _canonical_load(fixed_candidate_path)
    fixed_terminal = _canonical_load(fixed_terminal_path)
    fixed_ledger = _canonical_load(fixed_ledger_path)
    psf_identities = _canonical_load(psf_identities_path)
    if (location_terminal.get("state") != "LOCATION_SELECTION_VALIDATED" or
            location_terminal.get("selection_sha256") != SELECTION_SHA256 or
            locations.get("selection_sha256") != SELECTION_SHA256):
        raise NativeExtractionError("LOCATION_SELECTION_BINDING_INVALID")
    if (aux_terminal.get("state") != "AUXILIARY_PRODUCTS_ACQUIRED" or
            aux_ledger.get("state") != "COMPLETE"):
        raise NativeExtractionError("AUXILIARY_ACQUISITION_STATE_INVALID")
    if (fixed_terminal.get("state") != "BOUNDED_NATIVE_PRODUCTS_ACQUIRED" or
            fixed_ledger.get("state") != "COMPLETE"):
        raise NativeExtractionError("FIXED_ACQUISITION_STATE_INVALID")
    _verify_seal(aux_contract)
    _verify_seal(fixed_candidate)
    _verify_seal(psf_identities)
    return {
        "locations": locations, "aux_contract": aux_contract,
        "aux_ledger": aux_ledger, "fixed_candidate": fixed_candidate,
        "fixed_ledger": fixed_ledger, "psf_identities": psf_identities,
        "manifest_bindings": {
            "spec_sha256": SPEC_SHA256, "mip_sha256": MIP_SHA256,
            "locations_sha256": LOCATIONS_SHA256,
            "selection_sha256": SELECTION_SHA256,
            "auxiliary_contract_sha256": AUX_CONTRACT_SHA256,
            "auxiliary_terminal_sha256": AUX_TERMINAL_SHA256,
            "auxiliary_ledger_sha256": AUX_LEDGER_SHA256,
            "fixed_candidate_sha256": FIXED_CANDIDATE_SHA256,
            "fixed_terminal_sha256": FIXED_TERMINAL_SHA256,
            "fixed_ledger_sha256": FIXED_LEDGER_SHA256,
            "psf_identities_sha256": PSF_IDENTITIES_SHA256,
            "implementation_aggregate": implementation_hash(project),
        },
    }


def build_plan(project: Path, *, verify_body_hashes: bool = True) -> dict:
    project = Path(project).resolve()
    bound = _authority_bindings(project)
    sources: dict[tuple[str, str, str | None], dict] = {}
    aux_rows = [row for row in bound["aux_contract"]["resources"]
                if row.get("batch") == "AUXILIARY_FIRST"]
    if len(aux_rows) != 14:
        raise NativeExtractionError("AUXILIARY_SOURCE_INVENTORY_INVALID")
    for row in aux_rows:
        rid = row["resource_id"]
        region, product, band = _prop(row, "region"), _prop(row, "product"), _prop(row, "band")
        hdu = _prop(row, "hdu_contract")["physical_image_hdu"]
        source = _source_path(project, AUX_ROOT_RELATIVE, rid)
        sources[(region, product, band)] = {
            "resource_id": rid, "region": region, "brick": _prop(row, "brick"),
            "product": product, "band": band, "source_path": str(source.relative_to(project)),
            "source_body_sha256": bound["aux_ledger"]["checksums"][rid],
            "source_shape": _prop(row, "expected_shape"),
            "expected_dtype_name": _prop(row, "units_dtype_contract")["dtype"],
            "source_hdu": hdu,
        }
    fixed_rows = bound["fixed_candidate"]["fixed_native_resources"]
    if len(fixed_rows) != 12:
        raise NativeExtractionError("FIXED_SOURCE_INVENTORY_INVALID")
    for row in fixed_rows:
        rid = row["resource_id"]
        key = (row["region"], row["product"], row["band"])
        source = _source_path(project, FIXED_ROOT_RELATIVE, rid, "fixed_native")
        expected = row["expected_structure"]
        sources[key] = {
            "resource_id": rid, "region": row["region"], "brick": row["brick"],
            "product": row["product"], "band": row["band"],
            "source_path": str(source.relative_to(project)),
            "source_body_sha256": bound["fixed_ledger"]["checksums"][rid],
            "source_shape": expected["shape"], "expected_dtype_name": expected["dtype"],
            "source_hdu": expected["physical_image_hdu"],
        }
    expected_keys = {(region, product, band) for region in ("south", "north")
                     for product, band in PRODUCT_ORDER}
    if set(sources) != expected_keys:
        raise NativeExtractionError("SOURCE_IDENTITY_SET_INVALID")
    for source in sources.values():
        if (source["source_shape"] != list(PARENT_SHAPE) or
                source["expected_dtype_name"] != EXPECTED_DTYPES[source["product"]]):
            raise NativeExtractionError("SOURCE_STRUCTURE_CONTRACT_INVALID",
                                        source["resource_id"])
    if verify_body_hashes:
        for source in sources.values():
            if file_hash(project / source["source_path"]) != source["source_body_sha256"]:
                raise NativeExtractionError("SOURCE_BODY_HASH_MISMATCH", source["resource_id"])
    locations = bound["locations"]["locations"]
    if [row.get("slot") for row in locations] != list(SLOTS):
        raise NativeExtractionError("LOCATION_ORDER_INVALID")
    crops = []
    for location in locations:
        x, y = location["x"], location["y"]
        bounds = [x - 64, y - 64, x + 65, y + 65]
        window = location["window"]
        if (window.get("requested") != bounds or window.get("obtained") != bounds or
                window.get("integer_offset") != bounds[:2] or
                window.get("offset_in_requested") != [0, 0] or
                window.get("padding") is not False or window.get("resampling") is not False):
            raise NativeExtractionError("FROZEN_WINDOW_INVALID", location["slot"])
        for product, band in PRODUCT_ORDER:
            source = sources[(location["region"], product, band)]
            filename = (f"{product}-{band}.npy" if band is not None
                        else "maskbits-optical.npy")
            crops.append({
                "slot": location["slot"], "region": location["region"],
                "brick": location["brick"], "product": product, "band": band,
                "slice_bounds_xy": bounds, "filename": filename, **source,
            })
    if len(crops) != 78:
        raise NativeExtractionError("CROP_PLAN_COUNT_INVALID")
    psf_rows = bound["fixed_candidate"]["psf_transport_resources"]
    psf_mappings = []
    identities = {row["identity_id"]: row for row in bound["psf_identities"]["identities"]}
    for row in psf_rows:
        rid = row["resource_id"]
        source = _source_path(project, FIXED_ROOT_RELATIVE, rid, "psf")
        checkpoint = _canonical_load(project / FIXED_ROOT_RELATIVE / "CHECKPOINTS" / f"{rid}.json")
        _verify_seal(checkpoint)
        if verify_body_hashes and file_hash(source) != bound["fixed_ledger"]["checksums"][rid]:
            raise NativeExtractionError("PSF_SOURCE_HASH_MISMATCH", rid)
        image_hdus = [item for item in checkpoint["descriptor"]["hdus"] if item["is_image"]]
        plane_mapping = {item["band"]: item["physical_hdu"] for item in image_hdus}
        shape_mapping = {item["band"]: item["shape"] for item in image_hdus}
        identity_ids = row["observational_identity_ids"]
        if (plane_mapping != {"g": 0, "r": 1, "z": 2} or
                shape_mapping != row["expected_shapes"] or
                any(identity not in identities for identity in identity_ids)):
            raise NativeExtractionError("PSF_MAPPING_INVALID", rid)
        psf_mappings.append({
            "slot": row["slot"], "region": row["region"], "brick": row["brick"],
            "point_id": row["point_id"], "transport_id": rid,
            "source_response_path": str(source.relative_to(project)),
            "source_response_sha256": bound["fixed_ledger"]["checksums"][rid],
            "plane_mapping": plane_mapping,
            "observational_identity_ids": identity_ids,
            "native_provider_shapes": shape_mapping,
        })
    if (len(psf_mappings) != 18 or
            len({identity for row in psf_mappings
                 for identity in row["observational_identity_ids"]}) != 54):
        raise NativeExtractionError("PSF_INVENTORY_INVALID")
    return {"authority_bindings": bound["manifest_bindings"], "crops": crops,
            "psf_mappings": psf_mappings}


class BoundedSectionAccessor:
    """Return only an authorized compressed-image section and track technical access."""

    def __init__(self, fits_module=fits):
        self._fits = fits_module
        self.section_calls = 0
        self.authorized_elements_returned = 0
        self.full_plane_materializations = 0
        self.unauthorized_pixels_exposed = 0

    def read(self, path: Path, hdu_index: int, bounds: list[int],
             expected_shape: list[int]) -> tuple[np.ndarray, fits.Header]:
        x0, y0, x1, y1 = bounds
        if (not isinstance(expected_shape, list) or len(expected_shape) != 2 or
                any(not isinstance(value, int) or value <= 0 for value in expected_shape) or
                x1 - x0 != 129 or y1 - y0 != 129 or
                not (0 <= x0 < x1 <= expected_shape[1] and
                     0 <= y0 < y1 <= expected_shape[0])):
            raise NativeExtractionError("SECTION_BOUNDS_INVALID")
        try:
            with self._fits.open(path, mode="readonly", memmap=False,
                                 do_not_scale_image_data=True, uint=False,
                                 lazy_load_hdus=True) as hdus:
                if not isinstance(hdu_index, int) or not 0 <= hdu_index < len(hdus):
                    raise NativeExtractionError("SOURCE_HDU_INVALID")
                hdu = hdus[hdu_index]
                if not isinstance(hdu, self._fits.CompImageHDU):
                    raise NativeExtractionError("SOURCE_NOT_TILED_COMPRESSED_IMAGE")
                if bool(getattr(hdu, "_data_loaded", False)):
                    raise NativeExtractionError("FULL_PLANE_ALREADY_MATERIALIZED")
                header = hdu.header.copy()
                section = np.asarray(hdu.section[y0:y1, x0:x1])
                if bool(getattr(hdu, "_data_loaded", False)):
                    self.full_plane_materializations += 1
                    raise NativeExtractionError("FULL_PLANE_MATERIALIZATION_FORBIDDEN")
        except NativeExtractionError:
            raise
        except Exception as exc:
            raise NativeExtractionError("BOUNDED_SECTION_DECODE_FAILED") from exc
        if section.shape != ARRAY_SHAPE:
            raise NativeExtractionError("SECTION_SHAPE_INVALID")
        descriptor = section.dtype.str
        if not section.flags.c_contiguous:
            section = np.ascontiguousarray(section)
        if section.dtype.str != descriptor:
            raise NativeExtractionError("SECTION_DTYPE_CHANGED")
        self.section_calls += 1
        self.authorized_elements_returned += section.size
        return section, header


def array_content_hash(array: np.ndarray) -> str:
    value = np.asarray(array)
    metadata = {"dtype": value.dtype.str, "order": "C", "shape": list(value.shape)}
    return hashlib.sha256(ARRAY_HASH_PREFIX + canonical(metadata) + b"\n" +
                          value.tobytes(order="C")).hexdigest()


def write_canonical_npy(path: Path, array: np.ndarray) -> dict:
    value = np.asarray(array)
    if (value.shape != ARRAY_SHAPE or value.dtype.hasobject or value.dtype.fields is not None or
            not value.flags.c_contiguous):
        raise NativeExtractionError("CANONICAL_ARRAY_INPUT_INVALID")
    _write_exclusive(path, b"")
    try:
        with path.open("wb") as handle:
            np.lib.format.write_array(handle, value, version=(1, 0), allow_pickle=False)
            handle.flush()
            os.fsync(handle.fileno())
        with path.open("rb") as handle:
            reloaded = np.lib.format.read_array(handle, allow_pickle=False)
    except Exception as exc:
        raise NativeExtractionError("CANONICAL_NPY_WRITE_FAILED") from exc
    if (reloaded.dtype.str != value.dtype.str or reloaded.shape != value.shape or
            reloaded.tobytes(order="C") != value.tobytes(order="C")):
        raise NativeExtractionError("SOURCE_EQUALITY_FAILURE")
    source_hash = array_content_hash(value)
    output_hash = array_content_hash(reloaded)
    if source_hash != output_hash:
        raise NativeExtractionError("ARRAY_CONTENT_HASH_MISMATCH")
    return {"array_content_sha256": output_hash, "artifact_sha256": file_hash(path),
            "output_dtype": reloaded.dtype.str, "output_shape": list(reloaded.shape)}


def _json_value(value):
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, np.generic):
        return value.item()
    raise NativeExtractionError("WCS_VALUE_NOT_CANONICAL")


def _wcs_cards(wcs: WCS) -> list[list[Any]]:
    return [[card.keyword, _json_value(card.value)]
            for card in wcs.to_header(relax=True).cards]


def wcs_provenance(header: fits.Header, bounds: list[int]) -> dict:
    x0, y0, _, _ = bounds
    try:
        parent = WCS(header, relax=True)
    except Exception as exc:
        raise NativeExtractionError("PARENT_WCS_UNSUPPORTED") from exc
    if (parent.pixel_n_dim != 2 or parent.world_n_dim != 2 or
            bool(parent.has_distortion) or
            list(parent.wcs.ctype) != ["RA---TAN", "DEC--TAN"] or
            "CRPIX1" not in header or "CRPIX2" not in header):
        raise NativeExtractionError("PARENT_WCS_UNSUPPORTED")
    translated_header = header.copy()
    translated_header["CRPIX1"] = header["CRPIX1"] - x0
    translated_header["CRPIX2"] = header["CRPIX2"] - y0
    try:
        translated = WCS(translated_header, relax=True)
        points = np.array([[64.0, 64.0], [0.0, 0.0], [128.0, 0.0],
                           [0.0, 128.0], [128.0, 128.0]])
        parent_points = points + np.array([x0, y0])
        world = parent.all_pix2world(parent_points, 0)
        roundtrip = translated.all_world2pix(world, 0)
        residual = max(abs(float(value)) for value in (roundtrip - points).ravel())
    except Exception as exc:
        raise NativeExtractionError("TRANSLATED_WCS_VALIDATION_FAILED") from exc
    if not np.isfinite(residual) or residual > WCS_TOLERANCE_PIXELS:
        raise NativeExtractionError("TRANSLATED_WCS_RESIDUAL_EXCEEDED")
    parent_cards = _wcs_cards(parent)
    translated_cards = _wcs_cards(translated)
    raw_header = header.tostring(sep="\n", endcard=True, padding=False).encode("ascii")
    return {
        "parent_header_sha256": hashlib.sha256(raw_header).hexdigest(),
        "parent_wcs_cards": parent_cards,
        "parent_wcs_sha256": hashlib.sha256(canonical(parent_cards)).hexdigest(),
        "integer_origin_xy": [x0, y0],
        "translated_wcs_cards": translated_cards,
        "translated_wcs_sha256": hashlib.sha256(canonical(translated_cards)).hexdigest(),
        "validation_points": 5,
        "residual_upper_bound_pixels": residual,
        "residual_threshold_pixels": WCS_TOLERANCE_PIXELS,
    }


def _assert_no_science_fields(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in FORBIDDEN_ARTIFACT_KEYS:
                raise NativeExtractionError("SCIENCE_STATISTIC_FIELD_FORBIDDEN")
            _assert_no_science_fields(child)
    elif isinstance(value, list):
        for child in value:
            _assert_no_science_fields(child)


def _aggregate(accessor: BoundedSectionAccessor) -> dict:
    return {
        "slots": 6, "crop_arrays": 78, "psf_response_mappings": 18,
        "psf_observational_identities": 54, "padding_count": 0,
        "resampling_count": 0, "shape_failures": 0, "dtype_failures": 0,
        "source_equality_failures": 0, "unauthorized_product_observations": 0,
        "bounded_section_calls": accessor.section_calls,
        "authorized_elements_returned": accessor.authorized_elements_returned,
        "full_plane_materializations": accessor.full_plane_materializations,
        "unauthorized_pixels_exposed": accessor.unauthorized_pixels_exposed,
        "science_statistics_produced": 0, "network_requests": 0,
    }


def validate_inputs(project: Path) -> dict:
    plan = build_plan(project, verify_body_hashes=True)
    return {"stage_id": STAGE_ID, "state": "NATIVE_EXTRACTION_INPUTS_VALIDATED",
            "crop_plan_count": len(plan["crops"]),
            "psf_mapping_count": len(plan["psf_mappings"]),
            "science_pixels_accessed": 0, "network_requests": 0}


def _promote(staging: Path, raw: Path) -> None:
    if not staging.is_dir() or raw.exists():
        raise NativeExtractionError("ATOMIC_PROMOTION_PRECONDITION_FAILED")
    os.replace(staging, raw)


def execute(project: Path, *, accessor: BoundedSectionAccessor | None = None) -> dict:
    project = Path(project).resolve()
    root = project / STAGE_ROOT_RELATIVE
    manifest_path = project / MANIFEST_RELATIVE
    if root.exists() or manifest_path.exists():
        raise NativeExtractionError("SECOND_PUBLICATION_REFUSED")
    plan = build_plan(project, verify_body_hashes=True)
    root.mkdir(parents=True)
    staging = root / "STAGING"
    staging.mkdir()
    accessor = accessor or BoundedSectionAccessor()
    crop_records = []
    current = None
    try:
        for row in plan["crops"]:
            current = f"{row['slot']}:{row['product']}:{row['band']}"
            source_path = project / row["source_path"]
            array, header = accessor.read(source_path, row["source_hdu"],
                                          row["slice_bounds_xy"], row["source_shape"])
            if array.dtype.name != row["expected_dtype_name"]:
                raise NativeExtractionError("SOURCE_DTYPE_MISMATCH", current)
            image_guard = (array.tobytes(order="C") if row["product"] == "image" else None)
            target = staging / row["slot"] / row["filename"]
            hashes = write_canonical_npy(target, array)
            if image_guard is not None and image_guard != array.tobytes(order="C"):
                raise NativeExtractionError("IMAGE_VALUE_MUTATION", current)
            provenance = wcs_provenance(header, row["slice_bounds_xy"])
            crop_records.append({
                "slot": row["slot"], "region": row["region"], "brick": row["brick"],
                "product": row["product"], "band": row["band"],
                "source_resource_id": row["resource_id"],
                "source_path": row["source_path"],
                "source_body_sha256": row["source_body_sha256"],
                "source_shape": row["source_shape"], "source_dtype": array.dtype.str,
                "source_hdu": row["source_hdu"],
                "slice_bounds_xy": row["slice_bounds_xy"],
                "output_shape": hashes["output_shape"],
                "output_dtype": hashes["output_dtype"],
                "artifact_path": str((root / "RAW_IMMUTABLE" / row["slot"] /
                                      row["filename"]).relative_to(project)),
                "array_content_sha256": hashes["array_content_sha256"],
                "artifact_sha256": hashes["artifact_sha256"],
                "wcs_provenance": provenance,
            })
        aggregate = _aggregate(accessor)
        if (len(crop_records) != 78 or accessor.section_calls != 78 or
                accessor.authorized_elements_returned != 78 * 129 * 129 or
                accessor.full_plane_materializations != 0 or
                accessor.unauthorized_pixels_exposed != 0):
            raise NativeExtractionError("BOUNDED_ACCESS_COMPLETENESS_FAILURE")
        manifest = _seal({
            "schema_version": "OC3_NATIVE_EXTRACTION_MANIFEST_001",
            "stage_id": STAGE_ID, "state": SUCCESS,
            "authority_bindings": plan["authority_bindings"],
            "format_contract": {
                "artifact": "NUMPY_NPY_V1_0_UNCOMPRESSED",
                "allow_pickle": False, "fortran_order": False,
                "array_content_hash": "OC3_ARRAY_CONTENT_V1",
                "shape": [129, 129], "preserve_dtype_descriptor": True,
            },
            "crops": crop_records, "psf_mappings": plan["psf_mappings"],
            "aggregate": aggregate,
        })
        _assert_no_science_fields(manifest)
        for path in staging.rglob("*.npy"):
            os.chmod(path, 0o444)
        raw = root / "RAW_IMMUTABLE"
        _promote(staging, raw)
        _json_exclusive(manifest_path, manifest, readonly=True)
        audit = {
            "stage_id": STAGE_ID, "state": "NATIVE_EXTRACTION_AUDIT_VALIDATED",
            "manifest_sha256": file_hash(manifest_path), "manifest_seal": manifest["sealed"],
            **aggregate,
        }
        terminal = {"stage_id": STAGE_ID, "state": SUCCESS,
                    "manifest_sha256": file_hash(manifest_path),
                    "manifest_seal": manifest["sealed"], **aggregate}
        _assert_no_science_fields(audit)
        _assert_no_science_fields(terminal)
        _json_exclusive(root / "OC3_NATIVE_EXTRACTION_AUDIT.json", audit, readonly=True)
        _json_exclusive(root / "OC3_NATIVE_EXTRACTION_TERMINAL.json", terminal, readonly=True)
        _json_exclusive(root / "OC3_NATIVE_EXTRACTION_RUN.log", terminal, readonly=True)
        return terminal
    except Exception as exc:
        failure = {"stage_id": STAGE_ID, "state": FAILURE,
                   "error": getattr(exc, "code", "NATIVE_EXTRACTION_INTERNAL_FAILURE"),
                   "identity": current, "published_manifest": False,
                   "network_requests": 0, "science_statistics_produced": 0}
        for name in ("OC3_NATIVE_EXTRACTION_AUDIT.json",
                     "OC3_NATIVE_EXTRACTION_TERMINAL.json",
                     "OC3_NATIVE_EXTRACTION_RUN.log"):
            path = root / name
            if not path.exists():
                _json_exclusive(path, failure, readonly=True)
        if isinstance(exc, NativeExtractionError):
            raise
        raise NativeExtractionError("NATIVE_EXTRACTION_INTERNAL_FAILURE", current) from exc
