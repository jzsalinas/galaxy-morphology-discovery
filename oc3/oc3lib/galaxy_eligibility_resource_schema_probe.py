"""Bounded OC-3 galaxy-eligibility panel binding and gated schema probe.

P0 is deliberately offline and observes only the frozen technical cells from
the local DR9 brick summaries.  P1 transport is constructed only after a
separate final authorization binds a sealed candidate.  The real P1 path is
not exercised by importing this module or by running P0.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import csv
import gzip
import hashlib
import http.client
import io
import json
import math
import os
from pathlib import Path
import re
import resource
import struct
import threading
import time
from types import MappingProxyType
from typing import Callable, Iterable, Sequence
from urllib.parse import urljoin, urlsplit

from .core import canonical, implementation_hash
from .metadata_value_semantics import validate_brickname
from .patch_metadata_decode import ResourceAccounting, _validate_table
from .provider_physical_contracts import (
    PRODUCTION_PHYSICAL_CONTRACTS,
    FrozenPhysicalContract,
    PhysicalRole,
)
from .provider_schema import grz_median_present_v1


STAGE_ID = "OC3-GALAXY-ELIGIBILITY-RESOURCE-SCHEMA-PROBE-001"
SCOPE = "DOCUMENTARY_RESOURCE_SCHEMA_PROBE_ONLY"
PANEL_VERSION = "OC3_GALAXY_ELIGIBILITY_PANEL_V1"
ELIGIBILITY_RULE_VERSION = "OC3_GALAXY_ELIGIBILITY_TECHNICAL_ELIGIBILITY_V1"
P0_SUCCESS_TERMINAL = "GALAXY_ELIGIBILITY_PANEL_BOUND"
P0_FAILURE_TERMINAL = "GALAXY_ELIGIBILITY_PANEL_BINDING_FAILED"
P1_SUCCESS_TERMINAL = "GALAXY_ELIGIBILITY_RESOURCE_SCHEMA_PROBE_RESOLVED"
P1_INCONCLUSIVE_TERMINAL = "GALAXY_ELIGIBILITY_RESOURCE_SCHEMA_PROBE_INCONCLUSIVE"
FIREWALL_UNAVAILABLE = "TRACTOR_SELECTIVE_COLUMN_FIREWALL_UNAVAILABLE"
SPEC_SHA256 = "db80f8fefda0aad4a7e1cea4fb3e32bca0f238d33d2a52cbaf72af5da9ec5f17"

PROJECT = Path("/home/jzsalinas/Documents/galaxy-morphology-discovery")
ATTEMPT = PROJECT / "oc3/metadata_bootstrap/OC3-METADATA-BOOTSTRAP-001"
ROOT_PATH = ATTEMPT / "RAW_IMMUTABLE/ROOT_SUMMARY/survey-bricks.fits.gz"
NORTH_PATH = ATTEMPT / "RAW_IMMUTABLE/NORTH_SUMMARY/survey-bricks-dr9-north.fits.gz"
SOUTH_PATH = ATTEMPT / "RAW_IMMUTABLE/SOUTH_SUMMARY/survey-bricks-dr9-south.fits.gz"
FIXTURE_PATH = PROJECT / "oc3/INPUTS/OC3_DEVELOPMENT_BRICKS.csv"
DOCUMENTARY_MANIFEST_PATH = PROJECT / "oc3/INPUTS/OC3_GALAXY_ELIGIBILITY_DOCUMENTARY_MANIFEST_001.json"
PANEL_MANIFEST_PATH = PROJECT / "oc3/INPUTS/OC3_GALAXY_ELIGIBILITY_PANEL_MANIFEST.json"
P1_CANDIDATE_PATH = PROJECT / "oc3/INPUTS/OC3_GALAXY_ELIGIBILITY_P1_AUTHORIZATION_CANDIDATE_001.json"
RUN_DIRECTORY = PROJECT / "oc3/galaxy_eligibility_resource_schema_probe" / STAGE_ID

EXPECTED_AUTHORITIES = MappingProxyType({
    "ROOT_SUMMARY": (ROOT_PATH, "dc943d702357f93553b9e5d15e87ace38df94eb7095f4100657407b3f9919c5f"),
    "NORTH_SUMMARY": (NORTH_PATH, "2edd5c295fdad26852c6f224a3ff023cff43dd0e03a53acd35b767e726ee72fb"),
    "SOUTH_SUMMARY": (SOUTH_PATH, "7360414f5d53571ca70fa0cb483eb8c80cfcbe80df0856a117246f442a0b9a3f"),
    "DEVELOPMENT_FIXTURES": (FIXTURE_PATH, "147c0942a5340ed18eec23a610f8afd5721390fad09c1da7ed01593deb40fab6"),
})

ROOT_ALLOWED_FIELDS = ("BRICKNAME", "BRICKID", "RA", "DEC", "RA1", "RA2", "DEC1", "DEC2")
REGIONAL_ALLOWED_FIELDS = (
    "brickname", "brickid", "ra", "dec", "ra1", "ra2", "dec1", "dec2",
    "area", "survey_primary", "nexp_g", "nexp_r", "nexp_z",
)
A_CORE = ("RELEASE", "BRICKID", "OBJID", "BRICKNAME", "BRICK_PRIMARY", "RA", "DEC", "BX", "BY")
C1_EXTENSION = (
    "REF_CAT", "REF_ID", "REF_EPOCH", "PARALLAX", "PARALLAX_IVAR", "PMRA",
    "PMRA_IVAR", "PMDEC", "PMDEC_IVAR", "GAIA_ASTROMETRIC_PARAMS_SOLVED",
)
TRACTOR_ALLOWLIST = frozenset(A_CORE + C1_EXTENSION)
TRACTOR_DENYLIST = frozenset(("TYPE", "DCHISQ", "SERSIC", "SHAPE_R", "SHAPE_E1", "SHAPE_E2"))

TRACTOR_BASE = "https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9"
P1_SPEC_MAXIMA = MappingProxyType({
    "requests": 96,
    "body_bytes": 16 * 1024 * 1024,
    "per_resource_range_bytes": 512 * 1024,
    "concurrency": 4,
    "automatic_retries_per_resource": 1,
    "redirects_per_request": 3,
})
FIRST_P1_POLICY = MappingProxyType({
    "concurrency": 1,
    "automatic_retries_per_resource": 0,
    "redirects_per_request": 3,
})
P0_CAPS = MappingProxyType({
    "network_requests": 0,
    "network_body_bytes": 0,
    "local_io_bytes": 1024 * 1024 * 1024,
    "ram_bytes": 2 * 1024 * 1024 * 1024,
    "threads": 1,
    "compute_seconds": 300,
    "wall_seconds": 900,
    "output_bytes": 4 * 1024 * 1024,
})

P0_FILES = (
    "P0_INPUT_BINDING.json",
    "P0_AGGREGATE_EVIDENCE.json",
    "P0_TERMINAL.json",
    "P0_RUN.log",
)


class EligibilityProbeError(Exception):
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


def object_seal(value: object) -> str:
    return sha256_bytes(canonical(value))


def sealed_object(value: dict[str, object]) -> dict[str, object]:
    if "sealed" in value:
        raise EligibilityProbeError("SEAL_INPUT_INVALID")
    result = dict(value)
    result["sealed"] = object_seal(value)
    return result


def validate_sealed(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) == {"sealed"}:
        raise EligibilityProbeError("SEALED_OBJECT_INVALID")
    seal = value.get("sealed")
    body = {key: item for key, item in value.items() if key != "sealed"}
    if not isinstance(seal, str) or seal != object_seal(body):
        raise EligibilityProbeError("SEALED_OBJECT_INVALID")
    return value


def canonical_json_bytes(value: object) -> bytes:
    return canonical(value) + b"\n"


def write_immutable(path: Path, data: bytes) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise EligibilityProbeError("IMMUTABLE_OUTPUT_CONFLICT")
        return
    if len(data) > P0_CAPS["output_bytes"]:
        raise EligibilityProbeError("P0_OUTPUT_LIMIT")
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def write_json_immutable(path: Path, value: object) -> None:
    write_immutable(path, canonical_json_bytes(value))


def load_canonical_json(path: Path) -> dict[str, object]:
    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        raise EligibilityProbeError("CANONICAL_JSON_INVALID") from exc
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_strict_object)
    except (UnicodeError, ValueError) as exc:
        raise EligibilityProbeError("CANONICAL_JSON_INVALID") from exc
    if not isinstance(value, dict) or raw != canonical_json_bytes(value):
        raise EligibilityProbeError("CANONICAL_JSON_INVALID")
    return value


def _strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


@dataclass
class Tripwires:
    forbidden_field_observations: int = 0
    forbidden_value_decode_count: int = 0
    forbidden_value_materialization_count: int = 0
    forbidden_value_serialization_count: int = 0
    forbidden_value_log_count: int = 0
    morphology_label_accesses: int = 0

    def object(self) -> dict[str, int]:
        return {key: getattr(self, key) for key in (
            "forbidden_field_observations", "forbidden_value_decode_count",
            "forbidden_value_materialization_count", "forbidden_value_serialization_count",
            "forbidden_value_log_count", "morphology_label_accesses",
        )}

    def require_zero(self) -> None:
        if any(self.object().values()):
            raise EligibilityProbeError("FIELD_FIREWALL_TRIPWIRE")


@dataclass
class P0Observation:
    decoded_fields: dict[str, tuple[str, ...]] = field(default_factory=lambda: {
        "ROOT_SUMMARY": ROOT_ALLOWED_FIELDS,
        "NORTH_SUMMARY": REGIONAL_ALLOWED_FIELDS,
        "SOUTH_SUMMARY": REGIONAL_ALLOWED_FIELDS,
    })
    allowed_cell_values_decoded: int = 0
    opaque_provider_bytes_transited: int = 0
    tripwires: Tripwires = field(default_factory=Tripwires)

    def object(self) -> dict[str, object]:
        return {
            "allowed_cell_values_decoded": self.allowed_cell_values_decoded,
            "decoded_fields": {key: list(value) for key, value in sorted(self.decoded_fields.items())},
            "opaque_provider_bytes_transited": self.opaque_provider_bytes_transited,
            "tripwires": self.tripwires.object(),
        }


@dataclass(frozen=True)
class RootRow:
    brickname: bytes
    brickid: int
    geometry: tuple[float, float, float, float, float, float]


@dataclass(frozen=True)
class RegionalRow:
    region: str
    brickname: bytes
    brickid: int
    geometry: tuple[float, float, float, float, float, float]
    area: float
    survey_primary: bool
    nexp: tuple[int, int, int]


@dataclass(frozen=True)
class PanelCandidate:
    region: str
    brickname: str
    brickid: int

    @property
    def hash_bytes(self) -> bytes:
        return (
            f"OC3-GALAXY-ELIGIBILITY-PANEL-V1\n"
            f"region={self.region}\n"
            f"brickname={self.brickname}\n"
            f"brickid={self.brickid}\n"
        ).encode("utf-8")

    @property
    def selection_sha256(self) -> str:
        return sha256_bytes(self.hash_bytes)

    def object(self, panel_index: int) -> dict[str, object]:
        return {
            "brickid": self.brickid,
            "brickname": self.brickname,
            "panel_index": panel_index,
            "region": self.region,
            "selection_sha256": self.selection_sha256,
        }


class P0Guard:
    def __init__(self) -> None:
        self.wall_start = time.monotonic()
        self.cpu_start = time.process_time()

    def check(self) -> None:
        if (time.monotonic() - self.wall_start > P0_CAPS["wall_seconds"] or
                time.process_time() - self.cpu_start > P0_CAPS["compute_seconds"] or
                threading.active_count() > P0_CAPS["threads"]):
            raise EligibilityProbeError("P0_RESOURCE_LIMIT")
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        peak_bytes = peak * 1024 if peak < 2**40 else peak
        if peak_bytes > P0_CAPS["ram_bytes"]:
            raise EligibilityProbeError("P0_RESOURCE_LIMIT")

    def elapsed(self) -> tuple[int, int]:
        return int(time.monotonic() - self.wall_start), int(time.process_time() - self.cpu_start)


class P0Accounting(ResourceAccounting):
    def __init__(self) -> None:
        super().__init__()
        self.guard = P0Guard()

    def charge_io(self, amount: int) -> None:
        if type(amount) is not int or amount < 0 or self.local_io_bytes + amount > P0_CAPS["local_io_bytes"]:
            raise EligibilityProbeError("P0_RESOURCE_LIMIT")
        self.local_io_bytes += amount


def validate_authorities(accounting: P0Accounting | None = None) -> dict[str, object]:
    accounting = accounting or P0Accounting()
    rows = []
    for role, (path, expected) in EXPECTED_AUTHORITIES.items():
        if not path.is_file() or path.is_symlink():
            raise EligibilityProbeError("P0_AUTHORITY_BINDING_FAILURE")
        observed = accounting.hash_file(path)
        if observed != expected:
            raise EligibilityProbeError("P0_AUTHORITY_BINDING_FAILURE")
        rows.append({"path": str(path.relative_to(PROJECT)), "role": role, "sha256": observed})
    if file_sha256(PROJECT / "OC3_GALAXY_ELIGIBILITY_BOUNDED_EVIDENCE_SPEC.md") != SPEC_SHA256:
        raise EligibilityProbeError("P0_AUTHORITY_BINDING_FAILURE")
    contracts = {
        PhysicalRole.ROOT_SUMMARY: EXPECTED_AUTHORITIES["ROOT_SUMMARY"][1],
        PhysicalRole.NORTH_SUMMARY: EXPECTED_AUTHORITIES["NORTH_SUMMARY"][1],
        PhysicalRole.SOUTH_SUMMARY: EXPECTED_AUTHORITIES["SOUTH_SUMMARY"][1],
    }
    for role, expected in contracts.items():
        if PRODUCTION_PHYSICAL_CONTRACTS[role].expected_provider_full_file_sha256 != expected:
            raise EligibilityProbeError("P0_PHYSICAL_CONTRACT_FAILURE")
    return {"authorities": rows, "specification_sha256": SPEC_SHA256}


def load_fixture_exclusions(path: Path = FIXTURE_PATH) -> frozenset[tuple[str, str]]:
    try:
        with Path(path).open("r", encoding="ascii", newline="") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames != ["region", "brickname", "development", "holdout_disjoint", "evidence_ref"]:
                raise EligibilityProbeError("P0_FIXTURE_SCHEMA_FAILURE")
            rows = tuple(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise EligibilityProbeError("P0_FIXTURE_SCHEMA_FAILURE") from exc
    exclusions = set()
    for row in rows:
        if (set(row) != set(reader.fieldnames) or row["region"] not in ("north", "south") or
                row["development"] != "true" or row["holdout_disjoint"] != "true" or
                not row["evidence_ref"]):
            raise EligibilityProbeError("P0_FIXTURE_SCHEMA_FAILURE")
        name = validate_brickname(row["brickname"].encode("ascii")).value
        if (row["region"], name) in exclusions:
            raise EligibilityProbeError("P0_FIXTURE_SCHEMA_FAILURE")
        exclusions.add((row["region"], name))
    if not exclusions:
        raise EligibilityProbeError("P0_FIXTURE_SCHEMA_FAILURE")
    return frozenset(exclusions)


def _decode_cell(data: bytes, base: int, layout: tuple[int, int, str]):
    offset, width, tform = layout
    raw = data[base + offset:base + offset + width]
    if len(raw) != width:
        raise EligibilityProbeError("P0_SELECTIVE_DECODE_TRUNCATED")
    if tform == "8A":
        validate_brickname(bytes(raw))
        return bytes(raw)
    if tform == "J":
        return struct.unpack(">i", raw)[0]
    if tform == "I":
        return struct.unpack(">h", raw)[0]
    if tform == "D":
        return struct.unpack(">d", raw)[0]
    if tform == "L":
        if raw == b"T":
            return True
        if raw == b"F":
            return False
        raise EligibilityProbeError("P0_LOGICAL_VALUE_INVALID")
    raise EligibilityProbeError("P0_FIELD_LAYOUT_FAILURE")


def _load_fits_bytes(path: Path, contract: FrozenPhysicalContract, accounting: P0Accounting) -> bytes:
    compressed = accounting.read_bytes(path)
    try:
        data = gzip.decompress(compressed) if contract.compression == "gzip" else compressed
    except (OSError, EOFError) as exc:
        raise EligibilityProbeError("P0_FITS_DECOMPRESSION_FAILURE") from exc
    accounting.charge_io(len(data))
    accounting.check()
    return data


def _selected_layout(data: bytes, contract: FrozenPhysicalContract,
                     fields: tuple[str, ...]) -> tuple[int, int, dict[str, tuple[int, int, str]]]:
    try:
        data_start, nrows, offsets = _validate_table(data, contract)
    except Exception as exc:
        raise EligibilityProbeError("P0_PHYSICAL_CONTRACT_FAILURE") from exc
    all_layout = {name: (offset, width, tform) for offset, width, tform, name in offsets}
    if len(all_layout) != len(offsets) or any(name not in all_layout for name in fields):
        raise EligibilityProbeError("P0_FIELD_LAYOUT_FAILURE")
    return data_start, nrows, {name: all_layout[name] for name in fields}


def decode_root(path: Path, accounting: P0Accounting,
                observation: P0Observation) -> tuple[RootRow, ...]:
    contract = PRODUCTION_PHYSICAL_CONTRACTS[PhysicalRole.ROOT_SUMMARY]
    data = _load_fits_bytes(path, contract, accounting)
    start, count, layout = _selected_layout(data, contract, ROOT_ALLOWED_FIELDS)
    rows = []
    for index in range(count):
        if index % 8192 == 0:
            accounting.check()
        base = start + contract.naxis1 * index
        values = {name: _decode_cell(data, base, layout[name]) for name in ROOT_ALLOWED_FIELDS}
        rows.append(RootRow(values["BRICKNAME"], values["BRICKID"], tuple(
            values[name] for name in ("RA", "DEC", "RA1", "RA2", "DEC1", "DEC2"))))
    observation.allowed_cell_values_decoded += count * len(ROOT_ALLOWED_FIELDS)
    observation.opaque_provider_bytes_transited += contract.naxis1 * count
    return tuple(rows)


def decode_regional(path: Path, region: str, accounting: P0Accounting,
                    observation: P0Observation) -> tuple[RegionalRow, ...]:
    role = PhysicalRole.NORTH_SUMMARY if region == "north" else PhysicalRole.SOUTH_SUMMARY
    contract = PRODUCTION_PHYSICAL_CONTRACTS[role]
    data = _load_fits_bytes(path, contract, accounting)
    start, count, layout = _selected_layout(data, contract, REGIONAL_ALLOWED_FIELDS)
    rows = []
    for index in range(count):
        if index % 8192 == 0:
            accounting.check()
        base = start + contract.naxis1 * index
        values = {name: _decode_cell(data, base, layout[name]) for name in REGIONAL_ALLOWED_FIELDS}
        rows.append(RegionalRow(
            region, values["brickname"], values["brickid"], tuple(
                values[name] for name in ("ra", "dec", "ra1", "ra2", "dec1", "dec2")),
            values["area"], values["survey_primary"],
            tuple(values[name] for name in ("nexp_g", "nexp_r", "nexp_z")),
        ))
    observation.allowed_cell_values_decoded += count * len(REGIONAL_ALLOWED_FIELDS)
    observation.opaque_provider_bytes_transited += contract.naxis1 * count
    return tuple(rows)


def _valid_geometry(values: tuple[float, ...], area: float | None = None) -> bool:
    if any(type(value) is not float or not math.isfinite(value) for value in values):
        return False
    ra, dec, ra1, ra2, dec1, dec2 = values
    if not (0 <= ra < 360 and -90 <= dec <= 90 and
            0 <= ra1 <= 360 and 0 <= ra2 <= 360 and
            -90 <= dec1 <= 90 and -90 <= dec2 <= 90 and dec1 <= dec2):
        return False
    return area is None or (type(area) is float and math.isfinite(area) and area > 0)


def selection_hash_bytes(region: str, brickname: str, brickid: int) -> bytes:
    if region not in ("north", "south") or isinstance(brickid, bool) or not isinstance(brickid, int):
        raise EligibilityProbeError("P0_HASH_INPUT_INVALID")
    validate_brickname(brickname.encode("ascii"))
    if str(brickid) != f"{brickid:d}":
        raise EligibilityProbeError("P0_HASH_INPUT_INVALID")
    return (
        "OC3-GALAXY-ELIGIBILITY-PANEL-V1\n"
        f"region={region}\n"
        f"brickname={brickname}\n"
        f"brickid={brickid}\n"
    ).encode("utf-8")


def select_panel(root_rows: Iterable[RootRow], north_rows: Iterable[RegionalRow],
                 south_rows: Iterable[RegionalRow], fixtures: frozenset[tuple[str, str]]) -> tuple[
                     tuple[PanelCandidate, ...], dict[str, object]]:
    roots = tuple(root_rows)
    if len({row.brickname for row in roots}) != len(roots) or len({row.brickid for row in roots}) != len(roots):
        raise EligibilityProbeError("P0_DUPLICATE_ROOT_IDENTITY")
    root_index = {row.brickname: row for row in roots}
    regional = {"north": tuple(north_rows), "south": tuple(south_rows)}
    combined = regional["north"] + regional["south"]
    if (len({row.brickname for row in combined}) != len(combined) or
            len({row.brickid for row in combined}) != len(combined)):
        raise EligibilityProbeError("P0_DUPLICATE_REGIONAL_IDENTITY")
    exclusions: dict[str, dict[str, int]] = {}
    selected = []
    all_hashes = set()
    for region in ("north", "south"):
        counters = {"input_rows": len(regional[region]), "invalid_geometry": 0,
                    "survey_primary_false": 0, "grz_absent": 0, "fixture_excluded": 0,
                    "eligible_rows": 0}
        eligible = []
        for row in regional[region]:
            if row.region != region:
                raise EligibilityProbeError("P0_REGION_BINDING_FAILURE")
            validated = validate_brickname(row.brickname)
            root = root_index.get(row.brickname)
            if root is None or root.brickid != row.brickid or root.geometry != row.geometry:
                raise EligibilityProbeError("P0_ROOT_REGIONAL_JOIN_FAILURE")
            if not _valid_geometry(root.geometry) or not _valid_geometry(row.geometry, row.area):
                counters["invalid_geometry"] += 1
                continue
            if row.survey_primary is not True:
                counters["survey_primary_false"] += 1
                continue
            try:
                grz = grz_median_present_v1(*row.nexp)
            except Exception as exc:
                raise EligibilityProbeError("P0_NEXP_SEMANTICS_FAILURE") from exc
            if not grz:
                counters["grz_absent"] += 1
                continue
            if (region, validated.value) in fixtures:
                counters["fixture_excluded"] += 1
                continue
            candidate = PanelCandidate(region, validated.value, row.brickid)
            if candidate.selection_sha256 in all_hashes:
                raise EligibilityProbeError("P0_SELECTION_HASH_COLLISION")
            all_hashes.add(candidate.selection_sha256)
            eligible.append(candidate)
        counters["eligible_rows"] = len(eligible)
        if len(eligible) < 8:
            raise EligibilityProbeError("P0_LOW_CARDINALITY")
        ordered = sorted(eligible, key=lambda item: (
            item.selection_sha256, item.brickname.encode("ascii"), item.brickid))
        selected.extend(ordered[:8])
        exclusions[region] = counters
    if len(selected) != 16 or sum(item.region == "north" for item in selected) != 8 or sum(
            item.region == "south" for item in selected) != 8:
        raise EligibilityProbeError("P0_PANEL_CARDINALITY_FAILURE")
    if any((item.region, item.brickname) in fixtures for item in selected):
        raise EligibilityProbeError("P0_FIXTURE_LEAK")
    return tuple(selected), {"regions": exclusions, "tie_count": 0}


def tractor_url(region: str, brickname: str) -> str:
    if region not in ("north", "south"):
        raise EligibilityProbeError("TRACTOR_RESOURCE_IDENTITY_INVALID")
    name = validate_brickname(brickname.encode("ascii")).value
    return f"{TRACTOR_BASE}/{region}/tractor/{name[:3]}/tractor-{name}.fits"


def build_panel_manifest(panel: Sequence[PanelCandidate], authority_binding: dict[str, object],
                         exclusions: dict[str, object], observation: P0Observation,
                         accounting: P0Accounting) -> dict[str, object]:
    if len(panel) != 16:
        raise EligibilityProbeError("P0_PANEL_CARDINALITY_FAILURE")
    rows = [candidate.object(index) for index, candidate in enumerate(panel)]
    body = {
        "authorities": authority_binding["authorities"],
        "eligibility_rule_version": ELIGIBILITY_RULE_VERSION,
        "fixture_exclusion_source_sha256": EXPECTED_AUTHORITIES["DEVELOPMENT_FIXTURES"][1],
        "network_body_bytes": 0,
        "network_requests": 0,
        "observation": observation.object(),
        "order_sha256": object_seal(rows),
        "panel": rows,
        "panel_size": 16,
        "panel_version": PANEL_VERSION,
        "regional_counts": {"north": 8, "south": 8},
        "selection_statistics": exclusions,
        "specification_sha256": authority_binding["specification_sha256"],
        "stage_id": STAGE_ID,
    }
    observation.tripwires.require_zero()
    return sealed_object(body)


def build_p1_candidate(panel_manifest: dict[str, object], panel_file_sha256: str,
                       documentary_manifest: dict[str, object], current_implementation: str) -> dict[str, object]:
    validate_sealed(panel_manifest)
    validate_sealed(documentary_manifest)
    panel = panel_manifest.get("panel")
    if not isinstance(panel, list) or len(panel) != 16:
        raise EligibilityProbeError("P1_CANDIDATE_PANEL_INVALID")
    tractor = []
    for row in panel:
        if not isinstance(row, dict):
            raise EligibilityProbeError("P1_CANDIDATE_PANEL_INVALID")
        url = tractor_url(row.get("region"), row.get("brickname"))
        tractor.append({
            "brickid": row.get("brickid"),
            "brickname": row.get("brickname"),
            "directory_component": row.get("brickname")[:3],
            "literal_url": url,
            "panel_index": row.get("panel_index"),
            "region": row.get("region"),
            "resource_role": "TRACTOR_CANDIDATE",
        })
    documents = documentary_manifest.get("resources")
    if not isinstance(documents, list) or not documents:
        raise EligibilityProbeError("P1_DOCUMENTARY_MANIFEST_INVALID")
    # No local authority binds the literal B1 paths.  The first candidate is
    # therefore restricted to resolving the documentary contract only.
    body = {
        "authorization_state": "FINAL_AUTHORIZATION_ABSENT",
        "b1_candidate_filenames": [
            "survey-dr9-north-specObj-dr16.fits",
            "survey-dr9-south-specObj-dr16.fits",
        ],
        "b1_literal_urls": [],
        "candidate_scope": "MINIMUM_DOCUMENTARY_BINDING_ONLY",
        "documentary_manifest_seal": documentary_manifest["sealed"],
        "documentary_resources": documents,
        "expected_tripwires": Tripwires().object(),
        "implementation_aggregate": current_implementation,
        "network_order": ["DOCUMENTARY_AUTHORITIES_IN_MANIFEST_ORDER"],
        "panel_manifest_seal": panel_manifest["sealed"],
        "panel_manifest_sha256": panel_file_sha256,
        "policy": {
            "automatic_retries_per_resource": 0,
            "body_bytes_cap": 1024 * 1024,
            "concurrency": 1,
            "per_resource_range_body_bytes": 512 * 1024,
            "redirects_per_request": 3,
            "request_cap": 8,
        },
        "resume_requires_separate_authorization": True,
        "scope": SCOPE,
        "stage_id": STAGE_ID,
        "success_terminal": P1_SUCCESS_TERMINAL,
        "inconclusive_terminal": P1_INCONCLUSIVE_TERMINAL,
        "tractor_resources_after_documentary_resolution": tractor,
    }
    return sealed_object(body)


def validate_documentary_manifest(path: Path = DOCUMENTARY_MANIFEST_PATH) -> dict[str, object]:
    value = validate_sealed(load_canonical_json(path))
    if (value.get("schema_version") != "OC3_GALAXY_ELIGIBILITY_DOCUMENTARY_MANIFEST_001" or
            value.get("stage_id") != STAGE_ID or value.get("broad_web_crawling") is not False):
        raise EligibilityProbeError("P1_DOCUMENTARY_MANIFEST_INVALID")
    resources = value.get("resources")
    if not isinstance(resources, list) or len(resources) != 2:
        raise EligibilityProbeError("P1_DOCUMENTARY_MANIFEST_INVALID")
    expected_roles = ("TRACTOR_CATALOG_AND_C1_SCHEMA", "B1_EXTERNAL_MATCH_FILES_AND_SEMANTICS")
    for row, role in zip(resources, expected_roles):
        if (not isinstance(row, dict) or row.get("retrieval_role") != role or
                row.get("provider") != "Legacy Surveys DR9" or
                row.get("resolution_state") != "UNRESOLVED_PENDING_AUTHORIZED_P1" or
                row.get("retrieval_timestamp_utc") is not None or
                row.get("content_sha256") is not None or
                row.get("max_body_bytes") != 512 * 1024 or
                not isinstance(row.get("url"), str) or not row["url"].startswith("https://www.legacysurvey.org/dr9/")):
            raise EligibilityProbeError("P1_DOCUMENTARY_MANIFEST_INVALID")
    return value


def validate_inputs() -> dict[str, object]:
    accounting = P0Accounting()
    authority = validate_authorities(accounting)
    fixtures = load_fixture_exclusions()
    documentary = validate_documentary_manifest()
    return {
        "authority_count": len(authority["authorities"]),
        "documentary_resource_count": len(documentary["resources"]),
        "fixture_count": len(fixtures),
        "local_io_bytes": accounting.local_io_bytes,
        "network_requests": 0,
        "scope": SCOPE,
        "stage_id": STAGE_ID,
        "state": "GALAXY_ELIGIBILITY_PROBE_INPUTS_VALID",
    }


def _publish_p0(panel_manifest: dict[str, object], binding: dict[str, object],
                aggregate: dict[str, object], terminal: dict[str, object],
                candidate: dict[str, object], panel_path: Path, run_directory: Path,
                candidate_path: Path) -> None:
    run_directory = Path(run_directory)
    if run_directory.exists() and not run_directory.is_dir():
        raise EligibilityProbeError("IMMUTABLE_OUTPUT_CONFLICT")
    log = (
        f"stage_id={STAGE_ID}\n"
        f"terminal={terminal['terminal']}\n"
        f"panel_size={panel_manifest['panel_size']}\n"
        f"north={panel_manifest['regional_counts']['north']}\n"
        f"south={panel_manifest['regional_counts']['south']}\n"
        "network_requests=0\n"
        "tractor_rows_decoded=0\n"
        "spectroscopy_rows_decoded=0\n"
        "gaia_rows_decoded=0\n"
        "forbidden_field_observations=0\n"
    ).encode("ascii")
    outputs = {
        run_directory / "P0_INPUT_BINDING.json": canonical_json_bytes(binding),
        run_directory / "P0_AGGREGATE_EVIDENCE.json": canonical_json_bytes(aggregate),
        run_directory / "P0_TERMINAL.json": canonical_json_bytes(terminal),
        run_directory / "P0_RUN.log": log,
        Path(panel_path): canonical_json_bytes(panel_manifest),
        Path(candidate_path): canonical_json_bytes(candidate),
    }
    for path, data in outputs.items():
        write_immutable(path, data)


def execute_p0(*, panel_path: Path = PANEL_MANIFEST_PATH,
               run_directory: Path = RUN_DIRECTORY,
               candidate_path: Path = P1_CANDIDATE_PATH,
               decoder: Callable | None = None,
               current_implementation: str | None = None) -> dict[str, object]:
    panel_path = Path(panel_path); run_directory = Path(run_directory); candidate_path = Path(candidate_path)
    if panel_path == PANEL_MANIFEST_PATH:
        if (panel_path.resolve() != PANEL_MANIFEST_PATH or run_directory.resolve() != RUN_DIRECTORY or
                candidate_path.resolve() != P1_CANDIDATE_PATH):
            raise EligibilityProbeError("P0_OUTPUT_PATH_BINDING_FAILURE")
    if panel_path.exists() or run_directory.exists() or candidate_path.exists():
        # A complete immutable result may be inspected, but P0 is never replayed.
        if panel_path.is_file() and candidate_path.is_file() and run_directory.is_dir() and all(
                (run_directory / name).is_file() for name in P0_FILES):
            panel = validate_sealed(load_canonical_json(panel_path))
            terminal = load_canonical_json(run_directory / "P0_TERMINAL.json")
            if terminal.get("terminal") == P0_SUCCESS_TERMINAL and panel.get("panel_size") == 16:
                return {"candidate": validate_sealed(load_canonical_json(candidate_path)),
                        "panel": panel, "terminal": terminal, "reused_existing": True}
        raise EligibilityProbeError("P0_PARTIAL_OR_CONFLICTING_OUTPUT")
    accounting = P0Accounting()
    observation = P0Observation()
    authority = validate_authorities(accounting)
    fixtures = load_fixture_exclusions()
    documentary = validate_documentary_manifest()
    decode = decoder
    if decode is None:
        roots = decode_root(ROOT_PATH, accounting, observation)
        north = decode_regional(NORTH_PATH, "north", accounting, observation)
        south = decode_regional(SOUTH_PATH, "south", accounting, observation)
    else:
        roots, north, south = decode(observation)
    panel, exclusions = select_panel(roots, north, south, fixtures)
    manifest = build_panel_manifest(panel, authority, exclusions, observation, accounting)
    implementation = current_implementation or implementation_hash(PROJECT)
    panel_bytes = canonical_json_bytes(manifest)
    candidate = build_p1_candidate(manifest, sha256_bytes(panel_bytes), documentary, implementation)
    wall, cpu = accounting.guard.elapsed()
    binding = sealed_object({
        "authorities": authority,
        "current_implementation_aggregate": implementation,
        "documentary_manifest_sha256": file_sha256(DOCUMENTARY_MANIFEST_PATH),
        "network_authorized": False,
        "panel_output": str(panel_path.relative_to(PROJECT)) if panel_path.is_relative_to(PROJECT) else str(panel_path),
        "scope": SCOPE,
        "stage_id": STAGE_ID,
    })
    aggregate = sealed_object({
        "allowed_summary_cell_values_decoded": observation.allowed_cell_values_decoded,
        "fixture_leak_count": 0,
        "local_io_bytes": accounting.local_io_bytes,
        "network_body_bytes": 0,
        "network_requests": 0,
        "north_count": 8,
        "observation": observation.object(),
        "panel_manifest_seal": manifest["sealed"],
        "panel_size": 16,
        "south_count": 8,
        "spectroscopy_rows_decoded": 0,
        "stage_id": STAGE_ID,
        "tractor_rows_decoded": 0,
        "gaia_rows_decoded": 0,
        "resource_usage": {"compute_seconds": cpu, "wall_seconds": wall},
    })
    terminal = {
        "first_error_code": None,
        "network_requests": 0,
        "panel_manifest_seal": manifest["sealed"],
        "stage_id": STAGE_ID,
        "successful": True,
        "terminal": P0_SUCCESS_TERMINAL,
        "tripwires": observation.tripwires.object(),
    }
    _publish_p0(manifest, binding, aggregate, terminal, candidate,
                panel_path, run_directory, candidate_path)
    return {"candidate": candidate, "panel": manifest, "terminal": terminal, "reused_existing": False}


def dry_run() -> dict[str, object]:
    if PANEL_MANIFEST_PATH.exists() or RUN_DIRECTORY.exists() or P1_CANDIDATE_PATH.exists():
        state = "P0_ALREADY_BOUND_NO_REPLAY"
    else:
        state = "GALAXY_ELIGIBILITY_PROBE_DRY_RUN_OK"
    validated = validate_inputs()
    return {
        "documentary_resource_count": validated["documentary_resource_count"],
        "network_requests": 0,
        "panel_size_planned": 16,
        "scope": SCOPE,
        "stage_id": STAGE_ID,
        "state": state,
    }


@dataclass(frozen=True)
class BintableColumn:
    name: str
    tform: str
    offset: int
    width: int


_TFORM = re.compile(r"^(\d*)([LXBIJKAEDCMPQ])(?:\([^)]*\))?$")
_TFORM_BITS = {"L": 8, "B": 8, "I": 16, "J": 32, "K": 64, "A": 8,
               "E": 32, "D": 64, "C": 64, "M": 128, "P": 64, "Q": 128}


def tform_width(tform: str) -> int:
    match = _TFORM.fullmatch(tform)
    if not match:
        raise EligibilityProbeError("FITS_TFORM_UNSUPPORTED")
    repeat = int(match.group(1) or "1")
    if repeat <= 0:
        raise EligibilityProbeError("FITS_TFORM_UNSUPPORTED")
    code = match.group(2)
    bits = repeat if code == "X" else repeat * _TFORM_BITS[code]
    return (bits + 7) // 8


def bintable_layout(names: Sequence[str], tforms: Sequence[str], row_width: int) -> tuple[BintableColumn, ...]:
    if len(names) != len(tforms) or not names or len(set(names)) != len(names):
        raise EligibilityProbeError("FITS_SCHEMA_INVALID")
    offset = 0; columns = []
    for name, tform in zip(names, tforms):
        if not isinstance(name, str) or not name or not isinstance(tform, str):
            raise EligibilityProbeError("FITS_SCHEMA_INVALID")
        width = tform_width(tform)
        columns.append(BintableColumn(name, tform, offset, width))
        offset += width
    if offset != row_width:
        raise EligibilityProbeError("FITS_ROW_WIDTH_MISMATCH")
    return tuple(columns)


def validate_exhaustive_schema(observed: Sequence[BintableColumn],
                               expected: Sequence[tuple[str, str]]) -> None:
    if tuple((item.name, item.tform) for item in observed) != tuple(expected):
        raise EligibilityProbeError("PROVIDER_EXHAUSTIVE_SCHEMA_MISMATCH")


def schema_classification(columns: Sequence[BintableColumn]) -> dict[str, str]:
    result = {}
    for column in columns:
        if column.name in TRACTOR_ALLOWLIST:
            result[column.name] = "PROJECTABLE_AFTER_SEMANTICS_BOUND"
        elif column.name in TRACTOR_DENYLIST:
            result[column.name] = "EXPLICITLY_DENIED"
        else:
            result[column.name] = "NONPROJECTABLE"
    return result


def selective_projection_plan(columns: Sequence[BintableColumn], requested: Sequence[str], *,
                              exact_byte_ranges: bool, provider_projection: bool = False,
                              whole_row_fetch: bool = False) -> dict[str, object]:
    if whole_row_fetch:
        raise EligibilityProbeError("POST_DECODE_DROP_FORBIDDEN")
    requested_tuple = tuple(requested)
    if (not requested_tuple or len(set(requested_tuple)) != len(requested_tuple) or
            any(name not in TRACTOR_ALLOWLIST for name in requested_tuple)):
        raise EligibilityProbeError("TRACTOR_PROJECTION_NOT_ALLOWLISTED")
    by_name = {column.name: column for column in columns}
    if any(name not in by_name for name in requested_tuple):
        raise EligibilityProbeError("TRACTOR_PROJECTION_SCHEMA_UNRESOLVED")
    chosen = sorted((by_name[name] for name in requested_tuple), key=lambda item: item.offset)
    spans = []
    for column in chosen:
        if spans and spans[-1][0] + spans[-1][1] == column.offset:
            spans[-1] = (spans[-1][0], spans[-1][1] + column.width)
        else:
            spans.append((column.offset, column.width))
    prohibited = [column for column in columns if column.name not in requested_tuple]
    for start, width in spans:
        end = start + width
        if any(start < item.offset + item.width and item.offset < end for item in prohibited):
            raise EligibilityProbeError("TRACTOR_FORBIDDEN_BYTE_OVERLAP")
    feasible = bool(provider_projection or exact_byte_ranges)
    return {
        "cell_values_decoded": 0,
        "exact_byte_ranges_required": not provider_projection,
        "feasible": feasible,
        "forbidden_cell_bytes_per_row": 0 if feasible else None,
        "provider_projection": provider_projection,
        "row_relative_spans": [{"length": width, "offset": start} for start, width in spans],
        "state": "SELECTIVE_COLUMN_FIREWALL_FEASIBLE" if feasible else FIREWALL_UNAVAILABLE,
    }


def parse_fits_header(blocks: bytes) -> tuple[dict[str, object], int]:
    if not blocks or len(blocks) % 2880:
        raise EligibilityProbeError("FITS_HEADER_BLOCK_INVALID")
    cards = [blocks[index:index + 80].decode("ascii", errors="strict")
             for index in range(0, len(blocks), 80)]
    values = {}; end_card = None
    for index, card in enumerate(cards):
        key = card[:8].strip()
        if key == "END":
            end_card = index
            break
        if not key or card[8:10] != "= ":
            continue
        raw = card[10:80].split("/", 1)[0].strip()
        if raw.startswith("'") and raw.endswith("'"):
            value: object = raw[1:-1].rstrip()
        elif raw in ("T", "F"):
            value = raw == "T"
        else:
            try:
                value = int(raw)
            except ValueError:
                try: value = float(raw.replace("D", "E"))
                except ValueError: value = raw
        values[key] = value
    if end_card is None:
        raise EligibilityProbeError("FITS_HEADER_END_NOT_FOUND")
    used = ((end_card + 1 + 35) // 36) * 2880
    return values, used


def bintable_from_header(header: dict[str, object]) -> tuple[BintableColumn, ...]:
    if header.get("XTENSION") != "BINTABLE" or not isinstance(header.get("TFIELDS"), int):
        raise EligibilityProbeError("FITS_BINTABLE_REQUIRED")
    count = header["TFIELDS"]
    names = [header.get(f"TTYPE{index}") for index in range(1, count + 1)]
    tforms = [header.get(f"TFORM{index}") for index in range(1, count + 1)]
    if not isinstance(header.get("NAXIS1"), int):
        raise EligibilityProbeError("FITS_SCHEMA_INVALID")
    return bintable_layout(names, tforms, header["NAXIS1"])


def validate_final_authorization(candidate_path: Path, authorization_path: Path,
                                 command_argv_sha256: str) -> tuple[dict[str, object], dict[str, object]]:
    candidate = validate_sealed(load_canonical_json(candidate_path))
    authorization = load_canonical_json(authorization_path)
    required = {"authorization_id", "authorized", "candidate_sha256", "command_argv_sha256",
                "scope", "stage_id"}
    if (set(authorization) != required or authorization.get("authorized") is not True or
            authorization.get("stage_id") != STAGE_ID or authorization.get("scope") != SCOPE or
            authorization.get("candidate_sha256") != file_sha256(candidate_path) or
            authorization.get("command_argv_sha256") != command_argv_sha256):
        raise EligibilityProbeError("P1_FINAL_AUTHORIZATION_INVALID")
    return candidate, authorization


@dataclass
class NetworkBudget:
    request_cap: int
    body_cap: int
    per_resource_range_cap: int
    requests: int = 0
    body_bytes: int = 0
    ranges: dict[str, int] = field(default_factory=dict)

    def reserve(self, resource_id: str, maximum: int, *, is_range: bool,
                request_envelope: int = 1) -> None:
        if (maximum < 0 or request_envelope < 1 or
                self.requests + request_envelope > self.request_cap or
                self.body_bytes + maximum > self.body_cap):
            raise EligibilityProbeError("P1_RESOURCE_CAP")
        if is_range and self.ranges.get(resource_id, 0) + maximum > self.per_resource_range_cap:
            raise EligibilityProbeError("P1_RESOURCE_CAP")
        self.requests += request_envelope
        self.body_bytes += maximum
        if is_range:
            self.ranges[resource_id] = self.ranges.get(resource_id, 0) + maximum

    def settle(self, resource_id: str, maximum: int, actual: int, *, is_range: bool,
               request_envelope: int = 1, actual_requests: int = 1) -> None:
        if (actual < 0 or actual > maximum or actual_requests < 1 or
                actual_requests > request_envelope):
            raise EligibilityProbeError("P1_RESPONSE_CAP")
        self.requests -= request_envelope - actual_requests
        self.body_bytes -= maximum - actual
        if is_range:
            self.ranges[resource_id] -= maximum - actual


class BoundedHTTPTransport:
    """HTTPS-only transport; instantiated only after authorization validation."""

    def __init__(self, *, redirect_cap: int, timeout_seconds: int = 30):
        if redirect_cap < 0 or redirect_cap > FIRST_P1_POLICY["redirects_per_request"]:
            raise EligibilityProbeError("P1_REDIRECT_CAP")
        self.redirect_cap = redirect_cap
        self.timeout_seconds = timeout_seconds

    def request(self, method: str, url: str, *, byte_range: tuple[int, int] | None,
                max_body_bytes: int) -> dict[str, object]:
        current = url
        for redirect_count in range(self.redirect_cap + 1):
            parsed = urlsplit(current)
            if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
                raise EligibilityProbeError("P1_URL_INVALID")
            path = parsed.path or "/"
            if parsed.query:
                path += "?" + parsed.query
            headers = {"User-Agent": "OC3-galaxy-eligibility-schema-probe/1"}
            if byte_range is not None:
                headers["Range"] = f"bytes={byte_range[0]}-{byte_range[1]}"
            connection = http.client.HTTPSConnection(parsed.hostname, parsed.port or 443,
                                                      timeout=self.timeout_seconds)
            connection.request(method, path, headers=headers)
            response = connection.getresponse()
            response_headers = {key.lower(): value for key, value in response.getheaders()}
            if response.status in (301, 302, 303, 307, 308):
                location = response_headers.get("location")
                connection.close()
                if not location or redirect_count >= self.redirect_cap:
                    raise EligibilityProbeError("P1_REDIRECT_CAP")
                current = urljoin(current, location)
                continue
            if method == "HEAD":
                body = b""
            else:
                if byte_range is not None and response.status != 206:
                    connection.close()
                    raise EligibilityProbeError("P1_EXACT_RANGE_REQUIRED")
                length = response_headers.get("content-length")
                if length is None or not length.isdigit() or int(length) > max_body_bytes:
                    connection.close()
                    raise EligibilityProbeError("P1_RESPONSE_CAP")
                body = response.read(max_body_bytes + 1)
                if len(body) > max_body_bytes:
                    connection.close()
                    raise EligibilityProbeError("P1_RESPONSE_CAP")
            connection.close()
            return {"body": body, "final_url": current, "headers": response_headers,
                    "redirects": redirect_count, "requests_started": redirect_count + 1,
                    "status": response.status}
        raise EligibilityProbeError("P1_REDIRECT_CAP")


class DurableCheckpoint:
    def __init__(self, directory: Path):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def record(self, sequence: int, receipt: dict[str, object]) -> str:
        sealed = sealed_object(receipt)
        path = self.directory / f"{sequence:04d}.json"
        write_json_immutable(path, sealed)
        entries = []
        for item in sorted(self.directory.glob("[0-9][0-9][0-9][0-9].json")):
            entries.append({"name": item.name, "sha256": file_sha256(item)})
        checkpoint = sealed_object({"completed": entries, "completed_count": len(entries),
                                    "stage_id": STAGE_ID})
        checkpoint_path = self.directory / "CHECKPOINT.json"
        data = canonical_json_bytes(checkpoint)
        temporary = self.directory / ".CHECKPOINT.json.tmp"
        if temporary.exists():
            temporary.unlink()
        with temporary.open("xb") as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, checkpoint_path)
        directory_fd = os.open(self.directory, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        return checkpoint["sealed"]


def p1_logical_order(candidate: dict[str, object]) -> tuple[tuple[str, str, str], ...]:
    documents = candidate.get("documentary_resources")
    if not isinstance(documents, list):
        raise EligibilityProbeError("P1_CANDIDATE_INVALID")
    plan = [("DOCUMENT", row["retrieval_role"], row["url"]) for row in documents]
    if candidate.get("candidate_scope") == "MINIMUM_DOCUMENTARY_BINDING_ONLY":
        return tuple(plan)
    tractor = candidate.get("tractor_resources")
    b1 = candidate.get("b1_resources")
    if not isinstance(tractor, list) or len(tractor) != 16 or not isinstance(b1, list) or len(b1) != 2:
        raise EligibilityProbeError("P1_CANDIDATE_INVALID")
    plan.extend(("HEAD_TRACTOR", row["brickname"], row["literal_url"]) for row in tractor)
    plan.extend(("HEAD_B1", row["region"], row["literal_url"]) for row in b1)
    plan.extend(("HEADER_TRACTOR", row["brickname"], row["literal_url"]) for row in tractor)
    plan.extend(("HEADER_B1", row["region"], row["literal_url"]) for row in b1)
    return tuple(plan)


def _request_with_budget(transport: object, budget: NetworkBudget, *, method: str,
                         url: str, resource_id: str, maximum: int,
                         byte_range: tuple[int, int] | None,
                         redirect_cap: int) -> dict[str, object]:
    envelope = 1 + redirect_cap
    is_range = byte_range is not None
    budget.reserve(resource_id, maximum, is_range=is_range, request_envelope=envelope)
    response = transport.request(method, url, byte_range=byte_range, max_body_bytes=maximum)
    body = response.get("body")
    requests_started = response.get("requests_started", response.get("redirects", 0) + 1)
    if not isinstance(body, bytes) or not isinstance(requests_started, int):
        raise EligibilityProbeError("P1_TRANSPORT_RECEIPT_INVALID")
    budget.settle(resource_id, maximum, len(body), is_range=is_range,
                  request_envelope=envelope, actual_requests=requests_started)
    return response


def _fits_data_padded_size(header: dict[str, object]) -> int:
    bitpix = header.get("BITPIX")
    naxis = header.get("NAXIS")
    if not isinstance(bitpix, int) or not isinstance(naxis, int) or naxis < 0:
        raise EligibilityProbeError("FITS_HEADER_GEOMETRY_INVALID")
    if header.get("XTENSION") == "BINTABLE":
        naxis1 = header.get("NAXIS1"); naxis2 = header.get("NAXIS2")
        pcount = header.get("PCOUNT", 0); gcount = header.get("GCOUNT", 1)
        if not all(isinstance(value, int) and value >= 0 for value in (naxis1, naxis2, pcount, gcount)):
            raise EligibilityProbeError("FITS_HEADER_GEOMETRY_INVALID")
        raw = (naxis1 * naxis2 + pcount) * gcount
    elif naxis == 0:
        raw = 0
    else:
        axes = [header.get(f"NAXIS{index}") for index in range(1, naxis + 1)]
        if any(not isinstance(value, int) or value < 0 for value in axes):
            raise EligibilityProbeError("FITS_HEADER_GEOMETRY_INVALID")
        raw = abs(bitpix) // 8
        for value in axes:
            raw *= value
        raw += header.get("PCOUNT", 0)
        raw *= header.get("GCOUNT", 1)
    return ((raw + 2879) // 2880) * 2880


def _header_has_end(blocks: bytes) -> bool:
    for offset in range(0, len(blocks), 80):
        if blocks[offset:offset + 8] == b"END     ":
            return True
    return False


def _fetch_header(transport: object, budget: NetworkBudget, checkpoints: DurableCheckpoint,
                  sequence: list[int], raw_directory: Path, *, url: str,
                  resource_id: str, start: int, redirect_cap: int) -> tuple[dict[str, object], bytes]:
    blocks = bytearray()
    for block_index in range(182):  # 182 * 2880 < 512 KiB
        offset = start + block_index * 2880
        response = _request_with_budget(
            transport, budget, method="GET", url=url, resource_id=resource_id,
            maximum=2880, byte_range=(offset, offset + 2879), redirect_cap=redirect_cap)
        body = response["body"]
        if len(body) != 2880:
            raise EligibilityProbeError("FITS_HEADER_BLOCK_INVALID")
        blocks.extend(body)
        sequence[0] += 1
        checkpoints.record(sequence[0], {
            "body_bytes": len(body), "byte_range": [offset, offset + 2879],
            "content_sha256": sha256_bytes(body), "final_url": response["final_url"],
            "kind": "FITS_HEADER_BLOCK", "resource_id": resource_id,
            "status": response["status"],
        })
        if _header_has_end(bytes(blocks)):
            header, used = parse_fits_header(bytes(blocks))
            raw = bytes(blocks[:used])
            write_immutable(raw_directory / f"{resource_id}.{start}.header", raw)
            return header, raw
    raise EligibilityProbeError("FITS_HEADER_BLOCK_CAP")


def _probe_bintable_headers(transport: object, budget: NetworkBudget,
                            checkpoints: DurableCheckpoint, sequence: list[int],
                            raw_directory: Path, *, url: str, resource_id: str,
                            redirect_cap: int) -> tuple[dict[str, object], tuple[BintableColumn, ...]]:
    primary, primary_raw = _fetch_header(
        transport, budget, checkpoints, sequence, raw_directory, url=url,
        resource_id=resource_id, start=0, redirect_cap=redirect_cap)
    extension_start = len(primary_raw) + _fits_data_padded_size(primary)
    extension, extension_raw = _fetch_header(
        transport, budget, checkpoints, sequence, raw_directory, url=url,
        resource_id=resource_id, start=extension_start, redirect_cap=redirect_cap)
    columns = bintable_from_header(extension)
    return {
        "extension_header_sha256": sha256_bytes(extension_raw),
        "extension_header_start": extension_start,
        "naxis1": extension.get("NAXIS1"),
        "naxis2": extension.get("NAXIS2"),
        "primary_header_sha256": sha256_bytes(primary_raw),
        "tfields": extension.get("TFIELDS"),
    }, columns


def probe_resource_schema(candidate_path: Path, authorization_path: Path,
                          command_argv_sha256: str, output_directory: Path, *,
                          transport_factory: Callable[..., object] = BoundedHTTPTransport) -> dict[str, object]:
    candidate, authorization = validate_final_authorization(
        candidate_path, authorization_path, command_argv_sha256)
    policy = candidate.get("policy")
    if (not isinstance(policy, dict) or policy.get("concurrency") != 1 or
            policy.get("automatic_retries_per_resource") != 0 or
            policy.get("request_cap", 0) > P1_SPEC_MAXIMA["requests"] or
            policy.get("body_bytes_cap", 0) > P1_SPEC_MAXIMA["body_bytes"] or
            policy.get("per_resource_range_body_bytes", 0) > P1_SPEC_MAXIMA["per_resource_range_bytes"]):
        raise EligibilityProbeError("P1_POLICY_INVALID")
    # The construction boundary is intentionally after all authorization and
    # policy validation.
    transport = transport_factory(redirect_cap=policy["redirects_per_request"])
    budget = NetworkBudget(policy["request_cap"], policy["body_bytes_cap"],
                           policy["per_resource_range_body_bytes"])
    checkpoints = DurableCheckpoint(Path(output_directory) / "checkpoints")
    completed = 0
    sequence = [0]
    raw_directory = Path(output_directory) / "RAW_IMMUTABLE"
    raw_directory.mkdir(parents=True, exist_ok=True)
    head_evidence: dict[str, dict[str, object]] = {}
    plan = p1_logical_order(candidate)
    sequence = [0]
    for kind, resource_id, url in plan:
        if kind == "DOCUMENT":
            maximum = next(row["max_body_bytes"] for row in candidate["documentary_resources"]
                           if row["retrieval_role"] == resource_id)
            response = _request_with_budget(
                transport, budget, method="GET", url=url, resource_id=resource_id,
                maximum=maximum, byte_range=None,
                redirect_cap=policy["redirects_per_request"])
            body = response["body"]
            write_immutable(raw_directory / f"document-{completed:02d}.body", body)
            sequence[0] += 1
            checkpoints.record(sequence[0], {
                "body_bytes": len(body), "content_sha256": sha256_bytes(body),
                "final_url": response["final_url"], "kind": kind,
                "resource_id": resource_id, "status": response["status"],
            })
        elif kind.startswith("HEAD_"):
            response = _request_with_budget(
                transport, budget, method="HEAD", url=url, resource_id=resource_id,
                maximum=0, byte_range=None,
                redirect_cap=policy["redirects_per_request"])
            evidence = {
                "accept_ranges": response["headers"].get("accept-ranges"),
                "content_length": response["headers"].get("content-length"),
                "final_url": response["final_url"], "status": response["status"],
            }
            head_evidence[resource_id] = evidence
            sequence[0] += 1
            checkpoints.record(sequence[0], {"kind": kind, "resource_id": resource_id, **evidence})
        elif kind.startswith("HEADER_"):
            head = head_evidence.get(resource_id)
            if not head or head.get("accept_ranges", "").lower() != "bytes":
                raise EligibilityProbeError(FIREWALL_UNAVAILABLE)
            header_evidence, columns = _probe_bintable_headers(
                transport, budget, checkpoints, sequence, raw_directory,
                url=url, resource_id=resource_id,
                redirect_cap=policy["redirects_per_request"])
            if kind == "HEADER_TRACTOR":
                expected = candidate.get("tractor_exhaustive_schema")
                if not isinstance(expected, list):
                    raise EligibilityProbeError("P1_POST_DOCUMENTARY_CANDIDATE_REQUIRED")
                validate_exhaustive_schema(columns, tuple((row["name"], row["tform"]) for row in expected))
                projected = tuple(name for name in A_CORE + C1_EXTENSION
                                  if name in {column.name for column in columns})
                projection = selective_projection_plan(columns, projected, exact_byte_ranges=True)
            else:
                contracts = candidate.get("b1_exhaustive_schemas")
                region = next(row["region"] for row in candidate["b1_resources"]
                              if row["literal_url"] == url)
                if not isinstance(contracts, dict) or not isinstance(contracts.get(region), list):
                    raise EligibilityProbeError("P1_POST_DOCUMENTARY_CANDIDATE_REQUIRED")
                expected = contracts[region]
                validate_exhaustive_schema(columns, tuple((row["name"], row["tform"]) for row in expected))
                projection = {"cell_values_decoded": 0, "state": "B1_SCHEMA_ONLY_PANEL_ACCESS_UNRESOLVED"}
            sequence[0] += 1
            checkpoints.record(sequence[0], {
                "column_count": len(columns), "header_evidence": header_evidence,
                "kind": kind, "projection": projection, "resource_id": resource_id,
            })
        else:
            raise EligibilityProbeError("P1_REQUEST_PLAN_INVALID")
        completed += 1
    state = (P1_INCONCLUSIVE_TERMINAL
             if candidate.get("candidate_scope") == "MINIMUM_DOCUMENTARY_BINDING_ONLY"
             else P1_SUCCESS_TERMINAL)
    return {
        "authorization_id": authorization["authorization_id"],
        "body_bytes": budget.body_bytes,
        "completed_resources": completed,
        "network_requests": budget.requests,
        "stage_id": STAGE_ID,
        "state": state,
        "tripwires": Tripwires().object(),
    }
