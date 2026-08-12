#!/usr/bin/env python3
"""Base-branch currency (`SECB-WP-FWK-047`, scenario `BACP-05`).

Under squash merge GitHub merges the head onto whatever the base branch is **at
merge time**, so a verdict computed against an older base describes a tree that
will not be merged. `mergeable_state` answers a different question — *can* it
merge, not *was it judged against what it will merge into*.

This reports; it does not block, and the reason is measured rather than a
preference. With ten pull requests open, merging any one makes the other nine
stale: a blocking check would red the whole queue on the first merge and make
draining it impossible. The compensating control is the human merge gate that
already exists — a stale verdict is visible to the person deciding.

**Trigger to make it blocking:** a merge queue. Then re-evaluation is automatic
rather than manual, and refusing a stale verdict costs nothing. The queue is
deferred in `docs/14-plans/GOVERNANCE_DEFERRED_CAPABILITIES.md` §D4 behind
branch protection, which returns `403` on this plan.

Contract — SHAs are arguments rather than looked up, so this stays stdlib-only
and testable offline. CI already holds both:

    argv[1]   the base SHA the verdict was computed against
    argv[2]   the current tip of that base branch
    argv[3]   optional branch name, for the message only

Exit codes:

    0  CURRENT — the verdict was computed against the tree that will merge
    1  STALE   — the base moved; the verdict describes a different tree
    2  fail closed — a SHA is missing or malformed

`STALE` is exit 1 rather than 2 so a caller can tell "the base moved" from "the
check could not run". An absent or malformed SHA must never report `CURRENT`:
that is the fail-open this file exists to avoid.
"""

from __future__ import annotations

import re
import sys

SHA = re.compile(r"^[0-9a-f]{7,40}$")

EXIT_CURRENT = 0
EXIT_STALE = 1
EXIT_FAIL_CLOSED = 2


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(
            "BASE CURRENCY FAIL (closed): need the judged base SHA and the "
            "current tip; an unknown base is not a current base",
            file=sys.stderr,
        )
        return EXIT_FAIL_CLOSED

    judged, current = argv[1].strip().lower(), argv[2].strip().lower()
    branch = argv[3] if len(argv) > 3 else "the base branch"

    for label, value in (("judged base", judged), ("current tip", current)):
        if not SHA.match(value):
            print(
                f"BASE CURRENCY FAIL (closed): {label} {value!r} is not a SHA",
                file=sys.stderr,
            )
            return EXIT_FAIL_CLOSED

    # Compare on the shorter length: CI may hand a full SHA on one side and an
    # abbreviated one on the other, and treating that as a difference would
    # report staleness that does not exist.
    width = min(len(judged), len(current))
    if judged[:width] == current[:width]:
        print(f"BASE CURRENCY CURRENT: {branch} is at {judged[:12]}, as judged")
        return EXIT_CURRENT

    print(
        f"BASE CURRENCY STALE: the verdict was computed against {judged[:12]} "
        f"but {branch} is now at {current[:12]}. Under squash merge the head "
        f"will be merged onto the current tip, so this verdict describes a tree "
        f"that will not be merged. Re-run before merging.",
        file=sys.stderr,
    )
    return EXIT_STALE


if __name__ == "__main__":
    sys.exit(main(sys.argv))
