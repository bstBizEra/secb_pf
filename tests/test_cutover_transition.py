"""The cutover controller refuses what it cannot evidence — `SECB-WP-FWK-080` (#143).

    BUSINESS_DECISION_TO_DISCLOSE ≠ CAPABILITY_AVAILABLE ≠ CONTROL_CONFIGURED
      ≠ CONTROL_VERIFIED ≠ CONTROL_ENFORCED

Every refusal below is produced by **invoking the validator as a subprocess** against a
mutated manifest, and the permitted path is tested too, so no refusal is vacuous.

The controller performs no external effect. These tests therefore prove refusal logic and
nothing about GitHub: whether a ruleset can actually be created is unmeasured here, and
recorded as such.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check_cutover_transition.py"
MANIFEST = REPO_ROOT / "config" / "public_cutover_state.json"

OK = 0
FAIL = 2

CAPABILITIES = ("rulesets", "merge_queue", "artifact_attestations", "archival")


def manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def run(target: str, tmp_path=None, mutate=None, **env_extra) -> subprocess.CompletedProcess:
    data = manifest()
    if mutate:
        mutate(data)
    path = MANIFEST
    if mutate is not None:
        path = tmp_path / "manifest.json"
        path.write_text(json.dumps(data), encoding="utf-8")
    env = {"PATH": "/usr/bin:/bin", "MANIFEST": str(path)}
    env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(SCRIPT), target],
        capture_output=True, text=True, env=env, cwd=str(REPO_ROOT), timeout=30,
    )


# --- the shipped state --------------------------------------------------------


def test_the_manifest_ships_unapproved_and_performs_no_effect():
    data = manifest()
    assert data["lifecycle_state"] == "DISCLOSURE_UNAPPROVED"
    assert "PERFORMS NO EXTERNAL EFFECT" in data["$comment"]
    for name in CAPABILITIES:
        capability = data["capabilities"][name]
        assert capability["live_readback"]["status"] == "NOT_OBSERVED"
        assert capability["verified"] is False
        assert capability["enforced"] is False


def test_every_capability_is_tracked_separately():
    """One capability passing must never raise another.

    They are configured through different surfaces — rulesets, queue settings,
    attestation workflows, archival — and fail independently.
    """
    data = manifest()
    for name in CAPABILITIES:
        assert set(data["capabilities"][name]) >= {
            "configured_intent", "live_readback", "verified", "enforced"
        }, f"{name} does not carry the four separate facts"


# --- ordering ----------------------------------------------------------------


def test_the_first_transition_is_permitted_with_an_approval_reference():
    """The accept path, so the refusals below are not vacuous."""
    result = run("DISCLOSURE_APPROVED", APPROVAL_REF="operator decision 2026-08-15")
    assert result.returncode == OK, result.stderr
    assert "PERMITTED" in result.stdout


def test_skipping_a_state_is_refused(tmp_path):
    result = run("VISIBILITY_PUBLIC")
    assert result.returncode == FAIL
    assert "skips" in result.stderr


def test_a_backwards_transition_is_refused(tmp_path):
    result = run(
        "DISCLOSURE_UNAPPROVED", tmp_path,
        lambda d: d.update(lifecycle_state="VISIBILITY_PUBLIC"),
    )
    assert result.returncode == FAIL
    assert "does not advance" in result.stderr
    assert "disclosure is not undone" in result.stderr


@pytest.mark.parametrize("bogus", ["PUBLIC", "DONE", "", "disclosure_approved"])
def test_an_unknown_target_state_is_refused(bogus):
    result = run(bogus)
    assert result.returncode == FAIL
    assert "not a known state" in result.stderr or "no target state" in result.stderr


def test_an_unknown_current_state_is_refused(tmp_path):
    result = run("ORG_TRANSFERRED", tmp_path, lambda d: d.update(lifecycle_state="WHATEVER"))
    assert result.returncode == FAIL
    assert "not a known state" in result.stderr


# --- the transition an executor may never self-authorize ----------------------


def test_disclosure_approval_without_a_human_reference_is_refused():
    """The irreversible one. An executor recording it would manufacture the authority."""
    result = run("DISCLOSURE_APPROVED")
    assert result.returncode == FAIL
    assert "requires APPROVAL_REF" in result.stderr
    assert "secrecy is not restorable" in result.stderr


def test_disclosure_approval_requires_the_credential_prerequisite(tmp_path):
    """A secret still live when logs become public is disclosed, not rotated."""
    result = run(
        "DISCLOSURE_APPROVED", tmp_path,
        lambda d: d["irreversibility"].update(prerequisite="none"),
        APPROVAL_REF="operator decision",
    )
    assert result.returncode == FAIL
    assert "#115" in result.stderr


# --- observation, verification, enforcement ----------------------------------


def test_capabilities_observed_is_refused_while_readback_is_unobserved(tmp_path):
    """Unmeasured is not absent, and not available."""
    def advance(d):
        d["lifecycle_state"] = "VISIBILITY_PUBLIC"
    result = run("CAPABILITIES_OBSERVED", tmp_path, advance)
    assert result.returncode == FAIL
    assert "NOT_OBSERVED" in result.stderr
    assert "unmeasured" in result.stderr


def test_configured_intent_does_not_satisfy_verification(tmp_path):
    """The core substitution: intent is not a verified control."""
    def advance(d):
        d["lifecycle_state"] = "CONTROLS_CONFIGURED"
        for name in CAPABILITIES:
            d["capabilities"][name]["configured_intent"] = "required checks on main"
    result = run("CONTROLS_VERIFIED", tmp_path, advance)
    assert result.returncode == FAIL
    assert "Configured intent is not verification" in result.stderr


def test_one_verified_capability_does_not_carry_the_others(tmp_path):
    def advance(d):
        d["lifecycle_state"] = "CONTROLS_CONFIGURED"
        d["capabilities"]["rulesets"]["verified"] = True
    result = run("CONTROLS_VERIFIED", tmp_path, advance)
    assert result.returncode == FAIL
    assert "merge_queue is not verified" in result.stderr


def test_selective_activation_with_nothing_enforced_is_refused(tmp_path):
    def advance(d):
        d["lifecycle_state"] = "CONTROLS_VERIFIED"
    result = run("SELECTIVELY_ACTIVATED", tmp_path, advance)
    assert result.returncode == FAIL
    assert "nothing to activate" in result.stderr


def test_a_producer_may_not_record_a_consumer_stage(tmp_path):
    """`#134`'s boundary, enforced here rather than restated."""
    def advance(d):
        d["transition_evidence"]["CONSUMER_VERIFIED"] = "looks fine to me"
    result = run("DISCLOSURE_APPROVED", tmp_path, advance, APPROVAL_REF="operator decision")
    assert result.returncode == FAIL
    assert "cannot certify" in result.stderr


