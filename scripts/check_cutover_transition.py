#!/usr/bin/env python3
"""Validate a proposed public-cutover transition. Fail-closed.

`SECB-WP-FWK-080` (issue #143).

    BUSINESS_DECISION_TO_DISCLOSE
      ≠ CAPABILITY_AVAILABLE
      ≠ CONTROL_CONFIGURED
      ≠ CONTROL_VERIFIED
      ≠ CONTROL_ENFORCED

Five different facts that a single "we went public" would fuse. This validator refuses a
transition whose evidence is absent, and it **performs no external effect**: it does not
transfer a repository, change visibility, create a ruleset, enable a queue, or attest
anything. It reads a manifest and answers one question — may this transition be recorded.

Two properties it deliberately does not have:

* **It cannot approve disclosure.** `DISCLOSURE_APPROVED` requires a human decision. An
  executor recording it would be manufacturing the authority the gate exists to require,
  so the transition demands an approval reference the manifest cannot self-supply.
* **It cannot observe capability.** Every `live_readback` is `NOT_OBSERVED` because no
  external call is permitted at this state. Absent observation is *unmeasured*, never
  "absent" — and `configured_intent` never satisfies a `verified` requirement.

Contract:

    argv[1]        target lifecycle state
    MANIFEST       manifest path (default config/public_cutover_state.json)
    APPROVAL_REF   human approval reference, required for DISCLOSURE_APPROVED

Exit codes:

    0  the transition is permitted
    2  refused — unknown state, out of order, or evidence missing
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

OK = 0
FAIL = 2

DEFAULT_MANIFEST = "config/public_cutover_state.json"

# Ordered. A transition may advance exactly one step; nothing may be skipped, because
# each state's evidence is the next one's precondition.
ORDER = [
    "DISCLOSURE_UNAPPROVED",
    "DISCLOSURE_APPROVED",
    "ORG_TRANSFERRED",
    "VISIBILITY_PUBLIC",
    "CAPABILITIES_OBSERVED",
    "CONTROLS_CONFIGURED",
    "CONTROLS_VERIFIED",
    "SELECTIVELY_ACTIVATED",
]

CAPABILITIES = ("rulesets", "merge_queue", "artifact_attestations", "archival")


class Refused(ValueError):
    """The transition is not evidenced."""


def load(path: str) -> dict:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Refused(f"manifest unreadable or unparseable at {path} ({exc})") from exc


def check(manifest: dict, target: str, env: dict[str, str]) -> None:
    current = manifest.get("lifecycle_state")
    if current not in ORDER:
        raise Refused(f"current lifecycle_state {current!r} is not a known state")
    if target not in ORDER:
        raise Refused(f"target {target!r} is not a known state")

    here, there = ORDER.index(current), ORDER.index(target)
    if there <= here:
        raise Refused(
            f"{current} -> {target} does not advance. Reversing a cutover state does not "
            "reverse its effect: disclosure is not undone by re-recording an earlier state"
        )
    if there - here > 1:
        raise Refused(
            f"{current} -> {target} skips {ORDER[here + 1:there]}. Each state's evidence "
            "is the next one's precondition"
        )

    # The one transition an executor may never self-authorize.
    if target == "DISCLOSURE_APPROVED":
        approval = env.get("APPROVAL_REF", "").strip()
        if not approval:
            raise Refused(
                "DISCLOSURE_APPROVED requires APPROVAL_REF, a human decision reference. "
                "Making the repository public exposes Actions history and logs, and "
                "secrecy is not restorable by reverting visibility"
            )
        prerequisite = manifest.get("irreversibility", {}).get("prerequisite", "")
        if "#115" not in prerequisite:
            raise Refused(
                "the manifest must name the credential-cutover prerequisite (#115); a "
                "secret still live when logs become public is disclosed, not rotated"
            )

    if target == "CAPABILITIES_OBSERVED":
        unobserved = [
            name for name in CAPABILITIES
            if manifest["capabilities"][name]["live_readback"]["status"] == "NOT_OBSERVED"
        ]
        if unobserved:
            raise Refused(
                f"{unobserved} still report live_readback NOT_OBSERVED. A capability that "
                "has not been read is unmeasured, not available and not absent"
            )

    if target == "CONTROLS_VERIFIED":
        # Per capability, and never in aggregate: they are configured through different
        # surfaces and fail independently, so one passing cannot raise another.
        for name in CAPABILITIES:
            capability = manifest["capabilities"][name]
            if not capability.get("verified"):
                raise Refused(
                    f"{name} is not verified. Configured intent is not verification, and "
                    "no capability inherits another's result"
                )

    if target == "SELECTIVELY_ACTIVATED":
        unenforced = [n for n in CAPABILITIES if not manifest["capabilities"][n].get("enforced")]
        if unenforced == list(CAPABILITIES):
            raise Refused(
                "no capability is enforced; there is nothing to activate selectively"
            )

    # Producer-authored fields may never claim a consumer's act.
    forbidden = manifest.get("evidence_lifecycle", {}).get("producer_may_not_certify", [])
    recorded = manifest.get("transition_evidence", {})
    overreach = [stage for stage in forbidden if stage in recorded]
    if overreach:
        raise Refused(
            f"{overreach} appear in producer-authored transition_evidence. A producer "
            "cannot certify that a consumer verified or that enforcement was applied"
        )


def main(argv: list[str]) -> int:
    if len(argv) < 1:
        print("REFUSED: no target state given", file=sys.stderr)
        return FAIL
    env = dict(os.environ)
    try:
        manifest = load(env.get("MANIFEST", DEFAULT_MANIFEST))
        check(manifest, argv[0], env)
    except Refused as exc:
        print(f"CUTOVER TRANSITION REFUSED (closed): {exc}", file=sys.stderr)
        return FAIL
    except (KeyError, TypeError) as exc:
        print(f"CUTOVER TRANSITION REFUSED (closed): malformed manifest ({exc})", file=sys.stderr)
        return FAIL
    print(f"CUTOVER TRANSITION PERMITTED: {manifest['lifecycle_state']} -> {argv[0]}")
    return OK


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
