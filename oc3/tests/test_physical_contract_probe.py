import contextlib
import gzip
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

import oc3_probe
from oc3lib.core import canonical, digest, implementation_hash
from oc3lib.physical_contract_probe import *


PROJECT = Path(__file__).resolve().parents[2]
CANARY = b"ROW_CANARY_FORBIDDEN_9f86e8c6"


def card(key, value=None):
    if value is None:
        text = key
    elif isinstance(value, bool):
        text = f"{key:<8}= {'T' if value else 'F':>20}"
    elif isinstance(value, str):
        escaped = value.replace("'", "''")
        text = f"{key:<8}= '{escaped}'"
    else:
        text = f"{key:<8}= {value:>20}"
    return text[:80].ljust(80).encode("ascii")


def fits_header(cards, comments=0):
    values = list(cards)
    for index in range(comments):
        token = hashlib.sha256(f"comment-{index}".encode()).hexdigest()
        values.append(("COMMENT " + token)[:80].ljust(80).encode("ascii"))
    raw = b"".join(values) + card("END")
    return raw + b" " * ((-len(raw)) % 2880)


def primary(*, naxis=0, axes=(), bitpix=8):
    values = [card("SIMPLE", True), card("BITPIX", bitpix), card("NAXIS", naxis)]
    values.extend(card(f"NAXIS{index}", size) for index, size in enumerate(axes, 1))
    return fits_header(values)


def table(columns=None, *, rows=2, row_size=8, extra=None, comments=0):
    columns = columns or [("BRICKID", "J", {})]
    values = [card("XTENSION", "BINTABLE"), card("BITPIX", 8), card("NAXIS", 2),
              card("NAXIS1", row_size), card("NAXIS2", rows), card("PCOUNT", 0),
              card("GCOUNT", 1), card("TFIELDS", len(columns)), card("EXTNAME", "BRICKS")]
    for index, (name, form, metadata) in enumerate(columns, 1):
        values.extend((card(f"TTYPE{index}", name), card(f"TFORM{index}", form)))
        for prefix, key in (("TUNIT", "unit"), ("TNULL", "null"), ("TSCAL", "scale"), ("TZERO", "zero")):
            if key in metadata:
                values.append(card(f"{prefix}{index}", metadata[key]))
    values.extend(extra or ())
    return fits_header(values, comments=comments)


def fits_bytes(columns=None, *, primary_bytes=None, table_bytes=None, rows=True):
    value = (primary_bytes if primary_bytes is not None else primary())
    value += (table_bytes if table_bytes is not None else table(columns))
    return value + (CANARY + b"\x00" * 100 if rows else b"")


def binding():
    return ProbeBinding(PROBE_SPEC_SHA256, "b" * 64, ENVIRONMENT_FINGERPRINT, "a" * 64, "SYNTHETIC_ATTEMPT")


class Base(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="probe_SYNTHETIC_ONLY_")
        self.root = Path(self.temp.name)
        self.ledgers = []

    def tearDown(self):
        for ledger in self.ledgers:
            try:
                ledger.close()
            except Exception:
                pass
        self.temp.cleanup()

    def ledger(self, **caps):
        result = ProbeLedger(self.root / "ledger.sqlite", binding(), caps)
        self.ledgers.append(result)
        return result

    def code(self, expected, callback):
        with self.assertRaises(ProbeError) as caught:
            callback()
        self.assertEqual(caught.exception.code, expected)

    def head_response(self, role, *, accept="bytes", length=999999, status=200, **headers):
        values = {"content-length": str(length), "content-type": "application/fits",
                  "accept-ranges": accept, **headers}
        return MemoryResponse(b"HEAD_BODY_MUST_NOT_BE_READ", status=status, headers=values,
                              final_url=RESOURCES[role].url)

    def range_response(self, role, index, body=None, *, status=206, total=999999, **headers):
        body = b"x" * 65536 if body is None else body
        start = index * 65536
        values = {"content-length": str(len(body)), "content-range": f"bytes {start}-{start + 65535}/{total}",
                  **headers}
        return MemoryResponse(body, status=status, headers=values, final_url=RESOURCES[role].url)


