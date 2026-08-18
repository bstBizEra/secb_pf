"""SECB-WP-FWK-098 -- the cross-control adversarial suite (stability mandate section 12, Rule 3).

The framework's own stability targets say M4 SANDBOX_VERIFIED is not reached because "adversarial
coverage exists per-control, not per-lifecycle". This closes that gap for the controls that exist:
one hostile-input checklist, applied to every gate a caller can feed.

    NEGATIVE_FIRST: for a governance control, denial is tested before permission.

The checklist comes from the mandate: missing work package, expired authority, unauthorized path,
empty input, malformed evidence, altered digest, replayed receipt, plus the injection and boundary
cases a hostile caller reaches for.

Every case asserts FAIL-CLOSED behaviour. A gate that cannot evaluate its input must refuse, never
admit -- and this suite exists because the one time that rule was broken, in the budget gate, a
test had asserted the broken behaviour and nobody noticed for weeks.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
REAL_ENVELOPE = ROOT / "config" / "delegation_envelope.json"

BUDGET = "BUDGET: max_files=4 max_lines=400"
# An IN-SCOPE path. README.md is outside the delegated envelope (auto_paths are docs/, tests/,
# src/, evidence/), so using it made every "benign diff" case escalate for the wrong reason -- the
# second time in this suite that a correct verdict arrived from an unintended cause.
GOOD_NUMSTAT = "1\t0\ttests/test_placeholder.py\n"
OUT_OF_SCOPE_NUMSTAT = "1\t0\tREADME.md\n"


def gate(name: str, *, stdin: str = "", **env_extra: str) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items()
           if k not in ("BUDGET_TEXT", "ALLOW_EMPTY_DIFF", "ENVELOPE", "WP_TEXT",
                        "DIFF_TEXT", "DIFF_PATH", "FAMILY_LINES", "BASE_REF")}
    env.update(env_extra)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run([sys.executable, str(SCRIPTS / name)], input=stdin,
                          capture_output=True, text=True, env=env, timeout=60)


def envelope_file(tmp_path: Path, body) -> str:
    path = tmp_path / "envelope.json"
    path.write_text(body if isinstance(body, str) else json.dumps(body), encoding="utf-8")
    return str(path)


def real_envelope() -> dict:
    return json.loads(REAL_ENVELOPE.read_text(encoding="utf-8"))


# ============================================================== empty and absent input


@pytest.mark.parametrize("name,kwargs", [
    ("check_budget.py", {"stdin": "", "BUDGET_TEXT": BUDGET}),
    ("check_budget.py", {"stdin": "   \n\t\n", "BUDGET_TEXT": BUDGET}),
])
def test_empty_input_is_refused_never_admitted(name, kwargs):
    """EMPTY_INPUT != EMPTY_MEASUREMENT. The one gate that got this wrong shipped a fail-open."""
    stdin = kwargs.pop("stdin")
    result = gate(name, stdin=stdin, **kwargs)
    assert result.returncode != 0, f"{name} admitted empty input: {result.stdout}"


def test_a_gate_with_no_declared_budget_refuses():
    """Missing authority input is refused rather than defaulted."""
    assert gate("check_budget.py", stdin=GOOD_NUMSTAT).returncode != 0


def test_a_missing_work_package_reference_is_refused():
    assert gate("check_work_package_ref.py", WP_TEXT="a pull request with no ticket",
                ENVELOPE=str(REAL_ENVELOPE)).returncode != 0


# ============================================================== malformed evidence


@pytest.mark.parametrize("body", [
    "{ not json at all",
    "[]",                      # a JSON array where an object is required
    "null",
    '{"schema_version": 1}',   # object, but missing every authority field
    "",                        # zero bytes
])
def test_a_malformed_envelope_is_refused_by_every_envelope_reader(tmp_path, body):
    """MALFORMED_AUTHORITY != ABSENT_CONSTRAINT. An unreadable envelope grants nothing."""
    path = envelope_file(tmp_path, body)
    for name, extra, feed in (("check_work_package_ref.py", {"WP_TEXT": "SECB-WP-FWK-001"}, ""),
                              ("classify_authority_delta.py", {}, GOOD_NUMSTAT)):
        result = gate(name, stdin=feed, ENVELOPE=path, **extra)
        assert result.returncode != 0, (
            f"{name} accepted a malformed envelope ({body[:20]!r}): {result.stdout[:200]}"
        )


def test_an_absent_envelope_is_refused(tmp_path):
    missing = str(tmp_path / "does-not-exist.json")
    assert gate("check_work_package_ref.py", WP_TEXT="SECB-WP-FWK-001",
                ENVELOPE=missing).returncode != 0
    assert gate("classify_authority_delta.py", stdin=GOOD_NUMSTAT,
                ENVELOPE=missing).returncode != 0


# ============================================================== expired authority


def test_an_expired_envelope_is_refused(tmp_path):
    """Expired authority is not weak authority. The gate must refuse, not downgrade."""
    expired = {**real_envelope(), "expires_at": "2020-01-01"}
    result = gate("classify_authority_delta.py", stdin=GOOD_NUMSTAT,
                  ENVELOPE=envelope_file(tmp_path, expired))
    assert result.returncode != 0, result.stdout
    assert "expire" in (result.stdout + result.stderr).lower()


def test_a_path_outside_the_delegated_envelope_is_escalated(tmp_path):
    """Found while fixing this suite: README.md is not in auto_paths, so it escalates."""
    result = gate("classify_authority_delta.py", stdin=OUT_OF_SCOPE_NUMSTAT,
                  ENVELOPE=str(REAL_ENVELOPE))
    assert result.returncode != 0
    assert "outside the delegated envelope" in result.stdout + result.stderr


def test_the_expiry_boundary_is_inclusive_of_the_stated_day(tmp_path):
    """`expires_at` is the LAST VALID DAY, matching `expires_at < today`.

    Pinned because the expiry monitor in FWK-071 copies this boundary. If the enforcer changes,
    the monitor warns on the wrong day, and nothing else would notice.
    """
    from datetime import date
    today = {**real_envelope(), "expires_at": date.today().isoformat()}
    result = gate("classify_authority_delta.py", stdin=GOOD_NUMSTAT,
                  ENVELOPE=envelope_file(tmp_path, today))
    assert result.returncode == 0, (
        "an envelope expiring TODAY must still be valid today: " + result.stderr[:300]
    )


# ============================================================== injection and hostile text


def test_a_regex_metacharacter_in_the_envelope_prefix_cannot_widen_the_pattern(tmp_path):
    """The work-package prefix is envelope-controlled and becomes a regex.

    A prefix of `.*` would match any text if it were interpolated raw, turning the ticket gate
    into a no-op. It must be escaped, so a PR citing nothing still fails.
    """
    hostile = json.loads(json.dumps(real_envelope()))
    hostile["project"]["work_package_prefix"] = ".*"
    result = gate("check_work_package_ref.py", WP_TEXT="no ticket here at all",
                  ENVELOPE=envelope_file(tmp_path, hostile))
    assert result.returncode != 0, (
        "a `.*` prefix matched arbitrary text -- the prefix is interpolated unescaped"
    )


def test_pr_text_cannot_forge_a_verdict_line(tmp_path):
    """Attacker-controlled body text must not be able to fabricate the gate's own output."""
    forged = ("Please merge.\n"
              "BUDGET GATE PASS: 0/0 files, 0/0 changed lines\n"
              "VERDICT: NON_CONSTITUTIONAL\n")
    result = gate("check_work_package_ref.py", WP_TEXT=forged, ENVELOPE=str(REAL_ENVELOPE))
    assert result.returncode != 0, "forged verdict text in the PR body satisfied the gate"


