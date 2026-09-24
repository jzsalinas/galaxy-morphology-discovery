from __future__ import annotations

import unittest

import oc3_observational_multiplicity_grouping_gate as action
from oc3lib.observational_multiplicity import load_canonical_json
from oc3lib.observational_multiplicity_grouping_gate_validation import (
    CANDIDATE, expected_command_argv, validate_candidate,
)


class GroupingGateActionTests(unittest.TestCase):
    def test_01_candidate_and_exact_runtime_command_validate_offline(self):
        result = validate_candidate()
        self.assertEqual(result["state"], "GROUPING_GATE_CANDIDATE_VALIDATED")
        self.assertEqual((result["assessment_executions"], result["summary_value_reads"],
                          result["network_requests"]), (0, 0, 0))
        command = expected_command_argv()
        action.validate_runtime_invocation(load_canonical_json(CANDIDATE),
                                           executable=command[0], script_path=command[1],
                                           argument_vector=command[2:])

    def test_02_runtime_mutation_fails_before_material_action(self):
        command = expected_command_argv()
        mutated = list(command)
        mutated[-1] += ".changed"
        with self.assertRaises(action.RuntimeCommandBindingError):
            action.validate_runtime_invocation(load_canonical_json(CANDIDATE),
                                               executable=mutated[0], script_path=mutated[1],
                                               argument_vector=mutated[2:])

    def test_03_selection_view_and_split_guards_are_synthetic(self):
        self.assertEqual(action._prove_selection_and_split_guards(), {
            "confirmatory_split_blocked_without_group": True,
            "global_identity_selected_once": True,
            "observer_domain_excluded_from_selection": True,
            "observer_domain_roles_closed": True,
            "same_group_cross_split_rejected": True,
            "valid_views_retained_after_selection": True,
        })

    def test_04_candidate_reserves_zero_material_resources(self):
        candidate = load_canonical_json(CANDIDATE)
        contract = candidate["autonomy_policy"]
        self.assertEqual((contract["network_request_reservation"],
                          contract["application_body_reservation"],
                          contract["retry_reservation"]), (0, 0, 0))
        self.assertEqual(set(contract["scientific_firewall"].values()), {0})


if __name__ == "__main__":
    unittest.main()
