"""Refusals in secb_router leave by RouteHeld, never by an uncontrolled exception.

The module states one refusal contract: a fail-closed decision raises RouteHeld. Two paths broke it
and both were on the authorization side.

    authorize_effect   next(s for s in plan.selected if ...)     -> bare StopIteration
    fallback           fallback_controls[floor]                  -> KeyError

Neither granted anything, so both were fail-closed *by accident*. That is not the same as being
fail-closed by design, for three reasons that only appear at the call site:

  - a caller writing `except RouteHeld:` does not catch them, so a refusal becomes a crash;
  - `StopIteration` raised inside a generator is silently converted to RuntimeError by PEP 479, so
    the exception type depends on who called, not on what happened;
  - `KeyError('data')` does not say a floor was missing, so a caller cannot tell "omitted" from
    "present and lower" without knowing the implementation.

    RAISES_SOMETHING != REFUSES_UNDER_CONTRACT

Found by probing, not by reading: see the router invariants issue, items 3 and 4. #193 pins the
invariants that already held; this file covers the two that did not.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from secb_router.router import (  # noqa: E402
    RoutePlan, RouteHeld, Skill, authorize_effect, fallback,
)

FLOORS = ("risk", "authority", "validation", "data")


def a_skill(**over) -> Skill:
    base = dict(skill_id="s1", version="1", digest="d1",
                capabilities=frozenset({"cap"}), effects=frozenset({"read"}))
    base.update(over)
    return Skill(**base)


def a_plan(skills: list[Skill]) -> RoutePlan:
    return RoutePlan(route_id="r1", request_hash="h", registry_hash="h", policy_hash="h",
                     selected=list(skills), rejected={}, order=[s.skill_id for s in skills])


# --- authorize_effect: warranted but absent from the plan --------------------


def test_a_warranted_skill_absent_from_the_plan_is_refused_by_contract():
    # Reachable whenever invocation_warrants and plan.selected disagree. The function must not
    # depend on an invariant it never checks -- that is what made the old failure a StopIteration.
    plan = a_plan([a_skill()])
    plan.invocation_warrants.add("ghost")
    with pytest.raises(RouteHeld, match="skill not in plan"):
        authorize_effect(plan, "ghost", "read", confirmation=True)


def test_that_refusal_is_not_stopiteration_or_runtimeerror():
    # PEP 479 turns a StopIteration crossing a generator boundary into RuntimeError, so asserting
    # "it raises" is not enough: the type has to be stable regardless of the call site.
    plan = a_plan([a_skill()])
    plan.invocation_warrants.add("ghost")
    try:
        authorize_effect(plan, "ghost", "read", confirmation=True)
    except RouteHeld:
        pass
    except (StopIteration, RuntimeError) as exc:  # pragma: no cover - the regression
        pytest.fail(f"refusal escaped the contract as {type(exc).__name__}")


def test_the_refusal_survives_being_raised_inside_a_generator():
    # The concrete PEP 479 hazard, exercised rather than described.
    plan = a_plan([a_skill()])
    plan.invocation_warrants.add("ghost")

    def consume():
        yield authorize_effect(plan, "ghost", "read", confirmation=True)

    with pytest.raises(RouteHeld):
        list(consume())


# --- fallback: an omitted floor is the likeliest way to weaken one -----------


@pytest.mark.parametrize("omitted", FLOORS)
def test_a_fallback_omitting_any_floor_is_refused_by_contract(omitted):
    original = {f: 1 for f in FLOORS}
    proposed = {f: 1 for f in FLOORS if f != omitted}
    with pytest.raises(RouteHeld, match=f"no {omitted} floor"):
        fallback(original, proposed)


@pytest.mark.parametrize("omitted", FLOORS)
def test_an_original_omitting_any_floor_is_also_refused(omitted):
    # Symmetric: a comparison is only meaningful when both sides declare the floor. Refusing one
    # side and KeyError-ing on the other would be the same defect with the arguments swapped.
    original = {f: 1 for f in FLOORS if f != omitted}
    proposed = {f: 1 for f in FLOORS}
    with pytest.raises(RouteHeld, match=f"no {omitted} floor"):
        fallback(original, proposed)


def test_the_message_distinguishes_an_omitted_floor_from_a_lowered_one():
    original = {f: 2 for f in FLOORS}
    lowered = {**{f: 2 for f in FLOORS}, "risk": 1}
    omitted = {f: 2 for f in FLOORS if f != "risk"}
    with pytest.raises(RouteHeld, match="weakens risk floor"):
        fallback(original, lowered)
    with pytest.raises(RouteHeld, match="no risk floor"):
        fallback(original, omitted)


# --- the fix must not have loosened anything --------------------------------


def test_a_fallback_that_holds_every_floor_still_returns_a_new_version():
    assert fallback({f: 1 for f in FLOORS}, {f: 1 for f in FLOORS}) == 2


def test_a_fallback_that_raises_a_floor_is_still_permitted():
    assert fallback({f: 1 for f in FLOORS}, {f: 5 for f in FLOORS}) == 2


def test_a_present_skill_with_a_valid_warrant_still_authorizes():
    plan = a_plan([a_skill()])
    plan.invocation_warrants.add("s1")
    assert authorize_effect(plan, "s1", "read", confirmation=False)
