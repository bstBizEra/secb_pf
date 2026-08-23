#!/usr/bin/env python3
"""Early warning before the delegation envelope expires (SECB-WP-FWK-071, issue #130).

THE GAP. `config/delegation_envelope.json` expires on a fixed date, and
`scripts/classify_authority_delta.py` refuses an expired envelope. That refusal is correct and
it arrives too late: the check runs only when repository activity triggers it, so expiry is
first discovered when it BLOCKS an unrelated pull request, with zero operational lead time.

    ENFORCEMENT_EXISTS != WARNING_EXISTS
    TRIGGERED_BY_ACTIVITY != OBSERVED_ON_A_CLOCK

This is the observation half. It warns; it has no authority to renew, extend or edit anything,
and it never writes to the envelope.

INCLUSIVITY IS COPIED FROM THE ENFORCER, DELIBERATELY. The enforcing comparison is

    str(envelope["expires_at"]) < date.today().isoformat()

so the envelope is expired only STRICTLY AFTER `expires_at`; that date is the last valid day.
This monitor uses the same boundary. A monitor that disagreed with its enforcer by one day
would raise the alarm on the wrong day, which is worse than not raising it -- the reader would
calibrate on the monitor and be wrong at the boundary.

    MONITOR_SEMANTICS must equal ENFORCER_SEMANTICS

One difference is deliberate and is reported rather than hidden: this monitor evaluates in UTC,
while the enforcer calls `date.today()`, which is the runner's LOCAL date. On a non-UTC host the
two can differ by a day at the boundary. That is a defect in the enforcer, not something to
paper over here, and it is recorded as a finding rather than fixed in this work package.

FAIL-CLOSED. A missing, malformed or unparseable expiry is `OBSERVATION_INCOMPLETE` and
non-success -- never VALID. An absent observation is not a clean one, which is the same rule
that #163 restored to the budget gate.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path

OK = 0
FAIL = 2

THRESHOLDS_SCHEMA = "secb.envelope-expiry-thresholds/v1"
STATES = ("VALID", "RENEWAL_DUE", "CRITICAL", "EXPIRED", "OBSERVATION_INCOMPLETE")


class Incomplete(ValueError):
    """The observation could not be made. Never reported as a clean envelope."""


def digest(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def load(path: Path, label: str) -> tuple[dict, str]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise Incomplete(f"{label} is unreadable at {path} ({exc})") from exc
    try:
        return json.loads(raw), digest(raw)
    except json.JSONDecodeError as exc:
        raise Incomplete(f"{label} at {path} is not parseable JSON ({exc})") from exc


def evaluation_date(raw: str) -> date:
    """The instant of evaluation, in UTC. EVALUATE_AT makes boundary tests deterministic."""
    if not raw:
        return datetime.now(timezone.utc).date()
    try:
        text = raw.strip().replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise Incomplete(f"EVALUATE_AT {raw!r} is not an ISO-8601 date or instant ({exc})") from exc
    if parsed.tzinfo is None:
        raise Incomplete(
            f"EVALUATE_AT {raw!r} has no timezone. An instant without one is ambiguous, and the "
            "whole point of this check is which side of a date boundary we are on"
        )
    return parsed.astimezone(timezone.utc).date()


def parse_expiry(envelope: dict) -> date:
    value = envelope.get("expires_at")
    if value is None:
        raise Incomplete("the envelope declares no expires_at")
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise Incomplete(f"expires_at {value!r} is not an ISO-8601 date ({exc})") from exc


def classify(days_remaining: int, warning_days: int, critical_days: int) -> str:
    if days_remaining < 0:
        return "EXPIRED"
    if days_remaining <= critical_days:
        return "CRITICAL"
    if days_remaining <= warning_days:
        return "RENEWAL_DUE"
    return "VALID"


def read_thresholds(path: Path) -> tuple[dict, str]:
    thresholds, thresholds_digest = load(path, "the threshold configuration")
    if thresholds.get("schema") != THRESHOLDS_SCHEMA:
        raise Incomplete(
            f"threshold schema is {thresholds.get('schema')!r}, expected {THRESHOLDS_SCHEMA!r}"
        )
    for key in ("warning_days", "critical_days"):
        value = thresholds.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise Incomplete(f"{key} is {value!r}; a threshold must be a non-negative integer")
    if thresholds["critical_days"] > thresholds["warning_days"]:
        raise Incomplete(
            f"critical_days ({thresholds['critical_days']}) exceeds warning_days "
            f"({thresholds['warning_days']}), so CRITICAL would fire before RENEWAL_DUE and the "
            "ladder would report a less urgent state as the envelope got closer to expiry"
        )
    unknown = [s for s in thresholds.get("fail_states", []) if s not in STATES]
    if unknown:
        raise Incomplete(f"fail_states names unknown state(s) {unknown}; valid states {list(STATES)}")
    return thresholds, thresholds_digest


def declared_envelope(env: dict) -> str:
    """The envelope to observe, which the CALLER must name.

    This used to default to `config/delegation_envelope.json`. That default was the only subject
    any caller ever wanted, which is precisely what made it dangerous: a caller that MEANT to name
    an envelope and failed to -- a renamed variable, an edited workflow -- received a confident
    `VALID` verdict about a different file, with nothing in the output to say so.

        ABSENT_SUBJECT != DEFAULTED_SUBJECT

    `days_remaining: 78` about an envelope nobody asked about is worse than a refusal. The
    scheduled monitor still observes this repository's own envelope; it now says so at the call
    site rather than relying on this script to assume it.
    """
    declared = env.get("ENVELOPE", "").strip()
    if not declared:
        raise Incomplete(
            "no envelope was named: set ENVELOPE to the path to observe. This gate does not "
            "default, because a caller whose subject went missing would otherwise be handed a "
            "confident verdict about a file it never asked about"
        )
    return declared


def main(argv: list[str]) -> int:
    env = dict(os.environ)
    root = Path(env.get("REPO_ROOT", ".")).resolve()
    thresholds_path = root / env.get("THRESHOLDS", "config/envelope_expiry_thresholds.json")

    evaluated_at = datetime.now(timezone.utc).isoformat()
    try:
        thresholds, thresholds_digest = read_thresholds(thresholds_path)
        envelope_path = root / declared_envelope(env)
        envelope, envelope_digest = load(envelope_path, "the delegation envelope")
        today = evaluation_date(env.get("EVALUATE_AT", ""))
        expires_at = parse_expiry(envelope)
        days_remaining = (expires_at - today).days
        state = classify(days_remaining, thresholds["warning_days"], thresholds["critical_days"])
        fail_states = thresholds.get("fail_states", ["EXPIRED", "OBSERVATION_INCOMPLETE"])
    except Incomplete as exc:
        # Fail closed, and say what could not be observed. An unreadable threshold file cannot
        # yield a threshold-derived verdict, so nothing here pretends to one.
        print(json.dumps({
            "schema": "secb.envelope-expiry-observation/v1",
            "state": "OBSERVATION_INCOMPLETE",
            "reason": str(exc),
            "evaluated_at_utc": evaluated_at,
            "days_remaining": None,
            "confers_renewal_authority": False,
        }, indent=2, sort_keys=True))
        print(f"ENVELOPE EXPIRY: OBSERVATION_INCOMPLETE -- {exc}", file=sys.stderr)
        return FAIL

    report = {
        "schema": "secb.envelope-expiry-observation/v1",
        "envelope_digest": envelope_digest,
        "threshold_config_digest": thresholds_digest,
        "evaluated_at_utc": evaluated_at,
        "evaluation_date_utc": today.isoformat(),
        "expires_at": expires_at.isoformat(),
        "days_remaining": days_remaining,
        "state": state,
        "thresholds": {
            "warning_days": thresholds["warning_days"],
            "critical_days": thresholds["critical_days"],
        },
        "inclusivity": "expires_at is the last valid day, matching classify_authority_delta.py",
        "not_proven": [
            "that the envelope will be renewed; this observes, it does not act",
            "that the enforcing gate agrees at a date boundary on a non-UTC host, because it "
            "calls date.today() (local) while this evaluates in UTC",
        ],
        "confers_renewal_authority": False,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    if state in fail_states:
        print(
            f"ENVELOPE EXPIRY: {state} -- {days_remaining} day(s) remain until {expires_at}. "
            "This job is early warning only: it holds no authority to renew or extend the "
            "envelope, and renewal is a human decision.",
            file=sys.stderr,
        )
        return FAIL
    return OK


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
