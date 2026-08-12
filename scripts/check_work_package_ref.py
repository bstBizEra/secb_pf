#!/usr/bin/env python3
"""Authority Gate, minimal executable form: No Ticket, No Work.

AGENTS.md section 4 requires every unit of work to trace to a ticket, and
CONTROL_GATES.md gate 1 asks "Is the work authorized for this actor and
scope?". This script enforces the smallest verifiable slice of that rule:
a pull request must cite a work-package ID in its title or body before any
downstream gate runs.

The ID prefix is **configuration, not code** (``SECB-WP-FWK-036``). It is
read from ``project.work_package_prefix`` in the delegation envelope, so a
project instantiated from this framework changes a config value rather than
patching this file. Before that change the prefix was hard-coded, and the
bootstrap trial measured the cost: a new project's authority gate rejected
every pull request until someone found the regex.

Fail-closed by design (AGENTS.md section 4). Adding configuration adds a
failure mode this gate did not have, and every one of them exits 2:

    0  a work-package reference was found
    2  no reference found, no input, or the prefix cannot be determined

Input is read from the ``WP_TEXT`` environment variable when set, else from
the command line. CI passes the PR title and body through the environment so
that attacker-controlled text is never interpolated into a shell command.
The envelope path may be overridden with ``ENVELOPE``, matching
``classify_authority_delta.py``.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

# Anchored to the repository, not to the caller's working directory. CI invokes
# this from the repository root and would be satisfied by a relative path, but a
# gate whose configuration disappears when it is called from a subdirectory
# fails closed for a reason that has nothing to do with authority.
DEFAULT_ENVELOPE = str(
    Path(__file__).resolve().parent.parent / "config" / "delegation_envelope.json"
)

# A prefix must look like an identifier stem: uppercase alphanumerics and
# hyphens, no whitespace, no regex metacharacters. This is a guard against a
# malformed or hostile envelope turning the gate's pattern into something that
# matches everything -- which would fail open.
PREFIX_PATTERN = re.compile(r"^[A-Z0-9]+(?:-[A-Z0-9]+)*$")

PASS = 0
FAIL = 2


def load_prefix(path: str) -> str:
    """Return the configured work-package prefix, or raise ValueError."""
    try:
        with open(path, encoding="utf-8") as handle:
            envelope = json.load(handle)
    except OSError as exc:
        raise ValueError(f"envelope unreadable at {path} ({exc})") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"envelope is not valid JSON ({exc})") from exc

    prefix = (envelope.get("project") or {}).get("work_package_prefix")
    if not prefix:
        raise ValueError(
            "envelope has no project.work_package_prefix -- the gate cannot "
            "guess which ticket scheme authorizes work"
        )
    if not isinstance(prefix, str) or not PREFIX_PATTERN.match(prefix):
        raise ValueError(
            f"project.work_package_prefix {prefix!r} is not a plausible "
            "identifier prefix (uppercase alphanumerics and hyphens only)"
        )
    return prefix


def find_reference(text: str, prefix: str) -> str | None:
    """Return the first work-package ID for *prefix* in *text*, or None."""
    pattern = re.compile(rf"\b{re.escape(prefix)}-[A-Z0-9]+(?:-[A-Z0-9]+)*\b")
    match = pattern.search(text or "")
    return match.group(0) if match else None


def main(argv: list[str]) -> int:
    try:
        prefix = load_prefix(os.environ.get("ENVELOPE", DEFAULT_ENVELOPE))
    except ValueError as exc:
        print(f"AUTHORITY GATE FAIL (closed): {exc}", file=sys.stderr)
        return FAIL

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
        return FAIL

    ref = find_reference(text, prefix)
    if ref is None:
        print(
            f"AUTHORITY GATE FAIL: no {prefix}-* work-package reference found. "
            "AGENTS.md section 4: No Ticket, No Work.",
            file=sys.stderr,
        )
        return FAIL

    print(f"AUTHORITY GATE PASS: work-package reference {ref}")
    return PASS


if __name__ == "__main__":
    sys.exit(main(sys.argv))
