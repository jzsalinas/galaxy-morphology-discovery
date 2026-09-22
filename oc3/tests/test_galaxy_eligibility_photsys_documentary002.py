"""Offline tests for the distinct PHOTSYS documentary attempt 002."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import oc3_galaxy_eligibility_photsys_documentary002 as cli
from oc3lib.core import implementation_hash
import oc3lib.galaxy_eligibility_photsys_authority_probe as original
import oc3lib.galaxy_eligibility_photsys_documentary002 as stage


TARGET_URL = stage.DIRECTORY_URL + original.TARGET_FILENAME


def historical_documents(body0: bytes | None = None):
    bodies = [path.read_bytes() for path in stage.HISTORICAL_BODY_PATHS]
    if body0 is not None:
        bodies[0] = body0
    return [{"source_url": url, "body": body} for url, body in zip(
        original.DOCUMENTARY_ALLOWLIST, bodies)]


def directory_html(href: str | None, *, plain: bool = False) -> bytes:
    target = original.TARGET_FILENAME
    if plain:
        return f"<html><body>{target}</body></html>".encode()
    link = "" if href is None else f'<a href="{href}">{target}</a>'
    return f"<html><body>{link}</body></html>".encode()


def alter_target_photsys_type(body: bytes) -> bytes:
    """Alter only the PHOTSYS type inside the exact target product section."""
    start = body.index(b'<section id="survey-bricks-dr9-randoms-0-48-0-fits">')
    end = body.index(b"</section>", start)
    target = body[start:end]
    altered = target.replace(b"<td><p>char[1]</p></td>", b"<td><p>char[2]</p></td>", 1)
    if altered == target:
        raise AssertionError("frozen PHOTSYS table row was not found")
    return body[:start] + altered + body[end:]


class ParserCorrectionTests(unittest.TestCase):
    def test_01_preserved_real_bodies_fix_both_false_negatives(self):
        facts = original.documentary_facts(historical_documents())
        self.assertTrue(facts["brick_level_row_model_documented"])
        self.assertTrue(facts["photsys_exact_values_documented"])

    def test_02_product_structure_is_required_not_generic_text(self):
        body = stage.HISTORICAL_BODY_PATHS[0].read_bytes()
        changed = body.replace(b'<section id="survey-bricks-dr9-randoms-0-48-0-fits">',
                               b'<section id="unrelated-similar-file">', 1)
        facts = original.documentary_facts(historical_documents(changed))
        self.assertFalse(facts["brick_level_row_model_documented"])
        self.assertFalse(facts["photsys_exact_values_documented"])

    def test_03_exact_photsys_table_row_is_required(self):
        body = stage.HISTORICAL_BODY_PATHS[0].read_bytes()
        changed = alter_target_photsys_type(body)
        facts = original.documentary_facts(historical_documents(changed))
        self.assertTrue(facts["brick_level_row_model_documented"])
        self.assertFalse(facts["photsys_exact_values_documented"])

    def test_04_similarly_worded_paragraph_does_not_replace_table(self):
        body = stage.HISTORICAL_BODY_PATHS[0].read_bytes()
        changed = alter_target_photsys_type(body)
        changed += (b'<p>PHOTSYS char[1] "N", "S" or " " for bricks resolved to be '
                    b'"officially" in the north, south, or outside of the footprint, respectively.</p>')
        self.assertFalse(original.documentary_facts(historical_documents(changed))[
            "photsys_exact_values_documented"])

    def test_05_corrected_evidence_binds_immutable_hashes(self):
        evidence = stage.corrected_historical_parse()
        self.assertEqual(evidence["historical_body_sha256"], list(stage.HISTORICAL_BODY_HASHES))
        self.assertEqual(evidence["network_requests"], 0)
        self.assertEqual(evidence["parser_version"], "OC3_PHOTSYS_DOCUMENTARY_PARSER_V2")


class LiteralHrefTests(unittest.TestCase):
    def test_10_exact_relative_href_accepted(self):
        raw, resolved = stage.resolve_directory_href(directory_html(original.TARGET_FILENAME))
        self.assertEqual((raw, resolved), (original.TARGET_FILENAME, TARGET_URL))

    def test_11_exact_absolute_href_accepted(self):
        self.assertEqual(stage.resolve_directory_href(directory_html(TARGET_URL))[1], TARGET_URL)

    def test_12_plain_text_rejected(self):
        with self.assertRaises(original.PHOTSYSProbeError):
            stage.resolve_directory_href(directory_html(None, plain=True))

    def test_13_constructed_url_not_accepted(self):
        body = f'<a href="{stage.DIRECTORY_URL}">directory</a>{original.TARGET_FILENAME}'.encode()
        with self.assertRaises(original.PHOTSYSProbeError): stage.resolve_directory_href(body)

    def test_14_wrong_host_rejected(self):
        with self.assertRaises(original.PHOTSYSProbeError):
            stage.resolve_directory_href(directory_html("https://example.org/" + original.TARGET_FILENAME))

    def test_15_wrong_directory_rejected(self):
        wrong = "https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/north/" + original.TARGET_FILENAME
        with self.assertRaises(original.PHOTSYSProbeError): stage.resolve_directory_href(directory_html(wrong))

    def test_16_wrong_version_and_similar_names_rejected(self):
        for name in ("survey-bricks-dr9-randoms-0.49.0.fits", "randoms-1-0.fits",
                     "randoms-allsky-1-0.fits", "randoms-outside-1-0.fits"):
            with self.assertRaises(original.PHOTSYSProbeError):
                stage.resolve_directory_href(directory_html(name))

    def test_17_query_and_fragment_rejected(self):
        for suffix in ("?download=1", "#file"):
            with self.assertRaises(original.PHOTSYSProbeError):
                stage.resolve_directory_href(directory_html(original.TARGET_FILENAME + suffix))

    def test_18_duplicate_exact_href_rejected(self):
        body = directory_html(original.TARGET_FILENAME) + directory_html(TARGET_URL)
        # Both hyperlinks resolve to the same (href, URL) only when their raw href
        # is equal. Distinct raw evidence is ambiguous and must stop.
        with self.assertRaises(original.PHOTSYSProbeError): stage.resolve_directory_href(body)


class BoundaryAndExecutionTests(unittest.TestCase):
    def test_20_distinct_attempt_and_exact_allowlist(self):
        self.assertNotEqual(stage.ATTEMPT_ID, stage.HISTORICAL_ATTEMPT_ID)
        self.assertEqual(stage.DIRECTORY_URL,
                         "https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/randoms/")
        self.assertEqual(stage.RESOURCE_ROLE, "OFFICIAL_DR9_RANDOMS_DIRECTORY_INDEX")

    def test_21_tight_stage_caps_and_no_fits_capability(self):
        self.assertEqual((stage.REQUEST_CAP, stage.BODY_CAP, stage.REDIRECT_CAP), (2, 262144, 1))
        self.assertFalse(hasattr(stage.DirectoryTransport, "head"))
        self.assertFalse(hasattr(stage.DirectoryTransport, "range"))
        self.assertFalse(hasattr(stage.DirectoryTransport, "get_fits"))

    def test_22_historical_attempt_is_hash_valid_and_unchanged(self):
        value = stage.validate_historical_attempt()
        self.assertEqual(value["tree_seal"], stage.HISTORICAL_TREE_SEAL)
        self.assertEqual((value["requests"], value["body_bytes"]), (2, 257683))

    def test_23_input_validation_reuses_history_without_transport(self):
        with patch.object(stage, "DirectoryTransport", side_effect=AssertionError("transport")):
            result = stage.validate_inputs()
        self.assertEqual(result["network_requests"], 0)

    def test_24_candidate_has_one_resource_and_zero_fits_operations(self):
        command = ["python", "script"]
        candidate = stage.build_candidate(stage.file_sha256(stage.PARSE_EVIDENCE_PATH),
                                          implementation_hash(stage.PROJECT), command)
        self.assertEqual(candidate["new_documentary_resource"]["literal_url"], stage.DIRECTORY_URL)
        self.assertEqual(candidate["policy"]["logical_new_documentary_resources"], 1)
        self.assertTrue(all(value == 0 for value in candidate["negative_capabilities"].values()))

    def test_25_redirect_outside_allowlist_fails_before_second_transport(self):
        transport = object.__new__(stage.DirectoryTransport)
        transport.redirect_cap = 1; transport.timeout_seconds = 1
        class Response:
            status = 302
            def getheaders(self): return [("Location", "https://example.org/")]
        class Connection:
            def request(self, *args, **kwargs): pass
            def getresponse(self): return Response()
            def close(self): pass
        calls = []
        def factory(*args, **kwargs): calls.append(args); return Connection()
        with patch.object(stage.http.client, "HTTPSConnection", side_effect=factory), \
                self.assertRaises(original.PHOTSYSProbeError) as caught:
            transport.get(stage.DIRECTORY_URL, max_body_bytes=stage.BODY_CAP)
        self.assertEqual(caught.exception.code, "DOCUMENTARY_002_REDIRECT_OUTSIDE_ALLOWLIST")
        self.assertEqual(len(calls), 1)

    def test_26_synthetic_success_decodes_no_cells_and_requests_no_fits(self):
        command = ["synthetic"]
        candidate_value = stage.build_candidate(stage.file_sha256(stage.PARSE_EVIDENCE_PATH),
                                                implementation_hash(stage.PROJECT), command)
        class Transport:
            calls = []
            def __init__(self, **kwargs): self.kwargs = kwargs
            def get(self, url, *, max_body_bytes):
                self.calls.append((url, max_body_bytes))
                body = directory_html(original.TARGET_FILENAME)
                return {"body": body, "final_url": stage.DIRECTORY_URL,
                        "headers": {"content-length": str(len(body))},
                        "requests_started": 1, "status": 200}
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp); candidate = base / "candidate.json"; auth = base / "auth.json"
            stage.write_json_immutable(candidate, candidate_value)
            argv_hash = original.sha256_bytes(original.canonical(command))
            stage.write_json_immutable(auth, {
                "authorization_id": "synthetic", "authorization_state": "FINAL_HUMAN_AUTHORIZATION",
                "authorized": True, "candidate_sha256": stage.file_sha256(candidate),
                "command_argv_sha256": argv_hash, "scope": original.SCOPE,
                "stage_id": stage.ATTEMPT_ID})
            result = stage.execute(candidate, auth, argv_hash, base / "out", transport_factory=Transport)
            accounting = stage.load_canonical_json(
                base / "out/OC3_PHOTSYS_DOCUMENTARY_002_RESOURCE_ACCOUNTING.json")
            terminal = stage.load_canonical_json(base / "out/OC3_PHOTSYS_DOCUMENTARY_002_TERMINAL.json")
        self.assertEqual(result["state"], stage.SUCCESS)
        self.assertEqual(result["literal_official_url"], TARGET_URL)
        self.assertEqual(Transport.calls, [(stage.DIRECTORY_URL, stage.BODY_CAP)])
        self.assertEqual((accounting["data_head_requests"], accounting["data_range_requests"],
                          accounting["full_fits_gets"]), (0, 0, 0))
        self.assertEqual(terminal["table_cell_values_decoded"], 0)

    def test_27_previous_evidence_still_immutable_after_synthetic_execution(self):
        self.assertEqual(stage.validate_historical_attempt()["tree_seal"], stage.HISTORICAL_TREE_SEAL)

    def test_28_cli_modes_are_closed(self):
        options = {option for action in cli.parser()._actions for option in action.option_strings}
        self.assertTrue({"--help", "--validate-inputs", "--dry-run",
                         "--probe-documentary-002"}.issubset(options))

    def test_29_partial_failure_terminal_is_canonical_and_zero_fits(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "attempt"
            stage.persist_failure_terminal(output, "SYNTHETIC_FAILURE")
            accounting = stage.load_canonical_json(
                output / "OC3_PHOTSYS_DOCUMENTARY_002_RESOURCE_ACCOUNTING.json")
            terminal = stage.load_canonical_json(
                output / "OC3_PHOTSYS_DOCUMENTARY_002_TERMINAL.json")
            stage.validate_sealed(accounting); stage.validate_sealed(terminal)
        self.assertEqual(terminal["state"], stage.FAILED)
        self.assertEqual(terminal["table_cell_values_decoded"], 0)
        self.assertEqual((accounting["data_head_requests"], accounting["data_range_requests"],
                          accounting["full_fits_gets"]), (0, 0, 0))


if __name__ == "__main__":
    unittest.main()
