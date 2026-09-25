"""Columnar, memory-bounded semantics for supervised pilot-frame schema recovery."""
from __future__ import annotations
import csv
import hashlib
import math
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import numpy as np

from .core import InputError, IntegrityError
from .provider_physical_contracts import (
    PRODUCTION_PHYSICAL_CONTRACTS, FrozenPhysicalContract, PhysicalRole,
    validate_fits_structure,
)

MISSION_ID = "OC3-SOURCE-METADATA-FRAME-SCHEMA-RECOVERY-AUTONOMY-001"
STAGE_ID = "OC3-SOURCE-METADATA-PILOT-FRAME-SCHEMA-RECOVERY-001"
SCOPE = "OFFLINE_PILOT_FRAME_SCHEMA_RECOVERY_ONLY"
ACTION_KIND = "SUPERVISED_MEMORY_BOUNDED_FRAME_SCHEMA_RECOVERY"
HASH_ALGORITHM_ID = "SHA256_ASCII_GLOBAL_BRICK_IDENTITY_V1"
GUARD_ALGORITHM_ID = "WRAP_AWARE_CLOSED_RA_BRICKROW_GUARD_1_V1"
SELECTION_ALGORITHM_ID = "HASH_ORDER_DISJOINT_GUARD_2_TARGET_2_HOLDOUT_V1"
COLUMNAR_ALGORITHM_ID = "NUMPY_FIXED_WIDTH_COLUMNAR_FRAME_SCHEMA_RECOVERY_V1"
TARGET_COUNT = 2
HOLDOUT_COUNT = 2
STREAM_CAPTURE_CAP = 262_144
DIAGNOSTIC_SCHEMA = "OC3_FRAME_SCHEMA_RECOVERY_EXECUTION_DIAGNOSTIC_001"
ROOT_PHYSICAL_FIELDS = (
    "BRICKNAME", "BRICKID", "BRICKROW", "RA", "DEC", "RA1", "RA2", "DEC1", "DEC2",
)
REGIONAL_PHYSICAL_IDENTITY_FIELDS = ("brickname", "brickid")
PHYSICAL_SCHEMA_CONTRACT_MISMATCH = "PHYSICAL_SCHEMA_CONTRACT_MISMATCH"
ALLOWED_COLUMN_ACCESS_MISMATCH = "ALLOWED_COLUMN_ACCESS_MISMATCH"
IDENTITY_DECODE_FAILURE = "IDENTITY_DECODE_FAILURE"
GLOBAL_IDENTITY_INTEGRITY_FAILURE = "GLOBAL_IDENTITY_INTEGRITY_FAILURE"
FRAME_SELECTION_INTEGRITY_FAILURE = "FRAME_SELECTION_INTEGRITY_FAILURE"
WORKER_RUNTIME_FAILURE = "WORKER_RUNTIME_FAILURE"


class FrameRecoveryError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _validate_contract(path: Path, contract: FrozenPhysicalContract,
                       allowed_roles: tuple[PhysicalRole, ...]) -> None:
    if contract.role not in allowed_roles:
        raise FrameRecoveryError(PHYSICAL_SCHEMA_CONTRACT_MISMATCH)
    try:
        validate_fits_structure(path, contract)
    except (InputError, IntegrityError) as exc:
        raise FrameRecoveryError(PHYSICAL_SCHEMA_CONTRACT_MISMATCH) from exc


def _read_exact_columns(path: Path, contract: FrozenPhysicalContract,
                        physical_names: tuple[str, ...]) -> tuple[np.ndarray, ...]:
    """Validate the complete frozen header, then decode only exact named columns."""
    try:
        from astropy.io import fits
        with fits.open(path, mode="readonly", memmap=False, lazy_load_hdus=True,
                       do_not_scale_image_data=True, uint=False) as hdus:
            hdu = hdus[contract.target_hdu_index]
            if tuple(hdu.columns.names or ()) != tuple(column.ttype for column in contract.columns):
                raise FrameRecoveryError(PHYSICAL_SCHEMA_CONTRACT_MISMATCH)
            table = hdu.data
            return tuple(np.asarray(table[name]).copy() for name in physical_names)
    except FrameRecoveryError:
        raise
    except (KeyError, IndexError, TypeError, AttributeError) as exc:
        raise FrameRecoveryError(ALLOWED_COLUMN_ACCESS_MISMATCH) from exc
    except Exception as exc:
        raise FrameRecoveryError(IDENTITY_DECODE_FAILURE) from exc


