import ast
import contextlib
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

import oc3_photsys_selective_value_validation as cli
from oc3lib.photsys_selective_value_validation import *


def card(key, value=None):
    if value is None:
        text = key
    elif isinstance(value, bool):
        text = f"{key:<8}= {'T' if value else 'F':>20}"
    elif isinstance(value, str):
        text = f"{key:<8}= '{value}'"
    else:
        text = f"{key:<8}= {value:>20}"
    return text[:80].ljust(80).encode("ascii")


def fits_header(cards):
    raw = b"".join(cards) + card("END")
    return raw + b" " * ((-len(raw)) % 2880)


def root_fixture(path, rows, *, mutate_header=None):
    primary = fits_header([card("SIMPLE", True), card("BITPIX", 8), card("NAXIS", 0)])
    cards = [card("XTENSION", "BINTABLE"), card("BITPIX", 8), card("NAXIS", 2),
             card("NAXIS1", 70), card("NAXIS2", len(rows)), card("PCOUNT", 0),
             card("GCOUNT", 1), card("TFIELDS", len(PRODUCTION_ROOT_LAYOUT.column_names))]
    for index, (name, form) in enumerate(zip(PRODUCTION_ROOT_LAYOUT.column_names,
                                             PRODUCTION_ROOT_LAYOUT.column_forms), 1):
        cards.extend((card(f"TTYPE{index}", name), card(f"TFORM{index}", form)))
    if mutate_header:
        cards.append(card(*mutate_header))
    table = fits_header(cards)
    bodies = []
    for name, brickid, canary in rows:
        bodies.append(name + struct.pack(">i", brickid) + canary[:58].ljust(58, b"x"))
    with gzip.open(path, "wb") as stream:
        stream.write(primary + table + b"".join(bodies))
    return RootProjectionLayout(len(rows), 70, PRODUCTION_ROOT_LAYOUT.column_names,
                                PRODUCTION_ROOT_LAYOUT.column_forms)


def target_fixture(path, rows, *, data_offset=16, row_width=79):
    body = bytearray(b"H" * data_offset)
    for name, brickid, photsys in rows:
        row = bytearray(b"f" * row_width)
        row[0:8] = name
        row[8:12] = struct.pack(">i", brickid)
        row[70:71] = photsys
        body.extend(row)
    path.write_bytes(body)
    return PhotsysLayout(data_offset, len(rows), row_width, len(body))


def global_identity(name, brickid):
    return ProjectedGlobalBrickIdentity(name, name.decode("ascii"), brickid)


def validate_rows(target_rows, global_rows=None):
    counters = ObservationCounters()
    observations = []
    for index, (name, brickid, photsys) in enumerate(target_rows):
        counters.authorized_rows_processed += 1
        observations.append(observe_photsys_projection(
            index, name + struct.pack(">i", brickid), photsys, counters))
    globals_ = [global_identity(name, brickid) for name, brickid in
                (global_rows if global_rows is not None else
                 [(name, brickid) for name, brickid, _ in target_rows])]
    counters.global_rows_processed = len(globals_)
    counters.global_BRICKNAME_values_decoded = len(globals_)
    counters.global_BRICKID_values_decoded = len(globals_)
    aggregates, records = validate_projected_records(
        observations, globals_, counters, len(target_rows))
    return aggregates, records, counters


