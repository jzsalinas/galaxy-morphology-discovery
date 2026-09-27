#!/usr/bin/env python3
"""Full offline regression with exact Run-005 preparation substitutions."""
from __future__ import annotations

import json
from pathlib import Path
import socket
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

OC3 = Path(__file__).resolve().parents[2]
PROJECT = OC3.parent
sys.path.insert(0, str(OC3))

from recovery_tests.source_metadata.run003_active_socket_firewalled_regression import (
    ActiveRun003LifecycleTests,
    REPLACED_PREAUTHORIZATION_TESTS,
    _flatten,
    _forbidden,
)


RUN_003_CLOSED_BASE_COMMIT = "260abd2ab49977453176b939f07803aad0772b65"
REQUIRED_UNTRACKED_HISTORICAL_INPUTS = {"OC3_DEVELOPMENT_BRICKS.csv"}
HISTORICAL_INPUT_TRIPWIRE = (
    "test_physical_contract_probe.ManifestContractTripwireOutcomeTests."
    "test_88_no_production_directories_mutated"
)
RUN_004_INPUT_ADDITIONS = {
    "OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_MANDATE_004.json",
    "OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_POLICY_CORE_MANIFEST_004.json",
    "OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_RUN_003_CLOSURE_001.json",
    "OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_RUN_004_CLOSURE_001.json",
    "OC3_SOURCE_METADATA_RECOVERY_ACTION_REGISTRY_004.json",
    "OC3_SOURCE_METADATA_RECOVERY_FIRST_CANDIDATE_004.json",
    "OC3_SOURCE_METADATA_RECOVERY_FIRST_CANDIDATE_VALIDATION_004.json",
    "OC3_SOURCE_METADATA_RUN_004_DRIFT_MATRIX_001.json",
    "OC3_SOURCE_METADATA_RUN_004_INHERITED_TEST_RECEIPTS_001.json",
    "OC3_SOURCE_METADATA_RUN_004_INHERITED_TRANSPORT_AUTHORITY_001.json",
    "OC3_SOURCE_METADATA_RUN_004_INHERITED_TRANSPORT_CONTRACT_001.json",
    "OC3_SOURCE_METADATA_RUN_004_TRANSPORT_BOOTSTRAP_001.json",
}
RUN_005_INPUT_ADDITIONS = {
    "OC3_MANUAL_SOURCE_METADATA_ACQUISITION_BINDING_001.json",
    "OC3_SOURCE_METADATA_AUTONOMOUS_RECOVERY_POLICY_CORE_MANIFEST_005.json",
    "OC3_SOURCE_METADATA_RUN_005_DRIFT_MATRIX_001.json",
}
RUN_004_PREAUTHORIZATION_TESTS_NOW_HISTORICAL = {
    "test_source_metadata_recovery_run004_preparation.Run004PreparationTests.test_003_waiting_state_is_inactive_and_fresh",
    "test_source_metadata_recovery_run004_preparation.Run004PreparationTests.test_004_no_final_authorization_exists",
    "test_source_metadata_recovery_run004_preparation.Run004PreparationTests.test_005_no_run004_runtime_namespace_exists",
}
REPLACED_TESTS = REPLACED_PREAUTHORIZATION_TESTS | RUN_004_PREAUTHORIZATION_TESTS_NOW_HISTORICAL | {HISTORICAL_INPUT_TRIPWIRE}


def _closed_base_input_names() -> set[str]:
    result = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", RUN_003_CLOSED_BASE_COMMIT, "oc3/INPUTS"],
        cwd=PROJECT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError("RUN_003_CLOSED_BASE_COMMIT_UNAVAILABLE")
    prefix = "oc3/INPUTS/"
    names = {
        line[len(prefix):]
        for line in result.stdout.splitlines()
        if line.startswith(prefix) and "/" not in line[len(prefix):]
    }
    if not names:
        raise RuntimeError("RUN_003_CLOSED_BASE_INPUTS_UNAVAILABLE")
    return names


