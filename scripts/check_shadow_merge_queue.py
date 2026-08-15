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
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

OK = 0
FAIL = 2

REPO_MERGE_METHOD = "SQUASH"
DEFAULT_TEST = "python3 -m pytest -p no:cacheprovider -q tests/"


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
                conflicts = git("diff", "--name-only", "--diff-filter=U",
                                cwd=worktree, check=False)
                git("merge", "--abort", cwd=worktree, check=False)
                record["integration"] = "CONFLICT"
                record["conflicted_paths"] = [p for p in conflicts.splitlines() if p]
                record["tests"] = "NOT_RUN"
                prefixes.append(record)
                first_failing = ref
                break

            git("-c", "user.email=smq@local", "-c", "user.name=SMQ",
                "commit", "-q", "-m", f"smq: squash {ref}", cwd=worktree, check=False)
            record["integration"] = "SQUASHED"
            record["synthetic_commit_sha"] = git("rev-parse", "HEAD", cwd=worktree)
            record["synthetic_tree_sha"] = git("rev-parse", "HEAD^{tree}", cwd=worktree)

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

    receipt = {
        "schema": "secb.shadow-merge-queue-receipt/v1",
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

    receipt["not_proven"] = [
        "that GitHub's required checks pass on the merged result; these are local tests "
        "against a synthetic tree",
        "that this order is optimal, or the only drainable one",
        "that the result holds for any other base SHA or PR head",
    ]
    return receipt


def main(argv: list[str]) -> int:
    env = dict(os.environ)
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
