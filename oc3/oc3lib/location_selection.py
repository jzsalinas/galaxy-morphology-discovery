"""Deterministic offline selection of six OC-3 observational locations.

This module has no network transport.  Its only array-bearing inputs are the
14 immutable NEXP, PSFSIZE and optical MASKBITS products acquired by the
sealed auxiliary stage.
"""
from __future__ import annotations

from dataclasses import dataclass
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import stat
import time
from typing import Iterable

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

from .core import canonical, file_hash, implementation_hash


STAGE_ID = "OC3-OFFLINE-LOCATION-SELECTION-001"
SUCCESS = "LOCATION_SELECTION_VALIDATED"
FAILURE = "LOCATION_SELECTION_FAILED"
SPEC_RELATIVE = Path("OC3_BOUNDED_AUXILIARY_PIXEL_PILOT_SPEC.md")
SPEC_SHA256 = "dca2e5f8fe7d0783554116e042c02bcddde7bb083e05a31939fc2fd2bc9151ae"
BRICKS_RELATIVE = Path("oc3/INPUTS/OC3_DEVELOPMENT_BRICKS.csv")
BRICKS_SHA256 = "147c0942a5340ed18eec23a610f8afd5721390fad09c1da7ed01593deb40fab6"
CONTRACT_RELATIVE = Path(
    "oc3/resource_contract/OC3-RESOURCE-CONTRACT-PROBE-002/RESOURCE_CONTRACT_RESOLVED.json")
CONTRACT_SHA256 = "5afff8fddbcb8a9e86ea3f55cf89288840a21ca705bca121ed1b9204c349616d"
CANDIDATE_RELATIVE = Path("oc3/INPUTS/OC3_AUXILIARY_14_ACQUISITION_CANDIDATE_001.json")
CANDIDATE_SHA256 = "c1b07c6df47dc8144786aa1d5065d0a211033c0be1fc3237b967c986ec819850"
ACQUISITION_RELATIVE = Path(
    "oc3/auxiliary_acquisition/OC3-RESOURCE-CONTRACT-AUXILIARY-ACQUISITION-001")
LOCATIONS_RELATIVE = Path("oc3/TECHNICAL_INDEX/OC3_LOCATIONS.json")
FLOW_RELATIVE = Path("oc3/TECHNICAL_INDEX/OC3_SELECTION_FLOW.csv")
AUDIT_RELATIVE = Path("oc3/location_selection/OC3-OFFLINE-LOCATION-SELECTION-001")

SLOTS = ("S1", "S2", "S3", "N1", "N2", "N3")
BANDS = ("g", "r", "z")
ALLOWED_ORDER = tuple(
    (region, product, band)
    for region in ("south", "north")
    for product, bands in (("nexp", BANDS), ("psfsize", BANDS), ("maskbits", (None,)))
    for band in bands
)
ALLOWED_SET = frozenset(ALLOWED_ORDER)
GENERATION = {"south": 9012, "north": 9011}
FLAG_SELECTION = sum(1 << bit for bit in (*range(1, 8), 10, 11, 12, 13))
KNOWN_DR9_MASK = (1 << 14) - 1
LOCATION_KEYS = frozenset(
    ("slot", "region", "brick", "x", "y", "ra_dec", "window",
     "selection_hash", "status", "V"))
WINDOW_KEYS = frozenset(
    ("requested", "obtained", "integer_offset", "offset_in_requested", "padding", "resampling"))
MANIFEST_KEYS = frozenset(("binding", "locations", "selection_sha256"))


class LocationSelectionError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _load_canonical(path: Path) -> dict:
    try:
        raw = Path(path).read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise LocationSelectionError("INVALID_CANONICAL_INPUT") from exc
    if not isinstance(value, dict) or raw != canonical(value) + b"\n":
        raise LocationSelectionError("NONCANONICAL_INPUT")
    return value


def _verify_seal(value: dict) -> None:
    if not isinstance(value, dict) or not isinstance(value.get("sealed"), str):
        raise LocationSelectionError("RESOURCE_PLAN_SEAL_INVALID")
    body = dict(value)
    seal = body.pop("sealed")
    if hashlib.sha256(canonical(body)).hexdigest() != seal:
        raise LocationSelectionError("RESOURCE_PLAN_SEAL_INVALID")


