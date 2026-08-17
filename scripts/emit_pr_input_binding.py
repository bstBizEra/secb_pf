#!/usr/bin/env python3
"""Bind a gate result to the pull-request metadata it actually evaluated.

`SECB-WP-FWK-068` (issue #127).

A check attached only to `head_sha` goes stale the moment a title or body is edited,
and **GitHub does not mark it stale**. Measured, not supposed: the Gate 1 log for PR
#122 at head `1a569a9` recorded

    WP_TEXT: SECB-WP-FWK-062: register C-5, C-6, C-7 …
    AUTHORITY GATE PASS: work-package reference SECB-WP-FWK-062

while the pull request now reads `SECB-WP-FWK-066`. The green check evaluated an
identifier that no longer exists on that PR.

    head SHA unchanged  ≠  all reviewed inputs unchanged

PR metadata is not decoration. It supplies Gate 1's work-package ID, the budget
declaration, and — under squash merge — the commit subject that lands on `main`.

**Why a re-run cannot repair a stale check.** Re-running a workflow replays the
*original event payload*, so a re-run of #122's job would read `FWK-062` again and pass
again. Only an event carrying current metadata produces a current evaluation, which is
why `.github/workflows/ci.yml` now lists `edited` in its trigger types. The same
mechanism is why the budget discipline is *patch the body, then push*, never the
reverse.

Two modes, because the two halves happen at different times:

    emit      in CI, record what this run evaluated, so readback is possible
    --verify  at the merge decision, compare a recorded binding against live state

`CHECK_CURRENT` cannot be self-enforced by the run that produces it: within one run the
checked values and the current values are identical by construction. The verification is
necessarily external, and this script's emit half exists to make it possible at all.

Contract:

    GITHUB_EVENT_NAME  the triggering event      (refused unless pull_request)
    PR_TITLE      pull request title            (required)
    PR_BODY       pull request body             (optional; empty is legitimate)
    HEAD_SHA      pull request head SHA         (required)
    BASE_SHA      pull request base SHA         (required)
    MERGE_METHOD  merge method                  (default SQUASH)
    ENVELOPE      delegation envelope path      (default config/delegation_envelope.json)

Exit codes:

    0  binding emitted, or verification passed

Eligibility is not consumption. `eligible_for_normative_consumption: true` says this
record has the properties a consumer would require; it does not say a consumer read it,
and the producer is not entitled to claim the stages that belong to one.
    2  fail-closed: required input missing, or a `CHECK_CURRENT` term mismatched

Attacker-controlled text arrives through the environment, never through shell
interpolation (`NFR-16`).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# Reused rather than reimplemented: `load_prefix` carries six fail-closed paths
# (absent file, invalid JSON, absent project block, empty prefix, non-string prefix,
# regex metacharacters). A second copy of that logic would be a second thing to get
# wrong, and the two would drift.
from check_work_package_ref import (  # noqa: E402
    DEFAULT_ENVELOPE,
    find_reference,
    load_prefix,
)

OK = 0
FAIL = 2


class UnsupportedSubject(ValueError):
    """The event supplies a subject this schema cannot describe."""


class InvalidActionsContext(ValueError):
    """A run claims an Actions context it cannot substantiate."""


# Where this record sits in the evidence lifecycle, and where it does not. Each stage
# is a separate fact: none of them implies the next, and a producer cannot certify the
# stages that belong to a consumer.
#
#   GENERATED → CONTEXT_VALIDATED → PERSISTED → ADDRESSABLE
#             → INTEGRITY_BOUND → CONSUMER_VERIFIED → ENFORCEMENT_APPLIED
EVIDENCE_LIFECYCLE = {
    "reached": ["GENERATED", "CONTEXT_VALIDATED"],
    "not_reached": {
        "PERSISTED": "emitted to a step log; no structured record is stored",
        "ADDRESSABLE": "no stable receipt URI exists",
        "INTEGRITY_BOUND": "a digest is not a verified signer; nothing is attested",
        "CONSUMER_VERIFIED": "no consumer reads this record",
        "ENFORCEMENT_APPLIED": "no merge is denied on its absence or failure",
    },
    "producer_may_not_certify": [
        "CONSUMER_VERIFIED", "ENFORCEMENT_APPLIED",
    ],
}

LOCAL_DIAGNOSTIC = "LOCAL_DIAGNOSTIC"
EVENT_BOUND = "GITHUB_ACTIONS_EVENT_BOUND"
INVALID_CONTEXT = "INVALID_ACTIONS_CONTEXT"

# Any one of these present means the run is claiming to be in Actions. Claiming it
# obliges the full set: a partial context is refused rather than downgraded, because
# downgrading would let a caller obtain a diagnostic record while looking event-bound.
ACTIONS_VARS = ("GITHUB_ACTIONS", "GITHUB_EVENT_NAME", "GITHUB_EVENT_PATH")


# This schema describes exactly one subject: a single pull request, with one head, one
# base, one title and one budget declaration. A merge group is a different subject --
# an ordered set of pull requests plus a synthesized queue head -- and the fields below
# cannot carry it. Widening them to accept a list would give one schema two meanings.
SUBJECT_KIND = "PULL_REQUEST"
SUPPORTED_EVENT = "pull_request"

BUDGET_LINE = re.compile(r"^BUDGET:.*$", re.M)


def digest(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalized_subject(title: str) -> str:
    """The squash commit subject this title would produce.

    Recorded because under squash merge the PR title *becomes the commit message on
    `main`* — a claim that outlives the pull request. GitHub appends ` (#N)`; the
    number is not known to the gate, so only the normalized title is bound.
    """
    return " ".join(title.split())


def execution_context(env: dict[str, str], title: str, body: str,
                      head_sha: str, base_sha: str) -> dict:
    """Classify the run, and decide whether its output may be consumed as evidence.

    `GITHUB_ACTIONS`, `GITHUB_EVENT_NAME` and `GITHUB_EVENT_PATH` are default runner
    variables that a workflow's `env:` cannot override. That is **runner provenance, not
    cryptographic attestation** — anyone with shell access can set them — so the payload
    is re-read and compared against the values being bound rather than trusted.
    """
    claimed = [v for v in ACTIONS_VARS if env.get(v, "").strip()]
    if not claimed:
        return {
            "mode": LOCAL_DIAGNOSTIC,
            "event_payload_digest": None,
            "event_payload_consistent": None,
            "eligible_for_normative_consumption": False,
        }

    missing = [v for v in ACTIONS_VARS if not env.get(v, "").strip()]
    if missing:
        raise InvalidActionsContext(
            f"{INVALID_CONTEXT}: {claimed} present but {missing} absent. A partial "
            "Actions context is refused, not downgraded to a diagnostic record"
        )
    if env["GITHUB_ACTIONS"].strip().lower() != "true":
        raise InvalidActionsContext(f"{INVALID_CONTEXT}: GITHUB_ACTIONS is not true")

    try:
        raw = Path(env["GITHUB_EVENT_PATH"]).read_bytes()
        payload = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise InvalidActionsContext(
            f"{INVALID_CONTEXT}: event payload unreadable or unparseable ({exc})"
        ) from exc

    pull_request = payload.get("pull_request")
    if not isinstance(pull_request, dict):
        raise InvalidActionsContext(
            f"{INVALID_CONTEXT}: payload carries no pull_request object"
        )

    observed = {
        "title": pull_request.get("title"),
        "body": pull_request.get("body") or "",
        "head": (pull_request.get("head") or {}).get("sha"),
        "base": (pull_request.get("base") or {}).get("sha"),
    }
    bound = {"title": title, "body": body, "head": head_sha, "base": base_sha}
    mismatched = [k for k in bound if observed[k] != bound[k]]
    if mismatched:
        raise InvalidActionsContext(
            f"{INVALID_CONTEXT}: {mismatched} differ between the event payload and the "
            "values being bound. The emitter would otherwise stamp inputs the event did "
            "not supply"
        )

    return {
        "mode": EVENT_BOUND,
        "event_payload_digest": digest(raw.decode("utf-8", "replace")),
        "event_payload_consistent": True,
        "eligible_for_normative_consumption": True,
    }


def build_binding(env: dict[str, str]) -> dict:
    missing = [k for k in ("PR_TITLE", "HEAD_SHA", "BASE_SHA") if not env.get(k, "").strip()]
    if missing:
        raise ValueError(f"required input absent: {', '.join(missing)}")

    # Forward guard against schema laundering: PR-shaped inputs assembled under a
    # different event must not receive this schema's stamp. A merge-group runner could
    # populate PR_TITLE and HEAD_SHA from a queue entry and obtain a binding that claims
    # provenance the event never supplied. Emitting nothing is correct; the group has its
    # own envelope (`secb.merge-group-input-binding/v1`, tracked on #118).
    observed_event = env.get("GITHUB_EVENT_NAME", "").strip()
    if observed_event and observed_event != SUPPORTED_EVENT:
        raise UnsupportedSubject(
            f"UNSUPPORTED_SUBJECT: this schema binds a {SUBJECT_KIND} under "
            f"{SUPPORTED_EVENT!r}; observed event {observed_event!r}"
        )

    title = env["PR_TITLE"]
    body = env.get("PR_BODY", "")

    prefix = load_prefix(env.get("ENVELOPE", DEFAULT_ENVELOPE))
    work_package_id = find_reference(f"{title}\n{body}", prefix)

    budget_match = BUDGET_LINE.search(body)
    context = execution_context(env, title, body, env["HEAD_SHA"].strip(),
                                env["BASE_SHA"].strip())

    return {
        "schema": "secb.pr-input-binding/v1",
        "subject_kind": SUBJECT_KIND,
        "supported_event": SUPPORTED_EVENT,
        "merge_group_compatible": False,
        "observed_event": observed_event or "UNSET",
        "execution_context": context,
        "eligible_for_normative_consumption": context["eligible_for_normative_consumption"],
        "evidence_lifecycle": EVIDENCE_LIFECYCLE,
        "head_sha": env["HEAD_SHA"].strip(),
        "base_sha": env["BASE_SHA"].strip(),
        "title_digest": digest(title),
        "body_digest": digest(body),
        "work_package_id": work_package_id,
        "budget_digest": digest(budget_match.group(0)) if budget_match else None,
        "merge_method": env.get("MERGE_METHOD", "SQUASH"),
        "expected_commit_subject": normalized_subject(title),
        "not_proven": [
            "that the recorded values are still current — that is --verify's job",
            "that any consumer requires this binding",
            "anything about a merge group",
            "that this record has been consumed: eligibility is a property of the record, "
            "consumption is an act of a consumer, and no consumer exists",
            "that a LOCAL_DIAGNOSTIC record is evidence — it carries the same schema name "
            "and is not eligible; a normative consumer must reject it",
            "that runner variables are attestation; they are provenance, which is why the "
            "event payload is re-read and compared",
        ],
    }


# `base_sha` is bound because retargeting a pull request changes the diff under review
# without touching the head. A binding over the head alone would call that unchanged.
COMPARED = (
    "head_sha",
    "base_sha",
    "title_digest",
    "body_digest",
    "budget_digest",
    "work_package_id",
)


def verify(recorded: dict, current: dict) -> list[str]:
    """Return the names of mismatching `CHECK_CURRENT` terms — empty means current."""
    return [term for term in COMPARED if recorded.get(term) != current.get(term)]


def main(argv: list[str]) -> int:
    try:
        current = build_binding(dict(os.environ))
    except InvalidActionsContext as exc:
        print(f"BINDING REFUSED: {exc}", file=sys.stderr)
        return FAIL
    except UnsupportedSubject as exc:
        print(f"BINDING REFUSED: {exc}", file=sys.stderr)
        return FAIL
    except ValueError as exc:
        print(f"BINDING FAIL (closed): {exc}", file=sys.stderr)
        return FAIL

    if "--verify" in argv:
        index = argv.index("--verify")
        if index + 1 >= len(argv):
            print("BINDING FAIL (closed): --verify needs a recorded binding path", file=sys.stderr)
            return FAIL
        try:
            recorded = json.loads(Path(argv[index + 1]).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"BINDING FAIL (closed): recorded binding unreadable ({exc})", file=sys.stderr)
            return FAIL

        if not recorded.get("eligible_for_normative_consumption"):
            print(
                "EVIDENCE_NOT_CONSUMABLE: the recorded binding was produced in "
                f"{recorded.get('execution_context', {}).get('mode', 'an unknown mode')} "
                "and carries no event binding. Matching the schema name is not enough.",
                file=sys.stderr,
            )
            return FAIL

        mismatched = verify(recorded, current)
        if mismatched:
            print(
                "CHECK_CURRENT FAIL: " + ", ".join(mismatched) + " changed since the check ran. "
                "The prior result evaluated different inputs and does not carry forward.",
                file=sys.stderr,
            )
            return FAIL
        print("CHECK_CURRENT PASS: every bound input matches the live pull request")
        return OK

    print(json.dumps(current, indent=2, sort_keys=True))
    return OK


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
