"""Closed offline technical-brick selection for the bounded OC-3 pilot."""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import struct
import threading
import time
from types import MappingProxyType
from typing import Callable, Iterable

from .core import canonical, implementation_hash
from .metadata_value_semantics import (
    JoinRowInput, PatchRowInput, ValidatedPatchList, validate_brickname,
    validate_complete_patch_rows, validate_join_row, validate_patch_joins,
)
from .patch_metadata_decode import (
    EXPECTED_EVIDENCE, PATCH_RELATIVE, ROOT_RELATIVE, SOUTH_RELATIVE,
    PatchDecodeError, PatchObservation, PatchSelectiveFitsDecoder,
    ResourceAccounting, _validate_table, production_inputs as patch_production_inputs,
)
from .provider_physical_contracts import (
    PRODUCTION_PHYSICAL_CONTRACTS, FrozenPhysicalContract, PhysicalRole,
)
from .provider_schema import grz_median_present_v1


STAGE_ID = "OC3-TECHNICAL-SELECTION-001"
SUCCESS_TERMINAL = "TECHNICAL_PILOT_COHORT_MATERIALIZED"
FAILURE_TERMINAL = "TECHNICAL_PILOT_COHORT_MATERIALIZATION_FAILED"
SPEC_SHA256 = "781784819b6e9b8254d664d0d4d85478837c82de616a96e7ef590924f37882a8"
PROJECT = Path("/home/jzsalinas/Documents/galaxy-morphology-discovery")
ATTEMPT = PROJECT / "oc3/metadata_bootstrap/OC3-METADATA-BOOTSTRAP-001"
PATCH_EVIDENCE = PROJECT / "oc3/patch_metadata_decode/OC3-PATCH-METADATA-DECODE-001"
OUTPUT_CSV = PROJECT / "oc3/INPUTS/OC3_DEVELOPMENT_BRICKS.csv"
AUDIT_DIRECTORY = PROJECT / "oc3/technical_selection/OC3-TECHNICAL-SELECTION-001"

NORTH_RELATIVE = Path("RAW_IMMUTABLE/NORTH_SUMMARY/survey-bricks-dr9-north.fits.gz")
EXPECTED_RAW = MappingProxyType({
    PhysicalRole.ROOT_SUMMARY: (ROOT_RELATIVE, 13_147_987,
        "dc943d702357f93553b9e5d15e87ace38df94eb7095f4100657407b3f9919c5f"),
    PhysicalRole.NORTH_SUMMARY: (NORTH_RELATIVE, 20_882_100,
        "2edd5c295fdad26852c6f224a3ff023cff43dd0e03a53acd35b767e726ee72fb"),
    PhysicalRole.SOUTH_SUMMARY: (SOUTH_RELATIVE, 55_399_879,
        "7360414f5d53571ca70fa0cb483eb8c80cfcbe80df0856a117246f442a0b9a3f"),
    PhysicalRole.SOUTH_PATCH_LIST: (PATCH_RELATIVE, 31_680,
        "f87e7aa55360b935033fc0638491038e7170cc9b88fc6c0905000d420280f6b6"),
})
PATCH_OUTPUT_HASHES = MappingProxyType({
    "PATCH_DECODE_INPUT_BINDING.json": "2000b6a320e752c5e2259b20609a3f09d11cb53912eddb28fdf1ddb31c5b3404",
    "PATCH_DECODE_AGGREGATE_EVIDENCE.json": "b7544c4bff40189581d66126dcad4ddbc2b6a0f481220641bf2f9697f9e85caf",
    "PATCH_DECODE_TERMINAL.json": "79ccef6894d9fd6b612b8571bab500ef522a2f1797679c94fcbc8e1d4957da5c",
    "PATCH_DECODE_RUN.log": "e11e525be4da81584d9eec274b3267181219db7fce09eec973735ac975822abd",
})
PATCH_IMPLEMENTATION_AGGREGATE = "479feb485ac63399595f6bf0b69a281a784356ecb498842ea3f80c7d60826810"

ROOT_FIELDS = ("BRICKNAME", "BRICKID", "RA", "DEC", "RA1", "RA2", "DEC1", "DEC2")
REGIONAL_FIELDS = ("brickname", "brickid", "ra", "dec", "ra1", "ra2", "dec1", "dec2",
                   "nexp_g", "nexp_r", "nexp_z")
