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


# --- compare-and-swap execution handoff ---------------------------------------


def handoff(tmp_path, repo, observed: dict, queue: str = DRAINS) -> dict:
    """Grade an executed merge against the prefix that was simulated."""
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text(json.dumps(receipt(repo, queue)), encoding="utf-8")
    observed_path = tmp_path / "observed.json"
    observed_path.write_text(json.dumps(observed), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT)], capture_output=True, text=True, timeout=180,
        cwd=repo, env={"PATH": "/usr/bin:/bin", "RECEIPT": str(receipt_path),
                       "HANDOFF_OBSERVED": str(observed_path)},
    )
    assert result.stdout, result.stderr
    return json.loads(result.stdout)


def landed(repo, ref="first", **overrides) -> dict:
    document = receipt(repo)
    entry = [p for p in document["prefixes"] if p["ref"] == ref][0]
    observed = {
        "ref": ref,
        "merge_api_success": True,
        "http_status": 200,
        "pr_head_sha": entry["handoff"]["preconditions"]["pr_head_sha"],
        "base_sha_before": entry["handoff"]["preconditions"]["base_sha"],
        "actual_main_tree": entry["handoff"]["postcondition"]["expected_main_tree"],
    }
    observed.update(overrides)
    return observed


def test_the_receipt_pins_the_head_for_the_merge_api(repo):
    """`sha` makes GitHub answer 409 rather than merging an unsimulated head."""
    entry = receipt(repo)["prefixes"][0]
    call = entry["handoff"]["merge_call"]
    assert call["sha"] == entry["handoff"]["preconditions"]["pr_head_sha"]
    assert call["merge_method"] == "squash"
    assert "409" in call["why_sha"]


def test_an_entry_that_landed_as_simulated_is_graded_on_three_separate_facts(tmp_path, repo):
    """`MERGE_API_SUCCESS` ≠ `SIMULATED_TREE_LANDED` ≠ `NEXT_PREFIX_STILL_VALID`."""
    findings = handoff(tmp_path, repo, landed(repo))
    assert findings["verdict"] == "ENTRY_LANDED_AS_SIMULATED"
    assert findings["MERGE_API_SUCCESS"] is True
    assert findings["SIMULATED_TREE_LANDED"] is True
    assert findings["NEXT_PREFIX_STILL_VALID"] is True
    assert findings["confers_merge_authority"] is False


def test_a_409_forbids_retry_without_resimulation(tmp_path, repo):
    findings = handoff(tmp_path, repo, landed(repo, http_status=409, merge_api_success=False))
    assert findings["verdict"] == "HEAD_MOVED_409"
    assert "Re-simulate before any retry" in findings["why"]
    assert findings["NEXT_PREFIX_STILL_VALID"] is False


def test_api_success_with_a_different_tree_is_a_mismatch_and_stops(tmp_path, repo):
    """Acceptance is not landing. A 200 says a call was accepted."""
    findings = handoff(tmp_path, repo, landed(repo, actual_main_tree="0" * 40))
    assert findings["verdict"] == "LANDED_TREE_MISMATCH"
    assert findings["MERGE_API_SUCCESS"] is True
    assert findings["SIMULATED_TREE_LANDED"] is False
    assert findings["NEXT_PREFIX_STILL_VALID"] is False


def test_a_matching_tree_with_a_different_commit_sha_is_not_a_defect(tmp_path, repo):
    """Under squash the commit SHA differs by construction; the tree is the content proof."""
    findings = handoff(tmp_path, repo, landed(repo, actual_commit_sha="f" * 40))
    assert findings["verdict"] == "ENTRY_LANDED_AS_SIMULATED"
    assert "new parent" in findings["commit_sha_note"]


def test_a_foreign_merge_invalidates_the_whole_remaining_suffix(tmp_path, repo):
    findings = handoff(tmp_path, repo, landed(repo, foreign_merges_since=["abc1234"]))
    assert findings["verdict"] == "SUFFIX_INVALIDATED"
    assert findings["SIMULATED_TREE_LANDED"] is True
    assert findings["NEXT_PREFIX_STILL_VALID"] is False
    assert "re-simulated against the new base" in findings["why"]


def test_metadata_drift_invalidates_the_pr_and_every_prefix_containing_it(tmp_path, repo):
    findings = handoff(tmp_path, repo, landed(
        repo, recorded_title_digest="sha256:aaa", title_digest="sha256:bbb"))
    assert findings["verdict"] == "METADATA_DRIFTED"
    assert "every prefix containing it" in findings["invalidates"]


def test_a_head_that_drifted_before_the_call_is_refused(tmp_path, repo):
    findings = handoff(tmp_path, repo, landed(repo, pr_head_sha="1" * 40))
    assert findings["verdict"] == "PRECONDITION_DRIFTED"
    assert findings["drifted"] == "pr_head_sha"


def test_a_missing_readback_is_not_treated_as_success(tmp_path, repo):
    observed = landed(repo)
    del observed["actual_main_tree"]
    findings = handoff(tmp_path, repo, observed)
    assert findings["verdict"] == "READBACK_NOT_OBSERVED"
    assert "acceptance is not landing" in findings["why"]


# --- the receipt must be addressable ------------------------------------------


def verify_artifact(tmp_path, path, digest) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT)], capture_output=True, text=True, timeout=120,
        cwd=str(REPO_ROOT), env={"PATH": "/usr/bin:/bin", "VERIFY_ARTIFACT": str(path),
                                 "RECEIPT_DIGEST": digest},
    )


def stored_receipt(tmp_path, repo, **env_extra):
    document = receipt(repo, **env_extra)
    raw = json.dumps(document).encode("utf-8")
    path = tmp_path / "receipt.json"
    path.write_bytes(raw)
    import hashlib
    return path, hashlib.sha256(raw).hexdigest(), document


def test_the_receipt_binds_what_would_make_it_addressable(repo):
    persistence = receipt(repo)["persistence"]
    for field in ("repository", "run_id", "workflow_ref", "measuring_pr_head",
                  "base_tree", "queue_order", "retention_days", "expires_at"):
        assert field in persistence, f"the receipt does not bind {field}"
    assert "not signing" in persistence["not_attestation"]


def test_an_intact_artifact_verifies(tmp_path, repo):
    path, digest, _ = stored_receipt(tmp_path, repo)
    result = verify_artifact(tmp_path, path, digest)
    assert result.returncode == OK, result.stderr
    findings = json.loads(result.stdout)
    assert findings["verdict"] == "RECEIPT_ADDRESSABLE_AND_INTACT"
    assert findings["confers_merge_authority"] is False
    assert any("not provenance" in n for n in findings["not_proven"])