def read_root_physical(path: Path, contract: FrozenPhysicalContract | None = None) -> dict[str, np.ndarray]:
    contract = contract or PRODUCTION_PHYSICAL_CONTRACTS[PhysicalRole.ROOT_SUMMARY]
    _validate_contract(path, contract, (PhysicalRole.ROOT_SUMMARY,))
    values = _read_exact_columns(path, contract, ROOT_PHYSICAL_FIELDS)
    try:
        return root_columns(**{name.lower(): value for name, value in zip(ROOT_PHYSICAL_FIELDS, values)})
    except Exception as exc:
        raise FrameRecoveryError(IDENTITY_DECODE_FAILURE) from exc


def read_regional_identity_physical(path: Path, role: PhysicalRole,
                                    contract: FrozenPhysicalContract | None = None) -> np.ndarray:
    if role not in (PhysicalRole.NORTH_SUMMARY, PhysicalRole.SOUTH_SUMMARY):
        raise FrameRecoveryError(PHYSICAL_SCHEMA_CONTRACT_MISMATCH)
    contract = contract or PRODUCTION_PHYSICAL_CONTRACTS[role]
    _validate_contract(path, contract, (role,))
    brickname, brickid = _read_exact_columns(path, contract, REGIONAL_PHYSICAL_IDENTITY_FIELDS)
    try:
        # Physical lowercase names are normalized only here into the canonical project identity dtype.
        return identity_array(brickname, brickid)
    except Exception as exc:
        raise FrameRecoveryError(IDENTITY_DECODE_FAILURE) from exc


def _names(values: Sequence[object]) -> np.ndarray:
    converted = []
    for value in values:
        if isinstance(value, bytes):
            value = value.decode("ascii", errors="strict")
        converted.append(str(value).strip())
    width = max(1, max((len(value) for value in converted), default=1))
    return np.asarray(converted, dtype=f"U{width}")


def identity_array(bricknames: Sequence[object], brickids: Sequence[object]) -> np.ndarray:
    names = _names(bricknames)
    ids = np.asarray(brickids, dtype=np.int64)
    if names.shape != ids.shape or names.ndim != 1:
        raise FrameRecoveryError("IDENTITY_ARRAY_SHAPE_INVALID")
    result = np.empty(names.size, dtype=[("brickname", names.dtype), ("brickid", "<i8")])
    result["brickname"], result["brickid"] = names, ids
    return result


def require_unique_identities(values: np.ndarray, authority: str) -> None:
    if values.dtype.names != ("brickname", "brickid"):
        raise FrameRecoveryError("IDENTITY_DTYPE_INVALID")
    if np.unique(values).size != values.size:
        raise FrameRecoveryError(f"DUPLICATE_GLOBAL_BRICK_IDENTITY_{authority}")


def _as_identity_tuples(values: np.ndarray) -> tuple[tuple[str, int], ...]:
    return tuple((str(row["brickname"]), int(row["brickid"])) for row in values)


def global_view_both(root: np.ndarray, north: np.ndarray, south: np.ndarray,
                     excluded_bricknames: Iterable[str]) -> np.ndarray:
    require_unique_identities(root, "ROOT")
    require_unique_identities(north, "NORTH")
    require_unique_identities(south, "SOUTH")
    common = np.intersect1d(north, south, assume_unique=True)
    if common.size and not np.all(np.isin(common, root, assume_unique=True)):
        raise FrameRecoveryError("GLOBAL_IDENTITY_MISSING_FROM_ROOT")
    excluded = np.asarray(sorted(set(map(str, excluded_bricknames))), dtype=root["brickname"].dtype)
    if excluded.size:
        common = common[~np.isin(common["brickname"], excluded)]
    return np.sort(common)


def target_digest(brickname: str, brickid: int) -> str:
    literal = f"OC3_SOURCE_METADATA_DESCRIPTIVE_PILOT_001|{int(brickid)}|{brickname}"
    try:
        return hashlib.sha256(literal.encode("ascii")).hexdigest()
    except UnicodeEncodeError as exc:
        raise FrameRecoveryError("NON_ASCII_GLOBAL_BRICK_IDENTITY") from exc


def digest_order(eligible: np.ndarray) -> np.ndarray:
    digests = np.asarray([target_digest(str(row["brickname"]), int(row["brickid"]))
                          for row in eligible], dtype="U64")
    # Stable lexicographic tie-breakers retain deterministic behavior even for a hypothetical digest collision.
    return np.lexsort((eligible["brickid"], eligible["brickname"], digests))


