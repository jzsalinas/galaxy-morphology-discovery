"""Closed, offline PATCH metadata decode stage.

This module has no transport abstraction and accepts no URL.  It observes only
the three frozen PATCH fields and emits aggregate evidence without row values.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import gzip
import hashlib
import json
import os
from pathlib import Path
import resource
import struct
import threading
import time
from types import MappingProxyType
from typing import Iterable

from .core import canonical, implementation_hash
from .metadata_bootstrap import DecodeInstrumentation, SelectiveFitsDecoder, _table_location, _tform
from .metadata_value_semantics import (
    PATCH_CARDINALITY, PATCH_RELEASE, JoinRowInput, PatchRowInput,
    ValidatedPatchList, validate_complete_patch_rows, validate_join_row,
    validate_patch_joins,
)
from .provider_physical_contracts import (
    PRODUCTION_PHYSICAL_CONTRACTS, FrozenPhysicalContract, PhysicalRole,
)


STAGE_ID = "OC3-PATCH-METADATA-DECODE-001"
SUCCESS_TERMINAL = "PATCH_METADATA_DECODE_VALIDATED"
FAILURE_TERMINAL = "PATCH_METADATA_DECODE_FAILED"
SPEC_SHA256 = "bd0ebfba5a91a37522f672871d495794dd2af79fe629701073c2e72eb9019785"
SOURCE_BOOTSTRAP_IMPLEMENTATION = "432bcd449673786075938d3a290ad0ea139cc88bf1c2aae758c59d09179ef276"
SOURCE_AUTHORIZATION_SHA256 = "214d361fe163da1417e14d61efa203b3bdb97f15c4d7b6481aa50c2643345b56"
SOURCE_ENVIRONMENT = "b49e26767922123113707a13434821d6bf1d7711f28a2b9de7e5ce46d64e3bdf"
SOURCE_LEDGER_IDENTITY = "c2fea670f7d4594cbe4b9a889f7b95f0f06a7fe81d218198cfef817e62dafc07"
PROVIDER_PUBLISHED_CHECKSUM_KNOWN = False
PROJECT = Path("/home/jzsalinas/Documents/galaxy-morphology-discovery")
ATTEMPT = PROJECT / "oc3/metadata_bootstrap/OC3-METADATA-BOOTSTRAP-001"
OUTPUT = PROJECT / "oc3/patch_metadata_decode/OC3-PATCH-METADATA-DECODE-001"

PATCH_RELATIVE = Path("RAW_IMMUTABLE/SOUTH_PATCH_LIST/dr9-south-patched-bricks.fits")
ROOT_RELATIVE = Path("RAW_IMMUTABLE/ROOT_SUMMARY/survey-bricks.fits.gz")
SOUTH_RELATIVE = Path("RAW_IMMUTABLE/SOUTH_SUMMARY/survey-bricks-dr9-south.fits.gz")
PATCH_ALLOWED_FIELDS = ("RELEASE", "BRICKID", "BRICKNAME")
REFERENCE_ALLOWED_FIELDS = ("BRICKNAME", "BRICKID")
EXPECTED_RAW = MappingProxyType({
    PhysicalRole.SOUTH_PATCH_LIST: (PATCH_RELATIVE, 31_680,
        "f87e7aa55360b935033fc0638491038e7170cc9b88fc6c0905000d420280f6b6"),
    PhysicalRole.ROOT_SUMMARY: (ROOT_RELATIVE, 13_147_987,
        "dc943d702357f93553b9e5d15e87ace38df94eb7095f4100657407b3f9919c5f"),
    PhysicalRole.SOUTH_SUMMARY: (SOUTH_RELATIVE, 55_399_879,
        "7360414f5d53571ca70fa0cb483eb8c80cfcbe80df0856a117246f442a0b9a3f"),
})
EXPECTED_EVIDENCE = MappingProxyType({
    "BOOTSTRAP_TERMINAL.json": "6ca38830d7b8f364dbfb722f4c56de4697f80f9be705004d0897b3a13bdccef0",
    "PATCH_ACQUISITION_BOUND_EVIDENCE.json": "2dfad6faf65c48488d14f8aaacfb5e4a3638f5ac61161aa829e90f59ade04f37",
    "BOOTSTRAP_SEMANTIC_SUMMARY.json": "a0dd0c9bfa684a811c8033ade346d28381d6739a1991840bb23dacd00e7c9a7e",
    "BOOTSTRAP_RAW_FILE_MANIFEST.json": "021c31736ee19af4d137f35404a266140b2aac90349607f58bb0815df719ea2a",
    "BOOTSTRAP_LEDGER.sqlite": "ff6957e3c74001356edd104d13e4e213f9aba29d04578ea4d680dd390cf8f270",
})
OUTPUT_FILES = (
    "PATCH_DECODE_INPUT_BINDING.json",
    "PATCH_DECODE_AGGREGATE_EVIDENCE.json",
    "PATCH_DECODE_TERMINAL.json",
    "PATCH_DECODE_RUN.log",
)
CAPS = MappingProxyType({
    "network_requests": 0, "network_bytes": 0, "concurrency": 1,
    "threads": 1, "gpu": 0, "ram_bytes": 1_073_741_824,
    "local_io_bytes": 536_870_912, "output_bytes": 1_048_576,
    "compute_seconds": 300, "wall_seconds": 900,
})


class PatchDecodeError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class RuntimeGuard:
    """Cooperative fail-closed guard used throughout local reads and row scans."""

    def __init__(self):
        self.wall_start = time.monotonic()
        self.cpu_start = time.process_time()

    def check(self) -> None:
        if (time.monotonic() - self.wall_start > CAPS["wall_seconds"] or
                time.process_time() - self.cpu_start > CAPS["compute_seconds"] or
                threading.active_count() > CAPS["threads"]):
            raise PatchDecodeError("PATCH_RESOURCE_LIMIT_STOP")
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        peak_bytes = peak * 1024 if peak < 2**40 else peak
        if peak_bytes > CAPS["ram_bytes"]:
            raise PatchDecodeError("PATCH_RESOURCE_LIMIT_STOP")

    def elapsed(self) -> tuple[int, int]:
        return (int(time.monotonic() - self.wall_start),
                int(time.process_time() - self.cpu_start))


@dataclass
class ResourceAccounting:
    local_io_bytes: int = 0
    guard: RuntimeGuard = field(default_factory=RuntimeGuard)

    def read_bytes(self, path: Path) -> bytes:
        path = Path(path)
        size = path.stat().st_size
        self.charge_io(size)
        data = path.read_bytes()
        if len(data) != size:
            raise PatchDecodeError("PATCH_INPUT_BINDING_FAILURE")
        self.guard.check()
        return data

    def hash_file(self, path: Path) -> str:
        path = Path(path)
        expected_size = path.stat().st_size
        self.charge_io(expected_size)
        digest = hashlib.sha256()
        size = 0
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk); size += len(chunk); self.guard.check()
        if size != expected_size:
            raise PatchDecodeError("PATCH_INPUT_BINDING_FAILURE")
        return digest.hexdigest()

    def charge_io(self, amount: int) -> None:
        if type(amount) is not int or amount < 0 or self.local_io_bytes + amount > CAPS["local_io_bytes"]:
            raise PatchDecodeError("PATCH_RESOURCE_LIMIT_STOP")
        self.local_io_bytes += amount

    def check(self) -> None:
        self.guard.check()


@dataclass(frozen=True)
class StageInputs:
    attempt: Path
    patch: Path
    root: Path
    south: Path
    expected_hashes: MappingProxyType
    contracts: MappingProxyType
    source_bootstrap_implementation: str
    source_authorization_sha256: str
    source_environment: str
    source_ledger_identity: str
    synthetic_only: bool


@dataclass
class PatchObservation:
    decoded_fields: tuple[str, ...] = PATCH_ALLOWED_FIELDS
    opaque_bytes_transited: int = 0
    cell_values_decoded: int = 0
    unexpected_field_observation_count: int = 0
    unexpected_value_materialization_count: int = 0
    unexpected_value_log_count: int = 0
    unexpected_value_serialization_count: int = 0
    field_boundary_tripwire_count: int = 0

    def object(self) -> dict[str, object]:
        return {
            "cell_values_decoded": self.cell_values_decoded,
            "decoded_fields": list(self.decoded_fields),
            "field_boundary_tripwire_count": self.field_boundary_tripwire_count,
            "opaque_bytes_transited": self.opaque_bytes_transited,
            "unexpected_field_observation_count": self.unexpected_field_observation_count,
            "unexpected_value_log_count": self.unexpected_value_log_count,
            "unexpected_value_materialization_count": self.unexpected_value_materialization_count,
            "unexpected_value_serialization_count": self.unexpected_value_serialization_count,
        }


@dataclass
class StageMetrics:
    row_count: int = 0
    valid_row_count: int = 0
    release_valid_count: int = 0
    unique_brickname_count: int = 0
    unique_brickid_count: int = 0
    unique_pair_count: int = 0
    exact_root_matches: int = 0
    exact_south_matches: int = 0
    missing_from_root: int = 0
    missing_from_south: int = 0
    multiplicity_failures: int = 0
    brickid_mismatches: int = 0
    brickname_mismatches: int = 0
    ambiguous_joins: int = 0
    output_row_level_leakage_count: int = 0
    network_requests: int = 0
    network_bytes: int = 0

    def object(self) -> dict[str, int]:
        return {
            "ambiguous_joins": self.ambiguous_joins,
            "brickid_mismatches": self.brickid_mismatches,
            "brickname_mismatches": self.brickname_mismatches,
            "exact_ROOT_matches": self.exact_root_matches,
            "exact_SOUTH_matches": self.exact_south_matches,
            "missing_from_ROOT": self.missing_from_root,
            "missing_from_SOUTH": self.missing_from_south,
            "multiplicity_failures": self.multiplicity_failures,
            "network_bytes": self.network_bytes,
            "network_requests": self.network_requests,
            "output_row_level_leakage_count": self.output_row_level_leakage_count,
            "release_valid_count": self.release_valid_count,
            "row_count": self.row_count,
            "unique_BRICKID_count": self.unique_brickid_count,
            "unique_BRICKNAME_count": self.unique_brickname_count,
            "unique_pair_count": self.unique_pair_count,
            "valid_row_count": self.valid_row_count,
        }


def _strict_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate key")
        value[key] = item
    return value


def _load_evidence(path: Path, expected_sha: str, accounting: ResourceAccounting) -> dict:
    raw = accounting.read_bytes(path)
    if hashlib.sha256(raw).hexdigest() != expected_sha:
        raise PatchDecodeError("PATCH_INPUT_BINDING_FAILURE")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_strict_object)
    except (UnicodeError, ValueError) as exc:
        raise PatchDecodeError("PATCH_INPUT_BINDING_FAILURE") from exc
    if not isinstance(value, dict) or raw != canonical(value) + b"\n":
        raise PatchDecodeError("PATCH_INPUT_BINDING_FAILURE")
    return value


def _require_binding(value: dict) -> None:
    binding = value.get("binding")
    if (not isinstance(binding, dict) or
            binding.get("attempt_id") != "OC3-METADATA-BOOTSTRAP-001" or
            binding.get("authorization_sha256") != SOURCE_AUTHORIZATION_SHA256 or
            binding.get("implementation_aggregate") != SOURCE_BOOTSTRAP_IMPLEMENTATION or
            binding.get("environment_fingerprint") != SOURCE_ENVIRONMENT or
            binding.get("ledger_identity") != SOURCE_LEDGER_IDENTITY or
            binding.get("synthetic_only") is not False):
        raise PatchDecodeError("PATCH_INPUT_BINDING_FAILURE")


def production_inputs(attempt: Path, accounting: ResourceAccounting) -> StageInputs:
    attempt = Path(attempt)
    if (not attempt.is_absolute() or str(attempt) != str(ATTEMPT) or
            attempt.resolve() != ATTEMPT or not attempt.is_dir()):
        raise PatchDecodeError("PATCH_INPUT_BINDING_FAILURE")
    loaded = {name: _load_evidence(attempt / name, digest, accounting)
              for name, digest in EXPECTED_EVIDENCE.items() if name.endswith(".json")}
    terminal = loaded["BOOTSTRAP_TERMINAL.json"]
    patch_evidence = loaded["PATCH_ACQUISITION_BOUND_EVIDENCE.json"]
    semantic = loaded["BOOTSTRAP_SEMANTIC_SUMMARY.json"]
    manifest = loaded["BOOTSTRAP_RAW_FILE_MANIFEST.json"]
    for value in loaded.values():
        _require_binding(value)
    if (terminal.get("outcome") != "METADATA_BOOTSTRAP_PARTIALLY_RESOLVED" or
            terminal.get("successful") is not True or terminal.get("first_error_code") is not None or
            terminal.get("ledger_sha256") != EXPECTED_EVIDENCE["BOOTSTRAP_LEDGER.sqlite"] or
            terminal.get("incomplete_staging") != []):
        raise PatchDecodeError("PATCH_INPUT_BINDING_FAILURE")
    if (patch_evidence.get("state") != "PATCH_ACQUISITION_BOUND_PENDING_HUMAN_REVIEW" or
            patch_evidence.get("local_sha256") != EXPECTED_RAW[PhysicalRole.SOUTH_PATCH_LIST][2] or
            patch_evidence.get("acquired_byte_count") != 31_680 or
            patch_evidence.get("payload_bytes_observed") != 0 or
            patch_evidence.get("row_decoder_calls") != 0):
        raise PatchDecodeError("PATCH_INPUT_BINDING_FAILURE")
    if (semantic.get("patch_membership") != "NOT_OBSERVED" or
            semantic.get("patch_row_semantics") != "NOT_OBSERVED" or
            semantic.get("row_values_persisted") is not False or
            semantic.get("forbidden_values_observed") is not False):
        raise PatchDecodeError("PATCH_INPUT_BINDING_FAILURE")
    manifest_rows = {item.get("role"): item for item in manifest.get("resources", [])
                     if isinstance(item, dict)}
    expected_hashes = {}
    for role, (relative, size, digest) in EXPECTED_RAW.items():
        path = attempt / relative
        row = manifest_rows.get(role.value)
        if (not path.is_file() or path.is_symlink() or path.stat().st_size != size or
                path.stat().st_mode & 0o222 or
                not isinstance(row, dict) or row.get("raw_relative_path") != str(relative) or
                row.get("raw_byte_length") != size or row.get("raw_sha256") != digest or
                accounting.hash_file(path) != digest):
            raise PatchDecodeError("PATCH_INPUT_BINDING_FAILURE")
        expected_hashes[role] = digest
    if accounting.hash_file(attempt / "BOOTSTRAP_LEDGER.sqlite") != EXPECTED_EVIDENCE["BOOTSTRAP_LEDGER.sqlite"]:
        raise PatchDecodeError("PATCH_INPUT_BINDING_FAILURE")
    return StageInputs(
        attempt=attempt, patch=attempt / PATCH_RELATIVE, root=attempt / ROOT_RELATIVE,
        south=attempt / SOUTH_RELATIVE, expected_hashes=MappingProxyType(expected_hashes),
        contracts=PRODUCTION_PHYSICAL_CONTRACTS,
        source_bootstrap_implementation=SOURCE_BOOTSTRAP_IMPLEMENTATION,
        source_authorization_sha256=SOURCE_AUTHORIZATION_SHA256,
        source_environment=SOURCE_ENVIRONMENT, source_ledger_identity=SOURCE_LEDGER_IDENTITY,
        synthetic_only=False,
    )


def _validate_table(data: bytes, contract: FrozenPhysicalContract) -> tuple[int, int, list[tuple[int, int, str, str]]]:
    try:
        header, data_start = _table_location(data, contract)
        expected = {
            "XTENSION": contract.xtension, "BITPIX": contract.bitpix,
            "NAXIS": contract.naxis, "NAXIS1": contract.naxis1,
            "NAXIS2": contract.naxis2, "PCOUNT": contract.pcount,
            "GCOUNT": contract.gcount, "TFIELDS": contract.tfields,
        }
        if any(header.get(key) != value for key, value in expected.items()):
            raise PatchDecodeError("PATCH_PHYSICAL_CONTRACT_FAILURE")
        offsets = []; offset = 0
        for index, column in enumerate(contract.columns, 1):
            if (header.get(f"TTYPE{index}") != column.ttype or
                    header.get(f"TFORM{index}") != column.tform):
                raise PatchDecodeError("PATCH_PHYSICAL_CONTRACT_FAILURE")
            _, _, width = _tform(column.tform)
            offsets.append((offset, width, column.tform, column.ttype)); offset += width
        row_size = header.get("NAXIS1"); rows = header.get("NAXIS2")
        if type(row_size) is not int or type(rows) is not int or row_size != offset:
            raise PatchDecodeError("PATCH_PHYSICAL_CONTRACT_FAILURE")
        if data_start + row_size * rows > len(data):
            raise PatchDecodeError("PATCH_INPUT_BINDING_FAILURE")
        return data_start, rows, offsets
    except PatchDecodeError:
        raise
    except Exception as exc:
        raise PatchDecodeError("PATCH_PHYSICAL_CONTRACT_FAILURE") from exc


class PatchSelectiveFitsDecoder(SelectiveFitsDecoder):
    """Stage-scoped manual decoder; no generic PATCH record is constructed."""

    def __init__(self, accounting: ResourceAccounting):
        self.accounting = accounting

    def _data(self, path: Path, contract: FrozenPhysicalContract) -> bytes:
        raw = self.accounting.read_bytes(path)
        try:
            return gzip.decompress(raw) if contract.compression == "gzip" else raw
        except Exception as exc:
            raise PatchDecodeError("PATCH_INPUT_BINDING_FAILURE") from exc

    def decode_patch(self, path: Path, contract: FrozenPhysicalContract,
                     observation: PatchObservation) -> tuple[PatchRowInput, ...]:
        if contract.role is not PhysicalRole.SOUTH_PATCH_LIST:
            raise PatchDecodeError("PATCH_FIELD_BOUNDARY_FAILURE")
        names = tuple(column.ttype for column in contract.columns)
        if names != PATCH_ALLOWED_FIELDS:
            observation.field_boundary_tripwire_count += 1
            raise PatchDecodeError("PATCH_FIELD_BOUNDARY_FAILURE")
        data = self._data(path, contract)
        data_start, nrows, offsets = _validate_table(data, contract)
        by_name = {name: (offset, width, tform) for offset, width, tform, name in offsets}
        rows = []
        for row_index in range(nrows):
            if row_index % 8192 == 0:
                self.accounting.check()
            base = data_start + contract.naxis1 * row_index
            release_offset, release_width, _ = by_name["RELEASE"]
            brickid_offset, brickid_width, _ = by_name["BRICKID"]
            name_offset, name_width, _ = by_name["BRICKNAME"]
            release = struct.unpack(">h", data[base + release_offset:base + release_offset + release_width])[0]
            brickid = struct.unpack(">i", data[base + brickid_offset:base + brickid_offset + brickid_width])[0]
            brickname = bytes(data[base + name_offset:base + name_offset + name_width])
            rows.append(PatchRowInput(release, brickid, brickname))
            observation.cell_values_decoded += 3
        observation.opaque_bytes_transited += contract.naxis1 * nrows
        return tuple(rows)

    def decode_references(self, path: Path, contract: FrozenPhysicalContract) -> tuple[JoinRowInput, ...]:
        if contract.role not in (PhysicalRole.ROOT_SUMMARY, PhysicalRole.SOUTH_SUMMARY):
            raise PatchDecodeError("PATCH_FIELD_BOUNDARY_FAILURE")
        data = self._data(path, contract)
        data_start, nrows, offsets = _validate_table(data, contract)
        wanted = ("BRICKNAME", "BRICKID") if contract.role is PhysicalRole.ROOT_SUMMARY else ("brickname", "brickid")
        by_name = {name: (offset, width, tform) for offset, width, tform, name in offsets}
        if any(name not in by_name for name in wanted):
            raise PatchDecodeError("PATCH_PHYSICAL_CONTRACT_FAILURE")
        name_offset, name_width, name_form = by_name[wanted[0]]
        id_offset, id_width, id_form = by_name[wanted[1]]
        if name_form != "8A" or id_form != "J" or name_width != 8 or id_width != 4:
            raise PatchDecodeError("PATCH_PHYSICAL_CONTRACT_FAILURE")
        rows = []
        for row_index in range(nrows):
            if row_index % 8192 == 0:
                self.accounting.check()
            base = data_start + contract.naxis1 * row_index
            name = bytes(data[base + name_offset:base + name_offset + name_width])
            brickid = struct.unpack(">i", data[base + id_offset:base + id_offset + id_width])[0]
            rows.append(JoinRowInput(name, brickid))
        return tuple(rows)


def _join_audit(patch: ValidatedPatchList, root_rows: Iterable[JoinRowInput],
                south_rows: Iterable[JoinRowInput], metrics: StageMetrics) -> None:
    def index(rows):
        result = {}
        for supplied in rows:
            row = validate_join_row(supplied)
            result.setdefault(row.brickname.raw, []).append(row)
        return result
    root = index(root_rows); south = index(south_rows)
    for member in patch.rows:
        root_matches = root.get(member.brickname.raw, ())
        south_matches = south.get(member.brickname.raw, ())
        if not root_matches: metrics.missing_from_root += 1
        if not south_matches: metrics.missing_from_south += 1
        for matches in (root_matches, south_matches):
            if len(matches) > 1:
                metrics.multiplicity_failures += 1
                metrics.ambiguous_joins += 1
            elif len(matches) == 1 and matches[0].brickid != member.brickid:
                metrics.brickid_mismatches += 1
        if len(root_matches) == 1 and root_matches[0].brickid == member.brickid:
            metrics.exact_root_matches += 1
        if len(south_matches) == 1 and south_matches[0].brickid == member.brickid:
            metrics.exact_south_matches += 1
    failures = (metrics.missing_from_root, metrics.missing_from_south,
                metrics.multiplicity_failures, metrics.brickid_mismatches,
                metrics.brickname_mismatches, metrics.ambiguous_joins)
    if any(failures):
        raise PatchDecodeError("PATCH_RELATIONAL_FAILURE")
    try:
        validate_patch_joins(patch, root_rows, south_rows)
    except Exception as exc:
        raise PatchDecodeError("PATCH_RELATIONAL_FAILURE") from exc


def _encode_outputs(binding: dict, aggregate: dict, terminal: dict) -> dict[str, bytes]:
    values = {
        "PATCH_DECODE_INPUT_BINDING.json": canonical(binding) + b"\n",
        "PATCH_DECODE_AGGREGATE_EVIDENCE.json": canonical(aggregate) + b"\n",
        "PATCH_DECODE_TERMINAL.json": canonical(terminal) + b"\n",
    }
    log = (
        f"stage_id={STAGE_ID}\nterminal={terminal['terminal']}\n"
        f"first_error_code={terminal['first_error_code']}\n"
        f"row_count={aggregate['metrics']['row_count']}\n"
        f"valid_row_count={aggregate['metrics']['valid_row_count']}\n"
        f"network_requests=0\noutput_row_level_leakage_count=0\n"
    ).encode("utf-8")
    values["PATCH_DECODE_RUN.log"] = log
    return values


def _write_outputs(output: Path, values: dict[str, bytes]) -> None:
    if set(values) != set(OUTPUT_FILES) or sum(len(item) for item in values.values()) > CAPS["output_bytes"]:
        raise PatchDecodeError("PATCH_RESOURCE_LIMIT_STOP")
    try:
        output.mkdir(parents=True, exist_ok=False)
        for name in OUTPUT_FILES:
            with (output / name).open("xb") as stream:
                stream.write(values[name]); stream.flush(); os.fsync(stream.fileno())
    except FileExistsError as exc:
        raise PatchDecodeError("PATCH_LOCAL_STATE_CONFLICT") from exc


def execute_stage(inputs: StageInputs, output: Path, *, current_implementation: str,
                  accounting: ResourceAccounting | None = None,
                  decoder_factory=PatchSelectiveFitsDecoder) -> dict[str, object]:
    accounting = accounting or ResourceAccounting()
    output = Path(output)
    metrics = StageMetrics(); observation = PatchObservation()
    error_code = None
    binding = {
        "acquisition_bound_local_sha256": inputs.expected_hashes[PhysicalRole.SOUTH_PATCH_LIST],
        "allowed_patch_fields": list(PATCH_ALLOWED_FIELDS),
        "current_implementation_aggregate": current_implementation,
        "input_paths": {
            "PATCH": str(inputs.patch), "ROOT": str(inputs.root), "SOUTH": str(inputs.south),
        },
        "provider_published_checksum_known": False,
        "source_authorization_sha256": inputs.source_authorization_sha256,
        "source_bootstrap_implementation": inputs.source_bootstrap_implementation,
        "source_environment": inputs.source_environment,
        "source_ledger_identity": inputs.source_ledger_identity,
        "spec_sha256": SPEC_SHA256,
        "stage_id": STAGE_ID,
        "synthetic_only": inputs.synthetic_only,
    }
    try:
        for role, path in ((PhysicalRole.SOUTH_PATCH_LIST, inputs.patch),
                           (PhysicalRole.ROOT_SUMMARY, inputs.root),
                           (PhysicalRole.SOUTH_SUMMARY, inputs.south)):
            if (not path.is_file() or accounting.hash_file(path) != inputs.expected_hashes[role]):
                raise PatchDecodeError("PATCH_INPUT_BINDING_FAILURE")
        decoder = decoder_factory(accounting)
        patch_rows = decoder.decode_patch(
            inputs.patch, inputs.contracts[PhysicalRole.SOUTH_PATCH_LIST], observation)
        metrics.row_count = len(patch_rows)
        try:
            patch = validate_complete_patch_rows(patch_rows)
        except Exception as exc:
            raise PatchDecodeError("PATCH_VALUE_SEMANTICS_FAILURE") from exc
        metrics.valid_row_count = len(patch.rows)
        metrics.release_valid_count = sum(row.release == PATCH_RELEASE for row in patch.rows)
        metrics.unique_brickname_count = len(patch.bricknames)
        metrics.unique_brickid_count = len(patch.brickids)
        metrics.unique_pair_count = len(patch.identity_pairs)
        root_rows = decoder.decode_references(inputs.root, inputs.contracts[PhysicalRole.ROOT_SUMMARY])
        south_rows = decoder.decode_references(inputs.south, inputs.contracts[PhysicalRole.SOUTH_SUMMARY])
        _join_audit(patch, root_rows, south_rows, metrics)
        if (observation.decoded_fields != PATCH_ALLOWED_FIELDS or
                any((observation.unexpected_field_observation_count,
                     observation.unexpected_value_materialization_count,
                     observation.unexpected_value_log_count,
                     observation.unexpected_value_serialization_count))):
            raise PatchDecodeError("PATCH_FIELD_BOUNDARY_FAILURE")
        terminal_value = SUCCESS_TERMINAL
    except PatchDecodeError as exc:
        error_code = exc.code; terminal_value = FAILURE_TERMINAL
    except Exception:
        error_code = "PATCH_METADATA_DECODE_INTERNAL_FAILURE"; terminal_value = FAILURE_TERMINAL
    wall, compute = accounting.guard.elapsed()
    if wall > CAPS["wall_seconds"] or compute > CAPS["compute_seconds"]:
        error_code = "PATCH_RESOURCE_LIMIT_STOP"; terminal_value = FAILURE_TERMINAL
    aggregate = {
        "compute_seconds": compute,
        "decoder_observation": observation.object(),
        "local_io_bytes": accounting.local_io_bytes,
        "metrics": metrics.object(),
        "stage_id": STAGE_ID,
        "wall_seconds": wall,
    }
    terminal = {
        "first_error_code": error_code,
        "stage_id": STAGE_ID,
        "successful": terminal_value == SUCCESS_TERMINAL,
        "terminal": terminal_value,
    }
    try:
        # Output writes count toward the local-I/O cap.  Resolve the tiny
        # self-reference in the reported counter before reserving the bytes.
        input_io = accounting.local_io_bytes
        output_bytes = 0
        for _ in range(4):
            aggregate["local_io_bytes"] = input_io + output_bytes
            values = _encode_outputs(binding, aggregate, terminal)
            revised = sum(len(item) for item in values.values())
            if revised == output_bytes:
                break
            output_bytes = revised
        else:
            raise PatchDecodeError("PATCH_RESOURCE_LIMIT_STOP")
        accounting.charge_io(output_bytes)
        if aggregate["local_io_bytes"] != accounting.local_io_bytes:
            raise PatchDecodeError("PATCH_RESOURCE_LIMIT_STOP")
        _write_outputs(output, values)
    except PatchDecodeError:
        if output.exists():
            raise
        raise
    return {"aggregate": aggregate, "binding": binding, "terminal": terminal}


def run_production(attempt: Path, output: Path) -> dict[str, object]:
    accounting = ResourceAccounting()
    inputs = production_inputs(attempt, accounting)
    current = implementation_hash(PROJECT)
    return execute_stage(inputs, output, current_implementation=current, accounting=accounting)


def dry_run(attempt: Path, output: Path) -> dict[str, object]:
    if (str(Path(attempt)) != str(ATTEMPT) or str(Path(output)) != str(OUTPUT) or
            Path(output).exists()):
        raise PatchDecodeError("PATCH_INPUT_BINDING_FAILURE")
    return {
        "allowed_patch_fields": list(PATCH_ALLOWED_FIELDS),
        "network_bytes": 0, "network_requests": 0,
        "output_directory": str(OUTPUT), "stage_id": STAGE_ID,
        "state": "PATCH_METADATA_DECODE_DRY_RUN_OK",
    }