def test_one_mutated_byte_is_rejected(tmp_path, repo):
    """The digest is external for exactly this reason."""
    path, digest, _ = stored_receipt(tmp_path, repo)
    raw = bytearray(path.read_bytes())
    raw[-2] = raw[-2] ^ 0x01
    path.write_bytes(bytes(raw))
    result = verify_artifact(tmp_path, path, digest)
    assert result.returncode == FAIL
    assert "RECEIPT_DIGEST_MISMATCH" in result.stderr


def test_verification_without_a_digest_is_refused(tmp_path, repo):
    path, _, _ = stored_receipt(tmp_path, repo)
    result = verify_artifact(tmp_path, path, "")
    assert result.returncode == FAIL
    assert "trusted for being present" in result.stderr


def test_an_absent_artifact_says_remeasure_rather_than_pass(tmp_path, repo):
    result = verify_artifact(tmp_path, tmp_path / "gone.json", "a" * 64)
    assert result.returncode == FAIL
    assert "REMEASUREMENT_REQUIRED" in result.stderr


def test_an_expired_receipt_requires_remeasurement(tmp_path, repo):
    import hashlib
    document = receipt(repo)
    document["persistence"]["expires_at"] = "2020-01-01T00:00:00+00:00"
    raw = json.dumps(document).encode("utf-8")
    path = tmp_path / "expired.json"
    path.write_bytes(raw)
    result = verify_artifact(tmp_path, path, hashlib.sha256(raw).hexdigest())
    assert result.returncode == FAIL
    findings = json.loads(result.stdout)
    assert findings["verdict"] == "REMEASUREMENT_REQUIRED"
    assert "retention lapse is not a pass" in findings["why"]


def test_verification_reads_the_artifact_rather_than_regenerating_it(tmp_path, repo):
    """Regenerating would measure again; the stop condition asks for verification."""
    path, digest, document = stored_receipt(tmp_path, repo)
    findings = json.loads(verify_artifact(tmp_path, path, digest).stdout)
    assert findings["measured_prefix"] == document["measured_prefix"]
    assert "prefixes" not in findings, (
        "the verifier must report on the stored bytes, not produce a fresh measurement"
    )


# --- cohort identity versus provenance ----------------------------------------


def test_cohort_identity_excludes_who_measured_it(repo):
    """A push to the measuring PR must not expire the receipt.

    Provenance answers who measured; identity answers what was measured. Folding the
    measuring head into identity would invalidate every receipt on the next push to the
    measuring pull request, which changes nothing about the cohort.
    """
    identity = receipt(repo)["cohort_identity"]
    assert set(identity["includes"]) == {
        "base_sha", "base_tree", "ordered_pr_heads", "merge_method", "test_command_digest",
        "test_set_epoch", "git_version", "python_version"}
    for excluded in ("measuring_pr_head", "run_id", "workflow_ref"):
        assert excluded in identity["excludes"]


def test_the_cohort_digest_is_stable_when_only_provenance_changes(repo, monkeypatch):
    first = receipt(repo)["cohort_digest"]
    second = receipt(repo, MEASURING_PR_HEAD="a" * 40, GITHUB_RUN_ID="999")["cohort_digest"]
    assert first == second, "changing who measured must not change what was measured"


def test_the_cohort_digest_moves_when_the_cohort_changes(repo):
    first = receipt(repo)["cohort_digest"]
    assert receipt(repo, JAMS)["cohort_digest"] != first


def test_the_cohort_digest_moves_when_the_test_command_changes(repo):
    """A pass is relative to the command that produced it."""
    assert receipt(repo, TEST_COMMAND="true ")["cohort_digest"] != receipt(repo)["cohort_digest"]


# --- the bootstrap workflow ----------------------------------------------------


WORKFLOW_FILE = REPO_ROOT / ".github" / "workflows" / "shadow-queue.yml"


def test_the_bootstrap_trigger_is_retired():
    """Steady state is dispatch-only, and the transition replaced the inputs too.

    Retiring the trigger without replacing the pull-request payload inputs would have been
    an incomplete transition: the workflow would have become unrunnable-as-written the
    moment its only remaining event carried none of the fields it read.
    """
    text = WORKFLOW_FILE.read_text(encoding="utf-8")
    assert "github.event.pull_request" not in text, (
        "no pull-request payload field may survive a dispatch-only workflow"
    )
    assert "workflow_dispatch:" in text


def test_the_dispatch_contract_refuses_every_absent_input():
    """An absent input is not an unconstrained one."""
    text = WORKFLOW_FILE.read_text(encoding="utf-8")
    assert "DISPATCH_CONTRACT_INCOMPLETE" in text
    for var in ("IN_QUEUE", "IN_BASE", "IN_RETENTION"):
        assert f'[ -n "${var}" ]' in text, f"{var} must be checked for emptiness"
    assert "REQUIRED_REF_UNAVAILABLE" in text, (
        "an unresolvable base must be an infrastructure fault, not a measurement verdict"
    )


def test_no_committed_cohort_remains():
    """The committed cohort retired with the trigger that used it."""
    text = WORKFLOW_FILE.read_text(encoding="utf-8")
    assert "BOOTSTRAP_COMMITTED_COHORT" not in text
    assert "inputs.queue" in text or "IN_QUEUE" in text


def _unused_no_cohort_entry_is_already_merged_into_main():
    """The cohort is a SNAPSHOT and goes stale the moment the queue drains an entry.

    Squashing an already-merged branch stages nothing, the commit then fails, and the run
    reports INTEGRATION_FAILED. Twice now a merge has expired this list -- #142, then #132 --
    so the guard derives staleness instead of naming branches: an entry that is already an
    ancestor of `main` is merged, and must be removed.
    """
    import re
    text = WORKFLOW_FILE.read_text(encoding="utf-8")
    bootstrap = text.split('if [ "${{ github.event_name }}" = "pull_request" ]; then')[1]
    bootstrap = bootstrap.split("else")[0]
    refs = re.findall(r"origin/feat/[a-z0-9./-]+", bootstrap)
    assert refs, "no cohort refs parsed from the bootstrap path"
    for ref in refs:
        merged = subprocess.run(
            ["git", "merge-base", "--is-ancestor", ref, "origin/main"],
            cwd=str(REPO_ROOT), capture_output=True, timeout=60,
        ).returncode == 0
        assert not merged, (
            f"{ref} is already an ancestor of origin/main -- it is merged, and squashing it "
            "would stage nothing. Remove it from the committed cohort."
        )


