"""The shadow merge queue measures ordered drainability — `SECB-WP-FWK-083` (#149).

    PR_IS_INDIVIDUALLY_MERGEABLE ≠ ORDERED_PREFIX_IS_INTEGRABLE
      ≠ INTEGRATED_RESULT_PASSES_TESTS ≠ GITHUB_REQUIRED_CHECKS_PASSED

GitHub's `mergeable` tests one PR against the base. A queue builds cumulatively, so a queue
of individually-mergeable PRs can jam. These tests run the tool against real refs with a
trivial test command, so the git behaviour is exercised rather than mocked.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check_shadow_merge_queue.py"
SCHEMA = REPO_ROOT / "config" / "shadow_merge_queue_receipt.schema.json"

OK = 0
FAIL = 2

# Two real branches, so integration is measured and not simulated.
QUEUE = "origin/feat/secb-wp-fwk-055-envelope-note-correction,origin/feat/secb-wp-fwk-069-nfr-17-correction"


def run(**env_extra) -> subprocess.CompletedProcess:
    env = {"PATH": "/usr/bin:/bin", "QUEUE": QUEUE, "TEST_COMMAND": "true",
           "TIME_BUDGET": "300"}
    env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(SCRIPT)], capture_output=True, text=True,
        cwd=str(REPO_ROOT), env=env, timeout=300,
    )


def receipt(**env_extra) -> dict:
    result = run(**env_extra)
    assert result.stdout, result.stderr
    return json.loads(result.stdout)


def test_the_merge_method_must_match_the_repositorys():
    """`MERGE_METHOD_MISMATCH`, not `PASS` — a wrong-method prefix measures a phantom tree."""
    document = receipt(MERGE_METHOD="MERGE")
    assert document["verdict"] == "MERGE_METHOD_MISMATCH"
    assert document["measurement_status"] == "REFUSED"
    assert "will never exist" in document["why"]


def test_an_ordered_queue_that_drains_is_reported_complete():
    document = receipt()
    assert document["verdict"] == "QUEUE_DRAINS_AS_ORDERED"
    assert document["measurement_status"] == "COMPLETE"
    assert document["unmeasured_suffix"] == []
    assert len(document["prefixes"]) == 2
    for record in document["prefixes"]:
        assert record["integration"] == "SQUASHED"
        assert record["tests"] == "PASS"
        assert record["synthetic_tree_sha"]


def test_each_prefix_is_cumulative_not_a_single_pr():
    """The distinction GitHub's `mergeable` cannot express."""
    prefixes = receipt()["prefixes"]
    assert len(prefixes[0]["prefix"]) == 1
    assert len(prefixes[1]["prefix"]) == 2


def test_a_failing_prefix_is_not_attributed_to_its_last_entry():
    """`FIRST_FAILING_PREFIX_AT_PR_N` ≠ `PR_N_IS_SOLE_CAUSE`."""
    document = receipt(TEST_COMMAND="false")
    assert document["verdict"] == "QUEUE_NOT_DRAINABLE_AS_ORDERED"
    assert document["first_failing_prefix_at"]
    assert "IS_SOLE_CAUSE" in document["attribution"]
    assert "property of the combination" in document["attribution"]


def test_a_budget_exhaustion_is_unproven_not_failed():
    """A timeout is not a result, and the unmeasured suffix is not failing."""
    document = receipt(TEST_COMMAND="sleep 2 && true", TIME_BUDGET="0.1")
    assert document["measurement_status"] == "INCOMPLETE"
    assert document["verdict"] == "QUEUE_DRAINABILITY_UNPROVEN"
    assert document["unmeasured_suffix"]
    assert "NOT reported as failing" in document["unmeasured_note"]


def test_the_receipt_confers_no_merge_authority():
    document = receipt()
    assert document["confers_merge_authority"] is False
    assert any("required checks" in item for item in document["not_proven"])
    assert any("optimal" in item for item in document["not_proven"])


def test_the_environment_is_recorded_because_a_pass_is_relative_to_it():
    environment = receipt()["environment"]
    assert environment["test_command"] == "true"
    assert environment["test_command_digest"].startswith("sha256:")
    assert environment["git"] and environment["python"]


def test_an_absent_queue_is_refused():
    result = run(QUEUE="")
    assert result.returncode == FAIL
    assert "QUEUE is required" in result.stderr


def test_the_schema_pins_the_honesty_fields():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert schema["properties"]["confers_merge_authority"]["const"] is False
    assert set(schema["properties"]["verdict"]["enum"]) == {
        "QUEUE_DRAINS_AS_ORDERED", "QUEUE_NOT_DRAINABLE_AS_ORDERED",
        "QUEUE_DRAINABILITY_UNPROVEN", "MERGE_METHOD_MISMATCH",
    }
    assert "unmeasured" in schema["properties"]["unmeasured_suffix"]["description"]
