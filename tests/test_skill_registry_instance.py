"""The first skill-registry instance in this repository, and the effect boundary it declares.

`skill_registry_instances: 0` has been the measured state since the registry schema was written.
A schema with no instance enforces nothing, so this file exists to make the first one conform and
to keep it conforming.

The instance is validated against the schema BY PATH rather than by `$id` discovery, because
`skill-registry.schema.json` is one of the seven schemas with no `$id` (fix in flight on #192).
Discovery will start working when that lands; conformance is checkable today and is checked here.

    SCHEMA_EXISTS != SCHEMA_ENFORCED
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA = (REPO_ROOT / "docs" / "06-agent-orchestration" / "skill-router"
          / "skill-registry.schema.json")
REGISTRY = REPO_ROOT / "docs" / "skills" / "catalog" / "skill-registry.json"
SKILL_DOC = REPO_ROOT / "docs" / "skills" / "catalog" / "council-issue-intake.md"


def entries() -> list[dict]:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))["skills"]


def item_schema() -> dict:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    return (schema.get("properties", {}).get("skills", {}) or {}).get("items") or schema


def test_the_registry_is_not_empty():
    """An empty registry passes every per-entry check below without checking anything."""
    assert entries(), (
        "docs/skills/catalog/skill-registry.json declares no skills, so every assertion in this "
        "file is vacuous -- the state this instance was added to end"
    )


def test_every_entry_carries_the_schema_required_fields():
    required = item_schema()["required"]
    for entry in entries():
        missing = sorted(set(required) - set(entry))
        assert not missing, f"{entry.get('skill_id')} omits required field(s) {missing}"


def test_enum_valued_fields_hold_declared_values():
    props = item_schema()["properties"]
    for entry in entries():
        for field in ("status", "risk_ceiling"):
            allowed = props[field]["enum"]
            assert entry[field] in allowed, (
                f"{entry['skill_id']}.{field} = {entry[field]!r}, not one of {allowed}"
            )


def test_a_candidate_skill_claims_no_qualification_it_does_not_have():
    """`CANDIDATE` means unproven. The evidence field must say so rather than sit empty."""
    for entry in entries():
        if entry["status"] != "CANDIDATE":
            continue
        evidence = " ".join(entry["qualification_evidence"])
        assert evidence.strip(), f"{entry['skill_id']} is CANDIDATE with no evidence field at all"
        assert "NOT QUALIFIED" in evidence, (
            f"{entry['skill_id']} is CANDIDATE but its qualification_evidence does not say so. An "
            f"absent disclaimer reads to a consumer exactly like a qualified skill."
        )


def test_a_read_only_skill_declares_no_permitted_effects():
    """The effect boundary is the whole reason phases 4-6 of the upstream skill were not adopted.

    Upstream `gh-issues` spawns workers that branch, commit and open pull requests. This adaptation
    took phases 1-3 only. If `permitted_effects` ever becomes non-empty while the skill still
    describes itself as read-only, the boundary moved silently.
    """
    for entry in entries():
        if entry["skill_id"] != "council.issue-intake":
            continue
        assert entry["permitted_effects"] == [], (
            f"council.issue-intake declares effects {entry['permitted_effects']}. It is adopted as "
            f"read-only intake; an effect here means phases 4-6 arrived without the ladder advancing."
        )
        assert entry["risk_ceiling"] == "R0"


def test_the_instruction_digest_matches_the_skill_document():
    """A digest that does not track its document is a digest of something that no longer exists."""
    for entry in entries():
        if entry["skill_id"] != "council.issue-intake":
            continue
        actual = "sha256:" + hashlib.sha256(SKILL_DOC.read_bytes()).hexdigest()
        assert entry["instruction_digest"] == actual, (
            f"instruction_digest is stale.\n  recorded: {entry['instruction_digest']}\n"
            f"  actual:   {actual}\nThe skill document changed and the registry did not."
        )
