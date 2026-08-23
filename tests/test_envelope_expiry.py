"""SECB-WP-FWK-071 -- delegation-envelope expiry early warning (issue #130).

Every case invokes scripts/check_envelope_expiry.py as a subprocess, and the accept path runs
against the REAL envelope, so the suite fails if the shipped envelope stops being parseable.

The boundary cases are the point. A monitor is only useful if it agrees with the gate that
actually blocks work, so `test_the_last_valid_day_is_not_expired` pins the inclusivity copied
from `classify_authority_delta.py`: expired STRICTLY AFTER expires_at.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "scripts" / "check_envelope_expiry.py"
REAL_ENVELOPE = ROOT / "config" / "delegation_envelope.json"
REAL_THRESHOLDS = ROOT / "config" / "envelope_expiry_thresholds.json"

EXPIRY = "2026-11-08"


def write(tmp_path: Path, envelope: dict | str | None = None,
          thresholds: dict | str | None = None) -> Path:
    root = tmp_path / "repo"
    (root / "config").mkdir(parents=True, exist_ok=True)
    if envelope is not None:
        body = envelope if isinstance(envelope, str) else json.dumps(envelope)
        (root / "config" / "delegation_envelope.json").write_text(body, encoding="utf-8")
    default = json.loads(REAL_THRESHOLDS.read_text(encoding="utf-8"))
    body = thresholds if isinstance(thresholds, str) else json.dumps(
        default if thresholds is None else {**default, **thresholds})
    (root / "config" / "envelope_expiry_thresholds.json").write_text(body, encoding="utf-8")
    return root


def run(root: Path, at: str | None = None, **extra: str) -> subprocess.CompletedProcess:
    # The subject is NAMED, never defaulted -- the gate refuses an unnamed envelope, so every
    # case here says which one it means. `**extra` comes last so a case can override it, and
    # `ENVELOPE=""` is how a case asks for the absent-subject path.
    env = {**os.environ, "REPO_ROOT": str(root), "PYTHONDONTWRITEBYTECODE": "1",
           "ENVELOPE": "config/delegation_envelope.json", **extra}
    if at is not None:
        env["EVALUATE_AT"] = at
    return subprocess.run([sys.executable, str(TOOL)], capture_output=True, text=True,
                          env=env, check=False)


def state_of(result: subprocess.CompletedProcess) -> str:
    return json.loads(result.stdout)["state"]


# ----------------------------------------------------------------- the real envelope


def test_the_shipped_envelope_is_observable():
    """The accept path, against the envelope the repository actually ships."""
    result = run(ROOT)
    report = json.loads(result.stdout)
    assert report["state"] in ("VALID", "RENEWAL_DUE", "CRITICAL", "EXPIRED")
    assert report["expires_at"] == EXPIRY
    assert report["envelope_digest"].startswith("sha256:")
    assert report["threshold_config_digest"].startswith("sha256:")
    assert report["confers_renewal_authority"] is False


# ------------------------------------------------------------------ the state ladder


@pytest.mark.parametrize("at,expected", [
    ("2026-01-01T00:00:00+00:00", "VALID"),          # far out
    ("2026-10-08T00:00:00+00:00", "VALID"),          # 31 days: one outside the window
    ("2026-10-09T00:00:00+00:00", "RENEWAL_DUE"),    # exactly warning_days (30)
    ("2026-11-01T00:00:00+00:00", "CRITICAL"),       # exactly critical_days
    ("2026-11-02T00:00:00+00:00", "CRITICAL"),       # inside critical
    ("2026-11-08T00:00:00+00:00", "CRITICAL"),       # last valid day: 0 days remain
    ("2026-11-09T00:00:00+00:00", "EXPIRED"),        # strictly after
])
def test_the_state_ladder_at_each_boundary(tmp_path, at, expected):
    root = write(tmp_path, {"expires_at": EXPIRY})
    assert state_of(run(root, at)) == expected


def test_the_last_valid_day_is_not_expired(tmp_path):
    """Inclusivity is copied from the enforcer, and this is the test that pins it.

    `classify_authority_delta.py` refuses only when `expires_at < today`, so the expiry date is
    the last valid day. A monitor that called it expired one day early would warn on the wrong
    day, and a reader calibrated on the monitor would be wrong exactly at the boundary.
    """
    root = write(tmp_path, {"expires_at": EXPIRY})
    report = json.loads(run(root, f"{EXPIRY}T23:59:59+00:00").stdout)
    assert report["state"] != "EXPIRED"
    assert report["days_remaining"] == 0


def test_days_remaining_is_counted_in_utc_not_local(tmp_path):
    """An instant late on one UTC day and an instant early on the next differ by a day."""
    root = write(tmp_path, {"expires_at": EXPIRY})
    late = json.loads(run(root, "2026-11-01T23:30:00+00:00").stdout)["days_remaining"]
    early = json.loads(run(root, "2026-11-02T00:30:00+00:00").stdout)["days_remaining"]
    assert late == 7 and early == 6


def test_a_naive_evaluation_instant_is_refused(tmp_path):
    """Ambiguity is the one thing a date-boundary check cannot tolerate."""
    root = write(tmp_path, {"expires_at": EXPIRY})
    result = run(root, "2026-11-02T00:30:00")
    assert result.returncode == 2
    assert state_of(result) == "OBSERVATION_INCOMPLETE"
    assert "ambiguous" in result.stdout


# ------------------------------------------------------------------- fail-closed


@pytest.mark.parametrize("envelope,fragment", [
    ({"schema_version": 1}, "declares no expires_at"),
    ({"expires_at": "not-a-date"}, "not an ISO-8601 date"),
    ({"expires_at": None}, "declares no expires_at"),
    ("{ this is not json", "not parseable JSON"),
])
def test_an_unobservable_envelope_is_incomplete_never_valid(tmp_path, envelope, fragment):
    root = write(tmp_path, envelope)
    result = run(root, "2026-01-01T00:00:00+00:00")
    assert result.returncode == 2
    assert state_of(result) == "OBSERVATION_INCOMPLETE"
    assert fragment in result.stdout
    assert json.loads(result.stdout)["days_remaining"] is None


def test_a_missing_envelope_is_incomplete(tmp_path):
    root = write(tmp_path, envelope=None)
    result = run(root, "2026-01-01T00:00:00+00:00")
    assert result.returncode == 2
    assert state_of(result) == "OBSERVATION_INCOMPLETE"


def test_unreadable_thresholds_do_not_yield_a_threshold_verdict(tmp_path):
    """No threshold file, no threshold-derived state -- not a default that looks like one."""
    root = write(tmp_path, {"expires_at": EXPIRY}, thresholds="{ broken")
    result = run(root, "2026-01-01T00:00:00+00:00")
    assert result.returncode == 2
    assert state_of(result) == "OBSERVATION_INCOMPLETE"


@pytest.mark.parametrize("bad", [
    {"warning_days": -1}, {"critical_days": "7"}, {"warning_days": True},
])
def test_a_malformed_threshold_is_refused(tmp_path, bad):
    root = write(tmp_path, {"expires_at": EXPIRY}, bad)
    assert state_of(run(root, "2026-01-01T00:00:00+00:00")) == "OBSERVATION_INCOMPLETE"


def test_critical_wider_than_warning_is_refused(tmp_path):
    """An inverted ladder would report a LESS urgent state as expiry approaches."""
    root = write(tmp_path, {"expires_at": EXPIRY},
                 {"warning_days": 7, "critical_days": 30})
    result = run(root, "2026-01-01T00:00:00+00:00")
    assert result.returncode == 2
    assert "would fire before RENEWAL_DUE" in result.stdout


def test_an_unknown_fail_state_is_refused(tmp_path):
    root = write(tmp_path, {"expires_at": EXPIRY}, {"fail_states": ["PANIC"]})
    assert state_of(run(root, "2026-01-01T00:00:00+00:00")) == "OBSERVATION_INCOMPLETE"


# --------------------------------------------------------------- exit-code policy


def test_expired_and_critical_are_non_success(tmp_path):
    root = write(tmp_path, {"expires_at": EXPIRY})
    assert run(root, "2026-11-09T00:00:00+00:00").returncode == 2   # EXPIRED
    assert run(root, "2026-11-05T00:00:00+00:00").returncode == 2   # CRITICAL


def test_valid_and_renewal_due_are_success(tmp_path):
    root = write(tmp_path, {"expires_at": EXPIRY})
    assert run(root, "2026-01-01T00:00:00+00:00").returncode == 0   # VALID
    assert run(root, "2026-10-15T00:00:00+00:00").returncode == 0   # RENEWAL_DUE


def test_fail_states_are_configuration_not_a_constant(tmp_path):
    """Removing CRITICAL from the config follows the work package literally, and works."""
    root = write(tmp_path, {"expires_at": EXPIRY},
                 {"fail_states": ["EXPIRED", "OBSERVATION_INCOMPLETE"]})
    result = run(root, "2026-11-05T00:00:00+00:00")
    assert state_of(result) == "CRITICAL"
    assert result.returncode == 0


# ------------------------------------------------------- digests and read-only-ness


def test_the_digest_changes_when_the_envelope_or_thresholds_change(tmp_path):
    base = write(tmp_path, {"expires_at": EXPIRY})
    first = json.loads(run(base, "2026-01-01T00:00:00+00:00").stdout)

    moved = write(tmp_path / "b", {"expires_at": "2026-12-01"})
    second = json.loads(run(moved, "2026-01-01T00:00:00+00:00").stdout)
    assert second["envelope_digest"] != first["envelope_digest"]
    assert second["threshold_config_digest"] == first["threshold_config_digest"]

    retuned = write(tmp_path / "c", {"expires_at": EXPIRY}, {"warning_days": 45})
    third = json.loads(run(retuned, "2026-01-01T00:00:00+00:00").stdout)
    assert third["envelope_digest"] == first["envelope_digest"]
    assert third["threshold_config_digest"] != first["threshold_config_digest"]


def test_the_monitor_never_writes_to_the_envelope(tmp_path):
    """It observes. `no job may modify expires_at`, so the bytes must be identical after."""
    root = write(tmp_path, {"expires_at": EXPIRY})
    target = root / "config" / "delegation_envelope.json"
    before = target.read_bytes()
    run(root, "2026-11-09T00:00:00+00:00")
    assert target.read_bytes() == before


def test_the_report_confers_no_renewal_authority(tmp_path):
    root = write(tmp_path, {"expires_at": EXPIRY})
    result = run(root, "2026-11-05T00:00:00+00:00")
    assert json.loads(result.stdout)["confers_renewal_authority"] is False
    assert "renewal is a human decision" in result.stderr


# ------------------------------------------------------------------- the workflow


def test_the_workflow_is_scheduled_read_only_and_never_automatic_on_activity():
    """The trigger surface is the control: a clock and a manual dispatch, nothing else."""
    text = (ROOT / ".github" / "workflows" / "envelope-expiry-monitor.yml").read_text(
        encoding="utf-8")
    assert "schedule:" in text and "workflow_dispatch:" in text
    assert "\n  push:" not in text and "\n  pull_request:" not in text
    assert "permissions:\n  contents: read" in text
    assert "id-token" not in text


def test_the_workflow_reraises_the_evaluation_status():
    """A failure to publish the summary must not convert the evaluation to a pass."""
    text = (ROOT / ".github" / "workflows" / "envelope-expiry-monitor.yml").read_text(
        encoding="utf-8")
    assert 'exit "$STATUS"' in text
    assert "if: always()" in text
    # An absent status must not read as success.
    assert 'if [ -z "$STATUS" ]' in text


def test_an_unnamed_envelope_is_refused_rather_than_defaulted(tmp_path):
    """An absent subject must not resolve to the repository's own envelope.

    The gate used to default to `config/delegation_envelope.json`. Every real caller wanted
    exactly that file, which is what made the default dangerous rather than convenient: a caller
    that MEANT to name an envelope and failed to -- a renamed variable, an edited workflow --
    was handed `state: VALID, days_remaining: 78` about a file it never asked about, with nothing
    in the output to distinguish that from an answer to its actual question.

        ABSENT_SUBJECT != DEFAULTED_SUBJECT

    Paired deliberately, because a refusal alone would also be produced by a broken fixture and
    would prove nothing: the same root with the subject NAMED must succeed, which is what makes
    the refusal attributable to the absence rather than to an unusable environment.
    """
    root = write(tmp_path, {"expires_at": EXPIRY})

    named = run(root, at="2026-01-01T00:00:00+00:00")
    assert named.returncode == 0, (
        f"the paired success arm failed, so this fixture cannot prove anything about absence:\n"
        f"{named.stdout}\n{named.stderr}"
    )
    assert state_of(named) == "VALID"

    unnamed = run(root, at="2026-01-01T00:00:00+00:00", ENVELOPE="")
    assert unnamed.returncode != 0, (
        "the gate exited 0 with no envelope named. It measured SOMETHING and called it VALID, "
        "which is the confident-wrong-answer this refusal exists to prevent."
    )
    assert state_of(unnamed) == "OBSERVATION_INCOMPLETE"
    assert "no envelope was named" in unnamed.stderr
