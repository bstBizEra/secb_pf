#!/usr/bin/env python3
"""Evaluate a request against a declared policy bundle (FWK-105, P0 item 8).

THIS IS NOT OPA, AND SAYS SO. The scope names Open Policy Agent for repository-independent
decisions. NFR-12 keeps gates stdlib-only and CI installs only pytest, so the options were: vendor a
Rego interpreter (a large hand-written language implementation with no upside and every downside of
hand-rolled parsing), shell to an OPA binary (breaks hermeticity and adds an unpinned dependency to
every gate), or keep what policy-as-code is actually FOR and drop the language.

    POLICY_INTERFACE_PRESERVED != OPA_ADOPTED

What is load-bearing is preserved: the decision is computed from declared rules by a component the
requester does not control, and it returns the typed decision object the scope specifies --
`decision`, `reason_codes`, `required_evidence`, `obligations`, `valid_until`, `policy_digest`.
Adopting real OPA later changes the engine, not the interface.

DEFAULT DENY. A request matching no rule is denied. An unmatched request is an unclassified one, and
the point of an external decision is that silence is not consent.

DENY WINS. When rules disagree, deny beats conditional beats allow. A conflict resolved in favour of
permission would make adding a permissive rule a way to defeat every restrictive one.

THE REQUEST CANNOT CARRY THE POLICY. Rules come only from the bundle on disk, and the bundle's digest
is reported in every decision. A requester that could supply rules, or name its own reason codes,
would be deciding its own case -- which is the whole thing this component exists to prevent.

    REQUESTER_SUPPLIED_FACTS != REQUESTER_SUPPLIED_RULES
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

OK = 0
FAIL = 2

BUNDLE_SCHEMA = "secb.policy-bundle/v1"
EFFECTS = ("allow", "conditional", "deny")
PRECEDENCE = {"deny": 0, "conditional": 1, "allow": 2}
DECISION_TTL_MINUTES = 60


class Refused(ValueError):
    """The decision cannot be computed as requested."""


def canonical(payload: object) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def load_bundle(path: Path) -> tuple[dict, str]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise Refused(
            f"the policy bundle is unreadable at {path} ({exc}). Without rules there is no "
            "decision to compute, and defaulting to allow would make an unreadable policy the "
            "most permissive one"
        ) from exc
    try:
        bundle = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise Refused(f"the policy bundle is not parseable JSON ({exc})") from exc
    if bundle.get("schema") != BUNDLE_SCHEMA:
        raise Refused(f"bundle schema is {bundle.get('schema')!r}, expected {BUNDLE_SCHEMA!r}")
    rules = bundle.get("rules")
    if not rules:
        raise Refused("the bundle declares no rules; an empty policy decides nothing")
    seen = set()
    for rule in rules:
        for field in ("id", "effect", "operation", "when", "reason_codes"):
            if field not in rule:
                raise Refused(f"rule {rule.get('id', '?')!r} is missing {field!r}")
        if rule["effect"] not in EFFECTS:
            raise Refused(f"rule {rule['id']}: effect {rule['effect']!r} is not one of {EFFECTS}")
        if rule["id"] in seen:
            raise Refused(f"duplicate rule id {rule['id']!r}")
        seen.add(rule["id"])
        if rule["effect"] == "conditional" and not rule.get("obligations"):
            raise Refused(
                f"rule {rule['id']}: a conditional effect with no obligations is an allow that "
                "reads as a caveat"
            )
    digest = "sha256:" + hashlib.sha256(raw).hexdigest()
    return bundle, digest


def matches(rule: dict, facts: dict) -> bool:
    """Every declared condition must be present in the facts AND equal.

    An ABSENT fact does not match. A rule requiring `envelope_valid: true` must not fire because the
    requester omitted the field -- that would let a request earn a permission by saying less.
    """
    for key, expected in rule["when"].items():
        if key not in facts or facts[key] != expected:
            return False
    return True


def decide(bundle: dict, digest: str, request: dict, now: datetime) -> dict:
    operation = request.get("operation")
    if not operation:
        raise Refused("the request declares no operation")
    facts = request.get("facts")
    if facts is None:
        raise Refused(
            "the request declares no facts. An absent fact set is not an empty one, and every rule "
            "would vacuously fail to match into a default deny that hid a malformed request"
        )
    if not isinstance(facts, dict):
        raise Refused("facts must be an object")
    for forbidden in ("rules", "effect", "decision", "reason_codes", "policy_digest"):
        if forbidden in request:
            raise Refused(
                f"the request carries {forbidden!r}. A requester supplying rules or naming its own "
                "decision is deciding its own case -- REQUESTER_SUPPLIED_FACTS != "
                "REQUESTER_SUPPLIED_RULES"
            )

    applicable = [r for r in bundle["rules"]
                  if r["operation"] == operation and matches(r, facts)]
    if not applicable:
        return {
            "decision": "deny",
            "reason_codes": ["NO_MATCHING_RULE"],
            "matched_rules": [],
            "required_evidence": [],
            "obligations": [],
            "default_applied": True,
        }
    # Deny wins, then conditional. Resolving a conflict toward permission would make adding one
    # permissive rule a way to defeat every restrictive rule in the bundle.
    applicable.sort(key=lambda r: PRECEDENCE[r["effect"]])
    winner = applicable[0]["effect"]
    chosen = [r for r in applicable if r["effect"] == winner]
    return {
        "decision": winner,
        "reason_codes": sorted({c for r in chosen for c in r["reason_codes"]}),
        "matched_rules": sorted(r["id"] for r in chosen),
        "required_evidence": sorted({e for r in chosen for e in r.get("required_evidence", [])}),
        "obligations": sorted({o for r in chosen for o in r.get("obligations", [])}),
        "default_applied": False,
        "overridden_effects": sorted({r["effect"] for r in applicable} - {winner}),
    }


def main(argv: list[str]) -> int:
    env = dict(os.environ)
    request_path = env.get("REQUEST", "").strip()
    if not request_path:
        print("REFUSED (closed): REQUEST is required", file=sys.stderr)
        return FAIL
    root = Path(env.get("REPO_ROOT", ".")).resolve()
    bundle_path = root / env.get("POLICY_BUNDLE", "config/policies/core.policy.json")
    try:
        bundle, digest = load_bundle(bundle_path)
        request = json.loads(Path(request_path).read_text(encoding="utf-8"))
        now = datetime.now(timezone.utc)
        outcome = decide(bundle, digest, request, now)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"REFUSED (closed): request unreadable ({exc})", file=sys.stderr)
        return FAIL
    except Refused as exc:
        print(f"REFUSED (closed): {exc}", file=sys.stderr)
        return FAIL
    except (KeyError, TypeError, AttributeError) as exc:
        print(f"REFUSED (closed): malformed input ({exc!r})", file=sys.stderr)
        return FAIL

    print(json.dumps({
        "schema": "secb.policy-decision/v1",
        **outcome,
        "operation": request["operation"],
        "policy_version": bundle.get("version"),
        "policy_digest": digest,
        "evaluated_at": now.isoformat(),
        "valid_until": (now + timedelta(minutes=DECISION_TTL_MINUTES)).isoformat(),
        "engine": "secb-stdlib-policy/v1 (NOT OPA; the decision interface is preserved, the "
                  "language is not)",
        "not_proven": [
            "that the facts are TRUE; the evaluator decides on supplied facts and verifies none",
            "that an allow is an authorisation to act; obligations may remain unmet",
            "that this decision survives a bundle change -- policy_digest is what binds it",
        ],
        "confers_merge_authority": False,
    }, indent=2, sort_keys=True))
    return OK if outcome["decision"] in ("allow", "conditional") else FAIL


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