def _write_once(path: Path, data: bytes) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise LocationSelectionError("LOCATION_SELECTION_ALREADY_MATERIALIZED")
    with path.open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def parse_frozen_bricks(path: Path) -> dict[str, str]:
    path = Path(path)
    if (not path.is_file() or path.is_symlink() or file_hash(path) != BRICKS_SHA256):
        raise LocationSelectionError("FROZEN_BRICKS_BINDING_FAILURE")
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise LocationSelectionError("FROZEN_BRICKS_BINDING_FAILURE") from exc
    fields = ["region", "brickname", "development", "holdout_disjoint", "evidence_ref"]
    if reader.fieldnames != fields or len(rows) != 2:
        raise LocationSelectionError("FROZEN_BRICKS_BINDING_FAILURE")
    output = {}
    for row in rows:
        region = row["region"]
        if (region not in ("south", "north") or region in output or
                row["development"] != "true" or row["holdout_disjoint"] != "true" or
                row["evidence_ref"] != "OC3-TECHNICAL-SELECTION-001"):
            raise LocationSelectionError("FROZEN_BRICKS_BINDING_FAILURE")
        output[region] = row["brickname"]
    if tuple(output) != ("south", "north"):
        raise LocationSelectionError("FROZEN_BRICKS_BINDING_FAILURE")
    return output


def reticle(length: int) -> tuple[int, ...]:
    if not isinstance(length, int) or isinstance(length, bool) or length <= 0:
        raise LocationSelectionError("INVALID_NATIVE_AXIS")
    return tuple(sorted(set(range(0, length, 64)) | {length - 1}))


def complete_centers(shape: tuple[int, int]) -> tuple[tuple[int, int], ...]:
    height, width = shape
    return tuple((x, y) for y in reticle(height) for x in reticle(width)
                 if 64 <= x <= width - 65 and 64 <= y <= height - 65)


def selection_hash(slot: str, region: str, brick: str, x: int, y: int) -> str:
    if slot not in SLOTS or region not in ("south", "north"):
        raise LocationSelectionError("SELECTION_HASH_DOMAIN")
    text = f"OC3-v1|{slot}|{region}|{brick}|{x}|{y}"
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def ra_in_bounds(ra, ramin: float, ramax: float):
    values = np.mod(np.asarray(ra, dtype=np.float64), 360.0)
    lower, upper = ramin % 360.0, ramax % 360.0
    if lower <= upper:
        return (values >= lower) & (values < upper)
    return (values >= lower) | (values < upper)


def primary_mask(wcs: WCS, shape: tuple[int, int], bounds: tuple[float, float, float, float],
                 chunk_rows: int = 256) -> np.ndarray:
    height, width = shape
    ramin, ramax, decmin, decmax = bounds
    output = np.empty((height, width), dtype=bool)
    xs = np.arange(width, dtype=np.float64)
    for start in range(0, height, chunk_rows):
        stop = min(height, start + chunk_rows)
        yy = np.arange(start, stop, dtype=np.float64)[:, None]
        xx = np.broadcast_to(xs, (stop - start, width))
        yy = np.broadcast_to(yy, xx.shape)
        ra, dec = wcs.all_pix2world(xx, yy, 0)
        finite = np.isfinite(ra) & np.isfinite(dec)
        output[start:stop] = finite & ra_in_bounds(ra, ramin, ramax) & (dec >= decmin) & (dec < decmax)
    return output


def boundary_distance(window: np.ndarray) -> float:
    """Discrete geometric-boundary distance in the native pixel plane.

    A boundary lies halfway between horizontally or vertically adjacent pixel
    centers whose BRICK_PRIMARY membership differs.
    """
    values = np.asarray(window, dtype=bool)
    if values.shape != (129, 129) or values.all() or not values.any():
        raise LocationSelectionError("BOUNDARY_WINDOW_REQUIRED")
    distances = []
    hy, hx = np.nonzero(values[:, 1:] != values[:, :-1])
    if len(hx):
        distances.append(np.hypot((hx + .5) - 64.0, hy - 64.0))
    vy, vx = np.nonzero(values[1:, :] != values[:-1, :])
    if len(vx):
        distances.append(np.hypot(vx - 64.0, (vy + .5) - 64.0))
    if not distances:
        raise LocationSelectionError("PRIMARY_BOUNDARY_NOT_RESOLVED")
    return float(min(np.min(item) for item in distances))


def n2_class(windows: Iterable[np.ndarray]) -> int | None:
    arrays = tuple(np.asarray(item) for item in windows)
    if any(np.any(item == 0) and np.any(item > 0) for item in arrays):
        return 0
    if any(np.any(item == 1) for item in arrays):
        return 1
    return None