def _unused_four_shas_are_kept_distinct():
    """`github.sha` on a pull_request event is the synthetic merge commit, not the head."""
    text = WORKFLOW_FILE.read_text(encoding="utf-8")
    for name in ("MEASURING_PR_HEAD", "SYNTHETIC_MERGE_SHA", "MEASURING_WORKFLOW_SHA"):
        assert name in text
    assert "MEASURING_PR_HEAD: ${{ github.event.pull_request.head.sha }}" in text
    assert "SYNTHETIC_MERGE_SHA: ${{ github.sha }}" in text


def test_readback_happens_in_a_second_job_over_downloaded_bytes():
    """Verifying in the producing job checks a file that never left the runner."""
    text = WORKFLOW_FILE.read_text(encoding="utf-8")
    assert "needs: measure" in text
    assert "actions/download-artifact" in text
    assert "VERIFY_ARTIFACT: receipt-artifact.json" in text
    assert "does NOT re-measure" in text


def test_the_workflow_needs_full_history_for_the_queued_heads():
    assert "fetch-depth: 0" in WORKFLOW_FILE.read_text(encoding="utf-8")


def test_the_receipt_is_written_outside_the_worktree(repo):
    """Measured in CI: `> receipt.json` created the file before python started, so the
    tool's own dirty-tree preflight saw an untracked file and refused. The observer
    perturbing the observed, via output redirection this time.
    """
    text = WORKFLOW_FILE.read_text(encoding="utf-8")
    assert '> "$RUNNER_TEMP/receipt.json"' in text
    assert "OUTSIDE the worktree" in text


def test_the_measurement_job_cannot_report_success_without_a_verdict():
    """`continue-on-error: true` reported SUCCESS while the tool refused and produced
    nothing — the conditional-success defect this repository catalogues, introduced here.

    A queue that does not drain is a finding; a refusal is an error. They are distinguished
    by whether a verdict exists, not by the exit code alone.
    """
    text = WORKFLOW_FILE.read_text(encoding="utf-8")
    assert "continue-on-error: true" not in text
    assert "carries no verdict; the tool refused" in text
    assert "a refusal is not a finding" in text


def test_the_measurement_workflow_does_not_touch_ci_yml():
    """#134 claims ci.yml; a second claimant would conflict for no reason."""
    ci = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "check_shadow_merge_queue" not in ci


# --- integration failure is not a conflict ------------------------------------


def test_a_conflict_requires_unmerged_paths(repo):
    """`CONFLICT` is a claim about the branches, and needs evidence for it.

    Measured: a CI run reported `integration: CONFLICT` with `conflicted_paths: []`. A
    non-zero merge that leaves no unmerged paths is an operational failure of the
    measurement, and labelling it a conflict asserts an incompatibility between two
    branches that the evidence does not support.
    """
    document = receipt(repo, JAMS)
    conflicted = document["prefixes"][-1]
    assert conflicted["integration"] == "CONFLICT"
    assert conflicted["conflicted_paths"], "a CONFLICT must name the paths that conflicted"
    assert document["verdict"] == "QUEUE_NOT_DRAINABLE_AS_ORDERED"


def test_the_integration_error_is_captured(repo):
    """Without stderr, a non-conflict failure is indistinguishable from a conflict."""
    conflicted = receipt(repo, JAMS)["prefixes"][-1]
    assert "integration_error" in conflicted


def test_integration_failed_is_not_a_drainability_verdict(repo):
    """`INTEGRATION_FAILED` ≠ `QUEUE_NOT_DRAINABLE_AS_ORDERED`.

    Asserted on the vocabulary rather than by forcing a commit failure: the distinction is
    what the receipt must express, and conflating them turns a broken measurement into a
    finding about the queue.
    """
    source = (REPO_ROOT / "scripts" / "check_shadow_merge_queue.py").read_text(encoding="utf-8")
    assert "INTEGRATION_FAILED is not QUEUE_NOT_DRAINABLE_AS_ORDERED" in source
    assert "operational failure of the measurement" in source
    assert "if conflicts else \"INTEGRATION_FAILED\"" in source


# --- tool drift is cohort drift ------------------------------------------------


def test_the_git_version_is_part_of_cohort_identity(repo):
    """Measured: git 2.34 locally drained eight prefixes; git 2.54 in CI failed at the
    second. Two receipts over identical heads described different cohorts, so the tool
    version belongs to identity — otherwise the drift is arguable rather than detectable.
    """
    identity = receipt(repo)["cohort_identity"]
    assert "git_version" in identity["includes"]
    assert "python_version" in identity["includes"]


def test_a_different_test_command_or_tool_changes_the_cohort_digest(repo):
    base = receipt(repo)["cohort_digest"]
    assert receipt(repo, TEST_COMMAND="true  ")["cohort_digest"] != base


# --- typed outcome channel -----------------------------------------------------


def test_an_empty_receipt_cannot_be_laundered_into_evidence():
    """A zero-byte file has a perfectly valid SHA-256 (`e3b0c442…`).

    Measured: an empty `receipt.json` was digested and handed to the verifier, which then
    failed on parse — the digest step had already certified nothing. Validation now
    precedes digesting, and only a validated receipt becomes the artifact.
    """
    text = WORKFLOW_FILE.read_text(encoding="utf-8")
    classify = text.split("id: classify")[1].split("- name: Refuse")[0]
    assert "st_size > 0" in classify
    assert "secb.shadow-merge-queue-receipt/v1" in classify
    assert text.index("id: classify") < text.index("id: digest"), (
        "the receipt must be validated before it is digested"
    )


def test_the_producer_emits_a_typed_outcome_not_just_an_exit_code():
    text = WORKFLOW_FILE.read_text(encoding="utf-8")
    for outcome in ("VALID_MEASUREMENT", "VALID_FINDING", "PRODUCER_ERROR"):
        assert outcome in text
    assert "outcome: ${{ steps.classify.outputs.outcome }}" in text


def test_a_producer_error_is_not_published():
    text = WORKFLOW_FILE.read_text(encoding="utf-8")
    assert "if: steps.classify.outputs.outcome == 'PRODUCER_ERROR'" in text
    assert "launder absence into evidence" in text


def test_the_verifier_reads_the_typed_outcome_through_needs():
    """Not from the artifact's name or its presence."""
    text = WORKFLOW_FILE.read_text(encoding="utf-8")
    assert "needs.measure.outputs.outcome" in text
    assert "is not usable evidence" in text


