"""The Agent Council verdict record's measurable claims are pinned.

Unlike the four mandate records, this one is NOT proposed -- the adoption decision was made. What
must stay true is the collision analysis in §4, because a record asserting a collision that has been
resolved is worse than one that never mentioned it.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC = REPO_ROOT / "docs" / "00-governance" / "AGENT_COUNCIL_ADOPTION_VERDICT.md"
FLAT = " ".join(DOC.read_text(encoding="utf-8").split())
TAX = json.loads((REPO_ROOT / "config" / "identifier_taxonomy.json").read_text(encoding="utf-8"))
LADDERS = {e["prefix"]: e for e in TAX["ladders"]}
COLLISIONS = {c["prefix"]: c for c in TAX["collisions_recorded"]}


def test_it_records_a_decision_not_a_proposal():
    assert "APPROVED_WITH_CONDITIONS" in FLAT
    assert "not** `PROPOSED`" in FLAT or "not `PROPOSED`" in FLAT


def test_the_boundary_that_keeps_council_output_as_evidence():
    assert "evidence input" in FLAT and "never an approval" in FLAT


def test_L_is_still_the_governance_layer_ladder():
    # §4.1. If L is ever rebound or the risk ladder registered under it, this fails and the
    # inversion argument must be re-derived rather than left standing.
    assert "L" in LADDERS
    assert LADDERS["L"]["form"] == "L0-L3", LADDERS["L"]["form"]
    assert "governance layer" in LADDERS["L"]["bound_to"].lower()
    assert "L0_ROOT_CONSTITUTION" in LADDERS["L"]["home"], (
        "§4.1 rests on L0 being the constitution's filename; the registry no longer says so"
    )


def test_the_second_L_claimant_is_still_recorded_and_still_unadopted():
    # §4.2's precedent. The whole disposition argument depends on the registry having refused an
    # L0-L4 claimant before.
    assert "L" in COLLISIONS, "the L collision record is gone; §4.2 has no precedent to cite"
    record = COLLISIONS["L"]
    assert record["second_claimant_adopted"] is False
    assert record["observed_status"] == "SECOND_CLAIMANT_NOT_ADOPTED"
    assert any("L0-L4" in m for m in record["meanings"]), (
        "the recorded second claimant is no longer an L0-L4 claimant, so the 'third claimant to the "
        "same form' argument in §4.2 must be re-checked"
    )


def test_M_is_still_reserved_and_therefore_unavailable():
    # §4.2 states M cannot be the alternative because BACP already holds the reservation.
    reserved = {e["prefix"]: e for e in TAX["reserved_unbound"]}
    assert "M" in reserved, "M is no longer reserved; §4.2's 'M is not available' is stale"
    assert "NOT ADOPTED" in reserved["M"]["status"]


def test_P_is_still_unregistered():
    assert "P" not in LADDERS and "P" not in {e["prefix"] for e in TAX["reserved_unbound"]}, (
        "P is now registered; §4.3 lists it as owed and must be updated"
    )


def test_the_record_states_which_stages_are_not_yet_covered():
    assert "02, 07, 09, 11" in FLAT
