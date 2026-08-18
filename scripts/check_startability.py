#!/usr/bin/env python3
"""Resolve whether a work package is STARTABLE, from evidence (FWK-075, issue #137).

WHY. On 2026-08-15 the queue correctly declined to start FWK-074 (its parser existed only on
unmerged #134) and selected FWK-070 instead. That was the right call, made by reasoning, and
reasoning is not auditable. This makes the same decision reproducible.

    DESIGNABLE != STARTABLE
    QUEUE_BLOCKED != NO_ELIGIBLE_WORK

The second line is this round's own lesson: the merge queue was fully blocked and sixteen
operator-authored work packages had no implementing PR. A resolver that only looked at the queue
would have reported nothing to do.

WHAT IT REFUSES TO DO. It recommends; it grants nothing.

    RESOLVER_RECOMMENDS != WORK_AUTHORISED != MERGE_AUTHORISED

Unknown, stale, unparsed, assumed and proposed-only values are NOT truthy. A conjunct with no
evidence is `UNKNOWN`, and `UNKNOWN` blocks -- it never defaults to satisfied. A blocked
assessment must name the event that would make re-evaluation meaningful, because polling without
a state change must never turn BLOCKED into STARTABLE.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

OK = 0
FAIL = 2

SCHEMA = "secb.startability-assessment/v1"

IMPLEMENTATION_STATES = (
    "STARTABLE",
    "BLOCKED_BY_BYTES",
    "BLOCKED_BY_SEMANTIC_DEPENDENCY",
    "BLOCKED_BY_CONTENTION",
    "BLOCKED_BY_TASK_CONTEXT",
    "BLOCKED_BY_AUTHORITY",
    "BLOCKED_BY_UNKNOWN",
)
DEPENDENCY_CLASSES = {
    "BYTE_DEPENDENCY": "BLOCKED_BY_BYTES",
    "SEMANTIC_DEPENDENCY": "BLOCKED_BY_SEMANTIC_DEPENDENCY",
    "ORDERING_DEPENDENCY": "BLOCKED_BY_SEMANTIC_DEPENDENCY",
    "AUTHORITY_DEPENDENCY": "BLOCKED_BY_AUTHORITY",
    "CONTENT_REUSE_DEPENDENCY": "BLOCKED_BY_BYTES",
    "OBSERVATION_DEPENDENCY": "BLOCKED_BY_UNKNOWN",
}
# Only an EFFECTIVE_MAIN projection can satisfy a dependency. A proposed head may explain what
# WILL become startable; it cannot make an effective-main dependency true.
PROJECTIONS = ("EFFECTIVE_MAIN", "PROPOSED_HEAD")

CONJUNCTS = (
    "work_package_defined",
    "required_dependencies_resolved_on_effective_base",
    "required_bytes_available_on_effective_base",
    "canonical_reuse_target_available",
    "semantic_preconditions_satisfied",
    "contention_assessed_at_hunk_and_object_level",
    "task_context_coherent",
    "authority_route_available_for_proposed_change",
    "no_unresolved_unknowns",
)


class Refused(ValueError):
    """The assessment cannot be evaluated as written."""


def truthy(value: object) -> bool:
    """Only an explicit boolean true counts.

    A string, a null, a missing key or the word "assumed" are all NOT satisfied. This is the
    whole discipline in one function: an unevaluated conjunct must never read as a met one.
    """
    return value is True


def check_dependency(dep: dict, index: int) -> str | None:
    """Return the blocking implementation_state for one dependency, or None if resolved."""
    kind = dep.get("class")
    if kind not in DEPENDENCY_CLASSES:
        raise Refused(
            f"dependency[{index}]: class {kind!r} is not one of {sorted(DEPENDENCY_CLASSES)}"
        )
    if not dep.get("as_of_ref"):
        raise Refused(
            f"dependency[{index}]: no as_of_ref. A dependency verdict with no revision is not "
            "reproducible, and an unreproducible verdict is not evidence"
        )
    projection = dep.get("projection")
    if projection not in PROJECTIONS:
        raise Refused(f"dependency[{index}]: projection {projection!r} is not one of {PROJECTIONS}")

    if not truthy(dep.get("resolved")):
        return DEPENDENCY_CLASSES[kind]
    if projection != "EFFECTIVE_MAIN":
        # A dependency satisfied only on a proposed head is satisfied nowhere that counts.
        # Mergeable-and-green is still proposed: PROPOSED_HEAD_GREEN != LANDED.
        return DEPENDENCY_CLASSES[kind]
    return None


def check_contention(contention: dict) -> tuple[bool, list[str]]:
    """Three dimensions, reported independently.

        same file != overlapping hunks != semantic contention
        different files != independent authoritative objects

    A clean merge is evidence about TEXT only. It is not evidence about execution order, which is
    why `valid_execution_order` is separate and a false value blocks even when git is happy.
    """
    required = ("same_file", "overlapping_hunks", "same_authoritative_object")
    missing = [d for d in required if d not in contention]
    if missing:
        raise Refused(
            f"contention is missing dimension(s) {missing}. Each must be reported "
            "independently -- collapsing them is how 'different files' becomes a false "
            "clean bill of health for one shared authoritative object"
        )
    blockers = []
    if truthy(contention["overlapping_hunks"]):
        blockers.append("overlapping hunks with a concurrent change")
    if truthy(contention["same_authoritative_object"]):
        blockers.append("a concurrent change to the same authoritative object")
    if "valid_execution_order" in contention and not truthy(contention["valid_execution_order"]):
        blockers.append(
            "required execution order is not satisfied (a clean textual merge does not make an "
            "ordering valid)"
        )
    return (not blockers), blockers


def assess(record: dict) -> dict:
    if record.get("schema") != SCHEMA:
        raise Refused(f"schema is {record.get('schema')!r}, expected {SCHEMA!r}")
    for field in ("work_package_id", "as_of_ref", "projection", "design_state"):
        if not record.get(field):
            raise Refused(f"the assessment declares no {field}")
    if record["projection"] not in PROJECTIONS:
        raise Refused(f"projection {record['projection']!r} is not one of {PROJECTIONS}")
    if record["design_state"] not in ("DESIGNABLE", "BLOCKED"):
        raise Refused(f"design_state {record['design_state']!r} is not DESIGNABLE or BLOCKED")

    conjuncts = record.get("conjuncts") or {}
    unknown_keys = sorted(set(conjuncts) - set(CONJUNCTS))
    if unknown_keys:
        raise Refused(f"unrecognised conjunct(s) {unknown_keys}")

    blockers: list[str] = []
    states: list[str] = []

    # Dependencies first: they are the most common blocker and they carry their own class.
    for index, dep in enumerate(record.get("dependencies") or []):
        state = check_dependency(dep, index)
        if state:
            states.append(state)
            blockers.append(
                f"{dep['class']} unresolved on {dep['projection']}: "
                f"{dep.get('description', '(no description)')}"
            )

    contention = record.get("contention")
    if contention is None:
        states.append("BLOCKED_BY_CONTENTION")
        blockers.append("contention was not assessed; an unassessed boundary is not a clear one")
    else:
        clear, found = check_contention(contention)
        if not clear:
            states.append("BLOCKED_BY_CONTENTION")
            blockers.extend(found)

    # Every conjunct must be explicitly true. Absent is UNKNOWN, and UNKNOWN blocks.
    for name in CONJUNCTS:
        if name not in conjuncts:
            states.append("BLOCKED_BY_UNKNOWN")
            blockers.append(f"conjunct {name} is UNKNOWN -- absent, not satisfied")
        elif not truthy(conjuncts[name]):
            states.append({
                "required_bytes_available_on_effective_base": "BLOCKED_BY_BYTES",
                "canonical_reuse_target_available": "BLOCKED_BY_BYTES",
                "semantic_preconditions_satisfied": "BLOCKED_BY_SEMANTIC_DEPENDENCY",
                "task_context_coherent": "BLOCKED_BY_TASK_CONTEXT",
                "authority_route_available_for_proposed_change": "BLOCKED_BY_AUTHORITY",
            }.get(name, "BLOCKED_BY_UNKNOWN"))
            blockers.append(f"conjunct {name} is not satisfied")

    if record["design_state"] == "BLOCKED" and not states:
        raise Refused(
            "design_state is BLOCKED while every implementation conjunct is satisfied. "
            "DESIGNABLE != STARTABLE runs both ways: a package that cannot be specified cannot "
            "be reported ready to implement"
        )

    if states:
        # Report the most specific blocker rather than a generic one. BLOCKED_BY_UNKNOWN is the
        # weakest claim, so it loses to any state that names an actual cause.
        ordered = [s for s in IMPLEMENTATION_STATES if s in states and s != "BLOCKED_BY_UNKNOWN"]
        state = ordered[0] if ordered else "BLOCKED_BY_UNKNOWN"
    else:
        state = "STARTABLE"

    if state != "STARTABLE" and not record.get("next_recheck_trigger"):
        raise Refused(
            f"{record['work_package_id']} is {state} with no next_recheck_trigger. A blocked "
            "assessment must name the event that makes re-evaluation meaningful; otherwise "
            "polling alone turns BLOCKED into STARTABLE, which is exactly what evidence forbids"
        )

    return {
        "schema": "secb.startability-observation/v1",
        "work_package_id": record["work_package_id"],
        "as_of_ref": record["as_of_ref"],
        "projection": record["projection"],
        "design_state": record["design_state"],
        "implementation_state": state,
        "blockers": blockers,
        "next_recheck_trigger": record.get("next_recheck_trigger"),
        "contention": contention,
        "confers_work_authority": False,
        "not_proven": [
            "that a STARTABLE package is authorised; the resolver recommends and grants nothing",
            "that an assessment survives a change to main, an open head, or the work package",
            "that a clean textual merge implies a valid execution order",
        ],
    }


def select(assessments: list[dict], effective_ref: str) -> dict:
    """The deterministic selection rule. Never picks a blocked item because nothing else is left."""
    startable = [a for a in assessments if a["implementation_state"] == "STARTABLE"]
    stale = [a["work_package_id"] for a in assessments if a["as_of_ref"] != effective_ref]
    fresh = [a for a in startable if a["as_of_ref"] == effective_ref]
    return {
        "selected": fresh[0]["work_package_id"] if fresh else None,
        "startable": [a["work_package_id"] for a in startable],
        "excluded_stale": stale,
        "blocking_frontier": [
            {"work_package_id": a["work_package_id"],
             "implementation_state": a["implementation_state"],
             "next_recheck_trigger": a.get("next_recheck_trigger")}
            for a in assessments if a["implementation_state"] != "STARTABLE"
        ],
        "rule": (
            "excluded non-STARTABLE, excluded assessments stale against the effective ref, "
            "preserved declared order. If nothing is startable the frontier is reported and "
            "NOTHING is selected -- a blocked item is never chosen merely because it is all "
            "that remains."
        ),
    }


def main(argv: list[str]) -> int:
    env = dict(os.environ)
    path = env.get("ASSESSMENTS", "").strip()
    if not path:
        print("REFUSED (closed): ASSESSMENTS is required", file=sys.stderr)
        return FAIL
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        records = payload if isinstance(payload, list) else [payload]
        assessments = [assess(record) for record in records]
        effective_ref = env.get("EFFECTIVE_REF", "").strip()
        selection = select(assessments, effective_ref) if effective_ref else None
    except (OSError, json.JSONDecodeError) as exc:
        print(f"REFUSED (closed): assessments unreadable ({exc})", file=sys.stderr)
        return FAIL
    except Refused as exc:
        print(f"REFUSED (closed): {exc}", file=sys.stderr)
        return FAIL
    except (KeyError, TypeError, AttributeError) as exc:
        print(f"REFUSED (closed): malformed assessment ({exc!r})", file=sys.stderr)
        return FAIL

    print(json.dumps({
        "schema": "secb.startability-report/v1",
        "assessments": assessments,
        "selection": selection,
        "confers_work_authority": False,
    }, indent=2, sort_keys=True))
    return OK if any(a["implementation_state"] == "STARTABLE" for a in assessments) else FAIL


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
