"""Subprocess tests for scripts/check_merge_autonomy.py.

Invoked exactly as CI invokes it (stdin numstat + environment), per KN-002.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "check_merge_autonomy.py"

ELIGIBLE = 0
HUMAN_REQUIRED = 2

SEALED = (
    "docs/06-agent-orchestration/skill-router/"
    "SECB-WP-ENGLOOP-MVP-001 — Sandbox Evidence/router.py"
)


def run_gate(numstat: str, max_lines: str | None = None):
    env = {k: v for k, v in os.environ.items() if k != "MAX_LINES"}
    if max_lines is not None:
        env["MAX_LINES"] = max_lines
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=numstat,
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )


def test_eligible_docs_only():
    result = run_gate("10\t2\tdocs/14-plans/SECB-WP-FWK-099.md\n")
    assert result.returncode == ELIGIBLE
    assert "ELIGIBLE" in result.stdout


def test_eligible_mixed_r1_docs_tests_src():
    numstat = (
        "20\t0\tdocs/13-evidence/RECORD.md\n"
        "30\t5\ttests/test_thing.py\n"
        "40\t1\tsrc/secb_router/helper.py\n"
    )
    result = run_gate(numstat)
    assert result.returncode == ELIGIBLE
    assert "3 R1 path(s)" in result.stdout


@pytest.mark.parametrize(
    "path",
    [
        "AGENTS.md",
        "README.md",
        "docs/00-governance/CONTROL_GATES.md",
        "docs/12-decisions/ADR-SOMETHING.md",
        "scripts/check_budget.py",
        ".github/workflows/ci.yml",
        SEALED,
    ],
)
def test_protected_path_forces_human(path):
    result = run_gate(f"1\t1\t{path}\n")
    assert result.returncode == HUMAN_REQUIRED
    assert "protected path" in result.stderr


def test_protected_path_wins_even_when_mixed_with_r1():
    numstat = "5\t0\tdocs/plan.md\n1\t1\tAGENTS.md\n"
    result = run_gate(numstat)
    assert result.returncode == HUMAN_REQUIRED


def test_unclassified_path_forces_human():
    result = run_gate("1\t0\tinfra/terraform/main.tf\n")
    assert result.returncode == HUMAN_REQUIRED
    assert "not classified R1" in result.stderr


def test_size_cap_boundary_is_inclusive():
    result = run_gate("300\t300\tdocs/big.md\n")  # exactly 600
    assert result.returncode == ELIGIBLE


def test_over_size_cap_forces_human():
    result = run_gate("300\t301\tdocs/big.md\n")  # 601
    assert result.returncode == HUMAN_REQUIRED
    assert "exceeds the R1 cap" in result.stderr


def test_size_cap_override_is_honored():
    result = run_gate("60\t0\tdocs/small.md\n", max_lines="50")
    assert result.returncode == HUMAN_REQUIRED


def test_fail_closed_on_empty_input():
    result = run_gate("")
    assert result.returncode == HUMAN_REQUIRED
    assert "no diff parsed" in result.stderr


def test_fail_closed_on_unparseable_input():
    result = run_gate("garbage row without tabs\n")
    assert result.returncode == HUMAN_REQUIRED
    assert "unparseable" in result.stderr


def test_fail_closed_on_bad_max_lines():
    result = run_gate("1\t0\tdocs/a.md\n", max_lines="not-a-number")
    assert result.returncode == HUMAN_REQUIRED


def test_binary_file_counts_no_lines_but_is_classified():
    result = run_gate("-\t-\tdocs/diagram.png\n")
    assert result.returncode == ELIGIBLE


def test_path_with_spaces_and_em_dash_is_read_whole():
    # The sealed directory name contains spaces and an em dash; the parser
    # must take the path as the last field, not split it.
    result = run_gate(f"1\t1\t{SEALED}\n")
    assert result.returncode == HUMAN_REQUIRED
    assert "protected path" in result.stderr