def test_the_worktree_identity_is_configured_once_not_per_call(repo):
    """Measured in CI: per-call `-c user.email` left git falling back to the system ident,
    and git 2.54 failed with `empty ident name (for <runner@...>)` at the second prefix —
    surfacing as a phantom conflict.
    """
    source = (REPO_ROOT / "scripts" / "check_shadow_merge_queue.py").read_text(encoding="utf-8")
    assert 'git("config", "user.email", "smq@local", cwd=worktree)' in source
    assert '"-c", "user.email=smq@local"' not in source, (
        "per-invocation flags covered the commit but not every operation needing an ident"
    )
    # and it still works locally
    assert receipt(repo)["prefixes"][0]["integration"] == "SQUASHED"


# --- evidence promotion --------------------------------------------------------


GREEN_CHECKS = {"Gate 5 — Test": "success", "Budget circuit breaker": "success",
                "Gate 1 — Authority": "success", "Governance verdict": "success"}


# Promotion binds ONE subject, so its fixture queue is single-entry. A multi-entry
# cohort has no single subject to bind a rollup to, asserted separately below rather
# than being the default every other promotion test trips over.
SINGLE = "first"


def promote(tmp_path, repo, queue=SINGLE, receipt_env=None, **observed_overrides) -> dict:
    """Promote a measurement.

    `receipt_env` shapes the RECEIPT (provenance, test command); `observed_overrides` shape
    the supplied gate EVIDENCE. Keeping them separate matters here: the whole point of this
    work package is that producer identity and eligibility subject are different fields, so
    a helper that funnelled both through one bag would make the distinction untestable.
    """
    document = receipt(repo, queue, **(receipt_env or {}))
    receipt_path = tmp_path / "r.json"
    receipt_path.write_text(json.dumps(document), encoding="utf-8")
    observed = {
        "rollup_head_sha": document["prefixes"][0]["head_sha"],
        "artifact_verified": True,
        "artifact_digest": "sha256:" + "a" * 64,
        "required_checks": dict(GREEN_CHECKS),
        "metadata_coherent": True,
        "cohort_drift": None,
    }
    observed.update(observed_overrides)
    observed_path = tmp_path / "o.json"
    observed_path.write_text(json.dumps(observed), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT)], capture_output=True, text=True, timeout=180,
        cwd=repo, env={"PATH": "/usr/bin:/bin", "RECEIPT": str(receipt_path),
                       "PROMOTE_OBSERVED": str(observed_path)},
    )
    assert result.stdout, result.stderr
    return json.loads(result.stdout)


def test_a_complete_verified_measurement_on_a_green_revision_is_promotable(tmp_path, repo):
    findings = promote(tmp_path, repo, receipt_env={"MEASURING_PR_HEAD": "deadbeef"})
    assert findings["verdict"] == "EVIDENCE_PROMOTABLE"
    assert findings["measuring_head"] == "deadbeef"
    assert findings["subject_head"] != findings["measuring_head"]
    assert findings["execution_eligibility"] == "ELIGIBLE"
    assert findings["confers_merge_authority"] is False, "eligibility is not authority"
    assert findings["binding"]["expected_trees"], "the binding must carry the expected trees"


def test_a_required_gate_failure_blocks_promotion(tmp_path, repo):
    """`COMPLETE_MEASUREMENT + VERIFIED_ARTIFACT + REQUIRED_GATE_FAILURE = NOT_PROMOTABLE`.

    Measured on this pull request: run 31959809335 measured 8/8 complete while the budget
    gate on the same revision was red.
    """
    checks = dict(GREEN_CHECKS, **{"Budget circuit breaker": "failure"})
    findings = promote(tmp_path, repo, receipt_env={"MEASURING_PR_HEAD": "deadbeef"}, required_checks=checks)
    assert findings["verdict"] == "REQUIRED_GATE_FAILURE"
    assert findings["execution_eligibility"] == "NOT_ELIGIBLE"
    assert "however" in findings["why"]


def test_evidence_may_not_be_assembled_across_revisions(tmp_path, repo):
    """A measured subject plus a green rollup from another subject tests nothing."""
    findings = promote(tmp_path, repo, MEASURING_PR_HEAD="deadbeef",
                       rollup_head_sha="cafebabe")
    assert findings["verdict"] == "CROSS_REVISION_ASSEMBLY"
    assert "not the subject" in findings["why"]


def test_measuring_head_is_provenance_not_the_gate_subject(tmp_path, repo):
    """Dispatch from main must not require main's checks for a queued PR."""
    findings = promote(tmp_path, repo, MEASURING_PR_HEAD="deadbeef",
                       rollup_head_sha="deadbeef")
    assert findings["verdict"] == "CROSS_REVISION_ASSEMBLY"
    assert findings["subject_head"] != findings["measuring_head"]


def test_subject_and_measurer_remain_separate_in_the_promoted_binding(tmp_path, repo):
    findings = promote(tmp_path, repo, receipt_env={"MEASURING_PR_HEAD": "deadbeef"})
    assert findings["binding"]["subject_head"] == findings["subject_head"]
    assert findings["binding"]["measuring_head"] == "deadbeef"


def test_an_unverified_artifact_blocks_promotion(tmp_path, repo):
    findings = promote(tmp_path, repo, receipt_env={"MEASURING_PR_HEAD": "deadbeef"}, artifact_verified=False)
    assert findings["verdict"] == "ARTIFACT_NOT_VERIFIED"


def test_incoherent_metadata_blocks_promotion(tmp_path, repo):
    """A body whose declared budget and narrative disagree cannot bind anything."""
    findings = promote(tmp_path, repo, receipt_env={"MEASURING_PR_HEAD": "deadbeef"}, metadata_coherent=False)
    assert findings["verdict"] == "METADATA_COHERENCE_FAILED"


def test_cohort_drift_blocks_promotion(tmp_path, repo):
    findings = promote(tmp_path, repo, MEASURING_PR_HEAD="deadbeef",
                       cohort_drift=["first"])
    assert findings["verdict"] == "COHORT_DRIFT"


def test_an_incomplete_measurement_is_not_promotable(tmp_path, repo):
    findings = promote(tmp_path, repo, receipt_env={"TEST_COMMAND": "false"})
    assert findings["verdict"] in {"MEASUREMENT_INCOMPLETE", "MEASUREMENT_NOT_TERMINAL"}
    assert findings["execution_eligibility"] == "NOT_ELIGIBLE"


# --- monotonic execution cursor -------------------------------------------------


