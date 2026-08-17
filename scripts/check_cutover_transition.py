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

* **It cannot authorize disclosure by itself.** `DISCLOSURE_AUTHORIZED` requires an
  **Agentic Decision Receipt** — a snapshot-bound record from seven separated roles. The
  authority is agentic, not per-instance human approval; what an executor may never do is
  write its own authorization. A free-form `APPROVAL_REF` string was the previous gate and
  was no gate at all: the executor composes that text.
* **Distinct `actor_id` strings are not identity.** A single account can write any string
  into a receipt, exactly as one session can type any role banner. While `C-7` leaves
  identity separation unproven, the transition is refused with
  `IDENTITY_SEPARATION_UNPROVEN` — which is a missing substrate, not a reversion to human
  approval.
* **It cannot observe capability.** Every `live_readback` is `NOT_OBSERVED` because no
  external call is permitted at this state. Absent observation is *unmeasured*, never
  "absent" — and `configured_intent` never satisfies a `verified` requirement.

Contract:

    argv[1]           target lifecycle state
    MANIFEST          manifest path (default config/public_cutover_state.json)
    DECISION_RECEIPT  Agentic Decision Receipt path, required for DISCLOSURE_AUTHORIZED
    OBSERVED_SNAPSHOT observed-snapshot JSON path, required to detect a STALE receipt

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
    "DISCLOSURE_AUTHORIZED",
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


RECEIPT_SCHEMA = "secb.agentic-decision-receipt/v1"

# Agent Identity Substrate, lowest to highest (`SECB-WP-FWK-081`, issue #145).
#
#     ROLE_LABEL ≠ PLATFORM_PRINCIPAL ≠ CREDENTIAL_CUSTODY_DOMAIN ≠ DECISION_INDEPENDENCE
#
# A level, not a boolean. `identity_separation: PROVEN` was one bit that any edit could
# flip and that could not express a partial substrate. AIS1–AIS3 are real progress and
# each is insufficient for an irreversible effect on its own.
AIS_LADDER = [
    "AIS0_SELF_ASSERTED",
    "AIS1_WORKFLOW_BOUND",
    "AIS2_PLATFORM_PRINCIPALS",
    "AIS3_CUSTODY_SEPARATED",
    "AIS4_INDEPENDENT_DOMAINS",
]


def check_agentic_authorization(manifest: dict, env: dict[str, str]) -> None:
    """Verify an Agentic Decision Receipt, or refuse.

    Order matters: identity separation is checked **first**. Every check after it operates
    on self-asserted content, so passing them while the substrate is unproven would report
    a verified decision built out of text one actor wrote.
    """
    authorization = manifest["agentic_authorization"]

    separation = authorization["identity_separation"]
    observed = separation.get("observed_level")
    required = separation.get("required_level")
    for label, level in (("observed_level", observed), ("required_level", required)):
        if level not in AIS_LADDER:
            raise Refused(f"{label} {level!r} is not a known AIS level")
    if AIS_LADDER.index(observed) < AIS_LADDER.index(required):
        shortfall = AIS_LADDER[AIS_LADDER.index(observed) + 1:AIS_LADDER.index(required) + 1]
        raise Refused(
            f"IDENTITY_SEPARATION_INSUFFICIENT ({separation['condition']}): observed "
            f"{observed}, required {required}; missing {shortfall}. At AIS0 the roles are "
            "actor strings inside the artifact being authorized -- one account writes any "
            "of them, exactly as one session types any role banner. Public disclosure is "
            "irreversible, so partial substrate does not carry it. The authority model "
            "stays agentic; the identity substrate is what is missing"
        )

    receipt_path = env.get("DECISION_RECEIPT", "").strip()
    if not receipt_path:
        raise Refused(
            "DISCLOSURE_AUTHORIZED requires DECISION_RECEIPT. A free-form approval string "
            "is not a gate -- the executor composes it"
        )
    try:
        receipt = json.loads(Path(receipt_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Refused(f"decision receipt unreadable or unparseable ({exc})") from exc

    if receipt.get("schema") != RECEIPT_SCHEMA:
        raise Refused(f"receipt schema {receipt.get('schema')!r} is not {RECEIPT_SCHEMA}")

    ballot_roles = authorization["ballot_roles"]
    effect_roles = authorization["effect_roles"]
    roles = receipt.get("roles", {})
    missing = [r for r in ballot_roles + effect_roles if r not in roles]
    if missing:
        raise Refused(f"receipt omits roles {missing}")

    actors = {}
    for role in ballot_roles + effect_roles:
        actor = (roles[role] or {}).get("actor_id", "").strip()
        if not actor:
            raise Refused(f"role {role} names no actor_id")
        actors.setdefault(actor, []).append(role)
    shared = {a: r for a, r in actors.items() if len(r) > 1}
    if shared:
        raise Refused(
            f"one actor holds several roles: {shared}. Deciding and executing must not share "
            "a failure mode, and an executor may not certify its own effect"
        )

    for role in ballot_roles:
        if (roles[role] or {}).get("decision") != "AUTHORIZE":
            raise Refused(f"{role} did not record AUTHORIZE")

    bound = receipt.get("snapshot", {})
    fields = authorization["snapshot_binding"]["fields"]
    absent = [f for f in fields if not bound.get(f)]
    if absent:
        raise Refused(f"receipt binds no {absent}; a decision is about a state, not a repository")

    observed_path = env.get("OBSERVED_SNAPSHOT", "").strip()
    if not observed_path:
        raise Refused(
            "OBSERVED_SNAPSHOT is required: without an observation there is no way to tell "
            "a current receipt from a stale one, and this validator performs no external call"
        )
    try:
        observed = json.loads(Path(observed_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Refused(f"observed snapshot unreadable or unparseable ({exc})") from exc

    drifted = [f for f in fields if bound.get(f) != observed.get(f)]
    if drifted:
        raise Refused(
            f"RECEIPT_STALE: {drifted} changed since the decision was recorded"
        )

    if bound["credential_cutover_result"] != "PASSED":
        raise Refused(
            "credential cutover (#115) has not passed; a secret still live when logs become "
            "public is disclosed, not rotated"
        )


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
    if target == "DISCLOSURE_AUTHORIZED":
        check_agentic_authorization(manifest, env)

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