def n3_variation(windows: Iterable[np.ndarray]) -> float | None:
    arrays = tuple(np.asarray(item, dtype=np.float64) for item in windows)
    if len(arrays) != 3 or any(item.shape != (129, 129) for item in arrays):
        raise LocationSelectionError("N3_WINDOW_CONTRACT")
    if any(not np.all(np.isfinite(item)) or np.any(item <= 0) for item in arrays):
        return None
    medians = np.asarray([np.median(item) for item in arrays], dtype=np.float64)
    within = [float((np.max(item) - np.min(item)) / median)
              for item, median in zip(arrays, medians)]
    across = float(np.max(medians) / np.min(medians) - 1.0)
    value = max(*within, across)
    if not math.isfinite(value):
        raise LocationSelectionError("N3_NONFINITE_VARIATION")
    return float(value)


def _grid_error(reference: WCS, other: WCS, shape: tuple[int, int]) -> float:
    height, width = shape
    xs = np.asarray([-.5, 0., (width - 1) / 2, width - 1., width - .5])
    ys = np.asarray([-.5, 0., (height - 1) / 2, height - 1., height - .5])
    xx, yy = np.meshgrid(xs, ys)
    world = reference.all_pix2world(np.column_stack((xx.ravel(), yy.ravel())), 0)
    pixels = other.all_world2pix(world, 0)
    expected = np.column_stack((xx.ravel(), yy.ravel()))
    if not np.all(np.isfinite(pixels)):
        return math.inf
    return float(np.max(np.abs(pixels - expected)))


@dataclass
class RegionBundle:
    region: str
    brick: str
    arrays: dict[tuple[str, str | None], np.ndarray]
    headers: dict[tuple[str, str | None], fits.Header]
    wcs: WCS
    bounds: tuple[float, float, float, float]
    primary: np.ndarray
    file_hashes: dict[str, str]
    grid_error_max_pixels: float


class AuxiliaryObservationGuard:
    """Fail closed before path construction or FITS opening for other products."""
    def __init__(self, resources: dict[tuple[str, str, str | None], dict], raw_root: Path):
        if set(resources) != ALLOWED_SET:
            raise LocationSelectionError("AUXILIARY_IDENTITY_SET_MISMATCH")
        self._resources = resources
        self._root = Path(raw_root).resolve()
        self.observed: list[tuple[str, str, str | None]] = []

    def observe(self, region: str, product: str, band: str | None) -> tuple[np.ndarray, fits.Header, str]:
        identity = (region, product, band)
        if identity not in ALLOWED_SET or identity not in self._resources:
            raise LocationSelectionError("UNAUTHORIZED_PRODUCT_OBSERVATION")
        row = self._resources[identity]
        path = (self._root / f"{row['resource_id']}.fits.fz").resolve()
        if path.parent != self._root or not path.is_file() or path.is_symlink():
            raise LocationSelectionError("RAW_IMMUTABLE_RESOURCE_MISSING")
        self.observed.append(identity)
        expected_hdu = row["physical_hdu"]
        try:
            with fits.open(path, mode="readonly", memmap=False, do_not_scale_image_data=True,
                           uint=False, lazy_load_hdus=False) as hdus:
                if expected_hdu >= len(hdus) or hdus[expected_hdu].data is None:
                    raise LocationSelectionError("AUXILIARY_HDU_MISMATCH")
                array = np.array(hdus[expected_hdu].data, copy=True)
                header = hdus[expected_hdu].header.copy()
        except LocationSelectionError:
            raise
        except Exception as exc:
            raise LocationSelectionError("AUXILIARY_FITS_DECODE_FAILURE") from exc
        return array, header, file_hash(path)