class DecodeRulesTests(unittest.TestCase):
    def test_valid_photsys_bytes(self):
        for value in (b"N", b"S", b" "):
            self.assertEqual(decode_photsys(value), value)

    def test_right_padding_is_the_only_lexical_canonicalization(self):
        raw, canonical_name = decode_brickname(b"abc     ")
        self.assertEqual(raw, b"abc     ")
        self.assertEqual(canonical_name, "abc")

    def test_leading_embedded_non_ascii_and_nul_names_fail(self):
        for value in (b" 001p001", b"00 1p001", b"0001p00\xff", b"0001p00\0"):
            with self.subTest(value=value), self.assertRaises(SelectiveValidationError):
                decode_brickname(value)

    def test_malformed_global_name_semantics_fail_observation(self):
        counters = ObservationCounters()
        observed = observe_photsys_projection(0, b"abcdefgh" + struct.pack(">i", 1),
                                              b"N", counters)
        self.assertFalse(observed.brickname_valid)
        self.assertIn("BRICKNAME_INVALID", observed.error_codes)

    def test_signed_big_endian_boundaries(self):
        for value in (-(2**31), -1, 0, 2**31 - 1):
            self.assertEqual(decode_brickid(struct.pack(">i", value)), value)

    def test_invalid_photsys_nul_and_lowercase(self):
        for value in (b"\0", b"n", b"s", b"X"):
            with self.subTest(value=value), self.assertRaises(SelectiveValidationError) as caught:
                decode_photsys(value)
            self.assertEqual(caught.exception.code, INVALID_PHOTSYS)

    def test_closed_semantic_types_have_only_authorized_fields(self):
        self.assertEqual(set(ProjectedGlobalBrickIdentity.__dataclass_fields__),
                         {"brickname_raw", "brickname", "brickid"})
        self.assertEqual(set(ProjectedPhotsysRecord.__dataclass_fields__),
                         {"brickname_raw", "brickname", "brickid", "photsys_raw"})


class ExactSpanReaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="photsys_spans_SYNTHETIC_ONLY_")
        self.path = Path(self.temp.name) / "target.fits"
        self.rows = [(b"0001p001", -1, b"N"), (b"0002m002", 2**31 - 1, b" ")]
        self.layout = target_fixture(self.path, self.rows)

    def tearDown(self):
        self.temp.cleanup()

    def reader(self, calls):
        def observed_pread(fd, length, offset):
            calls.append((offset, length))
            return os.pread(fd, length, offset)
        return ExactSpanPhotsysReader(self.path, ObservationCounters(),
                                      layout=self.layout, pread=observed_pread,
                                      synthetic_only=True)

    def test_first_and_last_row_exact_offsets(self):
        calls = []
        with self.reader(calls) as reader:
            first = reader.read_projected(0)
            last = reader.read_projected(1)
        self.assertIsNotNone(first.record); self.assertIsNotNone(last.record)
        self.assertEqual(calls, [(16, 12), (86, 1), (95, 12), (165, 1)])

    def test_forbidden_span_fails_before_io(self):
        calls = []
        with self.reader(calls) as reader:
            for args in ((0, 0, 79), (0, -1, 12), (0, 0, 13),
                         (0, 69, 2), (-1, 0, 12), (2, 0, 12)):
                with self.subTest(args=args), self.assertRaises(SelectiveValidationError) as caught:
                    reader._read_span(*args)
                self.assertEqual(caught.exception.code, FIREWALL_VIOLATION)
        self.assertEqual(calls, [])

    def test_integer_overflow_controls_fail_before_io(self):
        calls = []
        with self.reader(calls) as reader:
            for row in (2**63, -(2**63)):
                with self.assertRaises(SelectiveValidationError):
                    reader._read_span(row, 0, 12)
        self.assertEqual(calls, [])

    def test_no_public_generic_reader_or_whole_row_capability(self):
        reader = self.reader([])
        self.assertFalse(hasattr(reader, "read"))
        self.assertFalse(hasattr(reader, "read_row"))
        self.assertEqual(reader._ALLOWED_SPANS, frozenset(((0, 12), (70, 1))))

    def test_wrong_production_layout_dimensions_fail(self):
        base = PRODUCTION_PHOTSYS_LAYOUT
        variants = (
            PhotsysLayout(base.data_offset, base.row_count, 78, base.file_size),
            PhotsysLayout(base.data_offset + 1, base.row_count, base.row_width, base.file_size + 1),
            PhotsysLayout(base.data_offset, base.row_count - 1, base.row_width, base.file_size),
            PhotsysLayout(base.data_offset, base.row_count, base.row_width, base.file_size + 1),
        )
        for layout in variants:
            with self.subTest(layout=layout), self.assertRaises(SelectiveValidationError) as caught:
                ExactSpanPhotsysReader(self.path, ObservationCounters(), layout=layout)
            self.assertEqual(caught.exception.code, PHYSICAL_MISMATCH)

    def test_wrong_hash_and_size_binding_fail(self):
        correct = hashlib.sha256(self.path.read_bytes()).hexdigest()
        validate_file_binding(self.path, correct, self.path.stat().st_size)
        for digest, size in (("0" * 64, self.path.stat().st_size),
                             (correct, self.path.stat().st_size + 1)):
            with self.subTest(digest=digest, size=size), self.assertRaises(SelectiveValidationError):
                validate_file_binding(self.path, digest, size)


class RootProjectionAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="root_projection_SYNTHETIC_ONLY_")
        self.path = Path(self.temp.name) / "root.fits.gz"
        self.rows = [(b"0001p001", -4, b"FORBIDDEN_CANARY_A"),
                     (b"0002m002", 9, b"FORBIDDEN_CANARY_B")]
        self.layout = root_fixture(self.path, self.rows)

    def tearDown(self):
        self.temp.cleanup()

    def test_opaque_rows_cross_only_as_identity_projection(self):
        counters = ObservationCounters()
        rows = tuple(RootGzipProjectionAdapter(
            self.path, counters, layout=self.layout, synthetic_only=True).iter_identities())
        self.assertEqual([(row.brickname_raw, row.brickid) for row in rows],
                         [(b"0001p001", -4), (b"0002m002", 9)])
        self.assertEqual(counters.global_opaque_bytes_transited, 140)
        self.assertEqual(counters.whole_row_materialization_count, 0)
        self.assertNotIn(b"FORBIDDEN_CANARY", repr(rows).encode())

    def test_header_contract_drift_fails_closed(self):
        bad = Path(self.temp.name) / "bad.fits.gz"
        layout = root_fixture(bad, self.rows, mutate_header=("EXTNAME", "BRICKS"))
        with self.assertRaises(SelectiveValidationError) as caught:
            tuple(RootGzipProjectionAdapter(
                bad, ObservationCounters(), layout=layout,
                synthetic_only=True).iter_identities())
        self.assertEqual(caught.exception.code, PHYSICAL_MISMATCH)

    def test_truncated_opaque_row_is_inconclusive(self):
        truncated = Path(self.temp.name) / "truncated.fits.gz"
        layout = root_fixture(truncated, self.rows)
        raw = gzip.open(truncated, "rb").read()[:-1]
        with gzip.open(truncated, "wb") as stream:
            stream.write(raw)
        with self.assertRaises(SelectiveValidationError) as caught:
            tuple(RootGzipProjectionAdapter(
                truncated, ObservationCounters(), layout=layout,
                synthetic_only=True).iter_identities())
        self.assertEqual(caught.exception.code, GLOBAL_ACCESS_INCONCLUSIVE)


