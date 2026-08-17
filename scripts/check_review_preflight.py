#!/usr/bin/env python3
"""Review preflight: run the refusal classes that have executable counterexamples (FWK-092).

WHAT THIS IS FOR. Thirteen landings held identity, and security-relevant policy review still needed
seven refusal-bearing comments on #159 and three revisions on #161. The strongest of those,
`OIDC_SUBJECT_NOT_PRODUCIBLE`, described a contract GitHub could not mint while 494 tests passed
green. The loop's mechanical half is reliable; its judgement half is not, and the way to close the
gap is not more autonomy -- it is moving reproducible refusal classes EARLIER, so review spends its
attention on what only judgement can settle.

    REVIEW_REFUSAL_REPRODUCED -> COUNTEREXAMPLE_ENCODED -> GUARD_CANDIDATE
      -> MUTATION_PROVEN -> PRE_REVIEW_ACTIVE -> EFFECTIVENESS_OBSERVED

WHAT IT IS NOT. It emits three SEPARATE outputs and never collapses them:

    MECHANICAL_PREFLIGHT   what a predicate with a counterexample can decide
    POLICY_REVIEW          always REQUIRED -- architecture, authority sufficiency, trust-domain
                           independence and whether a cited test is semantically adequate are
                           outside every predicate here
    MERGE_AUTHORITY        never conferred

    PRE_REVIEW_PASS != POLICY_PASS != MERGE_AUTHORITY

A green preflight means "the classes we can check mechanically are clean", which is a smaller claim
than it looks and is stated that way on purpose.

PHASE 1 IMPLEMENTS ONE CLASS: test-citation collectability. The rest are carried in the ledger at
earlier lifecycle states, because a record may not skip to PRE_REVIEW_ACTIVE without the evidence
each rung demands -- missing source, fixture, mutation, command or residual-judgement declaration
fails closed. That is the whole point of the lifecycle: it makes "we intend to guard this" and "this
is guarded" different, checkable states.

WHY COLLECTION AND NOT AST. #161 revision 3 verified citations by parsing the module and looking for
a matching `FunctionDef`. That proves a definition exists, not that pytest runs it:

    DEF_PRESENT != TEST_COLLECTED != GUARD_ENFORCED

A `def helper()` renamed to `test_helper` inside a class pytest ignores, a module shadowed by a
duplicate basename, a file outside the collected roots, a test excluded by configuration -- each
passes an AST check and runs zero times. So the predicate here is the node ID appearing in
`pytest --collect-only`, which is the only artifact that says "this will run".
"""
from __future__ import annotations

import json
import os
import posixpath
import subprocess
import sys
from pathlib import Path

OK = 0
FAIL = 2

LEDGER_SCHEMA = "secb.reusable-pattern-ledger/v1"

# Cumulative: each state requires everything the states below it require. This is what stops a
# record walking from prose to active without acquiring evidence on the way.
LIFECYCLE = (
    "OBSERVED",
    "COUNTEREXAMPLE_REPRODUCED",
    "GUARD_CANDIDATE",
    "MUTATION_PROVEN",
    "PRE_REVIEW_ACTIVE",
    "EFFECTIVENESS_OBSERVED",
    "RETIRED",
)
STATE_REQUIREMENTS = {
    "OBSERVED": ("refusal_id", "origin", "residual_judgement"),
    "COUNTEREXAMPLE_REPRODUCED": ("counterexample",),
    "GUARD_CANDIDATE": ("guard_predicate", "authoritative_source"),
    "MUTATION_PROVEN": ("positive_fixture", "negative_fixtures", "mutation"),
    "PRE_REVIEW_ACTIVE": ("pre_review_command", "guard_strength", "effective_commit"),
    "EFFECTIVENESS_OBSERVED": ("observations",),
    "RETIRED": (),
}
ORIGIN_REQUIREMENTS = ("pr", "comment", "refused_head")


class Refused(ValueError):
    """The preflight cannot be evaluated, or a record claims more than it evidences."""