def _validate_array(region: str, brick: str, product: str, band: str | None,
                    array: np.ndarray, header: fits.Header, expected_dtype: str) -> WCS:
    if array.ndim != 2 or array.shape != (3600, 3600):
        raise LocationSelectionError("AUXILIARY_NATIVE_SHAPE_MISMATCH")
    if str(array.dtype) != expected_dtype:
        raise LocationSelectionError("AUXILIARY_DTYPE_MISMATCH")
    if product in ("nexp", "maskbits"):
        if not np.issubdtype(array.dtype, np.integer) or np.any(array < 0):
            raise LocationSelectionError("AUXILIARY_NONNEGATIVE_INTEGER_FAILURE")
    elif product == "psfsize":
        if not np.issubdtype(array.dtype, np.floating) or str(header.get("BUNIT", "")).lower() != "arcsec":
            raise LocationSelectionError("PSFSIZE_CONTRACT_FAILURE")
    else:
        raise LocationSelectionError("UNAUTHORIZED_PRODUCT_OBSERVATION")
    if str(header.get("BRICK")) != brick or str(header.get("LSDR")) != "DR9":
        raise LocationSelectionError("AUXILIARY_PROVENANCE_MISMATCH")
    if int(header.get("DRVERSIO", -1)) != GENERATION[region]:
        raise LocationSelectionError("AUXILIARY_GENERATION_MISMATCH")
    if product == "nexp" and str(header.get("IMTYPE", "")) != "nexp":
        raise LocationSelectionError("AUXILIARY_PRODUCT_HEADER_MISMATCH")
    if product == "psfsize" and str(header.get("IMTYPE", "")) != "psfsize":
        raise LocationSelectionError("AUXILIARY_PRODUCT_HEADER_MISMATCH")
    if product == "maskbits" and str(header.get("IMTYPE", "")) != "maskbits":
        raise LocationSelectionError("AUXILIARY_PRODUCT_HEADER_MISMATCH")
    if "TAN" not in str(header.get("CTYPE1", "")) or "TAN" not in str(header.get("CTYPE2", "")):
        raise LocationSelectionError("AUXILIARY_WCS_MISMATCH")
    wcs = WCS(header)
    if wcs.pixel_n_dim != 2 or wcs.world_n_dim != 2 or wcs.has_distortion:
        raise LocationSelectionError("UNSUPPORTED_WCS_LAYOUT")
    return wcs


def load_region_bundle(region: str, brick: str, guard: AuxiliaryObservationGuard,
                       resources: dict[tuple[str, str, str | None], dict]) -> RegionBundle:
    arrays = {}
    headers = {}
    hashes = {}
    reference_wcs = None
    reference_bounds = None
    worst = 0.0
    for product, bands in (("nexp", BANDS), ("psfsize", BANDS), ("maskbits", (None,))):
        for band in bands:
            identity = (region, product, band)
            array, header, sha = guard.observe(*identity)
            expected_dtype = resources[identity]["expected_dtype"]
            current_wcs = _validate_array(region, brick, product, band, array, header, expected_dtype)
            try:
                bounds = tuple(float(header[key]) for key in ("RAMIN", "RAMAX", "DECMIN", "DECMAX"))
            except (KeyError, TypeError, ValueError) as exc:
                raise LocationSelectionError("BRICK_PRIMARY_BOUNDS_MISSING") from exc
            if not all(math.isfinite(value) for value in bounds) or not bounds[2] < bounds[3]:
                raise LocationSelectionError("BRICK_PRIMARY_BOUNDS_INVALID")
            if reference_wcs is None:
                reference_wcs, reference_bounds = current_wcs, bounds
            else:
                if bounds != reference_bounds:
                    raise LocationSelectionError("BRICK_PRIMARY_BOUNDS_MISMATCH")
                worst = max(worst, _grid_error(reference_wcs, current_wcs, array.shape))
            arrays[(product, band)] = array
            headers[(product, band)] = header
            hashes[resources[identity]["resource_id"]] = sha
    if worst > 1e-6:
        raise LocationSelectionError("AUXILIARY_GRID_MISMATCH")
    mask = primary_mask(reference_wcs, (3600, 3600), reference_bounds)
    return RegionBundle(region, brick, arrays, headers, reference_wcs, reference_bounds,
                        mask, hashes, worst)


def _features(bundle: RegionBundle) -> tuple[list[dict], int]:
    height, width = bundle.primary.shape
    full = complete_centers((height, width))
    total_reticle = len(reticle(width)) * len(reticle(height))
    output = []
    maskbits = bundle.arrays[("maskbits", None)]
    for x, y in full:
        sl = np.s_[y - 64:y + 65, x - 64:x + 65]
        primary_window = bundle.primary[sl]
        inside = bool(np.all(primary_window))
        mixed = bool(np.any(primary_window) and not inside)
        allowed_mask = bool(np.any(np.bitwise_and(maskbits[sl], FLAG_SELECTION) != 0))
        feature = {"x": x, "y": y, "inside": inside, "mixed": mixed,
                   "boundary_distance": boundary_distance(primary_window) if mixed else None,
                   "allowed_mask": allowed_mask, "n2_class": None, "V": None}
        if bundle.region == "north":
            feature["n2_class"] = n2_class(bundle.arrays[("nexp", band)][sl] for band in BANDS)
            feature["V"] = n3_variation(bundle.arrays[("psfsize", band)][sl] for band in BANDS)
        output.append(feature)
    return output, total_reticle


