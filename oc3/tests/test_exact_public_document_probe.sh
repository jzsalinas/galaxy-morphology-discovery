#!/usr/bin/env python3
"""Focused offline tests for the exact public-document probe."""
from importlib.machinery import SourceFileLoader
from pathlib import Path
import tempfile
import unittest

PROJECT = Path(__file__).resolve().parents[2]
module = SourceFileLoader("public_document_probe", str(PROJECT / "oc3/oc3_exact_public_document_probe.sh")).load_module()


class Tests(unittest.TestCase):
    def test_analysis_records_terms_and_closed_links(self):
        body = (b'<html><head><meta name="citation_title" content="Title">'
                b'<meta name="citation_doi" content="10.1/x"></head><body>'
                b'PHOTSYS outside of the footprint '
                b'<a href="https://doi.org/10.1/x">doi</a>'
                b'<a href="https://example.invalid/not-admitted">other</a></body></html>')
        result = module.analyze_html(body)
        self.assertEqual(result["term_counts"]["photsys"], 1)
        self.assertEqual(result["term_counts"]["outside of the footprint"], 1)
        self.assertEqual(result["discovered_candidate_links"], ["https://doi.org/10.1/x"])

    def test_invalid_utf8_fails_closed(self):
        with self.assertRaises(module.ProbeError):
            module.analyze_html(b"\xff")


if __name__ == "__main__":
    unittest.main()
