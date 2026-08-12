"""Subprocess tests for scripts/check_base_currency.py (`BACP-05`).

Invoked as CI invokes it. The three outcomes are distinguished by exit code, so
a caller never has to match on message text -- `STALE` is 1 and "could not run"
is 2, because conflating them is how a staleness check becomes a fail-open.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "check_base_currency.py"

CURRENT = 0
STALE = 1
FAIL_CLOSED = 2

A = "3b61307a1b2c3d4e5f60718293a4b5c6d7e8f901"
B = "4a71abd1122334455667788990011223344556677"[:40]


def run(*args: str):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, timeout=30,
    )


def test_equal_shas_report_current():
    result = run(A, A, "main")
    assert result.returncode == CURRENT
    assert "CURRENT" in result.stdout


def test_a_moved_base_is_stale_and_names_both_shas():
    result = run(A, B, "main")
    assert result.returncode == STALE
    assert A[:12] in result.stderr and B[:12] in result.stderr
    assert "will not be merged" in result.stderr


def test_an_abbreviated_sha_on_one_side_is_not_a_difference():
    """CI may hand a full SHA one side and a short one the other.

    Treating that as staleness would report a problem that does not exist,
    which is the kind of false positive that gets a check ignored.
    """
    assert run(A, A[:7], "main").returncode == CURRENT
    assert run(A[:7], A, "main").returncode == CURRENT


def test_a_missing_sha_fails_closed_rather_than_reporting_current():
    """The fail-open this script exists to avoid."""
    for args in ((), (A,)):
        result = run(*args)
        assert result.returncode == FAIL_CLOSED
        assert "not a current base" in result.stderr


def test_a_malformed_sha_fails_closed():
    for bad in ("", "zzzz", "main", "12345"):
        result = run(A, bad, "main")
        assert result.returncode == FAIL_CLOSED, bad
        assert "is not a SHA" in result.stderr


def test_stale_and_unrunnable_have_different_exit_codes():
    """The distinction a caller needs, asserted rather than assumed."""
    assert run(A, B).returncode != run(A, "nonsense").returncode


def test_the_script_records_why_it_does_not_block():
    """The reasoning must live with the code, not only in a ticket.

    A future reader deciding whether to make this blocking needs the
    measurement that says why it is not, and the trigger that would change
    the answer.
    """
    text = SCRIPT.read_text(encoding="utf-8")
    assert "does not block" in text
    assert "merge queue" in text
    assert "§D4" in text
