from copy import deepcopy
from datetime import datetime, timezone
import unittest

from router import (
    RouteHeld, Skill, append_event, apply_learning, authorize_effect,
    authorize_invocation, budget_gate, fallback, reconcile, repair, route,
    validate_handoff, verify_event_chain,
)


NOW = datetime(2026, 8, 9, tzinfo=timezone.utc)
POLICY = "policy-v1"


def skill(skill_id, capabilities, **kwargs):
    return Skill(skill_id, "1.0.0", f"digest-{skill_id}", frozenset(capabilities), **kwargs)


class RouterFIT(unittest.TestCase):
    def setUp(self):
        self.request = {
            "request_id": "req-1", "risk_tier": "R1",
            "required_capabilities": ["draft", "validate"],
            "explicit_skill_priorities": [], "permitted_effects": [],
        }
        self.skills = [
            skill("draft", {"draft"}),
            skill("validate", {"validate"}),
            skill("combo", {"draft", "validate"}, qualification=2),
        ]

    def test_fit_101_named_skill_priority_without_authority_bypass(self):
        req = deepcopy(self.request); req["explicit_skill_priorities"] = ["draft"]
        plan = route(req, self.skills, POLICY, NOW)
        self.assertIn("draft", plan.order)
        self.assertFalse(plan.invocation_warrants)

    def test_fit_102_unavailable_named_skill_fails_safely(self):
        req = deepcopy(self.request); req["explicit_skill_priorities"] = ["revoked"]
        skills = [skill("revoked", {"draft", "validate"}, status="REVOKED")]
        with self.assertRaises(RouteHeld): route(req, skills, POLICY, NOW)

    def test_fit_103_frozen_inputs_reproduce_route(self):
        a = route(self.request, self.skills, POLICY, NOW)
        b = route(self.request, list(reversed(self.skills)), POLICY, NOW)
        self.assertEqual((a.route_id, a.order), (b.route_id, b.order))

    def test_fit_104_redundant_skill_excluded(self):
        plan = route(self.request, self.skills, POLICY, NOW)
        self.assertEqual(plan.order, ["combo"])
        self.assertEqual(plan.rejected["draft"], "NOT_MINIMUM_SUFFICIENT")

    def test_fit_105_missing_capability_blocks(self):
        req = deepcopy(self.request); req["required_capabilities"].append("security")
        with self.assertRaises(RouteHeld): route(req, self.skills, POLICY, NOW)

    def test_fit_106_prerequisite_dag_and_handoff(self):
        skills = [skill("prep", {"prepare"}), skill("build", {"draft", "validate"}, prerequisites=("prep",))]
        plan = route(self.request, skills, POLICY, NOW)
        self.assertEqual(plan.order, ["prep", "build"])
        validate_handoff({"schema_id":"draft-v1", "validation_status":"PASS", "data_classification":"internal", "taint":[]}, "draft-v1", {"internal"})

    def test_fit_107_cycle_fails_closed(self):
        skills = [skill("a", {"draft"}, prerequisites=("b",)), skill("b", {"validate"}, prerequisites=("a",))]
        with self.assertRaises(RouteHeld): route(self.request, skills, POLICY, NOW)

    def test_fit_108_changed_digest_invalidates_route(self):
        plan = route(self.request, self.skills, POLICY, NOW)
        changed = list(self.skills); changed[2] = skill("combo", {"draft", "validate"})
        changed[2] = Skill(**{**changed[2].__dict__, "digest": "changed"})
        with self.assertRaises(RouteHeld): authorize_invocation(plan, "combo", request=self.request, skills=changed, policy_hash=POLICY)

    def test_fit_109_risk_ceiling_blocks(self):
        req = deepcopy(self.request); req["risk_tier"] = "R2"
        with self.assertRaises(RouteHeld): route(req, self.skills, POLICY, NOW)

    def test_fit_110_selection_does_not_authorize_effect(self):
        req = deepcopy(self.request); req["permitted_effects"] = ["write_file"]
        skills = [skill("writer", {"draft", "validate"}, effects=frozenset({"write_file"}))]
        plan = route(req, skills, POLICY, NOW)
        with self.assertRaises(RouteHeld): authorize_effect(plan, "writer", "write_file", confirmation=True)

    def test_fit_111_high_impact_requires_separate_confirmation(self):
        req = deepcopy(self.request); req["permitted_effects"] = ["publish"]
        skills = [skill("publisher", {"draft", "validate"}, effects=frozenset({"publish"}))]
        plan = route(req, skills, POLICY, NOW)
        authorize_invocation(plan, "publisher", request=req, skills=skills, policy_hash=POLICY)
        with self.assertRaises(RouteHeld): authorize_effect(plan, "publisher", "publish", confirmation=False)
        self.assertTrue(authorize_effect(plan, "publisher", "publish", confirmation=True))

    def test_fit_112_untrusted_output_not_instruction(self):
        handoff = {"schema_id":"x", "validation_status":"PASS", "data_classification":"internal", "taint":["untrusted_instruction"]}
        with self.assertRaises(RouteHeld): validate_handoff(handoff, "x", {"internal"})

    def test_fit_113_missing_instruction_resource_blocks(self):
        skills = [skill("build", {"draft", "validate"}, prerequisites=("instruction",))]
        with self.assertRaises(RouteHeld): route(self.request, skills, POLICY, NOW)

    def test_fit_114_handoff_mismatch_blocks(self):
        handoff = {"schema_id":"old", "validation_status":"PASS", "data_classification":"internal", "taint":[]}
        with self.assertRaises(RouteHeld): validate_handoff(handoff, "new", {"internal"})

    def test_fit_115_repair_cannot_weaken_acceptance(self):
        with self.assertRaises(RouteHeld): repair("baseline", "weaker", 0, 2)
        self.assertEqual(repair("baseline", "baseline", 0, 2), "REPAIRING")

    def test_fit_116_unknown_outcome_reconciles(self):
        with self.assertRaises(RouteHeld): reconcile("OUTCOME_UNKNOWN", None)
        self.assertEqual(reconcile("OUTCOME_UNKNOWN", "SUCCEEDED"), "SUCCEEDED")

    def test_fit_117_fallback_preserves_floors(self):
        floors = {"risk":2, "authority":2, "validation":2, "data":2}
        weaker = dict(floors); weaker["validation"] = 1
        with self.assertRaises(RouteHeld): fallback(floors, weaker)
        self.assertEqual(fallback(floors, floors), 2)

    def test_fit_118_budget_exhaustion_holds_except_containment(self):
        self.assertEqual(budget_gate(10, 10), "HELD")
        self.assertEqual(budget_gate(10, 10, containment=True), "CONTAINMENT_ONLY")

    def test_fit_119_evidence_reconstructs_and_detects_tamper(self):
        chain = []; append_event(chain, "CLASSIFIED", {"request":"req-1"}); append_event(chain, "PLANNED", {"skills":["combo"]})
        self.assertTrue(verify_event_chain(chain))
        chain[0]["payload_digest"] = "tampered"
        self.assertFalse(verify_event_chain(chain))

    def test_fit_120_learning_cannot_self_admit(self):
        registry = list(self.skills); before = deepcopy(registry)
        self.assertEqual(apply_learning(registry, {"success": True}), "CANDIDATE_OBSERVATION")
        self.assertEqual(registry, before)


if __name__ == "__main__":
    unittest.main(verbosity=2)

