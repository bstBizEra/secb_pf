#!/usr/bin/env python3
"""Authority Gate, minimal executable form: No Ticket, No Work.

AGENTS.md section 4 requires every unit of work to trace to a ticket, and
CONTROL_GATES.md gate 1 asks "Is the work authorized for this actor and
scope?". This script enforces the smallest verifiable slice of that rule:
a pull request must cite a work-package ID (``SECB-WP-...``) in its title
or body before any downstream gate runs.

Fail-closed by design (AGENTS.md section 4): missing input is a failure,
not a pass. Exit codes:

    0  a work-package reference was found
    2  no reference found, or nothing to check (fail closed)

Input is read from the ``WP_TEXT`` environment variable when set, else
from the command line. CI passes the PR title and body through the
environment so that attacker-controlled text is never interpolated into
a shell command.
"""

from __future__ import annotations

import os
import re
import sys

WP_PATTERN = re.compile(r"\bSECB-WP-[A-Z0-9]+(?:-[A-Z0-9]+)*\b")


def find_reference(text: str) -> str | None:
    """Return the first work-package ID in *text*, or None."""
    match = WP_PATTERN.search(text or "")
    return match.group(0) if match else None


def main(argv: list[str]) -> int:
    text = os.environ.get("WP_TEXT")
    if text is None:
        text = " ".join(argv[1:])
    text = text.strip()

    if not text:
        print(
            "AUTHORITY GATE FAIL (closed): no input text -- "
            "a work-package reference cannot be verified",
            file=sys.stderr,
        )
        return 2

    ref = find_reference(text)
    if ref is None:
        print(
            "AUTHORITY GATE FAIL: no SECB-WP-* work-package reference found. "
            "AGENTS.md section 4: No Ticket, No Work.",
            file=sys.stderr,
        )
        return 2

    print(f"AUTHORITY GATE PASS: work-package reference {ref}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