def collect_node_ids(root: Path, roots: list[str]) -> set[str]:
    """Every node ID pytest would collect, from pytest itself.

    Asking pytest is the point. Any reimplementation of collection -- globbing, AST walking,
    naming conventions -- is a second opinion about what runs, and the second opinion is the one
    that is wrong when they disagree.
    """
    command = [
        sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-q", "--collect-only",
        *roots,
    ]
    result = subprocess.run(
        command, cwd=root, capture_output=True, text=True, check=False,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    if result.returncode not in (0, 5):  # 5 = no tests collected, which is a finding not a crash
        raise Refused(
            "pytest collection failed, so no citation can be proven collectable. An unmeasured "
            f"collection is not an empty one.\n{result.stdout[-800:]}\n{result.stderr[-400:]}"
        )
    return {line.strip() for line in result.stdout.splitlines() if "::" in line}


def normalise(citation: dict) -> str:
    """Return the repository-relative POSIX path, or raise.

    Confinement is checked on the NORMALISED path, because `tests/../scripts/x.py` and
    `tests/x.py` differ only after normalisation, and an absolute path escapes the repository
    entirely. PATH_EXISTS != PATH_CONFINED.
    """
    raw = citation.get("file", "")
    if not raw:
        raise Refused("citation has no file")
    if "\\" in raw:
        raise Refused(f"citation path {raw!r} uses backslashes; declare POSIX-relative paths")
    if raw.startswith("/") or (len(raw) > 1 and raw[1] == ":"):
        raise Refused(f"citation path {raw!r} is absolute; citations are repository-relative")
    normalised = posixpath.normpath(raw)
    if normalised.startswith("..") or normalised == ".":
        raise Refused(f"citation path {raw!r} escapes the repository")
    if normalised != raw:
        raise Refused(
            f"citation path {raw!r} is not normalised (normalises to {normalised!r}); two "
            "spellings of one path are two citations that cannot be compared"
        )
    return normalised


def confined(path: str, roots: list[str]) -> bool:
    return any(path == r.rstrip("/") or path.startswith(r.rstrip("/") + "/") for r in roots)


def node_id_collected(path: str, test: str, collected: set[str]) -> bool:
    """A citation matches when pytest collected it, allowing for parametrisation."""
    exact = f"{path}::{test}"
    return exact in collected or any(
        node.startswith(exact + "[") for node in collected
    )


def check_citations(root: Path, ledger: dict, roots: list[str], collected: set[str]) -> list[str]:
    """Return findings. An empty list means every cited guard is collectable."""
    findings: list[str] = []
    for entry in ledger["patterns"]:
        for citation in entry.get("tests") or []:
            try:
                path = normalise(citation)
            except Refused as exc:
                findings.append(f"{entry['id']}: {exc}")
                continue
            if not confined(path, roots):
                findings.append(
                    f"{entry['id']}: {path} is outside the configured test roots {roots}. A guard "
                    "cited from outside the collected tree is not run by CI"
                )
                continue
            # PENDING_MERGE citations are absent from THIS tree by construction; their collection
            # is proven at the pinned head by check_pattern_ledger.py, not here. Applying an
            # identical boundary means the same path and naming rules -- not pretending the file
            # is present.
            if entry["guard"] == "PENDING_MERGE":
                continue
            if not node_id_collected(path, citation["test"], collected):
                findings.append(
                    f"{entry['id']}: {path}::{citation['test']} is not a node ID pytest collects. "
                    "A definition that is never collected runs zero times, and a guard that runs "
                    "zero times enforces nothing"
                )
    return findings


def check_promoted_refusals(records: list[dict]) -> tuple[list[str], dict]:
    """Validate lifecycle records. Raises on a contradiction; returns (findings, tally)."""
    findings: list[str] = []
    tally: dict[str, int] = {}
    seen: set[str] = set()
    for record in records:
        state = record.get("activation_state")
        if state not in LIFECYCLE:
            raise Refused(
                f"{record.get('refusal_id', '<no id>')}: activation_state {state!r} is not one of "
                f"{list(LIFECYCLE)}"
            )
        identifier = record.get("refusal_id", "")
        if identifier in seen:
            raise Refused(f"duplicate refusal_id {identifier!r}")
        seen.add(identifier)
        tally[state] = tally.get(state, 0) + 1

        # Cumulative requirements: a record at rung N must satisfy rungs 0..N.
        required: list[str] = []
        for rung in LIFECYCLE[: LIFECYCLE.index(state) + 1]:
            required.extend(STATE_REQUIREMENTS[rung])
        missing = [field for field in required if not record.get(field)]
        if missing:
            raise Refused(
                f"{identifier}: activation_state {state} requires {missing}, which are absent. A "
                "record may not advance to a rung whose evidence it does not carry -- prose "
                "cannot become active by relabelling"
            )
        origin_missing = [f for f in ORIGIN_REQUIREMENTS if not (record.get("origin") or {}).get(f)]
        if origin_missing:
            raise Refused(
                f"{identifier}: origin is missing {origin_missing}. A refusal with no pinned "
                "refused_head cannot be reproduced, and an unreproducible refusal cannot be "
                "promoted"
            )
        if state == "EFFECTIVENESS_OBSERVED":
            observations = record["observations"]
            if not observations.get("opportunities"):
                raise Refused(
                    f"{identifier}: EFFECTIVENESS_OBSERVED with zero opportunities. Effectiveness "
                    "is a ratio, and a ratio with no denominator is a claim"
                )
    return findings, tally


def main(argv: list[str]) -> int:
    env = dict(os.environ)
    root = Path(env.get("REPO_ROOT", ".")).resolve()
    ledger_path = root / env.get("LEDGER", "config/reusable_patterns.json")
    try:
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        if ledger.get("schema") != LEDGER_SCHEMA:
            raise Refused(f"ledger schema is {ledger.get('schema')!r}, expected {LEDGER_SCHEMA!r}")
        roots = ledger.get("test_roots")
        if not roots:
            raise Refused(
                "the ledger declares no test_roots. Confinement cannot be checked against an "
                "undeclared boundary, and an unchecked boundary is not a boundary"
            )
        records = ledger.get("promoted_refusals") or []
        record_findings, tally = check_promoted_refusals(records)
        collected = collect_node_ids(root, roots)
        findings = record_findings + check_citations(root, ledger, roots, collected)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"PREFLIGHT REFUSED (closed): ledger unreadable ({exc})", file=sys.stderr)
        return FAIL
    except Refused as exc:
        print(f"PREFLIGHT REFUSED (closed): {exc}", file=sys.stderr)
        return FAIL
    except (KeyError, TypeError, AttributeError) as exc:
        print(f"PREFLIGHT REFUSED (closed): malformed ledger ({exc!r})", file=sys.stderr)
        return FAIL

    active = [r["refusal_id"] for r in records if r["activation_state"] in
              ("PRE_REVIEW_ACTIVE", "EFFECTIVENESS_OBSERVED")]
    opportunities = sum((r.get("observations") or {}).get("opportunities", 0) for r in records)
    caught = sum((r.get("observations") or {}).get("caught_pre_review", 0) for r in records)
    escaped = sum((r.get("observations") or {}).get("escaped_to_review", 0) for r in records)
    false_positives = sum((r.get("observations") or {}).get("false_positives", 0) for r in records)

    report = {
        "schema": "secb.review-preflight-observation/v1",
        "MECHANICAL_PREFLIGHT": "FAIL" if findings else "PASS",
        "POLICY_REVIEW": "REQUIRED",
        "MERGE_AUTHORITY": "NOT_CONFERRED",
        "findings": findings,
        "active_guards": active,
        "lifecycle_tally": tally,
        "collected_node_ids": len(collected),
        "test_roots": roots,
        "metrics": {
            "opportunities": opportunities,
            "caught_pre_review": caught,
            "escaped_to_review": escaped,
            "false_positives": false_positives,
        },
        "residual_judgement": [
            "architecture and module boundaries",
            "authority sufficiency and trust-domain independence",
            "whether a cited test is SEMANTICALLY adequate for the pattern it guards",
            "whether a shortfall is acceptable for this change",
        ],
        "not_proven": [
            "that a clean preflight is a policy pass; it is a smaller claim, deliberately",
            "that this check is a REQUIRED status check; enforcement is read back separately",
            "that an inactive refusal class is unguarded by accident rather than by lifecycle",
        ],
        "confers_merge_authority": False,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return FAIL if findings else OK


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