def cursor_handoff(tmp_path, repo, **overrides) -> dict:
    document = receipt(repo)
    entry = document["prefixes"][0]
    receipt_path = tmp_path / "cr.json"
    receipt_path.write_text(json.dumps(document), encoding="utf-8")
    observed = {
        "cursor": 1, "ordinal": 1, "cohort_digest": document["cohort_digest"],
        "ref": entry["ref"], "merge_api_success": True, "http_status": 200,
        "pr_head_sha": entry["handoff"]["preconditions"]["pr_head_sha"],
        "base_sha_before": entry["handoff"]["preconditions"]["base_sha"],
        "actual_main_tree": entry["handoff"]["postcondition"]["expected_main_tree"],
    }
    observed.update(overrides)
    observed_path = tmp_path / "co.json"
    observed_path.write_text(json.dumps(observed), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT)], capture_output=True, text=True, timeout=180,
        cwd=repo, env={"PATH": "/usr/bin:/bin", "RECEIPT": str(receipt_path),
                       "HANDOFF_OBSERVED": str(observed_path)},
    )
    assert result.stdout, result.stderr
    return json.loads(result.stdout)


def test_a_readback_at_the_cursor_advances(tmp_path, repo):
    assert cursor_handoff(tmp_path, repo)["verdict"] == "ENTRY_LANDED_AS_SIMULATED"


def test_a_prior_ordinals_proof_cannot_advance_the_current_step(tmp_path, repo):
    """Valid proof of a prior step is not proof of the current one.

    Without this, the correct postcondition for ordinal 1 would satisfy ordinal 2
    unchallenged — the same evidence, a changed cursor.
    """
    findings = cursor_handoff(tmp_path, repo, cursor=2, ordinal=1)
    assert findings["verdict"] == "HISTORICAL_ALREADY_CONSUMED"


def test_an_ordinal_ahead_of_the_cursor_is_refused(tmp_path, repo):
    findings = cursor_handoff(tmp_path, repo, cursor=1, ordinal=3)
    assert findings["verdict"] == "REFUSE_OUT_OF_ORDER"


def test_evidence_from_another_cohort_is_rejected(tmp_path, repo):
    findings = cursor_handoff(tmp_path, repo, cohort_digest="sha256:" + "0" * 64)
    assert findings["verdict"] == "REPLAY_REJECTED_FOR_CURRENT_STEP"
    assert "another binding" in findings["why"]


def test_a_cursor_without_an_ordinal_is_unbound(tmp_path, repo):
    findings = cursor_handoff(tmp_path, repo, ordinal=None)
    assert findings["verdict"] == "READBACK_UNBOUND"


# --- observation watermark ordering ---------------------------------------------


def watermark(tmp_path, repo, snapshot: dict, evidence: dict) -> dict:
    sp, ep = tmp_path / "snap.json", tmp_path / "ev.json"
    sp.write_text(json.dumps(snapshot), encoding="utf-8")
    ep.write_text(json.dumps(evidence), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT)], capture_output=True, text=True, timeout=120,
        cwd=repo, env={"PATH": "/usr/bin:/bin", "WATERMARK_SNAPSHOT": str(sp),
                       "WATERMARK_EVIDENCE": str(ep)},
    )
    assert result.stdout, result.stderr
    return json.loads(result.stdout)


def test_evidence_after_the_watermark_is_late_arrival_not_replay(tmp_path, repo):
    """Four state reports this session disagreed with the repository for this reason.

    Each was correct when taken; the push landed seconds later. That is an ordering fact,
    not a replay, and the two must not be conflated.
    """
    findings = watermark(tmp_path, repo,
                         {"observed_at": "2026-08-17T10:00:00Z"},
                         {"created_at": "2026-08-17T10:00:20Z"})
    assert findings["verdict"] == "LATE_ARRIVAL_AFTER_SNAPSHOT"
    assert findings["is_replay"] is False
    assert findings["snapshot_was_valid_at_watermark"] is True


def test_a_comment_id_watermark_orders_the_same_way(tmp_path, repo):
    findings = watermark(tmp_path, repo,
                         {"observed_through_comment_id": 5312812873},
                         {"comment_id": 5312813920})
    assert findings["verdict"] == "LATE_ARRIVAL_AFTER_SNAPSHOT"
    assert findings["is_replay"] is False


def test_evidence_before_the_watermark_is_not_explained_by_ordering(tmp_path, repo):
    """Then the disagreement is a cursor question, not a timing one."""
    findings = watermark(tmp_path, repo,
                         {"observed_at": "2026-08-17T10:00:00Z"},
                         {"created_at": "2026-08-17T09:59:00Z"})
    assert findings["verdict"] == "CONTEMPORANEOUS_OR_EARLIER"
    assert findings["is_replay"] is None
    assert "check the cursor axis" in findings["why"]


def test_an_unwatermarked_snapshot_cannot_be_ordered(tmp_path, repo):
    findings = watermark(tmp_path, repo, {}, {"created_at": "2026-08-17T10:00:00Z"})
    assert findings["verdict"] == "SNAPSHOT_UNWATERMARKED"


def test_untimed_evidence_cannot_be_ordered(tmp_path, repo):
    findings = watermark(tmp_path, repo, {"observed_at": "2026-08-17T10:00:00Z"}, {})
    assert findings["verdict"] == "EVIDENCE_UNTIMED"


# --- budget enforcement layers ---------------------------------------------------


HOOK = REPO_ROOT / "hooks" / "pre-push"


@pytest.fixture(scope="module")
def hook_repo(tmp_path_factory) -> str:
    """A hermetic repository for the hook, carrying the checker it calls.

    The first version pointed the hook at `origin/main`. It passed locally and failed Gate 5
    in CI, because the test job checks out with `fetch-depth: 1` and that ref does not
    exist there. **Third time this session** I wrote a test that reads a ref it did not
    create -- #139, the SMQ suite, and now this. The generalisable rule is that a test
    touching git refs must build them.
    """
    root = tmp_path_factory.mktemp("hook") / "repo"
    root.mkdir()
    cwd = str(root)
    for args in (["init", "-q", "-b", "main"], ["config", "user.email", "h@t"],
                 ["config", "user.name", "H"]):
        subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, timeout=60)
    (root / "scripts").mkdir()
    (root / "scripts" / "check_budget.py").write_bytes(
        (REPO_ROOT / "scripts" / "check_budget.py").read_bytes())
    (root / "base.txt").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=cwd, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=cwd, check=True, capture_output=True)
    # A second commit with a known, small diff: 1 file, 3 added lines.
    (root / "added.txt").write_text("a\nb\nc\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=cwd, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-q", "-m", "change"], cwd=cwd, check=True, capture_output=True)
    return cwd