class Run005LifecycleTripwireTests(unittest.TestCase):
    def test_run005_package_is_inactive_and_run004_is_closed(self):
        from oc3lib.source_metadata_run005_preparation import validate_package
        values = validate_package()
        self.assertEqual(values["state"]["execution_status"], "NOT_STARTED")
        self.assertFalse(values["state"]["authorized"])
        self.assertEqual(values["closure"]["stop_reason"], "CONSUMED_ACTION_WITHOUT_TERMINAL_REPLAY_FORBIDDEN")
        self.assertEqual(values["closure"]["authorization"]["sha256"], "d6c9daae4ed052d24f413102e1a14e2428a05992030ba1d3be371a0c2abdc125")

    def test_exact_run005_input_additions_and_other_production_tripwires(self):
        baseline = _closed_base_input_names() | REQUIRED_UNTRACKED_HISTORICAL_INPUTS
        current = {item.name for item in (PROJECT / "oc3/INPUTS").iterdir()}
        additions = RUN_004_INPUT_ADDITIONS | RUN_005_INPUT_ADDITIONS
        self.assertEqual(current - baseline, additions)
        self.assertEqual(current, baseline | additions)

        technical_names = {
            item.name for item in (PROJECT / "oc3/TECHNICAL_INDEX").iterdir()
        }
        technical_base = {
            "OC3_LOCATIONS.json",
            "OC3_SELECTION_FLOW.csv",
            "OC3_PSF_IDENTITIES.json",
        }
        self.assertIn(
            technical_names,
            (technical_base, technical_base | {"OC3_NATIVE_EXTRACTION_MANIFEST.json"}),
        )
        for relative in ("oc3/provenance", "oc3/RAW_IMMUTABLE", "oc3/reports"):
            self.assertFalse(any((PROJECT / relative).iterdir()))


def main() -> int:
    start = time.monotonic()
    discovered = unittest.defaultTestLoader.discover(str(OC3 / "tests"), pattern="test_*.py")
    discovered_ids = {test.id() for test in _flatten(discovered)}
    observed_replacements = discovered_ids & REPLACED_TESTS
    if observed_replacements != REPLACED_TESTS:
        raise RuntimeError("RUN_004_LIFECYCLE_TEST_IDENTITY_DRIFT")
    retained = [test for test in _flatten(discovered) if test.id() not in REPLACED_TESTS]
    suite = unittest.TestSuite(retained)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(ActiveRun003LifecycleTests))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(Run005LifecycleTripwireTests))
    with patch.object(socket, "socket", _forbidden), \
            patch.object(socket, "create_connection", _forbidden), \
            patch.object(socket, "getaddrinfo", _forbidden), \
            patch.object(socket, "gethostbyname", _forbidden), \
            patch.object(socket, "gethostbyname_ex", _forbidden), \
            patch.object(socket, "gethostbyaddr", _forbidden), \
            patch.object(socket, "getnameinfo", _forbidden), \
            patch.object(socket, "getfqdn", _forbidden):
        result = unittest.TextTestRunner(verbosity=2).run(suite)
    summary = {
        "failed": len(result.errors) + len(result.failures),
        "passed": result.testsRun - len(result.errors) - len(result.failures) - len(result.skipped),
        "real_network_requests": 0,
        "replaced_lifecycle_assertions": len(REPLACED_TESTS),
        "run_003_closed_base_commit": RUN_003_CLOSED_BASE_COMMIT,
        "run_005_exact_input_additions": len(RUN_004_INPUT_ADDITIONS | RUN_005_INPUT_ADDITIONS),
        "seconds": round(time.monotonic() - start, 3),
        "skipped": len(result.skipped),
        "synthetic_only": True,
        "tests": result.testsRun,
    }
    print(json.dumps(summary, sort_keys=True))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