PATCH_FIELDS = ("RELEASE", "BRICKID", "BRICKNAME")
AUDIT_FILES = (
    "TECHNICAL_SELECTION_INPUT_BINDING.json",
    "TECHNICAL_SELECTION_AGGREGATE_EVIDENCE.json",
    "TECHNICAL_SELECTION_TERMINAL.json",
    "TECHNICAL_SELECTION_RUN.log",
)
CSV_HEADER = "region,brickname,development,holdout_disjoint,evidence_ref\n"
OUTPUT_BYTES_CAP = 1_048_576
RAM_BYTES_CAP = 2_147_483_648
COMPUTE_SECONDS_CAP = 1800
WALL_SECONDS_CAP = 3600


class SelectionError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class SelectionRuntimeGuard:
    def __init__(self):
        self.wall_start = time.monotonic(); self.cpu_start = time.process_time()

    def check(self) -> None:
        if (time.monotonic() - self.wall_start > WALL_SECONDS_CAP or
                time.process_time() - self.cpu_start > COMPUTE_SECONDS_CAP or
                threading.active_count() > 1):
            raise PatchDecodeError("PATCH_RESOURCE_LIMIT_STOP")
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        peak_bytes = peak * 1024 if peak < 2**40 else peak
        if peak_bytes > RAM_BYTES_CAP:
            raise PatchDecodeError("PATCH_RESOURCE_LIMIT_STOP")

    def elapsed(self) -> tuple[int, int]:
        return (int(time.monotonic() - self.wall_start),
                int(time.process_time() - self.cpu_start))


@dataclass(frozen=True)
class RootRow:
    brickname: bytes
    brickid: int
    geometry: tuple[float, float, float, float, float, float]


@dataclass(frozen=True)
class RegionalRow:
    brickname: bytes
    brickid: int
    geometry: tuple[float, float, float, float, float, float]
    nexp: tuple[int, int, int]


@dataclass(frozen=True)
class Candidate:
    region: str
    survey: str
    release_family: str
    generation: str
    brickname: bytes
    brickid: int
    grz: bool
    corrected_9012: bool


@dataclass(frozen=True)
class StageInputs:
    attempt: Path
    patch_evidence: Path
    root: Path
    north: Path
    south: Path
    patch: Path
    expected_hashes: MappingProxyType
    contracts: MappingProxyType
    patch_output_hashes: MappingProxyType
    synthetic_only: bool


@dataclass
class SelectionObservation:
    decoded_fields: dict[str, tuple[str, ...]] = field(default_factory=lambda: {
        "ROOT": ROOT_FIELDS, "NORTH": REGIONAL_FIELDS, "SOUTH": REGIONAL_FIELDS,
        "PATCH": PATCH_FIELDS,
    })
    opaque_bytes_transited: int = 0
    cell_values_decoded: int = 0
    unexpected_field_observation_count: int = 0
    unexpected_value_materialization_count: int = 0
    unexpected_value_log_count: int = 0
    unexpected_value_serialization_count: int = 0

    def object(self) -> dict[str, object]:
        return {
            "cell_values_decoded": self.cell_values_decoded,
            "decoded_fields": {key: list(value) for key, value in sorted(self.decoded_fields.items())},
            "opaque_bytes_transited": self.opaque_bytes_transited,
            "unexpected_field_observation_count": self.unexpected_field_observation_count,
            "unexpected_value_log_count": self.unexpected_value_log_count,
            "unexpected_value_materialization_count": self.unexpected_value_materialization_count,
            "unexpected_value_serialization_count": self.unexpected_value_serialization_count,
        }


@dataclass
class SelectionMetrics:
    root_input_count: int = 0
    north_input_count: int = 0
    south_input_count: int = 0
    patch_input_count: int = 0
    north_grz_excluded: int = 0
    south_grz_excluded: int = 0
    south_patch_excluded: int = 0
    eligible_north_count: int = 0
    eligible_south_count: int = 0
    selected_count: int = 0
    south_count: int = 0
    north_count: int = 0
    tie_count: int = 0
    row_level_leakage_count: int = 0
    network_requests: int = 0
    network_bytes: int = 0

    def object(self) -> dict[str, int]:
        return {key: getattr(self, key) for key in (
            "eligible_north_count", "eligible_south_count", "network_bytes", "network_requests",
            "north_count", "north_grz_excluded", "north_input_count", "patch_input_count",
            "root_input_count", "row_level_leakage_count", "selected_count", "south_count",
            "south_grz_excluded", "south_input_count", "south_patch_excluded", "tie_count",
        )}