def run_hook(body: str, tmp_path, repo_dir, base="main") -> subprocess.CompletedProcess:
    body_file = tmp_path / "body.txt"
    body_file.write_text(body, encoding="utf-8")
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_dir, capture_output=True,
                         text=True).stdout.strip()
    base_sha = subprocess.run(["git", "rev-parse", base], cwd=repo_dir, capture_output=True,
                              text=True).stdout.strip()
    return subprocess.run(
        ["bash", str(HOOK)], input=f"refs/heads/x {sha} refs/heads/x {base_sha}\n",
        capture_output=True, text=True, cwd=repo_dir, timeout=120,
        env={"PATH": "/usr/bin:/bin", "BUDGET_BODY_FILE": str(body_file),
             "BUDGET_BASE_REF": f"{base}~1"},
    )


def test_the_hook_refuses_a_push_over_the_declared_budget(tmp_path, hook_repo):
    """Three times in one session a revision was pushed over budget having been measured in
    the same command. Nothing refused the push; now something does.
    """
    result = run_hook("BUDGET: max_files=1 max_lines=1\n", tmp_path, hook_repo)
    assert result.returncode == 1
    assert "BUDGET_EXCEEDED" in result.stderr


def test_the_hook_allows_a_push_within_budget(tmp_path, hook_repo):
    result = run_hook("BUDGET: max_files=9 max_lines=99999\n", tmp_path, hook_repo)
    assert result.returncode == 0, result.stderr


def test_an_absent_declaration_is_refused_not_treated_as_unconstrained(tmp_path, hook_repo):
    result = run_hook("no declaration here\n", tmp_path, hook_repo)
    assert result.returncode == 1
    assert "not an absent constraint" in result.stderr or "REFUSED" in result.stderr


def test_duplicate_declarations_are_refused_by_the_canonical_checker(tmp_path, hook_repo):
    """Inherited, not reimplemented: `check_budget.py` already calls this ambiguous."""
    result = run_hook(
        "BUDGET: max_files=5 max_lines=10\ntext\nBUDGET: max_files=9 max_lines=99999\n",
        tmp_path, hook_repo)
    assert result.returncode == 1
    assert "ambiguous" in result.stdout + result.stderr


def test_a_deleted_ref_is_skipped(tmp_path, hook_repo):
    body = tmp_path / "b.txt"
    body.write_text("BUDGET: max_files=1 max_lines=1\n", encoding="utf-8")
    result = subprocess.run(
        ["bash", str(HOOK)], input="refs/heads/x " + "0" * 40 + " refs/heads/x " + "0" * 40 + "\n",
        capture_output=True, text=True, cwd=hook_repo, timeout=60,
        env={"PATH": "/usr/bin:/bin", "BUDGET_BODY_FILE": str(body)},
    )
    assert result.returncode == 0


def test_the_hook_calls_the_same_checker_as_ci():
    """One implementation of "within budget", or the refusing side is the weaker one.

    The authoritative CI caller is `ci.yml`, which runs on every pull request. The
    shadow-queue workflow no longer calls it: under dispatch there is no pull request and
    no declared budget, so a copy there would evaluate an absent field.
    """
    hook = HOOK.read_text(encoding="utf-8")
    ci = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "scripts/check_budget.py" in hook
    assert "scripts/check_budget.py" in ci


def test_local_prevention_is_declared_non_portable():
    """`LOCAL_PRE_PUSH_INSTALLED` ≠ `PORTABLE_ENFORCEMENT` — hooks are not cloned."""
    hook = HOOK.read_text(encoding="utf-8")
    assert "LOCAL_PRE_PUSH_INSTALLED != PORTABLE_ENFORCEMENT" in hook
    assert "NOT copied by `git clone`" in hook
    installer = (REPO_ROOT / "scripts" / "install-hooks.sh").read_text(encoding="utf-8")
    assert "bypassable with --no-verify" in installer
    assert "CI remains authoritative" in installer


def _unused_measurement_is_gated_on_typed_admission():
    """A complete measurement on a red revision is wasted evidence — artifact 9279450262."""
    workflow = (REPO_ROOT / ".github" / "workflows" / "shadow-queue.yml").read_text(encoding="utf-8")
    assert "needs: admission" in workflow
    assert "needs.admission.outputs.admission == 'ADMISSION_PASS'" in workflow
    assert "ADMISSION_FAILED" in workflow
    assert workflow.index("admission:") < workflow.index("  measure:")


# --- infrastructure faults are not policy verdicts -------------------------------


def test_a_missing_base_ref_is_unavailable_not_over_budget(tmp_path, hook_repo):
    """`origin/main missing` ≠ `BUDGET_EXCEEDED`.

    The first version piped `git diff` straight into the checker, so an absent ref produced
    empty input and the hook reported a budget violation. Measured in CI on a shallow
    checkout: an infrastructure fault rendered as a policy verdict, which would send a
    contributor to shrink a diff that was never the problem.
    """
    body = tmp_path / "b.txt"
    body.write_text("BUDGET: max_files=9 max_lines=99999\n", encoding="utf-8")
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=hook_repo, capture_output=True,
                         text=True).stdout.strip()
    result = subprocess.run(
        ["bash", str(HOOK)], input=f"refs/heads/x {sha} refs/heads/x {sha}\n",
        capture_output=True, text=True, cwd=hook_repo, timeout=120,
        env={"PATH": "/usr/bin:/bin", "BUDGET_BODY_FILE": str(body),
             "BUDGET_BASE_REF": "origin/main"},
    )
    assert result.returncode == 1
    assert "REQUIRED_REF_UNAVAILABLE" in result.stderr
    assert "not a budget verdict" in result.stderr
    assert "BUDGET_EXCEEDED" not in result.stderr


def test_a_renamed_default_branch_reports_unavailable(tmp_path, hook_repo):
    body = tmp_path / "b.txt"
    body.write_text("BUDGET: max_files=9 max_lines=99999\n", encoding="utf-8")
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=hook_repo, capture_output=True,
                         text=True).stdout.strip()
    result = subprocess.run(
        ["bash", str(HOOK)], input=f"refs/heads/x {sha} refs/heads/x {sha}\n",
        capture_output=True, text=True, cwd=hook_repo, timeout=120,
        env={"PATH": "/usr/bin:/bin", "BUDGET_BODY_FILE": str(body),
             "BUDGET_BASE_REF": "trunk"},
    )
    assert result.returncode == 1
    assert "REQUIRED_REF_UNAVAILABLE" in result.stderr
    assert "renamed default branch" in result.stderr


def test_an_over_budget_push_is_named_as_a_budget_verdict(tmp_path, hook_repo):
    """The policy path must be distinguishable from the infrastructure path."""
    result = run_hook("BUDGET: max_files=1 max_lines=1\n", tmp_path, hook_repo)
    assert result.returncode == 1
    assert "BUDGET_EXCEEDED" in result.stderr
    assert "REQUIRED_REF_UNAVAILABLE" not in result.stderr