class AuthorityCliAllowlistTests(Base):
    def test_01_probe_authorities_match(self):
        self.assertEqual(len(verify_probe_authorities(PROJECT)), 8)

    def test_02_spec_hash_bound(self):
        self.assertEqual(file_hash(PROJECT / PROBE_SPEC_NAME), PROBE_SPEC_SHA256)

    def test_03_pre_probe_aggregate_recorded(self):
        receipt = json.loads((PROJECT / "oc3/environment_setup/AMENDMENT_003_REPLAY_RECEIPT.json").read_text())
        self.assertEqual(receipt["implementation_aggregate"], PRE_PROBE_IMPLEMENTATION)

    def test_04_environment_fingerprint_bound(self):
        env = json.loads((PROJECT / "oc3/environment_setup/ENVIRONMENT.json").read_text())
        self.assertEqual(digest(canonical(env["state"])), ENVIRONMENT_FINGERPRINT)

    def test_05_allowlist_exact_seven(self):
        self.assertEqual(tuple(RESOURCES), FITS_ROLES + MANIFEST_ROLES)
        self.assertEqual(len(RESOURCES), 7)

    def test_06_alternate_url_rejected(self):
        role = "ROOT_SUMMARY"
        self.code("PROBE_RESOURCE_NOT_ALLOWLISTED", lambda: RequestIdentity(role, RESOURCES[role].url + ".mirror", "HEAD", None))

    def test_07_query_and_fragment_rejected(self):
        role = "ROOT_SUMMARY"
        for suffix in ("?x=1", "#fragment"):
            self.code("PROBE_RESOURCE_NOT_ALLOWLISTED", lambda suffix=suffix: RequestIdentity(role, RESOURCES[role].url + suffix, "HEAD", None))

    def test_08_http_scheme_rejected(self):
        role = "ROOT_SUMMARY"
        url = RESOURCES[role].url.replace("https://", "http://")
        self.code("PROBE_RESOURCE_NOT_ALLOWLISTED", lambda: RequestIdentity(role, url, "HEAD", None))

    def test_09_arbitrary_range_rejected(self):
        role = "ROOT_SUMMARY"
        self.code("PROBE_RANGE_NOT_ALLOWED", lambda: RequestIdentity(role, RESOURCES[role].url, "GET", "bytes=1-2"))

    def test_10_cli_help(self):
        with self.assertRaises(SystemExit) as caught, contextlib.redirect_stdout(io.StringIO()):
            oc3_probe.main(["--help"])
        self.assertEqual(caught.exception.code, 0)

    def test_11_cli_plan_offline_and_complete(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(oc3_probe.main(["plan", "--offline", "--project", str(PROJECT)]), 0)
        plan = json.loads(output.getvalue())
        self.assertFalse(plan["network"])
        self.assertEqual(len(plan["resources"]), 7)
        self.assertEqual(plan["scientific_execution"], "NOT_STARTED")

    def test_12_cli_dry_run_no_mutation(self):
        before = sorted(str(p.relative_to(self.root)) for p in self.root.rglob("*"))
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(oc3_probe.main(["run", "--dry-run", "--project", str(PROJECT)]), 0)
        self.assertEqual(before, sorted(str(p.relative_to(self.root)) for p in self.root.rglob("*")))

    def test_13_execute_without_authorization_blocked(self):
        error = io.StringIO()
        with contextlib.redirect_stderr(error):
            self.assertEqual(oc3_probe.main(["run", "--execute-network", "--project", str(PROJECT)]), 23)
        self.assertIn("PROBE_HUMAN_AUTHORIZATION_REQUIRED", error.getvalue())

    def test_14_default_run_does_not_network(self):
        error = io.StringIO()
        with contextlib.redirect_stderr(error):
            self.assertEqual(oc3_probe.main(["run", "--project", str(PROJECT)]), 23)
        self.assertIn("PROBE_HUMAN_AUTHORIZATION_REQUIRED", error.getvalue())


class LedgerLimitResumeTests(Base):
    def identity(self, role="ROOT_SUMMARY", index=0):
        return RequestIdentity(role, RESOURCES[role].url, "GET", RANGES[index])

    def test_15_ledger_binding_required_fields(self):
        self.code("PROBE_LEDGER_BINDING_INVALID", lambda: ProbeBinding(PROBE_SPEC_SHA256, "bad", ENVIRONMENT_FINGERPRINT, "a" * 64, "x"))

    def test_16_ledger_reservation_precedes_transport(self):
        ledger = self.ledger()
        token = ledger.reserve(self.identity(), 65536)
        self.assertEqual(ledger.summary()["requests"][0]["state"], "RESERVED")
        ledger.finish(token, "FAILED")

    def test_17_head_accounting_no_body(self):
        ledger = self.ledger()
        response = self.head_response("ROOT_SUMMARY")
        engine = ProbeEngine(MemoryTransport([response]), ledger)
        engine.head("ROOT_SUMMARY")
        self.assertEqual(response.position, 0)
        self.assertEqual(ledger.count("http_body_bytes"), 0)

    def test_18_request_cap(self):
        ledger = self.ledger(requests=1)
        token = ledger.reserve(self.identity(), 1)
        ledger.finish(token, "FAILED")
        self.code("PROBE_RESOURCE_LIMIT_STOP", lambda: ledger.reserve(self.identity("NORTH_SUMMARY"), 1))

    def test_19_concurrency_one(self):
        ledger = self.ledger()
        ledger.reserve(self.identity(), 1)
        self.code("PROBE_CONCURRENCY_LIMIT", lambda: ledger.reserve(self.identity("NORTH_SUMMARY"), 1))

    def test_20_per_resource_256kib_cap(self):
        ledger = self.ledger(fits_resource_bytes=10)
        self.code("PROBE_RESOURCE_LIMIT_STOP", lambda: ledger.reserve(self.identity(), 11))

    def test_21_global_one_mib_fits_cap(self):
        ledger = self.ledger(fits_body_bytes=10)
        self.code("PROBE_RESOURCE_LIMIT_STOP", lambda: ledger.reserve(self.identity(), 11))

    def test_22_total_nine_mib_cap(self):
        ledger = self.ledger(http_body_bytes=10)
        self.code("PROBE_RESOURCE_LIMIT_STOP", lambda: ledger.reserve(self.identity(), 11))

    def test_23_manifest_eight_mib_cap(self):
        ledger = self.ledger(manifest_body_bytes=10)
        role = "ROOT_CHECKSUM_MANIFEST"
        identity = RequestIdentity(role, RESOURCES[role].url, "GET", None)
        self.code("PROBE_RESOURCE_LIMIT_STOP", lambda: ledger.reserve(identity, 11))

    def test_24_disk_and_io_caps(self):
        ledger = self.ledger(disk_bytes=5, io_bytes=5)
        ledger.charge_local(disk=5, io=5)
        self.code("PROBE_RESOURCE_LIMIT_STOP", lambda: ledger.charge_local(io=1))

    def test_25_limits_cannot_increase(self):
        self.code("PROBE_LIMIT_INCREASE_OR_INVALID", lambda: probe_caps({"requests": 33}))

    def test_26_lower_limits_allowed(self):
        self.assertEqual(probe_caps({"requests": 1})["requests"], 1)

    def test_27_failed_partial_bytes_charged(self):
        ledger = self.ledger()
        token = ledger.reserve(self.identity(), 20)
        ledger.charge_response(token, 7)
        ledger.finish(token, "FAILED")
        self.assertEqual(ledger.count("fits_body_bytes"), 7)

    def test_28_retry_exact_identity(self):
        ledger = self.ledger()
        first = ledger.reserve(self.identity(), 1)
        ledger.finish(first, "FAILED")
        second = ledger.reserve(self.identity(), 1, retry_of=first)
        ledger.finish(second, "COMPLETE")
        self.assertEqual(ledger.count("requests"), 2)

    def test_29_retry_different_range_rejected(self):
        ledger = self.ledger()
        first = ledger.reserve(self.identity(index=0), 1)
        ledger.finish(first, "FAILED")
        self.code("PROBE_RETRY_IDENTITY_MISMATCH", lambda: ledger.reserve(self.identity(index=1), 1, retry_of=first))

    def test_30_retry_limit(self):
        ledger = self.ledger()
        first = ledger.reserve(self.identity(), 1); ledger.finish(first, "FAILED")
        second = ledger.reserve(self.identity(), 1, retry_of=first); ledger.finish(second, "FAILED")
        self.code("PROBE_RETRY_LIMIT_STOP", lambda: ledger.reserve(self.identity(), 1, retry_of=second))

    def test_31_resume_verified_chunks_contiguous(self):
        ledger = self.ledger()
        ledger.register_chunk("ROOT_SUMMARY", RANGES[0], b"a")
        ledger.register_chunk("ROOT_SUMMARY", RANGES[1], b"b")
        self.assertEqual([row[0] for row in ledger.verified_chunks("ROOT_SUMMARY")], list(RANGES[:2]))

    def test_32_resume_gap_not_reused(self):
        ledger = self.ledger()
        ledger.register_chunk("ROOT_SUMMARY", RANGES[1], b"b")
        self.assertEqual(ledger.verified_chunks("ROOT_SUMMARY"), [])

    def test_33_resume_corrupt_chunk_rejected(self):
        ledger = self.ledger()
        ledger.register_chunk("ROOT_SUMMARY", RANGES[0], b"a")
        self.code("PROBE_RESUME_CHUNK_CORRUPT", lambda: ledger.register_chunk("ROOT_SUMMARY", RANGES[0], b"other"))

    def test_34_pre_commit_crash_rolls_back(self):
        ledger = self.ledger()
        with self.assertRaises(OSError):
            ledger.reserve(self.identity(), 1, fault="before_commit")
        self.assertEqual(ledger.count("requests"), 0)

    def test_35_post_commit_crash_is_recoverable_and_charged(self):
        ledger = self.ledger()
        with self.assertRaises(OSError):
            ledger.reserve(self.identity(), 1, fault="after_commit")
        self.assertEqual(ledger.count("requests"), 1)
        self.assertEqual(ledger.recover(), 1)
        self.assertEqual(ledger.summary()["requests"][0]["state"], "CRASH_CHARGED")
        self.assertEqual(ledger.count("fits_body_bytes"), 1)


class TransportRangeTests(Base):
    def test_36_accept_ranges_yes(self):
        ledger = self.ledger(); engine = ProbeEngine(MemoryTransport([self.head_response("ROOT_SUMMARY")]), ledger)
        self.assertEqual(engine.head("ROOT_SUMMARY")["accept-ranges"], "bytes")

    def test_37_accept_ranges_absent(self):
        response = self.head_response("ROOT_SUMMARY"); response.headers.pop("accept-ranges")
        ledger = self.ledger(); engine = ProbeEngine(MemoryTransport([response]), ledger)
        self.assertNotIn("accept-ranges", engine.head("ROOT_SUMMARY"))

    def test_38_accept_ranges_none_stops(self):
        ledger = self.ledger(); engine = ProbeEngine(MemoryTransport([self.head_response("ROOT_SUMMARY", accept="none")]), ledger)
        self.code("PROBE_RANGE_UNAVAILABLE_STOP", lambda: engine.fits_contract("ROOT_SUMMARY"))

    def test_39_exact_first_range(self):
        ledger = self.ledger(); transport = MemoryTransport([self.range_response("ROOT_SUMMARY", 0)])
        engine = ProbeEngine(transport, ledger); engine.range_get("ROOT_SUMMARY", 0)
        self.assertEqual(transport.calls[0].byte_range, RANGES[0])

    def test_40_out_of_order_range_rejected(self):
        ledger = self.ledger(); engine = ProbeEngine(MemoryTransport([]), ledger)
        self.code("PROBE_RANGE_NOT_ALLOWED", lambda: engine.range_get("ROOT_SUMMARY", 1))

    def test_41_four_chunk_cap(self):
        ledger = self.ledger()
        responses = [self.range_response("ROOT_SUMMARY", i) for i in range(4)]
        engine = ProbeEngine(MemoryTransport(responses), ledger)
        for index in range(4): engine.range_get("ROOT_SUMMARY", index)
        self.code("PROBE_RANGE_NOT_ALLOWED", lambda: engine.range_get("ROOT_SUMMARY", 4))

    def test_42_206_required(self):
        ledger = self.ledger(); response = self.range_response("ROOT_SUMMARY", 0, status=500)
        self.code("PROBE_TRANSPORT_INTEGRITY_FAILURE", lambda: ProbeEngine(MemoryTransport([response]), ledger).range_get("ROOT_SUMMARY", 0))

    def test_43_200_to_range_stop_without_body_read(self):
        ledger = self.ledger(); response = self.range_response("ROOT_SUMMARY", 0, status=200)
        self.code("PROBE_RANGE_UNAVAILABLE_STOP", lambda: ProbeEngine(MemoryTransport([response]), ledger).range_get("ROOT_SUMMARY", 0))
        self.assertEqual(response.position, 0)

    def test_44_416_to_range_stop(self):
        ledger = self.ledger(); response = self.range_response("ROOT_SUMMARY", 0, status=416)
        self.code("PROBE_RANGE_UNAVAILABLE_STOP", lambda: ProbeEngine(MemoryTransport([response]), ledger).range_get("ROOT_SUMMARY", 0))

    def test_45_content_range_start_mismatch(self):
        ledger = self.ledger(); response = self.range_response("ROOT_SUMMARY", 0, **{"content-range": "bytes 1-65535/999999"})
        self.code("PROBE_TRANSPORT_INTEGRITY_FAILURE", lambda: ProbeEngine(MemoryTransport([response]), ledger).range_get("ROOT_SUMMARY", 0))

    def test_46_content_range_end_mismatch(self):
        ledger = self.ledger(); response = self.range_response("ROOT_SUMMARY", 0, **{"content-range": "bytes 0-65534/999999"})
        self.code("PROBE_TRANSPORT_INTEGRITY_FAILURE", lambda: ProbeEngine(MemoryTransport([response]), ledger).range_get("ROOT_SUMMARY", 0))

    def test_47_total_length_inconsistency(self):
        ledger = self.ledger(); responses = [self.range_response("ROOT_SUMMARY", 0, total=999999), self.range_response("ROOT_SUMMARY", 1, total=888888)]
        engine = ProbeEngine(MemoryTransport(responses), ledger); engine.range_get("ROOT_SUMMARY", 0)
        self.code("PROBE_TRANSPORT_INTEGRITY_FAILURE", lambda: engine.range_get("ROOT_SUMMARY", 1))

    def test_48_head_total_length_inconsistency(self):
        ledger = self.ledger(); responses = [self.head_response("ROOT_SUMMARY", length=123), self.range_response("ROOT_SUMMARY", 0, total=999999)]
        engine = ProbeEngine(MemoryTransport(responses), ledger); engine.head("ROOT_SUMMARY")
        self.code("PROBE_TRANSPORT_INTEGRITY_FAILURE", lambda: engine.range_get("ROOT_SUMMARY", 0))

    def test_49_content_encoding_mutation_rejected(self):
        ledger = self.ledger(); response = self.range_response("ROOT_SUMMARY", 0, **{"content-encoding": "gzip"})
        self.code("PROBE_TRANSPORT_INTEGRITY_FAILURE", lambda: ProbeEngine(MemoryTransport([response]), ledger).range_get("ROOT_SUMMARY", 0))

    def test_50_redirect_rejected(self):
        ledger = self.ledger(); response = self.range_response("ROOT_SUMMARY", 0); response.final_url += ".redirect"
        self.code("PROBE_TRANSPORT_INTEGRITY_FAILURE", lambda: ProbeEngine(MemoryTransport([response]), ledger).range_get("ROOT_SUMMARY", 0))

    def test_51_partial_body_is_charged(self):
        ledger = self.ledger(); response = self.range_response("ROOT_SUMMARY", 0); response.fail_after = 10
        with self.assertRaises(OSError): ProbeEngine(MemoryTransport([response]), ledger).range_get("ROOT_SUMMARY", 0)
        self.assertEqual(ledger.count("fits_body_bytes"), 10)

    def test_51b_head_redirect_status_rejected(self):
        ledger = self.ledger(); response = self.head_response("ROOT_SUMMARY", status=302)
        self.code("PROBE_TRANSPORT_INTEGRITY_FAILURE", lambda: ProbeEngine(MemoryTransport([response]), ledger).head("ROOT_SUMMARY"))


class FITSAndGzipTests(Base):
    def test_52_primary_naxis_zero_and_bintable(self):
        contract = parse_target_bintable(fits_bytes(rows=False))
        self.assertEqual((contract.hdu_index, contract.xtension), (1, "BINTABLE"))

    def test_53_intervening_nonzero_payload_stops(self):
        data = fits_bytes(primary_bytes=primary(naxis=1, axes=(1,)), rows=False)
        self.code("INTERVENING_DATA_PAYLOAD_STOP", lambda: parse_target_bintable(data))

    def test_54_bintable_column_order(self):
        columns = [("A", "J", {}), ("B", "3E", {}), ("C", "8A", {})]
        contract = parse_target_bintable(fits_bytes(columns, rows=False))
        self.assertEqual([column.ttype for column in contract.columns], ["A", "B", "C"])

    def test_55_tform_scalar_types(self):
        columns = [(name, form, {}) for name, form in zip("ABCDEFGHIJK", ("L", "X", "B", "I", "J", "K", "A", "E", "D", "C", "M"))]
        contract = parse_target_bintable(fits_bytes(columns, table_bytes=table(columns, row_size=64), rows=False))
        self.assertEqual([column.tform for column in contract.columns], [value[1] for value in columns])

    def test_56_tform_vector_types(self):
        columns = [("VECTOR", "12E", {}), ("TEXT", "32A", {})]
        contract = parse_target_bintable(fits_bytes(columns, table_bytes=table(columns, row_size=80), rows=False))
        self.assertEqual(contract.columns[0].tform, "12E")

    def test_57_column_metadata(self):
        columns = [("X", "J", {"unit": "deg", "null": -1, "scale": 2.0, "zero": 10.0})]
        column = parse_target_bintable(fits_bytes(columns, rows=False)).columns[0]
        self.assertEqual((column.tunit, column.tnull, column.tscal, column.tzero), ("deg", -1, 2.0, 10.0))

    def test_58_checksum_datasum_unverified(self):
        extra = [card("CHECKSUM", "abc"), card("DATASUM", "123")]
        contract = parse_target_bintable(fits_bytes(table_bytes=table(extra=extra), rows=False))
        value = contract.as_dict()
        self.assertEqual(value["checksum"], {"value": "abc", "verified": False})
        self.assertFalse(value["datasum"]["verified"])

    def test_59_malformed_header_rejected(self):
        bad = bytearray(fits_bytes(rows=False)); bad[0] = 255
        self.code("PROBE_MALFORMED_FITS_HEADER", lambda: parse_target_bintable(bytes(bad)))

    def test_60_missing_end_requires_more_and_never_reads_rows(self):
        bad = b"".join((card("SIMPLE", True), card("BITPIX", 8), card("NAXIS", 0))).ljust(2880, b" ")
        with self.assertRaises(NeedMoreHeaderData): parse_target_bintable(bad)

    def test_61_arithmetic_overflow_rejected(self):
        huge = primary(naxis=2, axes=(2**62, 8)) + table()
        self.code("PROBE_FITS_ARITHMETIC_OVERFLOW", lambda: parse_target_bintable(huge))

    def test_62_patch_header_only_and_canary_absent(self):
        extractor = UncompressedHeaderExtractor(); raw = fits_bytes()
        self.assertTrue(extractor.feed(raw))
        self.assertNotIn(CANARY, extractor.header_bytes)
        self.assertEqual(len(extractor.header_bytes), 5760)

    def test_63_patch_post_boundary_opaque(self):
        extractor = UncompressedHeaderExtractor(); extractor.feed(fits_bytes())
        before = extractor.header_bytes; extractor.feed(CANARY)
        self.assertEqual(extractor.header_bytes, before)

    def test_64_gzip_one_chunk_exact_boundary(self):
        extractor = GzipHeaderExtractor(); compressed = gzip.compress(fits_bytes())
        self.assertTrue(extractor.feed(compressed))
        self.assertEqual(len(extractor.header_bytes), 5760)
        self.assertEqual(extractor.uncompressed_header_bytes_emitted, 5760)

    def test_65_gzip_multi_chunk_header(self):
        large_table = table(comments=1800)
        compressed = gzip.compress(fits_bytes(table_bytes=large_table), compresslevel=1)
        self.assertGreater(len(compressed), 65536)
        extractor = GzipHeaderExtractor()
        self.assertFalse(extractor.feed(compressed[:65536]))
        self.assertTrue(extractor.feed(compressed[65536:]))

    def test_66_gzip_row_canary_never_emitted(self):
        extractor = GzipHeaderExtractor(); extractor.feed(gzip.compress(fits_bytes()))
        self.assertNotIn(CANARY, extractor.header_bytes)

    def test_67_gzip_post_header_attempt_tripwire(self):
        extractor = GzipHeaderExtractor(); extractor.feed(gzip.compress(fits_bytes()))
        self.code("PROBE_ROW_OBSERVATION_FORBIDDEN", lambda: extractor.feed(b"more"))

    def test_68_gzip_resume_reconstruction(self):
        compressed = gzip.compress(fits_bytes())
        chunks = [compressed[:20], compressed[20:]]
        rebuilt = reconstruct_gzip_header(chunks)
        self.assertIsNotNone(rebuilt.contract)
        self.assertEqual(rebuilt.header_bytes, reconstruct_gzip_header(chunks).header_bytes)


class ManifestContractTripwireOutcomeTests(Base):
    def manifest(self, role):
        resource = RESOURCES[role]
        return f"{resource.expected_sha256}  {resource.expected_name}\n".encode()

    def test_69_checksum_exact_entry(self):
        role = "ROOT_CHECKSUM_MANIFEST"
        self.assertEqual(parse_checksum_manifest(self.manifest(role), RESOURCES[role]), RESOURCES[role].expected_sha256)

    def test_70_checksum_duplicate_rejected(self):
        role = "ROOT_CHECKSUM_MANIFEST"
        self.code("PROVIDER_CHECKSUM_DOCUMENTATION_CONFLICT_STOP", lambda: parse_checksum_manifest(self.manifest(role) * 2, RESOURCES[role]))

    def test_71_checksum_missing_rejected(self):
        role = "ROOT_CHECKSUM_MANIFEST"
        body = ("a" * 64 + "  other.fits\n").encode()
        self.code("PROVIDER_CHECKSUM_DOCUMENTATION_CONFLICT_STOP", lambda: parse_checksum_manifest(body, RESOURCES[role]))

    def test_72_checksum_malformed_rejected(self):
        role = "ROOT_CHECKSUM_MANIFEST"
        self.code("PROVIDER_CHECKSUM_DOCUMENTATION_CONFLICT_STOP", lambda: parse_checksum_manifest(b"bad hash\n", RESOURCES[role]))

    def test_73_checksum_documentary_mismatch(self):
        role = "ROOT_CHECKSUM_MANIFEST"; resource = RESOURCES[role]
        body = ("0" * 64 + "  " + resource.expected_name + "\n").encode()
        self.code("PROVIDER_CHECKSUM_DOCUMENTATION_CONFLICT_STOP", lambda: parse_checksum_manifest(body, resource))

    def test_74_checksum_ambiguous_basename(self):
        role = "ROOT_CHECKSUM_MANIFEST"; resource = RESOURCES[role]
        body = self.manifest(role) + (resource.expected_sha256 + "  alternate/" + resource.expected_name + "\n").encode()
        self.code("PROVIDER_CHECKSUM_DOCUMENTATION_CONFLICT_STOP", lambda: parse_checksum_manifest(body, resource))

    def test_75_patch_checksum_absent_explicit(self):
        self.assertEqual(patch_checksum_status(), "PATCH_LIST_PROVIDER_CHECKSUM_NOT_FOUND")

    def contracts(self, root="J", north="I", south="I"):
        result = {}
        for role, form in (("ROOT_SUMMARY", root), ("NORTH_SUMMARY", north), ("SOUTH_SUMMARY", south)):
            if form is not None:
                result[role] = parse_target_bintable(fits_bytes([("BRICKID", form, {})], rows=False))
        return result

    def test_76_brickid_documented_support(self):
        self.assertEqual(brickid_outcome(self.contracts()), "BRICKID_PHYSICAL_LAYOUT_SUPPORTS_DOCUMENTATION")

    def test_77_brickid_structural_conflict(self):
        self.assertEqual(brickid_outcome(self.contracts(north="J")), "BRICKID_PHYSICAL_LAYOUT_CONFLICTS_WITH_DOCUMENTATION")

    def test_78_brickid_unresolved_missing(self):
        self.assertEqual(brickid_outcome(self.contracts(south=None)), "BRICKID_PHYSICAL_LAYOUT_UNRESOLVED")

    def test_79_brickid_unresolved_ambiguous(self):
        contracts = self.contracts(); contracts["SOUTH_SUMMARY"] = parse_target_bintable(fits_bytes([("BRICKID", "I", {}), ("brickid", "I", {})], rows=False))
        self.assertEqual(brickid_outcome(contracts), "BRICKID_PHYSICAL_LAYOUT_UNRESOLVED")

    def candidate(self):
        header = parse_target_bintable(fits_bytes(rows=False))
        return PhysicalContractCandidate(1, "ROOT_SUMMARY", RESOURCES["ROOT_SUMMARY"].url,
                                         RESOURCES["ROOT_SUMMARY"].url, "gzip", 123, "application/fits",
                                         '"etag"', "date", header, "d" * 64, ("e" * 64,))

    def test_80_contract_canonicalization_deterministic(self):
        self.assertEqual(self.candidate().sha256(), self.candidate().sha256())

    def test_81_contract_has_no_row_values(self):
        raw = self.candidate().canonical_bytes()
        self.assertNotIn(CANARY, raw)
        for forbidden in (b"row_values", b"cells", b"candidate_bricks"):
            self.assertNotIn(forbidden, raw)

    def test_82_transport_and_contract_models_distinct(self):
        self.assertNotEqual(set(TransportEvidence.__dataclass_fields__), set(PhysicalContractCandidate.__dataclass_fields__))

    def test_83_all_row_tripwires_fail(self):
        names = ("hdu_data", "table_read", "provider_schema_decode", "resolve_bootstrap_bricks", "decode_row", "decode_cell", "selection_helper")
        for name in names:
            self.code("PROBE_ROW_OBSERVATION_FORBIDDEN", lambda name=name: getattr(RowObservationTripwire, name)())

    def test_84_probe_module_has_no_forbidden_imports(self):
        source = (PROJECT / "oc3/oc3lib/physical_contract_probe.py").read_text()
        for value in ("from .bootstrap", "from .provider_schema", "from .selection", "astropy.table"):
            self.assertNotIn(value, source)

    def test_85_no_canary_in_errors_or_contract(self):
        try:
            RowObservationTripwire.decode_row(CANARY)
        except ProbeError as error:
            self.assertNotIn(CANARY.decode(), str(error))
        self.assertNotIn(CANARY, self.candidate().canonical_bytes())

    def test_86_terminal_precedence_exact(self):
        events = ["PROBE_RANGE_UNAVAILABLE_STOP", "PROBE_TRANSPORT_INTEGRITY_FAILURE", "PROBE_ROW_OBSERVATION_FORBIDDEN"]
        self.assertEqual(terminal_outcome(events), TERMINAL_PRECEDENCE[0])

    def test_87_partial_precedes_resolved(self):
        self.assertEqual(terminal_outcome(["INTERVENING_DATA_PAYLOAD_STOP", "PROBE_PHYSICAL_CONTRACTS_RESOLVED"]),
                         "PROBE_PHYSICAL_CONTRACTS_PARTIALLY_RESOLVED")

    def test_88_no_production_directories_mutated(self):
        # Later reviewed stages intentionally materialized these exact frozen
        # inputs. Preserve them while retaining the tripwire for every other
        # production directory.
        input_names = {item.name for item in (PROJECT / "oc3/INPUTS").iterdir()}
        input_base = {"OC3_DEVELOPMENT_BRICKS.csv",
                          "OC3_RESOURCE_CONTRACT_PROBE_BINDING_001.json",
                          "OC3_RESOURCE_CONTRACT_PROBE_BINDING_002.json",
                          "OC3_AUXILIARY_14_ACQUISITION_CANDIDATE_001.json",
                          "OC3_AUXILIARY_ACQUISITION_AUTHORIZATION_001.json",
                          "OC3_FIXED_NATIVE_RESOURCE_CONTRACT_001.json",
                          "OC3_FIXED_NATIVE_RESOURCE_PROBE_BINDING_001.json",
                          "OC3_PSF_RESOURCE_CONTRACT_001.json",
                          "OC3_COADD_PSF_CONTRACT_PROBE_BINDING_001.json",
                          "OC3_FIXED_NATIVE_PSF_ACQUISITION_CANDIDATE_001.json",
                          "OC3_FIXED_NATIVE_PSF_ACQUISITION_AUTHORIZATION_001.json"}
        eligibility_implementation = input_base | {
            "OC3_GALAXY_ELIGIBILITY_DOCUMENTARY_MANIFEST_001.json",
            "OC3_PHOTSYS_AUTHORITY_DOCUMENTARY_MANIFEST.json"}
        photsys_candidate = eligibility_implementation | {
            "OC3_PHOTSYS_AUTHORITY_RESOURCE_CANDIDATE.json"}
        photsys_documentary002_parse = photsys_candidate | {
            "OC3_PHOTSYS_DOCUMENTARY_002_HISTORICAL_PARSE_EVIDENCE.json"}
        photsys_documentary002_candidate = photsys_documentary002_parse | {
            "OC3_PHOTSYS_DOCUMENTARY_002_CANDIDATE.json"}
        photsys_physical_candidate = photsys_documentary002_candidate | {
            "OC3_PHOTSYS_PHYSICAL_PROBE_CANDIDATE_001.json"}
        photsys_reviewed_contract = photsys_physical_candidate | {
            "OC3_PHOTSYS_AUTHORITY_REVIEWED_PHYSICAL_CONTRACT_001.json"}
        photsys_full_acquisition_candidate = photsys_reviewed_contract | {
            "OC3_PHOTSYS_FULL_ACQUISITION_CANDIDATE_001.json"}
        photsys_selective_validation_candidate = photsys_full_acquisition_candidate | {
            "OC3_PHOTSYS_SELECTIVE_VALUE_VALIDATION_CANDIDATE_001.json"}
        photsys_histogram_candidate = photsys_selective_validation_candidate | {
            "OC3_PHOTSYS_RAW_BYTE_HISTOGRAM_CANDIDATE_001.json"}
        photsys_zero_provenance_candidate = photsys_histogram_candidate | {
            "OC3_PHOTSYS_ZERO_BYTE_PROVENANCE_RESOURCE_MANIFEST_001.json",
            "OC3_PHOTSYS_ZERO_BYTE_PROVENANCE_RESEARCH_CANDIDATE_001.json"}
        photsys_archive_head_candidate = photsys_zero_provenance_candidate | {
            "OC3_PHOTSYS_DESITARGET_ARCHIVE_HEAD_PROBE_CANDIDATE_001.json"}
        photsys_archive_range_candidate = photsys_archive_head_candidate | {
            "OC3_PHOTSYS_DESITARGET_ARCHIVE_RANGE_SIZE_PROBE_CANDIDATE_001.json"}
        photsys_autonomy_bootstrap = photsys_archive_range_candidate | {
            "OC3_AUTONOMY_MANDATE_001.json",
            "OC3_PHOTSYS_DESITARGET_ARCHIVE_RANGE_SIZE_RESOURCE_MANIFEST_002.json",
            "OC3_PHOTSYS_DESITARGET_ARCHIVE_RANGE_SIZE_PROBE_CANDIDATE_002.json"}
        photsys_autonomy_hardened = photsys_autonomy_bootstrap | {
            "OC3_AUTONOMY_POLICY_CORE_MANIFEST_001.json",
            "OC3_PHOTSYS_DESITARGET_ARCHIVE_RANGE_SIZE_ACTION_VALIDATION_RECEIPT_003.json",
            "OC3_PHOTSYS_DESITARGET_ARCHIVE_RANGE_SIZE_PROBE_CANDIDATE_003.json"}
        photsys_terminal_inputs = photsys_autonomy_hardened | {
            "OC3_PHOTSYS_DESITARGET_COMMIT_OBJECT_RESOURCE_MANIFEST_001.json",
            "OC3_PHOTSYS_DESITARGET_COMMIT_OBJECT_PROBE_CANDIDATE_001.json",
            "OC3_PHOTSYS_DESITARGET_COMMIT_OBJECT_ACTION_VALIDATION_RECEIPT_001.json",
            "OC3_PHOTSYS_DESITARGET_RECURSIVE_TREE_RESOURCE_MANIFEST_001.json",
            "OC3_PHOTSYS_DESITARGET_RECURSIVE_TREE_PROBE_CANDIDATE_001.json",
            "OC3_PHOTSYS_DESITARGET_RECURSIVE_TREE_ACTION_VALIDATION_RECEIPT_001.json",
            "OC3_PHOTSYS_DESITARGET_MANDATORY_BLOB_BUNDLE_RESOURCE_MANIFEST_001.json",
            "OC3_PHOTSYS_DESITARGET_MANDATORY_BLOB_BUNDLE_CANDIDATE_001.json",
            "OC3_PHOTSYS_DESITARGET_MANDATORY_BLOB_BUNDLE_ACTION_VALIDATION_RECEIPT_001.json",
            "OC3_PHOTSYS_MYERS_RANDOM_CATALOG_RESOURCE_MANIFEST_001.json",
            "OC3_PHOTSYS_MYERS_RANDOM_CATALOG_PROVENANCE_CANDIDATE_001.json",
            "OC3_PHOTSYS_MYERS_RANDOM_CATALOG_ACTION_VALIDATION_RECEIPT_001.json",
            "OC3_PHOTSYS_DESITARGET_SELECTED_PRODUCTION_BLOBS_RESOURCE_MANIFEST_001.json",
            "OC3_PHOTSYS_DESITARGET_SELECTED_PRODUCTION_BLOBS_CANDIDATE_001.json",
            "OC3_PHOTSYS_DESITARGET_SELECTED_PRODUCTION_BLOBS_ACTION_VALIDATION_RECEIPT_001.json"}
        observational_multiplicity_bootstrap = photsys_terminal_inputs | {
            "OC3_OBSERVATIONAL_MULTIPLICITY_AUTONOMY_MANDATE_001.json",
            "OC3_OBSERVATIONAL_MULTIPLICITY_POLICY_CORE_MANIFEST_001.json",
            "OC3_GLOBAL_VIEW_RELATION_AUDIT_CANDIDATE_001.json",
            "OC3_GLOBAL_VIEW_RELATION_AUDIT_CANDIDATE_VALIDATION_001.json"}
        observational_multiplicity_hardened = observational_multiplicity_bootstrap | {
            "OC3_GLOBAL_VIEW_RELATION_AUDIT_CANDIDATE_002.json",
            "OC3_GLOBAL_VIEW_RELATION_AUDIT_CANDIDATE_VALIDATION_002.json"}
        observational_multiplicity_policy_v2 = observational_multiplicity_hardened | {
            "OC3_OBSERVATIONAL_MULTIPLICITY_AUTONOMY_MANDATE_002.json",
            "OC3_OBSERVATIONAL_MULTIPLICITY_POLICY_CORE_MANIFEST_002.json",
            "OC3_GLOBAL_VIEW_RELATION_AUDIT_CANDIDATE_003.json",
            "OC3_GLOBAL_VIEW_RELATION_AUDIT_CANDIDATE_VALIDATION_003.json"}
        observational_multiplicity_runtime_binding = observational_multiplicity_policy_v2 | {
            "OC3_GLOBAL_VIEW_RELATION_AUDIT_CANDIDATE_004.json",
            "OC3_GLOBAL_VIEW_RELATION_AUDIT_CANDIDATE_VALIDATION_004.json"}
        eligibility_p0 = eligibility_implementation | {
            "OC3_GALAXY_ELIGIBILITY_PANEL_MANIFEST.json",
            "OC3_GALAXY_ELIGIBILITY_P1_AUTHORIZATION_CANDIDATE_001.json"}
        self.assertIn(input_names, (input_base, eligibility_implementation,
                                    photsys_candidate, photsys_documentary002_parse,
                                    photsys_documentary002_candidate,
                                    photsys_physical_candidate,
                                    photsys_reviewed_contract,
                                    photsys_full_acquisition_candidate,
                                    photsys_selective_validation_candidate,
                                    photsys_histogram_candidate,
                                    photsys_zero_provenance_candidate,
                                    photsys_archive_head_candidate,
                                    photsys_archive_range_candidate,
                                    photsys_autonomy_bootstrap,
                                    photsys_autonomy_hardened,
                                    photsys_terminal_inputs,
                                    observational_multiplicity_bootstrap,
                                    observational_multiplicity_hardened,
                                    observational_multiplicity_policy_v2,
                                    observational_multiplicity_runtime_binding,
                                    eligibility_p0))
        technical_names = {item.name for item in (PROJECT / "oc3/TECHNICAL_INDEX").iterdir()}
        technical_base = {"OC3_LOCATIONS.json", "OC3_SELECTION_FLOW.csv",
                          "OC3_PSF_IDENTITIES.json"}
        self.assertIn(technical_names,
                      (technical_base,
                       technical_base | {"OC3_NATIVE_EXTRACTION_MANIFEST.json"}))
        for relative in ("oc3/provenance", "oc3/RAW_IMMUTABLE", "oc3/reports"):
            self.assertFalse(any((PROJECT / relative).iterdir()))

    def test_89_single_audited_probe_attempt_is_preserved_immutably(self):
        probe_root = PROJECT / "oc3/provider_contract_probe"
        attempt = probe_root / "OC3-PHYSICAL-CONTRACT-PROBE-001"
        expected = {
            "PROBE_CHECKSUM_EVIDENCE.json": (1109, "f464983d87ef4ab2776b699a54490874667c7f4a7ca138269180d8467defee3f"),
            "PROBE_EVENTS.json": (145, "d130134b7bb46a612c8213aba80b0d5d613303d04d1870063b5d0a5677e75fd0"),
            "PROBE_LEDGER.sqlite": (40960, "8bd834e3a1fa28d820d7ac81f8fe049749761f518b569cc2d915beb32191b441"),
            "PROBE_PHYSICAL_CONTRACT_CANDIDATES.json": (15421, "eaa8287fab7c4de44dc265239dcf3b9e9e56f5c2adce4334711634cb9e9b7eb1"),
            "PROBE_TERMINAL.json": (257, "27b944d654045c314505e548242eee85416cf9391ffc337d5f4a834fbb3c84e3"),
            "PROBE_TRANSPORT_EVIDENCE.json": (2462, "cd0248193669bb2d303ca55fb24e3ab46f9b0ac2aefc59086c3df2dd49f4975a"),
            "compressed_prefix/NORTH_SUMMARY/0.part": (65536, "7b0cb006d16f193cdcef2120169d039300aa56d9aca863decc3d654c20be4cd6"),
            "compressed_prefix/ROOT_SUMMARY/0.part": (65536, "28c7b004fbbcf9cd02999c6345b6b5f428c901bf8b76fc10d6612aa29d5ded5e"),
            "compressed_prefix/SOUTH_SUMMARY/0.part": (65536, "383aa7a812405560e418efff4109268979c3ad45118e9d00ffbb0ad3c666748b"),
            "transport/NORTH_SUMMARY.head.json": (508, "833b31cdccb786069e07c2bbf0e286ca8a84c410399ab3b9ad1fa28e321e0a9c"),
            "transport/ROOT_SUMMARY.head.json": (490, "bf79a2189fd3ae09863059f4c5bcd5ae6531a4d242d75cd813603f3b8ddc972a"),
            "transport/SOUTH_PATCH_LIST.head.json": (410, "9d8ce43f7bc76529045a80c495d47787c1d7d539cbbd142d2d0889919edc6c3c"),
            "transport/SOUTH_SUMMARY.head.json": (508, "71636341463e738a601cf8aa8c24131e900762bb802ac5d17b12751bf24cb166"),
        }
        self.assertTrue(probe_root.is_dir())
        self.assertEqual(sorted(path.name for path in probe_root.iterdir()),
                         ["OC3-PHYSICAL-CONTRACT-PROBE-001"])
        observed = {str(path.relative_to(attempt)): path
                    for path in attempt.rglob("*") if path.is_file()}
        self.assertEqual(set(observed), set(expected))
        for relative, (size, sha256) in expected.items():
            path = observed[relative]
            self.assertEqual(path.stat().st_size, size)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), sha256)
        terminal = json.loads(observed["PROBE_TERMINAL.json"].read_text())
        self.assertEqual(terminal["outcome"], "PROBE_PHYSICAL_CONTRACTS_RESOLVED")
        self.assertEqual(terminal["scientific_execution"], "NOT_STARTED")
        authorization = PROJECT / "oc3/PROVIDER_PHYSICAL_CONTRACT_PROBE_AUTHORIZATION_001.json"
        authorization_sha256 = "e9ebef8bae1c78689ae6ca5ffc0eb0dc94d3901f6a785df758a414712fa55757"
        self.assertEqual(hashlib.sha256(authorization.read_bytes()).hexdigest(), authorization_sha256)
        uri = "file:%s?mode=ro&immutable=1" % observed["PROBE_LEDGER.sqlite"].resolve()
        with sqlite3.connect(uri, uri=True) as connection:
            binding = json.loads(connection.execute(
                "SELECT value FROM config WHERE key='binding'").fetchone()[0])
            retries = connection.execute(
                "SELECT COUNT(*) FROM requests WHERE retry_of IS NOT NULL").fetchone()[0]
        self.assertEqual(binding["attempt_id"], "OC3-PHYSICAL-CONTRACT-PROBE-001")
        self.assertEqual(binding["human_authorization_sha256"], authorization_sha256)
        self.assertEqual(retries, 0)

    def test_90_offline_transport_has_no_capability(self):
        identity = RequestIdentity("ROOT_SUMMARY", RESOURCES["ROOT_SUMMARY"].url, "HEAD", None)
        self.code("PROBE_OFFLINE_NETWORK_FORBIDDEN", lambda: OfflineTransport().open(identity))

    def test_91_runtime_wall_cap(self):
        guard = ProbeRuntimeGuard({"wall_seconds": 1})
        guard.wall_start -= 2
        self.code("PROBE_RESOURCE_LIMIT_STOP", guard.check)

    def test_92_full_synthetic_execution_resolves_without_rows(self):
        ledger = self.ledger()
        responses = []
        forms = {"ROOT_SUMMARY": "J", "NORTH_SUMMARY": "I", "SOUTH_SUMMARY": "I", "SOUTH_PATCH_LIST": "J"}
        for role in FITS_ROLES:
            responses.append(self.head_response(role))
            raw = fits_bytes([("BRICKID", forms[role], {})])
            body = gzip.compress(raw) if RESOURCES[role].compression == "gzip" else raw
            body = body + b"Z" * (65536 - len(body))
            responses.append(self.range_response(role, 0, body))
        for role in MANIFEST_ROLES:
            body = self.manifest(role)
            responses.append(MemoryResponse(body, status=200, headers={"content-length": str(len(body))}, final_url=RESOURCES[role].url))
        outcome = execute_probe(MemoryTransport(responses), ledger, self.root / "attempt")
        self.assertEqual(outcome, "PROBE_PHYSICAL_CONTRACTS_RESOLVED")
        terminal = json.loads((self.root / "attempt/PROBE_TERMINAL.json").read_text())
        self.assertEqual(terminal["scientific_execution"], "NOT_STARTED")
        candidate = (self.root / "attempt/PROBE_PHYSICAL_CONTRACT_CANDIDATES.json").read_bytes()
        self.assertNotIn(CANARY, candidate)
        self.assertEqual(ledger.count("requests"), 11)

    def test_93_full_synthetic_transport_failure_has_one_terminal(self):
        ledger = self.ledger()
        response = self.head_response("ROOT_SUMMARY", status=500)
        outcome = execute_probe(MemoryTransport([response]), ledger, self.root / "failed")
        self.assertEqual(outcome, "PROBE_TRANSPORT_INTEGRITY_FAILURE")
        value = json.loads((self.root / "failed/PROBE_TERMINAL.json").read_text())
        self.assertEqual(value["outcome"], outcome)


