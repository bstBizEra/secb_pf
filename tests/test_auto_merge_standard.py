"""Characterization fixtures for the two defect classes ruled `d = 2`.

`SECB-WP-FWK-063`. These tests assert **what the classifier does today**, compared
against a *declared* status in `docs/09-testing/negative_test_status.json` — not
against what it ought to do. That distinction is the whole design: a test written to
assert the correct behaviour would fail now and would be deleted or skipped, and a
test asserting the defect without a declared status reddens CI the day someone fixes
it. Both failure modes were already paid for once, in `§P1` of the negative-test
lifecycle.

So each test reads its scenario's declared `status` and asserts the behaviour that
status claims. When `WP-02` lands and the status flips to `CONTROL_FIXED`, these
tests assert the *fixed* behaviour instead, and the fix does not have to touch them.

The two scenarios were not discovered by writing fixtures. They were discovered by
merging them: #111 and #120.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
STATUS_FILE = REPO_ROOT / "docs" / "09-testing" / "negative_test_status.json"
CLASSIFIER = REPO_ROOT / "scripts" / "classify_authority_delta.py"

AUTO_APPROVED = 0
ESCALATE = 2


def scenario(scenario_id: str) -> dict:
    data = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
    for entry in data["scenarios"]:
        if entry["id"] == scenario_id:
            return entry
    raise AssertionError(f"{scenario_id} is not declared in negative_test_status.json")


def run_classifier(numstat: str, diff_text: str = "") -> subprocess.CompletedProcess:
    """Invoke the classifier as a subprocess, the surface CI uses."""
    env = {k: v for k, v in os.environ.items() if k not in ("DIFF_PATH", "DIFF_TEXT")}
    env["DIFF_TEXT"] = diff_text
    return subprocess.run(
        [sys.executable, str(CLASSIFIER)],
        input=numstat,
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )


# --- AMS-01 — path-based classification ignores material effect ---------------

# A numstat naming a stage-gate decision record. `docs/` is an auto_path, so the
# classifier sees an ordinary documentation change; the *content* is a verdict.
DECISION_RECORD_NUMSTAT = "27\t5\tdocs/13-evidence/STAGE_GATE_REQUIREMENTS_READY.md\n"


def test_gap_decision_record_under_docs_still_grades_g0():
    """`AMS-01`: reproduces the #111 class against its declared status."""
    declared = scenario("AMS-01")["status"]
    result = run_classifier(DECISION_RECORD_NUMSTAT)

    if declared == "GAP_REPRODUCED":
        assert result.returncode == AUTO_APPROVED, (
            "AMS-01 is declared GAP_REPRODUCED, meaning the classifier still grades a "
            "stage-gate decision record as G0 because of its path. It did not — which "
            "is good news and a status update: flip AMS-01 to CONTROL_FIXED in "
            "docs/09-testing/negative_test_status.json and this assertion inverts.\n"
            f"stdout: {result.stdout.strip()}"
        )
        assert "G0" in result.stdout, (
            "expected the G0 path classification in the verdict line; the gap is that "
            f"a decision record reaches it at all. Got: {result.stdout.strip()}"
        )
    elif declared == "CONTROL_FIXED":
        assert result.returncode == ESCALATE, (
            "AMS-01 is declared CONTROL_FIXED, so a decision record must no longer "
            f"grade G0. It still does: {result.stdout.strip()}"
        )
    else:
        pytest.fail(f"AMS-01 carries an unhandled status: {declared!r}")


def test_ams_01_records_that_effect_must_outrank_path():
    """The scenario must name its fix, or a reader cannot tell a gap from a policy."""
    entry = scenario("AMS-01")
    assert entry.get("named_fix"), "AMS-01 must name the fix that would close it"
    assert entry.get("characterization_fixture"), "AMS-01 must point at its fixture"
    assert "not_a_conformance_requirement" in entry, (
        "a GAP_REPRODUCED scenario must say so explicitly, or a later reader treats "
        "the reproduced defect as the required behaviour"
    )


# --- AMS-02 — effectuation without a head-bound receipt ----------------------


def test_gap_no_receipt_is_required_to_effectuate():
    """`AMS-02`: nothing in the tree requires a ratification receipt to merge."""
    declared = scenario("AMS-02")["status"]
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True, timeout=30
    ).stdout.splitlines()

    receipt_artifacts = [
        path
        for path in tracked
        if "ratification-receipt" in path.lower() or "ratification_receipt" in path.lower()
    ]

    if declared == "GAP_REPRODUCED":
        assert not receipt_artifacts, (
            "AMS-02 is declared GAP_REPRODUCED — no ratification-receipt artifact "
            "exists, so nothing can require one before a merge takes effect. Files "
            f"now present: {receipt_artifacts}. If a receipt mechanism has landed, "
            "flip AMS-02 to CONTROL_FIXED."
        )
    elif declared == "CONTROL_FIXED":
        assert receipt_artifacts, (
            "AMS-02 is declared CONTROL_FIXED, so a receipt artifact must exist"
        )
    else:
        pytest.fail(f"AMS-02 carries an unhandled status: {declared!r}")


def test_ams_02_records_the_capability_blocker_not_just_the_gap():
    """The receipt is unobtainable under one identity, and that must be recorded.

    Without this, `AMS-02` reads as work nobody has done. It is work nobody *can*
    do: the schema requires an actor independent of the executor, and GitHub refuses
    an approving review from a pull request's own author.
    """
    entry = scenario("AMS-02")
    blocked_by = entry.get("blocked_by", "")
    assert "C-7" in blocked_by, (
        "AMS-02 must cite C-7 as its blocker — the identity condition is why the "
        "receipt cannot be produced, and a gap without its blocker looks like neglect"
    )


# --- the standard that names both must not silently become binding -----------


def test_the_standard_is_marked_proposed_until_an_authority_lands_it():
    """`docs/00-governance/AUTO_MERGE_STANDARD.md` binds nothing by existing.

    The executor wrote it; only an authority with `G1` over `docs/00-governance/`
    can make it operative. A governance document that reads as in force because it
    is present is the `ISSUED` defect relocated into a file path.
    """
    standard = REPO_ROOT / "docs" / "00-governance" / "AUTO_MERGE_STANDARD.md"
    assert standard.is_file(), "the standard must exist for these scenarios to cite"
    text = standard.read_text(encoding="utf-8")
    assert "`PROPOSED`" in text, "the standard must declare itself PROPOSED"
    assert "binds nothing" in text, (
        "the standard must state that its presence in the repository is not force"
    )
