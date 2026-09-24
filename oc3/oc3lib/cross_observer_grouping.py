"""Closed, offline semantics for prospective cross-observer grouping research."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import os
from pathlib import Path
from typing import Iterable, Sequence

from .core import canonical

PROJECT = Path("/home/jzsalinas/Documents/galaxy-morphology-discovery")

ALLOWED_SOURCE_FIELDS = (
    "RELEASE", "BRICKID", "OBJID", "BRICKNAME", "BRICK_PRIMARY",
    "RA", "DEC", "RA_IVAR", "DEC_IVAR",
)
DENIED_VALUE_FIELDS = frozenset({
    "TYPE", "DCHISQ", "SERSIC", "SHAPE_R", "SHAPE_E1", "SHAPE_E2",
    "FLUX_G", "FLUX_R", "FLUX_Z", "MAG_G", "MAG_R", "MAG_Z",
    "PHOTO_Z", "REF_CAT", "REF_ID", "GALAXY_ZOO", "ZOOBOT",
})
REGIONAL_SOURCE_TABLES = frozenset({"ls_dr9.tractor_n", "ls_dr9.tractor_s"})
RESOLVED_TABLE = "ls_dr9.tractor"


class GroupingError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sealed(value: dict[str, object]) -> dict[str, object]:
    if "sealed" in value:
        raise GroupingError("SEAL_INPUT_INVALID")
    result = dict(value)
    result["sealed"] = sha256_bytes(canonical(value))
    return result


def validate_sealed(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or "sealed" not in value:
        raise GroupingError("SEALED_OBJECT_INVALID")
    body = {key: item for key, item in value.items() if key != "sealed"}
    if value["sealed"] != sha256_bytes(canonical(body)):
        raise GroupingError("SEALED_OBJECT_INVALID")
    return value


def _strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def load_canonical_json(path: Path) -> dict[str, object]:
    try:
        raw = Path(path).read_bytes()
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_strict_object)
    except (OSError, UnicodeError, ValueError) as exc:
        raise GroupingError("CANONICAL_JSON_INVALID") from exc
    if not isinstance(value, dict) or raw != canonical(value) + b"\n":
        raise GroupingError("CANONICAL_JSON_INVALID")
    return value


def write_json_immutable(path: Path, value: object) -> None:
    data = canonical(value) + b"\n"
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise GroupingError("IMMUTABLE_OUTPUT_CONFLICT")
        return
    if len(data) > 4 * 1024 * 1024:
        raise GroupingError("RESOURCE_LIMIT_EXCEEDED")
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def audit_implementation_aggregate(paths: Sequence[str] = ()) -> str:
    return sha256_bytes(canonical({path: file_sha256(PROJECT / path) for path in paths}))


@dataclass(frozen=True, order=True)
class CatalogSourceObservation:
    release: int
    brickid: int
    objid: int
    observer_domain: str

    def __post_init__(self) -> None:
        if any(type(value) is not int for value in (self.release, self.brickid, self.objid)):
            raise GroupingError("CATALOG_SOURCE_IDENTITY_INVALID")
        if self.observer_domain not in ("north", "south"):
            raise GroupingError("OBSERVER_DOMAIN_INVALID")

    @property
    def identity(self) -> tuple[int, int, int]:
        return self.release, self.brickid, self.objid


class AssociationState(str, Enum):
    NO_MATCH = "NO_MATCH"
    UNIQUE_MATCH = "UNIQUE_MATCH"
    MULTIPLE_MATCH = "MULTIPLE_MATCH"
    AMBIGUOUS_MATCH = "AMBIGUOUS_MATCH"
    INVALID_MATCH = "INVALID_MATCH"
    ONE_TO_MANY = "ONE_TO_MANY"
    MANY_TO_ONE = "MANY_TO_ONE"
    MANY_TO_MANY = "MANY_TO_MANY"


@dataclass(frozen=True)
class CrossObserverAssociation:
    north: tuple[CatalogSourceObservation, ...]
    south: tuple[CatalogSourceObservation, ...]
    state: AssociationState

    def __post_init__(self) -> None:
        if any(item.observer_domain != "north" for item in self.north):
            raise GroupingError("ASSOCIATION_DOMAIN_INVALID")
        if any(item.observer_domain != "south" for item in self.south):
            raise GroupingError("ASSOCIATION_DOMAIN_INVALID")
        cardinality = (len(self.north), len(self.south))
        allowed = {
            AssociationState.NO_MATCH: cardinality[0] == 0 or cardinality[1] == 0,
            AssociationState.UNIQUE_MATCH: cardinality == (1, 1),
            AssociationState.ONE_TO_MANY: cardinality[0] == 1 and cardinality[1] > 1,
            AssociationState.MANY_TO_ONE: cardinality[0] > 1 and cardinality[1] == 1,
            AssociationState.MANY_TO_MANY: cardinality[0] > 1 and cardinality[1] > 1,
            AssociationState.MULTIPLE_MATCH: max(cardinality) > 1,
            AssociationState.AMBIGUOUS_MATCH: cardinality[0] > 0 and cardinality[1] > 0,
            AssociationState.INVALID_MATCH: True,
        }
        if not allowed[self.state]:
            raise GroupingError("ASSOCIATION_CARDINALITY_INVALID")


@dataclass(frozen=True)
class SplitSafetyGroup:
    split_group_id: str
    observations: tuple[CatalogSourceObservation, ...]

    def __post_init__(self) -> None:
        if not self.split_group_id or not self.observations:
            raise GroupingError("SPLIT_GROUP_INVALID")


@dataclass(frozen=True)
class AstrophysicalObjectGroup:
    object_group_id: str
    observations: tuple[CatalogSourceObservation, ...]
    evidence_contract: str

    def __post_init__(self) -> None:
        if not self.object_group_id or not self.observations or not self.evidence_contract:
            raise GroupingError("OBJECT_GROUP_EVIDENCE_REQUIRED")


@dataclass(frozen=True)
class FrozenHoldoutContract:
    selection_domain: str
    development_digest: str
    holdout_digest: str

    def __post_init__(self) -> None:
        if self.selection_domain != "GLOBAL_BRICK_IDENTITY_HASH_V1":
            raise GroupingError("HOLDOUT_DOMAIN_INVALID")
        for digest in (self.development_digest, self.holdout_digest):
            if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
                raise GroupingError("HOLDOUT_DIGEST_INVALID")
        if self.development_digest == self.holdout_digest:
            raise GroupingError("HOLDOUT_SEPARATION_INVALID")


def validate_source_projection(fields: Iterable[str]) -> tuple[str, ...]:
    observed = tuple(fields)
    if observed != ALLOWED_SOURCE_FIELDS:
        raise GroupingError("SOURCE_PROJECTION_NOT_EXACT")
    if DENIED_VALUE_FIELDS.intersection(observed):
        raise GroupingError("DENIED_SOURCE_VALUE_FIELD")
    return observed


def validate_regional_source_table(table: str, *, exact_schema_contract: bool) -> str:
    if table == RESOLVED_TABLE:
        raise GroupingError("RESOLVED_TRACTOR_NOT_INDEPENDENT_POPULATION")
    if table not in REGIONAL_SOURCE_TABLES:
        raise GroupingError("REGIONAL_SOURCE_TABLE_NOT_ALLOWED")
    if exact_schema_contract is not True:
        raise GroupingError("EXACT_SOURCE_SCHEMA_CONTRACT_REQUIRED")
    return table


def classify_candidate_cardinality(north_count: int, south_count: int, *, invalid: bool = False) -> AssociationState:
    if any(type(value) is not int or value < 0 for value in (north_count, south_count)):
        raise GroupingError("ASSOCIATION_CARDINALITY_INVALID")
    if invalid:
        return AssociationState.INVALID_MATCH
    if north_count == 0 or south_count == 0:
        return AssociationState.NO_MATCH
    if (north_count, south_count) == (1, 1):
        return AssociationState.UNIQUE_MATCH
    if north_count == 1:
        return AssociationState.ONE_TO_MANY
    if south_count == 1:
        return AssociationState.MANY_TO_ONE
    return AssociationState.MANY_TO_MANY


def preserve_candidate_set(candidates: Sequence[CatalogSourceObservation]) -> tuple[CatalogSourceObservation, ...]:
    """Preserve deterministic candidates; never choose a nearest row implicitly."""
    return tuple(sorted(candidates, key=lambda item: (item.release, item.brickid, item.objid, item.observer_domain)))


def validate_positional_uncertainty_contract(*, uses_ra_dec_ivar: bool,
                                             calibration_covariance_bound: bool,
                                             extended_centroid_model_bound: bool) -> None:
    if uses_ra_dec_ivar and not calibration_covariance_bound:
        raise GroupingError("STATISTICAL_IVAR_NOT_COMPLETE_COVARIANCE")
    if not extended_centroid_model_bound:
        raise GroupingError("EXTENDED_SOURCE_CENTROID_MODEL_UNRESOLVED")


def validate_observer_domain_role(role: str) -> None:
    if role not in ("PROVENANCE", "CONFOUND_AUDIT", "REPLICATION_AUDIT"):
        raise GroupingError("OBSERVER_DOMAIN_ROLE_FORBIDDEN")


def validate_replication_claim(group: AstrophysicalObjectGroup | None) -> None:
    if group is None:
        raise GroupingError("UNKNOWN_GROUPING_BLOCKS_REPLICATION_CLAIM")


def validate_split_assignments(rows: Iterable[tuple[str | None, str]], *, confirmatory: bool) -> None:
    assignments: dict[str, str] = {}
    for group_id, split in rows:
        if group_id is None:
            if confirmatory:
                raise GroupingError("UNKNOWN_GROUPING_BLOCKS_CONFIRMATORY_SPLIT")
            continue
        if group_id in assignments and assignments[group_id] != split:
            raise GroupingError("SPLIT_GROUP_LEAKAGE")
        assignments[group_id] = split
