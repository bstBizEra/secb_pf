"""SecB v1.5.1 sandbox reference router.

This module is deliberately side-effect free.  It proves control semantics for
FIT-101--120; it is not a production router or an authority service.

Provenance: copied from the sealed v1.5 baseline
(docs/06-agent-orchestration/skill-router/"SECB-WP-ENGLOOP-MVP-001 -- Sandbox
Evidence"/router.py, SHA-256 4d1dab78...) certified SANDBOX_TESTED under
review REV-SECB-ENGLOOP-MVP-001-20260810.  The sealed baseline must never be
edited -- the review voids on any change -- so fixes land here.

v1.5.1 (SECB-WP-FWK-010): fixes review finding F1 -- registry_hash now pins
every selection-relevant field.  In v1.5 the hash omitted validation,
qualification, cost and expires_at, all of which feed the selection score, so
a registry change in those fields left existing routes valid.  Routing
invariant 4 requires the complete pinned state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from itertools import combinations
import json
from typing import Iterable


RISK = {"R0": 0, "R1": 1, "R2": 2, "R3": 3, "R4": 4}
HIGH_IMPACT_EFFECTS = {
    "delete", "publish", "deploy", "external_message", "financial",
    "credential_access", "permission_change", "sensitive_disclosure",
}


class RouteHeld(RuntimeError):
    """A fail-closed routing or authorization decision."""


@dataclass(frozen=True)
class Skill:
    skill_id: str
    version: str
    digest: str
    capabilities: frozenset[str]
    status: str = "QUALIFIED"
    risk_ceiling: str = "R1"
    prerequisites: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()
    effects: frozenset[str] = frozenset()
    validation: frozenset[str] = frozenset({"schema"})
    qualification: int = 1
    cost: int = 1
    expires_at: str = "2099-01-01T00:00:00+00:00"

    def qualified(self, now: datetime) -> bool:
        return self.status == "QUALIFIED" and datetime.fromisoformat(self.expires_at) > now


@dataclass
class RoutePlan:
    route_id: str
    request_hash: str
    registry_hash: str
    policy_hash: str
    selected: list[Skill]
    rejected: dict[str, str]
    order: list[str]
    version: int = 1
    status: str = "PLANNED"
    invocation_warrants: set[str] = field(default_factory=set)
    effect_warrants: set[tuple[str, str]] = field(default_factory=set)


def canonical_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(raw.encode()).hexdigest()


def registry_hash(skills: Iterable[Skill]) -> str:
    rows = [
        {
            "id": s.skill_id, "version": s.version, "digest": s.digest,
            "status": s.status, "capabilities": sorted(s.capabilities),
            "risk": s.risk_ceiling, "prerequisites": list(s.prerequisites),
            "conflicts": list(s.conflicts), "effects": sorted(s.effects),
            # F1 fix (v1.5.1): these four feed the selection score, so a
            # change to any of them must invalidate previously planned routes.
            "validation": sorted(s.validation), "qualification": s.qualification,
            "cost": s.cost, "expires_at": s.expires_at,
        }
        for s in sorted(skills, key=lambda item: (item.skill_id, item.version))
    ]
    return canonical_hash(rows)


def _expand_prerequisites(
    chosen: set[str],
    eligible_by_id: dict[str, Skill],
    all_by_id: dict[str, Skill] | None = None,
) -> set[str]:
    """Expand prerequisites, walking ONLY eligible skills.

    Eligibility (status, expiry, risk ceiling, permitted effects) is enforced on
    the top-level candidate loop. Expanding against the full registry would carry
    a skill into the plan through the transitive edge without any of those checks
    -- a REVOKED, expired skill reached as a prerequisite would be selected and
    could then obtain both an invocation and an effect warrant. A prerequisite
    that is not eligible makes the combination non-viable; the caller skips it.
    """
    expanded = set(chosen)
    pending = list(chosen)
    while pending:
        current = eligible_by_id[pending.pop()]
        for required in current.prerequisites:
            if required not in eligible_by_id:
                if all_by_id is not None and required in all_by_id:
                    raise RouteHeld(f"prerequisite not eligible: {required}")
                raise RouteHeld(f"missing prerequisite: {required}")
            if required not in expanded:
                expanded.add(required)
                pending.append(required)
    return expanded


def _topological_order(ids: set[str], by_id: dict[str, Skill]) -> list[str]:
    visiting: set[str] = set()
    visited: set[str] = set()
    result: list[str] = []

    def visit(skill_id: str) -> None:
        if skill_id in visiting:
            raise RouteHeld("cyclic prerequisite graph")
        if skill_id in visited:
            return
        visiting.add(skill_id)
        for dependency in sorted(by_id[skill_id].prerequisites):
            if dependency in ids:
                visit(dependency)
        visiting.remove(skill_id)
        visited.add(skill_id)
        result.append(skill_id)

    for skill_id in sorted(ids):
        visit(skill_id)
    return result


def _eligible(skill: Skill, request: dict, now: datetime) -> tuple[bool, str]:
    if not skill.qualified(now):
        return False, "NOT_QUALIFIED"
    if RISK[request["risk_tier"]] > RISK[skill.risk_ceiling]:
        return False, "RISK_CEILING"
    if skill.effects - set(request.get("permitted_effects", [])):
        return False, "EFFECT_NOT_PERMITTED"
    return True, "ELIGIBLE"


def route(request: dict, skills: list[Skill], policy_hash: str, now: datetime | None = None) -> RoutePlan:
    now = now or datetime.now(timezone.utc)
    request_hash = canonical_hash(request)
    by_id = {skill.skill_id: skill for skill in skills}
    rejected: dict[str, str] = {}
    eligible: list[Skill] = []
    for skill in skills:
        ok, reason = _eligible(skill, request, now)
        if ok:
            eligible.append(skill)
        else:
            rejected[skill.skill_id] = reason

    explicit = tuple(request.get("explicit_skill_priorities", []))
    eligible_by_id = {skill.skill_id: skill for skill in eligible}
    eligible_ids = set(eligible_by_id)
    missing_named = [skill_id for skill_id in explicit if skill_id not in eligible_ids]
    if missing_named:
        raise RouteHeld(f"named skill unavailable or unqualified: {missing_named[0]}")

    required = set(request["required_capabilities"])
    candidates: list[tuple[tuple, set[str]]] = []
    for size in range(1, len(eligible) + 1):
        for combo in combinations(eligible, size):
            combo_ids = {s.skill_id for s in combo}
            if explicit and not set(explicit) <= combo_ids:
                continue
            try:
                ids = _expand_prerequisites(combo_ids, eligible_by_id, by_id)
            except RouteHeld:
                continue
            chosen = [by_id[i] for i in ids]
            if any(set(s.conflicts) & ids for s in chosen):
                continue
            coverage = set().union(*(s.capabilities for s in chosen))
            if not required <= coverage:
                continue
            names = tuple(sorted(ids))
            score = (
                len(ids),
                sum(max(0, RISK[request["risk_tier"]] - RISK[s.risk_ceiling]) for s in chosen),
                -sum(s.qualification for s in chosen),
                -len(set().union(*(s.validation for s in chosen))),
                sum(bool(s.effects) for s in chosen), sum(s.cost for s in chosen), names,
            )
            candidates.append((score, ids))
        if candidates:
            break
    if not candidates:
        raise RouteHeld("mandatory capability coverage unavailable")
    ids = min(candidates, key=lambda row: row[0])[1]
    order = _topological_order(ids, by_id)
    for skill in eligible:
        if skill.skill_id not in ids:
            rejected[skill.skill_id] = "NOT_MINIMUM_SUFFICIENT"
    selected = [by_id[i] for i in order]
    return RoutePlan(
        route_id="route-" + request_hash[:12], request_hash=request_hash,
        registry_hash=registry_hash(skills), policy_hash=policy_hash,
        selected=selected, rejected=rejected, order=order,
    )


def authorize_invocation(plan: RoutePlan, skill_id: str, *, request: dict,
                         skills: list[Skill], policy_hash: str) -> str:
    if plan.request_hash != canonical_hash(request):
        raise RouteHeld("request changed")
    if plan.registry_hash != registry_hash(skills):
        raise RouteHeld("registry or instruction digest changed")
    if plan.policy_hash != policy_hash:
        raise RouteHeld("policy changed")
    if skill_id not in plan.order:
        raise RouteHeld("skill not selected")
    warrant = canonical_hash([plan.route_id, plan.version, skill_id, "invoke"])
    plan.invocation_warrants.add(skill_id)
    plan.status = "AUTHORIZED"
    return warrant


def authorize_effect(plan: RoutePlan, skill_id: str, effect: str, *, confirmation: bool) -> str:
    if skill_id not in plan.invocation_warrants:
        raise RouteHeld("invocation not authorized")
    skill = next(s for s in plan.selected if s.skill_id == skill_id)
    if effect not in skill.effects:
        raise RouteHeld("effect outside skill contract")
    if effect in HIGH_IMPACT_EFFECTS and not confirmation:
        raise RouteHeld("separate effect confirmation required")
    plan.effect_warrants.add((skill_id, effect))
    return canonical_hash([plan.route_id, plan.version, skill_id, effect, "effect"])


def validate_handoff(handoff: dict, expected_schema: str, allowed_classifications: set[str]) -> None:
    if handoff.get("schema_id") != expected_schema:
        raise RouteHeld("handoff schema mismatch")
    if handoff.get("validation_status") != "PASS":
        raise RouteHeld("handoff validation failed")
    if handoff.get("data_classification") not in allowed_classifications:
        raise RouteHeld("handoff data classification prohibited")
    if "untrusted_instruction" in handoff.get("taint", []):
        raise RouteHeld("untrusted output cannot become instruction")


def repair(acceptance_hash: str, proposed_acceptance_hash: str, attempts: int, limit: int) -> str:
    if proposed_acceptance_hash != acceptance_hash:
        raise RouteHeld("acceptance criteria weakening prohibited")
    if attempts >= limit:
        raise RouteHeld("repair budget exhausted")
    return "REPAIRING"


def reconcile(status: str, readback_status: str | None) -> str:
    if status != "OUTCOME_UNKNOWN":
        return status
    if readback_status not in {"SUCCEEDED", "FAILED"}:
        raise RouteHeld("outcome must be reconciled before retry")
    return readback_status


def fallback(original_controls: dict, fallback_controls: dict) -> int:
    for floor in ("risk", "authority", "validation", "data"):
        if fallback_controls[floor] < original_controls[floor]:
            raise RouteHeld(f"fallback weakens {floor} floor")
    return 2  # a fallback creates a new route version


def budget_gate(consumed: int, limit: int, containment: bool = False) -> str:
    if consumed < limit:
        return "CONTINUE"
    return "CONTAINMENT_ONLY" if containment else "HELD"


def append_event(chain: list[dict], event_type: str, payload: dict) -> dict:
    previous = chain[-1]["event_hash"] if chain else "GENESIS"
    event = {
        "sequence": len(chain) + 1, "event_type": event_type,
        "payload_digest": canonical_hash(payload), "previous_event_hash": previous,
    }
    event["event_hash"] = canonical_hash(event)
    chain.append(event)
    return event


def verify_event_chain(chain: list[dict]) -> bool:
    previous = "GENESIS"
    for position, event in enumerate(chain, 1):
        body = {k: v for k, v in event.items() if k != "event_hash"}
        if event["sequence"] != position or event["previous_event_hash"] != previous:
            return False
        if canonical_hash(body) != event["event_hash"]:
            return False
        previous = event["event_hash"]
    return True


def apply_learning(registry: list[Skill], observation: dict) -> str:
    del registry, observation
    return "CANDIDATE_OBSERVATION"  # never mutates/adopts registry entries