class Clarification001RangeEOFTests(Base):
    """Prospective synthetic coverage for Clarification 001 only."""

    def eof_response(self, role, index, total, body=None, *, end=None,
                     content_length=None, content_range=None, status=206, **headers):
        start = index * 65536
        actual_end = min(start + 65535, total - 1) if end is None else end
        expected = max(0, actual_end - start + 1)
        body = b"x" * expected if body is None else body
        values = {
            "content-length": str(len(body) if content_length is None else content_length),
            "content-range": content_range or f"bytes {start}-{actual_end}/{total}",
            **headers,
        }
        return MemoryResponse(body, status=status, headers=values, final_url=RESOURCES[role].url)

    def test_c01_clarification_authority_and_history_bound(self):
        self.assertEqual(file_hash(PROJECT / PROBE_CLARIFICATION_001_NAME), PROBE_CLARIFICATION_001_SHA256)
        self.assertEqual(PRE_CLARIFICATION_001_IMPLEMENTATION,
                         "df8fe72deb876b567e076e05fbd7108bd4734ead4b3b467bc2c7d1f306b836f7")

    def test_c02_first_range_non_eof_full_accepted(self):
        ledger = self.ledger()
        engine = ProbeEngine(MemoryTransport([self.eof_response("ROOT_SUMMARY", 0, 90000)]), ledger)
        self.assertEqual(len(engine.range_get("ROOT_SUMMARY", 0)), 65536)

    def test_c03_first_range_eof_short_accepted(self):
        ledger = self.ledger()
        engine = ProbeEngine(MemoryTransport([self.eof_response("ROOT_SUMMARY", 0, 40000)]), ledger)
        self.assertEqual(len(engine.range_get("ROOT_SUMMARY", 0)), 40000)

    def test_c04_second_range_eof_short_accepted(self):
        ledger = self.ledger()
        responses = [self.eof_response("ROOT_SUMMARY", 0, 90000),
                     self.eof_response("ROOT_SUMMARY", 1, 90000)]
        engine = ProbeEngine(MemoryTransport(responses), ledger)
        self.assertEqual(len(engine.range_get("ROOT_SUMMARY", 0)), 65536)
        self.assertEqual(len(engine.range_get("ROOT_SUMMARY", 1)), 24464)

    def test_c05_third_range_eof_short_accepted(self):
        ledger = self.ledger()
        responses = [self.eof_response("ROOT_SUMMARY", i, 150000) for i in range(3)]
        engine = ProbeEngine(MemoryTransport(responses), ledger)
        sizes = [len(engine.range_get("ROOT_SUMMARY", i)) for i in range(3)]
        self.assertEqual(sizes, [65536, 65536, 18928])

    def test_c06_fourth_range_eof_short_accepted(self):
        ledger = self.ledger()
        responses = [self.eof_response("ROOT_SUMMARY", i, 210000) for i in range(4)]
        engine = ProbeEngine(MemoryTransport(responses), ledger)
        sizes = [len(engine.range_get("ROOT_SUMMARY", i)) for i in range(4)]
        self.assertEqual(sizes, [65536, 65536, 65536, 13392])

    def test_c07_exact_eof_edge_is_full_range(self):
        ledger = self.ledger()
        engine = ProbeEngine(MemoryTransport([self.eof_response("ROOT_SUMMARY", 0, 65536)]), ledger)
        self.assertEqual(len(engine.range_get("ROOT_SUMMARY", 0)), 65536)

    def test_c08_non_eof_short_span_rejected(self):
        ledger = self.ledger()
        response = self.eof_response("ROOT_SUMMARY", 0, 90000, body=b"x" * 40000,
                                     end=39999, content_length=40000)
        self.code("PROBE_TRANSPORT_INTEGRITY_FAILURE",
                  lambda: ProbeEngine(MemoryTransport([response]), ledger).range_get("ROOT_SUMMARY", 0))

    def test_c09_content_length_span_mismatch_rejected(self):
        ledger = self.ledger()
        response = self.eof_response("ROOT_SUMMARY", 0, 40000, content_length=39999)
        self.code("PROBE_TRANSPORT_INTEGRITY_FAILURE",
                  lambda: ProbeEngine(MemoryTransport([response]), ledger).range_get("ROOT_SUMMARY", 0))

    def test_c10_body_shorter_than_declared_rejected_and_charged(self):
        ledger = self.ledger()
        response = self.eof_response("ROOT_SUMMARY", 0, 40000, body=b"x" * 39999,
                                     content_length=40000)
        self.code("PROBE_TRANSPORT_INTEGRITY_FAILURE",
                  lambda: ProbeEngine(MemoryTransport([response]), ledger).range_get("ROOT_SUMMARY", 0))
        self.assertEqual(ledger.count("fits_body_bytes"), 39999)

    def test_c11_body_longer_than_declared_rejected_and_charged(self):
        ledger = self.ledger()
        response = self.eof_response("ROOT_SUMMARY", 0, 40000, body=b"x" * 40001,
                                     content_length=40000)
        self.code("PROBE_TRANSPORT_INTEGRITY_FAILURE",
                  lambda: ProbeEngine(MemoryTransport([response]), ledger).range_get("ROOT_SUMMARY", 0))
        self.assertEqual(ledger.count("fits_body_bytes"), 40001)

    def test_c12_head_length_and_range_total_must_match(self):
        ledger = self.ledger()
        transport = MemoryTransport([self.head_response("ROOT_SUMMARY", length=40001),
                                     self.eof_response("ROOT_SUMMARY", 0, 40000)])
        engine = ProbeEngine(transport, ledger)
        engine.head("ROOT_SUMMARY")
        self.code("PROBE_TRANSPORT_INTEGRITY_FAILURE", lambda: engine.range_get("ROOT_SUMMARY", 0))

    def test_c13_etag_drift_rejected(self):
        ledger = self.ledger()
        transport = MemoryTransport([self.head_response("ROOT_SUMMARY", length=40000, etag='"v1"'),
                                     self.eof_response("ROOT_SUMMARY", 0, 40000, etag='"v2"')])
        engine = ProbeEngine(transport, ledger)
        engine.head("ROOT_SUMMARY")
        self.code("PROBE_TRANSPORT_INTEGRITY_FAILURE", lambda: engine.range_get("ROOT_SUMMARY", 0))

    def test_c14_last_modified_drift_rejected(self):
        ledger = self.ledger()
        transport = MemoryTransport([
            self.head_response("ROOT_SUMMARY", length=40000, **{"last-modified": "one"}),
            self.eof_response("ROOT_SUMMARY", 0, 40000, **{"last-modified": "two"}),
        ])
        engine = ProbeEngine(transport, ledger)
        engine.head("ROOT_SUMMARY")
        self.code("PROBE_TRANSPORT_INTEGRITY_FAILURE", lambda: engine.range_get("ROOT_SUMMARY", 0))

    def test_c15_no_next_request_when_start_at_or_beyond_known_eof(self):
        ledger = self.ledger()
        transport = MemoryTransport([self.eof_response("ROOT_SUMMARY", 0, 40000)])
        engine = ProbeEngine(transport, ledger)
        engine.range_get("ROOT_SUMMARY", 0)
        self.code("PROBE_REPRESENTATION_EOF_BEFORE_HEADER_COMPLETE",
                  lambda: engine.range_get("ROOT_SUMMARY", 1))
        self.assertEqual(len(transport.calls), 1)
        self.assertEqual(ledger.count("requests"), 1)

    def test_c16_next_request_remains_literal_when_start_before_eof(self):
        ledger = self.ledger()
        transport = MemoryTransport([self.eof_response("ROOT_SUMMARY", 0, 90000),
                                     self.eof_response("ROOT_SUMMARY", 1, 90000)])
        engine = ProbeEngine(transport, ledger)
        engine.range_get("ROOT_SUMMARY", 0)
        engine.range_get("ROOT_SUMMARY", 1)
        self.assertEqual([call.byte_range for call in transport.calls], list(RANGES[:2]))

    def test_c17_wildcard_total_rejected(self):
        ledger = self.ledger()
        response = self.eof_response("ROOT_SUMMARY", 0, 40000,
                                     content_range="bytes 0-39999/*")
        self.code("PROBE_TRANSPORT_INTEGRITY_FAILURE",
                  lambda: ProbeEngine(MemoryTransport([response]), ledger).range_get("ROOT_SUMMARY", 0))

    def test_c18_zero_negative_nondecimal_and_overflow_totals_rejected(self):
        invalid = ("0", "-1", "4e4", "40000 ", str(2**63))
        for index, total in enumerate(invalid):
            with self.subTest(total=total):
                root = self.root / f"invalid-{index}"
                ledger = ProbeLedger(root / "ledger.sqlite", binding())
                self.ledgers.append(ledger)
                response = self.eof_response("ROOT_SUMMARY", 0, 40000,
                                             content_range=f"bytes 0-39999/{total}")
                self.code("PROBE_TRANSPORT_INTEGRITY_FAILURE",
                          lambda ledger=ledger, response=response:
                          ProbeEngine(MemoryTransport([response]), ledger).range_get("ROOT_SUMMARY", 0))

    def test_c19_eof_before_uncompressed_header_is_partial_without_next_request(self):
        incomplete = (primary() + table(comments=600))[:40000]
        ledger = self.ledger()
        transport = MemoryTransport([self.head_response("SOUTH_PATCH_LIST", length=len(incomplete)),
                                     self.eof_response("SOUTH_PATCH_LIST", 0, len(incomplete), body=incomplete)])
        engine = ProbeEngine(transport, ledger)
        self.code("PROBE_REPRESENTATION_EOF_BEFORE_HEADER_COMPLETE",
                  lambda: engine.fits_contract("SOUTH_PATCH_LIST"))
        self.assertEqual(len(transport.calls), 2)
        self.assertEqual(terminal_outcome(["PROBE_REPRESENTATION_EOF_BEFORE_HEADER_COMPLETE"]),
                         "PROBE_PHYSICAL_CONTRACTS_PARTIALLY_RESOLVED")

    def test_c20_eof_before_gzip_header_is_partial_without_next_request(self):
        incomplete = (primary() + table(comments=600))[:40000]
        compressed = gzip.compress(incomplete)
        ledger = self.ledger()
        transport = MemoryTransport([self.head_response("ROOT_SUMMARY", length=len(compressed)),
                                     self.eof_response("ROOT_SUMMARY", 0, len(compressed), body=compressed)])
        engine = ProbeEngine(transport, ledger)
        self.code("PROBE_REPRESENTATION_EOF_BEFORE_HEADER_COMPLETE",
                  lambda: engine.fits_contract("ROOT_SUMMARY"))
        self.assertEqual(len(transport.calls), 2)

    def test_c21_patch_eof_short_keeps_post_header_canary_opaque(self):
        raw = fits_bytes()
        self.assertLess(len(raw), 65536)
        ledger = self.ledger()
        transport = MemoryTransport([self.head_response("SOUTH_PATCH_LIST", length=len(raw)),
                                     self.eof_response("SOUTH_PATCH_LIST", 0, len(raw), body=raw)])
        contract, evidence = ProbeEngine(transport, ledger).fits_contract("SOUTH_PATCH_LIST")
        exported = canonical({"contract": contract.as_dict(), "evidence": evidence.as_dict()})
        self.assertNotIn(CANARY, exported)
        self.assertEqual(contract.header_end, 5760)
        self.assertEqual(evidence.wire_bytes_received, len(raw))

    def test_c22_gzip_eof_short_preserves_output_firewall(self):
        compressed = gzip.compress(fits_bytes())
        self.assertLess(len(compressed), 65536)
        ledger = self.ledger()
        transport = MemoryTransport([self.head_response("ROOT_SUMMARY", length=len(compressed)),
                                     self.eof_response("ROOT_SUMMARY", 0, len(compressed), body=compressed)])
        contract, evidence = ProbeEngine(transport, ledger).fits_contract("ROOT_SUMMARY")
        exported = canonical({"contract": contract.as_dict(), "evidence": evidence.as_dict()})
        self.assertNotIn(CANARY, exported)
        self.assertEqual(evidence.uncompressed_header_bytes_emitted, 5760)

    def test_c23_eof_short_accounting_uses_actual_received_bytes(self):
        ledger = self.ledger()
        engine = ProbeEngine(MemoryTransport([self.eof_response("ROOT_SUMMARY", 0, 40000)]), ledger)
        engine.range_get("ROOT_SUMMARY", 0)
        self.assertEqual(ledger.count("http_body_bytes"), 40000)
        self.assertEqual(ledger.count("fits_body_bytes"), 40000)
        self.assertEqual(ledger.summary()["requests"][0]["actual"], 40000)

    def test_c24_unused_reservation_is_not_request_credit(self):
        ledger = self.ledger()
        transport = MemoryTransport([self.eof_response("ROOT_SUMMARY", 0, 40000)])
        engine = ProbeEngine(transport, ledger)
        engine.range_get("ROOT_SUMMARY", 0)
        self.code("PROBE_REPRESENTATION_EOF_BEFORE_HEADER_COMPLETE",
                  lambda: engine.range_get("ROOT_SUMMARY", 1))
        self.assertEqual((ledger.count("requests"), ledger.count("fits_body_bytes")), (1, 40000))

    def test_c25_post_reservation_crash_retains_full_conservative_charge(self):
        ledger = self.ledger()
        identity = RequestIdentity("ROOT_SUMMARY", RESOURCES["ROOT_SUMMARY"].url, "GET", RANGES[0])
        with self.assertRaises(OSError):
            ledger.reserve(identity, 65536, fault="after_commit")
        self.assertEqual(ledger.recover(), 1)
        self.assertEqual(ledger.count("fits_body_bytes"), 65536)
        self.assertEqual(ledger.summary()["requests"][0]["state"], "CRASH_CHARGED")

    def test_c26_range_200_behavior_unchanged(self):
        ledger = self.ledger()
        response = self.eof_response("ROOT_SUMMARY", 0, 40000, status=200)
        self.code("PROBE_RANGE_UNAVAILABLE_STOP",
                  lambda: ProbeEngine(MemoryTransport([response]), ledger).range_get("ROOT_SUMMARY", 0))
        self.assertEqual(response.position, 0)

    def test_c27_range_416_behavior_unchanged(self):
        ledger = self.ledger()
        response = self.eof_response("ROOT_SUMMARY", 0, 40000, status=416)
        self.code("PROBE_RANGE_UNAVAILABLE_STOP",
                  lambda: ProbeEngine(MemoryTransport([response]), ledger).range_get("ROOT_SUMMARY", 0))
        self.assertEqual(response.position, 0)

    def test_c28_terminal_precedence_unchanged_with_eof_event(self):
        events = ["PROBE_REPRESENTATION_EOF_BEFORE_HEADER_COMPLETE",
                  "PROBE_RANGE_UNAVAILABLE_STOP", "PROBE_TRANSPORT_INTEGRITY_FAILURE",
                  "PROBE_ROW_OBSERVATION_FORBIDDEN"]
        self.assertEqual(terminal_outcome(events), "PROBE_ROW_OBSERVATION_INTEGRITY_FAILURE")

    def test_c29_exact_second_range_eof_edge_is_full(self):
        ledger = self.ledger()
        transport = MemoryTransport([self.eof_response("ROOT_SUMMARY", 0, 131072),
                                     self.eof_response("ROOT_SUMMARY", 1, 131072)])
        engine = ProbeEngine(transport, ledger)
        self.assertEqual(len(engine.range_get("ROOT_SUMMARY", 0)), 65536)
        self.assertEqual(len(engine.range_get("ROOT_SUMMARY", 1)), 65536)

    def test_c30_binding_identity_includes_clarification(self):
        identity = RequestIdentity("ROOT_SUMMARY", RESOURCES["ROOT_SUMMARY"].url, "HEAD", None)
        self.assertEqual(identity.clarification_001_sha256, PROBE_CLARIFICATION_001_SHA256)
        self.assertEqual(binding().as_dict()["clarification_001_sha256"], PROBE_CLARIFICATION_001_SHA256)

    def test_c31_identity_drift_between_range_responses_rejected(self):
        ledger = self.ledger()
        transport = MemoryTransport([
            self.eof_response("ROOT_SUMMARY", 0, 90000, etag='"v1"'),
            self.eof_response("ROOT_SUMMARY", 1, 90000, etag='"v2"'),
        ])
        engine = ProbeEngine(transport, ledger)
        engine.range_get("ROOT_SUMMARY", 0)
        self.code("PROBE_TRANSPORT_INTEGRITY_FAILURE", lambda: engine.range_get("ROOT_SUMMARY", 1))
