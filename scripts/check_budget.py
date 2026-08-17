#!/usr/bin/env python3
"""Budget circuit breaker, minimal executable form.

AGENTS.md section 6 makes a reached budget cap a mandatory stop condition
and section 7 makes budget limits a required work-package field. This
script is the first slice of BUDGET_CIRCUIT_BREAKER_POLICY.md that can
actually trip: every pull request must declare a diff budget, and CI
fails the PR when the diff exceeds it.

Contract:

    stdin             output of ``git diff --numstat <base>...<head>``
    BUDGET_TEXT       the PR body, containing exactly one budget line:

        BUDGET: max_files=<int> max_lines=<int>

    ALLOW_EMPTY_DIFF  set to "1" to declare a genuinely empty diff deliberately

Exit codes (fail-closed, AGENTS.md section 4):

    0  diff is within the declared budget, or ALLOW_EMPTY_DIFF=1 and stdin was empty
       (reported NOT_APPLICABLE, never PASS -- nothing was measured)
    2  budget missing, malformed, declared twice, exceeded, OR stdin carried no numstat
       rows without ALLOW_EMPTY_DIFF (BUDGET_DIFF_ABSENT)

Counting rules: every changed path counts as one file. Lines are added
plus deleted. Binary files report no line counts in numstat ("-"); they
count as one file and zero lines, so a binary-heavy PR is bounded by
max_files rather than silently unbounded.
"""

from __future__ import annotations

import os
import re
import sys

BUDGET_PATTERN = re.compile(
    r"^\s*BUDGET:\s*max_files=(\d+)\s+max_lines=(\d+)\s*$", re.MULTILINE
)

FAIL = 2


def parse_budget(text: str) -> tuple[int, int]:
    """Return (max_files, max_lines) or raise ValueError, fail-closed."""
    matches = BUDGET_PATTERN.findall(text or "")
    if not matches:
        raise ValueError(
            "no budget declared -- every PR body must contain exactly one "
            "line: 'BUDGET: max_files=<n> max_lines=<n>' (AGENTS.md section 7)"
        )
    if len(matches) > 1:
        raise ValueError(
            f"{len(matches)} BUDGET lines found -- the budget authority is "
            "ambiguous; declare exactly one"
        )
    max_files, max_lines = matches[0]
    return int(max_files), int(max_lines)


def measure_diff(numstat: str) -> tuple[int, int]:
    """Return (files, lines) totals from git numstat output."""
    files = 0
    lines = 0
    for row in numstat.splitlines():
        row = row.strip()
        if not row:
            continue
        parts = row.split("\t")
        if len(parts) < 3:
            raise ValueError(f"unrecognized numstat row: {row!r}")
        added, deleted = parts[0], parts[1]
        files += 1
        if added != "-":  # "-" marks a binary file: counted, lines unknown
            lines += int(added) + int(deleted)
    return files, lines


def main() -> int:
    try:
        max_files, max_lines = parse_budget(os.environ.get("BUDGET_TEXT", ""))
        raw = sys.stdin.read()
    except ValueError as exc:
        print(f"BUDGET GATE FAIL (closed): {exc}", file=sys.stderr)
        return FAIL

    # An absent diff is not a diff of zero. This gate is fed by a shell pipeline
    #
    #     git diff --numstat "$BASE_SHA...$HEAD_SHA" | python scripts/check_budget.py
    #
    # and GitHub's default shell is `bash -e`, which does NOT set pipefail -- so the step's
    # exit status is THIS script's. When `git diff` fails, most realistically because the base
    # SHA is not present in a shallow clone, it writes nothing to stdout and its non-zero exit
    # is discarded. Before this branch existed, that produced "BUDGET GATE PASS: 0/N files" and
    # a green admission check that had measured nothing at all.
    #
    #     EMPTY_INPUT != EMPTY_DIFF
    #     MEASUREMENT_NOT_PERFORMED != MEASUREMENT_FOUND_NOTHING
    #
    # The two sibling gates fed the same way already escalate on absent input: both
    # classify_authority_delta.py and check_dual_policy.py answer "no diff parsed -- authority
    # delta cannot be established" with the strictest verdict. This gate was the only one that
    # read absence as compliance. Fixing it here rather than adding `set -o pipefail` to the
    # workflow is deliberate: the distinction is only observable at the point that consumes the
    # bytes, a gate must not depend on its caller's shell options for fail-closed behaviour, and
    # `.github/workflows/ci.yml` is claimed by two long-open branches (#113, #123).
    if not raw.strip():
        if os.environ.get("ALLOW_EMPTY_DIFF") == "1":
            # A genuinely empty diff is legitimate but rare (a revert reduced to nothing). It is
            # reported as NOT_APPLICABLE and never as PASS: nothing was measured against the
            # ceiling, so calling it "within budget" would overstate what the gate observed.
            print(
                "BUDGET GATE NOT_APPLICABLE: no changed paths were reported and "
                "ALLOW_EMPTY_DIFF=1 was set explicitly. Nothing was measured against the "
                f"declared {max_files} files / {max_lines} lines."
            )
            return 0
        print(
            "BUDGET GATE FAIL (closed): BUDGET_DIFF_ABSENT -- stdin carried no numstat rows. "
            "Either the diff command failed (an unreachable base SHA in a shallow clone is the "
            "usual cause, and a bash pipeline without pipefail hides its exit status) or the "
            "pipe was not wired. An unmeasured diff is not a diff within budget. If the diff is "
            "genuinely empty, set ALLOW_EMPTY_DIFF=1 to say so deliberately.",
            file=sys.stderr,
        )
        return FAIL

    try:
        files, lines = measure_diff(raw)
    except ValueError as exc:
        print(f"BUDGET GATE FAIL (closed): {exc}", file=sys.stderr)
        return FAIL

    usage = (
        f"{files}/{max_files} files, {lines}/{max_lines} changed lines"
    )
    if files > max_files or lines > max_lines:
        print(
            f"BUDGET GATE FAIL: diff exceeds the declared budget -- {usage}. "
            "AGENTS.md section 6: a reached cap is a stop condition; "
            "shrink the change or re-negotiate the budget on the ticket.",
            file=sys.stderr,
        )
        return FAIL

    print(f"BUDGET GATE PASS: {usage}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
