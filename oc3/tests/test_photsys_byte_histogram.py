import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

import oc3_photsys_byte_histogram as cli
from oc3lib.core import canonical
from oc3lib.photsys_byte_histogram import *


def synthetic_fixture(path: Path, values: list[int], *, data_offset=16, row_width=79):
    body = bytearray(b"H" * data_offset)
    for value in values:
        row = bytearray(b"x" * row_width)
        row[70] = value
        body.extend(row)
    path.write_bytes(body)
    return HistogramLayout(data_offset, len(values), row_width, len(body))


def success_histogram():
    counts = [0] * 256
    counts[0x4E] = EXPECTED_N
    counts[0x53] = EXPECTED_S
    counts[0x20] = EXPECTED_SPACE
    counts[0x01] = EXPECTED_OUTSIDE
    return counts


def success_counters():
    return HistogramCounters(EXPECTED_ROWS, EXPECTED_ROWS, EXPECTED_ROWS)


class HistogramConstructionTests(unittest.TestCase):
    def test_N_S_and_space_bins(self):
        counts = histogram_from_raw_bytes([b"N", b"S", b" "])
        self.assertEqual((counts[0x4E], counts[0x53], counts[0x20]), (1, 1, 1))

    def test_one_outside_V1_byte(self):
        counts = histogram_from_raw_bytes([bytes([1])])
        self.assertEqual(counts[1], 1)
        self.assertEqual(sum(counts), 1)

    def test_multiple_outside_V1_bytes(self):
        counts = histogram_from_raw_bytes([bytes([1]), bytes([2]), bytes([1])])
        self.assertEqual((counts[1], counts[2]), (2, 1))

    def test_all_256_bins(self):
        counts = histogram_from_raw_bytes([bytes([value]) for value in range(256)])
        self.assertEqual(counts, [1] * 256)

    def test_exact_histogram_size(self):
        self.assertEqual(len(histogram_from_raw_bytes([])), 256)

    def test_malformed_synthetic_value_rejected(self):
        for value in (b"", b"ab", bytearray(b"a")):
            with self.subTest(value=value), self.assertRaises(HistogramError):
                histogram_from_raw_bytes([value])

    def test_exact_sum(self):
        values = [bytes([7])] * 19 + [bytes([255])] * 3
        self.assertEqual(sum(histogram_from_raw_bytes(values)), 22)


class ExactReaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="photsys_histogram_SYNTHETIC_ONLY_")
        self.path = Path(self.temp.name) / "fixture.bin"
        self.layout = synthetic_fixture(self.path, [3, 4])

    def tearDown(self):
        self.temp.cleanup()

    def reader(self, calls):
        def traced(fd, length, offset):
            calls.append((fd, length, offset))
            return os.pread(fd, length, offset)
        return ExactPhotsysByteReader(self.path, HistogramCounters(),
                                      layout=self.layout, pread=traced,
                                      synthetic_only=True)

    def test_first_and_last_row_exact_offsets(self):
        calls = []
        with self.reader(calls) as reader:
            self.assertEqual(reader.read_photsys_byte(0), bytes([3]))
            self.assertEqual(reader.read_photsys_byte(1), bytes([4]))
        self.assertEqual([(length, offset) for _, length, offset in calls],
                         [(1, 16 + 70), (1, 16 + 79 + 70)])

    def test_exactly_one_pread_per_row(self):
        calls = []
        with self.reader(calls) as reader:
            counts = observe_histogram(reader)
            self.assertEqual(reader.counters.rows_processed, 2)
            self.assertEqual(reader.counters.single_byte_pread_count, 2)
            self.assertEqual(reader.counters.authorized_PHOTSYS_bytes_observed, 2)
        self.assertEqual(len(calls), 2)
        self.assertEqual((counts[3], counts[4]), (1, 1))

    def test_forbidden_spans_rejected_before_io(self):
        calls = []
        with self.reader(calls) as reader:
            for kwargs in ({"relative_offset": 0, "length": 1},
                           {"relative_offset": 70, "length": 2},
                           {"relative_offset": 69, "length": 2}):
                with self.subTest(kwargs=kwargs), self.assertRaises(HistogramError) as caught:
                    reader._read_photsys_byte(0, **kwargs)
                self.assertEqual(caught.exception.code, FORBIDDEN_SPAN)
        self.assertEqual(calls, [])

    def test_negative_and_out_of_range_rejected_before_io(self):
        calls = []
        with self.reader(calls) as reader:
            for row in (-1, 2, 2**63, -(2**63)):
                with self.subTest(row=row), self.assertRaises(HistogramError) as caught:
                    reader.read_photsys_byte(row)
                self.assertEqual(caught.exception.code, FORBIDDEN_SPAN)
        self.assertEqual(calls, [])

    def test_boolean_row_is_not_an_integer_ordinal(self):
        calls = []
        with self.reader(calls) as reader, self.assertRaises(HistogramError):
            reader.read_photsys_byte(True)
        self.assertEqual(calls, [])

    def test_truncated_single_byte_read_is_incomplete(self):
        calls = []
        def empty(fd, length, offset):
            calls.append((length, offset)); return b""
        reader = ExactPhotsysByteReader(self.path, HistogramCounters(),
                                        layout=self.layout, pread=empty,
                                        synthetic_only=True)
        with reader, self.assertRaises(HistogramError) as caught:
            reader.read_photsys_byte(0)
        self.assertEqual(caught.exception.code, INCOMPLETE)
        self.assertEqual(calls, [(1, 86)])

    def test_no_generic_or_whole_row_API(self):
        reader = self.reader([])
        for name in ("read", "read_span", "read_row", "read_identity", "read_root"):
            self.assertFalse(hasattr(reader, name))

    def test_wrong_production_layout_dimensions_rejected(self):
        base = PRODUCTION_LAYOUT
        variants = (
            HistogramLayout(base.data_offset + 1, base.row_count, base.row_width, base.file_size),
            HistogramLayout(base.data_offset, base.row_count - 1, base.row_width, base.file_size),
            HistogramLayout(base.data_offset, base.row_count, base.row_width - 1, base.file_size),
            HistogramLayout(base.data_offset, base.row_count, base.row_width, base.file_size, 69),
        )
        for layout in variants:
            with self.subTest(layout=layout), self.assertRaises(HistogramError) as caught:
                ExactPhotsysByteReader(self.path, HistogramCounters(), layout=layout)
            self.assertEqual(caught.exception.code, PHYSICAL_MISMATCH)

    def test_invalid_layout_arithmetic_rejected(self):
        variants = (
            HistogramLayout(-1, 2, 79, 200),
            HistogramLayout(16, 2, 70, 200),
            HistogramLayout(16, 2, 79, 20),
            HistogramLayout(16, 2, 79, 200, 70, 2),
        )
        for layout in variants:
            with self.subTest(layout=layout), self.assertRaises(HistogramError):
                layout.validate()

    def test_boundary_ready_does_not_call_pread(self):
        calls = []
        self.reader(calls).boundary_ready()
        self.assertEqual(calls, [])


