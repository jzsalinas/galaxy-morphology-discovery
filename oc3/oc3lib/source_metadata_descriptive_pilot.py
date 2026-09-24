"""Frozen, morphology-blind algorithms for the OC3 source-metadata pilot.

This module is offline.  It contains no HTTP client and no matching classifier.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import csv
import hashlib
import math
from pathlib import Path
from typing import Iterable, Mapping, Sequence

MISSION_ID = "OC3-SOURCE-METADATA-DESCRIPTIVE-PILOT-AUTONOMY-001"
FRAME_STAGE_ID = "OC3-SOURCE-METADATA-PILOT-FRAME-DERIVATION-001"
FRAME_SCOPE = "OFFLINE_PILOT_FRAME_DERIVATION_ONLY"
HASH_ALGORITHM_ID = "SHA256_ASCII_GLOBAL_BRICK_IDENTITY_V1"
GUARD_ALGORITHM_ID = "WRAP_AWARE_CLOSED_RA_BRICKROW_GUARD_1_V1"
SELECTION_ALGORITHM_ID = "HASH_ORDER_DISJOINT_GUARD_2_TARGET_2_HOLDOUT_V1"
TARGET_COUNT = 2
HOLDOUT_COUNT = 2
NEIGHBOR_RANK_COUNT = 2
MAX_SOURCE_ROWS_PER_DOMAIN = 150000
ROW_QUERY_HARD_CAP = 150001
QUANTILE_GRID = (0.0, 0.05, 0.25, 0.50, 0.75, 0.95, 1.0)
REGIONAL_TABLES = ("ls_dr9.tractor_n", "ls_dr9.tractor_s")
SOURCE_PROJECTION = (
    "release", "brickid", "objid", "brickname", "brick_primary",
    "ra", "dec", "ra_ivar", "dec_ivar",
)
DENIED_SOURCE_VALUE_COLUMNS = frozenset({
    "type", "dchisq", "sersic", "shape_r", "shape_e1", "shape_e2",
    "flux_g", "flux_r", "flux_z", "mag_g", "mag_r", "mag_z", "color",
    "photo_z", "ref_cat", "ref_id", "photsys", "galaxy_zoo", "zoobot",
    "pixels", "image_measurements",
})
ORDER_BY = ("release", "brickid", "objid")
REQUEST_CAP = 5
BODY_CAP = 67_108_864
RESPONSE_CAPS = {
    "schema": 524_288, "north_count": 65_536, "south_count": 65_536,
    "north_rows": 32_505_856, "south_rows": 32_505_856,
}

LOCAL_NEAREST_TERM = "LOCAL_NEAREST_WITHIN_GUARD"
LOCAL_SECOND_TERM = "LOCAL_SECOND_NEAREST_WITHIN_GUARD"
LOCAL_RECIPROCAL_TERM = "LOCAL_RECIPROCAL_NEAREST"


class PilotIntegrityError(ValueError):
    pass


@dataclass(frozen=True, order=True)
class GlobalBrickIdentity:
    brickname: str
    brickid: int


@dataclass(frozen=True)
class BrickGeometry:
    identity: GlobalBrickIdentity
    brickrow: int
    ra: float
    dec: float
    ra1: float
    ra2: float
    dec1: float
    dec2: float


@dataclass(frozen=True)
class FrameSelection:
    identity: GlobalBrickIdentity
    digest: str
    role: str
    guard: tuple[GlobalBrickIdentity, ...]


def _identity(row: Mapping[str, object]) -> GlobalBrickIdentity:
    return GlobalBrickIdentity(str(row["BRICKNAME"]).strip(), int(row["BRICKID"]))


def identity_index(rows: Iterable[Mapping[str, object]]) -> dict[GlobalBrickIdentity, Mapping[str, object]]:
    result: dict[GlobalBrickIdentity, Mapping[str, object]] = {}
    for row in rows:
        identity = _identity(row)
        if identity in result:
            raise PilotIntegrityError("DUPLICATE_GLOBAL_BRICK_IDENTITY")
        result[identity] = row
    return result


def reconstruct_global_view_both(
    root_rows: Iterable[Mapping[str, object]], north_rows: Iterable[Mapping[str, object]],
    south_rows: Iterable[Mapping[str, object]], excluded: Iterable[GlobalBrickIdentity | str],
) -> tuple[dict[GlobalBrickIdentity, BrickGeometry], tuple[GlobalBrickIdentity, ...]]:
    roots = identity_index(root_rows)
    north = identity_index(north_rows)
    south = identity_index(south_rows)
    excluded_values = tuple(excluded)
    excluded_set = {value for value in excluded_values if isinstance(value, GlobalBrickIdentity)}
    excluded_names = {value for value in excluded_values if isinstance(value, str)}
    common = sorted(identity for identity in (set(north) & set(south)) - excluded_set
                    if identity.brickname not in excluded_names)
    if any(identity not in roots for identity in common):
        raise PilotIntegrityError("GLOBAL_IDENTITY_MISSING_FROM_ROOT")
    geometry = {
        identity: BrickGeometry(identity, int(roots[identity]["BRICKROW"]),
            *[float(roots[identity][key]) for key in ("RA", "DEC", "RA1", "RA2", "DEC1", "DEC2")])
        for identity in roots
    }
    return geometry, tuple(common)


def target_digest(identity: GlobalBrickIdentity) -> str:
    literal = f"OC3_SOURCE_METADATA_DESCRIPTIVE_PILOT_001|{identity.brickid}|{identity.brickname}"
    try:
        encoded = literal.encode("ascii")
    except UnicodeEncodeError as exc:
        raise PilotIntegrityError("NON_ASCII_GLOBAL_BRICK_IDENTITY") from exc
    return hashlib.sha256(encoded).hexdigest()


def _ra_segments(ra1: float, ra2: float) -> tuple[tuple[float, float], ...]:
    if not (math.isfinite(ra1) and math.isfinite(ra2) and 0.0 <= ra1 <= 360.0 and 0.0 <= ra2 <= 360.0):
        raise PilotIntegrityError("INVALID_RA_INTERVAL")
    return ((ra1, ra2),) if ra1 <= ra2 else ((ra1, 360.0), (0.0, ra2))


def closed_ra_intervals_overlap(a1: float, a2: float, b1: float, b2: float) -> bool:
    return any(max(left_a, left_b) <= min(right_a, right_b)
               for left_a, right_a in _ra_segments(a1, a2)
               for left_b, right_b in _ra_segments(b1, b2))


def guard_one(target: GlobalBrickIdentity,
              geometry: Mapping[GlobalBrickIdentity, BrickGeometry]) -> tuple[GlobalBrickIdentity, ...]:
    if target not in geometry:
        raise PilotIntegrityError("TARGET_GEOMETRY_MISSING")
    t = geometry[target]
    members = tuple(sorted(identity for identity, brick in geometry.items()
        if abs(brick.brickrow - t.brickrow) <= 1 and
        closed_ra_intervals_overlap(brick.ra1, brick.ra2, t.ra1, t.ra2)))
    if target not in members:
        raise PilotIntegrityError("TARGET_NOT_IN_GUARD")
    return members


def select_frame(eligible: Sequence[GlobalBrickIdentity],
                 geometry: Mapping[GlobalBrickIdentity, BrickGeometry]) -> tuple[FrameSelection, ...]:
    accepted: list[FrameSelection] = []
    occupied: set[GlobalBrickIdentity] = set()
    ordered = sorted(set(eligible), key=lambda identity: (target_digest(identity), identity))
    for identity in ordered:
        guard = guard_one(identity, geometry)
        if occupied.isdisjoint(guard):
            role = "PILOT_TARGET" if len(accepted) < TARGET_COUNT else "RESERVED_HOLDOUT"
            accepted.append(FrameSelection(identity, target_digest(identity), role, guard))
            occupied.update(guard)
            if len(accepted) == TARGET_COUNT + HOLDOUT_COUNT:
                break
    if len(accepted) != TARGET_COUNT + HOLDOUT_COUNT:
        raise PilotIntegrityError("FOUR_DISJOINT_GUARDS_UNAVAILABLE")
    return tuple(accepted)


def frame_payload(selections: Sequence[FrameSelection], geometry: Mapping[GlobalBrickIdentity, BrickGeometry],
                  authority_hashes: Mapping[str, str]) -> dict[str, object]:
    if [item.role for item in selections] != ["PILOT_TARGET"] * 2 + ["RESERVED_HOLDOUT"] * 2:
        raise PilotIntegrityError("FRAME_ROLE_COUNT_INVALID")
    return {
        "authority_hashes": dict(sorted(authority_hashes.items())),
        "guard_algorithm_id": GUARD_ALGORITHM_ID,
        "hash_algorithm_id": HASH_ALGORITHM_ID,
        "schema_version": "OC3_SOURCE_METADATA_PILOT_FRAME_001",
        "selection_algorithm_id": SELECTION_ALGORITHM_ID,
        "selections": [{
            "digest": item.digest,
            "global_identity": asdict(item.identity),
            "guard": [{"geometry": asdict(geometry[member]), "global_identity": asdict(member)}
                      for member in item.guard],
            "role": item.role,
        } for item in selections],
        "stage_id": FRAME_STAGE_ID,
    }


def target_guard_union(selections: Sequence[FrameSelection]) -> tuple[str, ...]:
    """Return only target support; reserved holdouts are deliberately inaccessible."""
    targets = [item for item in selections if item.role == "PILOT_TARGET"]
    if len(targets) != TARGET_COUNT or sum(item.role == "RESERVED_HOLDOUT" for item in selections) != HOLDOUT_COUNT:
        raise PilotIntegrityError("FRAME_ROLE_COUNT_INVALID")
    return tuple(sorted({identity.brickname for item in targets for identity in item.guard}))


def read_development_identities(path: Path) -> tuple[GlobalBrickIdentity | str, ...]:
    with Path(path).open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        names = {name.upper(): name for name in (reader.fieldnames or [])}
        if "BRICKNAME" not in names:
            raise PilotIntegrityError("DEVELOPMENT_IDENTITY_COLUMNS_MISSING")
        if "BRICKID" in names:
            return tuple(GlobalBrickIdentity(str(row[names["BRICKNAME"]]).strip(), int(row[names["BRICKID"]]))
                         for row in reader)
        return tuple(str(row[names["BRICKNAME"]]).strip() for row in reader)


def validate_source_projection(columns: Iterable[str]) -> None:
    normalized = tuple(str(value).lower() for value in columns)
    if normalized != SOURCE_PROJECTION:
        raise PilotIntegrityError("SOURCE_PROJECTION_NOT_EXACT")
    if set(normalized) & DENIED_SOURCE_VALUE_COLUMNS:
        raise PilotIntegrityError("DENIED_SOURCE_VALUE_COLUMN")


def validate_regional_table(table: str) -> None:
    if table not in REGIONAL_TABLES:
        raise PilotIntegrityError("REGIONAL_TABLE_NOT_ALLOWED")


def quoted_bricks(bricks: Iterable[str]) -> str:
    values = sorted(set(bricks))
    if not values or any(not value or not value.replace("m", "").replace("p", "").isalnum() for value in values):
        raise PilotIntegrityError("TARGET_GUARD_UNION_INVALID")
    return ",".join("'" + value + "'" for value in values)


def schema_query() -> str:
    fields = ",".join("'" + field + "'" for field in SOURCE_PROJECTION)
    return ("SELECT table_name,column_name,datatype,description FROM TAP_SCHEMA.columns "
            "WHERE table_name IN ('ls_dr9.tractor_n','ls_dr9.tractor_s') "
            f"AND column_name IN ({fields}) ORDER BY table_name,column_name")


def count_query(table: str, bricks: Iterable[str]) -> str:
    validate_regional_table(table)
    return (f"SELECT brickname,COUNT(*) AS source_count FROM {table} WHERE brick_primary=1 "
            f"AND brickname IN ({quoted_bricks(bricks)}) GROUP BY brickname ORDER BY brickname")


def row_query(table: str, bricks: Iterable[str]) -> str:
    validate_regional_table(table)
    return (f"SELECT TOP {ROW_QUERY_HARD_CAP} {','.join(SOURCE_PROJECTION)} FROM {table} "
            f"WHERE brick_primary=1 AND brickname IN ({quoted_bricks(bricks)}) "
            f"ORDER BY {','.join(ORDER_BY)}")


class AcquisitionSequence:
    """Fail-closed schema -> two counts -> rows state machine."""
    def __init__(self) -> None:
        self.schema_valid = False
        self.counts: dict[str, int] = {}
        self.resource_bound = False

    def accept_schema(self, table_columns: Mapping[str, Iterable[str]]) -> None:
        if set(table_columns) != set(REGIONAL_TABLES):
            raise PilotIntegrityError("SCHEMA_TABLE_SET_INVALID")
        for columns in table_columns.values():
            if set(map(str.lower, columns)) != set(SOURCE_PROJECTION):
                raise PilotIntegrityError("SCHEMA_REQUIRED_FIELDS_MISSING")
        self.schema_valid = True

    def accept_count(self, table: str, per_brick: Mapping[str, int]) -> None:
        if not self.schema_valid:
            raise PilotIntegrityError("COUNT_BEFORE_SCHEMA")
        validate_regional_table(table)
        total = sum(per_brick.values())
        if any(type(value) is not int or value < 0 for value in per_brick.values()):
            raise PilotIntegrityError("COUNT_INVALID")
        self.counts[table] = total
        if total > MAX_SOURCE_ROWS_PER_DOMAIN:
            self.resource_bound = True

    def rows_allowed(self, table: str) -> bool:
        validate_regional_table(table)
        return self.schema_valid and set(self.counts) == set(REGIONAL_TABLES) and not self.resource_bound

    def require_rows_allowed(self, table: str) -> None:
        if not self.rows_allowed(table):
            raise PilotIntegrityError("ROWS_NOT_AUTHORIZED_AFTER_PREFLIGHT")


def validate_row_count(rows_returned: int) -> None:
    if type(rows_returned) is not int or rows_returned < 0:
        raise PilotIntegrityError("ROW_COUNT_INVALID")
    if rows_returned >= ROW_QUERY_HARD_CAP:
        raise PilotIntegrityError("ROW_HARD_CAP_OVERFLOW")


def validate_source_rows(rows: Iterable[Mapping[str, object]], domain: str,
                         allowed_bricks: set[str]) -> tuple[dict[str, object], ...]:
    if domain not in ("north", "south"):
        raise PilotIntegrityError("PROCESSING_DOMAIN_INVALID")
    result = []
    identities = set()
    for original in rows:
        row = {str(k).lower(): v for k, v in original.items()}
        validate_source_projection(row.keys())
        if str(row["brickname"]) not in allowed_bricks or row["brick_primary"] not in (1, True, "1"):
            raise PilotIntegrityError("SOURCE_ROW_OUTSIDE_FRAME")
        identity = (int(row["release"]), int(row["brickid"]), int(row["objid"]))
        if identity in identities:
            raise PilotIntegrityError("DUPLICATE_CATALOG_IDENTITY")
        identities.add(identity)
        ra, dec = float(row["ra"]), float(row["dec"])
        if not (math.isfinite(ra) and 0 <= ra < 360 and math.isfinite(dec) and -90 <= dec <= 90):
            raise PilotIntegrityError("INVALID_SOURCE_COORDINATE")
        result.append({**row, "processing_domain": domain})
    return tuple(result)


def unit_vector(ra_deg: float, dec_deg: float) -> tuple[float, float, float]:
    ra, dec = math.radians(ra_deg), math.radians(dec_deg)
    scale = math.cos(dec)
    return scale * math.cos(ra), scale * math.sin(ra), math.sin(dec)


def angular_separation_deg(a: tuple[float, float], b: tuple[float, float]) -> float:
    ua, ub = unit_vector(*a), unit_vector(*b)
    dot = min(1.0, max(-1.0, sum(x * y for x, y in zip(ua, ub))))
    return math.degrees(math.acos(dot))


def local_two_nearest(anchor: tuple[float, float], candidates: Sequence[tuple[object, float, float]]) -> tuple[tuple[object, float], ...]:
    ranked = sorted(((identity, angular_separation_deg(anchor, (ra, dec)))
                     for identity, ra, dec in candidates), key=lambda item: (item[1], repr(item[0])))
    return tuple(ranked[:NEIGHBOR_RANK_COUNT])


def local_reciprocal(anchor_id: object, candidate_id: object,
                     forward_nearest: Mapping[object, object], reverse_nearest: Mapping[object, object]) -> bool:
    return forward_nearest.get(anchor_id) == candidate_id and reverse_nearest.get(candidate_id) == anchor_id


def descriptive_quantiles(values: Sequence[float]) -> dict[str, float | None]:
    if not values:
        return {format(q, ".2f"): None for q in QUANTILE_GRID}
    ordered = sorted(float(value) for value in values)
    if any(not math.isfinite(value) for value in ordered):
        raise PilotIntegrityError("NONFINITE_DESCRIPTIVE_VALUE")
    result: dict[str, float] = {}
    for q in QUANTILE_GRID:
        position = q * (len(ordered) - 1)
        lower, upper = math.floor(position), math.ceil(position)
        fraction = position - lower
        result[format(q, ".2f")] = ordered[lower] * (1 - fraction) + ordered[upper] * fraction
    return result
