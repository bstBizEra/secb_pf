"""SECB-WP-FWK-092 phase 1 -- the review preflight, and the collectability predicate.

Every refusal invokes scripts/check_review_preflight.py as a subprocess. The accept path runs
against the REAL shipped ledger, so a renamed guard or a moved test root fails CI rather than
rotting quietly.

The predicate under test is the one #161 revision 3 got half-right:

    DEF_PRESENT != TEST_COLLECTED != GUARD_ENFORCED

An AST check proves a definition exists. Only pytest's own collection proves it runs, which is why
`test_a_defined_but_uncollected_citation_is_refused` builds a module with a perfectly real
`def test_x` that pytest will not collect, and asserts the preflight refuses it.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "scripts" / "check_review_preflight.py"
LEDGER_PATH = ROOT / "config" / "reusable_patterns.json"
SHIPPED = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))

# A citation that certainly collects: this file, this test.
COLLECTED = {"file": "tests/test_review_preflight.py", "test": "test_the_shipped_ledger_passes_preflight"}


def run(ledger: dict, tmp_path: Path, root: Path | None = None) -> subprocess.CompletedProcess:
    path = tmp_path / "ledger.json"
    path.write_text(json.dumps(ledger), encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(TOOL)], capture_output=True, text=True, check=False,
        env={
            **os.environ,
            "REPO_ROOT": str(root or ROOT),
            "LEDGER": str(path),
            "PYTHONDONTWRITEBYTECODE": "1",
        },
    )


def refuses(ledger: dict, tmp_path: Path, fragment: str) -> str:
    result = run(ledger, tmp_path)
    assert result.returncode == 2, f"expected refusal, got {result.returncode}: {result.stdout}"
    assert fragment in result.stderr, f"{fragment!r} not in {result.stderr!r}"
    return result.stderr


def finds(ledger: dict, tmp_path: Path, fragment: str) -> dict:
    """A FINDING is not a refusal: the preflight ran and reports FAIL with detail."""
    result = run(ledger, tmp_path)
    assert result.returncode == 2, result.stdout
    report = json.loads(result.stdout)
    assert report["MECHANICAL_PREFLIGHT"] == "FAIL"
    assert any(fragment in f for f in report["findings"]), report["findings"]
    return report


def minimal(**overrides) -> dict:
    """A ledger with one pattern citing one collected test, plus one valid active record."""
    entry = {
        "id": "RP-900", "name": "probe", "rule": "A != B", "origin": {"pr": 164},
        "guard": "MECHANICAL", "tests": [dict(COLLECTED)],
    }
    entry.update(overrides.pop("entry", {}))
    ledger = {
        "schema": "secb.reusable-pattern-ledger/v1",
        "test_roots": ["tests"],
        "patterns": [entry],
        "promoted_refusals": [deepcopy(SHIPPED["promoted_refusals"][0])],
    }
    ledger.update(overrides)
    return ledger


# ------------------------------------------------------------------------- accept path


def test_the_shipped_ledger_passes_preflight(tmp_path):
    """The real ledger against the real tree -- guards the citations, not just the parser."""
    result = run(SHIPPED, tmp_path)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["MECHANICAL_PREFLIGHT"] == "PASS"
    assert report["findings"] == []
    assert report["collected_node_ids"] > 400


def test_a_collected_citation_passes(tmp_path):
    result = run(minimal(), tmp_path)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["MECHANICAL_PREFLIGHT"] == "PASS"


def test_the_three_outputs_stay_separate(tmp_path):
    """A clean mechanical preflight must not read as a policy pass or as authority."""
    report = json.loads(run(SHIPPED, tmp_path).stdout)
    assert report["MECHANICAL_PREFLIGHT"] == "PASS"
    assert report["POLICY_REVIEW"] == "REQUIRED"
    assert report["MERGE_AUTHORITY"] == "NOT_CONFERRED"
    assert report["confers_merge_authority"] is False
    assert len(report["residual_judgement"]) >= 3


def test_a_mechanically_clean_package_still_requires_policy(tmp_path):
    """Required counterexample 12: clean preflight, unresolved architectural judgement."""
    report = json.loads(run(minimal(), tmp_path).stdout)
    assert report["MECHANICAL_PREFLIGHT"] == "PASS"
    assert report["POLICY_REVIEW"] == "REQUIRED"
    assert any("authority sufficiency" in r for r in report["residual_judgement"])


# ------------------------------------------- the collectability predicate (RF-001)


def test_a_defined_but_uncollected_citation_is_refused(tmp_path):
    """The counterexample AST checking accepts and collection rejects.

    A module inside the test roots defining a real top-level `def test_orphan()` -- but the file
    is named so pytest does not collect it. The definition is present; the node ID is not.
    """
    fake_root = tmp_path / "repo"
    (fake_root / "tests").mkdir(parents=True)
    (fake_root / "tests" / "helpers_not_collected.py").write_text(
        "def test_orphan():\n    assert True\n", encoding="utf-8")
    ledger = minimal(entry={"tests": [
        {"file": "tests/helpers_not_collected.py", "test": "test_orphan"}]})
    ledger["promoted_refusals"] = []
    path = tmp_path / "ledger.json"
    path.write_text(json.dumps(ledger), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(TOOL)], capture_output=True, text=True, check=False,
        env={**os.environ, "REPO_ROOT": str(fake_root), "LEDGER": str(path),
             "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert result.returncode == 2, result.stdout
    report = json.loads(result.stdout)
    assert any("not a node ID pytest collects" in f for f in report["findings"]), report
    assert any("runs zero times" in f for f in report["findings"])


def test_a_citation_outside_the_test_roots_is_refused(tmp_path):
    """Required counterexample 5."""
    finds(minimal(entry={"tests": [
        {"file": "scripts/check_review_preflight.py", "test": "test_main"}]}),
        tmp_path, "outside the configured test roots")


def test_a_citation_naming_a_helper_is_refused(tmp_path):
    """Required counterexample 6: `def helper()` is defined and never collected."""
    finds(minimal(entry={"tests": [
        {"file": "tests/test_review_preflight.py", "test": "minimal"}]}),
        tmp_path, "not a node ID pytest collects")


@pytest.mark.parametrize("bad", [
    "/etc/passwd",
    "tests/../scripts/check_review_preflight.py",
    "tests\\test_review_preflight.py",
])
def test_an_absolute_or_escaping_citation_is_refused(tmp_path, bad):
    """PATH_EXISTS != PATH_CONFINED -- absolute, traversing and backslash forms all refused."""
    report = finds(minimal(entry={"tests": [{"file": bad, "test": "x"}]}), tmp_path, "citation path")
    assert report["MECHANICAL_PREFLIGHT"] == "FAIL"


def test_an_unnormalised_citation_is_refused(tmp_path):
    """Two spellings of one path are two citations that cannot be compared."""
    finds(minimal(entry={"tests": [
        {"file": "tests/./test_review_preflight.py", "test": "test_a_collected_citation_passes"}]}),
        tmp_path, "not normalised")


def test_a_parametrised_citation_is_accepted(tmp_path):
    """Node IDs carry a `[param]` suffix; the bare name must still match."""
    result = run(minimal(entry={"tests": [
        {"file": "tests/test_review_preflight.py",
         "test": "test_an_absolute_or_escaping_citation_is_refused"}]}), tmp_path)
    assert result.returncode == 0, result.stderr


def test_pending_merge_citations_share_the_path_boundary(tmp_path):
    """Identical boundary: a PENDING_MERGE citation outside the roots is still refused.

    Its COLLECTION is proven at the pinned head by check_pattern_ledger.py, not here -- the file
    is absent from this tree by construction. What is checked identically is the path contract.
    """
    ledger = minimal(entry={
        "guard": "PENDING_MERGE", "pending_pr": 159,
        "pending_head": "d2a1b8bb90a2e7ea8c6bec7bf40e354e1d1513b4",
        "tests": [{"file": "scripts/nope.py", "test": "test_x"}]})
    finds(ledger, tmp_path, "outside the configured test roots")


def test_missing_test_roots_fails_closed(tmp_path):
    ledger = minimal()
    del ledger["test_roots"]
    refuses(ledger, tmp_path, "declares no test_roots")


# --------------------------------------------------- the promotion lifecycle


def test_a_record_cannot_reach_active_without_its_evidence(tmp_path):
    """Prose cannot become active by relabelling."""
    for field in ("counterexample", "guard_predicate", "mutation", "pre_review_command",
                  "positive_fixture", "residual_judgement"):
        ledger = minimal()
        del ledger["promoted_refusals"][0][field]
        stderr = refuses(ledger, tmp_path, "requires")
        assert field in stderr


def test_an_unknown_activation_state_is_refused(tmp_path):
    ledger = minimal()
    ledger["promoted_refusals"][0]["activation_state"] = "ENFORCED"
    refuses(ledger, tmp_path, "is not one of")


def test_an_origin_without_a_refused_head_is_refused(tmp_path):
    """An unreproducible refusal cannot be promoted."""
    ledger = minimal()
    del ledger["promoted_refusals"][0]["origin"]["refused_head"]
    stderr = refuses(ledger, tmp_path, "origin is missing")
    assert "cannot be reproduced" in stderr


def test_effectiveness_requires_a_denominator(tmp_path):
    ledger = minimal()
    record = ledger["promoted_refusals"][0]
    record["activation_state"] = "EFFECTIVENESS_OBSERVED"
    record["observations"] = {"opportunities": 0, "caught_pre_review": 0,
                              "escaped_to_review": 0, "false_positives": 0}
    stderr = refuses(ledger, tmp_path, "zero opportunities")
    assert "a ratio with no denominator" in stderr


def test_a_duplicate_refusal_id_is_refused(tmp_path):
    ledger = minimal()
    ledger["promoted_refusals"].append(deepcopy(ledger["promoted_refusals"][0]))
    refuses(ledger, tmp_path, "duplicate refusal_id")


def test_earlier_lifecycle_states_need_less(tmp_path):
    """An OBSERVED record needs origin and residual_judgement only -- and no more.

    This is what keeps the lifecycle usable: recording a refusal must be cheap, or nobody records
    one, and then the ledger only ever contains what someone had time to fully guard.
    """
    ledger = minimal()
    ledger["promoted_refusals"] = [{
        "refusal_id": "RF-900",
        "origin": {"pr": 164, "comment": 1, "refused_head": "0" * 40},
        "residual_judgement": "everything",
        "activation_state": "OBSERVED",
    }]
    result = run(ledger, tmp_path)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["lifecycle_tally"] == {"OBSERVED": 1}


# ------------------------------------------------------------------ the shipped records


def test_the_shipped_records_declare_their_phase_and_blockers():
    """Only RF-001 is active; the rest sit at honest earlier rungs."""
    records = {r["refusal_id"]: r for r in SHIPPED["promoted_refusals"]}
    assert records["RF-001"]["activation_state"] == "PRE_REVIEW_ACTIVE"
    assert records["RF-002"]["activation_state"] == "COUNTEREXAMPLE_REPRODUCED"
    assert "unmerged #159" in records["RF-002"]["blocked_on"]
    for identifier, record in records.items():
        assert record.get("residual_judgement"), identifier
        assert record["origin"]["refused_head"], identifier


def test_every_active_record_cites_a_collected_positive_fixture(tmp_path):
    """An active guard's own positive fixture must itself be collectable.

    Otherwise the guard is proven by a test that never runs, which is the defect one level up.
    """
    report = json.loads(run(SHIPPED, tmp_path).stdout)
    assert report["MECHANICAL_PREFLIGHT"] == "PASS"
    for record in SHIPPED["promoted_refusals"]:
        if record["activation_state"] != "PRE_REVIEW_ACTIVE":
            continue
        for citation in [record["positive_fixture"], *record["negative_fixtures"]]:
            path, _, name = citation.partition("::")
            source = (ROOT / path).read_text(encoding="utf-8")
            assert f"def {name}(" in source, citation


def test_metrics_start_at_zero_and_are_reported(tmp_path):
    """The denominators #164 asks for exist from day one, at zero, rather than being back-filled."""
    report = json.loads(run(SHIPPED, tmp_path).stdout)
    assert report["metrics"] == {"opportunities": 0, "caught_pre_review": 0,
                                 "escaped_to_review": 0, "false_positives": 0}