def _strict_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate key")
        value[key] = item
    return value


def _canonical_json(path: Path, expected_sha: str, accounting: ResourceAccounting) -> dict:
    raw = accounting.read_bytes(path)
    if hashlib.sha256(raw).hexdigest() != expected_sha:
        raise SelectionError("TECHNICAL_SELECTION_INPUT_BINDING_FAILURE")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_strict_object)
    except (UnicodeError, ValueError) as exc:
        raise SelectionError("TECHNICAL_SELECTION_INPUT_BINDING_FAILURE") from exc
    if not isinstance(value, dict) or raw != canonical(value) + b"\n":
        raise SelectionError("TECHNICAL_SELECTION_INPUT_BINDING_FAILURE")
    return value


def production_inputs(attempt: Path, patch_evidence: Path,
                      accounting: ResourceAccounting) -> StageInputs:
    attempt = Path(attempt); patch_evidence = Path(patch_evidence)
    if (not attempt.is_absolute() or attempt.resolve() != ATTEMPT or str(attempt) != str(ATTEMPT) or
            not patch_evidence.is_absolute() or patch_evidence.resolve() != PATCH_EVIDENCE or
            str(patch_evidence) != str(PATCH_EVIDENCE)):
        raise SelectionError("TECHNICAL_SELECTION_INPUT_BINDING_FAILURE")
    try:
        base = patch_production_inputs(attempt, accounting)
    except (PatchDecodeError, OSError) as exc:
        raise SelectionError("TECHNICAL_SELECTION_INPUT_BINDING_FAILURE") from exc

    try:
        entries = tuple(patch_evidence.iterdir())
    except OSError as exc:
        raise SelectionError("TECHNICAL_SELECTION_INPUT_BINDING_FAILURE") from exc
    if ({item.name for item in entries if item.is_file()} != set(PATCH_OUTPUT_HASHES) or
            any(item.is_dir() or item.is_symlink() for item in entries)):
        raise SelectionError("TECHNICAL_SELECTION_INPUT_BINDING_FAILURE")
    patch_docs = {}
    for name, digest in PATCH_OUTPUT_HASHES.items():
        path = patch_evidence / name
        if name.endswith(".json"):
            patch_docs[name] = _canonical_json(path, digest, accounting)
        elif accounting.hash_file(path) != digest:
            raise SelectionError("TECHNICAL_SELECTION_INPUT_BINDING_FAILURE")
    binding = patch_docs["PATCH_DECODE_INPUT_BINDING.json"]
    aggregate = patch_docs["PATCH_DECODE_AGGREGATE_EVIDENCE.json"]
    terminal = patch_docs["PATCH_DECODE_TERMINAL.json"]
    metrics = aggregate.get("metrics")
    observation = aggregate.get("decoder_observation")
    if (binding.get("current_implementation_aggregate") != PATCH_IMPLEMENTATION_AGGREGATE or
            binding.get("synthetic_only") is not False or
            binding.get("allowed_patch_fields") != list(PATCH_FIELDS) or
            terminal != {"first_error_code": None, "stage_id": "OC3-PATCH-METADATA-DECODE-001",
                         "successful": True, "terminal": "PATCH_METADATA_DECODE_VALIDATED"} or
            not isinstance(metrics, dict) or metrics.get("row_count") != 1691 or
            metrics.get("valid_row_count") != 1691 or metrics.get("release_valid_count") != 1691 or
            metrics.get("unique_BRICKNAME_count") != 1691 or
            metrics.get("unique_BRICKID_count") != 1691 or metrics.get("unique_pair_count") != 1691 or
            metrics.get("network_requests") != 0 or metrics.get("output_row_level_leakage_count") != 0 or
            not isinstance(observation, dict) or observation.get("decoded_fields") != list(PATCH_FIELDS) or
            observation.get("unexpected_field_observation_count") != 0):
        raise SelectionError("TECHNICAL_SELECTION_INPUT_BINDING_FAILURE")

    manifest = _canonical_json(attempt / "BOOTSTRAP_RAW_FILE_MANIFEST.json",
                               EXPECTED_EVIDENCE["BOOTSTRAP_RAW_FILE_MANIFEST.json"], accounting)
    manifest_rows = {row.get("role"): row for row in manifest.get("resources", [])
                     if isinstance(row, dict)}
    north = attempt / NORTH_RELATIVE
    relative, size, digest = EXPECTED_RAW[PhysicalRole.NORTH_SUMMARY]
    row = manifest_rows.get(PhysicalRole.NORTH_SUMMARY.value)
    if (not north.is_file() or north.is_symlink() or north.stat().st_size != size or
            north.stat().st_mode & 0o222 or not isinstance(row, dict) or
            row.get("raw_relative_path") != str(relative) or row.get("raw_byte_length") != size or
            row.get("raw_sha256") != digest or accounting.hash_file(north) != digest):
        raise SelectionError("TECHNICAL_SELECTION_INPUT_BINDING_FAILURE")
    expected = dict(base.expected_hashes); expected[PhysicalRole.NORTH_SUMMARY] = digest
    return StageInputs(attempt, patch_evidence, base.root, north, base.south, base.patch,
                       MappingProxyType(expected), PRODUCTION_PHYSICAL_CONTRACTS,
                       PATCH_OUTPUT_HASHES, False)


