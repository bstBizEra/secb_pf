"""Subprocess tests for scripts/check_work_package_ref.py (Authority Gate).

Every test invokes the script as a real subprocess -- the same surface CI
uses -- rather than importing it. A gate that passes unit tests through
import but breaks when invoked is a fail-open defect; testing the invoked
command is what catches it.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "check_work_package_ref.py"

PASS = 0
FAIL_CLOSED = 2


def run_gate(args: list[str] | None = None, env_text: str | None = None):
    env = {k: v for k, v in os.environ.items() if k != "WP_TEXT"}
    if env_text is not None:
        env["WP_TEXT"] = env_text
    return subprocess.run(
        [sys.executable, str(SCRIPT), *(args or [])],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )


def test_pass_when_title_cites_work_package():
    result = run_gate(env_text="feat: add intake form (SECB-WP-FWK-002)")
    assert result.returncode == PASS
    assert "SECB-WP-FWK-002" in result.stdout


def test_pass_reference_may_appear_anywhere_in_body():
    result = run_gate(env_text="Some title\n\nImplements SECB-WP-ENGLOOP-004.")
    assert result.returncode == PASS


def test_fail_when_no_reference_present():
    result = run_gate(env_text="feat: quick improvement, no ticket")
    assert result.returncode == FAIL_CLOSED
    assert "No Ticket, No Work" in result.stderr


def test_fail_closed_on_empty_input():
    result = run_gate(env_text="")
    assert result.returncode == FAIL_CLOSED
    assert "fail" in result.stderr.lower() or "FAIL" in result.stderr


def test_fail_closed_when_nothing_provided_at_all():
    result = run_gate()
    assert result.returncode == FAIL_CLOSED


def test_fail_on_lookalike_prefix_without_id():
    # "SECB-WP-" alone is not a work package; the ID segment is required.
    result = run_gate(env_text="mentions SECB-WP- but never a real ID")
    assert result.returncode == FAIL_CLOSED


def test_fail_on_lowercase_reference():
    # IDs are uppercase by convention; lowercase text must not pass the gate.
    result = run_gate(env_text="secb-wp-fwk-002 lowercase does not count")
    assert result.returncode == FAIL_CLOSED


def test_env_var_takes_precedence_over_argv():
    # CI feeds text via WP_TEXT so PR titles are never shell-interpolated;
    # argv must not override the trusted channel once it is set.
    result = run_gate(args=["SECB-WP-FAKE-999"], env_text="no reference here")
    assert result.returncode == FAIL_CLOSED


def test_argv_fallback_still_works_without_env():
    result = run_gate(args=["chore:", "cleanup", "under", "SECB-WP-FWK-002"])
    assert result.returncode == PASS