def root_columns(*, brickname: Sequence[object], brickid: Sequence[object],
                 brickrow: Sequence[object], ra: Sequence[object], dec: Sequence[object],
                 ra1: Sequence[object], ra2: Sequence[object], dec1: Sequence[object],
                 dec2: Sequence[object]) -> dict[str, np.ndarray]:
    identity = identity_array(brickname, brickid)
    count = identity.size
    result = {"identity": identity, "brickname": identity["brickname"], "brickid": identity["brickid"],
              "brickrow": np.asarray(brickrow, dtype=np.int64),
              "ra": np.asarray(ra, dtype=np.float64), "dec": np.asarray(dec, dtype=np.float64),
              "ra1": np.asarray(ra1, dtype=np.float64), "ra2": np.asarray(ra2, dtype=np.float64),
              "dec1": np.asarray(dec1, dtype=np.float64), "dec2": np.asarray(dec2, dtype=np.float64)}
    if any(value.shape != (count,) for key, value in result.items() if key != "identity"):
        raise FrameRecoveryError("ROOT_COLUMN_SHAPE_INVALID")
    for key in ("ra", "dec", "ra1", "ra2", "dec1", "dec2"):
        if not np.all(np.isfinite(result[key])):
            raise FrameRecoveryError("ROOT_GEOMETRY_NONFINITE")
    if not (np.all((result["ra1"] >= 0) & (result["ra1"] <= 360)) and
            np.all((result["ra2"] >= 0) & (result["ra2"] <= 360))):
        raise FrameRecoveryError("ROOT_RA_INTERVAL_INVALID")
    require_unique_identities(identity, "ROOT")
    return result


def _segment_overlap(left: np.ndarray, right: np.ndarray, a: float, b: float) -> np.ndarray:
    return np.maximum(left, a) <= np.minimum(right, b)


def wrap_aware_overlap_mask(ra1: np.ndarray, ra2: np.ndarray, target_ra1: float,
                            target_ra2: float) -> np.ndarray:
    nonwrap = ra1 <= ra2
    result = np.zeros(ra1.size, dtype=np.bool_)
    target_segments = ((target_ra1, target_ra2),) if target_ra1 <= target_ra2 else (
        (target_ra1, 360.0), (0.0, target_ra2))
    for left, right in target_segments:
        result |= nonwrap & _segment_overlap(ra1, ra2, left, right)
        result |= (~nonwrap) & (_segment_overlap(ra1, np.full(ra1.shape, 360.0), left, right) |
                                _segment_overlap(np.zeros(ra1.shape), ra2, left, right))
    return result


def identity_index(root: Mapping[str, np.ndarray], identity: tuple[str, int]) -> int:
    mask = (root["brickname"] == identity[0]) & (root["brickid"] == identity[1])
    indices = np.flatnonzero(mask)
    if indices.size != 1:
        raise FrameRecoveryError("ROOT_IDENTITY_LOOKUP_INVALID")
    return int(indices[0])


def guard_indices(root: Mapping[str, np.ndarray], identity: tuple[str, int]) -> np.ndarray:
    index = identity_index(root, identity)
    mask = (np.abs(root["brickrow"] - root["brickrow"][index]) <= 1) & wrap_aware_overlap_mask(
        root["ra1"], root["ra2"], float(root["ra1"][index]), float(root["ra2"][index]))
    indices = np.flatnonzero(mask)
    if index not in indices:
        raise FrameRecoveryError("TARGET_NOT_IN_GUARD")
    return indices


def select_frame(root: Mapping[str, np.ndarray], eligible: np.ndarray) -> tuple[dict[str, object], ...]:
    accepted: list[dict[str, object]] = []
    occupied = np.zeros(root["identity"].size, dtype=np.bool_)
    for position in digest_order(eligible):
        row = eligible[position]
        identity = (str(row["brickname"]), int(row["brickid"]))
        guard = guard_indices(root, identity)
        if not np.any(occupied[guard]):
            accepted.append({"identity": identity, "digest": target_digest(*identity),
                             "role": "PILOT_TARGET" if len(accepted) < TARGET_COUNT else "RESERVED_HOLDOUT",
                             "guard_indices": guard})
            occupied[guard] = True
            if len(accepted) == TARGET_COUNT + HOLDOUT_COUNT:
                break
    if len(accepted) != TARGET_COUNT + HOLDOUT_COUNT:
        raise FrameRecoveryError("FOUR_DISJOINT_GUARDS_UNAVAILABLE")
    return tuple(accepted)