class TechnicalSelectiveFitsDecoder(PatchSelectiveFitsDecoder):
    """Stage-scoped row-stride projection; no complete provider row is built."""

    @staticmethod
    def _selected_layout(data: bytes, contract: FrozenPhysicalContract,
                         fields: tuple[str, ...]) -> tuple[int, int, dict[str, tuple[int, int, str]]]:
        data_start, nrows, offsets = _validate_table(data, contract)
        layout = {name: (offset, width, tform) for offset, width, tform, name in offsets}
        if any(name not in layout for name in fields):
            raise SelectionError("TECHNICAL_SELECTION_FIELD_BOUNDARY_FAILURE")
        return data_start, nrows, {name: layout[name] for name in fields}

    @staticmethod
    def _cell(data: bytes, base: int, item: tuple[int, int, str]):
        offset, width, tform = item; raw = data[base + offset:base + offset + width]
        if len(raw) != width:
            raise SelectionError("TECHNICAL_SELECTION_VALUE_SEMANTICS_FAILURE")
        if tform == "8A": return bytes(raw)
        if tform == "J": return struct.unpack(">i", raw)[0]
        if tform == "I": return struct.unpack(">h", raw)[0]
        if tform == "D": return struct.unpack(">d", raw)[0]
        raise SelectionError("TECHNICAL_SELECTION_FIELD_BOUNDARY_FAILURE")

    def decode_root(self, path: Path, contract: FrozenPhysicalContract,
                    observation: SelectionObservation) -> tuple[RootRow, ...]:
        if contract.role is not PhysicalRole.ROOT_SUMMARY:
            raise SelectionError("TECHNICAL_SELECTION_FIELD_BOUNDARY_FAILURE")
        data = self._data(path, contract)
        start, count, layout = self._selected_layout(data, contract, ROOT_FIELDS)
        rows = []
        for index in range(count):
            if index % 8192 == 0: self.accounting.check()
            base = start + contract.naxis1 * index
            values = {name: self._cell(data, base, layout[name]) for name in ROOT_FIELDS}
            rows.append(RootRow(values["BRICKNAME"], values["BRICKID"],
                                tuple(values[name] for name in ("RA", "DEC", "RA1", "RA2", "DEC1", "DEC2"))))
        observation.opaque_bytes_transited += contract.naxis1 * count
        observation.cell_values_decoded += len(ROOT_FIELDS) * count
        return tuple(rows)

    def decode_regional(self, path: Path, contract: FrozenPhysicalContract,
                        observation: SelectionObservation) -> tuple[RegionalRow, ...]:
        if contract.role not in (PhysicalRole.NORTH_SUMMARY, PhysicalRole.SOUTH_SUMMARY):
            raise SelectionError("TECHNICAL_SELECTION_FIELD_BOUNDARY_FAILURE")
        data = self._data(path, contract)
        start, count, layout = self._selected_layout(data, contract, REGIONAL_FIELDS)
        rows = []
        for index in range(count):
            if index % 8192 == 0: self.accounting.check()
            base = start + contract.naxis1 * index
            values = {name: self._cell(data, base, layout[name]) for name in REGIONAL_FIELDS}
            rows.append(RegionalRow(values["brickname"], values["brickid"],
                                    tuple(values[name] for name in ("ra", "dec", "ra1", "ra2", "dec1", "dec2")),
                                    tuple(values[name] for name in ("nexp_g", "nexp_r", "nexp_z"))))
        observation.opaque_bytes_transited += contract.naxis1 * count
        observation.cell_values_decoded += len(REGIONAL_FIELDS) * count
        return tuple(rows)


