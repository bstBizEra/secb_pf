"""SECB-WP-FWK-102 -- authority, agent and tool objects (P0 item 2).

The framework's mission line is "SecB assigns and verifies authority. It is not a super-agent."
That only means something if the four things it keeps apart are separately resolvable:

    runtime identity != role != capability != authority

Identity already lives in config/agent_identity_registry.schema.json (FWK-081) and is not
redefined. This adds role (agent), capability (tool) and authority (grant), and enforces the
properties that make a grant a bound rather than a description.

NO EFFECTIVE GRANT IS SHIPPED. Every grant here is a test fixture. An agent that wrote itself a
grant into the repository would be performing exactly the self-authorisation the exclusions forbid,
and `test_the_repository_ships_no_effective_authority_grant` asserts none exists.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from test_control_kernel import validate  # reuse the kernel validator, do not re-create

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"


def load(name: str) -> dict:
    return json.loads((SCHEMAS / f"{name}.schema.json").read_text(encoding="utf-8"))


def grant(**over) -> dict:
    body = {
        "schema": "secb.authority-grant/v1", "grant_id": "G-1", "agent_id": "AGENT-ENG-001",
        "work_package_id": "SECB-WP-FWK-102", "issued_by": "operator",
        "issued_at": "2026-08-18T00:00:00+00:00", "expires_at": "2026-08-18T01:00:00+00:00",
        "repository": "bstBizEra/secb_pf", "branch": "feat/x", "permitted_paths": ["tests/"],
        "tool_allowlist": ["TOOL-READ-001"], "environment": "repository",
        "network_policy": "none", "budget": {"max_files": 3, "max_lines": 200},
        "required_evidence": ["diff", "test results"],
        "prohibited_actions": ["merge to main"],
        "confers_merge_authority": False, "may_delegate": False,
    }
    body.update(over)
    return body


def agent(**over) -> dict:
    body = {
        "schema": "secb.agent/v1", "agent_id": "AGENT-ENG-001", "role": "software_engineer",
        "responsibilities": ["implement an authorised work package"],
        "prohibited_roles": ["qa_verdict", "release_authority"],
        "tool_requests": ["TOOL-EDIT-001"], "authority_ceiling": "C1",
        "termination_conditions": ["acceptance criteria met", "budget exhausted"],
    }
    body.update(over)
    return body


def tool(**over) -> dict:
    body = {
        "schema": "secb.tool/v1", "tool_id": "TOOL-GIT-MERGE-001", "version": "1.0.0",
        "purpose": "compare-and-swap merge", "risk_class": "C2",
        "required_authority": ["repository_write"], "side_effect": "mutates_repository",
        "idempotency": "conditional", "destructive": False,
        "evidence": ["target_base_sha", "actual_result_tree"], "timeout_seconds": 120,
    }
    body.update(over)
    return body


# --------------------------------------------------- the four separations


def test_identity_is_not_redefined_here():
    """Identity resolves in the FWK-081 registry; a second definition would let a holder assert
    both what it is and what it may do."""
    assert (ROOT / "config" / "agent_identity_registry.schema.json").is_file()
    for name in ("authority-grant", "agent", "tool"):
        text = json.dumps(load(name))
        assert "app_id" not in text and "installation_id" not in text, name


def test_an_agent_requests_tools_and_never_grants_them():
    """`tool_requests` on the agent, `tool_allowlist` on the grant. The field names are the control."""
    assert "tool_requests" in load("agent")["properties"]
    assert "tool_allowlist" not in load("agent")["properties"]
    assert "tool_allowlist" in load("authority-grant")["properties"]
    assert "tool_requests" not in load("authority-grant")["properties"]


def test_authority_is_non_transitive_by_pinned_field():
    """`may_delegate` is required AND const false, so transitivity cannot arrive as a default."""
    schema = load("authority-grant")
    assert "may_delegate" in schema["required"]
    assert schema["properties"]["may_delegate"]["const"] is False
    assert validate(grant(may_delegate=True), schema)


def test_a_grant_cannot_confer_merge_authority():
    schema = load("authority-grant")
    assert schema["properties"]["confers_merge_authority"]["const"] is False
    assert validate(grant(confers_merge_authority=True), schema)


# --------------------------------------------------- a bound not written is not a bound


@pytest.mark.parametrize("field", ["expires_at", "permitted_paths", "budget", "environment",
                                   "network_policy", "required_evidence", "prohibited_actions",
                                   "work_package_id", "branch", "repository"])
def test_every_bound_is_required(field):
    """An omitted scope reads as unlimited to anyone holding the grant."""
    body = grant()
    del body[field]
    assert any(field in e for e in validate(body, load("authority-grant"))), field


def test_an_empty_path_list_is_not_anywhere(): 
    assert any("minItems" in e for e in validate(grant(permitted_paths=[]),
                                                 load("authority-grant")))


def test_a_grant_with_no_required_evidence_is_rejected():
    """Evidence declared at grant time cannot be chosen afterwards to fit the outcome."""
    assert any("minItems" in e for e in validate(grant(required_evidence=[]),
                                                 load("authority-grant")))


def test_a_well_formed_grant_validates():
    assert validate(grant(), load("authority-grant")) == []


# --------------------------------------------------- the agent side


def test_an_agent_must_name_a_role_it_may_not_hold():
    """The producer may not issue its own final verdict, so prohibited_roles is required."""
    assert any("minItems" in e for e in validate(agent(prohibited_roles=[]), load("agent")))


def test_an_agent_must_declare_how_it_stops():
    assert any("minItems" in e for e in validate(agent(termination_conditions=[]), load("agent")))


def test_an_authority_ceiling_is_a_bound_not_an_entitlement():
    schema = load("agent")
    assert schema["properties"]["authority_ceiling"]["enum"] == ["C0", "C1", "C2", "C3", "C4"]
    assert "upper bound" in schema["properties"]["authority_ceiling"]["description"]
    assert validate(agent(authority_ceiling="C9"), schema)


# --------------------------------------------------- the tool side


def test_a_tool_declares_what_it_needs_authorising_for():
    assert any("minItems" in e for e in validate(tool(required_authority=[]), load("tool")))


def test_a_mutating_tool_must_emit_evidence():
    """A mutating tool producing no evidence leaves nothing to reconcile against."""
    assert any("minItems" in e for e in validate(tool(evidence=[]), load("tool")))


def test_a_tool_must_declare_a_timeout():
    body = tool()
    del body["timeout_seconds"]
    assert any("timeout_seconds" in e for e in validate(body, load("tool")))


def test_a_destructive_tool_must_name_its_rollback():
    """Draft-07 cannot express this conditional cleanly, so it is enforced here and the schema
    says so rather than implying the constraint is structural."""
    schema = load("tool")
    assert "enforced by the validator" in schema["properties"]["rollback_tool"]["description"]
    destructive = tool(destructive=True)
    assert "rollback_tool" not in destructive
    assert requires_rollback(destructive) is False
    assert requires_rollback(tool(destructive=True, rollback_tool="TOOL-REVERT-001")) is True
    assert requires_rollback(tool(destructive=False)) is True


def requires_rollback(descriptor: dict) -> bool:
    return not descriptor.get("destructive") or bool(descriptor.get("rollback_tool"))


# --------------------------------------------------- no self-authorisation


def test_a_grant_issued_by_its_own_holder_is_a_finding():
    """An agent may not issue its own authority. Draft-07 cannot compare two sibling fields, so
    this is enforced here and declared, not implied."""
    assert issuer_is_independent(grant()) is True
    assert issuer_is_independent(grant(issued_by="AGENT-ENG-001")) is False


def issuer_is_independent(g: dict) -> bool:
    return g["issued_by"] != g["agent_id"]


def test_the_repository_ships_no_effective_authority_grant():
    """Writing a grant for itself into the repository is the self-authorisation the exclusions
    forbid. Every grant in this codebase is a test fixture, and this asserts it stays that way."""
    offenders = []
    for path in ROOT.rglob("*.json"):
        if ".git" in path.as_posix() or "/tests/" in path.as_posix():
            continue
        try:
            body = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            continue
        if isinstance(body, dict) and body.get("schema") == "secb.authority-grant/v1":
            offenders.append(path.as_posix())
    assert offenders == [], f"effective authority grants committed: {offenders}"