# --- fail-closed on the manifest itself --------------------------------------


def test_an_absent_manifest_fails_closed():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "DISCLOSURE_APPROVED"],
        capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=30,
        env={"PATH": "/usr/bin:/bin", "MANIFEST": "/nonexistent/manifest.json"},
    )
    assert result.returncode == FAIL
    assert "unreadable or unparseable" in result.stderr


def test_a_malformed_manifest_fails_closed(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text('{"lifecycle_state": "DISCLOSURE_UNAPPROVED"', encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "DISCLOSURE_APPROVED"],
        capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=30,
        env={"PATH": "/usr/bin:/bin", "MANIFEST": str(path)},
    )
    assert result.returncode == FAIL


def test_a_manifest_missing_a_capability_fails_closed(tmp_path):
    def break_it(d):
        d["lifecycle_state"] = "VISIBILITY_PUBLIC"
        del d["capabilities"]["merge_queue"]
    result = run("CAPABILITIES_OBSERVED", tmp_path, break_it)
    assert result.returncode == FAIL
    assert "malformed manifest" in result.stderr


# --- what the controller cites rather than restates --------------------------


def test_the_evidence_lifecycle_is_cited_not_copied():
    """Criterion 4 without a competing definition.

    The stage vocabulary belongs to `secb.pr-input-binding/v1` (#134, unmerged). Copying
    the list here would create a second source that drifts from the first — the defect
    #135 records for parser duplication, one layer up.
    """
    lifecycle = manifest()["evidence_lifecycle"]
    assert lifecycle["restated_here"] is False
    assert "scripts/emit_pr_input_binding.py" in lifecycle["canonical_source"]
    assert "UNMERGED" in lifecycle["canonical_source_state"]
    assert set(lifecycle["producer_may_not_certify"]) == {
        "CONSUMER_VERIFIED", "ENFORCEMENT_APPLIED"
    }


def test_the_referenced_obligations_are_not_closed_by_this_manifest():
    """Pointing at an obligation must not discharge it."""
    obligations = {o["issue"]: o for o in manifest()["independent_obligations"]}
    assert set(obligations) == {117, 118, 119}
    for issue, obligation in obligations.items():
        assert obligation["closed_by_this_manifest"] is False, (
            f"#{issue} must remain open on its own terms"
        )


def test_the_merge_queue_prerequisite_names_the_skipped_checks_defect():
    """Enabling the queue before `ci.yml` handles `merge_group` produces skipped checks."""
    capability = manifest()["capabilities"]["merge_queue"]
    assert "merge_group" in capability["blocking_prerequisite"]
    assert "SKIPPED" in capability["blocking_prerequisite"]
    assert capability["membership_proof"].startswith("NOT_PROVEN")