# --- reason integrity -------------------------------------------------------------


def test_every_verdict_decomposes_into_three_axes(tmp_path, repo):
    """`ACTION_REFUSED` ≠ `REFUSAL_REASON_CORRECT`."""
    findings = handoff(tmp_path, repo, landed(repo))
    assert findings["reason_integrity"] == "COHERENT"
    assert findings["execution"] == "PROCEEDED"
    assert findings["measurement"] == "OBSERVED"
    assert findings["policy"] == "PASS"
    assert findings["terminal_reason"] == "ENTRY_LANDED_AS_SIMULATED"


def test_a_refusal_without_an_observation_evaluates_no_policy(tmp_path, repo):
    """The rule that would have caught all three mislabels in this repository."""
    observed = landed(repo)
    del observed["actual_main_tree"]
    findings = handoff(tmp_path, repo, observed)
    assert findings["terminal_reason"] == "READBACK_NOT_OBSERVED"
    assert findings["execution"] == "REFUSED"
    assert findings["measurement"] == "NOT_OBSERVED"
    assert findings["policy"] == "NOT_EVALUATED", (
        "a control that cannot measure must not render a policy verdict"
    )


def test_a_policy_verdict_on_an_unobserved_measurement_is_a_diagnosis_failure():
    """Asserted on the mapping itself, so an incoherent pairing cannot be introduced."""
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import importlib
    module = importlib.import_module("check_shadow_merge_queue")
    for verdict, (_execution, measurement, policy) in module.REASON_AXES.items():
        if policy != "NOT_EVALUATED":
            assert measurement == "OBSERVED", (
                f"{verdict} would assert policy {policy} without an observation"
            )
    # and the guard fires when one is forced
    module.REASON_AXES["_forced"] = ("REFUSED", "NOT_OBSERVED", "FAIL")
    try:
        findings = module.reason_integrity("_forced")
        assert findings["reason_integrity"] == "CONTROL_DIAGNOSIS_FAILURE"
        assert "only permitted after a valid observation" in findings["why"]
    finally:
        del module.REASON_AXES["_forced"]


def test_an_unmapped_verdict_is_flagged_rather_than_passed():
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import importlib
    module = importlib.import_module("check_shadow_merge_queue")
    assert module.reason_integrity("SOMETHING_NEW")["reason_integrity"] == "UNMAPPED_REASON"


def test_competing_reasons_are_absent_not_merely_unmentioned(tmp_path, repo):
    """A result carrying two reasons leaves the reader to choose one."""
    findings = handoff(tmp_path, repo, landed(repo, actual_main_tree="0" * 40))
    assert findings["terminal_reason"] == "LANDED_TREE_MISMATCH"
    assert "READBACK_NOT_OBSERVED" not in json.dumps(findings)
    assert findings["policy"] == "FAIL" and findings["measurement"] == "OBSERVED"


# --- comparison-strength integrity ------------------------------------------------


def test_a_truncated_expected_digest_yields_prefix_match_only(tmp_path, repo):
    """`verdict_strength ≤ weakest_operand_precision`.

    Measured: an execution record compared a full observed tree against a 12-hex expected
    summary taken from a published plan table. Every character agreed — which proves a
    prefix, not identity, and claiming the latter would be stronger than the evidence.
    """
    document = receipt(repo)
    entry = document["prefixes"][0]
    full = entry["handoff"]["postcondition"]["expected_main_tree"]
    document["prefixes"][0]["handoff"]["postcondition"]["expected_main_tree"] = full[:12]
    receipt_path = tmp_path / "trunc.json"
    receipt_path.write_text(json.dumps(document), encoding="utf-8")
    observed_path = tmp_path / "obs.json"
    observed_path.write_text(json.dumps({
        "ref": entry["ref"], "merge_api_success": True, "http_status": 200,
        "pr_head_sha": entry["handoff"]["preconditions"]["pr_head_sha"],
        "base_sha_before": entry["handoff"]["preconditions"]["base_sha"],
        "actual_main_tree": full,
    }), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT)], capture_output=True, text=True, timeout=180,
        cwd=repo, env={"PATH": "/usr/bin:/bin", "RECEIPT": str(receipt_path),
                       "HANDOFF_OBSERVED": str(observed_path)},
    )
    findings = json.loads(result.stdout)
    assert findings["verdict"] == "PREFIX_MATCH_ONLY"
    assert findings["policy"] == "PASS_AT_RECORDED_PRECISION"
    assert findings["SIMULATED_TREE_LANDED"] is None, (
        "a prefix agreement must not be recorded as the tree having landed"
    )
    assert "Full identity is not proven" in findings["why"]


def test_two_full_digests_still_prove_identity(tmp_path, repo):
    """The accept path, so the downgrade is not vacuous."""
    findings = handoff(tmp_path, repo, landed(repo))
    assert findings["verdict"] == "ENTRY_LANDED_AS_SIMULATED"
    assert findings["policy"] == "PASS"


def test_prefix_match_does_not_release_the_suffix(tmp_path, repo):
    document = receipt(repo)
    entry = document["prefixes"][0]
    full = entry["handoff"]["postcondition"]["expected_main_tree"]
    document["prefixes"][0]["handoff"]["postcondition"]["expected_main_tree"] = full[:8]
    rp, op = tmp_path / "r.json", tmp_path / "o.json"
    rp.write_text(json.dumps(document), encoding="utf-8")
    op.write_text(json.dumps({
        "ref": entry["ref"], "merge_api_success": True, "http_status": 200,
        "pr_head_sha": entry["handoff"]["preconditions"]["pr_head_sha"],
        "base_sha_before": entry["handoff"]["preconditions"]["base_sha"],
        "actual_main_tree": full,
    }), encoding="utf-8")
    findings = json.loads(subprocess.run(
        [sys.executable, str(SCRIPT)], capture_output=True, text=True, timeout=180,
        cwd=repo, env={"PATH": "/usr/bin:/bin", "RECEIPT": str(rp),
                       "HANDOFF_OBSERVED": str(op)}).stdout)
    assert findings["NEXT_PREFIX_STILL_VALID"] is None, (
        "an unproven postcondition must not advance the queue"
    )


# --- computed-state admissibility -------------------------------------------------


def computed_state(repo, value) -> dict:
    env = {"PATH": "/usr/bin:/bin", "COMPUTED_STATE": "" if value is None else str(value)}
    result = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True,
                            timeout=60, cwd=repo, env=env)
    assert result.stdout, result.stderr
    return json.loads(result.stdout)


