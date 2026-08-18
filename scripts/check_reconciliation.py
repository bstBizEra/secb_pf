#!/usr/bin/env python3
"""Reconcile DECLARED state against OBSERVED state (FWK-099, P0 item 10).

WHY THIS IS THE PRIORITY. The stability mandate ranks false closure third, above production gaps
and non-deterministic gates, and nothing above it is open. Closure is the one claim that decays
silently: a work package declared CLOSED stays closed in every report even after the head it was
measured against is superseded, the branch is deleted, or the evidence it cited stops resolving.

    DECLARED_CLOSED != OBSERVABLY_CLOSED
    RECEIPT_EXISTS != RECEIPT_STILL_APPLIES

WHAT IT DETECTS. Six divergence classes, each reported separately because collapsing them into
"out of sync" loses the only information that tells an operator what to do:

    FALSE_CLOSURE            declared closed, observably not landed
    ORPHANED_WORK            declared active, no observable subject
    SUPERSEDED_HEAD          evidence bound to a head that is no longer the subject's head
    STALE_RECEIPT            receipt bound to a base that is no longer effective
    UNVERIFIABLE_RELEASE     released artifact whose evidence no longer resolves
    DEPENDENCY_INVERSION     a subject declared ready whose declared dependency has not landed

HERMETIC BY CONSTRUCTION. It takes a state SNAPSHOT and reconciles it. It performs no network
calls, so it cannot silently reconcile against a state it fetched at an unknown time -- the
snapshot carries its own observation instant, and a snapshot with no instant is refused. Gathering
is a separate concern with separate trust: SNAPSHOT_SUPPLIED != STATE_OBSERVED_NOW.

WHAT IT WILL NOT DO. It reports; it repairs nothing and closes nothing. A reconciler that could
edit the state it audits would be able to make its own report clean.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

OK = 0
FAIL = 2

SCHEMA = "secb.reconciliation-snapshot/v1"

DIVERGENCE_CLASSES = (
    "FALSE_CLOSURE",
    "ORPHANED_WORK",
    "SUPERSEDED_HEAD",
    "STALE_RECEIPT",
    "UNVERIFIABLE_RELEASE",
    "DEPENDENCY_INVERSION",
)
CLOSED_STATES = ("CLOSED", "EFFECTIVE", "RECONCILED")
ACTIVE_STATES = ("ADMITTED", "AUTHORIZED", "EXECUTING", "CANDIDATE_READY", "VERIFYING",
                 "CHALLENGING", "ELIGIBLE", "COMMITTING", "OBSERVING")


class Refused(ValueError):
    """The snapshot cannot be reconciled as given."""


def parse_instant(label: str, value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise Refused(f"{label}: {value!r} is not an ISO-8601 instant ({exc})") from exc
    if parsed.tzinfo is None:
        raise Refused(f"{label}: {value!r} has no timezone")
    return parsed


def reconcile(snapshot: dict) -> tuple[list[dict], dict]:
    """Return (divergences, tally). Raises when the snapshot itself cannot be trusted."""
    if snapshot.get("schema") != SCHEMA:
        raise Refused(f"schema is {snapshot.get('schema')!r}, expected {SCHEMA!r}")
    if not snapshot.get("observed_at"):
        raise Refused(
            "the snapshot declares no observed_at. A reconciliation against state of unknown age "
            "cannot distinguish 'agrees' from 'agreed at some point'"
        )
    parse_instant("observed_at", snapshot["observed_at"])
    effective_base = snapshot.get("effective_base_sha")
    if not effective_base:
        raise Refused(
            "the snapshot declares no effective_base_sha, so STALE_RECEIPT cannot be evaluated "
            "and a clean report would be a claim about a comparison never made"
        )

    subjects = snapshot.get("subjects")
    if subjects is None:
        raise Refused("the snapshot declares no subjects; an absent list is not an empty one")

    landed = {s["id"] for s in subjects if s.get("observed_landed") is True}
    divergences: list[dict] = []

    def report(kind: str, subject: str, detail: str) -> None:
        divergences.append({"class": kind, "subject": subject, "detail": detail})

    for subject in subjects:
        sid = subject.get("id")
        if not sid:
            raise Refused("a subject has no id")
        declared = subject.get("declared_state")
        if declared is None:
            raise Refused(f"{sid}: no declared_state. UNKNOWN is not CLOSED, and it is not clean")

        # FALSE_CLOSURE -- the class this tool exists for.
        if declared in CLOSED_STATES and subject.get("observed_landed") is not True:
            report("FALSE_CLOSURE", sid,
                   f"declared {declared} but not observably landed; closure is a claim about the "
                   "repository, not about the tracker")

        # ORPHANED_WORK -- declared in flight with nothing observable behind it.
        if declared in ACTIVE_STATES and not subject.get("observed_subject_exists", True):
            report("ORPHANED_WORK", sid,
                   f"declared {declared} but no observable subject (branch or pull request)")

        # SUPERSEDED_HEAD -- evidence bound to a head the subject has moved past.
        evidence_head = subject.get("evidence_head_sha")
        observed_head = subject.get("observed_head_sha")
        if evidence_head and observed_head and evidence_head != observed_head:
            report("SUPERSEDED_HEAD", sid,
                   f"evidence binds {evidence_head[:12]} but the head is {observed_head[:12]}; "
                   "the evidence remains valid history and does not describe this subject")

        # STALE_RECEIPT -- receipt measured against a base that is no longer effective.
        receipt_base = subject.get("receipt_base_sha")
        if receipt_base and receipt_base != effective_base:
            report("STALE_RECEIPT", sid,
                   f"receipt bound to base {receipt_base[:12]}, effective base is "
                   f"{effective_base[:12]}; SUPERSEDED_FOR_CURRENT_ELIGIBILITY, not invalid history")

        # UNVERIFIABLE_RELEASE -- a release whose evidence no longer resolves.
        if subject.get("released") and subject.get("evidence_resolvable") is False:
            report("UNVERIFIABLE_RELEASE", sid,
                   "released, and its evidence no longer resolves; closure is valid only while "
                   "its evidence remains verifiable")

        # DEPENDENCY_INVERSION -- ready on paper, dependency not landed in fact.
        for dependency in subject.get("declared_dependencies") or []:
            if declared in ("ELIGIBLE", "COMMITTING") and dependency not in landed:
                report("DEPENDENCY_INVERSION", sid,
                       f"declared {declared} while dependency {dependency} has not landed")

    tally = {cls: sum(1 for d in divergences if d["class"] == cls) for cls in DIVERGENCE_CLASSES}
    return divergences, tally


def main(argv: list[str]) -> int:
    env = dict(os.environ)
    path = env.get("SNAPSHOT", "").strip()
    if not path:
        print("REFUSED (closed): SNAPSHOT is required", file=sys.stderr)
        return FAIL
    try:
        snapshot = json.loads(Path(path).read_text(encoding="utf-8"))
        divergences, tally = reconcile(snapshot)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"REFUSED (closed): snapshot unreadable ({exc})", file=sys.stderr)
        return FAIL
    except Refused as exc:
        print(f"REFUSED (closed): {exc}", file=sys.stderr)
        return FAIL
    except (KeyError, TypeError, AttributeError) as exc:
        print(f"REFUSED (closed): malformed snapshot ({exc!r})", file=sys.stderr)
        return FAIL

    print(json.dumps({
        "schema": "secb.reconciliation-verdict/v1",
        "verdict": "RECONCILED" if not divergences else "DIVERGENCE_FOUND",
        "observed_at": snapshot["observed_at"],
        "effective_base_sha": snapshot["effective_base_sha"],
        "subjects_examined": len(snapshot["subjects"]),
        "divergences": divergences,
        "tally": tally,
        "not_proven": [
            "that the snapshot describes the state as of now; it describes observed_at",
            "that an absent divergence class was checked against real data rather than an "
            "empty field -- a subject that omits evidence_head_sha cannot report SUPERSEDED_HEAD",
        ],
        "repairs_nothing": True,
        "confers_merge_authority": False,
    }, indent=2, sort_keys=True))
    return OK if not divergences else FAIL


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