def _geometry(root: Mapping[str, np.ndarray], index: int) -> dict[str, object]:
    return {"brickname": str(root["brickname"][index]), "brickid": int(root["brickid"][index]),
            "brickrow": int(root["brickrow"][index]), "ra": float(root["ra"][index]),
            "dec": float(root["dec"][index]), "ra1": float(root["ra1"][index]),
            "ra2": float(root["ra2"][index]), "dec1": float(root["dec1"][index]),
            "dec2": float(root["dec2"][index])}


def frame_payload(root: Mapping[str, np.ndarray], selections: Sequence[Mapping[str, object]],
                  authority_hashes: Mapping[str, str], implementation_aggregate: str) -> dict[str, object]:
    roles = [item["role"] for item in selections]
    if roles != ["PILOT_TARGET", "PILOT_TARGET", "RESERVED_HOLDOUT", "RESERVED_HOLDOUT"]:
        raise FrameRecoveryError("FRAME_ROLE_COUNT_INVALID")
    return {"authority_hashes": dict(sorted(authority_hashes.items())),
            "columnar_algorithm_id": COLUMNAR_ALGORITHM_ID,
            "guard_algorithm_id": GUARD_ALGORITHM_ID, "hash_algorithm_id": HASH_ALGORITHM_ID,
            "implementation_aggregate": implementation_aggregate,
            "schema_version": "OC3_SOURCE_METADATA_PILOT_FRAME_001",
            "selection_algorithm_id": SELECTION_ALGORITHM_ID,
            "selections": [{"digest": item["digest"],
                "global_identity": {"brickname": item["identity"][0], "brickid": item["identity"][1]},
                "guard": [_geometry(root, int(index)) for index in item["guard_indices"]],
                "role": item["role"]} for item in selections], "stage_id": STAGE_ID}


def validate_frame_payload(value: Mapping[str, object], authority_hashes: Mapping[str, str],
                           implementation_aggregate: str) -> None:
    if (value.get("schema_version") != "OC3_SOURCE_METADATA_PILOT_FRAME_001" or
            value.get("stage_id") != STAGE_ID or value.get("authority_hashes") != dict(sorted(authority_hashes.items())) or
            value.get("implementation_aggregate") != implementation_aggregate or
            value.get("hash_algorithm_id") != HASH_ALGORITHM_ID or value.get("guard_algorithm_id") != GUARD_ALGORITHM_ID or
            value.get("selection_algorithm_id") != SELECTION_ALGORITHM_ID or value.get("columnar_algorithm_id") != COLUMNAR_ALGORITHM_ID):
        raise FrameRecoveryError("PILOT_FRAME_BINDING_INVALID")
    selections = value.get("selections")
    if not isinstance(selections, list) or [item.get("role") for item in selections] != [
            "PILOT_TARGET", "PILOT_TARGET", "RESERVED_HOLDOUT", "RESERVED_HOLDOUT"]:
        raise FrameRecoveryError("PILOT_FRAME_SELECTION_INVALID")
    guards = []
    for item in selections:
        identity = item.get("global_identity", {})
        if item.get("digest") != target_digest(str(identity.get("brickname")), int(identity.get("brickid"))):
            raise FrameRecoveryError("PILOT_FRAME_DIGEST_INVALID")
        guard = item.get("guard")
        if not isinstance(guard, list) or not guard:
            raise FrameRecoveryError("PILOT_FRAME_GUARD_INVALID")
        members = {(row["brickname"], int(row["brickid"])) for row in guard}
        if (identity["brickname"], int(identity["brickid"])) not in members:
            raise FrameRecoveryError("PILOT_FRAME_TARGET_NOT_IN_GUARD")
        guards.append(members)
    if any(not guards[i].isdisjoint(guards[j]) for i in range(4) for j in range(i)):
        raise FrameRecoveryError("PILOT_FRAME_GUARDS_NOT_DISJOINT")


def read_development_bricknames(path: Path) -> tuple[str, ...]:
    with Path(path).open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        names = {name.upper(): name for name in (reader.fieldnames or [])}
        if "BRICKNAME" not in names:
            raise FrameRecoveryError("DEVELOPMENT_IDENTITY_COLUMNS_MISSING")
        return tuple(str(row[names["BRICKNAME"]]).strip() for row in reader)


def compact_array_bytes(root: Mapping[str, np.ndarray], north: np.ndarray, south: np.ndarray) -> int:
    unique = {id(value): value for value in root.values()}
    return sum(value.nbytes for value in unique.values()) + north.nbytes + south.nbytes