def _root_index(rows: Iterable[RootRow]) -> dict[bytes, RootRow]:
    result = {}; ids = set()
    try:
        for row in rows:
            name = validate_brickname(row.brickname)
            identity = validate_join_row(JoinRowInput(row.brickname, row.brickid))
            if any(type(value) not in (int, float) or not math.isfinite(value) for value in row.geometry):
                raise ValueError
            if name.raw in result or identity.brickid in ids:
                raise ValueError
            result[name.raw] = row; ids.add(identity.brickid)
    except Exception as exc:
        raise SelectionError("TECHNICAL_SELECTION_VALUE_SEMANTICS_FAILURE") from exc
    return result


def _regional_rows(rows: Iterable[RegionalRow], root: dict[bytes, RootRow]) -> tuple[RegionalRow, ...]:
    output = []; names = set(); ids = set()
    try:
        for row in rows:
            name = validate_brickname(row.brickname)
            identity = validate_join_row(JoinRowInput(row.brickname, row.brickid))
            if name.raw in names or identity.brickid in ids:
                raise ValueError
            if any(type(value) not in (int, float) or not math.isfinite(value) for value in row.geometry):
                raise ValueError
            if any(type(value) is not int for value in row.nexp):
                raise ValueError
            parent = root.get(name.raw)
            if parent is None or parent.brickid != row.brickid or parent.geometry != row.geometry:
                raise SelectionError("TECHNICAL_SELECTION_JOIN_FAILURE")
            grz_median_present_v1(*row.nexp)
            names.add(name.raw); ids.add(identity.brickid); output.append(row)
    except SelectionError:
        raise
    except Exception as exc:
        raise SelectionError("TECHNICAL_SELECTION_VALUE_SEMANTICS_FAILURE") from exc
    return tuple(output)


def candidate_is_eligible(candidate: Candidate) -> bool:
    if candidate.region == "south":
        expected = ("DECaLS", "DR9", "9012", True, True)
    elif candidate.region == "north":
        expected = ("BASS_MzLS", "DR9", "9011", True, False)
    else:
        return False
    return (candidate.survey, candidate.release_family, candidate.generation,
            candidate.grz, candidate.corrected_9012) == expected


def selection_hash(candidate: Candidate) -> str:
    name = validate_brickname(candidate.brickname).value
    return hashlib.sha256(f"OC3-v1|brick|{candidate.region}|{name}".encode("utf-8")).hexdigest()


def order_candidates(candidates: Iterable[Candidate], *,
                     hasher: Callable[[Candidate], str] = selection_hash
                     ) -> tuple[tuple[Candidate, ...], str, int]:
    decorated = [(hasher(candidate), validate_brickname(candidate.brickname).value, candidate)
                 for candidate in candidates]
    decorated.sort(key=lambda item: (item[0], item[1].encode("ascii")))
    sequence = b"".join(f"{digest}|{name}\n".encode("utf-8") for digest, name, _ in decorated)
    frequencies = {}
    for digest, _, _ in decorated: frequencies[digest] = frequencies.get(digest, 0) + 1
    ties = sum(count - 1 for count in frequencies.values() if count > 1)
    return tuple(item[2] for item in decorated), hashlib.sha256(sequence).hexdigest(), ties