def _choose(slot: str, region: str, brick: str, pool: list[dict], used: set[tuple[int, int]],
            key) -> tuple[dict, int]:
    excluded = sum((row["x"], row["y"]) in used for row in pool)
    available = [row for row in pool if (row["x"], row["y"]) not in used]
    if not available:
        raise LocationSelectionError(f"MISSING_SLOT_{slot}")
    chosen = min(available, key=key)
    used.add((chosen["x"], chosen["y"]))
    return chosen, excluded


def _slot_hash(slot: str, bundle: RegionBundle, row: dict) -> str:
    return selection_hash(slot, bundle.region, bundle.brick, row["x"], row["y"])


def select_region(bundle: RegionBundle) -> tuple[list[tuple[str, dict, str]], list[dict], dict]:
    features, total_reticle = _features(bundle)
    used: set[tuple[int, int]] = set()
    selected = []
    flow = []
    slots = ("S1", "S2", "S3") if bundle.region == "south" else ("N1", "N2", "N3")
    class_counts = {"class_0": 0, "class_1": 0}
    for slot in slots:
        if slot in ("S1", "N1"):
            pool = [row for row in features if row["inside"]]
            key = lambda row, s=slot: (_slot_hash(s, bundle, row), row["y"], row["x"])
        elif slot == "S2":
            pool = [row for row in features if row["mixed"]]
            key = lambda row: (row["boundary_distance"], _slot_hash(slot, bundle, row), row["y"], row["x"])
        elif slot == "S3":
            pool = [row for row in features if row["allowed_mask"]]
            key = lambda row: (_slot_hash(slot, bundle, row), row["y"], row["x"])
        elif slot == "N2":
            zero = [row for row in features if row["n2_class"] == 0]
            one = [row for row in features if row["n2_class"] == 1]
            class_counts = {"class_0": len(zero), "class_1": len(one)}
            zero_available = [row for row in zero if (row["x"], row["y"]) not in used]
            pool = zero if zero_available else one
            key = lambda row: (int(row["n2_class"]), _slot_hash(slot, bundle, row), row["y"], row["x"])
        else:  # N3
            pool = [row for row in features if row["V"] is not None]
            key = lambda row: (-row["V"], _slot_hash(slot, bundle, row), row["y"], row["x"])
        chosen, exclusions = _choose(slot, bundle.region, bundle.brick, pool, used, key)
        status = "STRATUM_NOT_EXERCISED" if slot == "N3" and chosen["V"] < .10 else "SELECTED"
        selected.append((slot, chosen, status))
        flow.append({"slot": slot, "reticle_count": total_reticle,
                     "geometry_eligible_count": len(features),
                     "stratum_candidate_count": len(pool),
                     "already_used_exclusions": exclusions,
                     "selected": 1, "status": status})
    return selected, flow, {"n2_candidate_counts": class_counts}


def _window(x: int, y: int) -> dict:
    requested = [x - 64, y - 64, x + 65, y + 65]
    return {"requested": requested, "obtained": list(requested),
            "integer_offset": [x - 64, y - 64], "offset_in_requested": [0, 0],
            "padding": False, "resampling": False}


def _location(slot: str, row: dict, status: str, bundle: RegionBundle) -> dict:
    ra, dec = bundle.wcs.all_pix2world(float(row["x"]), float(row["y"]), 0)
    return {"slot": slot, "region": bundle.region, "brick": bundle.brick,
            "x": int(row["x"]), "y": int(row["y"]),
            "ra_dec": [float(ra) % 360.0, float(dec)], "window": _window(row["x"], row["y"]),
            "selection_hash": selection_hash(slot, bundle.region, bundle.brick, row["x"], row["y"]),
            "status": status, "V": float(row["V"]) if slot == "N3" else None}


def _histogram(array: np.ndarray) -> dict[str, int]:
    values, counts = np.unique(array, return_counts=True)
    return {str(int(value)): int(count) for value, count in zip(values, counts)}


