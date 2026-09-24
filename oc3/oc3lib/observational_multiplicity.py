"""Offline, PHOTSYS-independent global-brick/view relation primitives.

Importing this module performs no file, network, FITS, PHOTSYS, Tractor, pixel,
or morphology access.  The real local-authority reader is reachable only from
the explicitly permitted audit entry point.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import csv
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import struct
from types import MappingProxyType
from typing import Iterable, Mapping, Sequence

from .core import canonical
from .metadata_value_semantics import validate_brickname
from .patch_metadata_decode import _validate_table
from .provider_physical_contracts import PRODUCTION_PHYSICAL_CONTRACTS, PhysicalRole


PROJECT = Path("/home/jzsalinas/Documents/galaxy-morphology-discovery")
STAGE_ID = "OC3-GLOBAL-VIEW-RELATION-AUDIT-001"
SCOPE = "OFFLINE_GLOBAL_VIEW_RELATION_ONLY"
SUCCESS_TERMINAL = "GLOBAL_VIEW_RELATION_VALIDATED"
SPEC_PATH = PROJECT / "OC3_GLOBAL_VIEW_RELATION_AUDIT_SPEC_001.md"
SPEC_SHA256 = "8df3d02f71c472aba204b251b28cc95353dd553bcd81f7f2a656a390bc7c9ac8"
ATTEMPT = PROJECT / "oc3/metadata_bootstrap/OC3-METADATA-BOOTSTRAP-001"
FIXTURE_PATH = PROJECT / "oc3/INPUTS/OC3_DEVELOPMENT_BRICKS.csv"

AUTHORITIES = MappingProxyType({
    "ROOT_SUMMARY": (
        ATTEMPT / "RAW_IMMUTABLE/ROOT_SUMMARY/survey-bricks.fits.gz",
        13_147_987,
        "dc943d702357f93553b9e5d15e87ace38df94eb7095f4100657407b3f9919c5f",
        PhysicalRole.ROOT_SUMMARY,
    ),
    "NORTH_SUMMARY": (
        ATTEMPT / "RAW_IMMUTABLE/NORTH_SUMMARY/survey-bricks-dr9-north.fits.gz",
        20_882_100,
        "2edd5c295fdad26852c6f224a3ff023cff43dd0e03a53acd35b767e726ee72fb",
        PhysicalRole.NORTH_SUMMARY,
    ),
    "SOUTH_SUMMARY": (
        ATTEMPT / "RAW_IMMUTABLE/SOUTH_SUMMARY/survey-bricks-dr9-south.fits.gz",
        55_399_879,
        "7360414f5d53571ca70fa0cb483eb8c80cfcbe80df0856a117246f442a0b9a3f",
        PhysicalRole.SOUTH_SUMMARY,
    ),
    "DEVELOPMENT_FIXTURES": (
        FIXTURE_PATH,
        None,
        "147c0942a5340ed18eec23a610f8afd5721390fad09c1da7ed01593deb40fab6",
        None,
    ),
})

ROOT_FIELDS = ("BRICKNAME", "BRICKID", "RA", "DEC", "RA1", "RA2", "DEC1", "DEC2")
REGIONAL_FIELDS = ("brickname", "brickid", "ra", "dec", "ra1", "ra2", "dec1", "dec2")
FORBIDDEN_FIELD_TOKENS = frozenset({
    "photsys", "type", "dchisq", "sersic", "shape_r", "shape_e1", "shape_e2",
    "galaxy_zoo", "zoobot", "morphology", "label",
})
VIEW_NORTH_ONLY = "GLOBAL_VIEW_NORTH_ONLY"
VIEW_SOUTH_ONLY = "GLOBAL_VIEW_SOUTH_ONLY"
VIEW_BOTH = "GLOBAL_VIEW_BOTH"
VIEW_NONE = "GLOBAL_VIEW_NONE"
SELECTION_PREFIX = "OC3-GALAXY-ELIGIBILITY-GLOBAL-IDENTITY-SELECTION-V1"
AUDIT_IMPLEMENTATION_FILES = (
    "OC3_GLOBAL_VIEW_RELATION_AUDIT_SPEC_001.md",
    "oc3/oc3_observational_multiplicity.py",
    "oc3/oc3lib/observational_multiplicity.py",
)


class MultiplicityError(Exception):
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
        raise MultiplicityError("SEAL_INPUT_INVALID")
    result = dict(value)
    result["sealed"] = sha256_bytes(canonical(value))
    return result


def validate_sealed(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or "sealed" not in value:
        raise MultiplicityError("SEALED_OBJECT_INVALID")
    body = {key: item for key, item in value.items() if key != "sealed"}
    if value["sealed"] != sha256_bytes(canonical(body)):
        raise MultiplicityError("SEALED_OBJECT_INVALID")
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
        raise MultiplicityError("CANONICAL_JSON_INVALID") from exc
    if not isinstance(value, dict) or raw != canonical(value) + b"\n":
        raise MultiplicityError("CANONICAL_JSON_INVALID")
    return value


def write_json_immutable(path: Path, value: object) -> None:
    data = canonical(value) + b"\n"
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise MultiplicityError("IMMUTABLE_OUTPUT_CONFLICT")
        return
    if len(data) > 4 * 1024 * 1024:
        raise MultiplicityError("RESOURCE_LIMIT_EXCEEDED")
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def audit_implementation_aggregate() -> str:
    return sha256_bytes(canonical({path: file_sha256(PROJECT / path)
                                   for path in AUDIT_IMPLEMENTATION_FILES}))


@dataclass(frozen=True, order=True)
class GlobalBrickIdentity:
    brickname: bytes
    brickid: int

    def __post_init__(self) -> None:
        try:
            validate_brickname(self.brickname)
        except Exception as exc:
            raise MultiplicityError("IDENTITY_INVALID") from exc
        if type(self.brickid) is not int:
            raise MultiplicityError("IDENTITY_INVALID")

    @property
    def text_name(self) -> str:
        return self.brickname.decode("ascii")


@dataclass(frozen=True)
class RootBrick:
    identity: GlobalBrickIdentity
    geometry: tuple[float, float, float, float, float, float]


@dataclass(frozen=True)
class RegionalBrickView:
    observer_domain: str
    identity: GlobalBrickIdentity
    geometry: tuple[float, float, float, float, float, float]
    technically_valid: bool = True

    def __post_init__(self) -> None:
        if self.observer_domain not in ("north", "south") or type(self.technically_valid) is not bool:
            raise MultiplicityError("OBSERVER_DOMAIN_INVALID")


@dataclass(frozen=True)
class RelationEntry:
    identity: GlobalBrickIdentity
    category: str
    views: tuple[RegionalBrickView, ...]
    fixture_excluded: bool


@dataclass
class AccessCounters:
    network_requests: int = 0
    network_body_bytes: int = 0
    PHOTSYS_reads: int = 0
    Tractor_cells_read: int = 0
    source_rows_read: int = 0
    image_pixels_read: int = 0
    morphology_accesses: int = 0
    label_accesses: int = 0
    allowed_identity_geometry_cells_decoded: int = 0
    opaque_provider_bytes_transited: int = 0
    local_io_bytes: int = 0

    def require_clean(self) -> None:
        forbidden = (self.network_requests, self.network_body_bytes, self.PHOTSYS_reads,
                     self.Tractor_cells_read, self.source_rows_read, self.image_pixels_read,
                     self.morphology_accesses, self.label_accesses)
        if any(forbidden):
            raise MultiplicityError("FIELD_FIREWALL_VIOLATION")
        if self.local_io_bytes > 1024 * 1024 * 1024:
            raise MultiplicityError("RESOURCE_LIMIT_EXCEEDED")

    def object(self) -> dict[str, int]:
        return {key: getattr(self, key) for key in self.__dataclass_fields__}


def _valid_geometry(geometry: Sequence[float]) -> bool:
    if len(geometry) != 6 or any(type(value) is not float or not math.isfinite(value) for value in geometry):
        return False
    ra, dec, ra1, ra2, dec1, dec2 = geometry
    return (0 <= ra < 360 and -90 <= dec <= 90 and 0 <= ra1 <= 360 and
            0 <= ra2 <= 360 and -90 <= dec1 <= dec2 <= 90)


def _unique_root(rows: Iterable[RootBrick]) -> tuple[tuple[RootBrick, ...], dict[GlobalBrickIdentity, RootBrick]]:
    values = tuple(rows)
    by_name: dict[bytes, RootBrick] = {}
    by_id: dict[int, RootBrick] = {}
    by_pair: dict[GlobalBrickIdentity, RootBrick] = {}
    for row in values:
        if not _valid_geometry(row.geometry):
            raise MultiplicityError("ROOT_GEOMETRY_INVALID")
        if row.identity.brickname in by_name or row.identity.brickid in by_id or row.identity in by_pair:
            raise MultiplicityError("ROOT_IDENTITY_DUPLICATE")
        by_name[row.identity.brickname] = row
        by_id[row.identity.brickid] = row
        by_pair[row.identity] = row
    return values, by_pair


def _unique_regional(rows: Iterable[RegionalBrickView], domain: str,
                     roots: Mapping[GlobalBrickIdentity, RootBrick]) -> dict[GlobalBrickIdentity, RegionalBrickView]:
    by_name: set[bytes] = set()
    by_id: set[int] = set()
    result: dict[GlobalBrickIdentity, RegionalBrickView] = {}
    for row in tuple(rows):
        if row.observer_domain != domain:
            raise MultiplicityError("OBSERVER_DOMAIN_INVALID")
        if (row.identity.brickname in by_name or row.identity.brickid in by_id or
                row.identity in result):
            raise MultiplicityError("REGIONAL_IDENTITY_DUPLICATE")
        root = roots.get(row.identity)
        if root is None:
            raise MultiplicityError("REGIONAL_ROOT_IDENTITY_MISMATCH")
        if not _valid_geometry(row.geometry) or row.geometry != root.geometry:
            raise MultiplicityError("REGIONAL_ROOT_GEOMETRY_MISMATCH")
        by_name.add(row.identity.brickname)
        by_id.add(row.identity.brickid)
        result[row.identity] = row
    return result


def build_global_view_relation(root_rows: Iterable[RootBrick],
                               north_rows: Iterable[RegionalBrickView],
                               south_rows: Iterable[RegionalBrickView],
                               fixture_identities: Iterable[GlobalBrickIdentity] = ()) -> tuple[
                                   tuple[RelationEntry, ...], dict[str, int]]:
    roots, root_index = _unique_root(root_rows)
    north = _unique_regional(north_rows, "north", root_index)
    south = _unique_regional(south_rows, "south", root_index)
    fixtures = frozenset(fixture_identities)
    if not fixtures.issubset(root_index):
        raise MultiplicityError("FIXTURE_ROOT_BINDING_FAILURE")
    counts = {
        "global_identities_total": len(roots), "north_present": len(north),
        "south_present": len(south), "north_only": 0, "south_only": 0,
        "both": 0, "no_regional_view": 0, "identity_conflicts": 0,
        "geometry_conflicts": 0, "fixture_exclusions": len(fixtures),
    }
    entries = []
    for root in sorted(roots, key=lambda row: (row.identity.brickname, row.identity.brickid)):
        views = tuple(view for view in (north.get(root.identity), south.get(root.identity)) if view is not None)
        domains = {view.observer_domain for view in views}
        if domains == {"north", "south"}:
            category = VIEW_BOTH; counts["both"] += 1
        elif domains == {"north"}:
            category = VIEW_NORTH_ONLY; counts["north_only"] += 1
        elif domains == {"south"}:
            category = VIEW_SOUTH_ONLY; counts["south_only"] += 1
        else:
            category = VIEW_NONE; counts["no_regional_view"] += 1
        entries.append(RelationEntry(root.identity, category, views, root.identity in fixtures))
    return tuple(entries), counts


def global_selection_hash_bytes(identity: GlobalBrickIdentity) -> bytes:
    return (f"{SELECTION_PREFIX}\nbrickname={identity.text_name}\n"
            f"brickid={identity.brickid}\n").encode("ascii")


def select_global_identities(entries: Iterable[RelationEntry], count: int) -> tuple[RelationEntry, ...]:
    if type(count) is not int or count < 1:
        raise MultiplicityError("SELECTION_COUNT_INVALID")
    eligible = tuple(entry for entry in entries if not entry.fixture_excluded and entry.views)
    if len(eligible) < count:
        raise MultiplicityError("SELECTION_CARDINALITY_INSUFFICIENT")
    return tuple(sorted(eligible, key=lambda entry: (
        sha256_bytes(global_selection_hash_bytes(entry.identity)),
        entry.identity.brickname, entry.identity.brickid,
    ))[:count])


def retain_all_valid_views(selected: Iterable[RelationEntry]) -> tuple[RegionalBrickView, ...]:
    result = []
    seen: set[tuple[GlobalBrickIdentity, str]] = set()
    for entry in selected:
        for view in entry.views:
            key = (entry.identity, view.observer_domain)
            if view.identity != entry.identity or key in seen:
                raise MultiplicityError("VIEW_RELATION_INVALID")
            seen.add(key)
            if view.technically_valid:
                result.append(view)
    return tuple(result)


def validate_selection_contract(fields: Iterable[str]) -> None:
    normalized = tuple(str(field).lower() for field in fields)
    if normalized != ("brickname", "brickid") or any(
            field in ("region", "observer_domain", "north", "south", "balance", "quota")
            for field in normalized):
        raise MultiplicityError("OBSERVER_DOMAIN_SELECTION_FORBIDDEN")


def validate_observer_domain_role(role: str) -> None:
    if role not in ("PROVENANCE", "CONFOUND_AUDIT", "REPLICATION_AUDIT"):
        raise MultiplicityError("OBSERVER_DOMAIN_ROLE_FORBIDDEN")


def validate_split_assignments(rows: Iterable[tuple[str | None, str]], *, confirmatory: bool) -> None:
    groups: dict[str, str] = {}
    for group_id, split in rows:
        if group_id is None:
            if confirmatory:
                raise MultiplicityError("UNRESOLVED_GROUPING_BLOCKS_CONFIRMATORY_SPLIT")
            continue
        if group_id in groups and groups[group_id] != split:
            raise MultiplicityError("SPLIT_GROUP_LEAKAGE")
        groups[group_id] = split


def validate_authority_bindings() -> list[dict[str, object]]:
    bindings = []
    for role, (path, expected_size, expected_sha, physical_role) in AUTHORITIES.items():
        if not path.is_file() or path.is_symlink():
            raise MultiplicityError("INPUT_AUTHORITY_MISMATCH")
        size = path.stat().st_size
        if expected_size is not None and size != expected_size:
            raise MultiplicityError("INPUT_AUTHORITY_MISMATCH")
        if file_sha256(path) != expected_sha:
            raise MultiplicityError("INPUT_AUTHORITY_MISMATCH")
        if physical_role is not None:
            contract = PRODUCTION_PHYSICAL_CONTRACTS[physical_role]
            if contract.expected_provider_full_file_sha256 != expected_sha:
                raise MultiplicityError("INPUT_AUTHORITY_MISMATCH")
        bindings.append({"path": str(path.relative_to(PROJECT)), "role": role,
                         "sha256": expected_sha, "size": size})
    if not SPEC_PATH.is_file() or file_sha256(SPEC_PATH) != SPEC_SHA256:
        raise MultiplicityError("INPUT_AUTHORITY_MISMATCH")
    return bindings


def _decode_cell(data: bytes, base: int, layout: tuple[int, int, str]):
    offset, width, tform = layout
    raw = data[base + offset:base + offset + width]
    if len(raw) != width:
        raise MultiplicityError("SELECTIVE_DECODE_TRUNCATED")
    if tform == "8A":
        validate_brickname(bytes(raw)); return bytes(raw)
    if tform == "J":
        return struct.unpack(">i", raw)[0]
    if tform == "D":
        return struct.unpack(">d", raw)[0]
    raise MultiplicityError("FIELD_LAYOUT_FAILURE")


def _decode_summary(path: Path, role: PhysicalRole, fields: tuple[str, ...],
                    counters: AccessCounters) -> tuple[tuple[object, ...], ...]:
    contract = PRODUCTION_PHYSICAL_CONTRACTS[role]
    compressed = path.read_bytes()
    counters.local_io_bytes += len(compressed)
    try:
        data = gzip.decompress(compressed) if contract.compression == "gzip" else compressed
    except (OSError, EOFError) as exc:
        raise MultiplicityError("FITS_DECOMPRESSION_FAILURE") from exc
    counters.local_io_bytes += len(data)
    counters.opaque_provider_bytes_transited += contract.naxis1 * contract.naxis2
    counters.require_clean()
    try:
        start, count, offsets = _validate_table(data, contract)
    except Exception as exc:
        raise MultiplicityError("PHYSICAL_CONTRACT_FAILURE") from exc
    layout_all = {name: (offset, width, tform) for offset, width, tform, name in offsets}
    if len(layout_all) != len(offsets) or any(field not in layout_all for field in fields):
        raise MultiplicityError("FIELD_LAYOUT_FAILURE")
    if any(token in field.lower() for field in fields for token in FORBIDDEN_FIELD_TOKENS):
        raise MultiplicityError("FIELD_FIREWALL_VIOLATION")
    rows = []
    for index in range(count):
        base = start + contract.naxis1 * index
        rows.append(tuple(_decode_cell(data, base, layout_all[field]) for field in fields))
    counters.allowed_identity_geometry_cells_decoded += count * len(fields)
    return tuple(rows)


def decode_local_authorities(counters: AccessCounters) -> tuple[
        tuple[RootBrick, ...], tuple[RegionalBrickView, ...], tuple[RegionalBrickView, ...]]:
    root_raw = _decode_summary(AUTHORITIES["ROOT_SUMMARY"][0], PhysicalRole.ROOT_SUMMARY,
                               ROOT_FIELDS, counters)
    north_raw = _decode_summary(AUTHORITIES["NORTH_SUMMARY"][0], PhysicalRole.NORTH_SUMMARY,
                                REGIONAL_FIELDS, counters)
    south_raw = _decode_summary(AUTHORITIES["SOUTH_SUMMARY"][0], PhysicalRole.SOUTH_SUMMARY,
                                REGIONAL_FIELDS, counters)
    roots = tuple(RootBrick(GlobalBrickIdentity(row[0], row[1]), tuple(row[2:])) for row in root_raw)
    north = tuple(RegionalBrickView("north", GlobalBrickIdentity(row[0], row[1]), tuple(row[2:]))
                  for row in north_raw)
    south = tuple(RegionalBrickView("south", GlobalBrickIdentity(row[0], row[1]), tuple(row[2:]))
                  for row in south_raw)
    return roots, north, south


def load_fixture_identities(root_rows: Iterable[RootBrick]) -> frozenset[GlobalBrickIdentity]:
    by_name = {row.identity.brickname: row.identity for row in root_rows}
    try:
        with FIXTURE_PATH.open("r", encoding="ascii", newline="") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames != ["region", "brickname", "development", "holdout_disjoint", "evidence_ref"]:
                raise MultiplicityError("FIXTURE_ROOT_BINDING_FAILURE")
            names = []
            for row in reader:
                if (set(row) != set(reader.fieldnames) or row["region"] not in ("north", "south") or
                        row["development"] != "true" or row["holdout_disjoint"] != "true" or
                        not row["evidence_ref"]):
                    raise MultiplicityError("FIXTURE_ROOT_BINDING_FAILURE")
                names.append(validate_brickname(row["brickname"].encode("ascii")).raw)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise MultiplicityError("FIXTURE_ROOT_BINDING_FAILURE") from exc
    try:
        return frozenset(by_name[name] for name in names)
    except KeyError as exc:
        raise MultiplicityError("FIXTURE_ROOT_BINDING_FAILURE") from exc


def run_local_relation_audit(output_directory: Path) -> dict[str, object]:
    bindings = validate_authority_bindings()
    counters = AccessCounters()
    roots, north, south = decode_local_authorities(counters)
    fixtures = load_fixture_identities(roots)
    entries, aggregate = build_global_view_relation(roots, north, south, fixtures)
    counters.require_clean()
    if aggregate["identity_conflicts"] or aggregate["geometry_conflicts"]:
        raise MultiplicityError("RELATION_CONFLICT")
    output_directory = Path(output_directory)
    input_binding = sealed({
        "authorities": bindings, "decoded_fields": {
            "ROOT_SUMMARY": list(ROOT_FIELDS), "NORTH_SUMMARY": list(REGIONAL_FIELDS),
            "SOUTH_SUMMARY": list(REGIONAL_FIELDS),
        }, "scope": SCOPE, "stage_id": STAGE_ID,
    })
    aggregate_evidence = sealed({
        "aggregate": aggregate, "counters": counters.object(),
        "relation_entry_count": len(entries), "scope": SCOPE, "stage_id": STAGE_ID,
    })
    terminal = sealed({
        "aggregate_sha256": sha256_bytes(canonical(aggregate_evidence) + b"\n"),
        "counters": counters.object(), "scope": SCOPE, "stage_id": STAGE_ID,
        "state": SUCCESS_TERMINAL,
    })
    write_json_immutable(output_directory / "INPUT_BINDING.json", input_binding)
    write_json_immutable(output_directory / "AGGREGATE_EVIDENCE.json", aggregate_evidence)
    write_json_immutable(output_directory / "TERMINAL.json", terminal)
    return terminal
