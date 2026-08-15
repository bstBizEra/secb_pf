#!/usr/bin/env python3
"""Bind a gate result to the pull-request metadata it actually evaluated.

`SECB-WP-FWK-068` (issue #127).

A check attached only to `head_sha` goes stale the moment a title or body is edited,
and **GitHub does not mark it stale**. Measured, not supposed: the Gate 1 log for PR
#122 at head `1a569a9` recorded

    WP_TEXT: SECB-WP-FWK-062: register C-5, C-6, C-7 …
    AUTHORITY GATE PASS: work-package reference SECB-WP-FWK-062

while the pull request now reads `SECB-WP-FWK-066`. The green check evaluated an
identifier that no longer exists on that PR.

    head SHA unchanged  ≠  all reviewed inputs unchanged

PR metadata is not decoration. It supplies Gate 1's work-package ID, the budget
declaration, and — under squash merge — the commit subject that lands on `main`.

**Why a re-run cannot repair a stale check.** Re-running a workflow replays the
*original event payload*, so a re-run of #122's job would read `FWK-062` again and pass
again. Only an event carrying current metadata produces a current evaluation, which is
why `.github/workflows/ci.yml` now lists `edited` in its trigger types. The same
mechanism is why the budget discipline is *patch the body, then push*, never the
reverse.

Two modes, because the two halves happen at different times:

    emit      in CI, record what this run evaluated, so readback is possible
    --verify  at the merge decision, compare a recorded binding against live state

`CHECK_CURRENT` cannot be self-enforced by the run that produces it: within one run the
checked values and the current values are identical by construction. The verification is
necessarily external, and this script's emit half exists to make it possible at all.

Contract:

    PR_TITLE      pull request title            (required)
    PR_BODY       pull request body             (optional; empty is legitimate)
    HEAD_SHA      pull request head SHA         (required)
    BASE_SHA      pull request base SHA         (required)
    MERGE_METHOD  merge method                  (default SQUASH)
    ENVELOPE      delegation envelope path      (default config/delegation_envelope.json)

Exit codes:

    0  binding emitted, or verification passed
    2  fail-closed: required input missing, or a `CHECK_CURRENT` term mismatched

Attacker-controlled text arrives through the environment, never through shell
interpolation (`NFR-16`).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# Reused rather than reimplemented: `load_prefix` carries six fail-closed paths
# (absent file, invalid JSON, absent project block, empty prefix, non-string prefix,
# regex metacharacters). A second copy of that logic would be a second thing to get
# wrong, and the two would drift.
from check_work_package_ref import (  # noqa: E402
    DEFAULT_ENVELOPE,
    find_reference,
    load_prefix,
)

OK = 0
FAIL = 2

BUDGET_LINE = re.compile(r"^BUDGET:.*$", re.M)


def digest(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalized_subject(title: str) -> str:
    """The squash commit subject this title would produce.

    Recorded because under squash merge the PR title *becomes the commit message on
    `main`* — a claim that outlives the pull request. GitHub appends ` (#N)`; the
    number is not known to the gate, so only the normalized title is bound.
    """
    return " ".join(title.split())


def build_binding(env: dict[str, str]) -> dict:
    missing = [k for k in ("PR_TITLE", "HEAD_SHA", "BASE_SHA") if not env.get(k, "").strip()]
    if missing:
        raise ValueError(f"required input absent: {', '.join(missing)}")

    title = env["PR_TITLE"]
    body = env.get("PR_BODY", "")

    prefix = load_prefix(env.get("ENVELOPE", DEFAULT_ENVELOPE))
    work_package_id = find_reference(f"{title}\n{body}", prefix)

    budget_match = BUDGET_LINE.search(body)

    return {
        "schema": "secb.pr-input-binding/v1",
        "head_sha": env["HEAD_SHA"].strip(),
        "base_sha": env["BASE_SHA"].strip(),
        "title_digest": digest(title),
        "body_digest": digest(body),
        "work_package_id": work_package_id,
        "budget_digest": digest(budget_match.group(0)) if budget_match else None,
        "merge_method": env.get("MERGE_METHOD", "SQUASH"),
        "expected_commit_subject": normalized_subject(title),
        "not_proven": [
            "that the recorded values are still current — that is --verify's job",
            "that any consumer requires this binding",
        ],
    }


# `base_sha` is bound because retargeting a pull request changes the diff under review
# without touching the head. A binding over the head alone would call that unchanged.
COMPARED = (
    "head_sha",
    "base_sha",
    "title_digest",
    "body_digest",
    "budget_digest",
    "work_package_id",
)


def verify(recorded: dict, current: dict) -> list[str]:
    """Return the names of mismatching `CHECK_CURRENT` terms — empty means current."""
    return [term for term in COMPARED if recorded.get(term) != current.get(term)]


def main(argv: list[str]) -> int:
    try:
        current = build_binding(dict(os.environ))
    except ValueError as exc:
        print(f"BINDING FAIL (closed): {exc}", file=sys.stderr)
        return FAIL

    if "--verify" in argv:
        index = argv.index("--verify")
        if index + 1 >= len(argv):
            print("BINDING FAIL (closed): --verify needs a recorded binding path", file=sys.stderr)
            return FAIL
        try:
            recorded = json.loads(Path(argv[index + 1]).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"BINDING FAIL (closed): recorded binding unreadable ({exc})", file=sys.stderr)
            return FAIL

        mismatched = verify(recorded, current)
        if mismatched:
            print(
                "CHECK_CURRENT FAIL: " + ", ".join(mismatched) + " changed since the check ran. "
                "The prior result evaluated different inputs and does not carry forward.",
                file=sys.stderr,
            )
            return FAIL
        print("CHECK_CURRENT PASS: every bound input matches the live pull request")
        return OK

    print(json.dumps(current, indent=2, sort_keys=True))
    return OK


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
