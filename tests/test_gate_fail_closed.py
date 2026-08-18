"""Every workflow-invoked gate refuses absent and malformed input.

WHY THIS EXISTS. SECB-WP-FWK-063 (#163) found that check_budget.py reported
"BUDGET GATE PASS: 0/N files" for a diff that was never computed -- an unreachable base SHA in a
shallow clone produced empty stdin, and empty input read as a clean measurement.

    MEASUREMENT_NOT_PERFORMED != MEASUREMENT_FOUND_NOTHING

That was fixed for one gate. Nothing has ever asserted the property for the others, so the audit
that establishes it has to be re-run by hand and a NEW gate can ship with the same fail-open and
nothing objects. This converts that audit into a standing check.

Measured at the time of writing: all nine invoked gates exit 2 on both empty and malformed stdin
with every gate-related environment variable stripped. This test does not introduce the property;
it pins a property the surface already has, so the day it stops being true is the day CI says so
rather than the day someone thinks to look.

DISCOVERY IS BY EXECUTION PATH, NOT BY FILENAME. The set comes from check_control_graph's
invoked_scripts_in -- the same parser the control-surface completeness guard uses. Deriving it
here with a second glob or regex would create two implementations of "which gates does CI run",
which disagree eventually, and this test would then enforce the weaker one (C-CEG-01). A script
that no workflow invokes is deliberately out of scope: a dormant script cannot fail open.

WHAT THIS DOES NOT COVER, stated because a test's silence reads as coverage.

Gate logic that lives in the WORKFLOW rather than in a script is invisible here. The concurrent
change-family aggregate is computed by shell in ci.yml, reported family=0 for every pull request
this repository has ever produced, and this test would not have caught it (see #190). The
boundary is the process this test can start; a `for` loop over `gh pr list` inside a `run:` block
is not one.

    SCRIPT_FAILS_CLOSED != WORKFLOW_STEP_FAILS_CLOSED

WHAT THE FIRST DRAFT OF THIS FILE GOT WRONG, kept because the correction is the point.

The env-stripped tests below assert only that a gate with NO subject at all refuses. That is a
real property and it is NOT the #163 property. Reinstating the pre-#163 fail-open in
check_budget.py did not fail them: with BUDGET_TEXT stripped, the gate refuses because the budget
DECLARATION is missing, and never reaches the empty-stdin branch at all.

    EXITS_NONZERO != REFUSED_THE_ABSENT_INPUT

A test can pass for a reason adjacent to the one it names. So the load-bearing tests are the
PAIRED ones: each stdin-consuming gate is given a valid environment and a valid subject and must
succeed, then the same environment with an absent subject and must refuse. The success half is
what proves the environment was sufficient, which is what makes the refusal attributable to the
absence rather than to a missing variable.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from check_control_graph import invoked_scripts_in  # noqa: E402

# Every environment variable any gate reads for its subject. Stripped so the input is genuinely
# ABSENT rather than inherited from whatever ran the suite -- the distinction under test.
GATE_ENV = frozenset({
    "BUDGET_TEXT", "BUDGET_BODY_FILE", "BUDGET_BASE_REF", "ALLOW_EMPTY_DIFF",
    "ENVELOPE", "DIFF_TEXT", "DIFF_PATH", "FAMILY_LINES", "BASE_REF",
    "PR_BODY", "PR_TITLE", "WP_TEXT", "BASE_SHA", "HEAD_SHA", "PR_NUMBER",
    "THRESHOLDS", "REPO_ROOT", "EVALUATE_AT", "SNAPSHOT", "ARTIFACT",
})

MALFORMED = "!!! this is not a numstat row !!!\nnor \x01 is this\n"

OK = 0


def invoked() -> list[str]:
    found = sorted(invoked_scripts_in(REPO_ROOT / ".github" / "workflows"))
    assert found, (
        "no invoked scripts were parsed out of .github/workflows -- the workflow shape changed "
        "and this test would silently check nothing"
    )
    return found


def run_gate(script: str, payload: str) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k not in GATE_ENV}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / script)],
        input=payload, capture_output=True, text=True, env=env, cwd=REPO_ROOT, timeout=120,
    )


def test_the_discovered_gate_set_is_not_empty_and_matches_the_manifest():
    # If discovery silently returned a subset, every parametrized test below would pass by
    # checking nothing. Cross-checked against the control surface, which classifies the same set.
    import json

    manifest = json.loads((REPO_ROOT / "config" / "control_surface.json").read_text(encoding="utf-8"))
    accounted = {e["path"] for e in manifest["controls"]} | {
        e["path"] for e in manifest["declared_exclusions"]
    }
    unaccounted = set(invoked()) - accounted
    assert not unaccounted, (
        f"discovery found invoked gates the control surface does not classify: {sorted(unaccounted)}"
    )


@pytest.mark.parametrize("script", invoked())
def test_gate_with_no_subject_at_all_refuses(script):
    result = run_gate(script, "")
    assert result.returncode != OK, (
        f"{script} exited 0 with EMPTY stdin and no subject in the environment. Nothing was "
        f"measured, so success overstates what the gate observed -- the exact defect #163 removed "
        f"from check_budget.py, where absent input read as a clean diff.\n"
        f"  stdout: {result.stdout[:300]!r}\n"
        f"If this gate legitimately has nothing to do without input, it must say so with a "
        f"non-success NOT_APPLICABLE rather than PASS."
    )


@pytest.mark.parametrize("script", invoked())
def test_gate_with_no_subject_refuses_malformed_input(script):
    result = run_gate(script, MALFORMED)
    assert result.returncode != OK, (
        f"{script} exited 0 on input it cannot possibly have parsed. A gate that accepts "
        f"unparseable input has no way to distinguish a clean subject from a broken one.\n"
        f"  stdout: {result.stdout[:300]!r}"
    )


@pytest.mark.parametrize("script", invoked())
def test_gate_says_what_it_could_not_observe(script):
    # Fail-closed is necessary and not sufficient: an operator reading a red check needs to know
    # WHICH input was missing. A bare non-zero exit with no diagnosis sends them to the source.
    result = run_gate(script, "")
    assert (result.stdout + result.stderr).strip(), (
        f"{script} refused empty input but emitted nothing on stdout or stderr. A refusal with no "
        f"stated reason is indistinguishable from a crash."
    )


# --- the load-bearing half: absence is the ONLY variable ---------------------

# Minimal SUFFICIENT environment per stdin-consuming gate. Sufficiency is not asserted by reading
# the source; each pair below proves it by succeeding on a valid subject first.
STDIN_GATES = {
    "scripts/check_budget.py": {"BUDGET_TEXT": "BUDGET: max_files=9 max_lines=900"},
    "scripts/classify_authority_delta.py": {},
    "scripts/check_dual_policy.py": {"BASE_REF": "HEAD"},
}

VALID_SUBJECT = "3\t1\tdocs/14-plans/SECB-WP-FWK-999.md\n"


def run_with(script: str, extra: dict, payload: str) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k not in GATE_ENV}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.update(extra)
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / script)],
        input=payload, capture_output=True, text=True, env=env, cwd=REPO_ROOT, timeout=120,
    )


def test_the_paired_set_names_only_real_invoked_gates():
    # Guards the pair list against drift in one direction only, and says so: it catches a name
    # that no workflow invokes, and CANNOT catch a new stdin-consuming gate that nobody added
    # here. That second direction needs a person, so it is written down rather than implied.
    stray = sorted(set(STDIN_GATES) - set(invoked()))
    assert not stray, (
        f"STDIN_GATES names scripts no workflow invokes: {stray}. Either the workflow stopped "
        "invoking them, or the name is wrong and these pairs have been testing nothing."
    )


@pytest.mark.parametrize("script,extra", sorted(STDIN_GATES.items()))
def test_a_sufficient_environment_lets_the_gate_succeed(script, extra):
    # The control half. Without it, the refusal below could come from an inadequate environment
    # and the pair would prove nothing -- which is exactly how this file's first draft passed
    # while a reinstated fail-open went undetected.
    result = run_with(script, extra, VALID_SUBJECT)
    assert result.returncode == OK, (
        f"{script} did not succeed on a valid subject with the environment this test supplies, so "
        f"the paired absence test below cannot attribute a refusal to the absent input. Fix the "
        f"environment in STDIN_GATES.\n  stdout: {result.stdout[:300]!r}\n"
        f"  stderr: {result.stderr[:300]!r}"
    )


@pytest.mark.parametrize("script,extra", sorted(STDIN_GATES.items()))
def test_the_same_gate_refuses_when_only_the_subject_is_absent(script, extra):
    # Everything the successful run had, minus the subject. A zero here is the #163 defect
    # exactly: a gate reporting a clean measurement of a diff that was never computed.
    result = run_with(script, extra, "")
    assert result.returncode != OK, (
        f"{script} exited 0 with a sufficient environment and an ABSENT subject. It reported a "
        f"clean result for something it never measured -- the defect #163 removed from "
        f"check_budget.py, where an unreachable base SHA in a shallow clone produced "
        f"'BUDGET GATE PASS: 0/N files'.\n  stdout: {result.stdout[:300]!r}"
    )
    said = (result.stdout + result.stderr)
    assert said.strip(), f"{script} refused silently; an operator cannot tell refusal from a crash"


@pytest.mark.parametrize("script,extra", sorted(STDIN_GATES.items()))
def test_the_refusal_is_distinguishable_from_the_success(script, extra):
    # Fail-closed with an identical message would leave a reader unable to tell which run they are
    # looking at. The diagnosis must change, not just the exit code.
    ok = run_with(script, extra, VALID_SUBJECT)
    absent = run_with(script, extra, "")
    assert (ok.stdout + ok.stderr).strip() != (absent.stdout + absent.stderr).strip(), (
        f"{script} emits the same text whether it measured a subject or refused for want of one"
    )
