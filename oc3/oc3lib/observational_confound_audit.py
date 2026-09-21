"""Deterministic offline two-tier audit of frozen observational products."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
from pathlib import Path
import stat
from typing import Any, Callable

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

from .core import canonical, file_hash, implementation_hash


STAGE_ID = "OC3-OBSERVATIONAL-CONFOUND-AUDIT-001"
SUCCESS = "OBSERVATIONAL_CONFOUND_AUDIT_COMPLETED"
FAILURE = "OBSERVER_AUDIT_INCOMPLETE"
SPEC_RELATIVE = Path("OC3_OBSERVATIONAL_CONFOUND_AUDIT_SPEC.md")
SPEC_SHA256 = "8c997a2eb4a58c50eb72604ab7d1c9a8ece61863ad2af96640bc7569580091c3"
EXTRACTION_SPEC_RELATIVE = Path("OC3_OFFLINE_NATIVE_EXTRACTION_SPEC.md")
EXTRACTION_SPEC_SHA256 = "e5a86e69b97ca1daff42e44e9abfd823a5bb37ccf181f1aec4650dd88264c6d2"
MIP_RELATIVE = Path("MORPHOLOGICAL_INFORMATION_PRESERVATION_SPEC.md")
MIP_SHA256 = "f7f27acbe42a0caecd1f0e4e2e86eedea6c546434d95c16143c0a7d122f38f24"
MANIFEST_RELATIVE = Path("oc3/TECHNICAL_INDEX/OC3_NATIVE_EXTRACTION_MANIFEST.json")
MANIFEST_SHA256 = "f9002086f90d70eab2e0a9dcf76b6e5099f21847449053a819191b05717fc298"
MANIFEST_SEAL = "3083c3004419c5bd72eee12aeb5d2c78ad59703fc88f99fb9d7d0d613648fc75"
LOCATIONS_RELATIVE = Path("oc3/TECHNICAL_INDEX/OC3_LOCATIONS.json")
LOCATIONS_SHA256 = "33d593638c074a3ff59d32d3e4c38558e8912377ea15818ca5072087007c97d1"
SELECTION_SHA256 = "2e6f2cb070a363e9e3dbdb1f25670590c33500a293bb926d8ff94657a2ff8860"
EXTRACTION_ROOT = Path("oc3/NATIVE_EXTRACTION/OC3-OFFLINE-NATIVE-EXTRACTION-001")
EXTRACTION_TERMINAL_RELATIVE = EXTRACTION_ROOT / "OC3_NATIVE_EXTRACTION_TERMINAL.json"
STAGE_ROOT_RELATIVE = Path("oc3/CONFOUND_AUDIT/OC3-OBSERVATIONAL-CONFOUND-AUDIT-001")

SLOTS = ("S1", "S2", "S3", "N1", "N2", "N3")
BANDS = ("g", "r", "z")
TIER_A_PRODUCTS = ("invvar", "nexp", "maskbits", "psfsize")
PRODUCT_ORDER = (("image", "g"), ("image", "r"), ("image", "z"),
                 ("invvar", "g"), ("invvar", "r"), ("invvar", "z"),
                 ("nexp", "g"), ("nexp", "r"), ("nexp", "z"),
                 ("psfsize", "g"), ("psfsize", "r"), ("psfsize", "z"),
                 ("maskbits", None))
FAMILY_ORDER = {name: index for index, name in enumerate(
    ("NEXP", "INVVAR", "MASKBITS", "PSFSIZE", "COADD_PSF", "WCS_GEOMETRY", "IMAGE"))}
QUANTILES = (0.05, 0.25, 0.50, 0.75, 0.95)
KNOWN_MASK = (1 << 14) - 1
OPTICAL_BITS = (*range(1, 8), 10, 11, 12, 13)
OPTICAL_MASK = sum(1 << bit for bit in OPTICAL_BITS)
WISE_MASK = (1 << 8) | (1 << 9)
PSF_HASH_PREFIX = b"OC3_PSF_PLANE_V1\n"
N3_FROZEN_V = 0.8293932498304606
N3_TOLERANCE = 1e-12
METRIC_FIELDS = ("slot", "region", "brick", "tier", "family", "band", "point_id",
                 "metric_id", "level", "value_int", "value_float", "value_text",
                 "unit", "interpretation_scope", "validity_state")
CONTRAST_FIELDS = ("contrast_id", "left_slot", "right_slot", "feature_id", "left_value",
                   "right_value", "signed_difference", "unit", "interpretation_scope",
                   "comparison_state")
CONTRASTS = (("C01", "S1", "S2"), ("C02", "S1", "S3"),
             ("C03", "N1", "N2"), ("C04", "N1", "N3"),
             ("C05", "S1", "N1"))
SLOT_INTENTS = {
    "S1": "south interior observational reference",
    "S2": "south BRICK_PRIMARY boundary condition",
    "S3": "south optical MASKBITS condition",
    "N1": "north interior observational reference",
    "N2": "north exposure-support transition",
    "N3": "north spatial PSFSIZE variation",
}
PRIMARY_ROLES = {
    "S1": "FROZEN_INTERIOR_REFERENCE", "S2": "FROZEN_BOUNDARY_CROSSING",
    "S3": "NOT_CONSTRAINED_BY_SLOT_DESIGN", "N1": "FROZEN_INTERIOR_REFERENCE",
    "N2": "NOT_CONSTRAINED_BY_SLOT_DESIGN", "N3": "NOT_CONSTRAINED_BY_SLOT_DESIGN",
}
QUESTIONS = [
    "Did all six intended observational strata survive exact extraction?",
    "How heterogeneous is exposure support within and between slots?",
    "How heterogeneous is the inverse-variance/noise proxy?",
    "Which optical mask conditions are present and how spatially prevalent are they?",
    "How much PSFSIZE variation exists within and across windows?",
    "Does provider coadd-PSF representation vary across P0/P1/P2 and bands?",
    "Are south and north observational conditions different in ways a future encoder could potentially learn?",
    "Does S2 expose its frozen boundary condition?",
    "Does N2 expose a coverage discontinuity under its frozen class-0 rule?",
    "Does N3 reproduce the deliberately selected PSFSIZE-variation condition?",
    "Which observer variables, if any, warrant later prospective invariance or robustness experiments?",
]


class AuditError(Exception):
    def __init__(self, code: str, identity: str | None = None):
        self.code = code
        self.identity = identity
        super().__init__(code)


def _load_canonical(path: Path) -> dict:
    try:
        raw = Path(path).read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise AuditError("CANONICAL_INPUT_INVALID", str(path)) from exc
    if not isinstance(value, dict) or raw != canonical(value) + b"\n":
        raise AuditError("CANONICAL_INPUT_INVALID", str(path))
    return value


def _seal(value: dict) -> dict:
    body = dict(value)
    body.pop("sealed", None)
    body["sealed"] = hashlib.sha256(canonical(body)).hexdigest()
    return body


def _verify_seal(value: dict, expected: str | None = None) -> None:
    observed = value.get("sealed") if isinstance(value, dict) else None
    if observed != _seal(value).get("sealed") or (expected is not None and observed != expected):
        raise AuditError("SEAL_INVALID")


def _exact_file(project: Path, relative: Path, digest: str) -> Path:
    path = project / relative
    if not path.is_file() or path.is_symlink() or file_hash(path) != digest:
        raise AuditError("FROZEN_INPUT_HASH_MISMATCH", str(relative))
    return path


def _readonly_file(project: Path, relative: str, digest: str) -> Path:
    path = (project / relative).resolve()
    if (not path.is_relative_to(project) or not path.is_file() or path.is_symlink() or
            file_hash(path) != digest or stat.S_IMODE(path.stat().st_mode) & 0o222):
        raise AuditError("IMMUTABLE_INPUT_INVALID", relative)
    return path


def _write_exclusive(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise AuditError("OUTPUT_ALREADY_EXISTS", str(path))
    with path.open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def _write_json(path: Path, value: dict) -> str:
    data = canonical(value) + b"\n"
    _write_exclusive(path, data)
    return hashlib.sha256(data).hexdigest()


def _csv_scalar(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    if isinstance(value, (float, np.floating)):
        number = float(value)
        if not math.isfinite(number):
            raise AuditError("NONFINITE_OUTPUT_FORBIDDEN")
        return json.dumps(number, allow_nan=False, separators=(",", ":"))
    return str(value)


def _write_csv(path: Path, fieldnames: tuple[str, ...] | list[str], rows: list[dict]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise AuditError("OUTPUT_ALREADY_EXISTS", str(path))
    with path.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n",
                                extrasaction="raise")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_scalar(row.get(key)) for key in fieldnames})
        handle.flush()
        os.fsync(handle.fileno())
    return file_hash(path)


def _manifest_plan(project: Path, *, verify_payload_hashes: bool = True) -> dict:
    project = Path(project).resolve()
    _exact_file(project, SPEC_RELATIVE, SPEC_SHA256)
    _exact_file(project, EXTRACTION_SPEC_RELATIVE, EXTRACTION_SPEC_SHA256)
    _exact_file(project, MIP_RELATIVE, MIP_SHA256)
    manifest_path = _exact_file(project, MANIFEST_RELATIVE, MANIFEST_SHA256)
    locations_path = _exact_file(project, LOCATIONS_RELATIVE, LOCATIONS_SHA256)
    manifest = _load_canonical(manifest_path)
    terminal = _load_canonical(project / EXTRACTION_TERMINAL_RELATIVE)
    locations = _load_canonical(locations_path)
    _verify_seal(manifest, MANIFEST_SEAL)
    if (manifest.get("state") != "NATIVE_EXTRACTION_VALIDATED" or
            terminal.get("state") != "NATIVE_EXTRACTION_VALIDATED" or
            manifest.get("aggregate", {}).get("slots") != 6 or
            manifest.get("aggregate", {}).get("crop_arrays") != 78 or
            manifest.get("aggregate", {}).get("psf_response_mappings") != 18 or
            manifest.get("aggregate", {}).get("psf_observational_identities") != 54 or
            locations.get("selection_sha256") != SELECTION_SHA256):
        raise AuditError("EXTRACTION_AUTHORITY_INVALID")
    crops = manifest.get("crops")
    psf = manifest.get("psf_mappings")
    expected = [(slot, product, band) for slot in SLOTS for product, band in PRODUCT_ORDER]
    if (not isinstance(crops, list) or len(crops) != 78 or
            [(row.get("slot"), row.get("product"), row.get("band")) for row in crops] != expected):
        raise AuditError("CROP_INVENTORY_INVALID")
    if (not isinstance(psf, list) or len(psf) != 18 or
            [(row.get("slot"), row.get("point_id")) for row in psf] !=
            [(slot, point) for slot in SLOTS for point in ("P0", "P1", "P2")]):
        raise AuditError("PSF_INVENTORY_INVALID")
    if len({identity for row in psf for identity in row.get("observational_identity_ids", [])}) != 54:
        raise AuditError("PSF_IDENTITY_INVENTORY_INVALID")
    snapshot = {
        str(SPEC_RELATIVE): SPEC_SHA256, str(EXTRACTION_SPEC_RELATIVE): EXTRACTION_SPEC_SHA256,
        str(MIP_RELATIVE): MIP_SHA256, str(MANIFEST_RELATIVE): MANIFEST_SHA256,
        str(LOCATIONS_RELATIVE): LOCATIONS_SHA256,
        str(EXTRACTION_TERMINAL_RELATIVE): file_hash(project / EXTRACTION_TERMINAL_RELATIVE),
    }
    for row in crops:
        if (row.get("output_shape") != [129, 129] or
                row.get("output_dtype") != row.get("source_dtype") or
                row.get("slice_bounds_xy", [0, 0, 0, 0])[2] - row["slice_bounds_xy"][0] != 129 or
                row["slice_bounds_xy"][3] - row["slice_bounds_xy"][1] != 129):
            raise AuditError("CROP_STRUCTURE_INVALID", row.get("slot"))
        path = project / row["artifact_path"]
        if verify_payload_hashes:
            _readonly_file(project, row["artifact_path"], row["artifact_sha256"])
        elif not path.is_file() or path.is_symlink():
            raise AuditError("IMMUTABLE_INPUT_INVALID", row["artifact_path"])
        snapshot[row["artifact_path"]] = row["artifact_sha256"]
    for row in psf:
        path = project / row["source_response_path"]
        if verify_payload_hashes:
            _readonly_file(project, row["source_response_path"], row["source_response_sha256"])
        elif not path.is_file() or path.is_symlink():
            raise AuditError("IMMUTABLE_INPUT_INVALID", row["source_response_path"])
        snapshot[row["source_response_path"]] = row["source_response_sha256"]
    header_rows = {}
    for region in ("south", "north"):
        row = next(item for item in crops if item["region"] == region and
                   item["product"] == "nexp" and item["band"] == "g")
        if verify_payload_hashes:
            _readonly_file(project, row["source_path"], row["source_body_sha256"])
        header_rows[region] = row
        snapshot[row["source_path"]] = row["source_body_sha256"]
    return {"manifest": manifest, "terminal": terminal, "locations": locations,
            "crops": crops, "psf": psf, "header_rows": header_rows,
            "snapshot": snapshot}


def _recheck_snapshot(project: Path, snapshot: dict[str, str]) -> int:
    for relative, expected in snapshot.items():
        path = project / relative
        if not path.is_file() or path.is_symlink() or file_hash(path) != expected:
            raise AuditError("INPUT_MODIFICATION_DETECTED", relative)
    return 0


class ArrayAccessGate:
    """Closed crop reader that enforces complete observer tier before IMAGE."""

    def __init__(self, project: Path, loader: Callable[[Path], np.ndarray] | None = None):
        self.project = Path(project)
        self.loader = loader or self._numpy_loader
        self.tier_a_complete = False
        self.tier_a_crop_reads = 0
        self.image_reads = 0
        self.image_reads_before_tier_a_complete = 0

    @staticmethod
    def _numpy_loader(path: Path) -> np.ndarray:
        with path.open("rb") as handle:
            return np.lib.format.read_array(handle, allow_pickle=False)

    def read(self, row: dict) -> np.ndarray:
        product = row["product"]
        if product == "image":
            if not self.tier_a_complete:
                self.image_reads_before_tier_a_complete += 1
                raise AuditError("IMAGE_BEFORE_TIER_A_COMPLETE", row["slot"])
            self.image_reads += 1
        elif product in TIER_A_PRODUCTS:
            if self.tier_a_complete:
                raise AuditError("TIER_A_READ_AFTER_COMPLETION", row["slot"])
            self.tier_a_crop_reads += 1
        else:
            raise AuditError("UNAUTHORIZED_CROP_PRODUCT", product)
        value = np.asarray(self.loader(self.project / row["artifact_path"]))
        if (value.shape != (129, 129) or value.dtype.str != row["output_dtype"] or
                value.dtype.hasobject or value.dtype.fields is not None):
            raise AuditError("CROP_DECODE_CONTRACT_INVALID", row["slot"])
        return value

    def complete_tier_a(self) -> None:
        if self.tier_a_crop_reads != 60 or self.image_reads != 0:
            raise AuditError("TIER_A_COMPLETENESS_FAILURE")
        self.tier_a_complete = True


def _metric(slot: str, region: str, brick: str, tier: str, family: str,
            metric_id: str, value: Any = None, *, band: str | None = None,
            point_id: str | None = None, level: str | int | None = None,
            unit: str = "dimensionless", validity: str = "DEFINED") -> dict:
    row = {key: None for key in METRIC_FIELDS}
    row.update({"slot": slot, "region": region, "brick": brick, "tier": tier,
                "family": family, "band": band, "point_id": point_id,
                "metric_id": metric_id, "level": level, "unit": unit,
                "interpretation_scope": ("OBSERVER_ONLY" if tier == "A" else
                                         "SCENE_MIXED_OBSERVATION"),
                "validity_state": validity})
    if value is None:
        return row
    if isinstance(value, (bool, str, list, tuple)):
        row["value_text"] = (canonical(list(value)).decode("utf-8")
                             if isinstance(value, (list, tuple)) else
                             ("true" if value is True else "false" if value is False else value))
    elif isinstance(value, (int, np.integer)):
        row["value_int"] = int(value)
    elif isinstance(value, (float, np.floating)):
        if not math.isfinite(float(value)):
            raise AuditError("NONFINITE_OUTPUT_FORBIDDEN", metric_id)
        row["value_float"] = float(value)
    else:
        raise AuditError("UNSUPPORTED_METRIC_VALUE", metric_id)
    return row


def transition_counts(array: np.ndarray) -> tuple[int, int, int]:
    value = np.asarray(array)
    horizontal = int(np.count_nonzero(value[:, 1:] != value[:, :-1]))
    vertical = int(np.count_nonzero(value[1:, :] != value[:-1, :]))
    return horizontal, vertical, horizontal + vertical


def fixed_quantiles(values: np.ndarray) -> dict[str, float]:
    value = np.asarray(values)
    if value.size == 0:
        raise AuditError("NO_VALUES_FOR_QUANTILES")
    observed = np.quantile(value, QUANTILES, method="linear")
    return {name: float(item) for name, item in
            zip(("q05", "q25", "q50", "q75", "q95"), observed)}


def n3_variation(arrays: list[np.ndarray]) -> float:
    values = [np.asarray(item, dtype=np.float64) for item in arrays]
    if (len(values) != 3 or any(item.shape != (129, 129) for item in values) or
            any(not np.all(np.isfinite(item)) or np.any(item <= 0) for item in values)):
        raise AuditError("N3_INPUT_INVALID")
    medians = np.asarray([np.median(item) for item in values], dtype=np.float64)
    within = [float((np.max(item) - np.min(item)) / median)
              for item, median in zip(values, medians)]
    return float(max(*within, float(np.max(medians) / np.min(medians) - 1.0)))


def psf_plane_hash(array: np.ndarray) -> str:
    value = np.asarray(array)
    if not value.flags.c_contiguous:
        value = np.ascontiguousarray(value)
    metadata = {"dtype": value.dtype.str, "order": "C", "shape": list(value.shape)}
    return hashlib.sha256(PSF_HASH_PREFIX + canonical(metadata) + b"\n" +
                          value.tobytes(order="C")).hexdigest()


def raw_peak(array: np.ndarray) -> tuple[int, int] | None:
    value = np.asarray(array)
    finite = np.isfinite(value)
    if not np.any(finite):
        return None
    maximum = np.max(value[finite])
    indexes = np.argwhere(finite & (value == maximum))
    y, x = indexes[0]
    return int(y), int(x)


def psf_raw_sum(array: np.ndarray) -> float | None:
    value = np.asarray(array)
    if not np.all(np.isfinite(value)):
        return None
    return math.fsum(float(item) for item in value.ravel(order="C"))


def ra_in_bounds(ra: np.ndarray, lower: float, upper: float) -> np.ndarray:
    values = np.mod(np.asarray(ra, dtype=np.float64), 360.0)
    lo, hi = lower % 360.0, upper % 360.0
    return ((values >= lo) & (values < hi) if lo <= hi
            else (values >= lo) | (values < hi))


def primary_geometry(wcs: WCS, bounds: tuple[float, float, float, float]) -> dict:
    yy, xx = np.mgrid[0:129, 0:129]
    ra, dec = wcs.all_pix2world(xx.astype(np.float64), yy.astype(np.float64), 0)
    lo, hi, dec_lo, dec_hi = bounds
    mask = (np.isfinite(ra) & np.isfinite(dec) & ra_in_bounds(ra, lo, hi) &
            (dec >= dec_lo) & (dec < dec_hi))
    count = int(np.count_nonzero(mask))
    horizontal, vertical, total = transition_counts(mask)
    if count == mask.size:
        state, distance = "ALL_PRIMARY", None
    elif count == 0:
        state, distance = "NO_PRIMARY", None
    else:
        state = "MIXED_PRIMARY"
        distances = []
        hy, hx = np.nonzero(mask[:, 1:] != mask[:, :-1])
        if len(hx):
            distances.append(np.hypot((hx + .5) - 64.0, hy - 64.0))
        vy, vx = np.nonzero(mask[1:, :] != mask[:-1, :])
        if len(vx):
            distances.append(np.hypot(vx - 64.0, (vy + .5) - 64.0))
        if not distances:
            raise AuditError("PRIMARY_BOUNDARY_NOT_RESOLVED")
        distance = float(min(np.min(item) for item in distances))
    return {"primary_count": count, "nonprimary_count": int(mask.size - count),
            "primary_fraction": float(count / mask.size), "horizontal": horizontal,
            "vertical": vertical, "total": total, "state": state,
            "center_boundary_distance": distance}


def _wrapped_delta(left: float, right: float) -> float:
    return (left - right + 180.0) % 360.0 - 180.0


def wcs_jacobian(wcs: WCS, x: float, y: float) -> dict:
    points = np.asarray([[x, y], [x + .5, y], [x - .5, y],
                         [x, y + .5], [x, y - .5]], dtype=np.float64)
    world = wcs.all_pix2world(points, 0)
    if not np.all(np.isfinite(world)):
        raise AuditError("WCS_JACOBIAN_NONFINITE")
    center = world[0]
    cosdec = math.cos(math.radians(float(center[1])))
    matrix = np.asarray([
        [_wrapped_delta(world[1, 0], world[2, 0]) * cosdec * 3600.0,
         _wrapped_delta(world[3, 0], world[4, 0]) * cosdec * 3600.0],
        [(world[1, 1] - world[2, 1]) * 3600.0,
         (world[3, 1] - world[4, 1]) * 3600.0],
    ], dtype=np.float64)
    singular = np.linalg.svd(matrix, compute_uv=False)
    area = abs(float(np.linalg.det(matrix)))
    if (not np.all(np.isfinite(singular)) or not math.isfinite(area) or
            singular[-1] <= 0 or area <= 0):
        raise AuditError("WCS_JACOBIAN_SINGULAR")
    return {"singular_max": float(singular[0]), "singular_min": float(singular[1]),
            "area": area, "axis_ratio": float(singular[0] / singular[1])}


def _header_bounds(project: Path, row: dict) -> tuple[tuple[float, float, float, float], int]:
    path = project / row["source_path"]
    try:
        with fits.open(path, mode="readonly", memmap=False, do_not_scale_image_data=True,
                       uint=False, lazy_load_hdus=True) as hdus:
            hdu = hdus[row["source_hdu"]]
            if bool(getattr(hdu, "_data_loaded", False)):
                raise AuditError("HEADER_READ_LOADED_DATA", row["region"])
            header = hdu.header.copy()
            bounds = tuple(float(header[key]) for key in
                           ("RAMIN", "RAMAX", "DECMIN", "DECMAX"))
            if bool(getattr(hdu, "_data_loaded", False)):
                raise AuditError("HEADER_READ_LOADED_DATA", row["region"])
    except AuditError:
        raise
    except Exception as exc:
        raise AuditError("BRICK_PRIMARY_HEADER_INVALID", row["region"]) from exc
    if not all(math.isfinite(value) for value in bounds) or not bounds[2] < bounds[3]:
        raise AuditError("BRICK_PRIMARY_BOUNDS_INVALID", row["region"])
    return bounds, 1


def _wcs_from_cards(cards: list[list[Any]]) -> WCS:
    try:
        header = fits.Header()
        for key, value in cards:
            header[key] = value
        result = WCS(header, relax=True)
    except Exception as exc:
        raise AuditError("MANIFEST_WCS_INVALID") from exc
    if result.pixel_n_dim != 2 or result.world_n_dim != 2 or result.has_distortion:
        raise AuditError("MANIFEST_WCS_UNSUPPORTED")
    return result


class AuditEngine:
    def __init__(self, project: Path, plan: dict,
                 gate: ArrayAccessGate | None = None,
                 psf_opener: Callable[[Path], Any] | None = None):
        self.project = Path(project)
        self.plan = plan
        self.gate = gate or ArrayAccessGate(project)
        self.psf_opener = psf_opener
        self.rows: list[dict] = []
        self.features = {slot: {} for slot in SLOTS}
        self.units: dict[str, str] = {}
        self.tier_a_components: set[str] = set()
        self.psf_body_reads = 0
        self.psf_plane_decodes = 0
        self.header_only_reads = 0
        self.stratum_not_expressed = False
        self.witnesses: list[str] = []
        self.nexp_arrays: dict[tuple[str, str], np.ndarray] = {}
        self.psfsize_arrays: dict[tuple[str, str], np.ndarray] = {}

    def add(self, row: dict) -> None:
        self.rows.append(row)

    def add_value(self, source: dict, tier: str, family: str, metric_id: str,
                  value: Any = None, **kwargs) -> None:
        self.add(_metric(source["slot"], source["region"], source["brick"], tier,
                         family, metric_id, value, band=kwargs.pop("band", source.get("band")),
                         **kwargs))

    def feature(self, slot: str, name: str, value: Any, unit: str = "dimensionless") -> None:
        if name in self.features[slot]:
            raise AuditError("DUPLICATE_FEATURE", name)
        self.features[slot][name] = value
        self.units[name] = unit

    def _add_quantiles(self, row: dict, family: str, finite_values: np.ndarray,
                       names: tuple[str, ...] = ("q05", "q25", "q50", "q75", "q95"),
                       prefix: str = "", unit: str = "native") -> dict[str, float] | None:
        if finite_values.size == 0:
            for name in names:
                self.add_value(row, "A" if family != "IMAGE" else "B", family,
                               prefix + name, None, unit=unit, validity="NO_FINITE_VALUES")
            return None
        values = fixed_quantiles(finite_values)
        for name in names:
            self.add_value(row, "A" if family != "IMAGE" else "B", family,
                           prefix + name, values[name], unit=unit)
        return values

    def _nexp(self, row: dict, array: np.ndarray) -> None:
        if array.dtype.kind not in "iu" or np.any(array < 0):
            raise AuditError("NEXP_CONTRACT_INVALID", row["slot"])
        unique, counts = np.unique(array, return_counts=True)
        total = int(array.size)
        zero = int(np.count_nonzero(array == 0))
        positive = int(np.count_nonzero(array > 0))
        horizontal, vertical, transitions = transition_counts(array)
        for level, count in zip(unique, counts):
            self.add_value(row, "A", "NEXP", "level_count", int(count),
                           level=int(level), unit="pixels")
            self.add_value(row, "A", "NEXP", "level_fraction", float(count / total),
                           level=int(level))
        metrics = {
            "pixel_count": (total, "pixels"), "zero_count": (zero, "pixels"),
            "zero_fraction": (zero / total, "dimensionless"),
            "positive_count": (positive, "pixels"),
            "positive_fraction": (positive / total, "dimensionless"),
            "minimum": (int(unique[0]), "exposures"),
            "maximum": (int(unique[-1]), "exposures"),
            "distinct_levels": (len(unique), "levels"),
            "horizontal_transition_count": (horizontal, "edges"),
            "vertical_transition_count": (vertical, "edges"),
            "total_transition_count": (transitions, "edges"),
            "transition_fraction": (transitions / 33024, "dimensionless"),
        }
        for metric_id, (value, unit) in metrics.items():
            self.add_value(row, "A", "NEXP", metric_id, value, unit=unit)
        band = row["band"]
        self.feature(row["slot"], f"nexp_zero_fraction_{band}", zero / total)
        self.feature(row["slot"], f"nexp_positive_fraction_{band}", positive / total)
        self.feature(row["slot"], f"nexp_distinct_levels_{band}", len(unique), "levels")
        self.feature(row["slot"], f"nexp_transition_count_{band}", transitions, "edges")
        self.feature(row["slot"], f"nexp_transition_fraction_{band}", transitions / 33024)
        self.feature(row["slot"], f"nexp_range_{band}", int(unique[-1] - unique[0]), "exposures")
        if transitions > 0:
            self.witnesses.append(f"NEXP:{row['slot']}:{band}")
        self.nexp_arrays[(row["slot"], band)] = array

    def _invvar(self, row: dict, array: np.ndarray) -> None:
        if array.dtype.kind != "f":
            raise AuditError("INVVAR_CONTRACT_INVALID", row["slot"])
        total = int(array.size)
        finite = np.isfinite(array)
        values = array[finite]
        finite_count = int(values.size)
        zero = int(np.count_nonzero(array == 0))
        positive_mask = np.isfinite(array) & (array > 0)
        positive = int(np.count_nonzero(positive_mask))
        negative = int(np.count_nonzero(np.isfinite(array) & (array < 0)))
        basics = {
            "pixel_count": (total, "pixels"), "finite_count": (finite_count, "pixels"),
            "finite_fraction": (finite_count / total, "dimensionless"),
            "nonfinite_count": (total - finite_count, "pixels"),
            "nonfinite_fraction": ((total - finite_count) / total, "dimensionless"),
            "zero_count": (zero, "pixels"), "zero_fraction": (zero / total, "dimensionless"),
            "positive_count": (positive, "pixels"),
            "positive_fraction": (positive / total, "dimensionless"),
            "negative_count": (negative, "pixels"),
            "negative_fraction": (negative / total, "dimensionless"),
        }
        for metric_id, (value, unit) in basics.items():
            self.add_value(row, "A", "INVVAR", metric_id, value, unit=unit)
        if finite_count:
            minimum, maximum = float(np.min(values)), float(np.max(values))
            quantiles = self._add_quantiles(row, "INVVAR", values)
            median, iqr = quantiles["q50"], quantiles["q75"] - quantiles["q25"]
            self.add_value(row, "A", "INVVAR", "finite_minimum", minimum, unit="native")
            self.add_value(row, "A", "INVVAR", "finite_maximum", maximum, unit="native")
            self.add_value(row, "A", "INVVAR", "median", median, unit="native")
            self.add_value(row, "A", "INVVAR", "iqr", iqr, unit="native")
            relative = None if median == 0 else iqr / abs(median)
            self.add_value(row, "A", "INVVAR", "relative_iqr", relative,
                           validity="DEFINED" if relative is not None else "UNDEFINED_ZERO_MEDIAN")
        else:
            minimum = maximum = median = iqr = relative = None
            for metric_id in ("finite_minimum", "finite_maximum", "median", "iqr", "relative_iqr"):
                self.add_value(row, "A", "INVVAR", metric_id, None,
                               unit="native", validity="NO_FINITE_VALUES")
            self._add_quantiles(row, "INVVAR", values)
        sigma = 1.0 / np.sqrt(array[positive_mask].astype(np.float64))
        self.add_value(row, "A", "INVVAR", "diagnostic_sigma_count", sigma.size, unit="pixels")
        self.add_value(row, "A", "INVVAR", "diagnostic_sigma_fraction", sigma.size / total)
        if sigma.size:
            sigma_q = self._add_quantiles(row, "INVVAR", sigma, prefix="diagnostic_sigma_",
                                          unit="diagnostic_sigma")
            sigma_min, sigma_max = float(np.min(sigma)), float(np.max(sigma))
            sigma_median = sigma_q["q50"]
            sigma_iqr = sigma_q["q75"] - sigma_q["q25"]
            for metric_id, value in (("diagnostic_sigma_minimum", sigma_min),
                                     ("diagnostic_sigma_maximum", sigma_max),
                                     ("diagnostic_sigma_median", sigma_median),
                                     ("diagnostic_sigma_iqr", sigma_iqr)):
                self.add_value(row, "A", "INVVAR", metric_id, value, unit="diagnostic_sigma")
        else:
            sigma_median = None
            self._add_quantiles(row, "INVVAR", sigma, prefix="diagnostic_sigma_",
                                unit="diagnostic_sigma")
            for metric_id in ("diagnostic_sigma_minimum", "diagnostic_sigma_maximum",
                              "diagnostic_sigma_median", "diagnostic_sigma_iqr"):
                self.add_value(row, "A", "INVVAR", metric_id, None,
                               unit="diagnostic_sigma", validity="NO_POSITIVE_INVVAR")
        band = row["band"]
        feature_values = {
            f"invvar_finite_fraction_{band}": finite_count / total,
            f"invvar_zero_fraction_{band}": zero / total,
            f"invvar_positive_fraction_{band}": positive / total,
            f"invvar_negative_fraction_{band}": negative / total,
            f"invvar_median_{band}": median, f"invvar_iqr_{band}": iqr,
            f"invvar_relative_iqr_{band}": relative,
            f"diagnostic_sigma_median_{band}": sigma_median,
        }
        for name, value in feature_values.items():
            self.feature(row["slot"], name, value,
                         "native" if "median" in name and "fraction" not in name else "dimensionless")
        if iqr is not None and iqr > 0:
            self.witnesses.append(f"INVVAR:{row['slot']}:{band}")

    def _maskbits(self, row: dict, array: np.ndarray) -> None:
        if array.dtype.kind not in "iu" or np.any(array < 0):
            raise AuditError("MASKBITS_CONTRACT_INVALID", row["slot"])
        raw = array.astype(np.uint64, copy=False)
        total = int(raw.size)
        zero = int(np.count_nonzero(raw == 0))
        optical = int(np.count_nonzero((raw & np.uint64(OPTICAL_MASK)) != 0))
        wise = int(np.count_nonzero((raw & np.uint64(WISE_MASK)) != 0))
        unknown_values = raw & ~np.uint64(KNOWN_MASK)
        unknown = int(np.count_nonzero(unknown_values != 0))
        self.add_value(row, "A", "MASKBITS", "pixel_count", total, unit="pixels")
        for metric_id, count in (("zero", zero), ("optical_any", optical),
                                 ("wise_any", wise), ("unknown", unknown)):
            self.add_value(row, "A", "MASKBITS", metric_id + "_count", count, unit="pixels")
            self.add_value(row, "A", "MASKBITS", metric_id + "_fraction", count / total)
        bit_counts = {}
        for bit in range(14):
            count = int(np.count_nonzero((raw & np.uint64(1 << bit)) != 0))
            bit_counts[bit] = count
            self.add_value(row, "A", "MASKBITS", "bit_count", count,
                           level=bit, unit="pixels")
            self.add_value(row, "A", "MASKBITS", "bit_fraction", count / total, level=bit)
        max_bit = int(np.max(raw)).bit_length() if raw.size else 0
        positions = []
        for bit in range(14, max_bit):
            count = int(np.count_nonzero((raw & np.uint64(1 << bit)) != 0))
            if count:
                positions.append(bit)
                self.add_value(row, "A", "MASKBITS", "unknown_bit_count", count,
                               level=bit, unit="pixels")
                self.add_value(row, "A", "MASKBITS", "unknown_bit_fraction", count / total,
                               level=bit)
        self.add_value(row, "A", "MASKBITS", "unknown_bit_positions", positions)
        optical_expressed = optical > 0
        self.add_value(row, "A", "MASKBITS", "s3_optical_condition_expressed",
                       optical_expressed if row["slot"] == "S3" else None,
                       validity="DEFINED" if row["slot"] == "S3" else "NOT_APPLICABLE")
        slot = row["slot"]
        self.feature(slot, "maskbits_zero_fraction", zero / total)
        self.feature(slot, "maskbits_nprimary_fraction", bit_counts[0] / total)
        self.feature(slot, "maskbits_optical_any_fraction", optical / total)
        self.feature(slot, "maskbits_wise_any_fraction", wise / total)
        for bit in OPTICAL_BITS:
            self.feature(slot, f"maskbits_bit{bit:02d}_fraction", bit_counts[bit] / total)
        self.feature(slot, "maskbits_unknown_fraction", unknown / total)
        if optical or unknown:
            self.witnesses.append(f"MASKBITS:{slot}")
        if slot == "S3" and not optical_expressed:
            self.stratum_not_expressed = True

    def _psfsize(self, row: dict, array: np.ndarray) -> None:
        if array.dtype.kind != "f":
            raise AuditError("PSFSIZE_CONTRACT_INVALID", row["slot"])
        total = int(array.size)
        finite_mask = np.isfinite(array)
        values = array[finite_mask]
        finite_count = int(values.size)
        nonpositive = int(np.count_nonzero(finite_mask & (array <= 0)))
        basics = {"pixel_count": (total, "pixels"), "finite_count": (finite_count, "pixels"),
                  "finite_fraction": (finite_count / total, "dimensionless"),
                  "nonfinite_count": (total - finite_count, "pixels"),
                  "nonfinite_fraction": ((total - finite_count) / total, "dimensionless"),
                  "nonpositive_count": (nonpositive, "pixels"),
                  "nonpositive_fraction": (nonpositive / total, "dimensionless")}
        for metric_id, (value, unit) in basics.items():
            self.add_value(row, "A", "PSFSIZE", metric_id, value, unit=unit)
        if finite_count:
            minimum, maximum = float(np.min(values)), float(np.max(values))
            quantiles = self._add_quantiles(row, "PSFSIZE", values,
                                            names=("q25", "q50", "q75"), unit="arcsec")
            median, iqr = quantiles["q50"], quantiles["q75"] - quantiles["q25"]
            relative = ((maximum - minimum) / median if median > 0 else None)
            for metric_id, value, unit in (("finite_minimum", minimum, "arcsec"),
                                           ("finite_maximum", maximum, "arcsec"),
                                           ("median", median, "arcsec"),
                                           ("iqr", iqr, "arcsec")):
                self.add_value(row, "A", "PSFSIZE", metric_id, value, unit=unit)
            self.add_value(row, "A", "PSFSIZE", "relative_range", relative,
                           validity="DEFINED" if relative is not None else "UNDEFINED_NONPOSITIVE_MEDIAN")
        else:
            minimum = maximum = median = iqr = relative = None
            self._add_quantiles(row, "PSFSIZE", values, names=("q25", "q50", "q75"),
                                unit="arcsec")
            for metric_id in ("finite_minimum", "finite_maximum", "median", "iqr", "relative_range"):
                self.add_value(row, "A", "PSFSIZE", metric_id, None,
                               unit="arcsec", validity="NO_FINITE_VALUES")
        band = row["band"]
        for name, value, unit in (
                (f"psfsize_finite_fraction_{band}", finite_count / total, "dimensionless"),
                (f"psfsize_nonpositive_fraction_{band}", nonpositive / total, "dimensionless"),
                (f"psfsize_median_{band}", median, "arcsec"),
                (f"psfsize_iqr_{band}", iqr, "arcsec"),
                (f"psfsize_relative_range_{band}", relative, "dimensionless")):
            self.feature(row["slot"], name, value, unit)
        if relative is not None and relative > 0:
            self.witnesses.append(f"PSFSIZE:{row['slot']}:{band}")
        self.psfsize_arrays[(row["slot"], band)] = array

    def run_crop_tier_a(self) -> None:
        lookup = {(row["slot"], row["product"], row["band"]): row
                  for row in self.plan["crops"]}
        for slot in SLOTS:
            for family, product, bands in (("NEXP", "nexp", BANDS),
                                           ("INVVAR", "invvar", BANDS),
                                           ("MASKBITS", "maskbits", (None,)),
                                           ("PSFSIZE", "psfsize", BANDS)):
                for band in bands:
                    row = lookup[(slot, product, band)]
                    array = self.gate.read(row)
                    {"NEXP": self._nexp, "INVVAR": self._invvar,
                     "MASKBITS": self._maskbits, "PSFSIZE": self._psfsize}[family](row, array)
        n2_bands = [band for band in BANDS
                    if np.any(self.nexp_arrays[("N2", band)] == 0) and
                    np.any(self.nexp_arrays[("N2", band)] > 0)]
        n2_source = lookup[("N2", "nexp", "g")]
        self.add_value(n2_source, "A", "NEXP", "class_0_condition_expressed",
                       bool(n2_bands), band=None)
        self.add_value(n2_source, "A", "NEXP", "bands_expressing_class_0",
                       n2_bands, band=None)
        if not n2_bands:
            self.stratum_not_expressed = True
        n3_value = n3_variation([self.psfsize_arrays[("N3", band)] for band in BANDS])
        n3_source = lookup[("N3", "psfsize", "g")]
        self.add_value(n3_source, "A", "PSFSIZE", "n3_variation_v", n3_value,
                       band=None)
        difference = abs(n3_value - N3_FROZEN_V)
        self.add_value(n3_source, "A", "PSFSIZE", "n3_frozen_absolute_difference",
                       difference, band=None)
        self.add_value(n3_source, "A", "PSFSIZE", "n3_consistency_expressed",
                       difference <= N3_TOLERANCE, band=None)
        if difference > N3_TOLERANCE:
            raise AuditError("N3_FROZEN_V_MISMATCH")
        self.tier_a_components.add("crop_metrics")

    def _open_psf(self, path: Path):
        if self.psf_opener is not None:
            return self.psf_opener(path)
        return fits.open(path, mode="readonly", memmap=False, do_not_scale_image_data=True,
                         uint=False, lazy_load_hdus=True)

    def run_psf(self) -> None:
        aggregates: dict[tuple[str, str], list[dict]] = {
            (slot, band): [] for slot in SLOTS for band in BANDS}
        for mapping in self.plan["psf"]:
            path = self.project / mapping["source_response_path"]
            try:
                with self._open_psf(path) as hdus:
                    self.psf_body_reads += 1
                    for band_index, band in enumerate(BANDS):
                        hdu_index = mapping["plane_mapping"][band]
                        if not isinstance(hdu_index, int) or not 0 <= hdu_index < len(hdus):
                            raise AuditError("PSF_HDU_INVALID", mapping["transport_id"])
                        array = np.asarray(hdus[hdu_index].data)
                        self.psf_plane_decodes += 1
                        if (list(array.shape) != mapping["native_provider_shapes"][band] or
                                array.ndim != 2 or array.dtype.hasobject or
                                array.dtype.fields is not None):
                            raise AuditError("PSF_PLANE_CONTRACT_INVALID", mapping["transport_id"])
                        source = {**mapping, "band": band}
                        total = int(array.size)
                        finite_mask = np.isfinite(array)
                        values = array[finite_mask]
                        finite_count = int(values.size)
                        minimum = float(np.min(values)) if finite_count else None
                        maximum = float(np.max(values)) if finite_count else None
                        raw_sum = psf_raw_sum(array)
                        peak = raw_peak(array)
                        plane_digest = psf_plane_hash(array)
                        identity = mapping["observational_identity_ids"][band_index]
                        entries = (
                            ("body_sha256", mapping["source_response_sha256"], "sha256", "DEFINED"),
                            ("observational_identity_id", identity, "identifier", "DEFINED"),
                            ("physical_hdu", hdu_index, "index", "DEFINED"),
                            ("height", array.shape[0], "pixels", "DEFINED"),
                            ("width", array.shape[1], "pixels", "DEFINED"),
                            ("dtype_descriptor", array.dtype.str, "numpy_dtype", "DEFINED"),
                            ("element_count", total, "samples", "DEFINED"),
                            ("finite_count", finite_count, "samples", "DEFINED"),
                            ("finite_fraction", finite_count / total, "dimensionless", "DEFINED"),
                            ("nonfinite_count", total - finite_count, "samples", "DEFINED"),
                            ("nonfinite_fraction", (total - finite_count) / total,
                             "dimensionless", "DEFINED"),
                            ("finite_minimum", minimum, "native", "DEFINED" if minimum is not None else "NO_FINITE_VALUES"),
                            ("finite_maximum", maximum, "native", "DEFINED" if maximum is not None else "NO_FINITE_VALUES"),
                            ("raw_sum", raw_sum, "sample_values", "DEFINED" if raw_sum is not None else "NONFINITE_PRESENT"),
                            ("raw_integral", raw_sum, "sample_pixel_units", "DEFINED" if raw_sum is not None else "NONFINITE_PRESENT"),
                            ("raw_peak_coordinate", list(peak) if peak is not None else None,
                             "y_x_index", "DEFINED" if peak is not None else "NO_FINITE_VALUES"),
                            ("plane_content_sha256", plane_digest, "sha256", "DEFINED"),
                            ("physical_psf_shape_metrics", "PHYSICAL_PSF_SHAPE_METRICS_DEFERRED",
                             "state", "DEFERRED_UNRESOLVED_NORMALIZATION"),
                        )
                        for metric_id, value, unit, validity in entries:
                            self.add(_metric(mapping["slot"], mapping["region"], mapping["brick"],
                                             "A", "COADD_PSF", metric_id, value, band=band,
                                             point_id=mapping["point_id"], unit=unit,
                                             validity=validity))
                        aggregates[(mapping["slot"], band)].append({
                            "shape": tuple(array.shape), "dtype": array.dtype.str,
                            "finite_fraction": finite_count / total, "raw_sum": raw_sum,
                            "peak": peak, "hash": plane_digest,
                        })
            except AuditError:
                raise
            except Exception as exc:
                raise AuditError("PSF_RESPONSE_DECODE_FAILED", mapping["transport_id"]) from exc
        if self.psf_body_reads != 18 or self.psf_plane_decodes != 54:
            raise AuditError("PSF_ACCESS_COUNT_INVALID")
        for slot in SLOTS:
            slot_mapping = next(row for row in self.plan["psf"] if row["slot"] == slot)
            for band in BANDS:
                records = aggregates[(slot, band)]
                if len(records) != 3:
                    raise AuditError("PSF_POINT_INVENTORY_INVALID", f"{slot}:{band}")
                shape_agree = len({item["shape"] for item in records}) == 1
                dtype_agree = len({item["dtype"] for item in records}) == 1
                sums = [item["raw_sum"] for item in records]
                if all(value is not None for value in sums):
                    sum_min, sum_max = min(sums), max(sums)
                    sum_range = sum_max - sum_min
                else:
                    sum_min = sum_max = sum_range = None
                peaks = [item["peak"] for item in records]
                if all(value is not None for value in peaks):
                    displacement = max(math.hypot(a[1] - b[1], a[0] - b[0])
                                       for index, a in enumerate(peaks)
                                       for b in peaks[index + 1:])
                else:
                    displacement = None
                distinct_hashes = len({item["hash"] for item in records})
                source = {**slot_mapping, "band": band}
                values = {
                    "shape_agreement": shape_agree, "dtype_agreement": dtype_agree,
                    "finite_fraction_min": min(item["finite_fraction"] for item in records),
                    "raw_sum_min": sum_min, "raw_sum_max": sum_max,
                    "raw_sum_range": sum_range, "distinct_plane_hashes": distinct_hashes,
                    "peak_displacement_max_pixels": displacement,
                }
                for metric_id, value in values.items():
                    self.add_value(source, "A", "COADD_PSF", "p0_p1_p2_" + metric_id,
                                   value, point_id=None,
                                   unit=("pixels" if "displacement" in metric_id else
                                         "sample_values" if "raw_sum" in metric_id else
                                         "dimensionless"))
                shape = records[0]["shape"] if shape_agree else (None, None)
                for name, value, unit in (
                        (f"psf_height_{band}", shape[0], "pixels"),
                        (f"psf_width_{band}", shape[1], "pixels"),
                        (f"psf_finite_fraction_min_{band}", values["finite_fraction_min"], "dimensionless"),
                        (f"psf_raw_sum_min_{band}", sum_min, "sample_values"),
                        (f"psf_raw_sum_max_{band}", sum_max, "sample_values"),
                        (f"psf_raw_sum_range_{band}", sum_range, "sample_values"),
                        (f"psf_distinct_plane_hashes_{band}", distinct_hashes, "count"),
                        (f"psf_peak_displacement_max_pixels_{band}", displacement, "pixels")):
                    self.feature(slot, name, value, unit)
                if distinct_hashes > 1:
                    self.witnesses.append(f"COADD_PSF:{slot}:{band}")
        self.tier_a_components.add("psf")

    def run_geometry(self) -> None:
        bounds_by_region = {}
        for region, row in self.plan["header_rows"].items():
            bounds, reads = _header_bounds(self.project, row)
            bounds_by_region[region] = bounds
            self.header_only_reads += reads
        if self.header_only_reads != 2:
            raise AuditError("HEADER_ONLY_READ_COUNT_INVALID")
        for slot in SLOTS:
            rows = [row for row in self.plan["crops"] if row["slot"] == slot]
            if len(rows) != 13:
                raise AuditError("SLOT_CROP_INVENTORY_INVALID", slot)
            first = rows[0]
            provenance = first["wcs_provenance"]
            agreement = all(
                row["slice_bounds_xy"] == first["slice_bounds_xy"] and
                row["wcs_provenance"]["integer_origin_xy"] == provenance["integer_origin_xy"] and
                row["wcs_provenance"]["parent_wcs_cards"] == provenance["parent_wcs_cards"] and
                row["wcs_provenance"]["translated_wcs_cards"] == provenance["translated_wcs_cards"]
                for row in rows)
            if not agreement:
                raise AuditError("SLOT_WCS_BOUNDS_DISAGREEMENT", slot)
            wcs = _wcs_from_cards(provenance["translated_wcs_cards"])
            primary = primary_geometry(wcs, bounds_by_region[first["region"]])
            max_residual = max(float(row["wcs_provenance"]["residual_upper_bound_pixels"])
                               for row in rows)
            source = {**first, "band": None}
            geometry_values = (
                ("primary_geometry_role", PRIMARY_ROLES[slot], "state"),
                ("observed_primary_geometry_status", primary["state"], "state"),
                ("primary_count", primary["primary_count"], "pixels"),
                ("nonprimary_count", primary["nonprimary_count"], "pixels"),
                ("primary_fraction", primary["primary_fraction"], "dimensionless"),
                ("primary_boundary_horizontal_transitions", primary["horizontal"], "edges"),
                ("primary_boundary_vertical_transitions", primary["vertical"], "edges"),
                ("primary_boundary_transition_count", primary["total"], "edges"),
                ("primary_center_boundary_distance_pixels", primary["center_boundary_distance"], "pixels"),
                ("wcs_roundtrip_residual_max_pixel", max_residual, "pixels"),
                ("padding", False, "boolean"), ("resampling", False, "boolean"),
            )
            for metric_id, value, unit in geometry_values:
                validity = ("NOT_APPLICABLE_NONMIXED" if metric_id ==
                            "primary_center_boundary_distance_pixels" and value is None else "DEFINED")
                self.add_value(source, "A", "WCS_GEOMETRY", metric_id, value,
                               band=None, unit=unit, validity=validity)
            point_defs = (("CENTER", 64.0, 64.0), ("CORNER_00", 0.0, 0.0),
                          ("CORNER_10", 128.0, 0.0), ("CORNER_01", 0.0, 128.0),
                          ("CORNER_11", 128.0, 128.0))
            jacobians = []
            for point_id, x, y in point_defs:
                value = wcs_jacobian(wcs, x, y)
                jacobians.append(value)
                for metric_id, observed, unit in (
                        ("jacobian_singular_max", value["singular_max"], "arcsec_per_pixel"),
                        ("jacobian_singular_min", value["singular_min"], "arcsec_per_pixel"),
                        ("jacobian_determinant_area", value["area"], "arcsec2_per_pixel2"),
                        ("jacobian_axis_ratio", value["axis_ratio"], "dimensionless")):
                    self.add_value(source, "A", "WCS_GEOMETRY", metric_id, observed,
                                   band=None, point_id=point_id, unit=unit)
            areas = [item["area"] for item in jacobians]
            area_min, area_max = min(areas), max(areas)
            area_median = float(np.median(np.asarray(areas, dtype=np.float64)))
            area_relative = (area_max - area_min) / area_median
            axis_max = max(item["axis_ratio"] for item in jacobians)
            pixel_scale = math.sqrt(jacobians[0]["area"])
            summaries = (
                ("pixel_scale_center_arcsec", pixel_scale, "arcsec_per_pixel"),
                ("pixel_area_min_arcsec2", area_min, "arcsec2_per_pixel2"),
                ("pixel_area_max_arcsec2", area_max, "arcsec2_per_pixel2"),
                ("pixel_area_relative_range_5point", area_relative, "dimensionless"),
                ("axis_ratio_max_5point", axis_max, "dimensionless"),
            )
            for metric_id, value, unit in summaries:
                self.add_value(source, "A", "WCS_GEOMETRY", metric_id, value,
                               band=None, unit=unit)
            self.feature(slot, "primary_geometry_role", PRIMARY_ROLES[slot], "state")
            self.feature(slot, "observed_primary_geometry_status", primary["state"], "state")
            for name, value, unit in (
                    ("primary_fraction", primary["primary_fraction"], "dimensionless"),
                    ("primary_boundary_transition_count", primary["total"], "edges"),
                    ("primary_center_boundary_distance_pixels", primary["center_boundary_distance"], "pixels"),
                    ("pixel_scale_center_arcsec", pixel_scale, "arcsec_per_pixel"),
                    ("pixel_area_min_arcsec2", area_min, "arcsec2_per_pixel2"),
                    ("pixel_area_max_arcsec2", area_max, "arcsec2_per_pixel2"),
                    ("pixel_area_relative_range_5point", area_relative, "dimensionless"),
                    ("axis_ratio_max_5point", axis_max, "dimensionless"),
                    ("wcs_roundtrip_residual_max_pixel", max_residual, "pixels")):
                self.feature(slot, name, value, unit)
            if area_relative > 0:
                self.witnesses.append(f"WCS_GEOMETRY:{slot}")
            expected = (primary["state"] == "ALL_PRIMARY" if slot in ("S1", "N1") else
                        primary["state"] == "MIXED_PRIMARY" and
                        primary["primary_count"] > 0 and primary["nonprimary_count"] > 0 and
                        primary["total"] > 0 if slot == "S2" else True)
            if not expected:
                self.stratum_not_expressed = True
        self.tier_a_components.add("geometry")

    def complete_tier_a(self) -> None:
        if self.tier_a_components != {"crop_metrics", "psf", "geometry"}:
            raise AuditError("TIER_A_COMPONENTS_INCOMPLETE")
        self.gate.complete_tier_a()

    def _image(self, row: dict, array: np.ndarray) -> None:
        if array.dtype.kind != "f":
            raise AuditError("IMAGE_CONTRACT_INVALID", row["slot"])
        total = int(array.size)
        finite = np.isfinite(array)
        values = array[finite]
        finite_count = int(values.size)
        zero = int(np.count_nonzero(array == 0))
        basics = {"pixel_count": (total, "pixels"), "finite_count": (finite_count, "pixels"),
                  "finite_fraction": (finite_count / total, "dimensionless"),
                  "nonfinite_count": (total - finite_count, "pixels"),
                  "nonfinite_fraction": ((total - finite_count) / total, "dimensionless"),
                  "zero_count": (zero, "pixels"), "zero_fraction": (zero / total, "dimensionless")}
        for metric_id, (value, unit) in basics.items():
            self.add_value(row, "B", "IMAGE", metric_id, value, unit=unit)
        if finite_count:
            minimum, maximum = float(np.min(values)), float(np.max(values))
            quantiles = self._add_quantiles(row, "IMAGE", values, unit="nanomaggy")
            median, iqr = quantiles["q50"], quantiles["q75"] - quantiles["q25"]
            for metric_id, value in (("finite_minimum", minimum), ("finite_maximum", maximum),
                                     ("median", median), ("iqr", iqr)):
                self.add_value(row, "B", "IMAGE", metric_id, value, unit="nanomaggy")
        else:
            self._add_quantiles(row, "IMAGE", values, unit="nanomaggy")
            for metric_id in ("finite_minimum", "finite_maximum", "median", "iqr"):
                self.add_value(row, "B", "IMAGE", metric_id, None,
                               unit="nanomaggy", validity="NO_FINITE_VALUES")

    def run_tier_b(self) -> None:
        for slot in SLOTS:
            for band in BANDS:
                row = next(item for item in self.plan["crops"] if item["slot"] == slot and
                           item["product"] == "image" and item["band"] == band)
                self._image(row, self.gate.read(row))
        if self.gate.image_reads != 18 or self.gate.image_reads_before_tier_a_complete != 0:
            raise AuditError("TIER_B_ACCESS_COUNT_INVALID")

    def ordered_rows(self) -> list[dict]:
        slot_order = {slot: index for index, slot in enumerate(SLOTS)}
        band_order = {"g": 0, "r": 1, "z": 2, None: 3}
        point_order = {"P0": 0, "P1": 1, "P2": 2,
                       "CENTER": 3, "CORNER_00": 4, "CORNER_10": 5,
                       "CORNER_01": 6, "CORNER_11": 7, None: 9}
        return sorted(self.rows, key=lambda row: (
            slot_order[row["slot"]], 0 if row["tier"] == "A" else 1,
            FAMILY_ORDER[row["family"]], band_order.get(row["band"], 9),
            point_order.get(row["point_id"], 9)))


def feature_columns() -> list[str]:
    columns = ["slot", "region", "brick", "primary_geometry_role",
               "observed_primary_geometry_status"]
    for band in BANDS:
        columns.extend(f"{name}_{band}" for name in (
            "nexp_zero_fraction", "nexp_positive_fraction", "nexp_distinct_levels",
            "nexp_transition_count", "nexp_transition_fraction", "nexp_range"))
    for band in BANDS:
        columns.extend(f"{name}_{band}" for name in (
            "invvar_finite_fraction", "invvar_zero_fraction", "invvar_positive_fraction",
            "invvar_negative_fraction", "invvar_median", "invvar_iqr",
            "invvar_relative_iqr", "diagnostic_sigma_median"))
    columns.extend(("maskbits_zero_fraction", "maskbits_nprimary_fraction",
                    "maskbits_optical_any_fraction", "maskbits_wise_any_fraction"))
    columns.extend(f"maskbits_bit{bit:02d}_fraction" for bit in OPTICAL_BITS)
    columns.append("maskbits_unknown_fraction")
    for band in BANDS:
        columns.extend(f"{name}_{band}" for name in (
            "psfsize_finite_fraction", "psfsize_nonpositive_fraction", "psfsize_median",
            "psfsize_iqr", "psfsize_relative_range"))
    for band in BANDS:
        columns.extend(f"{name}_{band}" for name in (
            "psf_height", "psf_width", "psf_finite_fraction_min", "psf_raw_sum_min",
            "psf_raw_sum_max", "psf_raw_sum_range", "psf_distinct_plane_hashes",
            "psf_peak_displacement_max_pixels"))
    columns.extend(("primary_fraction", "primary_boundary_transition_count",
                    "primary_center_boundary_distance_pixels", "pixel_scale_center_arcsec",
                    "pixel_area_min_arcsec2", "pixel_area_max_arcsec2",
                    "pixel_area_relative_range_5point", "axis_ratio_max_5point",
                    "wcs_roundtrip_residual_max_pixel"))
    if len(columns) != len(set(columns)):
        raise AuditError("FEATURE_SCHEMA_DUPLICATE")
    return columns


def build_feature_matrix(engine: AuditEngine) -> tuple[list[str], list[dict]]:
    columns = feature_columns()
    rows = []
    for slot in SLOTS:
        location = next(row for row in engine.plan["locations"]["locations"] if row["slot"] == slot)
        base = {"slot": slot, "region": location["region"], "brick": location["brick"]}
        base.update(engine.features[slot])
        if set(base) != set(columns):
            missing = sorted(set(columns) - set(base))
            extra = sorted(set(base) - set(columns))
            raise AuditError("FEATURE_SCHEMA_INCOMPLETE", canonical({"missing": missing,
                                                                      "extra": extra}).decode())
        rows.append(base)
    return columns, rows


def build_contrasts(columns: list[str], matrix: list[dict], units: dict[str, str]) -> list[dict]:
    lookup = {row["slot"]: row for row in matrix}
    output = []
    for contrast_id, left_slot, right_slot in CONTRASTS:
        for feature in columns[1:]:
            left, right = lookup[left_slot][feature], lookup[right_slot][feature]
            numeric = (isinstance(left, (int, float, np.integer, np.floating)) and
                       not isinstance(left, bool) and
                       isinstance(right, (int, float, np.integer, np.floating)) and
                       not isinstance(right, bool))
            if numeric:
                difference = float(left) - float(right)
                state = "DEFINED"
            elif left is None or right is None:
                difference, state = None, "UNDEFINED"
            else:
                difference, state = None, "EQUAL" if left == right else "DIFFERENT"
            output.append({
                "contrast_id": contrast_id, "left_slot": left_slot,
                "right_slot": right_slot, "feature_id": feature,
                "left_value": _csv_scalar(left), "right_value": _csv_scalar(right),
                "signed_difference": difference, "unit": units.get(feature, "identifier"),
                "interpretation_scope": "OBSERVER_ONLY", "comparison_state": state,
            })
    return output


def interpretation_state(engine: AuditEngine) -> str:
    if (not engine.gate.tier_a_complete or engine.gate.image_reads != 18 or
            engine.psf_body_reads != 18 or engine.psf_plane_decodes != 54):
        return FAILURE
    if engine.stratum_not_expressed:
        return "STRATUM_NOT_EXPRESSED"
    if engine.witnesses:
        return "CONFOUND_VARIATION_OBSERVED"
    return "LIMITED_VARIATION_OBSERVED"


def question_evidence(state: str) -> dict:
    return {
        "Q1": {"metric_ids": ["class_0_condition_expressed",
                                "s3_optical_condition_expressed",
                                "n3_consistency_expressed",
                                "observed_primary_geometry_status"], "state": state},
        "Q2": {"metric_ids": ["level_count", "zero_fraction", "positive_fraction",
                                "total_transition_count"], "state": state},
        "Q3": {"metric_ids": ["finite_fraction", "zero_fraction", "negative_fraction",
                                "relative_iqr", "diagnostic_sigma_median"], "state": state},
        "Q4": {"metric_ids": ["bit_fraction", "optical_any_fraction",
                                "unknown_fraction"], "state": state},
        "Q5": {"metric_ids": ["median", "iqr", "relative_range"], "state": state},
        "Q6": {"metric_ids": ["plane_content_sha256", "p0_p1_p2_distinct_plane_hashes",
                                "p0_p1_p2_peak_displacement_max_pixels"], "state": state},
        "Q7": {"metric_ids": ["C05"], "state": state},
        "Q8": {"metric_ids": ["observed_primary_geometry_status",
                                "primary_boundary_transition_count"], "state": state},
        "Q9": {"metric_ids": ["class_0_condition_expressed",
                                "bands_expressing_class_0"], "state": state},
        "Q10": {"metric_ids": ["n3_variation_v", "n3_frozen_absolute_difference",
                                 "n3_consistency_expressed"], "state": state},
        "Q11": {"metric_ids": ["OBSERVER_FEATURE_MATRIX"], "state": state},
    }


def _assert_machine_output_boundary(value: Any) -> None:
    prohibited = {"source_detection", "centroid", "segmentation", "sersic",
                  "concentration", "asymmetry", "texture", "embedding", "cluster",
                  "thumbnail", "rgb"}
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in prohibited:
                raise AuditError("PROHIBITED_OUTPUT_FIELD")
            _assert_machine_output_boundary(child)
    elif isinstance(value, list):
        for child in value:
            _assert_machine_output_boundary(child)


def _promote(staging: Path, root: Path) -> None:
    if (not staging.is_dir() or staging.parent != root or
            list(root.iterdir()) != [staging]):
        raise AuditError("PROMOTION_PRECONDITION_INVALID")
    ready = root.parent / (root.name + ".PUBLISH_READY")
    if ready.exists():
        raise AuditError("PROMOTION_TARGET_EXISTS")
    os.replace(staging, ready)
    root.rmdir()
    os.replace(ready, root)


def validate_inputs(project: Path) -> dict:
    plan = _manifest_plan(Path(project), verify_payload_hashes=True)
    return {"stage_id": STAGE_ID, "state": "OBSERVER_AUDIT_INPUTS_VALIDATED",
            "slots": 6, "crop_arrays": len(plan["crops"]),
            "psf_response_mappings": len(plan["psf"]),
            "crop_arrays_opened": 0, "psf_planes_decoded": 0,
            "network_requests": 0}


def execute(project: Path, *, gate: ArrayAccessGate | None = None,
            psf_opener: Callable[[Path], Any] | None = None) -> dict:
    project = Path(project).resolve()
    root = project / STAGE_ROOT_RELATIVE
    if root.exists() or (root.parent / (root.name + ".PUBLISH_READY")).exists():
        raise AuditError("SECOND_AUDIT_EXECUTION_REFUSED")
    plan = _manifest_plan(project, verify_payload_hashes=True)
    root.mkdir(parents=True)
    staging = root / "STAGING"
    staging.mkdir()
    engine = AuditEngine(project, plan, gate=gate, psf_opener=psf_opener)
    try:
        engine.run_crop_tier_a()
        engine.run_psf()
        engine.run_geometry()
        engine.complete_tier_a()
        engine.run_tier_b()
        input_modifications = _recheck_snapshot(project, plan["snapshot"])
        state = interpretation_state(engine)
        if state == FAILURE:
            raise AuditError("AUDIT_COMPLETENESS_FAILURE")
        columns, matrix = build_feature_matrix(engine)
        contrasts = build_contrasts(columns, matrix, engine.units)
        rows = engine.ordered_rows()
        slot_path = staging / "OC3_OBSERVER_AUDIT_SLOT_METRICS.csv"
        matrix_path = staging / "OC3_OBSERVER_FEATURE_MATRIX.csv"
        contrasts_path = staging / "OC3_OBSERVER_AUDIT_CONTRASTS.csv"
        output_hashes = {
            slot_path.name: _write_csv(slot_path, METRIC_FIELDS, rows),
            matrix_path.name: _write_csv(matrix_path, columns, matrix),
            contrasts_path.name: _write_csv(contrasts_path, CONTRAST_FIELDS, contrasts),
        }
        aggregate = {
            "slots": 6, "slot_metric_rows": len(rows), "feature_matrix_rows": 6,
            "contrast_rows": len(contrasts), "tier_a_complete": True,
            "tier_b_complete": True, "tier_a_crop_reads": engine.gate.tier_a_crop_reads,
            "image_reads": engine.gate.image_reads,
            "image_reads_before_tier_a_complete": engine.gate.image_reads_before_tier_a_complete,
            "psf_response_reads": engine.psf_body_reads,
            "psf_plane_decodes": engine.psf_plane_decodes,
            "header_only_reads": engine.header_only_reads,
            "physical_psf_shape_metrics_deferred": 54,
            "input_modifications": input_modifications, "images_displayed": 0,
            "plots_produced": 0, "preprocessing_operations": 0,
            "morphology_operations": 0, "network_requests": 0,
        }
        summary = _seal({
            "schema_version": "OC3_OBSERVER_AUDIT_SUMMARY_001",
            "stage_id": STAGE_ID, "state": state,
            "input_bindings": {
                "audit_spec_sha256": SPEC_SHA256,
                "extraction_manifest_sha256": MANIFEST_SHA256,
                "extraction_manifest_seal": MANIFEST_SEAL,
                "locations_sha256": LOCATIONS_SHA256,
                "selection_sha256": SELECTION_SHA256,
            },
            "method_bindings": {
                "implementation_aggregate": implementation_hash(project),
                "quantiles": list(QUANTILES), "quantile_method": "linear",
                "nexp_adjacency": "UNDIRECTED_FOUR_NEIGHBOUR_33024",
                "n3_absolute_tolerance": N3_TOLERANCE,
            },
            "slot_intents": SLOT_INTENTS,
            "psf_normalization_decision": "PHYSICAL_PSF_SHAPE_METRICS_DEFERRED",
            "prospective_questions": QUESTIONS,
            "question_evidence": question_evidence(state),
            "interpretation_states": [FAILURE, "STRATUM_NOT_EXPRESSED",
                                      "CONFOUND_VARIATION_OBSERVED",
                                      "LIMITED_VARIATION_OBSERVED"],
            "output_hashes": output_hashes, "aggregate": aggregate,
        })
        _assert_machine_output_boundary(summary)
        summary_path = staging / "OC3_OBSERVER_AUDIT_SUMMARY.json"
        summary_hash = _write_json(summary_path, summary)
        terminal = _seal({
            "schema_version": "OC3_OBSERVER_AUDIT_TERMINAL_001",
            "stage_id": STAGE_ID, "state": SUCCESS,
            "descriptive_state": state, "summary_sha256": summary_hash,
            "summary_seal": summary["sealed"],
            "output_hashes": {**output_hashes, summary_path.name: summary_hash},
            **aggregate,
        })
        _assert_machine_output_boundary(terminal)
        terminal_path = staging / "OC3_OBSERVER_AUDIT_TERMINAL.json"
        terminal_hash = _write_json(terminal_path, terminal)
        log = _seal({
            "schema_version": "OC3_OBSERVER_AUDIT_RUN_LOG_001",
            "stage_id": STAGE_ID, "state": SUCCESS,
            "descriptive_state": state, "terminal_sha256": terminal_hash,
            "tier_a_complete": True, "tier_b_complete": True,
            "network_requests": 0,
        })
        _write_json(staging / "OC3_OBSERVER_AUDIT_RUN.log", log)
        expected_names = {
            "OC3_OBSERVER_AUDIT_SLOT_METRICS.csv", "OC3_OBSERVER_FEATURE_MATRIX.csv",
            "OC3_OBSERVER_AUDIT_CONTRASTS.csv", "OC3_OBSERVER_AUDIT_SUMMARY.json",
            "OC3_OBSERVER_AUDIT_TERMINAL.json", "OC3_OBSERVER_AUDIT_RUN.log",
        }
        if {path.name for path in staging.iterdir()} != expected_names:
            raise AuditError("OUTPUT_INVENTORY_INVALID")
        for path in staging.iterdir():
            os.chmod(path, 0o444)
        _promote(staging, root)
        return terminal
    except AuditError:
        raise
    except Exception as exc:
        raise AuditError("AUDIT_INTERNAL_FAILURE") from exc