def selected_diagnostics(location: dict, bundle: RegionBundle) -> dict:
    x, y = location["x"], location["y"]
    sl = np.s_[y - 64:y + 65, x - 64:x + 65]
    nexp = {band: _histogram(bundle.arrays[("nexp", band)][sl]) for band in BANDS}
    mask = bundle.arrays[("maskbits", None)][sl]
    psf = {}
    for band in BANDS:
        values = bundle.arrays[("psfsize", band)][sl].astype(np.float64)
        finite = values[np.isfinite(values)]
        psf[band] = {"min": float(np.min(finite)) if finite.size else None,
                     "max": float(np.max(finite)) if finite.size else None,
                     "median": float(np.median(finite)) if finite.size else None,
                     "nonfinite_count": int(values.size - finite.size),
                     "nonpositive_count": int(np.sum(np.isfinite(values) & (values <= 0)))}
    return {"nexp_histograms": nexp, "maskbits_histogram": _histogram(mask),
            "unknown_maskbits_pixel_count": int(np.sum(np.bitwise_and(mask, ~KNOWN_DR9_MASK) != 0)),
            "psfsize": psf}


def validate_locations_manifest(manifest: dict, bricks: dict[str, str]) -> None:
    if not isinstance(manifest, dict) or set(manifest) != MANIFEST_KEYS:
        raise LocationSelectionError("LOCATIONS_SCHEMA_FAILURE")
    locations = manifest["locations"]
    if not isinstance(locations, list) or len(locations) != 6:
        raise LocationSelectionError("LOCATIONS_COUNT_FAILURE")
    if [row.get("slot") for row in locations] != list(SLOTS):
        raise LocationSelectionError("LOCATIONS_SLOT_ORDER_FAILURE")
    seen = set()
    for row in locations:
        if not isinstance(row, dict) or set(row) != LOCATION_KEYS:
            raise LocationSelectionError("LOCATIONS_SCHEMA_FAILURE")
        slot, region = row["slot"], row["region"]
        expected_region = "south" if slot.startswith("S") else "north"
        if region != expected_region or row["brick"] != bricks[region]:
            raise LocationSelectionError("LOCATIONS_BRICK_FAILURE")
        if (not isinstance(row["x"], int) or isinstance(row["x"], bool) or
                not isinstance(row["y"], int) or isinstance(row["y"], bool)):
            raise LocationSelectionError("LOCATIONS_COORDINATE_FAILURE")
        identity = (region, row["brick"], row["x"], row["y"])
        if identity in seen:
            raise LocationSelectionError("LOCATIONS_DISTINCTNESS_FAILURE")
        seen.add(identity)
        if row["selection_hash"] != selection_hash(slot, region, row["brick"], row["x"], row["y"]):
            raise LocationSelectionError("LOCATIONS_HASH_FAILURE")
        if not (isinstance(row["ra_dec"], list) and len(row["ra_dec"]) == 2 and
                all(isinstance(value, (int, float)) and math.isfinite(value) for value in row["ra_dec"])):
            raise LocationSelectionError("LOCATIONS_SKY_COORDINATE_FAILURE")
        window = row["window"]
        if (not isinstance(window, dict) or set(window) != WINDOW_KEYS or
                window["requested"] != window["obtained"] or
                window["offset_in_requested"] != [0, 0] or
                window["padding"] is not False or window["resampling"] is not False):
            raise LocationSelectionError("LOCATIONS_WINDOW_FAILURE")
        if slot == "N3":
            if (not isinstance(row["V"], float) or not math.isfinite(row["V"]) or
                    row["status"] not in ("SELECTED", "STRATUM_NOT_EXERCISED")):
                raise LocationSelectionError("LOCATIONS_N3_FAILURE")
        elif row["V"] is not None or row["status"] != "SELECTED":
            raise LocationSelectionError("LOCATIONS_STATUS_FAILURE")
    expected = hashlib.sha256(canonical(locations)).hexdigest()
    if manifest["selection_sha256"] != expected:
        raise LocationSelectionError("LOCATIONS_SELECTION_SEAL_FAILURE")


