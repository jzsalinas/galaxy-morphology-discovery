#!/usr/bin/env python3
"""Focused synthetic tests for the exact Git-object action implementation."""
from importlib.machinery import SourceFileLoader
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[2]
stage = SourceFileLoader("git_object_probe", str(ROOT / "oc3/oc3_exact_github_git_object_probe.sh")).load_module()


class GitObjectProbeTests(unittest.TestCase):
    def test_commit_object_exact(self):
        body = json.dumps({"sha": stage.COMMIT, "tree": {"sha": "1" * 40}}).encode()
        self.assertEqual(stage.validate_body("COMMIT_OBJECT", body, stage.COMMIT),
                         {"commit_sha": stage.COMMIT, "root_tree_sha": "1" * 40})

    def test_commit_mismatch_refused(self):
        body = json.dumps({"sha": "0" * 40, "tree": {"sha": "1" * 40}}).encode()
        with self.assertRaises(stage.ProbeError):
            stage.validate_body("COMMIT_OBJECT", body, stage.COMMIT)

    def test_tree_requires_complete_nonempty_inventory(self):
        sha = "2" * 40
        body = json.dumps({"sha": sha, "truncated": False,
                           "tree": [{"path": "py/desitarget/randoms.py", "type": "blob", "sha": "3" * 40}]}).encode()
        self.assertEqual(stage.validate_body("RECURSIVE_TREE", body, sha)["entry_count"], 1)
        for changed in ({"sha": sha, "truncated": True, "tree": []},
                        {"sha": sha, "truncated": False, "tree": []}):
            with self.assertRaises(stage.ProbeError):
                stage.validate_body("RECURSIVE_TREE", json.dumps(changed).encode(), sha)

    def test_no_network_during_import(self):
        self.assertEqual(stage.FIREWALL["astronomical_data_GETs"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