def _build_candidates(root_rows: tuple[RootRow, ...], north_rows: tuple[RegionalRow, ...],
                      south_rows: tuple[RegionalRow, ...], patch_rows: tuple[PatchRowInput, ...],
                      metrics: SelectionMetrics) -> tuple[tuple[Candidate, ...], tuple[Candidate, ...]]:
    root = _root_index(root_rows)
    north = _regional_rows(north_rows, root); south = _regional_rows(south_rows, root)
    try:
        patch = validate_complete_patch_rows(patch_rows)
        validate_patch_joins(patch,
            tuple(JoinRowInput(row.brickname, row.brickid) for row in root_rows),
            tuple(JoinRowInput(row.brickname, row.brickid) for row in south))
    except Exception as exc:
        raise SelectionError("TECHNICAL_SELECTION_JOIN_FAILURE") from exc
    membership = {row.brickname.raw: row.brickid for row in patch.rows}
    metrics.root_input_count = len(root_rows); metrics.north_input_count = len(north)
    metrics.south_input_count = len(south); metrics.patch_input_count = len(patch.rows)
    north_candidates = []; south_candidates = []
    for row in north:
        grz = grz_median_present_v1(*row.nexp)
        if not grz:
            metrics.north_grz_excluded += 1; continue
        candidate = Candidate("north", "BASS_MzLS", "DR9", "9011", row.brickname,
                              row.brickid, True, False)
        if not candidate_is_eligible(candidate):
            raise SelectionError("TECHNICAL_SELECTION_ELIGIBILITY_FAILURE")
        north_candidates.append(candidate)
    for row in south:
        grz = grz_median_present_v1(*row.nexp)
        if not grz:
            metrics.south_grz_excluded += 1; continue
        if membership.get(row.brickname) != row.brickid:
            metrics.south_patch_excluded += 1; continue
        candidate = Candidate("south", "DECaLS", "DR9", "9012", row.brickname,
                              row.brickid, True, True)
        if not candidate_is_eligible(candidate):
            raise SelectionError("TECHNICAL_SELECTION_ELIGIBILITY_FAILURE")
        south_candidates.append(candidate)
    metrics.eligible_north_count = len(north_candidates)
    metrics.eligible_south_count = len(south_candidates)
    return tuple(south_candidates), tuple(north_candidates)


def _csv(selected: tuple[Candidate, Candidate]) -> bytes:
    rows = [CSV_HEADER]
    for candidate in selected:
        name = validate_brickname(candidate.brickname).value
        rows.append(f"{candidate.region},{name},true,true,{STAGE_ID}\n")
    return "".join(rows).encode("utf-8")


def _encode_audit(binding: dict, aggregate: dict, terminal: dict) -> dict[str, bytes]:
    values = {
        "TECHNICAL_SELECTION_INPUT_BINDING.json": canonical(binding) + b"\n",
        "TECHNICAL_SELECTION_AGGREGATE_EVIDENCE.json": canonical(aggregate) + b"\n",
        "TECHNICAL_SELECTION_TERMINAL.json": canonical(terminal) + b"\n",
    }
    values["TECHNICAL_SELECTION_RUN.log"] = (
        f"stage_id={STAGE_ID}\nterminal={terminal['terminal']}\n"
        f"first_error_code={terminal['first_error_code']}\n"
        f"selected_count={aggregate['metrics']['selected_count']}\n"
        f"south_count={aggregate['metrics']['south_count']}\n"
        f"north_count={aggregate['metrics']['north_count']}\n"
        "network_requests=0\nrow_level_leakage_count=0\n"
    ).encode("utf-8")
    return values


def _publish(csv_path: Path, audit_directory: Path, csv_bytes: bytes | None,
             values: dict[str, bytes]) -> None:
    if set(values) != set(AUDIT_FILES) or sum(map(len, values.values())) + len(csv_bytes or b"") > OUTPUT_BYTES_CAP:
        raise SelectionError("TECHNICAL_SELECTION_RESOURCE_LIMIT_STOP")
    if csv_path.exists() or audit_directory.exists():
        raise SelectionError("TECHNICAL_SELECTION_LOCAL_STATE_CONFLICT")
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    audit_directory.parent.mkdir(parents=True, exist_ok=True)
    try:
        audit_directory.mkdir(exist_ok=False)
        for name in AUDIT_FILES:
            with (audit_directory / name).open("xb") as stream:
                stream.write(values[name]); stream.flush(); os.fsync(stream.fileno())
        if csv_bytes is not None:
            with csv_path.open("xb") as stream:
                stream.write(csv_bytes); stream.flush(); os.fsync(stream.fileno())
    except FileExistsError as exc:
        raise SelectionError("TECHNICAL_SELECTION_LOCAL_STATE_CONFLICT") from exc


