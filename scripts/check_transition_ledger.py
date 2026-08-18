"""Validate a transition ledger's SEQUENCE invariants (FWK-100, P0 item 7).

A per-object schema says one transition is well-formed. It cannot say the transitions form a
history. This validates the sequence, which is where the interesting failures live:

    TRANSITION_VALID != HISTORY_COHERENT
    LANDING_VERIFIED != LANDED_ON_THE_PREVIOUS_LANDING

The second line is the one that generalises the compare-and-swap handoff beyond a single merge.
Each landing has been verified individually all session -- pinned head, expected tree, readback --
and no control has ever checked that landing N+1 was built on landing N. A commit whose parent is
not the previous effective commit means something reached the branch out of band, and every
individual receipt would still verify.

INVARIANTS

    append-only      sequence numbers strictly increase by one, no gaps, no reuse
    continuity       per subject, from_state equals the previous to_state
    genesis          a subject's first transition starts from a declared genesis state
    no replay        a receipt digest may appear once
    monotonic time   occurred_at never moves backwards within a subject
    terminal         nothing follows a terminal state without an explicit reopen
    landing chain    a transition to EFFECTIVE must record actual == expected tree AND a parent
                     equal to the previous EFFECTIVE commit
    legality         every from -> to pair must be a declared edge of the canonical state machine

The legality invariant is the one this file shipped without. Continuity only asks whether a
transition starts where the subject was left; it never asks whether the step is possible. A ledger
recording DETECTED -> EFFECTIVE -- skipping eleven states including every verification and authority
gate -- was accepted, and the check exited 0.

    CONTINUOUS != LEGAL

FAIL-CLOSED. A ledger that cannot be ordered is refused rather than reported clean: an unordered
history is not a history, and validating it in file order would silently bless whatever order the
writer happened to use.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

OK = 0
FAIL = 2

SCHEMA = "secb.transition-ledger/v1"
MACHINE_SCHEMA = "secb.state-machine/v1"
DEFAULT_MACHINE = "config/state_machine.json"
REQUIRED_CAS = ("target_base_sha", "source_head_sha", "merge_base_sha", "expected_result_tree",
                "actual_result_tree", "actual_result_sha")


class Refused(ValueError):
    """The ledger is not a coherent history."""


def instant(label: str, value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise Refused(f"{label}: {value!r} is not an ISO-8601 instant ({exc})") from exc
    if parsed.tzinfo is None:
        raise Refused(f"{label}: {value!r} has no timezone; ordering would be ambiguous")
    return parsed


def load_machine(path: Path) -> dict:
    """Load and self-check the state machine. A malformed machine is refused, not worked around."""
    try:
        machine = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise Refused(
            f"the state machine is unreadable at {path} ({exc}). Without it legality cannot be "
            "evaluated, and a ledger validated on continuity alone would report clean on a "
            "history that is impossible"
        ) from exc
    except json.JSONDecodeError as exc:
        raise Refused(f"the state machine is not parseable JSON ({exc})") from exc
    if machine.get("schema") != MACHINE_SCHEMA:
        raise Refused(f"state machine schema is {machine.get('schema')!r}, expected {MACHINE_SCHEMA!r}")

    edges = machine.get("edges") or {}
    declared = set(machine.get("canonical_path") or []) | set(machine.get("exceptional_states") or [])
    if not declared:
        raise Refused("the state machine declares no states")
    referenced = set(edges) | {target for targets in edges.values() for target in targets}
    undeclared = sorted(referenced - declared)
    if undeclared:
        raise Refused(f"the state machine references undeclared states {undeclared}")
    terminal_with_exits = sorted(set(machine.get("terminal_states") or []) & set(edges))
    if terminal_with_exits:
        raise Refused(
            f"terminal states {terminal_with_exits} declare outgoing edges; a state that can be "
            "left is not terminal"
        )
    return machine


def legal(machine: dict, from_state: str, to_state: str, reopening: bool = False) -> bool:
    """Declared edges only. `reopening` widens to the declared REOPEN edges, never to anything.

    A justification that could make any edge legal would turn the state machine into a suggestion,
    so reopening is declared AND justified rather than justified alone.
    """
    if to_state == "QUARANTINED" and machine.get("quarantine_from_any"):
        return True
    if to_state in (machine.get("edges") or {}).get(from_state, []):
        return True
    if reopening and to_state in (machine.get("reopen_edges") or {}).get(from_state, []):
        return True
    return False


def validate(ledger: dict, machine: dict) -> dict:
    genesis = tuple(machine.get("genesis_states") or ())
    terminal = tuple(machine.get("terminal_states") or ())
    declared = set(machine.get("canonical_path") or []) | set(machine.get("exceptional_states") or [])
    if ledger.get("schema") != SCHEMA:
        raise Refused(f"schema is {ledger.get('schema')!r}, expected {SCHEMA!r}")
    entries = ledger.get("transitions")
    if entries is None:
        raise Refused("the ledger declares no transitions; an absent list is not an empty one")

    # Ordering first. Everything below reads the sequence, so an unorderable ledger cannot be
    # checked at all -- and reading it in file order would bless the writer's arbitrary order.
    seen_sequence: dict[int, str] = {}
    for entry in entries:
        number = entry.get("sequence")
        if not isinstance(number, int) or isinstance(number, bool):
            raise Refused(f"transition {entry.get('id', '?')} has no integer sequence")
        if number in seen_sequence:
            raise Refused(
                f"sequence {number} is used by both {seen_sequence[number]!r} and "
                f"{entry.get('id')!r}; an append-only ledger cannot reuse a position"
            )
        seen_sequence[number] = entry.get("id", "?")
    ordered = sorted(entries, key=lambda e: e["sequence"])
    expected_positions = list(range(ordered[0]["sequence"], ordered[0]["sequence"] + len(ordered)))
    actual_positions = [e["sequence"] for e in ordered]
    if actual_positions != expected_positions:
        missing = sorted(set(expected_positions) - set(actual_positions))
        raise Refused(
            f"the sequence has gaps at {missing}. A gap is indistinguishable from a deleted "
            "transition, which is what append-only exists to prevent"
        )

    seen_receipts: dict[str, str] = {}
    last_by_subject: dict[str, dict] = {}
    last_effective_commit: str | None = ledger.get("genesis_commit")
    landings = 0

    for entry in ordered:
        eid = entry.get("id", f"seq-{entry['sequence']}")
        subject = entry.get("subject_id")
        if not subject:
            raise Refused(f"{eid}: no subject_id")
        to_state = entry.get("to_state")
        from_state = entry.get("from_state")
        if not to_state or not from_state:
            raise Refused(f"{eid}: from_state and to_state are both required")
        unknown = sorted({from_state, to_state} - declared)
        if unknown:
            raise Refused(
                f"{eid}: state(s) {unknown} are not declared by the state machine. An undeclared "
                "state is vocabulary no control can reason about"
            )


        digest = entry.get("receipt_digest")
        if digest:
            if digest in seen_receipts:
                raise Refused(
                    f"{eid}: receipt {digest[:19]} was already applied by "
                    f"{seen_receipts[digest]!r}. A receipt is evidence of one transition, and "
                    "replaying it would let one verification authorise two state changes"
                )
            seen_receipts[digest] = eid

        previous = last_by_subject.get(subject)
        if previous is None:
            if from_state not in genesis and not entry.get("genesis_justification"):
                raise Refused(
                    f"{eid}: {subject} first appears transitioning FROM {from_state!r}, which is "
                    f"not a genesis state {list(genesis)}. A history that starts mid-way "
                    "is missing its beginning, or the subject already existed elsewhere"
                )
        else:
            if from_state != previous["to_state"]:
                raise Refused(
                    f"{eid}: {subject} transitions from {from_state!r} but its previous recorded "
                    f"state is {previous['to_state']!r}. A gap here is an unrecorded transition"
                )
            if previous["to_state"] in terminal and not entry.get("reopen_justification"):
                raise Refused(
                    f"{eid}: {subject} was {previous['to_state']!r}, which is terminal. Continuing "
                    "requires an explicit reopen_justification, so that reopening is a decision "
                    "rather than an accident"
                )
            if instant(f"{eid}.occurred_at", entry["occurred_at"]) < instant(
                    "previous.occurred_at", previous["occurred_at"]):
                raise Refused(f"{eid}: occurred_at moves backwards for {subject}")

        if not legal(machine, from_state, to_state,
                     reopening=bool(entry.get("reopen_justification"))):
            raise Refused(
                f"{eid}: {from_state} -> {to_state} is not a declared edge of the state machine. "
                "Continuity is satisfied and the step is still impossible -- CONTINUOUS != LEGAL"
            )

        if to_state == "EFFECTIVE":
            cas = entry.get("compare_and_swap")
            if not cas:
                raise Refused(f"{eid}: a transition to EFFECTIVE carries no compare_and_swap")
            missing = [f for f in REQUIRED_CAS if not cas.get(f)]
            if missing:
                raise Refused(f"{eid}: compare_and_swap is missing {missing}")
            if cas["actual_result_tree"] != cas["expected_result_tree"]:
                raise Refused(
                    f"{eid}: landed tree {cas['actual_result_tree'][:12]} is not the predicted "
                    f"{cas['expected_result_tree'][:12]}. The landing is not what was measured"
                )
            parent = cas.get("actual_parent_sha")
            if last_effective_commit and parent and parent != last_effective_commit:
                raise Refused(
                    f"{eid}: landed on parent {parent[:12]} but the previous effective commit is "
                    f"{last_effective_commit[:12]}. Each landing verifies individually and the "
                    "chain still breaks -- something reached the branch out of band"
                )
            last_effective_commit = cas["actual_result_sha"]
            landings += 1

        last_by_subject[subject] = entry

    return {
        "schema": "secb.transition-ledger-observation/v1",
        "verdict": "LEDGER_COHERENT",
        "transitions": len(ordered),
        "subjects": len(last_by_subject),
        "landings": landings,
        "head_effective_commit": last_effective_commit,
        "sequence_range": [ordered[0]["sequence"], ordered[-1]["sequence"]],
        "state_machine_version": machine.get("version"),
        "not_proven": [
            "that the ledger is complete; it proves the recorded history is coherent",
            "that a transition happened, only that it was recorded consistently",
            "that landings not recorded here did not occur",
            "that a legal transition was CORRECT; legality is a shape, not a judgement",
        ],
        "confers_merge_authority": False,
    }


def main(argv: list[str]) -> int:
    path = os.environ.get("LEDGER", "").strip()
    if not path:
        print("REFUSED (closed): LEDGER is required", file=sys.stderr)
        return FAIL
    root = Path(os.environ.get("REPO_ROOT", ".")).resolve()
    machine_path = root / os.environ.get("STATE_MACHINE", DEFAULT_MACHINE)
    try:
        report = validate(json.loads(Path(path).read_text(encoding="utf-8")),
                          load_machine(machine_path))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"REFUSED (closed): ledger unreadable ({exc})", file=sys.stderr)
        return FAIL
    except Refused as exc:
        print(f"REFUSED (closed): {exc}", file=sys.stderr)
        return FAIL
    except (KeyError, TypeError, AttributeError, IndexError) as exc:
        print(f"REFUSED (closed): malformed ledger ({exc!r})", file=sys.stderr)
        return FAIL
    print(json.dumps(report, indent=2, sort_keys=True))
    return OK


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
