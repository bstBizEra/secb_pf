"""Negative-first contract tests for the BADF registry validator (FWK-136).

Every test here mutates the committed tree, asserts a refusal, and restores in a
`finally`. A test that only proves the fixture is a failure, so each mutation is
applied to the real registry files rather than to a synthetic copy, and the
suite's own restoration is asserted at the end.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_badf_registry.py"
RECORD = ROOT / "badf" / "admissions" / "addyosmani-agent-skills.json"
REFUSE = 2


def run(mode: str = "all") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), mode],
        capture_output=True, text=True, cwd=ROOT,
    )


def mutate(path: Path, change) -> subprocess.CompletedProcess[str]:
    original = path.read_text(encoding="utf-8")
    document = json.loads(original)
    change(document)
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    try:
        return run()
    finally:
        path.write_text(original, encoding="utf-8")


def test_the_committed_tree_passes():
    """The control. Without it, every refusal below could be a broken script."""
    result = run()
    assert result.returncode == 0, result.stderr


def test_readiness_reports_engineering_ready_and_names_what_is_unmet():
    payload = json.loads(run("readiness").stdout)
    assert payload["readiness"] == "ENGINEERING_READY"
    unmet = " ".join(payload["unmet"])
    assert "AUTHORITY" in unmet and "PRODUCTION" in unmet


def test_readiness_cannot_report_ready_without_substrate():
    """False-READY is the failure this computation exists to prevent."""
    target = ROOT / "schemas" / "badf-session-checkpoint.schema.json"
    original = target.read_text(encoding="utf-8")
    target.unlink()
    try:
        payload = json.loads(run("readiness").stdout)
        assert payload["readiness"] == "NOT_READY"
    finally:
        target.write_text(original, encoding="utf-8")


@pytest.mark.parametrize(
    "registry,weakened",
    [("skill-registry.json", "allow"),
     ("mcp-registry.json", "allow"),
     ("tool-registry.json", "allow-mutation")],
)
def test_a_weakened_registry_posture_is_refused(registry, weakened):
    result = mutate(ROOT / "badf" / registry,
                    lambda d: d.__setitem__("default_policy", weakened))
    assert result.returncode == REFUSE
    assert "default_policy" in result.stderr


def test_a_moving_branch_is_not_accepted_as_provenance():
    """Standard 4.1: an unpinned reference is not production provenance."""
    result = mutate(RECORD, lambda d: d.__setitem__("upstream_commit", "main"))
    assert result.returncode == REFUSE
    assert "immutable" in result.stderr


def test_an_unknown_license_is_blocking():
    result = mutate(RECORD, lambda d: d.__setitem__("license_decision", "UNKNOWN"))
    assert result.returncode == REFUSE
    assert "UNKNOWN" in result.stderr


def test_an_undeclared_capability_class_is_refused():
    """Standard 4.4: undeclared capability is denied by default."""
    result = mutate(RECORD, lambda d: d["declared_capabilities"].pop("credentials"))
    assert result.returncode == REFUSE
    assert "credentials" in result.stderr


@pytest.mark.parametrize("state", ["ADMITTED", "APPROVED", "ACTIVATED"])
def test_claiming_admission_while_checks_are_unperformed_is_refused(state):
    """The record honestly says NOT_PERFORMED; the state must not outrun it."""
    result = mutate(RECORD, lambda d: d.__setitem__("lifecycle_state", state))
    assert result.returncode == REFUSE
    assert "NOT_PERFORMED" in result.stderr or "not a PASS" in result.stderr


def test_an_admitted_record_still_needs_a_verified_rollback():
    def change(document):
        document["lifecycle_state"] = "ADMITTED"
        for key in ("prompt_injection_assessment", "supply_chain_assessment",
                    "routing_tests"):
            document[key]["performed"] = True
            document[key]["outcome"] = "PASS"
    result = mutate(RECORD, change)
    assert result.returncode == REFUSE
    assert "rollback" in result.stderr


def test_activation_while_declaring_no_authority_is_refused():
    """Self-authorisation: activation is not conferred by registration."""
    def change(document):
        document["lifecycle_state"] = "ACTIVATED"
        for key in ("prompt_injection_assessment", "supply_chain_assessment",
                    "routing_tests"):
            document[key]["performed"] = True
            document[key]["outcome"] = "PASS"
        document["rollback"]["verified"] = True
    result = mutate(RECORD, change)
    assert result.returncode == REFUSE
    assert "authority" in result.stderr.lower()


def test_a_registered_skill_without_an_admission_record_is_refused():
    """Section 2: absence of a record is not acceptance."""
    result = mutate(
        ROOT / "badf" / "skill-registry.json",
        lambda d: d["skills"].append({"skill_id": "ghost", "version": "1.0.0"}),
    )
    assert result.returncode == REFUSE
    assert "ghost" in result.stderr


def test_an_unparseable_registry_refuses_rather_than_skipping():
    target = ROOT / "badf" / "mcp-registry.json"
    original = target.read_text(encoding="utf-8")
    target.write_text("{ not json", encoding="utf-8")
    try:
        result = run()
        assert result.returncode == REFUSE
        assert "unparseable" in result.stderr
    finally:
        target.write_text(original, encoding="utf-8")


def test_the_suite_restored_everything_it_mutated():
    """Guards against a test leaving the tree dirty and the next one passing on it."""
    assert run().returncode == 0