def execute_stage(inputs: StageInputs, output_csv: Path, audit_directory: Path, *,
                  current_implementation: str, accounting: ResourceAccounting | None = None,
                  decoder_factory=TechnicalSelectiveFitsDecoder) -> dict[str, object]:
    accounting = accounting or ResourceAccounting(guard=SelectionRuntimeGuard())
    output_csv = Path(output_csv); audit_directory = Path(audit_directory)
    if output_csv.exists() or audit_directory.exists():
        raise SelectionError("TECHNICAL_SELECTION_LOCAL_STATE_CONFLICT")
    metrics = SelectionMetrics(); observation = SelectionObservation()
    error_code = None; csv_bytes = None; sequence_hashes = {"north": None, "south": None}
    selected: tuple[Candidate, Candidate] | tuple[()] = ()
    binding = {
        "audit_directory": str(audit_directory),
        "current_implementation_aggregate": current_implementation,
        "input_paths": {"NORTH": str(inputs.north), "PATCH": str(inputs.patch),
                        "ROOT": str(inputs.root), "SOUTH": str(inputs.south)},
        "output_csv": str(output_csv),
        "patch_evidence_hashes": dict(inputs.patch_output_hashes),
        "raw_sha256": {role.value: digest for role, digest in inputs.expected_hashes.items()},
        "spec_sha256": SPEC_SHA256, "stage_id": STAGE_ID,
        "synthetic_only": inputs.synthetic_only,
    }
    try:
        for role, path in ((PhysicalRole.ROOT_SUMMARY, inputs.root),
                           (PhysicalRole.NORTH_SUMMARY, inputs.north),
                           (PhysicalRole.SOUTH_SUMMARY, inputs.south),
                           (PhysicalRole.SOUTH_PATCH_LIST, inputs.patch)):
            if not path.is_file() or accounting.hash_file(path) != inputs.expected_hashes[role]:
                raise SelectionError("TECHNICAL_SELECTION_INPUT_BINDING_FAILURE")
        decoder = decoder_factory(accounting)
        root_rows = decoder.decode_root(inputs.root, inputs.contracts[PhysicalRole.ROOT_SUMMARY], observation)
        north_rows = decoder.decode_regional(inputs.north, inputs.contracts[PhysicalRole.NORTH_SUMMARY], observation)
        south_rows = decoder.decode_regional(inputs.south, inputs.contracts[PhysicalRole.SOUTH_SUMMARY], observation)
        patch_observation = PatchObservation()
        patch_rows = decoder.decode_patch(inputs.patch, inputs.contracts[PhysicalRole.SOUTH_PATCH_LIST], patch_observation)
        observation.opaque_bytes_transited += patch_observation.opaque_bytes_transited
        observation.cell_values_decoded += patch_observation.cell_values_decoded
        observation.unexpected_field_observation_count += patch_observation.unexpected_field_observation_count
        observation.unexpected_value_materialization_count += patch_observation.unexpected_value_materialization_count
        observation.unexpected_value_log_count += patch_observation.unexpected_value_log_count
        observation.unexpected_value_serialization_count += patch_observation.unexpected_value_serialization_count
        south_candidates, north_candidates = _build_candidates(
            root_rows, north_rows, south_rows, patch_rows, metrics)
        ordered_south, sequence_hashes["south"], south_ties = order_candidates(south_candidates)
        ordered_north, sequence_hashes["north"], north_ties = order_candidates(north_candidates)
        metrics.tie_count = south_ties + north_ties
        if not ordered_south or not ordered_north:
            raise SelectionError("TECHNICAL_SELECTION_ELIGIBILITY_FAILURE")
        selected = (ordered_south[0], ordered_north[0])
        if selected[0].brickname == selected[1].brickname:
            raise SelectionError("TECHNICAL_SELECTION_DISTINCT_BRICKS_FAILURE")
        metrics.selected_count = 2; metrics.south_count = 1; metrics.north_count = 1
        csv_bytes = _csv(selected)
        terminal_value = SUCCESS_TERMINAL
    except SelectionError as exc:
        error_code = exc.code; terminal_value = FAILURE_TERMINAL; csv_bytes = None
    except PatchDecodeError as exc:
        if exc.code == "PATCH_RESOURCE_LIMIT_STOP":
            error_code = "TECHNICAL_SELECTION_RESOURCE_LIMIT_STOP"
        elif "FIELD" in exc.code or "PHYSICAL" in exc.code:
            error_code = "TECHNICAL_SELECTION_FIELD_BOUNDARY_FAILURE"
        else:
            error_code = "TECHNICAL_SELECTION_INPUT_BINDING_FAILURE"
        terminal_value = FAILURE_TERMINAL; csv_bytes = None
    except Exception:
        error_code = "TECHNICAL_SELECTION_INTERNAL_FAILURE"; terminal_value = FAILURE_TERMINAL; csv_bytes = None
    wall, compute = accounting.guard.elapsed()
    if wall > WALL_SECONDS_CAP or compute > COMPUTE_SECONDS_CAP:
        error_code = "TECHNICAL_SELECTION_RESOURCE_LIMIT_STOP"; terminal_value = FAILURE_TERMINAL; csv_bytes = None
    aggregate = {
        "candidate_sequence_sha256": sequence_hashes,
        "compute_seconds": compute,
        "csv_sha256": hashlib.sha256(csv_bytes).hexdigest() if csv_bytes is not None else None,
        "decoder_observation": observation.object(),
        "local_io_bytes": accounting.local_io_bytes,
        "metrics": metrics.object(),
        "stage_id": STAGE_ID,
        "wall_seconds": wall,
    }
    terminal = {"first_error_code": error_code, "stage_id": STAGE_ID,
                "successful": terminal_value == SUCCESS_TERMINAL, "terminal": terminal_value}
    values = _encode_audit(binding, aggregate, terminal)
    selected_names = tuple(candidate.brickname for candidate in selected)
    leakage = sum(1 for name in selected_names if any(name in body for body in values.values()))
    metrics.row_level_leakage_count = leakage
    if leakage:
        terminal = {"first_error_code": "TECHNICAL_SELECTION_OUTPUT_FIREWALL_FAILURE",
                    "stage_id": STAGE_ID, "successful": False, "terminal": FAILURE_TERMINAL}
        csv_bytes = None
    # Resolve local-I/O reporting after final audit encoding.
    base_io = accounting.local_io_bytes; output_bytes = 0
    for _ in range(4):
        aggregate["local_io_bytes"] = base_io + output_bytes
        aggregate["metrics"] = metrics.object()
        aggregate["csv_sha256"] = hashlib.sha256(csv_bytes).hexdigest() if csv_bytes is not None else None
        values = _encode_audit(binding, aggregate, terminal)
        revised = sum(map(len, values.values())) + len(csv_bytes or b"")
        if revised == output_bytes: break
        output_bytes = revised
    else:
        raise SelectionError("TECHNICAL_SELECTION_RESOURCE_LIMIT_STOP")
    try:
        accounting.charge_io(output_bytes)
    except PatchDecodeError as exc:
        raise SelectionError("TECHNICAL_SELECTION_RESOURCE_LIMIT_STOP") from exc
    _publish(output_csv, audit_directory, csv_bytes, values)
    return {"aggregate": aggregate, "binding": binding, "terminal": terminal}


