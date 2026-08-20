"""The learning mandate is recorded, not adopted — and its collision findings are pinned.

Same two jobs as test_production_mandate.py. The first four tests hold the RECORD/ADOPT separation.
The rest pin §6's collision findings against `config/identifier_taxonomy.json`, because a governance
document that states a measurement drifts out of truth silently: eight open pull requests in this
repository were found carrying figures that matched no measurement of anything.

    STATED_AS_MEASURED ∧ UNGUARDED → SILENTLY_FALSIFIABLE

Each pinned finding fails HERE the moment the registry stops matching the document — which is also
the moment the document should be updated, or the collision resolved.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC = REPO_ROOT / "docs" / "00-governance" / "AGENTIC_LEARNING_LOOP_MANDATE.md"
TEXT = DOC.read_text(encoding="utf-8")
# Phrase assertions run against whitespace-normalised text. A test that fails because prose was
# re-wrapped is measuring the line width, not the claim.
FLAT = " ".join(TEXT.split())
TAXONOMY = json.loads(
    (REPO_ROOT / "config" / "identifier_taxonomy.json").read_text(encoding="utf-8")
)
LADDERS = {entry["prefix"]: entry for entry in TAXONOMY["ladders"]}


# --- record, not adopt ------------------------------------------------------


def test_the_document_records_without_adopting():
    assert "PROPOSED — RECORDED, NOT ADOPTED" in FLAT
    assert "It does not enact one" in FLAT


def test_no_learning_object_may_cite_it_as_authority():
    assert "may cite it as authority" in FLAT


def test_it_restates_the_ladder_that_keeps_knowledge_below_authority():
    assert "Knowledge ≠ policy" in FLAT and "Policy ≠ authority" in FLAT


def test_it_names_its_own_limits():
    for claim in ("Not an adoption", "Not a scope change",
                  "Not an authorization to build", "no independent verification"):
        assert claim in FLAT, f"the limits section no longer states: {claim!r}"


# --- the collision findings, pinned against the registry --------------------


def test_the_K_prefix_is_still_bound_to_kpis():
    # §6.1. If K is ever rebound or the knowledge ladder is registered under it, this fails and the
    # document must be re-derived rather than left asserting a collision that was resolved.
    assert "K" in LADDERS, "the K ladder vanished from the registry"
    entry = LADDERS["K"]
    assert "key performance" in entry["bound_to"].lower(), (
        f"K is now bound to {entry['bound_to']!r}, not to KPIs. §6.1 of the mandate record "
        "describes a collision that may no longer exist."
    )
    assert entry["form"].startswith("K-01"), entry["form"]


def test_the_risk_ladder_is_R_not_C():
    # §6.2. The finding is that `risk_class: C2` uses C where R is the registered risk ladder.
    assert "risk" in LADDERS["R"]["bound_to"].lower()
    assert LADDERS["R"]["form"] == "R0-R4"
    assert "conflict" in LADDERS["C"]["bound_to"].lower(), (
        "C is no longer the conflict-impact ladder, so §6.2's reasoning must be re-derived"
    )


def test_the_C_prefix_already_carries_recorded_collisions():
    recorded = {c["prefix"] for c in TAXONOMY["collisions_recorded"]}
    assert "C" in recorded, (
        "§6.2 states that C already carries recorded live meanings; the registry no longer agrees"
    )


def test_a_knowledge_register_already_exists_with_a_registered_prefix():
    # §6.3, the duplicate-work finding. This is the one most likely to be resolved by a decision
    # rather than by a code change, and the document must not keep asserting it afterwards.
    assert "KN" in LADDERS, "the KN ladder vanished"
    assert "knowledge" in LADDERS["KN"]["bound_to"].lower()
    home = REPO_ROOT / "docs" / "13-evidence" / "KNOWLEDGE_REGISTER.md"
    assert home.is_file(), (
        "§6.3 rests on an existing knowledge register at docs/13-evidence/KNOWLEDGE_REGISTER.md, "
        "which is no longer present"
    )


def test_the_five_new_prefixes_are_still_unregistered():
    # §6.4. When any of these IS registered, this fails — which is the correct moment to strike it
    # from the document rather than leave a resolved item listed as owed.
    registered = set(LADDERS) | {r["prefix"] for r in TAXONOMY["reserved_unbound"]}
    for prefix in ("KC", "CC", "LL", "SECB-KNOW", "EPISODE"):
        assert prefix not in registered, (
            f"{prefix} is now registered; §6.4 lists it as owed and must be updated"
        )


# --- the structural baseline ------------------------------------------------


def test_the_proposed_learning_tree_is_still_absent():
    # §5. The day any of these appears, the baseline is stale and the Lean argument in §7 changes.
    for path in ("knowledge", "agents", "tools", "skills", "schemas/learning"):
        assert not (REPO_ROOT / path).exists(), (
            f"{path} now exists, but §5 records the entire proposed learning plane as ABSENT. "
            "Re-measure §5 and revisit §7's prematurity argument in the same change."
        )


def test_the_document_records_LL01_as_blocked_on_the_same_merge_gate():
    assert "LL-01 is blocked on the same merge gate as Stage 0" in FLAT
