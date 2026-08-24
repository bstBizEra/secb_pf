#!/usr/bin/env python3
"""Authority-delta classifier (`SECB-WP-FWK-012`).

Replaces the path-based binary classifier of `SECB-WP-FWK-011`. The question
is no longer "which files does this PR touch" but **"how does this PR change
authority or risk relative to the ratified delegation envelope"**.

Change classes and the verdict each produces:

    G0  non-governance work inside the envelope        AUTO_APPROVED
    G1  governance implementation, authority unchanged AGENT_BALLOT_REQUIRED
    G2  adjustment inside the delegated envelope       AGENT_BALLOT_REQUIRED
    G3  pre-authorized ladder advance, conditions met  AUTO_APPROVED_WITH_CONDITIONS
    G4  root authority expansion                       CONSTITUTIONAL_REQUIRED
    G5  prohibited: bypass, audit removal, evidence    REJECTED

Contract:

    stdin        output of ``git diff --numstat <base>...<head>``
    ENVELOPE     path to the delegation envelope (default config/delegation_envelope.json)
    FAMILY_LINES aggregate changed lines of the concurrent change family,
                 excluding this candidate (default 0 -- see below)
    DIFF_PATH    path to a file holding the unified diff body (preferred)
    DIFF_TEXT    the unified diff body inline (retained; size-limited, see below)

The diff body is what the `G5` scan reads, so it is not optional in effect:
without it, a change that deletes an enforcement control cannot be recognised
as prohibited. `DIFF_PATH` exists because `DIFF_TEXT` cannot carry one.
Linux caps a single environment string at ``MAX_ARG_STRLEN`` = 131072 bytes,
and a 160-line diff of long-line JSON exceeds that (`SECB-WP-FWK-043`). When
it did, the classifier was never executed at all: the shell failed with
`E2BIG`, `REJECTED` became unreachable, and CI reported the failure as a
routine escalation. Prefer `DIFF_PATH`; `DIFF_TEXT` remains for callers that
already work.

Exit codes:

    0  AUTO_APPROVED or AUTO_APPROVED_WITH_CONDITIONS — the envelope covers it
    2  escalation required (AGENT_BALLOT_REQUIRED or CONSTITUTIONAL_REQUIRED)
    3  REJECTED — prohibited change

The line ceiling applies to the **change family**, not to one diff
(`SECB-WP-FWK-046`). Splitting a change across concurrent pull requests evaded
it: one 1300-line change escalated while two 550-line halves each auto-approved,
because this script sees one diff at a time. `NFR-12` forbids it the network, so
it does not discover its siblings -- CI computes the aggregate and passes
`FAMILY_LINES`. **Absent means zero, and the verdict line says whether a family
was considered**, so a verdict taken without one is distinguishable from a
verdict taken with an empty one. A malformed or negative value escalates rather
than degrading to zero.

Not caught: sequential splitting. Merge one half, open the other, and each is
judged alone. Closing that needs a lookback over merged work, and a window wide
enough to matter would fold most of this repository into one family. Recorded as
a residual rather than claimed.

Fail-closed: a missing, unreadable, malformed, or expired envelope, an
unparseable diff, or an empty diff all escalate. A `DIFF_PATH` that is set but
cannot be read also escalates -- it must never be treated as an empty diff,
because an empty diff means "no prohibited signature found". `HUMAN_REQUIRED` is
deliberately absent from the vocabulary: the constitutional authority may in
future be a committee, a threshold-signature council, or an external body,
so the verdict names the *authority level* required, not the species of the
approver.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date
from pathlib import Path

AUTO_APPROVED = "AUTO_APPROVED"
AUTO_APPROVED_WITH_CONDITIONS = "AUTO_APPROVED_WITH_CONDITIONS"
AGENT_BALLOT_REQUIRED = "AGENT_BALLOT_REQUIRED"
CONSTITUTIONAL_REQUIRED = "CONSTITUTIONAL_REQUIRED"
REJECTED = "REJECTED"

EXIT_OK = 0
EXIT_ESCALATE = 2
EXIT_REJECTED = 3

EXIT_FOR = {
    AUTO_APPROVED: EXIT_OK,
    AUTO_APPROVED_WITH_CONDITIONS: EXIT_OK,
    AGENT_BALLOT_REQUIRED: EXIT_ESCALATE,
    CONSTITUTIONAL_REQUIRED: EXIT_ESCALATE,
    REJECTED: EXIT_REJECTED,
}

# Removing an audit trail, deleting evidence, or skipping a verifier is not a
# governance decision to be weighed — it is prohibited outright (G5). Detected
# as whole-file deletions of a control, plus one diff-body signature for the
# removal of an enforcement step from CI.
G5_PATH_DELETIONS = (
    "scripts/check_work_package_ref.py",
    "scripts/check_budget.py",
    "scripts/classify_authority_delta.py",
    "scripts/check_dual_policy.py",
    "docs/13-evidence/",
)

# Enforcement steps whose *removal* from CI is prohibited. Matched only on
# removed lines, never on a substring of the whole diff: an added line that
# merely quotes one of these strings — a test fixture, or documentation of
# this very rule — is not a removal. The first version of this check scanned
# the diff body as one string and rejected its own test fixture, the same
# false-positive class the sandbox MVP hit when its scanner read an in-memory
# `set.remove()` as filesystem deletion (EVIDENCE_RECORD.md, DEF-ENGLOOP-MVP-001).
G5_REMOVED_STEPS = (
    "run: python scripts/check_work_package_ref.py",
    "run: python scripts/check_budget.py",
    "run: python scripts/classify_authority_delta.py",
)


def removed_enforcement_steps(diff_text: str) -> list[str]:
    """Enforcement steps that appear on removed lines of *diff_text*."""
    found = []
    for line in (diff_text or "").splitlines():
        if not line.startswith("-") or line.startswith("---"):
            continue
        body = line[1:].strip()
        for step in G5_REMOVED_STEPS:
            if body.endswith(step):
                found.append(step)
    return found


def load_envelope(path: str) -> dict:
    with open(path, encoding="utf-8") as handle:
        envelope = json.load(handle)
    for key in ("scope", "absolute_ceilings", "current_tier", "expires_at"):
        if key not in envelope:
            raise ValueError(f"envelope missing required key: {key}")
    return envelope


def parse_numstat(numstat: str) -> tuple[list[tuple[str, int, bool, bool]], int]:
    """Return ([(path, lines, is_deletion, uncertain)], total_lines)."""
    rows: list[tuple[str, int, bool, bool]] = []
    total = 0
    for raw in numstat.splitlines():
        raw = raw.strip()
        if not raw:
            continue
        parts = raw.split("\t", 2)
        if len(parts) < 3:
            raise ValueError(f"unrecognized numstat row: {raw!r}")
        added, deleted, path = parts[0], parts[1], parts[2]
        # FAIL CLOSED on rows whose real paths cannot be recovered from this
        # format. `git diff --numstat` renders a rename as "old => new" or
        # "{old => new}/tail" inside the single path field, and C-quotes any
        # path with non-ASCII or control bytes. A file may also legitimately be
        # NAMED "a => b", so the two are not distinguishable here -- the format
        # is lossy, and any split is a guess. Guessing is what let a rename
        # carry a path out of its authority class. Refuse instead.
        if " => " in path or path.startswith('"'):
            raise ValueError(
                f"ambiguous numstat row -- paths not recoverable from this format: {raw!r}"
            )
        if added == "-":  # binary: line counts and deletion state are both unknowable here
            rows.append((path, 0, False, True))
            continue
        a, d = int(added), int(deleted)
        lines = a + d
        # is_deletion stays a PURE deletion (a == 0 and d > 0) -- widening it would
        # reject ordinary edits. `uncertain` carries what the counts cannot settle:
        # any row that removes content might be destroying a protected artifact,
        # and adding one line must not launder that away.
        # uncertain: the counts cannot settle whether a protected artifact lost
        # content. Any removal qualifies, and so does a 0/0 row -- deleting an
        # EMPTY file is byte-identical here to a no-op or a mode-only change.
        # uncertain: this row may have destroyed protected content, and the counts
        # cannot settle it. NET SHRINKAGE is the discriminator, not raw deletions:
        # a row that adds at least as much as it removes cannot have destroyed net
        # content -- it padded or rewrote. A 0/0 row is also unsettleable, because
        # deleting an EMPTY file is byte-identical here to a no-op or mode change.
        # This is why "+1 added / -500 deleted" escalates while "+117/-10" does not.
        rows.append((path, lines, a == 0 and d > 0, d > a or (a == 0 and d == 0)))
        total += lines
    return rows, total


def classify(
    rows: list[tuple[str, int, bool, bool]],
    total_lines: int,
    envelope: dict,
    diff_text: str,
    family_lines: int = 0,
) -> tuple[str, str]:
    """Return (verdict, reason)."""
    if not rows:
        return CONSTITUTIONAL_REQUIRED, "no diff parsed — authority delta cannot be established"

    scope = envelope["scope"]
    ceilings = envelope["absolute_ceilings"]
    paths = [path for path, _, _, _ in rows]

    # G5 first: prohibited changes are never weighed against anything.
    deleted_controls = [
        path for path, _, is_del, _u in rows
        if is_del and path.startswith(G5_PATH_DELETIONS)
    ]
    if deleted_controls:
        return REJECTED, (
            "prohibited: deletes a control or evidence artifact — "
            + ", ".join(sorted(deleted_controls)[:3])
        )
    # A row that removes content from a G5-protected surface, but is not a PURE
    # deletion, cannot be settled from line counts alone: "1 added / 500 deleted"
    # on a sealed evidence file is indistinguishable here from ordinary editing.
    # It is not REJECTED -- L0 calls evidence append-only while the repository's
    # own history edits evidence files, and resolving that is a policy act, not a
    # parser's. It escalates so a human decides.
    uncertain_controls = [
        path for path, _, is_del, uncertain in rows
        if uncertain and not is_del and path.startswith(G5_PATH_DELETIONS)
    ]
    if uncertain_controls:
        return CONSTITUTIONAL_REQUIRED, (
            "removes content from a control or evidence artifact; deletion cannot be "
            "determined from line counts — " + ", ".join(sorted(uncertain_controls)[:3])
        )

    removed_steps = removed_enforcement_steps(diff_text)
    if removed_steps:
        return REJECTED, (
            "prohibited: removes an enforcement step from CI — "
            + ", ".join(sorted(set(removed_steps)))
        )

    # Absolute ceiling: never waivable by any tier or ballot.
    if total_lines > ceilings["max_changed_lines_ever"]:
        return CONSTITUTIONAL_REQUIRED, (
            f"{total_lines} lines exceeds the absolute ceiling "
            f"{ceilings['max_changed_lines_ever']} — no tier may waive it"
        )

    # G4: anything that can alter the constitution, the envelope itself, the
    # classifier, the verifier, or the CI that runs them.
    constitutional = [p for p in paths if p.startswith(tuple(scope["constitutional_paths"]))]
    if constitutional:
        return CONSTITUTIONAL_REQUIRED, (
            "root authority surface touched: " + ", ".join(sorted(constitutional)[:4])
        )

    # G1/G2: governance implementation or in-envelope adjustment. Both need the
    # ballot layer, which is inert; they therefore escalate rather than pass.
    governance = [p for p in paths if p.startswith(tuple(scope["governance_implementation_paths"]))]
    if governance:
        state = envelope.get("ballot_layer", {}).get("state", "NOT_ACTIVE")
        detail = "" if state == "ACTIVE" else " (ballot layer NOT_ACTIVE — cannot be satisfied here)"
        return AGENT_BALLOT_REQUIRED, (
            "governance implementation: " + ", ".join(sorted(governance)[:4]) + detail
        )

    # G0 must lie wholly inside the delegated scope.
    outside = [p for p in paths if not p.startswith(tuple(scope["auto_paths"]))]
    if outside:
        return CONSTITUTIONAL_REQUIRED, (
            "path(s) outside the delegated envelope: " + ", ".join(sorted(outside)[:4])
        )

    cap = scope["max_changed_lines"]

    if total_lines > cap:
        return AGENT_BALLOT_REQUIRED, (
            f"{total_lines} lines exceeds the envelope cap {cap} "
            f"but is within the absolute ceiling"
        )

    # The cap applies to the change FAMILY, not to one diff. Splitting a change
    # across concurrent pull requests evaded it until FWK-046: two 550-line
    # halves each auto-approved where one 1100-line change would not.
    if family_lines and total_lines + family_lines > cap:
        return AGENT_BALLOT_REQUIRED, (
            f"{total_lines} lines is within the cap {cap} but the concurrent "
            f"change family totals {total_lines + family_lines} "
            f"({total_lines} here + {family_lines} in sibling changes), which "
            f"exceeds it — splitting a change does not lower its class"
        )

    family_note = (
        f", family +{family_lines}" if family_lines
        else ", no concurrent family reported"
    )
    return AUTO_APPROVED, (
        f"G0, {len(paths)} path(s), {total_lines}/{cap} lines{family_note}, "
        f"tier {envelope['current_tier']}"
    )


def read_family_lines() -> int:
    """Aggregate lines of the concurrent family, or raise ValueError.

    Supplied by the caller because `NFR-12` keeps this script off the network.
    An absent value is zero -- it has to be, or every local self-check in this
    repository would fail closed -- so the verdict line reports whether a family
    was considered instead of leaving absence invisible.
    """
    raw = os.environ.get("FAMILY_LINES", "").strip()
    if not raw:
        return 0
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(
            f"FAMILY_LINES is set to {raw!r}, which is not an integer; "
            "an unparseable family size is not a family of zero"
        ) from exc
    if value < 0:
        raise ValueError(f"FAMILY_LINES is negative ({value})")
    return value


def read_diff_body() -> str:
    """Return the unified diff body, or raise ValueError to fail closed.

    `DIFF_PATH` wins over `DIFF_TEXT` when both are set, because the file
    channel has no size limit and the environment channel does. An empty or
    absent value in either means "no diff body supplied", which is the
    pre-existing behaviour and leaves the G5 scan with nothing to read -- but
    a path that is *set and unreadable* is a different thing entirely, and it
    escalates rather than silently degrading into an empty diff.
    """
    path = os.environ.get("DIFF_PATH", "").strip()
    if path:
        try:
            return Path(path).read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            raise ValueError(
                f"DIFF_PATH is set to {path!r} but cannot be read ({exc}); "
                "an unreadable diff is not an empty diff"
            ) from exc
    return os.environ.get("DIFF_TEXT", "")


def main() -> int:
    envelope_path = os.environ.get("ENVELOPE", "config/delegation_envelope.json")
    try:
        envelope = load_envelope(envelope_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(
            f"VERDICT: {CONSTITUTIONAL_REQUIRED} — envelope unusable ({exc})",
            file=sys.stderr,
        )
        return EXIT_ESCALATE

    if str(envelope["expires_at"]) < date.today().isoformat():
        print(
            f"VERDICT: {CONSTITUTIONAL_REQUIRED} — envelope expired "
            f"{envelope['expires_at']}; renewal is a constitutional act",
            file=sys.stderr,
        )
        return EXIT_ESCALATE

    try:
        rows, total = parse_numstat(sys.stdin.read())
    except ValueError as exc:
        print(f"VERDICT: {CONSTITUTIONAL_REQUIRED} — {exc}", file=sys.stderr)
        return EXIT_ESCALATE

    try:
        diff_body = read_diff_body()
    except ValueError as exc:
        print(f"VERDICT: {CONSTITUTIONAL_REQUIRED} — {exc}", file=sys.stderr)
        return EXIT_ESCALATE

    try:
        family_lines = read_family_lines()
    except ValueError as exc:
        print(f"VERDICT: {CONSTITUTIONAL_REQUIRED} — {exc}", file=sys.stderr)
        return EXIT_ESCALATE

    verdict, reason = classify(rows, total, envelope, diff_body, family_lines)
    line = f"VERDICT: {verdict} — {reason}"
    if EXIT_FOR[verdict] == EXIT_OK:
        print(line)
    else:
        print(line, file=sys.stderr)
    return EXIT_FOR[verdict]


if __name__ == "__main__":
    sys.exit(main())
