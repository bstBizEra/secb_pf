#!/usr/bin/env python3
"""Shadow merge queue — measure whether an ordered queue actually drains.

`SECB-WP-FWK-083` (issue #149).

    PR_IS_INDIVIDUALLY_MERGEABLE
      ≠ ORDERED_PREFIX_IS_INTEGRABLE
      ≠ INTEGRATED_RESULT_PASSES_TESTS
      ≠ GITHUB_REQUIRED_CHECKS_PASSED

GitHub's `mergeable` field is a test merge of **one** PR against the current base. A real
queue builds a cumulative group from the latest base **and the entries ahead of it**, so a
queue of individually-mergeable PRs can still jam. This measures every cumulative prefix,
not just the final tree.

Three properties that make the receipt honest rather than reassuring:

* **Merge method must match the repository's.** SecB squash-merges, so each prefix is built
  with `git merge --squash`. Building with an ordinary merge measures a tree that will never
  exist, and the receipt says `MERGE_METHOD_MISMATCH` instead of `PASS`.
* **A first failing prefix is not a culprit.** `FIRST_FAILING_PREFIX_AT_PR_N` ≠
  `PR_N_IS_SOLE_CAUSE`: the failure is a property of the *combination*, and attributing it
  to the last entry added is the same error as blaming the last commit in a bisect range.
* **The measurement must not perturb what it measures.** The test run is given
  `PYTHONDONTWRITEBYTECODE=1`, and the worktree is checked for residue afterwards. Without
  this the run wrote `__pycache__` under the sealed-evidence directory and the
  sealed-evidence guard failed — a "queue defect" that was entirely the observer's.
  Suppressing the known contaminant is not proving there was none, so both are done.
* **A timeout is not a result.** Running out of budget yields
  `measurement_status: INCOMPLETE` and `QUEUE_DRAINABILITY_UNPROVEN`, and the first PR in
  the unmeasured suffix is **not** reported as failing.

It runs in a **linked worktree**, so the primary worktree is never touched — no checkout,
no reset, no stash. Nothing is pushed, no queue entry is created, and a receipt from this
tool **confers no merge authority**.

Contract:

    QUEUE          comma-separated refs, in queue order      (required)
    BASE           base ref                                  (default origin/main)
    MERGE_METHOD   SQUASH | MERGE | REBASE                    (default SQUASH)
    TEST_COMMAND   command run at each prefix                 (default pytest)
    TIME_BUDGET    seconds before the run stops honestly      (default 600)

Exit codes:

    0  every prefix integrated and passed, and the measurement is complete
    2  refused, a prefix failed, or the measurement is incomplete
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

OK = 0
FAIL = 2

REPO_MERGE_METHOD = "SQUASH"
DEFAULT_TEST = "python3 -m pytest -p no:cacheprovider -q tests/"


# --- reason integrity ---------------------------------------------------------
#
#     ACTION_REFUSED != REFUSAL_REASON_CORRECT
#
# Three times in this repository a control refused correctly and diagnosed wrongly:
# INTEGRATION_FAILED reported as CONFLICT, budget exhaustion reported as a failed prefix,
# and an unresolvable ref reported as BUDGET_EXCEEDED. A correct stop hides an incorrect
# reason, and fail-closed design makes that MORE likely -- refusing is right either way, so
# the mislabel survives review.
#
# Every verdict therefore carries three independent axes and exactly one terminal reason.
# The load-bearing rule: a POLICY verdict is only permitted after a valid OBSERVATION.
# Each of the three mislabels above asserted policy on an unobserved measurement.
REASON_AXES = {
    # verdict: (execution, measurement, policy)
    "ENTRY_LANDED_AS_SIMULATED":        ("PROCEEDED", "OBSERVED",     "PASS"),
    # A comparison against a truncated operand cannot prove full identity, however many
    # characters agree. `verdict_strength <= weakest_operand_precision`.
    "PREFIX_MATCH_ONLY":                ("PROCEEDED", "OBSERVED",     "PASS_AT_RECORDED_PRECISION"),
    "LANDED_TREE_MISMATCH":             ("REFUSED",   "OBSERVED",     "FAIL"),
    "SUFFIX_INVALIDATED":               ("REFUSED",   "OBSERVED",     "FAIL"),
    "HEAD_MOVED_409":                   ("REFUSED",   "OBSERVED",     "FAIL"),
    "PRECONDITION_DRIFTED":             ("REFUSED",   "OBSERVED",     "FAIL"),
    "METADATA_DRIFTED":                 ("REFUSED",   "OBSERVED",     "FAIL"),
    "MERGE_NOT_ACCEPTED":               ("REFUSED",   "OBSERVED",     "FAIL"),
    "READBACK_NOT_OBSERVED":            ("REFUSED",   "NOT_OBSERVED", "NOT_EVALUATED"),
    "HISTORICAL_ALREADY_CONSUMED":      ("REFUSED",   "NOT_OBSERVED", "NOT_EVALUATED"),
    "REFUSE_OUT_OF_ORDER":              ("REFUSED",   "NOT_OBSERVED", "NOT_EVALUATED"),
    "REPLAY_REJECTED_FOR_CURRENT_STEP": ("REFUSED",   "NOT_OBSERVED", "NOT_EVALUATED"),
    "READBACK_UNBOUND":                 ("REFUSED",   "NOT_OBSERVED", "NOT_EVALUATED"),
    "UNKNOWN_ENTRY":                    ("REFUSED",   "NOT_OBSERVED", "NOT_EVALUATED"),
    "EVIDENCE_PROMOTABLE":              ("PROCEEDED", "OBSERVED",     "PASS"),
    "REQUIRED_GATE_FAILURE":            ("REFUSED",   "OBSERVED",     "FAIL"),
    "CROSS_REVISION_ASSEMBLY":          ("REFUSED",   "NOT_OBSERVED", "NOT_EVALUATED"),
    "MEASUREMENT_INCOMPLETE":           ("REFUSED",   "INCOMPLETE",   "NOT_EVALUATED"),
    "MEASUREMENT_NOT_TERMINAL":         ("REFUSED",   "INCOMPLETE",   "NOT_EVALUATED"),
    "ARTIFACT_NOT_VERIFIED":            ("REFUSED",   "NOT_OBSERVED", "NOT_EVALUATED"),
    "METADATA_COHERENCE_FAILED":        ("REFUSED",   "OBSERVED",     "FAIL"),
    "COHORT_DRIFT":                     ("REFUSED",   "OBSERVED",     "FAIL"),
}


def reason_integrity(verdict: str) -> dict:
    """Decompose a terminal reason into its three axes, refusing incoherent pairings."""
    axes = REASON_AXES.get(verdict)
    if axes is None:
        return {"terminal_reason": verdict, "reason_integrity": "UNMAPPED_REASON",
                "why": "a verdict with no declared axes cannot be audited for diagnosis"}
    execution, measurement, policy = axes
    if policy not in ("NOT_EVALUATED",) and measurement != "OBSERVED":
        return {"terminal_reason": verdict, "reason_integrity": "CONTROL_DIAGNOSIS_FAILURE",
                "why": (f"{verdict} asserts policy {policy} on measurement {measurement}. A "
                        "policy verdict is only permitted after a valid observation")}
    return {"terminal_reason": verdict, "execution": execution,
            "measurement": measurement, "policy": policy,
            "reason_integrity": "COHERENT"}


class Refused(ValueError):
    """The measurement cannot be made honestly."""


def git(*args: str, cwd: str | None = None, check: bool = True) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise Refused(f"git {' '.join(args)} failed: {result.stderr.strip()[:200]}")
    return result.stdout.strip()


def digest(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def environment_digest(test_command: str) -> dict:
    """A pass is only meaningful against the environment that produced it."""
    return {
        "python": platform.python_version(),
        "platform": platform.system(),
        "git": git("--version").split()[-1],
        "test_command": test_command,
        "test_command_digest": digest(test_command),
    }


def canonical_cohort(receipt: dict) -> str:
    """The bytes that define WHAT was measured, in a fixed order.

    The **git version** is part of identity, not provenance. Measured: a local run on git
    2.34 reported eight prefixes draining while CI on git 2.54 failed at the second, so two
    receipts over identical heads described different cohorts. Tool drift means
    `REMEASUREMENT_REQUIRED`, and folding the version into the digest is what makes that
    detectable instead of arguable.
    """
    heads = [f"{p['ref']}@{p['head_sha']}" for p in receipt.get("prefixes", [])]
    persistence = receipt.get("persistence", {})
    environment = receipt.get("environment") or {}
    parts = [
        receipt.get("base_sha", ""),
        persistence.get("base_tree", ""),
        receipt.get("merge_method", ""),
        environment.get("test_command_digest", ""),
        f"git={environment.get('git', '')}",
        f"python={environment.get('python', '')}",
        *heads,
    ]
    return "\n".join(parts)


def measure(base: str, queue: list[str], method: str, test_command: str,
            budget: float) -> dict:
    if method != REPO_MERGE_METHOD:
        return {
            "measurement_status": "REFUSED",
            "verdict": "MERGE_METHOD_MISMATCH",
            "why": (
                f"the repository merges with {REPO_MERGE_METHOD} and this run was asked for "
                f"{method}. A prefix built the wrong way measures a tree that will never "
                "exist, so the result is not a PASS in either direction"
            ),
        }

    started = time.monotonic()
    workdir = tempfile.mkdtemp(prefix="smq-")
    worktree = str(Path(workdir) / "wt")
    prefixes: list[dict] = []
    first_failing: str | None = None
    contaminated = False
    try:
        git("worktree", "add", "--detach", "-q", worktree, base)
        # Configure the identity ON THE WORKTREE, not per invocation. Measured in CI:
        # per-call `-c user.email/-c user.name` covered the commit but not every operation
        # that needs an ident, and git 2.54 failed with `empty ident name (for
        # <runner@...>)` -- it had fallen back to the system identity. A runner with no
        # global git identity then broke the second prefix, and the failure surfaced as a
        # phantom conflict.
        git("config", "user.email", "smq@local", cwd=worktree)
        git("config", "user.name", "SMQ", cwd=worktree)
        for index, ref in enumerate(queue, start=1):
            if time.monotonic() - started > budget:
                break
            head = git("rev-parse", ref)
            record = {
                "position": index,
                "ref": ref,
                "head_sha": head,
                "prefix": queue[:index],
            }
            # Squash semantics: stage the combined change, then commit it as one tree, the
            # way the platform will land it.
            merge = subprocess.run(
                ["git", "merge", "--squash", "--no-commit", ref],
                cwd=worktree, capture_output=True, text=True,
            )
            if merge.returncode != 0:
                conflicts = [c for c in git("diff", "--name-only", "--diff-filter=U",
                                            cwd=worktree, check=False).splitlines() if c]
                git("merge", "--abort", cwd=worktree, check=False)
                record["conflicted_paths"] = conflicts
                record["integration_error"] = (merge.stderr or merge.stdout).strip()[:400]
                # A non-zero merge with NO unmerged paths is not a content conflict. The
                # first version labelled both CONFLICT, so an operational failure was
                # reported as an integration incompatibility between two branches --
                # measured: a CI run produced `CONFLICT` with `conflicted_paths: []`, which
                # is a claim about the branches that the evidence did not support.
                record["integration"] = "CONFLICT" if conflicts else "INTEGRATION_FAILED"
                record["tests"] = "NOT_RUN"
                prefixes.append(record)
                first_failing = ref
                break

            commit = subprocess.run(
                ["git", "commit", "-q", "-m", f"smq: squash {ref}"],
                cwd=worktree, capture_output=True, text=True,
            )
            if commit.returncode != 0:
                # A failed commit leaves the squash staged, so the NEXT merge fails with no
                # unmerged paths -- which is how an unchecked commit turned into a phantom
                # conflict one entry later.
                record["integration"] = "INTEGRATION_FAILED"
                record["integration_error"] = (commit.stderr or commit.stdout).strip()[:400]
                record["tests"] = "NOT_RUN"
                prefixes.append(record)
                first_failing = ref
                break
            record["integration"] = "SQUASHED"
            record["synthetic_commit_sha"] = git("rev-parse", "HEAD", cwd=worktree)
            record["synthetic_tree_sha"] = git("rev-parse", "HEAD^{tree}", cwd=worktree)
            # Compare-and-swap handoff: a receipt is valid for ONE snapshot. These are the
            # tokens that must still hold at merge time, and the pinned head goes to the
            # merge API's `sha` parameter so GitHub answers 409 rather than merging a head
            # nobody simulated.
            record["handoff"] = {
                "preconditions": {
                    "base_sha": git("rev-parse", base),
                    "base_tree": git("rev-parse", f"{base}^{{tree}}"),
                    "pr_head_sha": head,
                    "merge_method": method,
                },
                "merge_call": {
                    "endpoint": "PUT /repos/{owner}/{repo}/pulls/{number}/merge",
                    "sha": head,
                    "merge_method": method.lower(),
                    "why_sha": "pins the head; a changed head yields 409 Conflict instead of "
                               "merging something no prefix simulated",
                },
                "postcondition": {
                    "expected_main_tree": record["synthetic_tree_sha"],
                    "readback": "actual_main_tree == simulated_prefix_tree",
                },
            }

            # The measurement must not perturb what it measures. Without
            # PYTHONDONTWRITEBYTECODE the test run writes __pycache__ into the tree,
            # including under the sealed-evidence directory, and the sealed-evidence guard
            # then fails -- reporting a queue defect that is entirely the observer's.
            # Measured: this produced a false QUEUE_NOT_DRAINABLE_AS_ORDERED at the first
            # prefix, and the same tree passed 175 tests when run cleanly.
            test_env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
            tests = subprocess.run(
                test_command, shell=True, cwd=worktree,
                capture_output=True, text=True, env=test_env,
            )
            record["tests"] = "PASS" if tests.returncode == 0 else "FAIL"
            record["test_summary"] = (tests.stdout or tests.stderr).strip().splitlines()[-1:]

            # Suppressing the known contaminant is not the same as proving there was none.
            residue = [line for line in
                       git("status", "--porcelain", cwd=worktree, check=False).splitlines()
                       if line.strip()]
            if residue:
                record["contamination"] = residue[:10]
                record["tests"] = "MEASUREMENT_CONTAMINATED"
                prefixes.append(record)
                first_failing = None
                contaminated = True
                break

            prefixes.append(record)
            if tests.returncode != 0:
                first_failing = ref
                break
    finally:
        git("worktree", "remove", "--force", worktree, check=False)
        shutil.rmtree(workdir, ignore_errors=True)

    measured = [p["ref"] for p in prefixes]
    unmeasured = [r for r in queue if r not in measured]
    complete = not unmeasured and first_failing is None

    # Persistence binding. A receipt that only exists in a shell's scratch directory is
    # not addressable: after a squash you could show MERGE_API_SUCCESS and never prove
    # SIMULATED_TREE_LANDED, because the expected tree would be gone.
    env = os.environ
    retention = int(env.get("ARTIFACT_RETENTION_DAYS", "90"))
    receipt = {
        "schema": "secb.shadow-merge-queue-receipt/v1",
        "persistence": {
            "repository": env.get("GITHUB_REPOSITORY", "NOT_OBSERVED"),
            "run_id": env.get("GITHUB_RUN_ID", "NOT_OBSERVED"),
            "workflow_ref": env.get("GITHUB_WORKFLOW_REF", "NOT_OBSERVED"),
            "measuring_pr_head": env.get("MEASURING_PR_HEAD", "NOT_OBSERVED"),
            "base_tree": git("rev-parse", f"{base}^{{tree}}"),
            "queue_order": list(queue),
            "retention_days": retention,
            "expires_at": (datetime.now(timezone.utc)
                           + timedelta(days=retention)).isoformat(),
            "digest_is_external": (
                "The receipt's own digest is NOT stored inside it -- a mutated file whose "
                "embedded digest was recomputed would verify against itself. The digest is "
                "emitted to the run summary and supplied to the validator out of band."
            ),
            "not_attestation": (
                "Persisting bytes is not signing them. An Actions artifact proves storage "
                "and retention, not provenance, and it confers no merge authority."
            ),
        },
        "base_ref": base,
        "base_sha": git("rev-parse", base),
        "merge_method": method,
        "environment": environment_digest(test_command),
        "prefixes": prefixes,
        "measured_prefix": measured,
        "unmeasured_suffix": unmeasured,
        "measurement_status": "COMPLETE" if not unmeasured else "INCOMPLETE",
        "confers_merge_authority": False,
    }

    if contaminated:
        receipt["verdict"] = "MEASUREMENT_CONTAMINATED"
        receipt["measurement_status"] = "REFUSED"
        receipt["why"] = (
            "the test command left the worktree dirty, so the tree that was tested is not "
            "the tree that was built. A result from a perturbed measurement is not a result "
            "in either direction"
        )
    elif any(p.get("integration") == "INTEGRATION_FAILED" for p in prefixes):
        failure = next(p for p in prefixes if p.get("integration") == "INTEGRATION_FAILED")
        receipt["verdict"] = "INTEGRATION_FAILED"
        receipt["first_failing_prefix_at"] = failure["ref"]
        receipt["why"] = (
            "the merge did not complete and left no unmerged paths, so this is an "
            "operational failure of the measurement, NOT evidence that the branches are "
            "incompatible. It says nothing about drainability in either direction"
        )
        receipt["attribution"] = "INTEGRATION_FAILED is not QUEUE_NOT_DRAINABLE_AS_ORDERED"
    elif first_failing:
        receipt["first_failing_prefix_at"] = first_failing
        receipt["attribution"] = (
            f"FIRST_FAILING_PREFIX_AT {first_failing} is NOT {first_failing}_IS_SOLE_CAUSE. "
            "The failure is a property of the combination; blaming the last entry added is "
            "the error a bisect range invites."
        )
        receipt["verdict"] = "QUEUE_NOT_DRAINABLE_AS_ORDERED"
    elif unmeasured:
        receipt["verdict"] = "QUEUE_DRAINABILITY_UNPROVEN"
        receipt["unmeasured_note"] = (
            "The budget ran out. The first entry in the unmeasured suffix is NOT reported as "
            "failing -- it is unmeasured, which is a different fact."
        )
    else:
        receipt["verdict"] = "QUEUE_DRAINS_AS_ORDERED"

    # Cohort identity excludes the measuring run. A push to the measuring pull request
    # changes the workflow head and the run id; it does not change what was measured, so it
    # must not invalidate the receipt. The cohort is the base, the ordered heads, the merge
    # method and the test command -- nothing about who observed them.
    receipt["cohort_digest"] = digest(canonical_cohort(receipt))
    receipt["cohort_identity"] = {
        "includes": ["base_sha", "base_tree", "ordered_pr_heads", "merge_method",
                     "test_command_digest", "git_version", "python_version"],
        "excludes": ["measuring_pr_head", "run_id", "workflow_ref", "measured_at"],
        "why": (
            "Provenance answers who measured; identity answers what was measured. Folding "
            "the measuring head into identity would expire every receipt on the next push "
            "to the measuring pull request, which changes nothing about the cohort."
        ),
    }

    receipt["not_proven"] = [
        "that GitHub's required checks pass on the merged result; these are local tests "
        "against a synthetic tree",
        "that this order is optimal, or the only drainable one",
        "that the result holds for any other base SHA or PR head",
    ]
    return receipt


# --- compare-and-swap handoff -------------------------------------------------

def validate_handoff(receipt: dict, observed: dict) -> dict:
    """Grade an executed merge against the prefix that was simulated.

    Three facts, deliberately not one:

        MERGE_API_SUCCESS ≠ SIMULATED_TREE_LANDED ≠ NEXT_PREFIX_STILL_VALID

    A `200` from the merge API says a call was accepted. It does not say the resulting tree
    is the one measured, and it says nothing about whether the remaining queue is still
    valid — another merge may have landed in between, which is exactly the case a real
    merge queue rebuilds its group for.
    """
    # Monotonic execution cursor. A readback is evidence for exactly ONE ordinal against
    # ONE cohort: valid proof of a prior step is not proof of the current one. Without this,
    # the correct postcondition for ordinal 1 would satisfy ordinal 2 unchallenged.
    cursor = observed.get("cursor")
    if cursor is not None:
        ordinal = observed.get("ordinal")
        if ordinal is None:
            return {"verdict": "READBACK_UNBOUND",
                    "why": "a cursor was supplied but the readback names no ordinal"}
        if observed.get("cohort_digest") != receipt.get("cohort_digest"):
            return {"verdict": "REPLAY_REJECTED_FOR_CURRENT_STEP",
                    "why": ("the readback is bound to a different cohort digest; evidence "
                            "from another binding cannot advance this one")}
        if ordinal < cursor:
            return {"verdict": "HISTORICAL_ALREADY_CONSUMED",
                    "why": f"ordinal {ordinal} was consumed; the cursor is at {cursor}"}
        if ordinal > cursor:
            return {"verdict": "REFUSE_OUT_OF_ORDER",
                    "why": f"ordinal {ordinal} arrived while the cursor is at {cursor}"}

    entries = {p["ref"]: p for p in receipt.get("prefixes", [])}
    ref = observed.get("ref")
    if ref not in entries:
        return {"verdict": "UNKNOWN_ENTRY",
                "why": f"{ref!r} is not a measured prefix in this receipt"}
    record = entries[ref]
    handoff = record.get("handoff") or {}
    pre = handoff.get("preconditions", {})

    findings = {
        "ref": ref,
        "MERGE_API_SUCCESS": bool(observed.get("merge_api_success")),
        "SIMULATED_TREE_LANDED": None,
        "NEXT_PREFIX_STILL_VALID": None,
    }

    if observed.get("http_status") == 409:
        findings["verdict"] = "HEAD_MOVED_409"
        findings["why"] = (
            "the pinned head no longer matched. Re-simulate before any retry: retrying a "
            "409 against a new head merges something no prefix measured"
        )
        findings["NEXT_PREFIX_STILL_VALID"] = False
        return findings

    for token, key in (("pr_head_sha", "pr_head_sha"), ("base_sha", "base_sha_before")):
        if observed.get(key) and pre.get(token) and observed[key] != pre[token]:
            findings["verdict"] = "PRECONDITION_DRIFTED"
            findings["drifted"] = token
            findings["NEXT_PREFIX_STILL_VALID"] = False
            return findings

    for digest_key in ("title_digest", "body_digest"):
        recorded, seen = observed.get(f"recorded_{digest_key}"), observed.get(digest_key)
        if recorded and seen and recorded != seen:
            findings["verdict"] = "METADATA_DRIFTED"
            findings["drifted"] = digest_key
            findings["invalidates"] = (
                "this PR and every prefix containing it; metadata supplies the "
                "work-package ID and the squash subject"
            )
            findings["NEXT_PREFIX_STILL_VALID"] = False
            return findings

    if not findings["MERGE_API_SUCCESS"]:
        findings["verdict"] = "MERGE_NOT_ACCEPTED"
        findings["NEXT_PREFIX_STILL_VALID"] = False
        return findings

    expected = (handoff.get("postcondition") or {}).get("expected_main_tree")
    actual = observed.get("actual_main_tree")

    # Comparison-strength integrity. A published plan truncates digests for display; a
    # comparison against that truncation proves a PREFIX, not identity. Measured: an
    # execution record compared a full observed tree against a 12-hex expected summary and
    # every character agreed -- which is a prefix match, and calling it full identity would
    # be a claim stronger than its weakest operand.
    full = re.compile(r"^[0-9a-f]{40}$")
    if actual and expected and not (full.match(expected) and full.match(actual)):
        if actual.startswith(expected) or expected.startswith(actual):
            findings["verdict"] = "PREFIX_MATCH_ONLY"
            findings["SIMULATED_TREE_LANDED"] = None
            findings["why"] = (
                f"expected {expected!r} and observed {actual!r} agree on every character "
                "compared, but at least one operand is truncated. Full identity is not "
                "proven; obtain the full digest from the artifact receipt"
            )
            findings["NEXT_PREFIX_STILL_VALID"] = None
            return findings

    if not actual:
        findings["verdict"] = "READBACK_NOT_OBSERVED"
        findings["why"] = "no actual_main_tree supplied; acceptance is not landing"
        return findings
    findings["SIMULATED_TREE_LANDED"] = actual == expected
    if actual != expected:
        findings["verdict"] = "LANDED_TREE_MISMATCH"
        findings["why"] = (
            f"expected tree {expected} and observed {actual}. Stop: every remaining prefix "
            "was simulated on a base that did not materialise"
        )
        findings["NEXT_PREFIX_STILL_VALID"] = False
        return findings

    # Tree matched. A different commit SHA is expected under squash and is not a defect:
    # the tree is the content proof, and the actual SHA becomes the next prefix's parent.
    findings["commit_sha_note"] = (
        "tree matched; a differing commit SHA is normal under squash. The tree is the "
        "content proof and the actual SHA is the new parent for the next prefix."
    )
    foreign = observed.get("foreign_merges_since")
    findings["NEXT_PREFIX_STILL_VALID"] = not foreign
    findings["verdict"] = "ENTRY_LANDED_AS_SIMULATED" if not foreign else "SUFFIX_INVALIDATED"
    if foreign:
        findings["why"] = (
            "another merge landed on main between simulation and execution, so every "
            "remaining prefix must be re-simulated against the new base"
        )
    return findings


def classify_watermark(snapshot: dict, evidence: dict) -> dict:
    """Order a disagreement in time, which the cursor cannot do.

        evidence.created_at > snapshot.observed_at
          → LATE_ARRIVAL_AFTER_SNAPSHOT   ≠ REPLAY

    Two independent axes. The **cursor** checks whether evidence is bound to the right
    ordinal, commit and tree; the **watermark** checks whether it existed when the snapshot
    was taken. Evidence can be perfectly bound and simply newer than the observer, which is
    not a replay and not a defect -- it is a reader who looked before it arrived.

    Measured: four state reports in this session disagreed with the repository because they
    were taken seconds before a push. Each was correct at its watermark.
    """
    observed_at = snapshot.get("observed_at")
    through = snapshot.get("observed_through_comment_id")
    if not observed_at and not through:
        return {"verdict": "SNAPSHOT_UNWATERMARKED",
                "why": ("a snapshot with neither observed_at nor "
                        "observed_through_comment_id cannot be ordered against anything, so "
                        "a disagreement with it is unclassifiable")}
    created_at = evidence.get("created_at")
    comment_id = evidence.get("comment_id")
    # Either axis orders it: a timestamp, or a monotonic comment id. Requiring the
    # timestamp would have rejected evidence ordered only by comment id -- which is the
    # watermark form this session actually used.
    if not created_at and not comment_id:
        return {"verdict": "EVIDENCE_UNTIMED",
                "why": "the evidence carries neither created_at nor comment_id to order"}
    if observed_at and created_at and created_at > observed_at:
        return {"verdict": "LATE_ARRIVAL_AFTER_SNAPSHOT",
                "why": (f"the evidence appeared at {created_at}, after the snapshot's "
                        f"watermark {observed_at}. The snapshot was correct when taken; the "
                        "evidence is not a replay"),
                "is_replay": False, "snapshot_was_valid_at_watermark": True}
    if through and comment_id and comment_id > through:
        return {"verdict": "LATE_ARRIVAL_AFTER_SNAPSHOT",
                "why": (f"comment {evidence['comment_id']} follows the snapshot's watermark "
                        f"{through}"),
                "is_replay": False, "snapshot_was_valid_at_watermark": True}
    return {"verdict": "CONTEMPORANEOUS_OR_EARLIER",
            "why": ("the evidence predates the snapshot's watermark, so a disagreement is "
                    "NOT explained by ordering -- check the cursor axis instead"),
            "is_replay": None}


# --- evidence promotion --------------------------------------------------------

def promote(receipt: dict, observed: dict) -> dict:
    """Decide whether a complete measurement may underwrite execution.

        COMPLETE_MEASUREMENT + VERIFIED_ARTIFACT + REQUIRED_GATE_FAILURE
          = EVIDENCE_NOT_PROMOTABLE

    The binding is **one revision**. Evidence may not be assembled across revisions: a
    measurement from one head plus a green gate from the next describes a tree nobody
    tested. GitHub requires its checks to pass on the latest commit for the same reason.
    """
    persistence = receipt.get("persistence", {})
    measuring_head = persistence.get("measuring_pr_head")
    findings = {
        "schema": "secb.evidence-promotion/v1",
        "measuring_pr_head": measuring_head,
        "cohort_digest": receipt.get("cohort_digest"),
        "confers_merge_authority": False,
    }

    def refuse(verdict, why):
        findings.update(verdict=verdict, why=why, execution_eligibility="NOT_ELIGIBLE")
        return findings

    if observed.get("rollup_head_sha") != measuring_head:
        return refuse(
            "CROSS_REVISION_ASSEMBLY",
            f"the check rollup is for {observed.get('rollup_head_sha')} and the measurement "
            f"for {measuring_head}. A measurement from one revision plus a gate result from "
            "another describes a tree nobody tested",
        )
    if receipt.get("measurement_status") != "COMPLETE":
        return refuse("MEASUREMENT_INCOMPLETE",
                      f"measurement_status is {receipt.get('measurement_status')}")
    if receipt.get("verdict") != "QUEUE_DRAINS_AS_ORDERED":
        return refuse("MEASUREMENT_NOT_TERMINAL", f"verdict is {receipt.get('verdict')}")
    if receipt.get("unmeasured_suffix"):
        return refuse("MEASUREMENT_INCOMPLETE", "an unmeasured suffix remains")
    if not observed.get("artifact_verified"):
        return refuse("ARTIFACT_NOT_VERIFIED",
                      "the stored bytes were not read back against an external digest")
    failing = [c for c, state in (observed.get("required_checks") or {}).items()
               if state != "success"]
    if failing or not observed.get("required_checks"):
        return refuse(
            "REQUIRED_GATE_FAILURE",
            f"required checks {failing or '(none reported)'} on the measuring revision. A "
            "run whose revision fails a required gate cannot underwrite execution, however "
            "complete its measurement",
        )
    if not observed.get("metadata_coherent"):
        return refuse(
            "METADATA_COHERENCE_FAILED",
            "the declared budget and the verification narrative disagree; a body that "
            "contradicts itself cannot be the binding for anything",
        )
    if observed.get("cohort_drift"):
        return refuse("COHORT_DRIFT", f"bound inputs changed: {observed['cohort_drift']}")

    findings.update(
        verdict="EVIDENCE_PROMOTABLE",
        execution_eligibility="ELIGIBLE",
        binding={
            "measuring_pr_head": measuring_head,
            "workflow_ref": persistence.get("workflow_ref"),
            "base_sha": receipt.get("base_sha"),
            "base_tree": persistence.get("base_tree"),
            "cohort_heads": [p["ref"] + "@" + p["head_sha"] for p in receipt["prefixes"]],
            "expected_trees": {p["ref"]: p["synthetic_tree_sha"] for p in receipt["prefixes"]},
            "merge_method": receipt.get("merge_method"),
            "environment": receipt.get("environment"),
            "artifact_digest": observed.get("artifact_digest"),
            "expires_at": persistence.get("expires_at"),
            "required_checks": observed.get("required_checks"),
        },
        not_proven=[
            "that any merge may proceed; eligibility is not authority",
            "that the binding survives a new push to any cohort head",
        ],
    )
    return findings


def main(argv: list[str]) -> int:
    env = dict(os.environ)

    if env.get("WATERMARK_SNAPSHOT"):
        try:
            snapshot = json.loads(Path(env["WATERMARK_SNAPSHOT"]).read_text(encoding="utf-8"))
            evidence = json.loads(Path(env["WATERMARK_EVIDENCE"]).read_text(encoding="utf-8"))
        except (OSError, KeyError, json.JSONDecodeError) as exc:
            print(f"REFUSED (closed): WATERMARK_SNAPSHOT and WATERMARK_EVIDENCE required "
                  f"({exc})", file=sys.stderr)
            return FAIL
        findings = classify_watermark(snapshot, evidence)
        print(json.dumps(findings, indent=2, sort_keys=True))
        return OK

    if env.get("PROMOTE_OBSERVED"):
        try:
            receipt = json.loads(Path(env["RECEIPT"]).read_text(encoding="utf-8"))
            observed = json.loads(Path(env["PROMOTE_OBSERVED"]).read_text(encoding="utf-8"))
        except (OSError, KeyError, json.JSONDecodeError) as exc:
            print(f"REFUSED (closed): RECEIPT and PROMOTE_OBSERVED required ({exc})",
                  file=sys.stderr)
            return FAIL
        findings = promote(receipt, observed)
        findings.update(reason_integrity(findings.get("verdict", "")))
        print(json.dumps(findings, indent=2, sort_keys=True))
        return OK if findings.get("verdict") == "EVIDENCE_PROMOTABLE" else FAIL

    # Artifact verification: read the DOWNLOADED bytes and check them against a digest
    # supplied separately. Regenerating the receipt here would measure again rather than
    # verify what was stored, which is the difference the stop condition names.
    if env.get("VERIFY_ARTIFACT"):
        path = Path(env["VERIFY_ARTIFACT"])
        expected = env.get("RECEIPT_DIGEST", "").strip().removeprefix("sha256:")
        if not expected:
            print("REFUSED (closed): RECEIPT_DIGEST is required; an artifact verified "
                  "against no digest is an artifact trusted for being present",
                  file=sys.stderr)
            return FAIL
        try:
            raw = path.read_bytes()
        except OSError as exc:
            print(f"REFUSED (closed): artifact unreadable ({exc}). If retention lapsed, "
                  "the verdict is REMEASUREMENT_REQUIRED, not a pass", file=sys.stderr)
            return FAIL
        actual = hashlib.sha256(raw).hexdigest()
        if actual != expected:
            print(f"REFUSED (closed): RECEIPT_DIGEST_MISMATCH expected {expected[:16]} "
                  f"observed {actual[:16]}; one changed byte invalidates the receipt",
                  file=sys.stderr)
            return FAIL
        try:
            stored = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            print(f"REFUSED (closed): artifact is not a receipt ({exc})", file=sys.stderr)
            return FAIL
        expiry = (stored.get("persistence") or {}).get("expires_at")
        if expiry and datetime.fromisoformat(expiry) < datetime.now(timezone.utc):
            print(json.dumps({
                "verdict": "REMEASUREMENT_REQUIRED",
                "why": f"the receipt expired at {expiry}; retention lapse is not a pass",
                "confers_merge_authority": False,
            }, indent=2, sort_keys=True))
            return FAIL
        print(json.dumps({
            "verdict": "RECEIPT_ADDRESSABLE_AND_INTACT",
            "receipt_digest": f"sha256:{actual}",
            "expires_at": expiry,
            "measured_prefix": stored.get("measured_prefix", []),
            "cohort_digest": stored.get("cohort_digest"),
            "not_proven": [
                "that the bytes are attested; storage and retention are not provenance",
                "that the measurement is still current; bound inputs must be re-checked",
            ],
            "confers_merge_authority": False,
        }, indent=2, sort_keys=True))
        return OK

    # Handoff validation reads a prior receipt; it performs no merge and calls nothing.
    if env.get("HANDOFF_OBSERVED"):
        try:
            receipt = json.loads(Path(env["RECEIPT"]).read_text(encoding="utf-8"))
            observed = json.loads(Path(env["HANDOFF_OBSERVED"]).read_text(encoding="utf-8"))
        except (OSError, KeyError, json.JSONDecodeError) as exc:
            print(f"REFUSED (closed): RECEIPT and HANDOFF_OBSERVED required ({exc})",
                  file=sys.stderr)
            return FAIL
        findings = validate_handoff(receipt, observed)
        findings.update(reason_integrity(findings.get("verdict", "")))
        findings["confers_merge_authority"] = False
        print(json.dumps(findings, indent=2, sort_keys=True))
        return OK if findings.get("verdict") == "ENTRY_LANDED_AS_SIMULATED" else FAIL

    queue = [r.strip() for r in env.get("QUEUE", "").split(",") if r.strip()]
    if not queue:
        print("REFUSED (closed): QUEUE is required, in queue order", file=sys.stderr)
        return FAIL
    try:
        # Destructive-worktree preflight (SECB-WP-FWK-074): this tool never touches the
        # primary worktree, but a dirty tree means the operator's state is in flux and the
        # refs being measured may not be what they think.
        if git("status", "--porcelain"):
            raise Refused("the primary worktree is dirty; commit or set it aside first")
        receipt = measure(
            base=env.get("BASE", "origin/main"),
            queue=queue,
            method=env.get("MERGE_METHOD", REPO_MERGE_METHOD),
            test_command=env.get("TEST_COMMAND", DEFAULT_TEST),
            budget=float(env.get("TIME_BUDGET", "600")),
        )
    except Refused as exc:
        print(f"REFUSED (closed): {exc}", file=sys.stderr)
        return FAIL

    print(json.dumps(receipt, indent=2, sort_keys=True))
    return OK if receipt.get("verdict") == "QUEUE_DRAINS_AS_ORDERED" else FAIL


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
