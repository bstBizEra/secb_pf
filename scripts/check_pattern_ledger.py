#!/usr/bin/env python3
"""Validate the reusable-pattern ledger against the tree it ships in (FWK-090).

WHY THIS EXISTS. Roughly thirty reusable patterns were established across the FWK-079..089
work packages, and every one of them lived only in a pull-request comment. A comment is not
greppable by the next agent, carries no provenance a tool can check, and -- worst -- can claim
that a pattern is enforced by a test that does not exist. That last failure is not
hypothetical: a governing document in a sibling repository named a required test which had
never been written, and every agent that read the document believed the guard was in force.

    DOCUMENTED != ENFORCED
    CITED != PRESENT

So the ledger is machine-readable and each entry declares HOW it is guarded, and this tool
refuses any entry whose declared guard disagrees with what is actually in the tree:

    MECHANICAL    every cited test must EXIST here. A phantom citation is refused.
    PENDING_MERGE at least one cited test must be ABSENT here, and an open PR must be named.
                  If all of them are already present, the classification is stale -- also
                  refused, because a ledger that under-claims decays into one nobody trusts.
    PROSE_ONLY    no test may be cited. An entry that cites a guard while calling itself
                  prose hides the drift in the opposite direction.

Both directions are checked, because either one silently turns the ledger into decoration.

WHAT IT DELIBERATELY DOES NOT DO. It does not judge whether a cited test actually exercises
the pattern it claims to guard -- only a human reviewer can say that. It reports the guarded
ratio and never rounds it up: patterns that are honest prose stay visibly prose.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

OK = 0
FAIL = 2

SCHEMA = "secb.reusable-pattern-ledger/v1"
GUARD_CLASSES = ("MECHANICAL", "PENDING_MERGE", "PROSE_ONLY")
ID_PATTERN = re.compile(r"^RP-\d{3}$")
REQUIRED_FIELDS = ("id", "name", "rule", "origin", "guard")

# A pattern states a DISTINCTION, an IMPLICATION, a CONJUNCTION or an ORDERING. Without one it
# is a slogan, and a slogan cannot be applied to a new case by anyone who was not in the
# conversation that produced it. The ordering forms are here because the root pattern of this
# whole family -- claim <= mechanism <= verified behaviour -- is an ordering and nothing else;
# the first draft of this list omitted them and refused that entry, which was the check
# working correctly against a rule that was too narrow.
RULE_MARKERS = ("!=", "≠", "->", "→", "∧", "^", "<=", "≤", ">=", "≥")


class Refused(ValueError):
    """The ledger contradicts the tree, or an entry is not a pattern."""


def test_exists(root: Path, citation: dict) -> bool:
    """True when the cited file exists AND defines the cited test."""
    path = root / citation["file"]
    if not path.is_file():
        return False
    source = path.read_text(encoding="utf-8")
    return re.search(rf"^def {re.escape(citation['test'])}\b", source, re.M) is not None


def check_entry(root: Path, entry: dict, seen: dict) -> tuple[bool, list[str]]:
    """Return (mechanically_guarded, notes). Raises Refused on a contradiction."""
    missing = [f for f in REQUIRED_FIELDS if not entry.get(f)]
    if missing:
        raise Refused(f"{entry.get('id', '<no id>')}: missing required field(s) {missing}")

    identifier = entry["id"]
    if not ID_PATTERN.match(identifier):
        raise Refused(f"{identifier!r} is not of the form RP-000")
    if identifier in seen:
        raise Refused(f"duplicate id {identifier!r} (also used by {seen[identifier]!r})")
    seen[identifier] = entry["name"]

    if not any(marker in entry["rule"] for marker in RULE_MARKERS):
        raise Refused(
            f"{identifier}: rule {entry['rule']!r} states no distinction or implication. A "
            "pattern without one is a slogan, and a slogan cannot be applied to a new case"
        )

    origin = entry["origin"]
    if not (origin.get("pr") or origin.get("issue")):
        raise Refused(
            f"{identifier}: origin names neither a pr nor an issue. A pattern with no "
            "provenance is folklore -- unauditable and unfalsifiable"
        )

    guard = entry["guard"]
    if guard not in GUARD_CLASSES:
        raise Refused(f"{identifier}: guard {guard!r} is not one of {GUARD_CLASSES}")
    citations = entry.get("tests") or []

    if guard == "PROSE_ONLY":
        if citations:
            raise Refused(
                f"{identifier}: declared PROSE_ONLY but cites {len(citations)} test(s). An "
                "entry that cites a guard while calling itself prose understates its own "
                "enforcement, which is drift in the direction nobody audits"
            )
        return False, [f"{identifier}: prose only, no guard claimed"]

    if not citations:
        raise Refused(f"{identifier}: guard {guard} cites no tests")

    present = [c for c in citations if test_exists(root, c)]
    absent = [c for c in citations if c not in present]

    if guard == "MECHANICAL":
        if absent:
            raise Refused(
                f"{identifier}: declared MECHANICAL but "
                + ", ".join(f"{c['file']}::{c['test']}" for c in absent)
                + " is not in this tree. A phantom citation is worse than no citation: every "
                "reader concludes the guard is in force"
            )
        return True, [f"{identifier}: {len(present)} guard(s) present"]

    # PENDING_MERGE
    if not entry.get("pending_pr"):
        raise Refused(f"{identifier}: PENDING_MERGE requires pending_pr")
    if not absent:
        raise Refused(
            f"{identifier}: declared PENDING_MERGE against PR #{entry['pending_pr']}, but every "
            "cited test is already present. The classification is stale -- promote it to "
            "MECHANICAL. A ledger that under-claims decays into one nobody trusts"
        )
    return False, [
        f"{identifier}: pending PR #{entry['pending_pr']}, "
        f"{len(absent)} guard(s) not yet in this tree"
    ]


def validate(root: Path, ledger: dict) -> dict:
    if ledger.get("schema") != SCHEMA:
        raise Refused(f"schema is {ledger.get('schema')!r}, expected {SCHEMA!r}")
    patterns = ledger.get("patterns")
    if not patterns:
        raise Refused("ledger declares no patterns")

    seen: dict[str, str] = {}
    guarded: list[str] = []
    notes: list[str] = []
    for entry in patterns:
        is_guarded, entry_notes = check_entry(root, entry, seen)
        notes.extend(entry_notes)
        if is_guarded:
            guarded.append(entry["id"])

    by_guard: dict[str, int] = {}
    for entry in patterns:
        by_guard[entry["guard"]] = by_guard.get(entry["guard"], 0) + 1

    return {
        "schema": "secb.pattern-ledger-observation/v1",
        "patterns": len(patterns),
        "mechanically_guarded": len(guarded),
        "by_guard_class": by_guard,
        "guarded_ids": guarded,
        "notes": notes,
        "not_proven": [
            "that a cited test exercises the pattern it claims to guard; only review can say",
            "that an unguarded pattern is wrong -- honest prose is better than a phantom test",
            "that this ledger is complete; absence of an entry is not absence of a pattern",
        ],
        "confers_merge_authority": False,
    }


def main(argv: list[str]) -> int:
    env = dict(os.environ)
    path = Path(env.get("LEDGER", "config/reusable_patterns.json"))
    root = Path(env.get("REPO_ROOT", ".")).resolve()
    try:
        ledger = json.loads((root / path).read_text(encoding="utf-8"))
        report = validate(root, ledger)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"REFUSED (closed): ledger unreadable or unparseable ({exc})", file=sys.stderr)
        return FAIL
    except Refused as exc:
        print(f"REFUSED (closed): {exc}", file=sys.stderr)
        return FAIL
    except (KeyError, TypeError, AttributeError) as exc:
        print(f"REFUSED (closed): malformed ledger ({exc!r})", file=sys.stderr)
        return FAIL

    print(json.dumps(report, indent=2, sort_keys=True))
    return OK


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
