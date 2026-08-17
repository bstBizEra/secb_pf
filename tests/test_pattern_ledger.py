"""SECB-WP-FWK-090 -- the reusable-pattern ledger validator.

Every refusal is produced by INVOKING scripts/check_pattern_ledger.py as a subprocess against
a mutated ledger. The accept path runs against the REAL ledger the repository ships, so the
suite fails if a shipped entry ever cites a guard that has been renamed or deleted -- which is
the drift this tool exists to catch, applied to itself.

Two of these tests are cited BY the ledger (RP-025, RP-026). That is deliberate and it is
load-bearing in the ordering sense: while they did not exist, the validator refused the
ledger that named them. The tool enforced counterexample-first order on its own author.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "scripts" / "check_pattern_ledger.py"
LEDGER_PATH = ROOT / "config" / "reusable_patterns.json"

SHIPPED = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
# A citation that certainly resolves: this file, this test.
REAL = {"file": "tests/test_pattern_ledger.py", "test": "test_the_shipped_ledger_validates"}


def run(ledger: dict, tmp_path: Path) -> subprocess.CompletedProcess:
    path = tmp_path / "ledger.json"
    path.write_text(json.dumps(ledger), encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(TOOL)], capture_output=True, text=True, check=False,
        env={
            **os.environ,
            "LEDGER": str(path),
            "REPO_ROOT": str(ROOT),
            "PYTHONDONTWRITEBYTECODE": "1",
        },
    )


def refuses(ledger: dict, tmp_path: Path, fragment: str) -> str:
    result = run(ledger, tmp_path)
    assert result.returncode == 2, f"expected refusal, got {result.returncode}: {result.stdout}"
    assert "REFUSED (closed)" in result.stderr
    assert fragment in result.stderr, f"{fragment!r} not in {result.stderr!r}"
    return result.stderr


def one(**overrides) -> dict:
    """A single-entry ledger, minimal and valid, with overrides applied to the entry."""
    entry = {
        "id": "RP-900",
        "name": "A probe pattern",
        "rule": "A != B",
        "origin": {"pr": 159},
        "guard": "PROSE_ONLY",
    }
    entry.update(overrides)
    return {"schema": "secb.reusable-pattern-ledger/v1", "patterns": [entry]}


# ------------------------------------------------------------------------- accept path


def test_the_shipped_ledger_validates(tmp_path):
    """The real ledger, against the real tree. Guards the citations, not just the parser."""
    result = run(SHIPPED, tmp_path)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["patterns"] == len(SHIPPED["patterns"])
    assert report["mechanically_guarded"] >= 1
    assert report["confers_merge_authority"] is False


def test_the_guarded_ratio_is_reported_and_never_rounded_up(tmp_path):
    """Honest prose must stay visibly prose: the ratio is emitted, not a pass/fail badge."""
    report = json.loads(run(SHIPPED, tmp_path).stdout)
    classes = report["by_guard_class"]
    assert report["mechanically_guarded"] == classes.get("MECHANICAL", 0)
    assert report["mechanically_guarded"] < report["patterns"], (
        "if every pattern were mechanically guarded the ratio would stop being informative; "
        "this assertion exists to notice the day someone 'fixes' the ratio by relabelling"
    )
    assert classes.get("PROSE_ONLY", 0) >= 1


# --------------------------------------------------------------- the two cited guards


def test_a_mechanical_claim_whose_test_is_absent_is_refused(tmp_path):
    """RP-026, first direction: a phantom citation.

    The failure this prevents is not hypothetical -- a governing document can name a required
    test that was never written, and every agent that reads it believes the guard is in force.
    """
    absent_file = one(guard="MECHANICAL", tests=[{"file": "tests/test_nope.py", "test": "test_x"}])
    stderr = refuses(absent_file, tmp_path, "is not in this tree")
    assert "worse than no citation" in stderr

    # Sharper: the FILE exists, the test name does not. A path-only check would pass this.
    absent_name = one(guard="MECHANICAL", tests=[
        {"file": "tests/test_pattern_ledger.py", "test": "test_this_name_does_not_exist"}])
    refuses(absent_name, tmp_path, "is not in this tree")


def test_a_pending_claim_whose_tests_all_exist_is_refused(tmp_path):
    """RP-026, second direction: a stale PENDING_MERGE.

    Under-claiming is checked because it decays the ledger as surely as over-claiming: entries
    that say "not yet enforced" long after they are enforced train readers to ignore the field.
    """
    stale = one(guard="PENDING_MERGE", pending_pr=159, tests=[REAL])
    stderr = refuses(stale, tmp_path, "classification is stale")
    assert "promote it to MECHANICAL" in stderr


def test_a_prose_entry_may_not_cite_a_guard(tmp_path):
    """RP-026, third direction: prose that quietly cites enforcement."""
    refuses(one(guard="PROSE_ONLY", tests=[REAL]), tmp_path, "understates its own")


# ------------------------------------------------------------------- structural refusals


def test_a_mechanical_entry_with_no_tests_is_refused(tmp_path):
    refuses(one(guard="MECHANICAL"), tmp_path, "cites no tests")


def test_a_pending_entry_without_a_pr_is_refused(tmp_path):
    ledger = one(guard="PENDING_MERGE",
                 tests=[{"file": "tests/test_nope.py", "test": "test_x"}])
    refuses(ledger, tmp_path, "requires pending_pr")


def test_a_duplicate_id_is_refused(tmp_path):
    ledger = one()
    ledger["patterns"].append(deepcopy(ledger["patterns"][0]))
    refuses(ledger, tmp_path, "duplicate id")


def test_a_malformed_id_is_refused(tmp_path):
    refuses(one(id="RP-1"), tmp_path, "is not of the form")


def test_a_rule_without_a_distinction_is_refused(tmp_path):
    """A pattern with no stated relation is a slogan."""
    stderr = refuses(one(rule="be careful with evidence"), tmp_path, "states no distinction")
    assert "slogan" in stderr


def test_an_ordering_rule_is_accepted_as_a_rule(tmp_path):
    """The root pattern of this family is an ordering and nothing else.

    The first draft of the marker list omitted `<=` and refused RP-001 -- the check working
    correctly against a rule that was too narrow. This test pins the widened form.
    """
    result = run(one(rule="CLAIM_STRENGTH <= MECHANISM_STRENGTH <= VERIFIED_BEHAVIOUR"), tmp_path)
    assert result.returncode == 0, result.stderr


def test_an_entry_without_provenance_is_refused(tmp_path):
    stderr = refuses(one(origin={"note": "somebody said so"}), tmp_path, "neither a pr nor an issue")
    assert "folklore" in stderr


def test_an_unknown_guard_class_is_refused(tmp_path):
    refuses(one(guard="ENFORCED_SOMEHOW"), tmp_path, "is not one of")


def test_a_missing_required_field_is_refused(tmp_path):
    for field in ("id", "name", "rule", "origin", "guard"):
        ledger = one()
        del ledger["patterns"][0][field]
        refuses(ledger, tmp_path, "missing required field")


def test_the_wrong_schema_is_refused(tmp_path):
    ledger = one()
    ledger["schema"] = "secb.reusable-pattern-ledger/v2"
    refuses(ledger, tmp_path, "expected 'secb.reusable-pattern-ledger/v1'")


def test_an_empty_ledger_is_refused(tmp_path):
    ledger = one()
    ledger["patterns"] = []
    refuses(ledger, tmp_path, "declares no patterns")


def test_an_unreadable_ledger_is_refused(tmp_path):
    result = subprocess.run(
        [sys.executable, str(TOOL)], capture_output=True, text=True, check=False,
        env={
            **os.environ,
            "LEDGER": str(tmp_path / "absent.json"),
            "REPO_ROOT": str(ROOT),
            "PYTHONDONTWRITEBYTECODE": "1",
        },
    )
    assert result.returncode == 2
    assert "unreadable or unparseable" in result.stderr


# ------------------------------------------------------------------------ the contract


def test_every_shipped_pending_entry_names_an_open_pr():
    """A PENDING_MERGE entry whose PR has merged should have become MECHANICAL.

    Checked structurally rather than over the network: the validator already proves the cited
    tests are absent from this tree, and a merged PR's tests would be present. This asserts the
    field is populated so a human can resolve it.
    """
    for entry in SHIPPED["patterns"]:
        if entry["guard"] == "PENDING_MERGE":
            assert isinstance(entry["pending_pr"], int), entry["id"]
            assert entry.get("tests"), entry["id"]


def test_no_shipped_entry_claims_more_than_its_guard_class():
    """The ledger's own instance of RP-001: no entry may out-claim its mechanism."""
    for entry in SHIPPED["patterns"]:
        if entry["guard"] == "PROSE_ONLY":
            assert not entry.get("tests"), f"{entry['id']} is prose but cites tests"
        else:
            assert entry.get("tests"), f"{entry['id']} claims {entry['guard']} with no tests"
