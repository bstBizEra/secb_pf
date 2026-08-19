"""A held, waiting, or completed route cannot be re-authorized.

authorize_invocation re-verified request, registry and policy hashes, confirmed the skill was in the
plan -- and then assigned `plan.status = "AUTHORIZED"` without ever reading the status it overwrote.
Measured before the fix:

    HELD                    -> AUTHORIZED, warrant issued
    COMPLETED               -> AUTHORIZED, warrant issued
    CLARIFICATION_REQUIRED  -> AUTHORIZED, warrant issued
    FALLBACK                -> AUTHORIZED, warrant issued

HELD is the fail-closed state the whole design rests on; the module's exception class is named
RouteHeld for it. A hold that the next authorization call clears is not a hold.

    STATUS_RECORDED != STATUS_ENFORCED

THE VOCABULARY IS NOT INVENTED BY THE FIX. The nine statuses come from the `status` enum of
docs/06-agent-orchestration/skill-router/route-plan.schema.json, which is on main. An earlier note on
the findings issue claimed this fix was blocked on config/state_machine.json (#179); that was wrong
and conflated two vocabularies -- #179 governs work-package transitions, not route plans. The schema
was the authority all along, and it was already effective.

    TWO_LADDERS_SHARING_A_SHAPE != ONE_LADDER

test_the_split_covers_the_schema_enum_exactly is the load-bearing test here: it binds the code's
classification to the schema, so adding a status to the schema without deciding whether it may be
authorized from fails in this suite rather than defaulting to permitted.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from secb_router.router import (  # noqa: E402
    AUTHORIZABLE_STATUSES, NON_AUTHORIZABLE_STATUSES, RoutePlan, RouteHeld, Skill,
    authorize_invocation, canonical_hash, registry_hash,
)

SCHEMA = REPO_ROOT / "docs" / "06-agent-orchestration" / "skill-router" / "route-plan.schema.json"
REQUEST = {"goal": "x"}


def a_skill() -> Skill:
    return Skill(skill_id="s1", version="1", digest="d1",
                 capabilities=frozenset({"cap"}), effects=frozenset({"read"}))


def plan_in(status: str, skills: list[Skill] | None = None) -> RoutePlan:
    skills = skills or [a_skill()]
    return RoutePlan(route_id="r1", request_hash=canonical_hash(REQUEST),
                     registry_hash=registry_hash(skills), policy_hash="p1",
                     selected=list(skills), rejected={}, order=[s.skill_id for s in skills],
                     status=status)


def schema_statuses() -> set[str]:
    document = json.loads(SCHEMA.read_text(encoding="utf-8"))
    return set(document["properties"]["status"]["enum"])


# --- the split is total and disjoint against the schema ---------------------


def test_the_split_covers_the_schema_enum_exactly():
    # The whole point of the fix. If a status exists in the schema and in neither set, an allowlist
    # check refuses it -- safe, but silently, and nobody decided. If it exists in both, the
    # classification contradicts itself.
    declared = schema_statuses()
    classified = AUTHORIZABLE_STATUSES | NON_AUTHORIZABLE_STATUSES
    assert classified == declared, (
        f"unclassified in the code: {sorted(declared - classified)}; "
        f"named in the code but absent from the schema: {sorted(classified - declared)}. "
        "Every RoutePlan status must be explicitly authorizable or not."
    )


def test_no_status_is_both_authorizable_and_not():
    overlap = AUTHORIZABLE_STATUSES & NON_AUTHORIZABLE_STATUSES
    assert not overlap, f"contradictory classification for {sorted(overlap)}"


def test_the_three_stop_states_are_the_ones_excluded():
    # Named literally rather than derived, so a change to the policy is visible as a diff here and
    # not just as a set-membership shift somewhere else.
    assert NON_AUTHORIZABLE_STATUSES == {"HELD", "CLARIFICATION_REQUIRED", "COMPLETED"}


# --- refusal, and no side effects on refusal --------------------------------


@pytest.mark.parametrize("status", sorted(NON_AUTHORIZABLE_STATUSES))
def test_a_stopped_route_is_refused(status):
    plan = plan_in(status)
    skills = plan.selected
    with pytest.raises(RouteHeld, match=f"plan status {status} is not authorizable"):
        authorize_invocation(plan, "s1", request=REQUEST, skills=skills, policy_hash="p1")


@pytest.mark.parametrize("status", sorted(NON_AUTHORIZABLE_STATUSES))
def test_a_refused_authorization_leaves_no_trace(status):
    # A refusal that still mutated the plan would be worse than the original defect: the caller sees
    # an exception and the plan carries a warrant anyway.
    plan = plan_in(status)
    skills = plan.selected
    with pytest.raises(RouteHeld):
        authorize_invocation(plan, "s1", request=REQUEST, skills=skills, policy_hash="p1")
    assert plan.status == status, "the refused call overwrote the status it refused"
    assert not plan.invocation_warrants, "a refused authorization issued a warrant"


@pytest.mark.parametrize("status", sorted(NON_AUTHORIZABLE_STATUSES))
def test_the_status_is_checked_before_the_hashes(status):
    # Order matters for what the refusal TELLS the caller. If hashes were verified first, a held
    # plan with a stale request would answer "request changed", implying that a matching request
    # would have been authorized -- which it would not.
    plan = plan_in(status)
    with pytest.raises(RouteHeld, match="not authorizable"):
        authorize_invocation(plan, "s1", request={"goal": "DIFFERENT"},
                             skills=plan.selected, policy_hash="WRONG")


# --- every other status still authorizes -----------------------------------


@pytest.mark.parametrize("status", sorted(AUTHORIZABLE_STATUSES))
def test_an_authorizable_route_still_authorizes(status):
    plan = plan_in(status)
    warrant = authorize_invocation(plan, "s1", request=REQUEST,
                                   skills=plan.selected, policy_hash="p1")
    assert warrant
    assert plan.status == "AUTHORIZED"
    assert "s1" in plan.invocation_warrants


def test_a_second_skill_in_the_same_plan_can_still_be_authorized():
    # The reason AUTHORIZED must itself be authorizable: a multi-skill plan authorizes each skill in
    # turn, and the first call sets the status the second one reads.
    first, second = a_skill(), Skill(skill_id="s2", version="1", digest="d2",
                                     capabilities=frozenset({"cap"}), effects=frozenset({"read"}))
    plan = plan_in("PLANNED", [first, second])
    authorize_invocation(plan, "s1", request=REQUEST, skills=plan.selected, policy_hash="p1")
    assert plan.status == "AUTHORIZED"
    authorize_invocation(plan, "s2", request=REQUEST, skills=plan.selected, policy_hash="p1")
    assert plan.invocation_warrants == {"s1", "s2"}


def test_the_existing_subject_checks_are_unchanged_for_an_authorizable_plan():
    # The guard must not have shadowed the checks it now precedes.
    plan = plan_in("PLANNED")
    with pytest.raises(RouteHeld, match="request changed"):
        authorize_invocation(plan, "s1", request={"goal": "other"},
                             skills=plan.selected, policy_hash="p1")
