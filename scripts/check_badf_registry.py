#!/usr/bin/env python3
"""BADF registry and admission validator (SECB-WP-FWK-136).

Fail-closed. Exit 0 only when every declared posture holds and every admission
record is internally consistent with the lifecycle state it claims.

Implements docs/00-governance/BADF_SKILL_ADMISSION_STANDARD.md, bound to blob
b2fcad267a09bc6612ac508272165476daa2c109. If that document changes, this
validator's claim to implement it is stale and must be re-verified.

Deliberately NOT a second validator: it reads the same fail-closed exit
convention as check_budget.py and check_work_package_ref.py (0 pass, 2 refuse),
and does not re-implement authority classification, budget accounting, or
evidence binding, which already exist.

Modes (MODE env or argv[1]):
  registries  posture + shape of badf/*.json
  admissions  every record under badf/admissions/
  readiness   deterministic readiness computation
  all         default
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OK, REFUSE = 0, 2

# The posture each registry must hold. Pinned to exact values, not merely
# required-to-be-present: "present" is satisfied by "allow", which is the
# condition being prevented.
REQUIRED_POLICIES = {
    "badf/skill-registry.json": "approved-only",
    "badf/mcp-registry.json": "deny",
    "badf/tool-registry.json": "deny-mutation",
}

# A lifecycle state at or beyond ADMITTED asserts that the mandatory checks
# passed. Below it, NOT_PERFORMED is honest rather than disqualifying.
ADMITTED_OR_BEYOND = {
    "ADMITTED", "SANDBOXED", "VALIDATED", "APPROVED", "REGISTERED",
    "ACTIVATED", "MONITORED",
}
GATED_ASSESSMENTS = (
    "prompt_injection_assessment",
    "supply_chain_assessment",
    "routing_tests",
)
CAPABILITY_CLASSES = ("network", "filesystem", "commands", "credentials",
                      "external_services")


class Refused(Exception):
    pass


def load(rel: str) -> dict:
    path = ROOT / rel
    if not path.is_file():
        raise Refused(f"{rel} is absent")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise Refused(f"{rel} is unparseable: {exc}") from exc


def check_registries() -> list[str]:
    notes = []
    for rel, expected in REQUIRED_POLICIES.items():
        document = load(rel)
        actual = document.get("default_policy")
        if actual != expected:
            raise Refused(
                f"{rel} default_policy must be {expected!r}, found {actual!r}"
            )
        notes.append(f"{rel} posture {expected}")

    skills = load("badf/skill-registry.json").get("skills")
    if not isinstance(skills, list):
        raise Refused("badf/skill-registry.json skills must be an array")
    # An entry here asserts REGISTERED. Registration without an admission
    # record is the "absence of a record is not acceptance" case in section 2.
    known = {p.stem for p in (ROOT / "badf/admissions").glob("*.json")}
    for entry in skills:
        skill_id = entry.get("skill_id")
        if skill_id not in known:
            raise Refused(
                f"skill registry entry {skill_id!r} has no admission record"
            )
    return notes


def check_admissions() -> list[str]:
    directory = ROOT / "badf/admissions"
    if not directory.is_dir():
        raise Refused("badf/admissions does not exist")
    records = sorted(directory.glob("*.json"))
    if not records:
        raise Refused("badf/admissions contains no records")

    schema = load("schemas/badf-admission-record.schema.json")
    required = set(schema["required"])
    notes = []
    for path in records:
        record = load(f"badf/admissions/{path.name}")
        label = f"admission {path.name}"
        missing = sorted(required - set(record))
        if missing:
            raise Refused(f"{label} missing required fields: {missing}")

        commit = record["upstream_commit"]
        if len(commit) != 40 or not all(c in "0123456789abcdef" for c in commit):
            raise Refused(
                f"{label} upstream_commit {commit!r} is not an immutable 40-hex "
                "commit (standard 4.1: a moving branch is not provenance)"
            )
        if record["license_decision"] == "UNKNOWN":
            raise Refused(f"{label} license status is UNKNOWN, which is blocking")

        caps = record["declared_capabilities"]
        missing_classes = sorted(set(CAPABILITY_CLASSES) - set(caps))
        if missing_classes:
            raise Refused(f"{label} declares no capability class for {missing_classes}")

        state = record["lifecycle_state"]
        if state in ADMITTED_OR_BEYOND:
            for key in GATED_ASSESSMENTS:
                outcome = record[key].get("outcome")
                if outcome != "PASS":
                    raise Refused(
                        f"{label} claims lifecycle_state {state!r} while {key} "
                        f"is {outcome!r}. A state at or beyond ADMITTED asserts "
                        "these passed; missing evidence is not a PASS."
                    )
            if not record["rollback"].get("verified"):
                raise Refused(
                    f"{label} claims {state!r} with an unverified rollback"
                )
        if state == "ACTIVATED" and record["declared_authority"] == "NONE":
            raise Refused(
                f"{label} is ACTIVATED while declaring authority NONE"
            )
        notes.append(f"{path.stem}: {state}")
    return notes


def compute_readiness() -> tuple[str, list[str]]:
    """Deterministic, and unable to report READY while substrate is absent."""
    unmet = []
    if not (ROOT / "badf/admissions").is_dir():
        unmet.append("SUBSTRATE: no admissions directory")
    for rel in REQUIRED_POLICIES:
        if not (ROOT / rel).is_file():
            unmet.append(f"SUBSTRATE: {rel} absent")
    for rel in ("schemas/badf-admission-record.schema.json",
                "schemas/badf-session-checkpoint.schema.json"):
        if not (ROOT / rel).is_file():
            unmet.append(f"SCHEMA: {rel} absent")

    activated = [
        r for r in sorted((ROOT / "badf/admissions").glob("*.json"))
        if json.loads(r.read_text(encoding="utf-8")).get("lifecycle_state") == "ACTIVATED"
    ] if (ROOT / "badf/admissions").is_dir() else []
    if not activated:
        unmet.append("ACTIVATION: no skill has reached ACTIVATED")

    # Deliberately unmet by construction: this work package creates no authority
    # record, no production executor and no post-deployment evidence. Reporting
    # anything above ENGINEERING_READY here would be the false-READY case the
    # mandate names.
    unmet.append("AUTHORITY: no effective authority record exists")
    unmet.append("PRODUCTION: no post-deployment evidence exists")

    substrate_ok = not [u for u in unmet if u.startswith(("SUBSTRATE", "SCHEMA"))]
    state = "ENGINEERING_READY" if substrate_ok else "NOT_READY"
    return state, unmet


def main(argv: list[str]) -> int:
    mode = os.environ.get("MODE") or (argv[1] if len(argv) > 1 else "all")
    try:
        report: dict[str, object] = {"mode": mode}
        if mode in ("registries", "all"):
            report["registries"] = check_registries()
        if mode in ("admissions", "all"):
            report["admissions"] = check_admissions()
        if mode in ("readiness", "all"):
            state, unmet = compute_readiness()
            report["readiness"] = state
            report["unmet"] = unmet
        elif mode not in ("registries", "admissions"):
            raise Refused(f"unknown MODE {mode!r}")
    except Refused as exc:
        print(f"BADF REGISTRY REFUSED (closed): {exc}", file=sys.stderr)
        return REFUSE
    except (OSError, KeyError, TypeError) as exc:
        print(f"BADF REGISTRY REFUSED (closed): {type(exc).__name__}: {exc}",
              file=sys.stderr)
        return REFUSE
    print(json.dumps(report, indent=2, sort_keys=True))
    return OK


if __name__ == "__main__":
    sys.exit(main(sys.argv))