def verify_acquisition(project: Path) -> tuple[dict, dict, dict]:
    project = Path(project).resolve()
    if file_hash(project / SPEC_RELATIVE) != SPEC_SHA256:
        raise LocationSelectionError("FROZEN_SPECIFICATION_MISMATCH")
    bricks = parse_frozen_bricks(project / BRICKS_RELATIVE)
    contract_path = project / CONTRACT_RELATIVE
    candidate_path = project / CANDIDATE_RELATIVE
    root = project / ACQUISITION_RELATIVE
    if file_hash(contract_path) != CONTRACT_SHA256 or file_hash(candidate_path) != CANDIDATE_SHA256:
        raise LocationSelectionError("RESOURCE_BINDING_MISMATCH")
    contract = _load_canonical(contract_path)
    candidate = _load_canonical(candidate_path)
    ledger = _load_canonical(root / "AUXILIARY_LEDGER.json")
    plan = _load_canonical(root / "AUXILIARY_RESOURCE_PLAN.json")
    terminal = _load_canonical(root / "AUXILIARY_TERMINAL.json")
    _verify_seal(plan)
    if (terminal.get("state") != "AUXILIARY_PRODUCTS_ACQUIRED" or terminal.get("published_count") != 14 or
            terminal.get("location_selection") is not False or ledger.get("state") != "COMPLETE" or
            ledger.get("completed") != ledger.get("published") or len(ledger.get("published", [])) != 14 or
            plan.get("resource_ids") != ledger.get("published") or
            plan.get("candidate_sha256") != CANDIDATE_SHA256 or
            plan.get("resolved_contract_sha256") != CONTRACT_SHA256):
        raise LocationSelectionError("AUXILIARY_ACQUISITION_EVIDENCE_FAILURE")
    candidate_rows = candidate.get("resources")
    contract_rows = {row.get("resource_id"): row for row in contract.get("resources", [])}
    if not isinstance(candidate_rows, list) or len(candidate_rows) != 14:
        raise LocationSelectionError("AUXILIARY_IDENTITY_SET_MISMATCH")
    resources = {}
    for position, (bound, identity) in enumerate(zip(candidate_rows, ALLOWED_ORDER)):
        region, product, band = identity
        if (bound.get("region"), bound.get("product"), bound.get("band")) != identity:
            raise LocationSelectionError("AUXILIARY_ORDER_MISMATCH")
        row = contract_rows.get(bound.get("resource_id"))
        if row is None or (row["region"]["value"], row["product"]["value"], row["band"]["value"]) != identity:
            raise LocationSelectionError("AUXILIARY_CONTRACT_MISMATCH")
        if row["brick"]["value"] != bricks[region]:
            raise LocationSelectionError("AUXILIARY_BRICK_MISMATCH")
        hdu = row["hdu_contract"]["value"].get("physical_image_hdu")
        dtype = row["units_dtype_contract"]["value"].get("dtype")
        if not isinstance(hdu, int) or dtype not in ("int16", "float32"):
            raise LocationSelectionError("AUXILIARY_PHYSICAL_CONTRACT_MISSING")
        rid = bound["resource_id"]
        raw_path = root / "RAW_IMMUTABLE" / f"{rid}.fits.fz"
        if (not raw_path.is_file() or raw_path.is_symlink() or
                stat.S_IMODE(raw_path.stat().st_mode) & 0o222 or
                raw_path.stat().st_size != bound["expected_content_length"] or
                file_hash(raw_path) != ledger["checksums"].get(rid)):
            raise LocationSelectionError("RAW_IMMUTABLE_BINDING_FAILURE")
        resources[identity] = {"resource_id": rid, "physical_hdu": hdu,
                               "expected_dtype": dtype, "position": position}
    if set(resources) != ALLOWED_SET or set(ledger["checksums"]) != {v["resource_id"] for v in resources.values()}:
        raise LocationSelectionError("AUXILIARY_IDENTITY_SET_MISMATCH")
    binding = {
        "schema_version": "OC3_OFFLINE_LOCATION_SELECTION_BINDING_001",
        "stage_id": STAGE_ID,
        "specification_sha256": SPEC_SHA256,
        "development_bricks_sha256": BRICKS_SHA256,
        "resolved_contract_sha256": CONTRACT_SHA256,
        "candidate_sha256": CANDIDATE_SHA256,
        "acquisition_terminal_sha256": file_hash(root / "AUXILIARY_TERMINAL.json"),
        "acquisition_ledger_sha256": file_hash(root / "AUXILIARY_LEDGER.json"),
        "acquisition_resource_plan_sha256": file_hash(root / "AUXILIARY_RESOURCE_PLAN.json"),
        "implementation_aggregate": implementation_hash(project),
        "allowed_products": ["nexp:g,r,z", "psfsize:g,r,z", "maskbits:optical"],
        "network_capability": False,
    }
    return bricks, resources, binding


def _flow_csv(flow: list[dict]) -> bytes:
    from io import StringIO
    fields = ["slot", "reticle_count", "geometry_eligible_count", "stratum_candidate_count",
              "already_used_exclusions", "selected", "status"]
    handle = StringIO(newline="")
    writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(flow)
    return handle.getvalue().encode("utf-8")


