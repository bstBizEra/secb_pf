"""Eligibility must hold on the transitive edge, not only the top-level loop.

`route()` filters candidates through `_eligible` -- status, expiry, risk ceiling,
permitted effects. Prerequisites were expanded against the FULL registry, so a
skill that failed every one of those checks could still enter the plan by being
named as another skill's prerequisite, and could then obtain both an invocation
warrant and an effect warrant.

The sealed FIT suite covers each axis separately -- a directly-named revoked
skill is refused (FIT-102), and a QUALIFIED prerequisite routes (FIT-106) -- but
never their intersection, which is where the defect lived.

Latent while the prerequisite graph is empty. The first registered skill with a
prerequisite makes it live, which is exactly what a skill-import programme does.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from secb_router.router import (
    RouteHeld,
    Skill,
    authorize_effect,
    authorize_invocation,
    route,
)

NOW = datetime(2026, 8, 25, tzinfo=timezone.utc)
POLICY = "policy-hash-1"
EXPIRED = "2000-01-01T00:00:00+00:00"
LIVE = "2099-01-01T00:00:00+00:00"


def _request(**over):
    base = {
        "risk_tier": "R1",
        "required_capabilities": {"main"},
        "permitted_effects": [],
    }
    base.update(over)
    return base


def _carrier(**over):
    """A QUALIFIED skill that covers the request and depends on `blocked`."""
    kw = dict(
        skill_id="carrier",
        version="1.0",
        digest="d",
        capabilities=frozenset({"main"}),
        status="QUALIFIED",
        risk_ceiling="R3",
        expires_at=LIVE,
        prerequisites=("blocked",),
    )
    kw.update(over)
    return Skill(**kw)


# Each case makes `blocked` fail exactly ONE eligibility check.
INELIGIBLE = [
    pytest.param({"status": "REVOKED"}, id="revoked"),
    pytest.param({"status": "SUSPENDED"}, id="suspended"),
    pytest.param({"status": "CANDIDATE"}, id="candidate-not-qualified"),
    pytest.param({"expires_at": EXPIRED}, id="expired"),
    pytest.param({"risk_ceiling": "R0"}, id="risk-ceiling-below-request"),
    pytest.param({"effects": frozenset({"network_egress"})}, id="effect-not-permitted"),
]


@pytest.mark.parametrize("defect", INELIGIBLE)
def test_an_ineligible_prerequisite_cannot_enter_the_plan(defect):
    kw = dict(
        skill_id="blocked",
        version="1.0",
        digest="d",
        capabilities=frozenset({"dep"}),
        status="QUALIFIED",
        risk_ceiling="R3",
        expires_at=LIVE,
    )
    kw.update(defect)          # a defect REPLACES the healthy default
    blocked = Skill(**kw)
    skills = [blocked, _carrier()]
    request = _request()

    with pytest.raises(RouteHeld):
        plan = route(request, skills, POLICY, now=NOW)
        # If a plan is ever produced, the defect is that `blocked` reached it.
        assert "blocked" not in plan.order, (
            f"ineligible prerequisite entered the plan via the transitive edge: {defect}"
        )


def test_no_warrant_is_reachable_for_an_ineligible_prerequisite():
    """The end state that matters: warrants, not plan membership."""
    blocked = Skill(
        "blocked", "1.0", "d", frozenset({"dep"}),
        status="REVOKED", risk_ceiling="R0", expires_at=EXPIRED,
        effects=frozenset({"network_egress"}),
    )
    skills = [blocked, _carrier()]
    request = _request()

    try:
        plan = route(request, skills, POLICY, now=NOW)
    except RouteHeld:
        return  # fail-closed: no plan, therefore no warrant

    with pytest.raises(RouteHeld):
        authorize_invocation(
            plan, "blocked", request=request, skills=skills, policy_hash=POLICY
        )
    with pytest.raises(RouteHeld):
        authorize_effect(plan, "blocked", "network_egress", confirmation=False)


def test_a_plan_never_both_rejects_and_selects_the_same_skill():
    """An audit record asserting both about one skill states a falsehood."""
    blocked = Skill(
        "blocked", "1.0", "d", frozenset({"dep"}),
        status="REVOKED", expires_at=EXPIRED,
    )
    skills = [blocked, _carrier()]
    try:
        plan = route(_request(), skills, POLICY, now=NOW)
    except RouteHeld:
        return
    assert not (set(plan.rejected) & set(plan.order)), (
        f"skill appears in rejected and order simultaneously: "
        f"{set(plan.rejected) & set(plan.order)}"
    )


def test_an_eligible_prerequisite_still_routes():
    """The control. The fix must not break legitimate transitive dependencies."""
    dep = Skill(
        "blocked", "1.0", "d", frozenset({"dep"}),
        status="QUALIFIED", risk_ceiling="R3", expires_at=LIVE,
    )
    plan = route(_request(), [dep, _carrier()], POLICY, now=NOW)
    assert "blocked" in plan.order, "an eligible prerequisite was wrongly excluded"
    assert plan.order.index("blocked") < plan.order.index("carrier")


def test_a_genuinely_missing_prerequisite_is_still_distinguishable():
    """A prerequisite absent from the registry is a different fault from an
    ineligible one, and the messages must not collapse into each other."""
    with pytest.raises(RouteHeld):
        route(_request(), [_carrier()], POLICY, now=NOW)