class CapabilityFirewallTests(unittest.TestCase):
    def test_BRICKNAME_access_attempt(self):
        counters = HistogramCounters()
        with self.assertRaises(HistogramError) as caught:
            reject_identity_or_root_attempt("BRICKNAME", counters)
        self.assertEqual(caught.exception.code, IDENTITY_OR_ROOT)
        self.assertEqual(counters.BRICKNAME_values_observed, 1)

    def test_BRICKID_access_attempt(self):
        counters = HistogramCounters()
        with self.assertRaises(HistogramError):
            reject_identity_or_root_attempt("BRICKID", counters)
        self.assertEqual(counters.BRICKID_values_observed, 1)

    def test_ROOT_access_attempt(self):
        counters = HistogramCounters()
        with self.assertRaises(HistogramError):
            reject_identity_or_root_attempt("ROOT", counters)
        self.assertEqual(counters.ROOT_values_observed, 1)

    def test_whole_row_fallback_attempt(self):
        counters = HistogramCounters()
        with self.assertRaises(HistogramError) as caught:
            reject_whole_row_attempt(counters)
        self.assertEqual(caught.exception.code, WHOLE_ROW)
        self.assertEqual(counters.whole_row_materialization_count, 1)

    def test_forbidden_libraries_are_not_invoked_by_reader(self):
        class Tripwire(types.ModuleType):
            def __getattr__(self, name):
                raise AssertionError("FORBIDDEN_LIBRARY_USED")
        with tempfile.TemporaryDirectory(prefix="hist_tripwire_SYNTHETIC_ONLY_") as temp:
            path = Path(temp) / "fixture.bin"
            layout = synthetic_fixture(path, [17])
            counters = HistogramCounters()
            injected = {name: Tripwire(name) for name in
                        ("mmap", "pandas", "numpy", "astropy", "astropy.table")}
            with patch.dict(sys.modules, injected):
                with ExactPhotsysByteReader(path, counters, layout=layout,
                                            synthetic_only=True) as reader:
                    self.assertEqual(reader.read_photsys_byte(0), bytes([17]))


class TerminalAndConsistencyTests(unittest.TestCase):
    def test_V1_consistency_success(self):
        histogram = success_histogram()
        self.assertEqual(terminal_outcome(success_counters(), histogram), SUCCESS)
        self.assertTrue(v1_consistency(histogram)["consistent"])

    def test_wrong_N_count(self):
        histogram = success_histogram(); histogram[0x4E] -= 1; histogram[1] += 1
        self.assertEqual(terminal_outcome(success_counters(), histogram), V1_MISMATCH)

    def test_wrong_S_count(self):
        histogram = success_histogram(); histogram[0x53] -= 1; histogram[1] += 1
        self.assertEqual(terminal_outcome(success_counters(), histogram), V1_MISMATCH)

    def test_wrong_space_count(self):
        histogram = success_histogram(); histogram[0x20] += 1; histogram[1] -= 1
        self.assertEqual(terminal_outcome(success_counters(), histogram), V1_MISMATCH)

    def test_wrong_outside_domain_count(self):
        histogram = success_histogram(); histogram[1] -= 1; histogram[0x4E] += 1
        self.assertEqual(terminal_outcome(success_counters(), histogram), V1_MISMATCH)

    def test_wrong_histogram_length(self):
        self.assertEqual(terminal_outcome(success_counters(), [0] * 255), TOTAL_MISMATCH)

    def test_wrong_histogram_sum(self):
        histogram = success_histogram(); histogram[1] -= 1
        self.assertEqual(terminal_outcome(success_counters(), histogram), TOTAL_MISMATCH)

    def test_negative_or_noninteger_count(self):
        for value in (-1, 1.0):
            histogram = success_histogram(); histogram[1] = value
            with self.subTest(value=value):
                self.assertEqual(terminal_outcome(success_counters(), histogram), TOTAL_MISMATCH)

    def test_row_count_mismatch_precedes_incomplete(self):
        self.assertEqual(terminal_outcome(HistogramCounters(), None, complete=False),
                         ROW_COUNT_MISMATCH)

    def test_terminal_precedence(self):
        counters = success_counters()
        counters.forbidden_span_access_count = 1
        counters.whole_row_materialization_count = 1
        counters.ROOT_values_observed = 1
        self.assertEqual(terminal_outcome(counters, success_histogram(),
                                          input_valid=False, physical_valid=False),
                         FORBIDDEN_SPAN)

    def test_incomplete_after_complete_counters(self):
        self.assertEqual(terminal_outcome(success_counters(), None), INCOMPLETE)


