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

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check_shadow_merge_queue.py"
SCHEMA = REPO_ROOT / "config" / "shadow_merge_queue_receipt.schema.json"

OK = 0
FAIL = 2

def git(*args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, timeout=60)


@pytest.fixture(scope="module")
def repo(tmp_path_factory) -> str:
    """A hermetic fixture repository, not this one.

    The first version measured real `origin/feat/...` branches. It passed locally and
    **failed in CI**, because the workflow checks out with `fetch-depth: 1` and those refs
    do not exist there — the same environment dependency documented on #139, reproduced by
    me one pull request later. Building the repository under test removes the dependency
    rather than skipping around it, and makes the conflict case deterministic instead of
    incidental.
    """
    root = tmp_path_factory.mktemp("smq-fixture") / "repo"
    root.mkdir()
    cwd = str(root)
    git("init", "-q", "-b", "main", cwd=cwd)
    git("config", "user.email", "smq@test", cwd=cwd)
    git("config", "user.name", "SMQ Test", cwd=cwd)
    (root / "shared.txt").write_text("base\n", encoding="utf-8")
    git("add", "-A", cwd=cwd)
    git("commit", "-q", "-m", "base", cwd=cwd)

    git("checkout", "-q", "-b", "first", cwd=cwd)
    (root / "shared.txt").write_text("first\n", encoding="utf-8")
    git("commit", "-qam", "first", cwd=cwd)

    # touches shared.txt differently -> conflicts once `first` is in the prefix
    git("checkout", "-q", "main", cwd=cwd)
    git("checkout", "-q", "-b", "conflicting", cwd=cwd)
    (root / "shared.txt").write_text("conflicting\n", encoding="utf-8")
    git("commit", "-qam", "conflicting", cwd=cwd)

    # touches a different file -> integrates cleanly after `first`
    git("checkout", "-q", "main", cwd=cwd)
    git("checkout", "-q", "-b", "independent", cwd=cwd)
    (root / "other.txt").write_text("other\n", encoding="utf-8")
    git("add", "-A", cwd=cwd)
    git("commit", "-q", "-m", "independent", cwd=cwd)

    git("checkout", "-q", "main", cwd=cwd)
    return cwd


DRAINS = "first,independent"
JAMS = "first,conflicting"


def run(repo: str, queue: str = DRAINS, **env_extra) -> subprocess.CompletedProcess:
    env = {"PATH": "/usr/bin:/bin", "QUEUE": queue, "BASE": "main",
           "TEST_COMMAND": "true", "TIME_BUDGET": "120"}
    env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(SCRIPT)], capture_output=True, text=True,
        cwd=repo, env=env, timeout=180,
    )


def receipt(repo: str, queue: str = DRAINS, **env_extra) -> dict:
    result = run(repo, queue, **env_extra)
    assert result.stdout, result.stderr
    return json.loads(result.stdout)


def test_the_merge_method_must_match_the_repositorys(repo):
    """`MERGE_METHOD_MISMATCH`, not `PASS` — a wrong-method prefix measures a phantom tree."""
    document = receipt(repo, MERGE_METHOD="MERGE")
    assert document["verdict"] == "MERGE_METHOD_MISMATCH"
    assert document["measurement_status"] == "REFUSED"
    assert "will never exist" in document["why"]


def test_an_ordered_queue_that_drains_is_reported_complete(repo):
    document = receipt(repo)
    assert document["verdict"] == "QUEUE_DRAINS_AS_ORDERED"
    assert document["measurement_status"] == "COMPLETE"
    assert document["unmeasured_suffix"] == []
    assert len(document["prefixes"]) == 2
    for record in document["prefixes"]:
        assert record["integration"] == "SQUASHED"
        assert record["tests"] == "PASS"
        assert record["synthetic_tree_sha"]


def test_each_prefix_is_cumulative_not_a_single_pr(repo):
    """The distinction GitHub's `mergeable` cannot express."""
    prefixes = receipt(repo)["prefixes"]
    assert len(prefixes[0]["prefix"]) == 1
    assert len(prefixes[1]["prefix"]) == 2