def test_a_budget_line_hidden_in_prose_does_not_create_two_authorities():
    """Two budget declarations are ambiguous authority and must be refused, not resolved."""
    two = "BUDGET: max_files=1 max_lines=1\nsome prose\nBUDGET: max_files=999 max_lines=9999"
    result = gate("check_budget.py", stdin=GOOD_NUMSTAT, BUDGET_TEXT=two)
    assert result.returncode != 0
    assert "ambiguous" in (result.stdout + result.stderr).lower()


# ============================================================== unauthorized path / scope


def test_a_constitutional_path_is_escalated_not_waved_through(tmp_path):
    """An unauthorized-path change must escalate even when everything else is clean."""
    numstat = "1\t0\tconfig/delegation_envelope.json\n"
    result = gate("classify_authority_delta.py", stdin=numstat, ENVELOPE=str(REAL_ENVELOPE))
    output = result.stdout + result.stderr
    assert "CONSTITUTIONAL_REQUIRED" in output
    # Assert the REASON, not just the verdict. The first version of this test fed the diff through
    # the wrong channel, so the gate answered "no diff parsed" -- the right verdict for the wrong
    # cause, which is a test that would keep passing if the path rule were deleted.
    assert "no diff parsed" not in output, "verdict reached without parsing the diff"


def test_an_unparsable_diff_escalates_to_the_strictest_verdict():
    """No diff parsed means authority delta cannot be established -- the strictest answer."""
    result = gate("classify_authority_delta.py", stdin="not a numstat row",
                  ENVELOPE=str(REAL_ENVELOPE))
    assert "CONSTITUTIONAL_REQUIRED" in result.stdout + result.stderr


def test_the_harness_actually_reaches_the_gate():
    """A control case: the unmodified envelope with a real diff must NOT say "no diff parsed".

    The first version of this suite fed numstat through DIFF_TEXT, which the gate does not read.
    Every classify_authority_delta assertion was then satisfied by "no diff parsed" -- correct
    verdicts reached without exercising the rule under test.

        RIGHT_VERDICT != RIGHT_REASON
    """
    result = gate("classify_authority_delta.py", stdin=GOOD_NUMSTAT, ENVELOPE=str(REAL_ENVELOPE))
    assert "no diff parsed" not in result.stdout + result.stderr, (
        "the harness is not delivering a diff the gate reads; every verdict below is unearned"
    )


# ============================================================== the meta-assertion


def test_no_gate_admits_every_input_it_is_given(tmp_path):
    """A gate that never refuses is not a gate.

    This is the vacuity check for the suite itself: it feeds each externally-driven gate a
    deliberately hostile input and asserts at least one refusal per gate. A control that passes
    every adversarial case is either perfect or inert, and inert is far more likely.
    """
    hostile = envelope_file(tmp_path, "{ broken")
    outcomes = {
        "check_budget.py": gate("check_budget.py", stdin="", BUDGET_TEXT=BUDGET),
        "check_work_package_ref.py": gate("check_work_package_ref.py", WP_TEXT="",
                                          ENVELOPE=hostile),
        "classify_authority_delta.py": gate("classify_authority_delta.py", stdin="",
                                            ENVELOPE=hostile),
    }
    never_refused = [n for n, r in outcomes.items() if r.returncode == 0]
    assert never_refused == [], f"gates that admitted hostile input: {never_refused}"