class BindingAndPublicationTests(unittest.TestCase):
    def test_wrong_input_hash_and_size(self):
        with tempfile.TemporaryDirectory(prefix="hist_binding_SYNTHETIC_ONLY_") as temp:
            path = Path(temp) / "input.bin"; path.write_bytes(b"abc")
            digest = hashlib.sha256(b"abc").hexdigest()
            validate_file_binding(path, digest, 3)
            for expected_hash, expected_size in (("0" * 64, 3), (digest, 4)):
                with self.subTest(expected_hash=expected_hash, expected_size=expected_size), \
                        self.assertRaises(HistogramError):
                    validate_file_binding(path, expected_hash, expected_size)

    def test_canonical_serialization_deterministic(self):
        first = canonical_histogram_artifact(success_histogram(), success_counters(), "a" * 64)
        second = canonical_histogram_artifact(success_histogram(), success_counters(), "a" * 64)
        self.assertEqual(canonical(first), canonical(second))
        self.assertEqual(first["sealed"], second["sealed"])
        self.assertEqual(first["histogram_sha256"], second["histogram_sha256"])

    def test_histogram_sha_is_numeric_array_hash(self):
        artifact = canonical_histogram_artifact(success_histogram(), success_counters(), "b" * 64)
        self.assertEqual(artifact["histogram_sha256"],
                         hashlib.sha256(canonical(success_histogram())).hexdigest())

    def test_failure_produces_no_histogram(self):
        with tempfile.TemporaryDirectory(prefix="hist_publish_SYNTHETIC_ONLY_") as temp:
            output = Path(temp)
            with self.assertRaises(HistogramError):
                publish_success_histogram([0] * 256, HistogramCounters(), output, "c" * 64)
            self.assertFalse((output / HISTOGRAM_FILENAME).exists())

    def test_no_row_linked_output(self):
        artifact = canonical_histogram_artifact(success_histogram(), success_counters(), "d" * 64)
        encoded = canonical(artifact)
        for forbidden in (b'"row_ordinal"', b'"byte_offset"', b'"sample_rows"',
                          b'"identity"', b'"first_unexpected_row"'):
            self.assertNotIn(forbidden, encoded)
        self.assertEqual(set(artifact) - {"sealed"}, {
            "histogram_counts", "histogram_sha256", "implementation_aggregate",
            "input", "observability_counters", "physical_contract", "schema_version",
            "stage_id", "state", "v1_evidence",
        })

    def test_success_publish_is_immutable(self):
        with tempfile.TemporaryDirectory(prefix="hist_success_SYNTHETIC_ONLY_") as temp:
            output = Path(temp)
            artifact = publish_success_histogram(success_histogram(), success_counters(),
                                                 output, "e" * 64)
            self.assertEqual(json.loads((output / HISTOGRAM_FILENAME).read_text()), artifact)
            self.assertEqual((output / HISTOGRAM_FILENAME).stat().st_mode & 0o777, 0o444)


class CLIBoundaryTests(unittest.TestCase):
    def test_help_lists_all_modes(self):
        help_text = cli.parser().format_help()
        for option in ("--validate-inputs", "--dry-run",
                       "--observe-photsys-byte-histogram"):
            self.assertIn(option, help_text)

    def test_observation_without_execution_gate_is_closed(self):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            result = cli.main(["--observe-photsys-byte-histogram"])
        self.assertEqual(result, 2)
        self.assertIn(INCONCLUSIVE, stderr.getvalue())

    def test_exact_command_contains_observation_mode_and_authorization(self):
        command = exact_command()
        self.assertIn("--observe-photsys-byte-histogram", command)
        self.assertIn("--execute-real-byte-observation", command)
        self.assertIn("--authorization", command)

    def test_final_authorization_is_absent(self):
        self.assertFalse(AUTHORIZATION_PATH.exists())


if __name__ == "__main__":
    unittest.main()
