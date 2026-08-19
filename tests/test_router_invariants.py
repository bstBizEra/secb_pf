"""Fail-closed invariants of secb_router, the only product code in the tree.

src/secb_router/router.py implements, in 299 lines, most of what the production mandate's §2 asks
SecB to demonstrate: verify authority before execution (authorize_invocation), gate high-impact
effects (authorize_effect), preserve handoffs (validate_handoff), refuse to fabricate closure
(reconcile), enforce budgets (budget_gate) and keep durable history (append_event /
verify_event_chain).

It had four tests, all about registry hashing. Everything below was unpinned, so a regression in any
refusal path would have been silent.

WHAT THIS FILE DOES AND DOES NOT DO. It pins the properties that hold. It does NOT encode the gaps
found while writing it as expected behaviour -- a test asserting that a HELD route can be
re-authorized would make a defect the specification. Those are filed instead; see the router
invariants issue. The distinction matters:

    PINNING_A_CORRECT_PROPERTY != FREEZING_CURRENT_BEHAVIOUR
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from secb_router.router import (  # noqa: E402
    HIGH_IMPACT_EFFECTS, RoutePlan, RouteHeld, Skill, append_event, authorize_effect,
    authorize_invocation, budget_gate, canonical_hash, reconcile, registry_hash, repair,
    validate_handoff, verify_event_chain,
)


def skill(**over) -> Skill:
    base = dict(skill_id="s1", version="1", digest="d1",
                capabilities=frozenset({"cap"}), effects=frozenset({"read", "delete"}))
    base.update(over)
    return Skill(**base)


def plan_for(request: dict, skills: list[Skill], policy_hash: str = "p1", **over) -> RoutePlan:
    base = dict(route_id="r1", request_hash=canonical_hash(request),
                registry_hash=registry_hash(skills), policy_hash=policy_hash,
                selected=list(skills), rejected={}, order=[s.skill_id for s in skills])
    base.update(over)
    return RoutePlan(**base)


# --- authority is re-verified at invocation, not trusted from planning -------


@pytest.mark.parametrize("mutation,reason", [
    ("request", "request changed"),
    ("registry", "registry or instruction digest changed"),
    ("policy", "policy changed"),
])
def test_invocation_is_refused_when_the_bound_subject_changed(mutation, reason):
    # A plan authorizes a specific request against a specific registry under a specific policy.
    # If any of the three moved between planning and invocation, the plan describes a different
    # decision -- the same distinction the shadow queue draws for a base that moved.
    request = {"goal": "x"}
    skills = [skill()]
    plan = plan_for(request, skills)
    args = dict(request=request, skills=skills, policy_hash="p1")
    if mutation == "request":
        args["request"] = {"goal": "y"}
    elif mutation == "registry":
        args["skills"] = [skill(digest="TAMPERED")]
    else:
        args["policy_hash"] = "p2"
    with pytest.raises(RouteHeld, match=reason):
        authorize_invocation(plan, "s1", **args)


def test_a_skill_outside_the_plan_cannot_be_invoked():
    request = {"goal": "x"}
    skills = [skill()]
    with pytest.raises(RouteHeld, match="skill not selected"):
        authorize_invocation(plan_for(request, skills), "not-in-plan",
                             request=request, skills=skills, policy_hash="p1")


# --- effects need their own warrant, and high-impact ones need confirmation --


def test_an_effect_cannot_be_applied_without_an_invocation_warrant():
    request = {"goal": "x"}
    skills = [skill()]
    with pytest.raises(RouteHeld, match="invocation not authorized"):
        authorize_effect(plan_for(request, skills), "s1", "read", confirmation=True)


def test_an_effect_outside_the_skill_contract_is_refused():
    request = {"goal": "x"}
    skills = [skill(effects=frozenset({"read"}))]
    plan = plan_for(request, skills)
    authorize_invocation(plan, "s1", request=request, skills=skills, policy_hash="p1")
    with pytest.raises(RouteHeld, match="effect outside skill contract"):
        authorize_effect(plan, "s1", "delete", confirmation=True)


@pytest.mark.parametrize("effect", sorted(HIGH_IMPACT_EFFECTS))
def test_every_high_impact_effect_requires_separate_confirmation(effect):
    # Parametrized over the real set rather than a sample: adding an effect to
    # HIGH_IMPACT_EFFECTS without a confirmation path should fail here, not in production.
    request = {"goal": "x"}
    skills = [skill(effects=frozenset({effect}))]
    plan = plan_for(request, skills)
    authorize_invocation(plan, "s1", request=request, skills=skills, policy_hash="p1")
    with pytest.raises(RouteHeld, match="separate effect confirmation required"):
        authorize_effect(plan, "s1", effect, confirmation=False)
    assert authorize_effect(plan, "s1", effect, confirmation=True)


# --- a handoff cannot smuggle instructions or leak classification -----------


@pytest.mark.parametrize("handoff,reason", [
    ({"schema_id": "wrong", "validation_status": "PASS", "data_classification": "INTERNAL"},
     "handoff schema mismatch"),
    ({"schema_id": "ok", "validation_status": "FAIL", "data_classification": "INTERNAL"},
     "handoff validation failed"),
    ({"schema_id": "ok", "validation_status": "PASS", "data_classification": "SECRET"},
     "handoff data classification prohibited"),
    ({"schema_id": "ok", "validation_status": "PASS", "data_classification": "INTERNAL",
      "taint": ["untrusted_instruction"]}, "untrusted output cannot become instruction"),
])
def test_handoff_refusals(handoff, reason):
    with pytest.raises(RouteHeld, match=reason):
        validate_handoff(handoff, "ok", {"INTERNAL", "PUBLIC"})


def test_a_handoff_missing_every_field_is_refused_not_defaulted():
    # An absent field must not read as an acceptable value.
    with pytest.raises(RouteHeld):
        validate_handoff({}, "ok", {"INTERNAL"})


# --- closure is never fabricated --------------------------------------------


@pytest.mark.parametrize("readback", [None, "", "PENDING", "succeeded", "SUCCESS", "unknown"])
def test_an_unknown_outcome_cannot_be_closed_without_an_exact_readback(readback):
    # Only the exact tokens SUCCEEDED and FAILED resolve an unknown outcome. Lowercase and
    # near-miss spellings are refused, so a typo cannot close a run that never reported.
    with pytest.raises(RouteHeld, match="outcome must be reconciled before retry"):
        reconcile("OUTCOME_UNKNOWN", readback)


@pytest.mark.parametrize("readback", ["SUCCEEDED", "FAILED"])
def test_an_exact_readback_resolves_the_unknown_outcome(readback):
    assert reconcile("OUTCOME_UNKNOWN", readback) == readback


def test_a_known_outcome_is_returned_unchanged_and_needs_no_readback():
    assert reconcile("SUCCEEDED", None) == "SUCCEEDED"


def test_repair_cannot_weaken_acceptance_criteria():
    with pytest.raises(RouteHeld, match="acceptance criteria weakening prohibited"):
        repair("hash-a", "hash-b", attempts=0, limit=3)


def test_repair_stops_at_its_budget_rather_than_at_one_past_it():
    assert repair("h", "h", attempts=2, limit=3) == "REPAIRING"
    with pytest.raises(RouteHeld, match="repair budget exhausted"):
        repair("h", "h", attempts=3, limit=3)


# --- the budget cap is a stop condition, not a threshold to exceed ----------


def test_the_budget_holds_when_the_cap_is_reached_not_after_it():
    # consumed == limit must already stop. A gate that only trips above the cap permits exactly
    # one over-budget action, and "reached" is the wording the governing rule uses.
    assert budget_gate(9, 10) == "CONTINUE"
    assert budget_gate(10, 10) == "HELD"
    assert budget_gate(11, 10) == "HELD"


def test_containment_is_the_only_thing_permitted_past_the_cap():
    assert budget_gate(10, 10, containment=True) == "CONTAINMENT_ONLY"
    assert budget_gate(9, 10, containment=True) == "CONTINUE"


# --- the event chain detects modification -----------------------------------


def built_chain() -> list[dict]:
    chain: list[dict] = []
    append_event(chain, "ROUTE_PLANNED", {"route": "r1"})
    append_event(chain, "SKILL_INVOKED", {"skill": "s1"})
    append_event(chain, "EFFECT_APPLIED", {"effect": "read"})
    append_event(chain, "OUTCOME_FAILED", {"reason": "downstream 500"})
    return chain


def test_an_untouched_chain_verifies():
    assert verify_event_chain(built_chain()) is True


def test_a_tampered_payload_digest_is_detected():
    chain = built_chain()
    chain[2]["payload_digest"] = canonical_hash({"effect": "delete"})
    assert verify_event_chain(chain) is False


def test_a_relabelled_outcome_is_detected():
    # The case that matters most: turning a failure into a success after the fact.
    chain = built_chain()
    chain[3]["event_type"] = "OUTCOME_SUCCEEDED"
    assert verify_event_chain(chain) is False


def test_reordering_is_detected():
    chain = built_chain()
    chain[1], chain[2] = chain[2], chain[1]
    assert verify_event_chain(chain) is False


def test_removing_an_event_from_the_middle_is_detected():
    chain = built_chain()
    del chain[1]
    assert verify_event_chain(chain) is False


def test_each_event_binds_to_its_predecessor_and_the_first_to_GENESIS():
    chain = built_chain()
    assert chain[0]["previous_event_hash"] == "GENESIS"
    for earlier, later in zip(chain, chain[1:]):
        assert later["previous_event_hash"] == earlier["event_hash"]
        assert later["sequence"] == earlier["sequence"] + 1