def execute(project: Path) -> dict:
    project = Path(project).resolve()
    locations_path = project / LOCATIONS_RELATIVE
    flow_path = project / FLOW_RELATIVE
    audit = project / AUDIT_RELATIVE
    terminal_path = audit / "LOCATION_SELECTION_TERMINAL.json"
    for path in (locations_path, flow_path, audit / "OC3_LOCATION_SELECTION_AGGREGATE.json", terminal_path):
        if path.exists():
            raise LocationSelectionError("LOCATION_SELECTION_ALREADY_MATERIALIZED")
    started_wall, started_cpu = time.monotonic(), time.process_time()
    bricks, resources, binding = verify_acquisition(project)
    guard = AuxiliaryObservationGuard(resources, project / ACQUISITION_RELATIVE / "RAW_IMMUTABLE")
    all_locations = []
    all_flow = []
    diagnostics = {}
    file_hashes = {}
    grid_errors = {}
    n2_counts = {}
    for region in ("south", "north"):
        bundle = load_region_bundle(region, bricks[region], guard, resources)
        selected, flow, extra = select_region(bundle)
        region_locations = [_location(slot, row, status, bundle) for slot, row, status in selected]
        all_locations.extend(region_locations)
        all_flow.extend(flow)
        diagnostics.update({location["slot"]: selected_diagnostics(location, bundle)
                            for location in region_locations})
        file_hashes.update(bundle.file_hashes)
        grid_errors[region] = bundle.grid_error_max_pixels
        if region == "north":
            n2_counts = extra["n2_candidate_counts"]
        del bundle
    if [row["slot"] for row in all_locations] != list(SLOTS):
        raise LocationSelectionError("LOCATION_ORDER_FAILURE")
    manifest = {"binding": binding, "locations": all_locations,
                "selection_sha256": hashlib.sha256(canonical(all_locations)).hexdigest()}
    validate_locations_manifest(manifest, bricks)
    aggregate = {
        "schema_version": "OC3_LOCATION_SELECTION_AGGREGATE_001",
        "stage_id": STAGE_ID,
        "input_hashes": {"development_bricks": BRICKS_SHA256, "resolved_contract": CONTRACT_SHA256,
                         "auxiliary_candidate": CANDIDATE_SHA256,
                         "acquisition_terminal": binding["acquisition_terminal_sha256"],
                         "acquisition_ledger": binding["acquisition_ledger_sha256"],
                         "acquisition_resource_plan": binding["acquisition_resource_plan_sha256"]},
        "array_file_hashes": dict(sorted(file_hashes.items())),
        "allowed_observations": [f"{r}:{p}:{b if b is not None else 'optical'}" for r, p, b in guard.observed],
        "unauthorized_product_observations": 0,
        "network_requests": 0,
        "network_body_bytes": 0,
        "grid_error_max_pixels": grid_errors,
        "n2_candidate_counts": n2_counts,
        "slot_diagnostics": diagnostics,
        "slot_counts": {row["slot"]: {k: row[k] for k in
                        ("reticle_count", "geometry_eligible_count", "stratum_candidate_count",
                         "already_used_exclusions", "selected", "status")} for row in all_flow},
        "n3_selected_V": next(row["V"] for row in all_locations if row["slot"] == "N3"),
        "selected_count": 6,
        "south_count": 3,
        "north_count": 3,
        "row_level_leakage_count": 0,
    }
    terminal = {"stage_id": STAGE_ID, "state": SUCCESS, "selected_count": 6,
                "south_count": 3, "north_count": 3,
                "selection_sha256": manifest["selection_sha256"],
                "unauthorized_product_observations": 0,
                "row_level_leakage_count": 0, "network_requests": 0,
                "network_body_bytes": 0,
                "compute_seconds": round(time.process_time() - started_cpu, 6),
                "wall_seconds": round(time.monotonic() - started_wall, 6)}
    _write_once(flow_path, _flow_csv(all_flow))
    _write_once(audit / "OC3_LOCATION_SELECTION_AGGREGATE.json", canonical(aggregate) + b"\n")
    _write_once(locations_path, canonical(manifest) + b"\n")
    _write_once(audit / "LOCATION_SELECTION_RUN.log", canonical(terminal) + b"\n")
    _write_once(terminal_path, canonical(terminal) + b"\n")
    return terminal


def dry_run(project: Path) -> dict:
    bricks, resources, binding = verify_acquisition(Path(project).resolve())
    return {"stage_id": STAGE_ID, "state": "READY_FOR_OFFLINE_LOCATION_SELECTION",
            "resource_count": len(resources), "bricks": len(bricks),
            "implementation_aggregate": binding["implementation_aggregate"],
            "network_requests": 0, "network_body_bytes": 0,
            "arrays_decoded": 0}
