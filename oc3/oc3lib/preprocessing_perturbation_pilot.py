"""Closed offline preprocessing-perturbation pilot; no representation semantics."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
from pathlib import Path
import stat
import struct
from typing import Any

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

from .core import canonical, file_hash, implementation_hash


STAGE_ID = "OC3-PREPROCESSING-INVARIANCE-PERTURBATION-PILOT-001"
SUCCESS = "PREPROCESSING_INVARIANCE_PERTURBATION_PILOT_COMPLETED"
FAILURE = "PREPROCESSING_INVARIANCE_PERTURBATION_PILOT_FAILED"

SPEC_RELATIVE = Path("OC3_PREPROCESSING_INVARIANCE_PERTURBATION_PILOT_SPEC.md")
SPEC_SHA256 = "4ef5b16a9cc9de25ca194bdbf947bae8491035692fb3499356393093d919f1cd"
DECISION_RELATIVE = Path("OC3_PREPROCESSING_AND_INVARIANCE_DECISION_001.md")
DECISION_SHA256 = "de91bb4b25c002b7c4d5ee0744f6fc7e719d43ec6a969885f66d423b2ac80cf9"
CLARIFICATION_RELATIVE = Path(
    "OC3_PREPROCESSING_AND_INVARIANCE_DECISION_001_TERMINOLOGY_CLARIFICATION_001.md")
CLARIFICATION_SHA256 = "42c13760a18e1c88189a1bf02ac63546eae1d1c85296b4a57e55dfff06e30052"
MANIFEST_RELATIVE = Path("oc3/TECHNICAL_INDEX/OC3_NATIVE_EXTRACTION_MANIFEST.json")
MANIFEST_SHA256 = "f9002086f90d70eab2e0a9dcf76b6e5099f21847449053a819191b05717fc298"
MANIFEST_SEAL = "3083c3004419c5bd72eee12aeb5d2c78ad59703fc88f99fb9d7d0d613648fc75"
EXTRACTION_TERMINAL_RELATIVE = Path(
    "oc3/NATIVE_EXTRACTION/OC3-OFFLINE-NATIVE-EXTRACTION-001/"
    "OC3_NATIVE_EXTRACTION_TERMINAL.json")
EXTRACTION_TERMINAL_SHA256 = "da8abd2b6ab3c072945dab887c85d675ca032ac6c5e44fd46b79575b6ec28248"
LOCATIONS_RELATIVE = Path("oc3/TECHNICAL_INDEX/OC3_LOCATIONS.json")
LOCATIONS_SHA256 = "33d593638c074a3ff59d32d3e4c38558e8912377ea15818ca5072087007c97d1"
AUDIT_METRICS_RELATIVE = Path(
    "oc3/CONFOUND_AUDIT/OC3-OBSERVATIONAL-CONFOUND-AUDIT-001/"
    "OC3_OBSERVER_AUDIT_SLOT_METRICS.csv")
AUDIT_METRICS_SHA256 = "993d75eca71331e9fc8ea223d24f1ee5335541f0b8cec61817b3f2d2185ecf5e"
AUDIT_TERMINAL_RELATIVE = Path(
    "oc3/CONFOUND_AUDIT/OC3-OBSERVATIONAL-CONFOUND-AUDIT-001/"
    "OC3_OBSERVER_AUDIT_TERMINAL.json")
AUDIT_TERMINAL_SHA256 = "3740cac96ed138e8ab587b62bfcef8ad8222bae1c21de5730f52d61ca2cae3b0"
STAGE_ROOT_RELATIVE = Path(
    "oc3/PERTURBATION_PILOT/OC3-PREPROCESSING-INVARIANCE-PERTURBATION-PILOT-001")

SLOTS = ("S1", "S2", "S3", "N1", "N2", "N3")
BANDS = ("g", "r", "z")
PRODUCT_ORDER = (("image", "g"), ("image", "r"), ("image", "z"),
                 ("invvar", "g"), ("invvar", "r"), ("invvar", "z"),
                 ("nexp", "g"), ("nexp", "r"), ("nexp", "z"),
                 ("psfsize", "g"), ("psfsize", "r"), ("psfsize", "z"),
                 ("maskbits", None))
ARRAY_SHAPE = (129, 129)
ARRAY_HASH_PREFIX = b"OC3_ARRAY_CONTENT_V1\n"
WCS_TOLERANCE_PIXELS = 1e-6

EXECUTE_BRANCHES = (
    "B00_NATIVE_IMAGE_ONLY", "B01_MULTIPLICATIVE_FLUX_SCALE",
    "B02_ADDITIVE_OFFSET", "B03_ROBUST_GLOBAL_SCALE", "B12_ROTATION",
    "B13_REFLECTION", "B14_BAND_ABLATION")
EXECUTABLE_ENTRIES = (
    "B00_NATIVE_IMAGE_ONLY", "B01_MULTIPLICATIVE_FLUX_SCALE",
    "B02_ADDITIVE_OFFSET", "B03_ROBUST_GLOBAL_SCALE", "B12_ROTATION",
    "B13_REFLECTION", "B14_G_ONLY", "B14_R_ONLY", "B14_Z_ONLY")
METADATA_BRANCHES = ("B09_NEXP_STRATIFICATION",)
RESERVED_BRANCHES = ("B04_INVVAR_CONDITIONING", "B05_MASK_FAMILY_CONDITIONING",
                     "B07_PSFSIZE_CONDITIONING", "B10_NEXP_CONDITIONING")
BLOCKED_BRANCHES = {
    "B06_CONTROLLED_MASK_REMOVAL": "NO_EXPLICIT_MASK_REMOVAL_GATE",
    "B08_PSF_PERTURBATION_OR_MATCHING":
        "PHYSICAL_PSF_NORMALIZATION_AND_MATCHING_SEMANTICS_UNRESOLVED",
    "B11_NEXP_CONTROLLED_PERTURBATION":
        "NO_PHYSICALLY_VALID_JOINT_IMAGE_INVVAR_NEXP_PERTURBATION",
    "B15_PRIMARY_ONLY_SENSITIVITY": "NO_PROSPECTIVE_PRIMARY_ONLY_SCIENTIFIC_GATE",
}

FLOAT32_BITS = {
    "factor_0p5": "3f000000", "factor_2p0": "40000000",
    "g": "3b4ff253", "r": "3bcb54da", "z": "3c8087b7",
    "negative_g": "bb4ff253", "negative_r": "bbcb54da", "negative_z": "bc8087b7",
}

SCALAR_VARIANTS = (
    ("B01_MULTIPLICATIVE_FLUX_SCALE", "B01_FACTOR_0P5", "multiply", "factor_0p5"),
    ("B01_MULTIPLICATIVE_FLUX_SCALE", "B01_FACTOR_2P0", "multiply", "factor_2p0"),
    ("B02_ADDITIVE_OFFSET", "B02_OFFSET_NEGATIVE", "add", "negative"),
    ("B02_ADDITIVE_OFFSET", "B02_OFFSET_POSITIVE", "add", "positive"),
    ("B03_ROBUST_GLOBAL_SCALE", "B03_DIVIDE_BY_DEVELOPMENT_REFERENCE_SCALE_001",
     "divide", "scale"),
)

AFFINES = {
    "B12_ROT90_CCW": {"branch": "B12_ROTATION", "kind": "rot90", "k": 1,
                       "A": [[0, 1], [-1, 0]], "t": [0, 128]},
    "B12_ROT180": {"branch": "B12_ROTATION", "kind": "rot90", "k": 2,
                    "A": [[-1, 0], [0, -1]], "t": [128, 128]},
    "B12_ROT270_CCW": {"branch": "B12_ROTATION", "kind": "rot90", "k": 3,
                        "A": [[0, -1], [1, 0]], "t": [128, 0]},
    "B13_REFLECT_HORIZONTAL": {"branch": "B13_REFLECTION", "kind": "fliplr",
                               "A": [[-1, 0], [0, 1]], "t": [128, 0]},
    "B13_REFLECT_VERTICAL": {"branch": "B13_REFLECTION", "kind": "flipud",
                             "A": [[1, 0], [0, -1]], "t": [0, 128]},
}

BAND_SELECTIONS = {
    "B14_G_ONLY": ("g", ("r", "z")),
    "B14_R_ONLY": ("r", ("g", "z")),
    "B14_Z_ONLY": ("z", ("g", "r")),
}

METRIC_FIELDS = (
    "stage_id", "branch_id", "variant_id", "slot", "product", "band",
    "source_artifact_sha256", "source_array_content_sha256",
    "output_artifact_sha256", "output_array_content_sha256",
    "input_shape", "output_shape", "input_dtype", "output_dtype",
    "input_finite_count", "output_finite_count", "input_nonfinite_count",
    "output_nonfinite_count", "input_exact_zero_count", "output_exact_zero_count",
    "changed_element_count", "changed_element_fraction", "input_finite_minimum",
    "input_finite_maximum", "output_finite_minimum", "output_finite_maximum",
    "inverse_applicable", "inverse_variant", "round_trip_bitwise_equal_count",
    "round_trip_bitwise_equal_fraction", "round_trip_max_absolute_difference",
    "support_alignment_pass", "wcs_consistency_applicable",
    "wcs_max_residual_native_pixels", "padding_count", "interpolation_count",
    "clipping_count")

LOSS_FIELDS = (
    "branch_id", "variant_id", "execution_class", "operation",
    "mathematically_reversible", "bitwise_reversible",
    "information_intentionally_removed", "information_potentially_distorted",
    "new_artifacts_possible", "observer_variables_synchronized",
    "observer_variables_unchanged", "observer_variables_not_synchronized",
    "known_semantic_limitation", "comparison_baseline", "execution_status")

NEXP_FIELDS = ("slot", "zero_support_bands", "transition_bands", "zero_count_g",
               "zero_count_r", "zero_count_z", "transition_count_g",
               "transition_count_r", "transition_count_z", "technical_stratum",
               "source_sha256")


class PilotError(Exception):
    def __init__(self, code: str, identity: str | None = None):
        self.code = code
        self.identity = identity
        super().__init__(code)


def _seal(value: dict) -> dict:
    result = dict(value)
    result.pop("sealed", None)
    result["sealed"] = hashlib.sha256(canonical(result)).hexdigest()
    return result


def _verify_seal(value: dict, expected: str | None = None) -> None:
    observed = value.get("sealed") if isinstance(value, dict) else None
    if observed != _seal(value).get("sealed") or (expected is not None and observed != expected):
        raise PilotError("SEAL_INVALID")


def _load_canonical(path: Path) -> dict:
    try:
        raw = Path(path).read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise PilotError("CANONICAL_INPUT_INVALID", str(path)) from exc
    if not isinstance(value, dict) or raw != canonical(value) + b"\n":
        raise PilotError("CANONICAL_INPUT_INVALID", str(path))
    return value


def _exact_file(project: Path, relative: Path, expected: str) -> Path:
    path = project / relative
    if not path.is_file() or path.is_symlink() or file_hash(path) != expected:
        raise PilotError("FROZEN_INPUT_HASH_MISMATCH", str(relative))
    return path


def _readonly_file(project: Path, relative: str, expected: str) -> Path:
    path = (project / relative).resolve()
    if (not path.is_relative_to(project) or not path.is_file() or path.is_symlink() or
            file_hash(path) != expected or stat.S_IMODE(path.stat().st_mode) & 0o222):
        raise PilotError("IMMUTABLE_NATIVE_INPUT_INVALID", relative)
    return path


def _write_exclusive(path: Path, data: bytes, *, readonly: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise PilotError("OUTPUT_ALREADY_EXISTS", str(path))
    with path.open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    if readonly:
        os.chmod(path, 0o444)


def _write_json(path: Path, value: dict, *, readonly: bool = False) -> str:
    data = canonical(value) + b"\n"
    _write_exclusive(path, data, readonly=readonly)
    return hashlib.sha256(data).hexdigest()


def _csv_scalar(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, tuple, dict)):
        return canonical(value).decode("utf-8")
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    if isinstance(value, (float, np.floating)):
        observed = float(value)
        if not math.isfinite(observed):
            raise PilotError("NONFINITE_MACHINE_OUTPUT")
        return json.dumps(observed, allow_nan=False, separators=(",", ":"))
    return str(value)


def _write_csv(path: Path, fields: tuple[str, ...], rows: list[dict]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise PilotError("OUTPUT_ALREADY_EXISTS", str(path))
    with path.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="raise",
                                lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _csv_scalar(row.get(field)) for field in fields})
        handle.flush()
        os.fsync(handle.fileno())
    return file_hash(path)


def array_content_hash(array: np.ndarray) -> str:
    value = np.asarray(array)
    metadata = {"dtype": value.dtype.str, "order": "C", "shape": list(value.shape)}
    return hashlib.sha256(ARRAY_HASH_PREFIX + canonical(metadata) + b"\n" +
                          value.tobytes(order="C")).hexdigest()


def write_canonical_npy(path: Path, array: np.ndarray) -> dict:
    value = np.asarray(array)
    if (value.shape != ARRAY_SHAPE or value.dtype.hasobject or value.dtype.fields is not None or
            not value.flags.c_contiguous):
        raise PilotError("CANONICAL_ARRAY_INPUT_INVALID")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise PilotError("OUTPUT_ALREADY_EXISTS", str(path))
    try:
        with path.open("xb") as handle:
            np.lib.format.write_array(handle, value, version=(1, 0), allow_pickle=False)
            handle.flush()
            os.fsync(handle.fileno())
        raw = path.read_bytes()
        if raw[:8] != b"\x93NUMPY\x01\x00":
            raise PilotError("CANONICAL_NPY_VERSION_INVALID")
        with path.open("rb") as handle:
            reloaded = np.lib.format.read_array(handle, allow_pickle=False)
    except PilotError:
        raise
    except Exception as exc:
        raise PilotError("CANONICAL_NPY_WRITE_FAILED") from exc
    if (reloaded.shape != value.shape or reloaded.dtype.str != value.dtype.str or
            not reloaded.flags.c_contiguous or
            reloaded.tobytes(order="C") != value.tobytes(order="C")):
        raise PilotError("INDEPENDENT_OUTPUT_VERIFICATION_FAILED")
    return {"artifact_sha256": file_hash(path),
            "array_content_sha256": array_content_hash(reloaded),
            "output_shape": list(reloaded.shape), "output_dtype": reloaded.dtype.str}


def _float32_from_bits(bits: str) -> np.float32:
    return np.float32(struct.unpack(">f", bytes.fromhex(bits))[0])


def development_scales() -> dict[str, np.float32]:
    return {band: _float32_from_bits(FLOAT32_BITS[band]) for band in BANDS}


def _verify_frozen_constants() -> None:
    expected = {
        "factor_0p5": 0.5, "factor_2p0": 2.0,
        "g": 0.003173012984916568, "r": 0.006205183453857899,
        "z": 0.01568971388041973,
    }
    for key, number in expected.items():
        observed = _float32_from_bits(FLOAT32_BITS[key])
        if float(observed) != number or struct.pack(">f", observed).hex() != FLOAT32_BITS[key]:
            raise PilotError("FROZEN_FLOAT32_CONSTANT_INVALID", key)
    for band in BANDS:
        positive = _float32_from_bits(FLOAT32_BITS[band])
        negative = _float32_from_bits(FLOAT32_BITS[f"negative_{band}"])
        if not np.signbit(negative) or negative != -positive:
            raise PilotError("FROZEN_FLOAT32_CONSTANT_INVALID", f"negative_{band}")


def _authority_plan(project: Path, *, verify_payload_hashes: bool = True) -> dict:
    project = Path(project).resolve()
    authorities = {
        str(SPEC_RELATIVE): SPEC_SHA256, str(DECISION_RELATIVE): DECISION_SHA256,
        str(CLARIFICATION_RELATIVE): CLARIFICATION_SHA256,
        str(MANIFEST_RELATIVE): MANIFEST_SHA256,
        str(EXTRACTION_TERMINAL_RELATIVE): EXTRACTION_TERMINAL_SHA256,
        str(LOCATIONS_RELATIVE): LOCATIONS_SHA256,
        str(AUDIT_METRICS_RELATIVE): AUDIT_METRICS_SHA256,
        str(AUDIT_TERMINAL_RELATIVE): AUDIT_TERMINAL_SHA256,
    }
    for relative, expected in authorities.items():
        _exact_file(project, Path(relative), expected)
    manifest = _load_canonical(project / MANIFEST_RELATIVE)
    extraction_terminal = _load_canonical(project / EXTRACTION_TERMINAL_RELATIVE)
    audit_terminal = _load_canonical(project / AUDIT_TERMINAL_RELATIVE)
    _verify_seal(manifest, MANIFEST_SEAL)
    _verify_seal(audit_terminal)
    if (manifest.get("stage_id") != "OC3-OFFLINE-NATIVE-EXTRACTION-001" or
            manifest.get("state") != "NATIVE_EXTRACTION_VALIDATED" or
            extraction_terminal.get("state") != "NATIVE_EXTRACTION_VALIDATED" or
            extraction_terminal.get("manifest_sha256") != MANIFEST_SHA256 or
            extraction_terminal.get("manifest_seal") != MANIFEST_SEAL or
            audit_terminal.get("state") != "OBSERVATIONAL_CONFOUND_AUDIT_COMPLETED" or
            audit_terminal.get("output_hashes", {}).get(
                "OC3_OBSERVER_AUDIT_SLOT_METRICS.csv") != AUDIT_METRICS_SHA256):
        raise PilotError("FROZEN_AUTHORITY_STATE_INVALID")
    crops = manifest.get("crops")
    psf = manifest.get("psf_mappings")
    expected_order = [(slot, product, band) for slot in SLOTS
                      for product, band in PRODUCT_ORDER]
    if (not isinstance(crops, list) or len(crops) != 78 or
            [(row.get("slot"), row.get("product"), row.get("band"))
             for row in crops] != expected_order or
            not isinstance(psf, list) or len(psf) != 18):
        raise PilotError("NATIVE_INVENTORY_INVALID")
    snapshot = dict(authorities)
    for row in crops:
        if (row.get("output_shape") != [129, 129] or
                row.get("output_dtype") != row.get("source_dtype") or
                row.get("product") not in {item[0] for item in PRODUCT_ORDER} or
                not isinstance(row.get("artifact_sha256"), str) or
                not isinstance(row.get("array_content_sha256"), str)):
            raise PilotError("NATIVE_MANIFEST_ROW_INVALID", row.get("slot"))
        relative = row.get("artifact_path")
        if verify_payload_hashes:
            _readonly_file(project, relative, row["artifact_sha256"])
        else:
            path = (project / relative).resolve()
            if not path.is_relative_to(project) or not path.is_file() or path.is_symlink():
                raise PilotError("IMMUTABLE_NATIVE_INPUT_INVALID", relative)
        snapshot[relative] = row["artifact_sha256"]
    _verify_frozen_constants()
    return {"manifest": manifest, "crops": crops, "psf": psf,
            "snapshot": snapshot, "authorities": authorities}


def _load_native_arrays(project: Path, plan: dict) -> dict[tuple[str, str, str | None], np.ndarray]:
    arrays = {}
    for row in plan["crops"]:
        path = project / row["artifact_path"]
        try:
            raw = path.read_bytes()
            if raw[:8] != b"\x93NUMPY\x01\x00":
                raise PilotError("NATIVE_NPY_VERSION_INVALID", row["artifact_path"])
            with path.open("rb") as handle:
                value = np.lib.format.read_array(handle, allow_pickle=False)
        except PilotError:
            raise
        except Exception as exc:
            raise PilotError("NATIVE_ARRAY_DECODE_FAILED", row["artifact_path"]) from exc
        if (value.shape != ARRAY_SHAPE or value.dtype.str != row["output_dtype"] or
                value.dtype.hasobject or value.dtype.fields is not None or
                not value.flags.c_contiguous or file_hash(path) != row["artifact_sha256"] or
                array_content_hash(value) != row["array_content_sha256"]):
            raise PilotError("NATIVE_ARRAY_INTEGRITY_INVALID", row["artifact_path"])
        value.setflags(write=False)
        arrays[(row["slot"], row["product"], row["band"])] = value
    if len(arrays) != 78:
        raise PilotError("NATIVE_ARRAY_LOAD_COUNT_INVALID")
    return arrays


def _recheck_snapshot(project: Path, snapshot: dict[str, str]) -> int:
    for relative, expected in snapshot.items():
        path = project / relative
        if not path.is_file() or path.is_symlink() or file_hash(path) != expected:
            raise PilotError("NATIVE_INPUT_MODIFICATION_DETECTED", relative)
    return 0


def _element_bytes(array: np.ndarray) -> np.ndarray:
    value = np.ascontiguousarray(array)
    return np.frombuffer(value.tobytes(order="C"), dtype=np.dtype(f"V{value.dtype.itemsize}"))


def bitwise_equal_count(left: np.ndarray, right: np.ndarray) -> int:
    if left.shape != right.shape or left.dtype.str != right.dtype.str:
        return 0
    return int(np.count_nonzero(_element_bytes(left) == _element_bytes(right)))


def multiset_bytes_equal(left: np.ndarray, right: np.ndarray) -> bool:
    if left.shape != right.shape or left.dtype.str != right.dtype.str:
        return False
    return bool(np.array_equal(np.sort(_element_bytes(left)), np.sort(_element_bytes(right))))


def scalar_transform(source: np.ndarray, operation: str, scalar: np.float32) -> tuple[np.ndarray, np.ndarray]:
    value = np.asarray(source)
    if value.dtype.name != "float32" or value.shape != ARRAY_SHAPE:
        raise PilotError("SCALAR_INPUT_INVALID")
    operand = np.asarray(scalar, dtype=value.dtype)
    output = np.empty_like(value, order="C")
    if operation == "multiply":
        np.multiply(value, operand, out=output, casting="same_kind")
        inverse_operand = np.asarray(np.float32(1.0) / np.float32(scalar), dtype=value.dtype)
        round_trip = np.empty_like(value, order="C")
        np.multiply(output, inverse_operand, out=round_trip, casting="same_kind")
    elif operation == "add":
        np.add(value, operand, out=output, casting="same_kind")
        round_trip = np.empty_like(value, order="C")
        np.subtract(output, operand, out=round_trip, casting="same_kind")
    elif operation == "divide":
        np.divide(value, operand, out=output, casting="same_kind")
        round_trip = np.empty_like(value, order="C")
        np.multiply(output, operand, out=round_trip, casting="same_kind")
    else:
        raise PilotError("SCALAR_OPERATION_INVALID", operation)
    if output.dtype.str != value.dtype.str or round_trip.dtype.str != value.dtype.str:
        raise PilotError("SCALAR_DTYPE_CHANGED")
    finite_input = np.isfinite(value)
    if np.any(finite_input & ~np.isfinite(output)):
        raise PilotError("FINITE_INPUT_BECAME_NONFINITE")
    return output, round_trip


def affine_transform(source: np.ndarray, variant: str) -> tuple[np.ndarray, np.ndarray]:
    if variant not in AFFINES:
        raise PilotError("AFFINE_VARIANT_INVALID", variant)
    config = AFFINES[variant]
    value = np.asarray(source)
    if value.shape != ARRAY_SHAPE:
        raise PilotError("AFFINE_INPUT_INVALID")
    if config["kind"] == "rot90":
        output = np.ascontiguousarray(np.rot90(value, k=config["k"]))
        inverse = np.ascontiguousarray(np.rot90(output, k=(4 - config["k"]) % 4))
    elif config["kind"] == "fliplr":
        output = np.ascontiguousarray(np.fliplr(value))
        inverse = np.ascontiguousarray(np.fliplr(output))
    else:
        output = np.ascontiguousarray(np.flipud(value))
        inverse = np.ascontiguousarray(np.flipud(output))
    if (output.dtype.str != value.dtype.str or not multiset_bytes_equal(value, output) or
            bitwise_equal_count(value, inverse) != value.size):
        raise PilotError("AFFINE_BYTE_PRESERVATION_FAILED", variant)
    return output, inverse


def _finite_extrema(array: np.ndarray) -> tuple[float | int | None, float | int | None]:
    value = np.asarray(array)
    finite = value[np.isfinite(value)]
    if finite.size == 0:
        return None, None
    return _json_number(finite.min()), _json_number(finite.max())


def _json_number(value: np.generic | int | float) -> int | float:
    if np.issubdtype(np.asarray(value).dtype, np.integer):
        return int(value)
    observed = float(value)
    if not math.isfinite(observed):
        raise PilotError("NONFINITE_MACHINE_OUTPUT")
    return observed


def technical_metric(row: dict, branch: str, variant: str, source: np.ndarray,
                     output: np.ndarray, output_hashes: dict, round_trip: np.ndarray,
                     *, inverse_variant: str, wcs_residual: float | None = None) -> dict:
    source_finite = np.isfinite(source)
    output_finite = np.isfinite(output)
    changed = source.size - bitwise_equal_count(source, output)
    roundtrip_equal = bitwise_equal_count(source, round_trip)
    comparable = source_finite & np.isfinite(round_trip)
    maximum_difference = (float(np.max(np.abs(source[comparable].astype(np.float64) -
                                             round_trip[comparable].astype(np.float64))))
                          if np.any(comparable) else None)
    source_min, source_max = _finite_extrema(source)
    output_min, output_max = _finite_extrema(output)
    return {
        "stage_id": STAGE_ID, "branch_id": branch, "variant_id": variant,
        "slot": row["slot"], "product": row["product"], "band": row["band"],
        "source_artifact_sha256": row["artifact_sha256"],
        "source_array_content_sha256": row["array_content_sha256"],
        "output_artifact_sha256": output_hashes["artifact_sha256"],
        "output_array_content_sha256": output_hashes["array_content_sha256"],
        "input_shape": list(source.shape), "output_shape": list(output.shape),
        "input_dtype": source.dtype.str, "output_dtype": output.dtype.str,
        "input_finite_count": int(np.count_nonzero(source_finite)),
        "output_finite_count": int(np.count_nonzero(output_finite)),
        "input_nonfinite_count": int(source.size - np.count_nonzero(source_finite)),
        "output_nonfinite_count": int(output.size - np.count_nonzero(output_finite)),
        "input_exact_zero_count": int(np.count_nonzero(source == 0)),
        "output_exact_zero_count": int(np.count_nonzero(output == 0)),
        "changed_element_count": changed,
        "changed_element_fraction": float(changed / source.size),
        "input_finite_minimum": source_min, "input_finite_maximum": source_max,
        "output_finite_minimum": output_min, "output_finite_maximum": output_max,
        "inverse_applicable": True, "inverse_variant": inverse_variant,
        "round_trip_bitwise_equal_count": roundtrip_equal,
        "round_trip_bitwise_equal_fraction": float(roundtrip_equal / source.size),
        "round_trip_max_absolute_difference": maximum_difference,
        "support_alignment_pass": True,
        "wcs_consistency_applicable": wcs_residual is not None,
        "wcs_max_residual_native_pixels": wcs_residual,
        "padding_count": 0, "interpolation_count": 0, "clipping_count": 0,
    }


def _wcs_from_cards(cards: list[list[Any]]) -> WCS:
    header = fits.Header()
    try:
        for key, value in cards:
            header[key] = value
        return WCS(header, relax=True)
    except Exception as exc:
        raise PilotError("NATIVE_WCS_INVALID") from exc


def validate_wcs_affine(row: dict, variant: str) -> dict:
    config = AFFINES[variant]
    provenance = row.get("wcs_provenance", {})
    cards = provenance.get("translated_wcs_cards")
    native_hash = provenance.get("translated_wcs_sha256")
    if (not isinstance(cards, list) or not isinstance(native_hash, str) or
            hashlib.sha256(canonical(cards)).hexdigest() != native_hash):
        raise PilotError("NATIVE_WCS_BINDING_INVALID", row.get("slot"))
    wcs = _wcs_from_cards(cards)
    if wcs.pixel_n_dim != 2 or wcs.world_n_dim != 2:
        raise PilotError("NATIVE_WCS_DIMENSION_INVALID", row.get("slot"))
    points = np.asarray([[64.0, 64.0], [0.0, 0.0], [128.0, 0.0], [0.0, 128.0],
                         [128.0, 128.0], [64.0, 0.0], [128.0, 64.0],
                         [64.0, 128.0], [0.0, 64.0]], dtype=np.float64)
    matrix = np.asarray(config["A"], dtype=np.float64)
    offset = np.asarray(config["t"], dtype=np.float64)
    native_points = (np.linalg.inv(matrix) @ (points - offset).T).T
    try:
        world = wcs.all_pix2world(native_points, 0)
        native_roundtrip = wcs.all_world2pix(world, 0)
    except Exception as exc:
        raise PilotError("WCS_AFFINE_EVALUATION_FAILED", row.get("slot")) from exc
    output_roundtrip = (matrix @ native_roundtrip.T).T + offset
    residual = float(np.max(np.abs(output_roundtrip - points)))
    if not math.isfinite(residual) or residual > WCS_TOLERANCE_PIXELS:
        raise PilotError("WCS_AFFINE_RESIDUAL_EXCEEDED", row.get("slot"))
    return {
        "variant_id": variant, "slot": row["slot"], "A": config["A"],
        "t": config["t"], "native_wcs_sha256": native_hash,
        "test_points_xy": points.astype(int).tolist(),
        "max_residual_native_pixels": residual,
        "residual_threshold_native_pixels": WCS_TOLERANCE_PIXELS,
        "padding_count": 0, "interpolation_count": 0,
        "provider_psf_response_transform": "NOT_EXECUTED",
        "psf_provenance_retained": True,
        "known_semantic_limitation":
            "TRANSFORMED_WINDOW_HAS_NO_TRANSFORMED_PROVIDER_PSF_RESPONSE",
    }


def _load_audit_rows(project: Path) -> list[dict]:
    path = project / AUDIT_METRICS_RELATIVE
    if file_hash(path) != AUDIT_METRICS_SHA256:
        raise PilotError("AUDIT_METRICS_HASH_MISMATCH")
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
    except OSError as exc:
        raise PilotError("AUDIT_METRICS_READ_FAILED") from exc
    return rows


def build_nexp_strata(project: Path) -> list[dict]:
    rows = _load_audit_rows(project)
    output = []
    expected = {"S1": "Z0_TALL", "S2": "Z0_TALL", "S3": "Z0_TSOME",
                "N1": "ZANY_TALL", "N2": "ZANY_TALL", "N3": "Z0_TSOME"}
    for slot in SLOTS:
        zero_counts = {}
        transitions = {}
        for band in BANDS:
            zero = [row for row in rows if row.get("slot") == slot and
                    row.get("tier") == "A" and row.get("family") == "NEXP" and
                    row.get("band") == band and row.get("metric_id") == "zero_count"]
            transition = [row for row in rows if row.get("slot") == slot and
                          row.get("tier") == "A" and row.get("family") == "NEXP" and
                          row.get("band") == band and
                          row.get("metric_id") == "total_transition_count"]
            if len(zero) != 1 or len(transition) != 1:
                raise PilotError("NEXP_FROZEN_ROW_INVALID", f"{slot}:{band}")
            zero_counts[band] = int(zero[0]["value_int"])
            transitions[band] = int(transition[0]["value_int"])
        zero_bands = [band for band in BANDS if zero_counts[band] > 0]
        transition_bands = [band for band in BANDS if transitions[band] > 0]
        zero_class = "ZANY" if zero_bands else "Z0"
        transition_class = ("TALL" if len(transition_bands) == 3 else
                            "TSOME" if transition_bands else "T0")
        label = f"{zero_class}_{transition_class}"
        if label != expected[slot]:
            raise PilotError("NEXP_FROZEN_STRATUM_MISMATCH", slot)
        output.append({
            "slot": slot, "zero_support_bands": zero_bands,
            "transition_bands": transition_bands,
            **{f"zero_count_{band}": zero_counts[band] for band in BANDS},
            **{f"transition_count_{band}": transitions[band] for band in BANDS},
            "technical_stratum": label, "source_sha256": AUDIT_METRICS_SHA256,
        })
    return output


def _row_index(crops: list[dict]) -> dict[tuple[str, str, str | None], dict]:
    return {(row["slot"], row["product"], row["band"]): row for row in crops}


def _filename(row: dict) -> str:
    return (f"{row['product']}-{row['band']}.npy" if row["band"] is not None
            else "maskbits-optical.npy")


def _scalar_for(variant: str, band: str) -> np.float32:
    if variant == "B01_FACTOR_0P5":
        return _float32_from_bits(FLOAT32_BITS["factor_0p5"])
    if variant == "B01_FACTOR_2P0":
        return _float32_from_bits(FLOAT32_BITS["factor_2p0"])
    if variant == "B02_OFFSET_NEGATIVE":
        return _float32_from_bits(FLOAT32_BITS[f"negative_{band}"])
    return development_scales()[band]


def _loss_row(branch: str, variant: str, execution_class: str, operation: str,
              *, mathematical: bool | str, bitwise: bool | str,
              removed: str, distorted: str, artifacts: str, synchronized: str,
              unchanged: str, unsynchronized: str, limitation: str,
              status: str) -> dict:
    return {
        "branch_id": branch, "variant_id": variant, "execution_class": execution_class,
        "operation": operation, "mathematically_reversible": mathematical,
        "bitwise_reversible": bitwise, "information_intentionally_removed": removed,
        "information_potentially_distorted": distorted,
        "new_artifacts_possible": artifacts,
        "observer_variables_synchronized": synchronized,
        "observer_variables_unchanged": unchanged,
        "observer_variables_not_synchronized": unsynchronized,
        "known_semantic_limitation": limitation,
        "comparison_baseline": "B00_NATIVE_IMAGE_ONLY", "execution_status": status,
    }


def build_information_loss_register(metric_rows: list[dict] | None = None) -> list[dict]:
    rows = [_loss_row(
        "B00_NATIVE_IMAGE_ONLY", "B00_NATIVE_IMAGE_ONLY", "EXECUTE_TRANSFORMATION_NOW",
        "REFERENCE_ONLY", mathematical=True, bitwise=True, removed="NONE",
        distorted="NONE", artifacts="NONE", synchronized="NONE_REQUIRED",
        unchanged="ALL_NATIVE_IMAGE_AND_OBSERVER_METADATA", unsynchronized="NONE",
        limitation="TECHNICAL_REFERENCE_ONLY", status="REFERENCE_VALIDATED")]
    for branch, variant, operation, _ in SCALAR_VARIANTS:
        if branch == "B01_MULTIPLICATIVE_FLUX_SCALE":
            removed, distorted = "ABSOLUTE_FLUX_SCALE", "FLOAT32_RANGE_AND_ROUNDING"
        elif branch == "B02_ADDITIVE_OFFSET":
            removed, distorted = "NATIVE_ZERO_LEVEL", "FLOAT32_ROUNDING_AND_ZERO_MEMBERSHIP"
        else:
            removed, distorted = ("NATIVE_UNIT_MAGNITUDE_RELATIVE_TO_DEVELOPMENT_SCALE",
                                  "FLOAT32_DIVISION_AND_ROUND_TRIP")
        relevant = ([row for row in metric_rows or [] if row["variant_id"] == variant]
                    if metric_rows is not None else [])
        bitwise: bool | str = (all(row["round_trip_bitwise_equal_count"] == 129 * 129
                                   for row in relevant)
                                if relevant else "MEASURE_ON_EXECUTION")
        rows.append(_loss_row(
            branch, variant, "EXECUTE_TRANSFORMATION_NOW", operation.upper(),
            mathematical=True, bitwise=bitwise, removed=removed, distorted=distorted,
            artifacts="NUMERICAL_ROUNDING", synchronized="IMAGE_G_R_Z_BY_RULE",
            unchanged="INVVAR_NEXP_MASKBITS_PSFSIZE_PSF_WCS",
            unsynchronized="NONE", limitation="DEVELOPMENT_STRESS_TEST_ONLY",
            status="EXECUTED"))
    for variant, config in AFFINES.items():
        rows.append(_loss_row(
            config["branch"], variant, "EXECUTE_TRANSFORMATION_NOW",
            "INTEGER_LATTICE_PERMUTATION", mathematical=True, bitwise=True,
            removed="NONE", distorted="NONE", artifacts="NONE",
            synchronized="IMAGE_INVVAR_NEXP_MASKBITS_PSFSIZE_WCS_AFFINE",
            unchanged="PROVIDER_PSF_PROVENANCE", unsynchronized="PROVIDER_PSF_RESPONSE",
            limitation="TRANSFORMED_WINDOW_HAS_NO_TRANSFORMED_PROVIDER_PSF_RESPONSE",
            status="EXECUTED"))
    for variant, (retained, omitted) in BAND_SELECTIONS.items():
        rows.append(_loss_row(
            "B14_BAND_ABLATION", variant, "EXECUTE_TRANSFORMATION_NOW",
            "REFERENCE_SELECTION", mathematical=False, bitwise=False,
            removed=f"BANDS_{'_'.join(omitted).upper()}_AND_CROSS_BAND_INFORMATION",
            distorted="NONE_IN_RETAINED_BAND", artifacts="NONE",
            synchronized=f"OBSERVER_METADATA_BAND_{retained.upper()}",
            unchanged="ALL_NATIVE_ARTIFACTS", unsynchronized="OMITTED_BAND_INPUTS",
            limitation="CHANNEL_ABLATION_NOT_OBSERVATIONAL_EQUIVALENCE", status="EXECUTED"))
    rows.append(_loss_row(
        "B09_NEXP_STRATIFICATION", "B09_NEXP_STRATIFICATION", "METADATA_ONLY_NOW",
        "METADATA_MAPPING_ONLY", mathematical="NOT_APPLICABLE",
        bitwise="NOT_APPLICABLE", removed="NONE",
        distorted="NONE", artifacts="NONE", synchronized="NEXP_AUDIT_ROWS",
        unchanged="ALL_NATIVE_ARTIFACTS", unsynchronized="NONE",
        limitation="SIX_WINDOW_DEVELOPMENT_MAPPING_NO_STATISTICAL_INFERENCE",
        status="METADATA_ONLY_COMPLETED"))
    for branch in RESERVED_BRANCHES:
        rows.append(_loss_row(
            branch, branch, "RESERVED_FOR_REPRESENTATION_STAGE", "NOT_EXECUTED",
            mathematical="NOT_APPLICABLE", bitwise="NOT_APPLICABLE",
            removed="NONE", distorted="NONE",
            artifacts="NONE", synchronized="NONE", unchanged="ALL_NATIVE_ARTIFACTS",
            unsynchronized="NONE", limitation="MODEL_CONDITIONING_ARCHITECTURE_NOT_DEFINED",
            status="RESERVED_FOR_REPRESENTATION_STAGE"))
    for branch, blocker in BLOCKED_BRANCHES.items():
        rows.append(_loss_row(
            branch, branch, "BLOCKED_BY_FROZEN_DEFERRAL_OR_GATE", "NOT_EXECUTED",
            mathematical="NOT_APPLICABLE", bitwise="NOT_APPLICABLE",
            removed="NONE", distorted="NONE",
            artifacts="NONE", synchronized="NONE", unchanged="ALL_NATIVE_ARTIFACTS",
            unsynchronized="NONE", limitation=blocker,
            status="BLOCKED_BY_FROZEN_DEFERRAL_OR_GATE"))
    if len(rows) != 23:
        raise PilotError("INFORMATION_LOSS_ROW_COUNT_INVALID")
    return rows


def _side_information(crops: list[dict], psf: list[dict]) -> dict:
    def refs(product: str) -> list[dict]:
        return [{"slot": row["slot"], "band": row["band"],
                 "artifact_path": row["artifact_path"],
                 "artifact_sha256": row["artifact_sha256"],
                 "array_content_sha256": row["array_content_sha256"]}
                for row in crops if row["product"] == product]
    result = {
        "B04_INVVAR_CONDITIONING": refs("invvar"),
        "B05_MASK_FAMILY_CONDITIONING": {
            "references": refs("maskbits"),
            "families": {"NPRIMARY": [0], "OPTICAL": [1, 2, 3, 4, 5, 6, 7, 10, 11, 12, 13],
                         "WISE": [8, 9], "UNKNOWN": "BITS_OUTSIDE_0_TO_13"}},
        "B07_PSFSIZE_CONDITIONING": {"references": refs("psfsize"),
                                      "psf_provenance": psf},
        "B10_NEXP_CONDITIONING": refs("nexp"),
    }
    if (len(result["B04_INVVAR_CONDITIONING"]) != 18 or
            len(result["B05_MASK_FAMILY_CONDITIONING"]["references"]) != 6 or
            len(result["B07_PSFSIZE_CONDITIONING"]["references"]) != 18 or
            len(result["B07_PSFSIZE_CONDITIONING"]["psf_provenance"]) != 18 or
            len(result["B10_NEXP_CONDITIONING"]) != 18):
        raise PilotError("RESERVED_SIDE_INFORMATION_INVALID")
    return result


def _branch_family_classes() -> list[dict]:
    rows = ([{"branch_id": branch, "execution_class": "EXECUTE_TRANSFORMATION_NOW"}
             for branch in EXECUTE_BRANCHES] +
            [{"branch_id": branch, "execution_class": "METADATA_ONLY_NOW"}
             for branch in METADATA_BRANCHES] +
            [{"branch_id": branch, "execution_class": "RESERVED_FOR_REPRESENTATION_STAGE"}
             for branch in RESERVED_BRANCHES] +
            [{"branch_id": branch, "execution_class": "BLOCKED_BY_FROZEN_DEFERRAL_OR_GATE",
              "blocker": blocker} for branch, blocker in BLOCKED_BRANCHES.items()])
    if len(rows) != 16 or len({row["branch_id"] for row in rows}) != 16:
        raise PilotError("BRANCH_CLASSIFICATION_INVALID")
    return rows


def _branch_classes() -> list[dict]:
    rows = ([{"branch_id": branch, "execution_class": "EXECUTE_TRANSFORMATION_NOW"}
             for branch in EXECUTABLE_ENTRIES] +
            [{"branch_id": branch, "execution_class": "METADATA_ONLY_NOW"}
             for branch in METADATA_BRANCHES] +
            [{"branch_id": branch, "execution_class": "RESERVED_FOR_REPRESENTATION_STAGE"}
             for branch in RESERVED_BRANCHES] +
            [{"branch_id": branch, "execution_class": "BLOCKED_BY_FROZEN_DEFERRAL_OR_GATE",
              "blocker": blocker} for branch, blocker in BLOCKED_BRANCHES.items()])
    if len(rows) != 18 or len({row["branch_id"] for row in rows}) != 18:
        raise PilotError("BRANCH_CLASSIFICATION_INVALID")
    return rows


def _readonly_tree(root: Path) -> None:
    for path in sorted(root.rglob("*"), reverse=True):
        if path.is_file():
            os.chmod(path, 0o444)
        elif path.is_dir():
            os.chmod(path, 0o555)


def _promote(staging: Path, root: Path) -> None:
    if not staging.is_dir() or staging.parent != root or list(root.iterdir()) != [staging]:
        raise PilotError("ATOMIC_PROMOTION_PRECONDITION_FAILED")
    ready = root.parent / (root.name + ".PUBLISH_READY")
    if ready.exists():
        raise PilotError("ATOMIC_PROMOTION_TARGET_EXISTS")
    os.replace(staging, ready)
    root.rmdir()
    os.replace(ready, root)


def validate_inputs(project: Path) -> dict:
    plan = _authority_plan(Path(project), verify_payload_hashes=True)
    return {"stage_id": STAGE_ID, "state": "PERTURBATION_PILOT_INPUTS_VALIDATED",
            "technical_development_bricks": 2, "observational_windows": 6,
            "astronomical_objects_defined": 0, "native_artifacts": len(plan["crops"]),
            "psf_provenance_records": len(plan["psf"]), "array_values_decoded": 0,
            "transformations_executed": 0, "network_requests": 0,
            "model_operations": 0, "morphology_operations": 0}


def execute(project: Path, *, plan: dict | None = None) -> dict:
    project = Path(project).resolve()
    root = project / STAGE_ROOT_RELATIVE
    ready = root.parent / (root.name + ".PUBLISH_READY")
    if root.exists() or ready.exists():
        raise PilotError("SECOND_OR_PARTIAL_EXECUTION_REFUSED")
    plan = plan or _authority_plan(project, verify_payload_hashes=True)
    arrays = _load_native_arrays(project, plan)
    index = _row_index(plan["crops"])
    nexp_rows = build_nexp_strata(project)
    root.mkdir(parents=True)
    staging = root / "STAGING"
    staging.mkdir()
    transformed_rows = []
    metric_rows = []
    wcs_rows = []
    current = None
    try:
        b00 = []
        for slot in SLOTS:
            for band in BANDS:
                row = index[(slot, "image", band)]
                b00.append({key: row[key] for key in
                            ("slot", "region", "brick", "band", "artifact_path",
                             "artifact_sha256", "array_content_sha256", "output_dtype",
                             "output_shape", "wcs_provenance")})
        if len(b00) != 18:
            raise PilotError("B00_REFERENCE_COUNT_INVALID")

        for branch, variant, operation, _ in SCALAR_VARIANTS:
            for slot in SLOTS:
                for band in BANDS:
                    current = f"{variant}:{slot}:{band}"
                    row = index[(slot, "image", band)]
                    source = arrays[(slot, "image", band)]
                    scalar = _scalar_for(variant, band)
                    output, round_trip = scalar_transform(source, operation, scalar)
                    target = staging / "TRANSFORMED" / variant / slot / _filename(row)
                    hashes = write_canonical_npy(target, output)
                    metric_rows.append(technical_metric(
                        row, branch, variant, source, output, hashes, round_trip,
                        inverse_variant={
                            "B01_FACTOR_0P5": "B01_FACTOR_2P0",
                            "B01_FACTOR_2P0": "B01_FACTOR_0P5",
                            "B02_OFFSET_NEGATIVE": "SUBTRACT_OPERATIONAL_OFFSET",
                            "B02_OFFSET_POSITIVE": "SUBTRACT_OPERATIONAL_OFFSET",
                            "B03_DIVIDE_BY_DEVELOPMENT_REFERENCE_SCALE_001":
                                "MULTIPLY_BY_DEVELOPMENT_REFERENCE_SCALE_001",
                        }[variant]))
                    transformed_rows.append({
                        "branch_id": branch, "variant_id": variant, "slot": slot,
                        "product": "image", "band": band,
                        "source_artifact_path": row["artifact_path"],
                        "source_artifact_sha256": row["artifact_sha256"],
                        "source_array_content_sha256": row["array_content_sha256"],
                        "output_artifact_path": str(target.relative_to(staging)), **hashes,
                        "operational_scalar": float(scalar),
                        "operational_scalar_binary32": struct.pack(">f", scalar).hex(),
                        "multiset_byte_preserved": None,
                    })

        for variant, config in AFFINES.items():
            for slot in SLOTS:
                current = f"{variant}:{slot}"
                slot_rows = [index[(slot, product, band)] for product, band in PRODUCT_ORDER]
                wcs_hashes = {row["wcs_provenance"]["translated_wcs_sha256"]
                              for row in slot_rows}
                if len(wcs_hashes) != 1:
                    raise PilotError("SLOT_WCS_NOT_SYNCHRONIZED", slot)
                wcs_result = validate_wcs_affine(index[(slot, "image", "g")], variant)
                wcs_rows.append(wcs_result)
                for row in slot_rows:
                    source = arrays[(slot, row["product"], row["band"])]
                    output, round_trip = affine_transform(source, variant)
                    target = staging / "TRANSFORMED" / variant / slot / _filename(row)
                    hashes = write_canonical_npy(target, output)
                    metric_rows.append(technical_metric(
                        row, config["branch"], variant, source, output, hashes, round_trip,
                        inverse_variant={"B12_ROT90_CCW": "B12_ROT270_CCW",
                                         "B12_ROT270_CCW": "B12_ROT90_CCW"}.get(
                                             variant, variant),
                        wcs_residual=wcs_result["max_residual_native_pixels"]))
                    transformed_rows.append({
                        "branch_id": config["branch"], "variant_id": variant,
                        "slot": slot, "product": row["product"], "band": row["band"],
                        "source_artifact_path": row["artifact_path"],
                        "source_artifact_sha256": row["artifact_sha256"],
                        "source_array_content_sha256": row["array_content_sha256"],
                        "output_artifact_path": str(target.relative_to(staging)), **hashes,
                        "A": config["A"], "t": config["t"],
                        "multiset_byte_preserved": True,
                    })

        if len(transformed_rows) != 480 or len(metric_rows) != 480:
            raise PilotError("TRANSFORMED_ARRAY_INVENTORY_INVALID")
        if len(list((staging / "TRANSFORMED").glob("*/*/*.npy"))) != 480:
            raise PilotError("TRANSFORMED_ARRAY_FILE_COUNT_INVALID")

        band_selections = []
        for variant, (retained, omitted) in BAND_SELECTIONS.items():
            for slot in SLOTS:
                selected = [index[(slot, product, retained)] for product in
                            ("image", "invvar", "nexp", "psfsize")]
                mask = index[(slot, "maskbits", None)]
                band_selections.append({
                    "branch_id": "B14_BAND_ABLATION", "variant_id": variant,
                    "slot": slot, "retained_band": retained, "omitted_bands": list(omitted),
                    "information_intentionally_unavailable":
                        f"BANDS_{'_'.join(omitted).upper()}_AND_CROSS_BAND_INFORMATION",
                    "observer_metadata_retained_for_selected_band":
                        ["INVVAR", "NEXP", "PSFSIZE", "MASKBITS", "PSF_PROVENANCE", "WCS"],
                    "source_hashes": [{"product": row["product"],
                                       "artifact_sha256": row["artifact_sha256"],
                                       "array_content_sha256": row["array_content_sha256"]}
                                      for row in selected + [mask]],
                    "pixel_arrays_created": 0,
                })
        if len(band_selections) != 18:
            raise PilotError("B14_REFERENCE_COUNT_INVALID")

        loss_rows = build_information_loss_register(metric_rows)
        metrics_path = staging / "OC3_PERTURBATION_TECHNICAL_EFFECT_METRICS.csv"
        loss_path = staging / "OC3_PERTURBATION_INFORMATION_LOSS_REGISTER.csv"
        nexp_path = staging / "OC3_NEXP_TECHNICAL_STRATA.csv"
        tabular_hashes = {
            metrics_path.name: _write_csv(metrics_path, METRIC_FIELDS, metric_rows),
            loss_path.name: _write_csv(loss_path, LOSS_FIELDS, loss_rows),
            nexp_path.name: _write_csv(nexp_path, NEXP_FIELDS, nexp_rows),
        }
        input_modifications = _recheck_snapshot(project, plan["snapshot"])
        aggregate = {
            "technical_development_bricks": 2, "observational_windows": 6,
            "astronomical_objects_defined": 0, "native_artifacts_validated": 78,
            "b00_image_references": 18, "executable_branch_count": 9,
            "executable_branch_family_count": 7,
            "executable_variant_count_including_b00": 14,
            "metadata_only_branch_count": 1, "reserved_branch_count": 4,
            "blocked_branch_count": 4, "transformed_arrays": 480,
            "technical_metric_rows": 480, "information_loss_rows": 23,
            "nexp_mapping_rows": 6, "band_selection_rows": 18,
            "wcs_adapter_rows": 30, "input_modifications": input_modifications,
            "padding_count": 0, "interpolation_count": 0, "clipping_count": 0,
            "provider_psf_transforms": 0, "network_requests": 0,
            "model_operations": 0, "encoder_operations": 0, "embedding_operations": 0,
            "clustering_operations": 0, "morphology_operations": 0,
            "label_accesses": 0, "images_displayed": 0, "plots_produced": 0,
        }
        manifest = _seal({
            "schema_version": "OC3_PERTURBATION_BRANCH_MANIFEST_001",
            "stage_id": STAGE_ID, "state": SUCCESS,
            "terminology": {"technical_development_bricks": 2,
                            "observational_windows": 6,
                            "astronomical_objects_defined": 0},
            "authority_bindings": {**plan["authorities"],
                                   "native_manifest_seal": MANIFEST_SEAL},
            "method_bindings": {
                "implementation_aggregate": implementation_hash(project),
                "numpy_version": np.__version__,
                "array_artifact": "NUMPY_NPY_V1_0_UNCOMPRESSED",
                "array_content_hash": "OC3_ARRAY_CONTENT_V1",
                "float32_constants": FLOAT32_BITS,
                "development_scale_labels":
                    ["DEVELOPMENT_ONLY_SCALE",
                     "NOT_AUTHORIZED_AS_FUTURE_TRAINING_SCALE"],
                "wcs_residual_threshold_native_pixels": WCS_TOLERANCE_PIXELS,
            },
            "branch_classes": _branch_classes(),
            "branch_family_classes": _branch_family_classes(), "b00_references": b00,
            "transformed_arrays": transformed_rows, "wcs_adapters": wcs_rows,
            "band_selections": band_selections,
            "nexp_strata": nexp_rows,
            "reserved_side_information": _side_information(plan["crops"], plan["psf"]),
            "output_hashes": tabular_hashes, "aggregate": aggregate,
        })
        manifest_path = staging / "OC3_PERTURBATION_BRANCH_MANIFEST.json"
        manifest_hash = _write_json(manifest_path, manifest)
        summary = _seal({
            "schema_version": "OC3_PERTURBATION_PILOT_SUMMARY_001",
            "stage_id": STAGE_ID, "state": SUCCESS,
            "branch_manifest_sha256": manifest_hash,
            "branch_manifest_seal": manifest["sealed"],
            "output_hashes": {**tabular_hashes, manifest_path.name: manifest_hash},
            "aggregate": aggregate,
            "scientific_selection_performed": False,
            "representation_learning_authorized": False,
        })
        summary_path = staging / "OC3_PERTURBATION_PILOT_SUMMARY.json"
        summary_hash = _write_json(summary_path, summary)
        terminal = _seal({
            "schema_version": "OC3_PERTURBATION_PILOT_TERMINAL_001",
            "stage_id": STAGE_ID, "state": SUCCESS,
            "summary_sha256": summary_hash, "summary_seal": summary["sealed"],
            "branch_manifest_sha256": manifest_hash,
            "branch_manifest_seal": manifest["sealed"], **aggregate,
        })
        terminal_path = staging / "OC3_PERTURBATION_PILOT_TERMINAL.json"
        terminal_hash = _write_json(terminal_path, terminal)
        log = _seal({
            "schema_version": "OC3_PERTURBATION_PILOT_RUN_LOG_001",
            "stage_id": STAGE_ID, "state": SUCCESS,
            "terminal_sha256": terminal_hash, "transformed_arrays": 480,
            "network_requests": 0, "model_operations": 0,
            "morphology_operations": 0,
        })
        _write_json(staging / "OC3_PERTURBATION_PILOT_RUN.log", log)
        expected_top = {"TRANSFORMED", "OC3_PERTURBATION_BRANCH_MANIFEST.json",
                        "OC3_PERTURBATION_TECHNICAL_EFFECT_METRICS.csv",
                        "OC3_PERTURBATION_INFORMATION_LOSS_REGISTER.csv",
                        "OC3_NEXP_TECHNICAL_STRATA.csv",
                        "OC3_PERTURBATION_PILOT_SUMMARY.json",
                        "OC3_PERTURBATION_PILOT_TERMINAL.json",
                        "OC3_PERTURBATION_PILOT_RUN.log"}
        if {path.name for path in staging.iterdir()} != expected_top:
            raise PilotError("OUTPUT_INVENTORY_INVALID")
        _readonly_tree(staging)
        os.chmod(staging, 0o755)
        _promote(staging, root)
        return terminal
    except Exception as exc:
        failure = _seal({
            "schema_version": "OC3_PERTURBATION_PILOT_TERMINAL_001",
            "stage_id": STAGE_ID, "state": FAILURE,
            "error": getattr(exc, "code", "PERTURBATION_PILOT_INTERNAL_FAILURE"),
            "identity": current, "successful_subset_published": False,
            "network_requests": 0, "model_operations": 0,
            "morphology_operations": 0,
        })
        failure_path = root / "OC3_PERTURBATION_PILOT_TERMINAL.json"
        if not failure_path.exists():
            _write_json(failure_path, failure, readonly=True)
        if isinstance(exc, PilotError):
            raise
        raise PilotError("PERTURBATION_PILOT_INTERNAL_FAILURE", current) from exc
