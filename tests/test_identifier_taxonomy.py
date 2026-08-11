"""Guards for config/identifier_taxonomy.json (`SECB-WP-FWK-041`).

Five identifier-prefix collisions were found by hand across four work
packages, each one discovered messages or days after it was introduced --
`C` three times over, `D` twice, and `E` and `L` proposed on top of prefixes
already bound. The registry turns that class of defect into a failing test:
a sixth collision is a duplicate key, not an archaeology exercise.

What these tests enforce is deliberately narrow. They **freeze the recorded
debt and block its growth**; they do not pretend the debt is paid. Renaming
a bound prefix rewrites decision records that cite it, which is the
operator's call, so the registry records dispositions rather than applying
them.
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
        "collisions_recorded with a disposition."
    )


def test_every_recorded_collision_names_its_meanings_and_a_disposition():
    # A collision recorded without a disposition is a note, not a decision.
    for c in load().get("collisions_recorded", []):
        assert len(c.get("meanings", [])) >= 2, f"{c['prefix']}: needs 2+ meanings"
        assert c.get("disposition"), f"{c['prefix']}: needs a disposition"
        assert c.get("evidenced_by"), f"{c['prefix']}: needs evidence"
        assert c["disposition"].split()[0] in ("OPEN", "BLOCKED", "RESOLVED"), (
            f"{c['prefix']}: disposition must start OPEN, BLOCKED or RESOLVED"
        )


def test_blocked_collisions_are_the_ones_with_an_unadopted_claimant():
    """`E` and `L` are BLOCKED because the second meaning is only proposed.

    That distinction matters: a BLOCKED collision can still be prevented, an
    OPEN one has already shipped and can only be renamed.
    """
    blocked = {
        c["prefix"]
        for c in load()["collisions_recorded"]
        if c["disposition"].startswith("BLOCKED")
    }
    assert {"E", "L"} <= blocked, (
        "E (expansion classes) and L (BACP artifact layers) must stay BLOCKED "
        "until they take a free prefix or are set-qualified at every use"
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


def test_registry_claims_no_rule_it_has_not_been_granted():
    """The registry records facts; it must not enact the naming rule.

    `SECB-WP-FWK-039` recommended "a prefix, once bound, is never rebound".
    Enacting that would bind agent behaviour, which is an act on the
    authority surface -- not something an executor lands by adding a config
    file. The registry says so about itself, and this test keeps it honest.
    """
    notes = " ".join(load().get("notes", []))
    assert "NOT enacted here" in notes
