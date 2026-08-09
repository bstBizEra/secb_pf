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


def run_gate(numstat: str, body: str | None):
    env = {k: v for k, v in os.environ.items() if k != "BUDGET_TEXT"}
    if body is not None:
        env["BUDGET_TEXT"] = body
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


def test_empty_diff_passes_any_budget():
    result = run_gate("", "BUDGET: max_files=0 max_lines=0")
    assert result.returncode == PASS


def test_fail_closed_on_garbage_numstat():
    result = run_gate("not a numstat row at all", BUDGET_2_40)
    assert result.returncode == FAIL