def test_a_conflicting_prefix_is_reported_with_its_paths(repo):
    """Integration failure, not test failure: the second entry cannot squash on top."""
    document = receipt(repo, JAMS)
    assert document["verdict"] == "QUEUE_NOT_DRAINABLE_AS_ORDERED"
    conflicted = document["prefixes"][-1]
    assert conflicted["integration"] == "CONFLICT"
    assert conflicted["tests"] == "NOT_RUN"
    assert "shared.txt" in conflicted["conflicted_paths"]


def test_a_failing_prefix_is_not_attributed_to_its_last_entry(repo):
    """`FIRST_FAILING_PREFIX_AT_PR_N` ≠ `PR_N_IS_SOLE_CAUSE`."""
    document = receipt(repo, TEST_COMMAND="false")
    assert document["verdict"] == "QUEUE_NOT_DRAINABLE_AS_ORDERED"
    assert document["first_failing_prefix_at"]
    assert "IS_SOLE_CAUSE" in document["attribution"]
    assert "property of the combination" in document["attribution"]


def test_a_budget_exhaustion_is_unproven_not_failed(repo):
    """A timeout is not a result, and the unmeasured suffix is not failing."""
    document = receipt(repo, TEST_COMMAND="sleep 2 && true", TIME_BUDGET="0.1")
    assert document["measurement_status"] == "INCOMPLETE"
    assert document["verdict"] == "QUEUE_DRAINABILITY_UNPROVEN"
    assert document["unmeasured_suffix"]
    assert "NOT reported as failing" in document["unmeasured_note"]


def test_a_test_command_that_dirties_the_tree_invalidates_the_measurement(repo):
    """The observer must not perturb the observed.

    Measured, not hypothetical: without `PYTHONDONTWRITEBYTECODE` the default test run
    wrote `__pycache__` under the sealed-evidence directory, the sealed-evidence guard
    failed, and the tool reported `QUEUE_NOT_DRAINABLE_AS_ORDERED` at the first prefix —
    a queue defect that was entirely its own. The same tree passed 175 tests when run
    cleanly. Suppressing the known contaminant is not proving there was none, so residue
    is detected too.
    """
    document = receipt(repo, TEST_COMMAND="touch contaminant.txt")
    assert document["verdict"] == "MEASUREMENT_CONTAMINATED"
    assert document["measurement_status"] == "REFUSED"
    assert "not the tree that was built" in document["why"]
    assert any("contaminant.txt" in line
               for line in document["prefixes"][-1]["contamination"])
    assert "first_failing_prefix_at" not in document, (
        "a contaminated run must not name a culprit; it produced no result"
    )


def test_bytecode_is_suppressed_so_the_default_command_does_not_self_contaminate(repo):
    document = receipt(repo, TEST_COMMAND="python3 -c \"import json\"")
    assert document["verdict"] == "QUEUE_DRAINS_AS_ORDERED"
    for record in document["prefixes"]:
        assert "contamination" not in record


def test_the_receipt_confers_no_merge_authority(repo):
    document = receipt(repo)
    assert document["confers_merge_authority"] is False
    assert any("required checks" in item for item in document["not_proven"])
    assert any("optimal" in item for item in document["not_proven"])


def test_the_environment_is_recorded_because_a_pass_is_relative_to_it(repo):
    environment = receipt(repo)["environment"]
    assert environment["test_command"] == "true"
    assert environment["test_command_digest"].startswith("sha256:")
    assert environment["git"] and environment["python"]


def test_a_dirty_primary_worktree_is_refused(repo):
    """The guard that made this suite need a clone in the first place."""
    (Path(repo) / "unexpected.txt").write_text("x", encoding="utf-8")
    try:
        result = run(repo)
        assert result.returncode == FAIL
        assert "dirty" in result.stderr
    finally:
        (Path(repo) / "unexpected.txt").unlink()


def test_an_absent_queue_is_refused(repo):
    result = run(repo, queue="")
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