def run_production(attempt: Path, patch_evidence: Path, output_csv: Path,
                   audit_directory: Path) -> dict[str, object]:
    output_csv = Path(output_csv); audit_directory = Path(audit_directory)
    if (not output_csv.is_absolute() or output_csv.resolve() != OUTPUT_CSV or
            str(output_csv) != str(OUTPUT_CSV) or not audit_directory.is_absolute() or
            audit_directory.resolve() != AUDIT_DIRECTORY or
            str(audit_directory) != str(AUDIT_DIRECTORY)):
        raise SelectionError("TECHNICAL_SELECTION_INPUT_BINDING_FAILURE")
    accounting = ResourceAccounting(guard=SelectionRuntimeGuard())
    inputs = production_inputs(attempt, patch_evidence, accounting)
    return execute_stage(inputs, output_csv, audit_directory,
                         current_implementation=implementation_hash(PROJECT), accounting=accounting)


def dry_run(attempt: Path, patch_evidence: Path, output_csv: Path,
            audit_directory: Path) -> dict[str, object]:
    if (Path(attempt) != ATTEMPT or Path(patch_evidence) != PATCH_EVIDENCE or
            Path(output_csv) != OUTPUT_CSV or Path(audit_directory) != AUDIT_DIRECTORY or
            Path(output_csv).exists() or Path(audit_directory).exists()):
        raise SelectionError("TECHNICAL_SELECTION_INPUT_BINDING_FAILURE")
    return {"audit_directory": str(AUDIT_DIRECTORY), "network_bytes": 0,
            "network_requests": 0, "output_csv": str(OUTPUT_CSV), "stage_id": STAGE_ID,
            "state": "TECHNICAL_SELECTION_DRY_RUN_OK"}