class JoinUniquenessTests(unittest.TestCase):
    BASE = [(b"0001p001", 1, b"N"), (b"0002m002", 2, b"S"),
            (b"0003p003", 3, b" ")]

    def test_success_and_photsys_distribution(self):
        aggregates, records, counters = validate_rows(self.BASE)
        self.assertEqual(aggregates.terminal, SUCCESS)
        self.assertEqual((aggregates.photsys_N, aggregates.photsys_S,
                          aggregates.photsys_space), (1, 1, 1))
        self.assertEqual(aggregates.matched, 3)
        self.assertTrue(counters.forbidden_clean())
        self.assertEqual(len(records), 3)

    def test_duplicate_raw_and_canonical_name(self):
        rows = [(b"0001p001", 1, b"N"), (b"0001p001", 2, b"S")]
        aggregates, _, _ = validate_rows(rows)
        self.assertEqual(aggregates.terminal, IDENTITY_DUPLICATE)
        self.assertEqual(aggregates.duplicate_raw_BRICKNAME, 1)
        self.assertEqual(aggregates.duplicate_canonical_BRICKNAME, 1)

    def test_duplicate_id(self):
        rows = [(b"0001p001", 1, b"N"), (b"0002p002", 1, b"S")]
        aggregates, _, _ = validate_rows(rows)
        self.assertEqual(aggregates.terminal, IDENTITY_DUPLICATE)
        self.assertEqual(aggregates.duplicate_BRICKID, 1)

    def test_duplicate_pair(self):
        rows = [(b"0001p001", 1, b"N"), (b"0001p001", 1, b"S")]
        aggregates, _, _ = validate_rows(rows)
        self.assertEqual(aggregates.terminal, IDENTITY_DUPLICATE)
        self.assertEqual(aggregates.duplicate_pair, 1)

    def test_both_missing_directions(self):
        target = [(b"0001p001", 1, b"N"), (b"0009p009", 9, b"S")]
        root = [(b"0001p001", 1), (b"0002p002", 2)]
        aggregates, _, _ = validate_rows(target, root)
        self.assertEqual(aggregates.terminal, GLOBAL_JOIN_CONFLICT)
        self.assertEqual(aggregates.missing_from_global_authority, 1)
        self.assertEqual(aggregates.missing_from_PHOTSYS_authority, 1)

    def test_brickname_conflict(self):
        target = [(b"0001p001", 2, b"N"), (b"0002p002", 9, b"S")]
        root = [(b"0001p001", 1), (b"0002p002", 2)]
        aggregates, _, _ = validate_rows(target, root)
        self.assertEqual(aggregates.BRICKID_conflict, 1)
        self.assertEqual(aggregates.identity_pair_conflict, 1)

    def test_brickid_conflict(self):
        target = [(b"0009p009", 1, b"N"), (b"0008p008", 2, b"S")]
        root = [(b"0001p001", 1), (b"0002p002", 2)]
        aggregates, _, _ = validate_rows(target, root)
        self.assertEqual(aggregates.BRICKNAME_conflict, 2)

    def test_invalid_photsys_precedence_and_counts(self):
        aggregates, records, counters = validate_rows([(b"0001p001", 1, b"\0")])
        self.assertEqual(aggregates.terminal, INVALID_PHOTSYS)
        self.assertEqual(aggregates.invalid_PHOTSYS, 1)
        self.assertEqual(aggregates.valid_BRICKNAME, 1)
        self.assertEqual(aggregates.valid_BRICKID, 1)
        self.assertEqual(records, ())
        self.assertEqual(counters.authorized_PHOTSYS_values_decoded, 1)

    def test_malformed_authorized_value_terminal(self):
        aggregates, _, _ = validate_rows([(b"abcdefgh", 1, b"N")],
                                         [(b"0001p001", 1)])
        self.assertEqual(aggregates.terminal, AUTHORIZED_VALUE_INVALID)
        self.assertEqual(aggregates.invalid_BRICKNAME, 1)

    def test_row_count_and_counter_mismatch(self):
        counters = ObservationCounters()
        observation = observe_photsys_projection(
            0, b"0001p001" + struct.pack(">i", 1), b"N", counters)
        aggregates, _ = validate_projected_records(
            [observation], [global_identity(b"0001p001", 1)], counters, 1)
        self.assertEqual(aggregates.terminal, ROW_COUNT_MISMATCH)

    def test_firewall_counter_has_highest_precedence(self):
        aggregates, _, counters = validate_rows(self.BASE)
        counters.forbidden_value_decode_count = 1
        rebuilt, _ = validate_projected_records(
            [observe_photsys_projection(index, name + struct.pack(">i", brickid), photsys,
                                        ObservationCounters())
             for index, (name, brickid, photsys) in enumerate(self.BASE)],
            [global_identity(name, brickid) for name, brickid, _ in self.BASE],
            counters, 3)
        self.assertEqual(rebuilt.terminal, FIREWALL_VIOLATION)


class ResolverAndTripwireTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="resolver_SYNTHETIC_ONLY_")
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def records(self):
        return (
            ProjectedPhotsysRecord(b"0002m002", "0002m002", -1, b"S"),
            ProjectedPhotsysRecord(b"0001p001", "0001p001", 2, b"N"),
        )

    def test_deterministic_sorting_binary_and_sha(self):
        first = canonical_resolver_bytes(self.records())
        second = canonical_resolver_bytes(tuple(reversed(self.records())))
        expected = (b"0001p001" + struct.pack(">i", 2) + b"N" +
                    b"0002m002" + struct.pack(">i", -1) + b"S")
        self.assertEqual(first, second)
        self.assertEqual(first, expected)
        self.assertEqual(hashlib.sha256(first).hexdigest(),
                         hashlib.sha256(expected).hexdigest())

    def test_success_publication_has_exact_binary_and_sidecar(self):
        aggregates, _, _ = validate_rows([(b"0001p001", 2, b"N"),
                                          (b"0002m002", -1, b"S")])
        sidecar = publish_success_resolver(
            aggregates, self.records(), self.root, {"synthetic": True}, "a" * 64)
        binary = self.root / PROJECTED_FILENAME
        self.assertEqual(binary.stat().st_size, 26)
        self.assertEqual(sidecar["binary_sha256"], hashlib.sha256(binary.read_bytes()).hexdigest())
        self.assertEqual(validate_sealed(load_canonical_json(self.root / PROJECTED_SIDECAR)),
                         sidecar)

    def test_no_resolver_on_failure(self):
        aggregates, records, _ = validate_rows([(b"0001p001", 1, b"x")])
        with self.assertRaises(SelectiveValidationError):
            publish_success_resolver(
                aggregates, records, self.root, {"synthetic": True}, "a" * 64)
        self.assertFalse((self.root / PROJECTED_FILENAME).exists())
        self.assertFalse((self.root / PROJECTED_SIDECAR).exists())

    def test_production_dependencies_offer_no_fallback(self):
        source = Path(__file__).parents[1] / "oc3lib/photsys_selective_value_validation.py"
        tree = ast.parse(source.read_text())
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        self.assertTrue({"numpy", "pandas", "astropy", "mmap"}.isdisjoint(imported))
        self.assertNotIn("read", ExactSpanPhotsysReader.__dict__)
        self.assertNotIn("read_row", ExactSpanPhotsysReader.__dict__)

    def test_runtime_tripwires_are_not_touched_by_exact_reader(self):
        target = self.root / "target.fits"
        layout = target_fixture(target, [(b"0001p001", 1, b"N")])
        exploding = types.ModuleType("exploding")
        def explode(*_args, **_kwargs):
            raise AssertionError("UNRESTRICTED_READER_TRIPWIRE")
        exploding.array = exploding.fromfile = exploding.memmap = exploding.read_csv = explode
        exploding.Table = explode
        with patch.dict(sys.modules, {name: exploding for name in
                                     ("numpy", "pandas", "astropy", "mmap")}):
            with ExactSpanPhotsysReader(
                    target, ObservationCounters(), layout=layout,
                    synthetic_only=True) as reader:
                self.assertIsNotNone(reader.read_projected(0).record)

    def test_cli_help_and_real_mode_requires_authorization(self):
        with self.assertRaises(SystemExit) as caught, contextlib.redirect_stdout(io.StringIO()):
            cli.main(["--help"])
        self.assertEqual(caught.exception.code, 0)
        error = io.StringIO()
        with contextlib.redirect_stderr(error):
            self.assertEqual(cli.main(["--validate-photsys-authority"]), 2)
        self.assertIn(INCONCLUSIVE, error.getvalue())

    def test_exact_command_is_real_mode_but_not_authorized(self):
        command = exact_command()
        self.assertIn("--validate-photsys-authority", command)
        self.assertIn("--execute-real-value-observation", command)
        self.assertFalse(AUTHORIZATION_PATH.exists())


if __name__ == "__main__":
    unittest.main()
