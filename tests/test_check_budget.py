"""Subprocess tests for scripts/check_budget.py (budget circuit breaker).

Same discipline as the authority-gate suite: every test invokes the script
as a subprocess with stdin + environment, the exact surface CI uses.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "check_budget.py"

PASS = 0
FAIL = 2

BUDGET_2_40 = "Some PR text.\n\nBUDGET: max_files=2 max_lines=40\n\nMore text."


def run_gate(numstat: str, body: str | None, **extra: str):
    env = {k: v for k, v in os.environ.items()
           if k not in ("BUDGET_TEXT", "ALLOW_EMPTY_DIFF")}
    if body is not None:
        env["BUDGET_TEXT"] = body
    env.update(extra)
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=numstat,
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )


def test_pass_within_budget_reports_usage():
    result = run_gate("10\t5\tsrc/a.py\n3\t2\tdocs/b.md\n", BUDGET_2_40)
    assert result.returncode == PASS
    assert "2/2 files, 20/40 changed lines" in result.stdout


def test_pass_at_exact_boundary():
    # A budget is a ceiling, not a strict bound: equal-to-limit passes.
    result = run_gate("20\t20\ta.py\n", "BUDGET: max_files=1 max_lines=40")
    assert result.returncode == PASS


def test_fail_when_file_count_exceeded():
    result = run_gate("1\t0\ta\n1\t0\tb\n1\t0\tc\n", BUDGET_2_40)
    assert result.returncode == FAIL
    assert "exceeds" in result.stderr


def test_fail_when_line_count_exceeded():
    result = run_gate("30\t20\tonly.py\n", BUDGET_2_40)
    assert result.returncode == FAIL
    assert "50/40" in result.stderr


def test_fail_closed_when_no_budget_declared():
    result = run_gate("1\t1\ta.py\n", "a PR body with no budget line")
    assert result.returncode == FAIL
    assert "no budget declared" in result.stderr


def test_fail_closed_when_env_missing_entirely():
    result = run_gate("1\t1\ta.py\n", body=None)
    assert result.returncode == FAIL


def test_fail_closed_on_malformed_budget():
    result = run_gate("1\t1\ta.py\n", "BUDGET: max_files=two max_lines=40")
    assert result.returncode == FAIL


def test_fail_closed_on_ambiguous_double_budget():
    body = "BUDGET: max_files=2 max_lines=40\nBUDGET: max_files=9 max_lines=999"
    result = run_gate("1\t1\ta.py\n", body)
    assert result.returncode == FAIL
    assert "ambiguous" in result.stderr


def test_binary_file_counts_toward_files_not_lines():
    result = run_gate("-\t-\timage.png\n", "BUDGET: max_files=1 max_lines=0")
    assert result.returncode == PASS
    assert "1/1 files, 0/0" in result.stdout


def test_empty_diff_does_not_pass_any_budget():
    """SECB-WP-FWK-091 inverts this test, and the inversion is the point.

    It previously read `assert result.returncode == PASS` for empty stdin against a
    zero budget -- so the fail-open was not an oversight, it was PINNED IN PLACE by a
    test. A guard that asserts the wrong behaviour is worse than an absent one: the
    absent guard leaves a hole, while this one defended it, and any attempt to close
    the hole showed up as a regression.

        TEST_EXISTS != TEST_ASSERTS_THE_RIGHT_THING

    An unmeasured diff cannot be "within" a budget of zero or of anything else,
    because nothing was compared to the ceiling.
    """
    result = run_gate("", "BUDGET: max_files=0 max_lines=0")
    assert result.returncode == FAIL
    assert "BUDGET_DIFF_ABSENT" in result.stderr


def test_fail_closed_on_garbage_numstat():
    result = run_gate("not a numstat row at all", BUDGET_2_40)
    assert result.returncode == FAIL


# ---------------------------------------------------------------------------
# SECB-WP-FWK-091: an absent diff is not a diff of zero.
#
# Until these tests existed the gate answered "BUDGET GATE PASS: 0/2 files" to
# empty stdin, and the fail-open was REACHABLE rather than theoretical. CI feeds
# this script through a shell pipeline:
#
#     git diff --numstat "$BASE_SHA...$HEAD_SHA" | python scripts/check_budget.py
#
# GitHub's default shell is `bash -e`, which does not set pipefail, so the step's
# exit status is this script's. A failing `git diff` -- an unreachable base SHA in
# a shallow clone being the ordinary cause -- printed nothing, exited non-zero into
# a discarded status, and produced a green admission check that measured nothing.
#
#     EMPTY_INPUT != EMPTY_DIFF
#     MEASUREMENT_NOT_PERFORMED != MEASUREMENT_FOUND_NOTHING
# ---------------------------------------------------------------------------


def test_empty_stdin_is_refused_not_passed():
    result = run_gate("", BUDGET_2_40)
    assert result.returncode == FAIL
    assert "BUDGET_DIFF_ABSENT" in result.stderr
    assert "PASS" not in result.stdout


def test_whitespace_only_stdin_is_refused():
    """A pipeline can deliver a bare newline; that is still nothing measured."""
    result = run_gate("\n  \n", BUDGET_2_40)
    assert result.returncode == FAIL
    assert "BUDGET_DIFF_ABSENT" in result.stderr


def test_a_failing_diff_command_in_the_ci_pipeline_is_refused(tmp_path):
    """The reachable form: reproduce CI's pipeline with a `git diff` that fails.

    `bash -e` without pipefail reports the LAST command's status, so this test would have
    passed with exit 0 before the fix. It is the counterexample for the whole work package.
    """
    script = tmp_path / "pipeline.sh"
    script.write_text(
        f'git diff --numstat "{"dead" * 10}...HEAD" 2>/dev/null '
        f'| "{sys.executable}" "{SCRIPT}"\n',
        encoding="utf-8",
    )
    env = {k: v for k, v in os.environ.items() if k != "ALLOW_EMPTY_DIFF"}
    env["BUDGET_TEXT"] = BUDGET_2_40
    result = subprocess.run(
        ["bash", "-e", str(script)],
        cwd=SCRIPT.parent.parent, capture_output=True, text=True, env=env, timeout=60,
    )
    assert result.returncode == FAIL, (
        "the pipeline must fail closed even though bash reports only the last command's status"
    )
    assert "BUDGET_DIFF_ABSENT" in result.stderr


def test_a_deliberately_empty_diff_is_not_applicable_never_pass():
    """The legitimate case is admitted, and is NOT called PASS.

    Nothing was measured against the ceiling, so "within budget" would overstate the
    observation -- the same distinction the sibling authority gates draw.
    """
    result = run_gate("", BUDGET_2_40, ALLOW_EMPTY_DIFF="1")
    assert result.returncode == PASS
    assert "NOT_APPLICABLE" in result.stdout
    assert "PASS" not in result.stdout


def test_allow_empty_diff_does_not_waive_a_real_measurement():
    """The opt-in covers absence only; a diff over budget still fails with it set."""
    over = "50\t0\ta.py\n50\t0\tb.py\n50\t0\tc.py\n"
    result = run_gate(over, BUDGET_2_40, ALLOW_EMPTY_DIFF="1")
    assert result.returncode == FAIL
    assert "exceeds the declared budget" in result.stderr


def test_allow_empty_diff_does_not_waive_a_missing_budget():
    """Order matters: no declared ceiling is refused before absence is considered."""
    result = run_gate("", None, ALLOW_EMPTY_DIFF="1")
    assert result.returncode == FAIL
    assert "no budget declared" in result.stderr


def test_a_single_real_row_still_measures():
    """Guard against over-correcting: one legitimate row must not be read as absent."""
    result = run_gate("1\t0\ta.py\n", BUDGET_2_40)
    assert result.returncode == PASS
    assert "BUDGET GATE PASS: 1/2 files, 1/40 changed lines" in result.stdout


def test_a_budget_declaration_may_not_span_two_physical_lines():
    """One declaration, one line -- and the declared-twice refusal depends on it.

    `\\s` matches newlines, so under `re.MULTILINE` the pattern accepted

        BUDGET: max_files=1
        max_lines=99999

    as a single valid declaration. The docstring requires "exactly one budget line", and the second
    consequence is the one that matters: a split declaration is ONE regex match, so it slipped past
    the duplicate refusal at `len(matches) > 1` while declaring values a reviewer never saw.

        HORIZONTAL_WHITESPACE != ANY_WHITESPACE

    Surfaced by a seeded-recall probe as an UNSEEDED defect in the live gate -- the seeds were
    elsewhere, and this was found alongside them.
    """
    split = run_gate("1\t0\ta.py\n", "BUDGET: max_files=1\nmax_lines=99999")
    assert split.returncode != 0, (
        "a budget split across two physical lines was accepted; being one match, it also evades "
        "the declared-twice refusal:\n" + split.stdout
    )
    assert "no budget declared" in (split.stdout + split.stderr)

    intact = run_gate("1\t0\ta.py\n", "BUDGET: max_files=5 max_lines=100")
    assert intact.returncode == 0, f"a normal one-line declaration must still pass:\n{intact.stdout}"
