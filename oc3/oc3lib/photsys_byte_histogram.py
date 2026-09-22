"""Closed, offline observation of the frozen one-byte PHOTSYS position.

The production reader has one semantic capability: one ``os.pread`` of one
byte at the reviewed PHOTSYS offset for a supplied row ordinal.  It has no
identity, ROOT, join, generic-span, whole-row, or table-decoding capability.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import os
from pathlib import Path
from typing import Callable, Iterator, Sequence

from .core import canonical, implementation_hash
from .galaxy_eligibility_photsys_authority_probe import (
    PROJECT, file_sha256, load_canonical_json, sealed, sha256_bytes,
    validate_sealed, write_json_immutable,
)


STAGE_ID = "OC3-GALAXY-ELIGIBILITY-PHOTSYS-BYTE-HISTOGRAM-001"
SCOPE = "PHOTSYS_SINGLE_BYTE_DISTRIBUTION_ONLY"
SUCCESS = "PHOTSYS_RAW_BYTE_HISTOGRAM_OBSERVED"
READY = "READY_AT_REAL_PHOTSYS_BYTE_OBSERVATION_BOUNDARY"

INPUT_MISMATCH = "PHOTSYS_BYTE_HISTOGRAM_INPUT_MISMATCH_FAILED"
PHYSICAL_MISMATCH = "PHOTSYS_BYTE_HISTOGRAM_PHYSICAL_LAYOUT_MISMATCH_FAILED"
FORBIDDEN_SPAN = "PHOTSYS_BYTE_HISTOGRAM_FORBIDDEN_SPAN_ACCESS_FAILED"
WHOLE_ROW = "PHOTSYS_BYTE_HISTOGRAM_WHOLE_ROW_MATERIALIZATION_FAILED"
IDENTITY_OR_ROOT = "PHOTSYS_BYTE_HISTOGRAM_IDENTITY_OR_ROOT_ACCESS_FAILED"
ROW_COUNT_MISMATCH = "PHOTSYS_BYTE_HISTOGRAM_ROW_COUNT_MISMATCH_FAILED"
INCOMPLETE = "PHOTSYS_BYTE_HISTOGRAM_INCOMPLETE"
TOTAL_MISMATCH = "PHOTSYS_BYTE_HISTOGRAM_TOTAL_MISMATCH_FAILED"
V1_MISMATCH = "PHOTSYS_BYTE_HISTOGRAM_V1_CONSISTENCY_MISMATCH_FAILED"
INCONCLUSIVE = "PHOTSYS_BYTE_HISTOGRAM_INCONCLUSIVE"

TERMINAL_PRECEDENCE = (
    FORBIDDEN_SPAN, WHOLE_ROW, IDENTITY_OR_ROOT, INPUT_MISMATCH,
    PHYSICAL_MISMATCH, ROW_COUNT_MISMATCH, INCOMPLETE, TOTAL_MISMATCH,
    V1_MISMATCH, SUCCESS,
)

SPEC_PATH = PROJECT / "OC3_PHOTSYS_OUT_OF_DOMAIN_BYTE_HISTOGRAM_SPEC.md"
SPEC_SHA256 = "127679c83acc9b7dc4e72a559b7b17857c7e53f2e4f63532675eeb13dfa10748"
V1_REVIEW_PATH = PROJECT / "OC3_PHOTSYS_SELECTIVE_VALUE_VALIDATION_POST_EXECUTION_REVIEW.md"
V1_REVIEW_SHA256 = "6b689ba5aff89131d09506ce0827c2aabc59fad3935d3740db3eee019de9d772"
PHOTSYS_PATH = PROJECT / (
    "oc3/photsys_authority_full_acquisition/"
    "OC3-GALAXY-ELIGIBILITY-PHOTSYS-AUTHORITY-ACQUISITION-001/"
    "RAW_IMMUTABLE/survey-bricks-dr9-randoms-0.48.0.fits"
)
PHOTSYS_SHA256 = "804d2caf327e808bb4047cc8792a5b08d01d8875149b7b7eb019ce982f6c3f8c"
PHOTSYS_BYTES = 52_323_840
REVIEWED_CONTRACT_PATH = PROJECT / "oc3/INPUTS/OC3_PHOTSYS_AUTHORITY_REVIEWED_PHYSICAL_CONTRACT_001.json"
REVIEWED_CONTRACT_SHA256 = "30b03a47adfc5cb1cc18b8c930dee2fa1d3f04597768558f84602d6ed2aae56f"
V1_RUNTIME = PROJECT / "oc3/photsys_selective_value_validation" / (
    "OC3-GALAXY-ELIGIBILITY-PHOTSYS-SELECTIVE-VALUE-VALIDATION-001"
)
V1_TERMINAL_PATH = V1_RUNTIME / "TERMINAL.json"
V1_TERMINAL_SHA256 = "ad817611054ace2daf395cebaa3a3bf70bfc90dac7f05a0f040366fdd1b241d8"
V1_AGGREGATES_PATH = V1_RUNTIME / "VALIDATION_AGGREGATES.json"
V1_AGGREGATES_SHA256 = "c0a7a0322a9f626e1d215717458b401ed260946211743bcea6f40abc065143af"
V1_OBSERVABILITY_PATH = V1_RUNTIME / "OBSERVABILITY.json"
V1_OBSERVABILITY_SHA256 = "977be060d5439908c0a47884ea2fe7c6211e4d1f7195f73ca4a060ef90bd420b"

CANDIDATE_PATH = PROJECT / "oc3/INPUTS/OC3_PHOTSYS_RAW_BYTE_HISTOGRAM_CANDIDATE_001.json"
AUTHORIZATION_PATH = PROJECT / "oc3/OC3_PHOTSYS_RAW_BYTE_HISTOGRAM_FINAL_AUTHORIZATION_001.json"
OUTPUT_ROOT = PROJECT / "oc3/photsys_byte_histogram" / STAGE_ID
HISTOGRAM_FILENAME = "OC3_PHOTSYS_RAW_BYTE_HISTOGRAM_001.json"

EXPECTED_N = 82_897
EXPECTED_S = 249_069
EXPECTED_SPACE = 0
EXPECTED_V1_TOTAL = 331_966
EXPECTED_OUTSIDE = 330_208
EXPECTED_ROWS = 662_174
MAX_SIGNED_OFFSET = 2**63 - 1


class HistogramError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class HistogramLayout:
    data_offset: int
    row_count: int
    row_width: int
    file_size: int
    photsys_offset: int = 70
    photsys_width: int = 1

    def validate(self) -> None:
        values = (self.data_offset, self.row_count, self.row_width,
                  self.file_size, self.photsys_offset, self.photsys_width)
        if any(type(value) is not int or value < 0 for value in values):
            raise HistogramError(PHYSICAL_MISMATCH)
        if (self.photsys_width != 1 or self.photsys_offset + 1 > self.row_width or
                self.data_offset + self.row_count * self.row_width > self.file_size or
                self.file_size > MAX_SIGNED_OFFSET):
            raise HistogramError(PHYSICAL_MISMATCH)


PRODUCTION_LAYOUT = HistogramLayout(11_520, EXPECTED_ROWS, 79, PHOTSYS_BYTES)


@dataclass
class HistogramCounters:
    rows_processed: int = 0
    authorized_PHOTSYS_bytes_observed: int = 0
    single_byte_pread_count: int = 0
    forbidden_span_access_count: int = 0
    whole_row_materialization_count: int = 0
    BRICKNAME_values_observed: int = 0
    BRICKID_values_observed: int = 0
    ROOT_values_observed: int = 0
    network_requests: int = 0

    def object(self) -> dict[str, int]:
        return asdict(self)

    def prohibited_clean(self) -> bool:
        return all(getattr(self, name) == 0 for name in (
            "forbidden_span_access_count", "whole_row_materialization_count",
            "BRICKNAME_values_observed", "BRICKID_values_observed",
            "ROOT_values_observed", "network_requests",
        ))


class ExactPhotsysByteReader:
    """Closed reader whose only public semantic operation returns one raw byte."""

    __slots__ = ("path", "counters", "layout", "_pread", "_fd", "synthetic_only")

    def __init__(self, path: Path, counters: HistogramCounters, *,
                 layout: HistogramLayout = PRODUCTION_LAYOUT,
                 pread: Callable[[int, int, int], bytes] = os.pread,
                 synthetic_only: bool = False):
        self.path = Path(path)
        self.counters = counters
        self.layout = layout
        self._pread = pread
        self._fd: int | None = None
        self.synthetic_only = synthetic_only
        layout.validate()
        if not synthetic_only and layout != PRODUCTION_LAYOUT:
            raise HistogramError(PHYSICAL_MISMATCH)

    def boundary_ready(self) -> None:
        if not self.path.is_file():
            raise HistogramError(INPUT_MISMATCH)
        if not self.synthetic_only and self.path.resolve() != PHOTSYS_PATH.resolve():
            raise HistogramError(INPUT_MISMATCH)

    def __enter__(self) -> "ExactPhotsysByteReader":
        self.boundary_ready()
        self._fd = os.open(self.path, os.O_RDONLY)
        return self

    def __exit__(self, *_: object) -> None:
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None

    def _read_photsys_byte(self, row_ordinal: int, *,
                           relative_offset: int = 70, length: int = 1) -> bytes:
        # Every request property is checked before the sole I/O primitive.
        if (type(row_ordinal) is not int or row_ordinal < 0 or
                row_ordinal >= self.layout.row_count or
                type(relative_offset) is not int or type(length) is not int or
                relative_offset != self.layout.photsys_offset or length != 1):
            self.counters.forbidden_span_access_count += 1
            raise HistogramError(FORBIDDEN_SPAN)
        product = row_ordinal * self.layout.row_width
        offset = self.layout.data_offset + product + relative_offset
        expected = self.layout.data_offset + row_ordinal * self.layout.row_width + 70
        if (product > MAX_SIGNED_OFFSET or offset > MAX_SIGNED_OFFSET or
                offset != expected or offset < self.layout.data_offset or
                offset + 1 > self.layout.file_size or
                relative_offset + 1 > self.layout.row_width):
            self.counters.forbidden_span_access_count += 1
            raise HistogramError(FORBIDDEN_SPAN)
        if self._fd is None:
            raise HistogramError(INCONCLUSIVE)
        raw = self._pread(self._fd, 1, offset)
        self.counters.single_byte_pread_count += 1
        if type(raw) is not bytes or len(raw) != 1:
            raise HistogramError(INCOMPLETE)
        self.counters.authorized_PHOTSYS_bytes_observed += 1
        self.counters.rows_processed += 1
        return raw

    def read_photsys_byte(self, row_ordinal: int) -> bytes:
        return self._read_photsys_byte(row_ordinal)

    def iter_photsys_bytes(self) -> Iterator[bytes]:
        for row_ordinal in range(self.layout.row_count):
            yield self.read_photsys_byte(row_ordinal)


def reject_whole_row_attempt(counters: HistogramCounters) -> None:
    counters.whole_row_materialization_count += 1
    raise HistogramError(WHOLE_ROW)


def reject_identity_or_root_attempt(capability: str, counters: HistogramCounters) -> None:
    target = {"BRICKNAME": "BRICKNAME_values_observed",
              "BRICKID": "BRICKID_values_observed", "ROOT": "ROOT_values_observed"}
    if capability in target:
        setattr(counters, target[capability], getattr(counters, target[capability]) + 1)
    raise HistogramError(IDENTITY_OR_ROOT)


def histogram_from_raw_bytes(values: Sequence[bytes]) -> list[int]:
    counts = [0] * 256
    for raw in values:
        if type(raw) is not bytes or len(raw) != 1:
            raise HistogramError(INCONCLUSIVE)
        counts[raw[0]] += 1
    return counts


def observe_histogram(reader: ExactPhotsysByteReader,
                      progress: Callable[[], None] | None = None) -> list[int]:
    counts = [0] * 256
    for raw in reader.iter_photsys_bytes():
        counts[raw[0]] += 1
        if progress is not None and reader.counters.rows_processed % 10_000 == 0:
            progress()
    return counts


def terminal_outcome(counters: HistogramCounters, histogram_counts: object | None,
                     *, complete: bool = True,
                     input_valid: bool = True, physical_valid: bool = True) -> str:
    # Frozen precedence: the first satisfied condition wins.
    if counters.forbidden_span_access_count:
        return FORBIDDEN_SPAN
    if counters.whole_row_materialization_count:
        return WHOLE_ROW
    if any((counters.BRICKNAME_values_observed, counters.BRICKID_values_observed,
            counters.ROOT_values_observed)):
        return IDENTITY_OR_ROOT
    if not input_valid:
        return INPUT_MISMATCH
    if not physical_valid:
        return PHYSICAL_MISMATCH
    if (counters.rows_processed != EXPECTED_ROWS or
            counters.authorized_PHOTSYS_bytes_observed != EXPECTED_ROWS or
            counters.single_byte_pread_count != EXPECTED_ROWS):
        return ROW_COUNT_MISMATCH
    if not complete or histogram_counts is None:
        return INCOMPLETE
    if (not isinstance(histogram_counts, list) or len(histogram_counts) != 256 or
            any(type(item) is not int or item < 0 for item in histogram_counts) or
            sum(histogram_counts) != EXPECTED_ROWS):
        return TOTAL_MISMATCH
    v1_total = sum(histogram_counts[index] for index in (0x4E, 0x53, 0x20))
    outside = sum(value for index, value in enumerate(histogram_counts)
                  if index not in (0x4E, 0x53, 0x20))
    if (histogram_counts[0x4E] != EXPECTED_N or
            histogram_counts[0x53] != EXPECTED_S or
            histogram_counts[0x20] != EXPECTED_SPACE or
            v1_total != EXPECTED_V1_TOTAL or outside != EXPECTED_OUTSIDE):
        return V1_MISMATCH
    if counters.network_requests or not counters.prohibited_clean():
        return INCONCLUSIVE
    return SUCCESS


def v1_consistency(histogram_counts: Sequence[int]) -> dict[str, object]:
    n_count = histogram_counts[0x4E]
    s_count = histogram_counts[0x53]
    space_count = histogram_counts[0x20]
    outside_count = sum(value for index, value in enumerate(histogram_counts)
                        if index not in (0x4E, 0x53, 0x20))
    checks = {
        "N_count_matches": n_count == EXPECTED_N,
        "S_count_matches": s_count == EXPECTED_S,
        "space_count_matches": space_count == EXPECTED_SPACE,
        "V1_domain_total_matches": n_count + s_count + space_count == EXPECTED_V1_TOTAL,
        "outside_V1_domain_total_matches": outside_count == EXPECTED_OUTSIDE,
        "grand_total_matches": sum(histogram_counts) == EXPECTED_ROWS,
    }
    # Persist pass/fail consistency only.  The complete numeric observation is
    # published in the success-only 256-bin artifact, never duplicated here.
    return {"checks": checks, "consistent": all(checks.values())}


def validate_file_binding(path: Path, expected_sha256: str, expected_bytes: int,
                          expected_mode: int | None = None) -> None:
    path = Path(path)
    if (not path.is_file() or path.stat().st_size != expected_bytes or
            file_sha256(path) != expected_sha256 or
            (expected_mode is not None and path.stat().st_mode & 0o777 != expected_mode)):
        raise HistogramError(INPUT_MISMATCH)


def _validate_historical_evidence() -> None:
    terminal = validate_sealed(load_canonical_json(V1_TERMINAL_PATH))
    aggregates = validate_sealed(load_canonical_json(V1_AGGREGATES_PATH))
    observability = validate_sealed(load_canonical_json(V1_OBSERVABILITY_PATH))
    observed = aggregates.get("aggregates", {})
    if (terminal.get("state") != "PHOTSYS_SELECTIVE_INVALID_PHOTSYS_FAILED" or
            terminal.get("authorized_rows_processed") != EXPECTED_ROWS or
            observed.get("total_rows") != EXPECTED_ROWS or
            observed.get("photsys_N") != EXPECTED_N or
            observed.get("photsys_S") != EXPECTED_S or
            observed.get("photsys_space") != EXPECTED_SPACE or
            observed.get("invalid_PHOTSYS") != EXPECTED_OUTSIDE or
            observability.get("counters", {}).get("authorized_PHOTSYS_values_decoded") != EXPECTED_ROWS):
        raise HistogramError(INPUT_MISMATCH)


def validate_real_inputs() -> dict[str, object]:
    expected = {
        SPEC_PATH: SPEC_SHA256, V1_REVIEW_PATH: V1_REVIEW_SHA256,
        REVIEWED_CONTRACT_PATH: REVIEWED_CONTRACT_SHA256,
        V1_TERMINAL_PATH: V1_TERMINAL_SHA256,
        V1_AGGREGATES_PATH: V1_AGGREGATES_SHA256,
        V1_OBSERVABILITY_PATH: V1_OBSERVABILITY_SHA256,
    }
    for path, digest in expected.items():
        if not path.is_file() or file_sha256(path) != digest:
            raise HistogramError(INPUT_MISMATCH)
    validate_file_binding(PHOTSYS_PATH, PHOTSYS_SHA256, PHOTSYS_BYTES, 0o444)
    contract = validate_sealed(load_canonical_json(REVIEWED_CONTRACT_PATH))
    physical = contract.get("physical_contract", {})
    if (contract.get("file_size") != PHOTSYS_BYTES or
            contract.get("first_table_data_byte") != PRODUCTION_LAYOUT.data_offset or
            physical.get("data_offset") != PRODUCTION_LAYOUT.data_offset or
            physical.get("row_count") != PRODUCTION_LAYOUT.row_count or
            physical.get("row_width") != PRODUCTION_LAYOUT.row_width):
        raise HistogramError(PHYSICAL_MISMATCH)
    columns = physical.get("column_schema", [])
    target = [item for item in columns if item.get("name") == "PHOTSYS"]
    if (len(target) != 1 or target[0].get("offset") != 70 or
            target[0].get("width") != 1 or target[0].get("tform") != "1A"):
        raise HistogramError(PHYSICAL_MISMATCH)
    _validate_historical_evidence()
    counters = HistogramCounters()
    return {"counters": counters.object(), "real_table_bytes_observed": 0,
            "stage_id": STAGE_ID, "state": "PHOTSYS_BYTE_HISTOGRAM_INPUTS_VALIDATED"}


def dry_run() -> dict[str, object]:
    validate_real_inputs()
    counters = HistogramCounters()
    reader = ExactPhotsysByteReader(PHOTSYS_PATH, counters)
    with reader:
        pass  # The next possible operation would be the first exact one-byte pread.
    return {"counters": counters.object(), "real_table_bytes_observed": 0,
            "stage_id": STAGE_ID, "state": READY}


def exact_command(project: Path = PROJECT) -> list[str]:
    project = Path(project).resolve()
    return [
        str(project / "oc3/.venv/bin/python"),
        str(project / "oc3/oc3_photsys_byte_histogram.py"),
        "--observe-photsys-byte-histogram", "--execute-real-byte-observation",
        "--candidate", str(project / CANDIDATE_PATH.relative_to(PROJECT)),
        "--authorization", str(project / AUTHORIZATION_PATH.relative_to(PROJECT)),
        "--output-directory", str(project / OUTPUT_ROOT.relative_to(PROJECT)),
    ]


def build_candidate(implementation_aggregate: str) -> dict[str, object]:
    validate_real_inputs()
    command = exact_command()
    return sealed({
        "candidate_state": "PENDING_HUMAN_REVIEW",
        "command_argv": command,
        "command_argv_sha256": sha256_bytes(canonical(command)),
        "execution": {"network": False, "offline_only": True,
                      "real_byte_observation": "REQUIRES_SEPARATE_FINAL_AUTHORIZATION"},
        "final_authorization_path": str(AUTHORIZATION_PATH),
        "final_authorization_present": False,
        "firewall": {"generic_semantic_reader": False, "identity_access": False,
                     "root_access": False, "whole_row_fallback": False,
                     "forbidden_counters_required": 0},
        "implementation_aggregate": implementation_aggregate,
        "input": {"path": str(PHOTSYS_PATH), "sha256": PHOTSYS_SHA256,
                  "size": PHOTSYS_BYTES},
        "interpretation": "PROHIBITED",
        "observation_contract": {
            "expected_single_byte_reads": EXPECTED_ROWS,
            "offset_formula": "11520 + row_ordinal*79 + 70",
            "pread_length": 1,
            "production_primitive": "os.pread(fd,1,offset)",
        },
        "output_contract": {"filename": HISTOGRAM_FILENAME,
                            "histogram_bins": 256, "row_linked_output": False,
                            "success_only": True},
        "physical_contract": {"path": str(REVIEWED_CONTRACT_PATH),
                              "sha256": REVIEWED_CONTRACT_SHA256,
                              "data_offset": 11520, "row_count": EXPECTED_ROWS,
                              "row_width": 79, "PHOTSYS_offset": 70,
                              "PHOTSYS_width": 1},
        "restart_boundary": {"automatic_resume": False,
                             "separate_review_and_authorization_required": True},
        "schema_version": "OC3_PHOTSYS_RAW_BYTE_HISTOGRAM_CANDIDATE_001",
        "scope": SCOPE,
        "specification": {"path": str(SPEC_PATH.relative_to(PROJECT)),
                          "sha256": SPEC_SHA256},
        "stage_id": STAGE_ID,
        "terminal_precedence": list(TERMINAL_PRECEDENCE),
        "terminal_states": list(TERMINAL_PRECEDENCE[:-1]) + [INCONCLUSIVE, SUCCESS],
        "v1_binding": {
            "review_path": str(V1_REVIEW_PATH.relative_to(PROJECT)),
            "review_sha256": V1_REVIEW_SHA256,
            "terminal_sha256": V1_TERMINAL_SHA256,
            "aggregates_sha256": V1_AGGREGATES_SHA256,
            "observability_sha256": V1_OBSERVABILITY_SHA256,
            "cross_checks": {"N": EXPECTED_N, "S": EXPECTED_S,
                             "space": EXPECTED_SPACE,
                             "V1_domain_total": EXPECTED_V1_TOTAL,
                             "outside_V1_domain_total": EXPECTED_OUTSIDE,
                             "grand_total": EXPECTED_ROWS},
            "semantics_unchanged": True,
        },
    })


def validate_candidate(path: Path = CANDIDATE_PATH,
                       *, require_authorization_absent: bool = True) -> dict[str, object]:
    try:
        candidate = validate_sealed(load_canonical_json(path))
    except Exception as exc:
        raise HistogramError(INPUT_MISMATCH) from exc
    if candidate != build_candidate(implementation_hash(PROJECT)):
        raise HistogramError(INPUT_MISMATCH)
    if require_authorization_absent and AUTHORIZATION_PATH.exists():
        raise HistogramError(INCONCLUSIVE)
    return candidate


def validate_authorization(path: Path, candidate_path: Path,
                           command_argv_sha256: str) -> dict[str, object]:
    try:
        value = validate_sealed(load_canonical_json(path))
    except Exception as exc:
        raise HistogramError(INCONCLUSIVE) from exc
    allowed = {"authorization_id", "authorization_state", "authorized",
               "candidate_sha256", "command_argv_sha256", "resume", "scope",
               "sealed", "stage_id"}
    if (set(value) != allowed or
            value.get("authorization_state") != "FINAL_HUMAN_AUTHORIZATION" or
            value.get("authorized") is not True or value.get("resume") is not False or
            value.get("scope") != SCOPE or value.get("stage_id") != STAGE_ID or
            value.get("candidate_sha256") != file_sha256(candidate_path) or
            value.get("command_argv_sha256") != command_argv_sha256):
        raise HistogramError(INCONCLUSIVE)
    return value


def _replace_json(path: Path, value: dict[str, object]) -> None:
    data = canonical(value) + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".partial")
    with temporary.open("wb") as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, path)


def _append_log(path: Path, value: dict[str, object]) -> None:
    with path.open("ab") as stream:
        stream.write(canonical(value) + b"\n"); stream.flush(); os.fsync(stream.fileno())


def canonical_histogram_artifact(histogram_counts: Sequence[int], counters: HistogramCounters,
                                 implementation_aggregate: str) -> dict[str, object]:
    counts = list(histogram_counts)
    return sealed({
        "histogram_counts": counts,
        "histogram_sha256": sha256_bytes(canonical(counts)),
        "implementation_aggregate": implementation_aggregate,
        "input": {"path": str(PHOTSYS_PATH), "sha256": PHOTSYS_SHA256,
                  "size": PHOTSYS_BYTES},
        "observability_counters": counters.object(),
        "physical_contract": {"path": str(REVIEWED_CONTRACT_PATH),
                              "sha256": REVIEWED_CONTRACT_SHA256},
        "schema_version": "OC3_PHOTSYS_RAW_BYTE_HISTOGRAM_001",
        "stage_id": STAGE_ID,
        "state": SUCCESS,
        "v1_evidence": {"review_sha256": V1_REVIEW_SHA256,
                        "terminal_sha256": V1_TERMINAL_SHA256,
                        "aggregates_sha256": V1_AGGREGATES_SHA256,
                        "observability_sha256": V1_OBSERVABILITY_SHA256},
    })


def publish_success_histogram(histogram_counts: Sequence[int], counters: HistogramCounters,
                              output_directory: Path,
                              implementation_aggregate: str) -> dict[str, object]:
    counts = list(histogram_counts)
    if terminal_outcome(counters, counts) != SUCCESS:
        raise HistogramError(INCONCLUSIVE)
    artifact = canonical_histogram_artifact(counts, counters, implementation_aggregate)
    artifact_path = Path(output_directory) / HISTOGRAM_FILENAME
    write_json_immutable(artifact_path, artifact)
    os.chmod(artifact_path, 0o444)
    return artifact


def run_real_observation(candidate_path: Path, authorization_path: Path,
                         command_argv_sha256: str, output_directory: Path) -> dict[str, object]:
    candidate = validate_candidate(candidate_path, require_authorization_absent=False)
    validate_authorization(authorization_path, candidate_path, command_argv_sha256)
    validate_real_inputs()
    output = Path(output_directory).resolve()
    if output != OUTPUT_ROOT.resolve() or output.exists():
        raise HistogramError(INCONCLUSIVE)
    output.mkdir(parents=True)
    counters = HistogramCounters()
    write_json_immutable(output / "INPUT_BINDING.json", sealed({
        "candidate_sha256": file_sha256(candidate_path),
        "implementation_aggregate": implementation_hash(PROJECT),
        "input_sha256": PHOTSYS_SHA256, "stage_id": STAGE_ID,
    }))
    progress_path = output / "PROGRESS.json"
    log_path = output / "RUN.log"
    histogram_counts: list[int] | None = None
    state = INCOMPLETE

    def persist_progress(phase: str) -> None:
        progress = sealed({"counters": counters.object(), "phase": phase,
                           "stage_id": STAGE_ID})
        _replace_json(progress_path, progress)
        _append_log(log_path, progress)

    try:
        persist_progress("INPUTS_BOUND")
        with ExactPhotsysByteReader(PHOTSYS_PATH, counters) as reader:
            histogram_counts = observe_histogram(
                reader, lambda: persist_progress("PHOTSYS_BYTE_OBSERVATION"))
        state = terminal_outcome(counters, histogram_counts)
        persist_progress("OBSERVATION_COMPLETE")
        consistency = v1_consistency(histogram_counts)
        _replace_json(output / "V1_CONSISTENCY.json", sealed({
            "result": consistency, "stage_id": STAGE_ID,
        }))
        _replace_json(output / "OBSERVABILITY.json", sealed({
            "counters": counters.object(), "stage_id": STAGE_ID,
        }))
        if state == SUCCESS:
            publish_success_histogram(histogram_counts, counters, output,
                                      candidate["implementation_aggregate"])
    except HistogramError as exc:
        state = exc.code if exc.code in TERMINAL_PRECEDENCE else INCONCLUSIVE
    except BaseException:
        state = terminal_outcome(counters, histogram_counts, complete=False)
        if state in (ROW_COUNT_MISMATCH,):
            state = INCOMPLETE
        raise
    finally:
        if not (output / "OBSERVABILITY.json").exists():
            _replace_json(output / "OBSERVABILITY.json", sealed({
                "counters": counters.object(), "stage_id": STAGE_ID,
            }))
        terminal = sealed({
            "counters": counters.object(),
            "histogram_published": (output / HISTOGRAM_FILENAME).exists(),
            "histogram_sha256": (sha256_bytes(canonical(histogram_counts))
                                 if state == SUCCESS and histogram_counts is not None else None),
            "stage_id": STAGE_ID, "state": state,
        })
        _replace_json(output / "TERMINAL.json", terminal)
        _append_log(log_path, terminal)
    return terminal
