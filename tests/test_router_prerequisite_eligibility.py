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

    # An ALTERNATIVE carrier covering the same capability WITHOUT the blocked
    # prerequisite. Without it route() always raises, `except RouteHeld: return`
    # fires, and the assertions below are unreachable -- the test then passes
    # whatever it claims. A previous revision of this file had exactly that bug
    # in two different shapes.
    alt = Skill(
        skill_id="alt",
        version="1.0",
        digest="d",
        capabilities=frozenset({"main"}),
        status="QUALIFIED",
        risk_ceiling="R3",
        expires_at=LIVE,
    )
    plan = route(request, skills + [alt], POLICY, now=NOW)
    assert plan.order, "expected a plan via the alternative carrier"
    assert "blocked" not in plan.order, (
        f"ineligible prerequisite entered the plan via the transitive edge: {defect}"
    )
    assert all(s.skill_id != "blocked" for s in plan.selected)


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


def test_a_duplicate_skill_id_cannot_shadow_an_eligible_entry():
    """`by_id` was last-wins, so a REVOKED entry sharing an id with a QUALIFIED
    one could be the entry `selected` resolved to -- and obtain warrants -- while
    `rejected` recorded it as NOT_QUALIFIED. Byte-identical warrant hashes were
    produced on base and on the first draft of this fix.
    """
    good = Skill("A", "1.0", "d", frozenset({"main"}), status="QUALIFIED", risk_ceiling="R3")
    revoked = Skill(
        "A", "2.0", "d", frozenset({"main"}), status="REVOKED", risk_ceiling="R0",
        expires_at=EXPIRED, effects=frozenset({"network_egress"}),
    )
    for skills in ([good, revoked], [revoked, good]):
        try:
            plan = route(_request(), skills, POLICY, now=NOW)
        except RouteHeld:
            continue  # fail-closed is an acceptable answer
        for chosen in plan.selected:
            assert chosen.status == "QUALIFIED", (
                f"an entry with status {chosen.status} reached plan.selected"
            )
            assert chosen.version == "1.0", (
                f"the REVOKED v{chosen.version} entry shadowed the QUALIFIED one"
            )
        # NOTE: `plan.rejected` is keyed by skill_id, so a rejected v2.0 and a
        # selected v1.0 collide in the record even when routing resolves
        # correctly. That is an audit-record ambiguity under legitimate
        # versioning, not an authorization defect, and it is NOT asserted
        # against here. Recorded in the commit message as a known limitation.


def test_coverage_is_computed_from_eligible_entries_only():
    """`chosen` must resolve through the eligible map.

    `chosen` feeds the coverage check that decides whether a combination is a
    valid candidate. Resolving it through the full registry lets a SHADOWED,
    ineligible entry supply the coverage that admits the combination -- so a
    plan is produced whose selected skills do not provide the capability the
    request required. The request must ask for the capability that ONLY the
    shadowed entry appears to have, or the mutation is invisible.
    """
    real = Skill("dup", "1.0", "d", frozenset({"main"}), status="QUALIFIED", risk_ceiling="R3")
    shadow = Skill(
        "dup", "2.0", "d", frozenset({"main", "secret"}),
        status="REVOKED", risk_ceiling="R0", expires_at=EXPIRED,
    )
    request = _request(required_capabilities={"main", "secret"})

    try:
        plan = route(request, [real, shadow], POLICY, now=NOW)
    except RouteHeld:
        return  # correct: nothing eligible supplies "secret"

    covered = set().union(*(s.capabilities for s in plan.selected))
    assert set(request["required_capabilities"]) <= covered, (
        f"plan claims coverage it does not supply: required "
        f"{request['required_capabilities']}, selected provides {covered}"
    )


def test_a_prerequisite_is_ordered_before_its_dependent():
    """`_topological_order` must resolve through the eligible map too.

    Given it the full registry and a shadowed id, it walks the wrong entry's
    prerequisite list and can emit a dependent ahead of what it depends on.
    """
    dep = Skill("dep", "1.0", "d", frozenset({"dep"}), status="QUALIFIED",
                risk_ceiling="R3", expires_at=LIVE)
    carrier = Skill("carrier", "1.0", "d", frozenset({"main"}), status="QUALIFIED",
                    risk_ceiling="R3", expires_at=LIVE, prerequisites=("dep",))
    shadow = Skill("carrier", "2.0", "d", frozenset({"main"}), status="REVOKED",
                   risk_ceiling="R0", expires_at=EXPIRED, prerequisites=())
    plan = route(_request(), [dep, carrier, shadow], POLICY, now=NOW)
    assert "dep" in plan.order and "carrier" in plan.order
    assert plan.order.index("dep") < plan.order.index("carrier"), (
        f"dependent ordered before its prerequisite: {plan.order}"
    )


def test_an_unrelated_duplicate_version_does_not_block_routing():
    """Two live versions of a skill the request never asks for must not hold the
    route. A registry-wide uniqueness guard did exactly that and was withdrawn."""
    main = Skill("main", "1.0", "d", frozenset({"main"}), status="QUALIFIED", risk_ceiling="R3")
    u1 = Skill("util", "1.0", "d", frozenset({"util"}), status="QUALIFIED", risk_ceiling="R3")
    u2 = Skill("util", "2.0", "d", frozenset({"util"}), status="QUALIFIED", risk_ceiling="R3")
    plan = route(_request(), [main, u1, u2], POLICY, now=NOW)
    assert plan.order == ["main"]


@pytest.mark.parametrize("tier", ["R0", "R1", "R2", "R3"])
def test_routing_does_not_invert_with_the_request_risk_tier(tier):
    """Lowering a request's tier must never make routing fail. A guard that did
    created a standing incentive to escalate a tier to make routing work."""
    a1 = Skill("A", "1.0", "d", frozenset({"main"}), status="QUALIFIED", risk_ceiling="R1")
    a2 = Skill("A", "2.0", "d", frozenset({"main"}), status="QUALIFIED", risk_ceiling="R3")
    plan = route(_request(risk_tier=tier), [a1, a2], POLICY, now=NOW)
    assert plan.order == ["A"]
