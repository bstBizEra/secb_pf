"""Guards for config/identifier_taxonomy.json (`SECB-WP-FWK-041`).

Five identifier-prefix collisions were found by hand across four work
packages, each one discovered messages or days after it was introduced --
`C` three times over, `D` twice, and `E` and `L` proposed on top of prefixes
already bound. The registry turns that class of defect into a failing test:
a sixth collision is a duplicate key, not an archaeology exercise.

What these tests enforce is deliberately narrow, and the previous version of
this docstring overstated it. They are **integrity checks on one file**: they
detect a new duplicate *recorded here*. They do **not** prevent collision debt
from growing in the repository -- demonstrated, not assumed: a colliding `G`
ladder written into a document without touching the registry passed all 73
tests, the classifier and the budget gate. Growth prevention belongs to
external policy and enforcement.

Corrected under the operator's research verdict of 2026-08-11: baseline freeze
and growth prevention are different properties, and only the first is a
registry function.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TAXONOMY = REPO_ROOT / "config" / "identifier_taxonomy.json"


def load() -> dict:
    return json.loads(TAXONOMY.read_text(encoding="utf-8"))


def test_registry_is_valid_json_with_the_required_top_level_fields():
    t = load()
    for field in ("taxonomy_id", "taxonomy_version", "as_of_commit", "ladders"):
        assert field in t, f"registry is missing {field}"
    assert re.fullmatch(r"\d+\.\d+\.\d+", t["taxonomy_version"])


def test_every_ladder_declares_where_it_lives_and_what_enforces_it():
    # A prefix whose home is unrecorded is how the collisions happened: the
    # meaning existed but nothing said where it was authoritative.
    for ladder in load()["ladders"]:
        for field in ("prefix", "form", "bound_to", "home", "enforced_by"):
            assert ladder.get(field), f"{ladder.get('prefix')} is missing {field}"


def test_no_prefix_is_bound_twice_outside_the_recorded_collisions():
    """The guard. A new duplicate prefix fails here rather than in review."""
    t = load()
    seen: dict[str, str] = {}
    duplicates = []
    for ladder in t["ladders"]:
        prefix = ladder["prefix"]
        if prefix in seen:
            duplicates.append(prefix)
        seen[prefix] = ladder["bound_to"]

    recorded = {c["prefix"] for c in t.get("collisions_recorded", [])}
    unexpected = set(duplicates) - recorded
    assert not unexpected, (
        f"prefix bound twice without a collision record: {sorted(unexpected)}. "
        "Either give the new ladder a free prefix, or add it to "
        "collisions_recorded with an observational status and an advisory "
        "recommendation."
    )


OBSERVATIONAL_STATUS = {"BOTH_IN_FORCE", "SECOND_CLAIMANT_NOT_ADOPTED", "RESOLVED"}


def test_every_recorded_collision_carries_meanings_evidence_and_an_observation():
    for c in load().get("collisions_recorded", []):
        assert len(c.get("meanings", [])) >= 2, f"{c['prefix']}: needs 2+ meanings"
        assert c.get("evidenced_by"), f"{c['prefix']}: needs evidence"
        assert c.get("observed_status") in OBSERVATIONAL_STATUS, (
            f"{c['prefix']}: observed_status must be observational, one of "
            f"{sorted(OBSERVATIONAL_STATUS)} -- a verdict token here would make "
            "the registry originate a decision"
        )


def test_no_collision_record_carries_a_prohibition():
    """The registry may recommend; it may not forbid.

    v1.0.0 of this file failed this: its `disposition` read *"BLOCKED --
    expansion classes may not enter SecB as bare E-n"*, and a test enforced
    that they stay blocked. That is a prohibition originated by a factual
    ledger and enforced by its own guard -- which contradicted the adjacent
    test asserting the registry enacts no rule. Caught by the operator's
    research verdict, not by this suite, which is why the check now exists.
    """
    forbidding = re.compile(r"\b(SHALL NOT|MUST NOT|may not|is prohibited|forbidden)\b")
    for c in load().get("collisions_recorded", []):
        reco = c.get("recommendation_advisory", "")
        assert reco.startswith("Advisory, not a rule"), (
            f"{c['prefix']}: a recommendation must label itself advisory"
        )
        assert not forbidding.search(reco), (
            f"{c['prefix']}: recommendation contains prohibitive language -- "
            "the registry records and recommends; enforcement is external"
        )


def test_observed_status_agrees_with_whether_the_second_claimant_is_adopted():
    """The status is a reading of the world, so it must match the world.

    This replaces a test that *mandated* `E` and `L` stay blocked. Mandating
    is enforcement; the registry only observes. If expansion classes or BACP
    layers are ever adopted, this test wants the record updated to say so --
    not to keep asserting a prohibition the authority never granted.
    """
    for c in load()["collisions_recorded"]:
        adopted = c["second_claimant_adopted"]
        expected = "BOTH_IN_FORCE" if adopted else "SECOND_CLAIMANT_NOT_ADOPTED"
        assert c["observed_status"] == expected, (
            f"{c['prefix']}: observed_status and second_claimant_adopted disagree"
        )


def test_reserved_prefixes_do_not_collide_with_bound_ones():
    t = load()
    bound = {ladder["prefix"] for ladder in t["ladders"]}
    for reserved in t.get("reserved_unbound", []):
        assert reserved["prefix"] not in bound, (
            f"{reserved['prefix']} is reserved but already bound -- "
            "reserving a taken prefix is the defect this file exists to catch"
        )
        assert "NOT ADOPTED" in reserved["status"], (
            "a reservation must state that it is not an adoption, or it "
            "becomes policy by filing"
        )


def test_the_L_prefix_is_recorded_as_belonging_to_the_constitution():
    # The specific fact that makes BACP's layer labels unimportable: L0 is
    # not a spare label here, it is the constitution's filename.
    ladders = {ladder["prefix"]: ladder for ladder in load()["ladders"]}
    assert "L" in ladders
    assert "L0_ROOT_CONSTITUTION.md" in ladders["L"]["home"]


def test_the_registry_states_its_own_boundary_and_what_it_cannot_do():
    """`FR-07`: a baseline freeze must not be read as growth prevention."""
    limits = load()["scope_and_limits"]
    for field in (
        "observation_boundary",
        "demonstrated_limit",
        "what_the_baseline_freeze_means",
        "append_only_basis",
        "growth_prevention_owner",
    ):
        assert limits.get(field), f"scope_and_limits is missing {field}"
    assert "NOT" in limits["what_the_baseline_freeze_means"]
    assert "external" in limits["growth_prevention_owner"]
    # The append-only claim must not be stronger than the mechanism.
    assert "git history" in limits["append_only_basis"]


def test_registry_claims_no_rule_it_has_not_been_granted():
    """The registry records facts; it must not enact the naming rule.

    `SECB-WP-FWK-039` recommended "a prefix, once bound, is never rebound".
    Enacting that would bind agent behaviour, which is an act on the
    authority surface -- not something an executor lands by adding a config
    file. The registry says so about itself, and this test keeps it honest.
    """
    notes = " ".join(load().get("notes", []))
    assert "does NOT enact a rule" in notes
    assert "remains ungranted" in notes
