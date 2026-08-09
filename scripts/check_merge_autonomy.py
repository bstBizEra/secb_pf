#!/usr/bin/env python3
"""R1 merge-eligibility classifier — the executable half of the standing
merge authorization (`SECB-WP-FWK-011`).

`RISK_AUTHORITY_MATRIX.md` sets Merge at tier `R1` to "Policy may permit",
and SoD §39 restricts self-approval to `R2-R4`. The policy in
`docs/00-governance/STANDING_MERGE_AUTHORIZATION.md` permits an executor to
merge its own change **only** when this classifier returns ELIGIBLE. The
classifier exists because a delegation enforced by an agent's self-restraint
is prose, not a control (KN-001).

Contract:

    stdin        output of ``git diff --numstat <base>...<head>``
    MAX_LINES    optional override of the diff-size cap (default 600)

Exit codes (fail-closed):

    0  ELIGIBLE       -- every path is R1, none protected, within the cap
    2  HUMAN_REQUIRED -- anything else, including empty or unparseable input

A verdict of HUMAN_REQUIRED is not an error; it is the normal answer for
governance, enforcement, and unclassified changes.
"""

from __future__ import annotations

import os
import sys

DEFAULT_MAX_LINES = 600

# Touching any of these forces a human merge. Governance and enforcement
# paths are excluded because an agent must not widen its own authority, and
# the sealed evidence directory is excluded because its certification voids
# on any change (REV-SECB-ENGLOOP-MVP-001-20260810).
PROTECTED_PREFIXES = (
    "AGENTS.md",
    "README.md",
    "docs/00-governance/",
    "docs/12-decisions/",
    "scripts/",
    ".github/",
    "docs/06-agent-orchestration/skill-router/SECB-WP-ENGLOOP-MVP-001",
)

# R1 per the matrix: reversible documentation, tests, and sandbox code.
R1_PREFIXES = (
    "docs/",
    "tests/",
    "src/",
    "config/",
    "evidence/",
)

ELIGIBLE = 0
HUMAN_REQUIRED = 2


def classify(paths: list[str], lines: int, max_lines: int) -> tuple[int, str]:
    """Return (exit_code, human-readable reason)."""
    if not paths:
        return HUMAN_REQUIRED, "no diff parsed -- eligibility cannot be established"

    protected = [p for p in paths if p.startswith(PROTECTED_PREFIXES)]
    if protected:
        return HUMAN_REQUIRED, (
            "protected path(s) touched: " + ", ".join(sorted(protected)[:5])
        )

    unclassified = [p for p in paths if not p.startswith(R1_PREFIXES)]
    if unclassified:
        return HUMAN_REQUIRED, (
            "path(s) not classified R1: " + ", ".join(sorted(unclassified)[:5])
        )

    if lines > max_lines:
        return HUMAN_REQUIRED, f"diff {lines} lines exceeds the R1 cap of {max_lines}"

    return ELIGIBLE, f"{len(paths)} R1 path(s), {lines}/{max_lines} lines"


def parse_numstat(numstat: str) -> tuple[list[str], int] | None:
    """Return (paths, total changed lines), or None if a row is unparseable."""
    paths: list[str] = []
    lines = 0
    for row in numstat.splitlines():
        row = row.strip()
        if not row:
            continue
        parts = row.split("\t")
        if len(parts) < 3:
            return None
        added, deleted, path = parts[0], parts[1], parts[-1]
        paths.append(path)
        if added != "-":  # "-" marks a binary file
            try:
                lines += int(added) + int(deleted)
            except ValueError:
                return None
    return paths, lines


def main() -> int:
    try:
        max_lines = int(os.environ.get("MAX_LINES", DEFAULT_MAX_LINES))
    except ValueError:
        print(
            "MERGE AUTONOMY: HUMAN_REQUIRED -- MAX_LINES is not an integer",
            file=sys.stderr,
        )
        return HUMAN_REQUIRED

    parsed = parse_numstat(sys.stdin.read())
    if parsed is None:
        print(
            "MERGE AUTONOMY: HUMAN_REQUIRED -- unparseable numstat input",
            file=sys.stderr,
        )
        return HUMAN_REQUIRED

    paths, lines = parsed
    code, reason = classify(paths, lines, max_lines)
    if code == ELIGIBLE:
        print(f"MERGE AUTONOMY: ELIGIBLE (R1 standing authorization) -- {reason}")
        return ELIGIBLE

    print(f"MERGE AUTONOMY: HUMAN_REQUIRED -- {reason}", file=sys.stderr)
    return HUMAN_REQUIRED


if __name__ == "__main__":
    sys.exit(main())
