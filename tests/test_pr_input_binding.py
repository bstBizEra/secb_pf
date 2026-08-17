"""`scripts/emit_pr_input_binding.py` — `SECB-WP-FWK-068`.

The defect this closes was measured, not hypothesised: Gate 1's log for PR #122 at head
`1a569a9` recorded `AUTHORITY GATE PASS: … SECB-WP-FWK-062` while the pull request now
reads `SECB-WP-FWK-066`. The check stayed green and GitHub showed nothing stale, because
a check is bound to `head_sha` and metadata is not part of it.

Every rejection path below is exercised by invoking the script as a subprocess, not by
importing it. A gate is what it does when run.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "emit_pr_input_binding.py"

OK = 0
FAIL = 2

BASE_ENV = {
    "PR_TITLE": "SECB-WP-FWK-068: bind a check to the metadata it evaluated",
    "PR_BODY": "Closes #127.\n\nBUDGET: max_files=4 max_lines=600\n\nBody text.",
    "HEAD_SHA": "5caad30f34be26dfae16731be1344e44a97928f2",
    "BASE_SHA": "f1b2516012dc69492a8a2480ea75d29a83f4def0",
}


def run(env: dict, *args: str) -> subprocess.CompletedProcess:
    full = {"PATH": "/usr/bin:/bin", "ENVELOPE": str(REPO_ROOT / "config" / "delegation_envelope.json")}
    full.update(env)
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, env=full, cwd=str(REPO_ROOT), timeout=30,
    )


def emit(env: dict) -> dict:
    result = run(env)
    assert result.returncode == OK, result.stderr
    return json.loads(result.stdout)


def actions_env(tmp_path, env: dict | None = None, **payload_overrides) -> dict:
    """A full, self-consistent Actions context — the only mode that yields evidence.

    Writes a real event payload and points `GITHUB_EVENT_PATH` at it, because the
    emitter re-reads and compares it. Runner variables are provenance, not attestation:
    a test that only set the variables would be asserting the weaker property.
    """
    env = dict(env or BASE_ENV)
    payload = {
        "pull_request": {
            "title": env["PR_TITLE"],
            "body": env.get("PR_BODY", ""),
            "head": {"sha": env["HEAD_SHA"]},
            "base": {"sha": env["BASE_SHA"]},
        }
    }
    for key, value in payload_overrides.items():
        if key == "drop_pull_request":
            payload.pop("pull_request")
        elif key in ("title", "body"):
            payload["pull_request"][key] = value
        elif key in ("head", "base"):
            payload["pull_request"][key] = {"sha": value}
    path = tmp_path / "event.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    env.update({
        "GITHUB_ACTIONS": "true",
        "GITHUB_EVENT_NAME": "pull_request",
        "GITHUB_EVENT_PATH": str(path),
    })
    return env


# --- emission ----------------------------------------------------------------


def test_binding_carries_every_field_the_decision_context_depends_on():
    binding = emit(BASE_ENV)
    for field in (
        "schema", "head_sha", "base_sha", "title_digest", "body_digest",
        "work_package_id", "budget_digest", "merge_method", "expected_commit_subject",
    ):
        assert field in binding, f"the binding omits {field!r}"
    assert binding["schema"] == "secb.pr-input-binding/v1"
    assert binding["work_package_id"] == "SECB-WP-FWK-068", (
        "the work-package ID must be parsed from the metadata, since that is the input "
        "Gate 1 actually reads"
    )


def test_the_squash_subject_is_bound_because_it_lands_on_main():
    binding = emit({**BASE_ENV, "PR_TITLE": "  spaced   title\t here  "})
    assert binding["expected_commit_subject"] == "spaced title here"


def test_budget_digest_is_null_when_no_budget_is_declared():
    binding = emit({**BASE_ENV, "PR_BODY": "No declaration here."})
    assert binding["budget_digest"] is None, (
        "an absent declaration must be visibly absent, not digested as empty text"
    )


def test_a_title_edit_changes_the_binding():
    """The whole point: this is what `head_sha` alone cannot see."""
    before = emit(BASE_ENV)
    after = emit({**BASE_ENV, "PR_TITLE": "SECB-WP-FWK-099: something else entirely"})
    assert before["head_sha"] == after["head_sha"], "the head is deliberately unchanged"
    assert before["title_digest"] != after["title_digest"]
    assert before["work_package_id"] != after["work_package_id"]


# --- verification -------------------------------------------------------------


def test_verify_refuses_a_local_diagnostic_record(tmp_path):
    """`--verify` is a normative consumer, so it must reject a diagnostic record.

    Same schema name, same fields, no event binding. If verification accepted it, the
    two modes would collapse and the classification would be decoration.
    """
    recorded = tmp_path / "local.json"
    recorded.write_text(json.dumps(emit(BASE_ENV)), encoding="utf-8")
    result = run(actions_env(tmp_path), "--verify", str(recorded))
    assert result.returncode == FAIL
    assert "EVIDENCE_NOT_CONSUMABLE" in result.stderr


def test_verify_passes_when_the_live_pull_request_still_matches(tmp_path):
    env = actions_env(tmp_path)
    recorded = tmp_path / "binding.json"
    recorded.write_text(json.dumps(emit(env)), encoding="utf-8")
    result = run(env, "--verify", str(recorded))
    assert result.returncode == OK, result.stderr
    assert "CHECK_CURRENT PASS" in result.stdout


@pytest.mark.parametrize(
    "key,value,term",
    [
        ("PR_TITLE", "SECB-WP-FWK-068: a different title", "title_digest"),
        ("PR_BODY", "BUDGET: max_files=4 max_lines=600\ndifferent body", "body_digest"),
        ("HEAD_SHA", "0000000000000000000000000000000000000000", "head_sha"),
        ("BASE_SHA", "1111111111111111111111111111111111111111", "base_sha"),
        ("PR_BODY", "Closes #127.\n\nBUDGET: max_files=99 max_lines=9999\n\nBody text.", "budget_digest"),
    ],
)
def test_verify_fails_and_names_the_term_that_changed(tmp_path, key, value, term):
    """`base_sha` is in this list on purpose.

    Retargeting a pull request changes the diff under review without touching the head,
    so a binding over the head alone would call that unchanged.
    """
    env = actions_env(tmp_path)
    recorded = tmp_path / "binding.json"
    recorded.write_text(json.dumps(emit(env)), encoding="utf-8")
    changed = actions_env(tmp_path, env={**BASE_ENV, key: value})
    result = run(changed, "--verify", str(recorded))
    assert result.returncode == FAIL
    assert "CHECK_CURRENT FAIL" in result.stderr
    assert term in result.stderr, (
        f"the failure must name {term!r} — 'something changed' does not tell a reader "
        f"what to re-check. Got: {result.stderr}"
    )


# --- fail-closed ---------------------------------------------------------------


@pytest.mark.parametrize("absent", ["PR_TITLE", "HEAD_SHA", "BASE_SHA"])
def test_absent_required_input_fails_closed(absent):
    env = {k: v for k, v in BASE_ENV.items() if k != absent}
    result = run(env)
    assert result.returncode == FAIL
    assert "BINDING FAIL (closed)" in result.stderr
    assert absent in result.stderr


def test_an_empty_body_is_legitimate_and_not_a_failure():
    """Absence of a body is not absence of an input — it is an input whose value is empty."""
    binding = emit({**BASE_ENV, "PR_BODY": ""})
    assert binding["body_digest"].startswith("sha256:")


def test_unreadable_recorded_binding_fails_closed(tmp_path):
    result = run(BASE_ENV, "--verify", str(tmp_path / "does-not-exist.json"))
    assert result.returncode == FAIL
    assert "BINDING FAIL (closed)" in result.stderr


def test_verify_without_a_path_fails_closed():
    result = run(BASE_ENV, "--verify")
    assert result.returncode == FAIL


def test_unreadable_envelope_fails_closed():
    """Inherited from `load_prefix`, which is reused rather than reimplemented."""
    result = run({**BASE_ENV, "ENVELOPE": "/nonexistent/envelope.json"})
    assert result.returncode == FAIL
    assert "BINDING FAIL (closed)" in result.stderr


# --- subject scope (#127 disposition) -----------------------------------------


def test_the_binding_names_the_only_subject_it_can_describe():
    binding = emit(BASE_ENV)
    assert binding["subject_kind"] == "PULL_REQUEST"
    assert binding["supported_event"] == "pull_request"
    assert binding["merge_group_compatible"] is False, (
        "one head, one base, one title, one budget — a merge group is an ordered set of "
        "pull requests plus a synthesized head, and widening these fields to take a list "
        "would give one schema two meanings"
    )


@pytest.mark.parametrize("event", ["merge_group", "push", "schedule", "workflow_dispatch"])
def test_a_non_pull_request_event_is_refused_rather_than_stamped(event):
    """Schema laundering: PR-shaped inputs must not buy this schema's provenance.

    A merge-group runner can populate `PR_TITLE` and `HEAD_SHA` from a queue entry. If
    the emitter stamped that, the binding would assert a subject the event never
    supplied. Refusing is correct — the group has its own envelope, tracked on #118.
    """
    result = run({**BASE_ENV, "GITHUB_EVENT_NAME": event})
    assert result.returncode == FAIL
    assert "UNSUPPORTED_SUBJECT" in result.stderr
    assert event in result.stderr


# --- two execution modes (#127 provenance contract) ---------------------------


def test_a_full_actions_context_is_event_bound_and_consumable(tmp_path):
    """The accept path, so every refusal below is non-vacuous."""
    binding = emit(actions_env(tmp_path))
    context = binding["execution_context"]
    assert context["mode"] == "GITHUB_ACTIONS_EVENT_BOUND"
    assert context["event_payload_consistent"] is True
    assert context["event_payload_digest"].startswith("sha256:")
    assert binding["eligible_for_normative_consumption"] is True


def test_a_local_run_is_diagnostic_and_not_consumable():
    """Usable for diagnosis, refused as evidence — the hole from the previous round.

    Previously an unset event was permitted and merely *declared* as a gap. A declared
    gap is still a gap: the record carried the same schema name and nothing marked it
    unusable. It is now classified and flagged instead.
    """
    binding = emit(BASE_ENV)
    assert binding["execution_context"]["mode"] == "LOCAL_DIAGNOSTIC"
    assert binding["eligible_for_normative_consumption"] is False
    assert binding["execution_context"]["event_payload_digest"] is None


@pytest.mark.parametrize("present", ["GITHUB_ACTIONS", "GITHUB_EVENT_PATH"])
def test_a_partial_actions_context_is_refused_not_downgraded(present):
    """Refused, not silently treated as local.

    Downgrading would hand a caller a diagnostic record while the run looked event-bound,
    which is the laundering shape one level up.
    """
    result = run({**BASE_ENV, present: "true" if present == "GITHUB_ACTIONS" else "/tmp/x"})
    assert result.returncode == FAIL
    assert "INVALID_ACTIONS_CONTEXT" in result.stderr


def test_actions_false_with_a_payload_is_refused(tmp_path):
    env = actions_env(tmp_path)
    env["GITHUB_ACTIONS"] = "false"
    result = run(env)
    assert result.returncode == FAIL
    assert "GITHUB_ACTIONS is not true" in result.stderr


def test_an_unreadable_event_payload_fails_closed(tmp_path):
    env = actions_env(tmp_path)
    env["GITHUB_EVENT_PATH"] = str(tmp_path / "absent.json")
    result = run(env)
    assert result.returncode == FAIL
    assert "unreadable or unparseable" in result.stderr


def test_a_payload_without_a_pull_request_object_fails_closed(tmp_path):
    result = run(actions_env(tmp_path, drop_pull_request=True))
    assert result.returncode == FAIL
    assert "no pull_request object" in result.stderr


@pytest.mark.parametrize("field,value", [
    ("title", "SECB-WP-FWK-999: a title the event never carried"),
    ("body", "a body the event never carried"),
    ("head", "9999999999999999999999999999999999999999"),
    ("base", "8888888888888888888888888888888888888888"),
])
def test_a_payload_inconsistent_with_the_bound_values_fails_closed(tmp_path, field, value):
    """Runner variables are provenance, not attestation.

    Anyone with shell access can set `GITHUB_ACTIONS=true`. What cannot be faked as
    cheaply is a payload that agrees with the values being bound, so the payload is
    re-read and compared field by field.
    """
    result = run(actions_env(tmp_path, **{field: value}))
    assert result.returncode == FAIL
    assert "INVALID_ACTIONS_CONTEXT" in result.stderr
    assert field in result.stderr


def test_eligibility_is_not_consumption(tmp_path):
    """The producer states a property; it may not state a consumer's act.

    `evidence_consumable: true` read as *"this has been consumed"*. It never could be:
    the emitter runs before any consumer exists, and none exists at all. The record now
    carries its lifecycle position and names the stages it has not reached.
    """
    binding = emit(actions_env(tmp_path))
    assert binding["eligible_for_normative_consumption"] is True
    assert "evidence_consumable" not in binding, (
        "the old name asserted a consumer state the producer cannot observe"
    )

    lifecycle = binding["evidence_lifecycle"]
    assert lifecycle["reached"] == ["GENERATED", "CONTEXT_VALIDATED"]
    for stage in ("PERSISTED", "ADDRESSABLE", "INTEGRITY_BOUND",
                  "CONSUMER_VERIFIED", "ENFORCEMENT_APPLIED"):
        assert stage in lifecycle["not_reached"], f"{stage} must be declared unreached"
        assert lifecycle["not_reached"][stage], f"{stage} must say why"
    assert set(lifecycle["producer_may_not_certify"]) == {
        "CONSUMER_VERIFIED", "ENFORCEMENT_APPLIED"
    }


def test_no_stage_is_inferred_from_the_one_before_it(tmp_path):
    """A log line is not a receipt; a digest is not a signer; verified is not enforced."""
    lifecycle = emit(actions_env(tmp_path))["evidence_lifecycle"]
    assert "step log" in lifecycle["not_reached"]["PERSISTED"]
    assert "verified signer" in lifecycle["not_reached"]["INTEGRITY_BOUND"]
    assert "no merge is denied" in lifecycle["not_reached"]["ENFORCEMENT_APPLIED"]


def test_binding_declares_what_it_does_not_prove():
    """Emission enables readback; it does not perform it, and no consumer requires it."""
    binding = emit(BASE_ENV)
    assert any("LOCAL_DIAGNOSTIC" in item for item in binding["not_proven"])
    assert any("attestation" in item for item in binding["not_proven"])
    assert any("consumption is an act of a consumer" in item for item in binding["not_proven"])
    assert binding["not_proven"], "the binding must state the claims it does not support"
    assert any("--verify" in item for item in binding["not_proven"])