@pytest.mark.parametrize("value", ["unknown", "", "null"])
def test_unknown_is_admissible_as_neither_permission_nor_refusal(repo, value):
    """`UNKNOWN` ≠ `CLEAN` and `UNKNOWN` ≠ `CONFLICT`.

    Before a merge GitHub may report `mergeable_state: unknown` while it computes a test
    merge. Reading that as clean would proceed on no evidence; reading it as a conflict
    would stop on no evidence.
    """
    findings = computed_state(repo, value)
    assert findings["verdict"] == "COMPUTED_STATE_UNKNOWN"
    assert findings["admissibility"] == "NOT_ADMISSIBLE"
    assert "neither permission nor refusal" in findings["why"]


def test_a_known_state_is_advisory_only(repo):
    """Even `clean` is a hint about a test merge, not authority."""
    findings = computed_state(repo, "clean")
    assert findings["admissibility"] == "ADVISORY_ONLY"
    assert findings["confers_merge_authority"] is False
    assert "not authority" in findings["why"]


def test_an_unmodelled_state_is_not_admissible(repo):
    findings = computed_state(repo, "some_new_state")
    assert findings["verdict"] == "COMPUTED_STATE_UNRECOGNISED"
    assert findings["admissibility"] == "NOT_ADMISSIBLE"


# --- terminal cohort closure ------------------------------------------------------


def test_a_drained_cohort_is_terminal_not_a_producer_fault(repo):
    """`QUEUE_COMPLETE` is the end of the work, not a failure of the measurer.

    Without this, #148's merge empties the committed cohort and the next run refuses with
    `QUEUE is required` — a red check on a pull request that did nothing wrong, and the
    fifth instance of a correct stop carrying the wrong subsystem's reason.
    """
    result = subprocess.run(
        [sys.executable, str(SCRIPT)], capture_output=True, text=True, timeout=60, cwd=repo,
        env={"PATH": "/usr/bin:/bin", "QUEUE": "", "COHORT_COMPLETE": "true"},
    )
    assert result.returncode == OK, result.stderr
    findings = json.loads(result.stdout)
    assert findings["verdict"] == "QUEUE_COMPLETE_TERMINAL"
    assert findings["measurement_status"] == "NOT_REQUIRED"
    assert findings["policy"] == "NOT_EVALUATED"
    assert "end of the work" in findings["why"]
    assert findings["confers_merge_authority"] is False


def test_an_empty_queue_without_the_completion_flag_is_still_refused(repo):
    """An accidental empty queue must not be read as a completed one."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT)], capture_output=True, text=True, timeout=60, cwd=repo,
        env={"PATH": "/usr/bin:/bin", "QUEUE": ""},
    )
    assert result.returncode == FAIL
    assert "QUEUE is required" in result.stderr
    assert "intentionally drained" in result.stderr


def test_the_terminal_verdict_is_publishable_evidence():
    """The workflow must treat it as a finding, not discard it as an error."""
    text = WORKFLOW_FILE.read_text(encoding="utf-8")
    assert "QUEUE_COMPLETE_TERMINAL" in text
    findings_block = text.split("FINDINGS = {")[1].split("}")[0]
    assert "QUEUE_COMPLETE_TERMINAL" in findings_block


def _unused_dispatch_path_is_not_claimed_as_verified():
    """`workflow_dispatch` cannot run until the workflow is on the default branch.

    So `DISPATCH_PATH_VERIFIED` is unreachable while #150 is open, and the workflow must not
    imply otherwise by retiring the trigger it still depends on.
    """
    text = WORKFLOW_FILE.read_text(encoding="utf-8")
    assert "pull_request:" in text, (
        "the bootstrap trigger is still required: removing it makes the workflow unrunnable "
        "until this PR merges, and the dispatch input contract would then be unexercised"
    )
    assert "REMOVE ONCE THE FIRST ARTIFACT IS PROVEN" in text


# --- CI collection-boundary identity ---------------------------------------------


def shadow_queue_module():
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import importlib
    return importlib.import_module("check_shadow_merge_queue")


def test_default_collection_boundary_is_byte_identical_to_ci():
    """QUEUE_TESTS_SUBSET_OF_CI -> QUEUE_TEST_SET_IDENTICAL_TO_CI."""
    module = shadow_queue_module()
    lines = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8").splitlines()
    start = next(
        index for index, line in enumerate(lines)
        if "python -m pytest -p no:cacheprovider -q" in line
    )
    ci_command_parts = []
    for line in lines[start:]:
        part = line.strip()
        if part.endswith("\\"):
            part = part[:-1].rstrip()
        ci_command_parts.append(part)
        if part == "tests/":
            break
    assert " ".join(ci_command_parts) == module.DEFAULT_TEST


def test_canonical_command_names_the_router_evidence_and_tests_roots():
    import shlex
    module = shadow_queue_module()
    classification = module.classify_test_set(module.DEFAULT_TEST)
    assert shlex.split(module.DEFAULT_TEST)[-2:] == [
        "docs/06-agent-orchestration/skill-router/"
        "SECB-WP-ENGLOOP-MVP-001 — Sandbox Evidence/test_router.py",
        "tests/",
    ]
    assert classification == {
        "test_set_epoch": "CI_EXPLICIT_ROOTS_V1",
        "ci_test_set_equivalent": True,
        "test_scope": "router FIT evidence + tests/",
    }


def test_legacy_subset_receipts_remain_named_but_are_not_ci_equivalent():
    module = shadow_queue_module()
    classification = module.classify_test_set(module.LEGACY_TEST)
    assert classification["test_set_epoch"] == "LEGACY_TESTS_DIR_ONLY_V0"
    assert classification["ci_test_set_equivalent"] is False
    assert "omitted" in classification["test_scope"]


def test_an_arbitrary_override_cannot_claim_ci_test_set_equivalence():
    module = shadow_queue_module()
    classification = module.classify_test_set("pytest")
    assert classification["test_set_epoch"] == "NON_CANONICAL_OVERRIDE"
    assert classification["ci_test_set_equivalent"] is False


def test_test_set_epoch_is_part_of_cohort_identity():
    module = shadow_queue_module()
    document = {
        "base_sha": "a" * 40,
        "merge_method": "SQUASH",
        "prefixes": [],
        "persistence": {"base_tree": "b" * 40},
        "environment": {
            "test_command_digest": "sha256:same",
            "test_set_epoch": module.CANONICAL_TEST_SET_EPOCH,
            "git": "2.54.0",
            "python": "3.13.0",
        },
    }
    canonical = module.canonical_cohort(document)
    document["environment"]["test_set_epoch"] = module.LEGACY_TEST_SET_EPOCH
    assert module.canonical_cohort(document) != canonical
