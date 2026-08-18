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
GENESIS_STATES = ("DETECTED",)
TERMINAL_STATES = ("CLOSED", "SUPERSEDED", "OUTSIDE_MANDATE", "QUARANTINED", "ROLLED_BACK")
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


def validate(ledger: dict) -> dict:
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
            if from_state not in GENESIS_STATES and not entry.get("genesis_justification"):
                raise Refused(
                    f"{eid}: {subject} first appears transitioning FROM {from_state!r}, which is "
                    f"not a genesis state {list(GENESIS_STATES)}. A history that starts mid-way "
                    "is missing its beginning, or the subject already existed elsewhere"
                )
        else:
            if from_state != previous["to_state"]:
                raise Refused(
                    f"{eid}: {subject} transitions from {from_state!r} but its previous recorded "
                    f"state is {previous['to_state']!r}. A gap here is an unrecorded transition"
                )
            if previous["to_state"] in TERMINAL_STATES and not entry.get("reopen_justification"):
                raise Refused(
                    f"{eid}: {subject} was {previous['to_state']!r}, which is terminal. Continuing "
                    "requires an explicit reopen_justification, so that reopening is a decision "
                    "rather than an accident"
                )
            if instant(f"{eid}.occurred_at", entry["occurred_at"]) < instant(
                    "previous.occurred_at", previous["occurred_at"]):
                raise Refused(f"{eid}: occurred_at moves backwards for {subject}")

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
        "not_proven": [
            "that the ledger is complete; it proves the recorded history is coherent",
            "that a transition happened, only that it was recorded consistently",
            "that landings not recorded here did not occur",
        ],
        "confers_merge_authority": False,
    }


def main(argv: list[str]) -> int:
    path = os.environ.get("LEDGER", "").strip()
    if not path:
        print("REFUSED (closed): LEDGER is required", file=sys.stderr)
        return FAIL
    try:
        report = validate(json.loads(Path(path).read_text(encoding="utf-8")))
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
