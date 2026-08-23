"""The self-repair record is recorded not adopted, and its measured claims are pinned.

Its §4.1 asserts the strongest claim in the series -- that this mandate introduces NO colliding
vocabulary, the first of four to do so. §5 asserts four integration verdicts. Both are measurements,
and a governance document that states a measurement without a guard drifts out of truth silently.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC = REPO_ROOT / "docs" / "00-governance" / "SELF_REPAIR_MANDATE.md"
FLAT = " ".join(DOC.read_text(encoding="utf-8").split())
TAXONOMY = json.loads(
    (REPO_ROOT / "config" / "identifier_taxonomy.json").read_text(encoding="utf-8")
)
LADDERS = {e["prefix"]: e for e in TAXONOMY["ladders"]}


def test_it_records_without_adopting():
    assert "PROPOSED — RECORDED, NOT ADOPTED" in FLAT
    assert "does not enact one" in FLAT


def test_it_repeats_the_mandate_own_prohibition_on_building_early():
    # §24 and §23 of the mandate forbid building before #171 lands and adoption is issued. The
    # record must keep saying so, since that is the sentence that makes it non-actionable.
    assert "target design only" in FLAT


def test_every_prefix_it_declares_is_registered_with_its_registered_meaning():
    # §4.1's claim. If any prefix here ever needs COLLIDES or NEW, the "first clean mandate" claim
    # is false and must be struck rather than left standing.
    for prefix in ("R", "KN", "SECB-WP", "C"):
        assert prefix in LADDERS, f"{prefix} is no longer registered; §4 must be re-derived"
    assert LADDERS["R"]["form"] == "R0-R4"
    assert "risk" in LADDERS["R"]["bound_to"].lower()
    assert "conflict" in LADDERS["C"]["bound_to"].lower()


def test_the_ordering_blocked_row_names_its_provider():
    """§5 row 2 must be SELF-DATING, the way row 1 already is.

    Row 1 reads "absent on `main`, present in #171" and needs no guard: it names both the state and
    the pull request that changes it, so it stays true after #171 lands. Row 2 read only "absent on
    `main`" -- a present-tense claim about a moving tree -- and was guarded by asserting that
    `schemas/` does not exist.

    That guard could only ever fail, because #171 creates `schemas/` and #171 is the whole reason
    the row says ORDERING_BLOCKED. It would have fired on the day the blockage was cleared, reporting
    the intended outcome as a defect, and the composed tree confirmed exactly that.

        MEASUREMENT_PINNED != TREE_FROZEN

    A measurement that names the ref it was taken at, and the change that supersedes it, does not
    drift and needs no tripwire. So the row is now self-dating and this guards the property that
    makes it so, rather than guarding the tree against moving.
    """
    row = next((line for line in DOC.read_text(encoding="utf-8").splitlines()
                if "ORDERING_BLOCKED" in line and "|" in line), None)
    assert row is not None, "§5 no longer has an ORDERING_BLOCKED row -- the matrix was re-derived"
    assert "absent on `main`" in row, f"row 2 no longer states the measured condition: {row}"
    assert "#171" in row, (
        f"row 2 states a present-tense condition without naming the pull request that supersedes "
        f"it, so it becomes false the day #171 lands rather than remaining a dated measurement: {row}"
    )


def test_the_two_refinement_rows_are_still_proposals_not_states():
    # §5.1. The finding is that INCOMPATIBLE_DESIGN and DUPLICATE_CAPABILITY describe proposals.
    # If a .rego file or a knowledge/ tree ever appears, they become present states and §5.1 is
    # wrong in the direction that matters.
    rego = [p for p in REPO_ROOT.rglob("*.rego") if ".git" not in p.parts]
    assert not rego, f".rego files now exist ({rego}); §5.1 claims none do"
    assert not (REPO_ROOT / "knowledge").exists(), (
        "a knowledge/ tree now exists; §5.1 records the DUPLICATE_CAPABILITY verdict as a "
        "proposal already dispositioned to 'extend KN-*, do not create'"
    )


def test_it_records_the_platform_failure_breaker_as_in_force():
    # §6. The mandate's own circuit breaker covers the condition actually in force, and the record
    # states that no product code was edited in response. That sentence is the evidence.
    assert "external platform failure is misclassified as code failure" in FLAT
    assert "no product code was edited in response" in FLAT
