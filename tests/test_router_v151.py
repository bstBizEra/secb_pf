"""Tests for router v1.5.1 (src/secb_router) — the F1 fix.

Two proof obligations, per SECB-WP-FWK-010:

1. **No behavioral regression:** the sealed FIT-101–120 suite is replayed,
   unmodified, against v1.5.1. The sealed suite is loaded from the evidence
   directory and its ``import router`` is pointed at the new module for the
   duration of the load — then restored, so the sealed suite still tests the
   sealed baseline when pytest collects it directly.
2. **F1 regression coverage:** for each field the v1.5 registry_hash omitted
   (validation, qualification, cost, expires_at), a change must now
   invalidate a previously planned route, fail-closed.
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from secb_router import router as v151  # noqa: E402

EVIDENCE_DIR = (
    ROOT / "docs" / "06-agent-orchestration" / "skill-router"
    / "SECB-WP-ENGLOOP-MVP-001 — Sandbox Evidence"
)

NOW = datetime(2026, 8, 10, tzinfo=timezone.utc)
POLICY = "policy-v1"


def _load_sealed_fit_suite_against_v151():
    """Load the sealed FIT test module with `router` resolved to v1.5.1."""
    saved = sys.modules.get("router")
    sys.modules["router"] = v151
    try:
        spec = importlib.util.spec_from_file_location(
            "sealed_fit_replay", EVIDENCE_DIR / "test_router.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        # Restore so a direct pytest collection of the sealed file still
        # imports the sealed baseline, not v1.5.1.
        if saved is not None:
            sys.modules["router"] = saved
        else:
            sys.modules.pop("router", None)
    return module


def test_sealed_fit_101_120_pass_against_v151():
    module = _load_sealed_fit_suite_against_v151()
    suite = unittest.TestLoader().loadTestsFromTestCase(module.RouterFIT)
    assert suite.countTestCases() == 20
    result = unittest.TextTestRunner(verbosity=0).run(suite)
    assert result.wasSuccessful(), (
        f"FIT replay failures against v1.5.1: {result.failures + result.errors}"
    )


def _base_setup():
    request = {
        "request_id": "req-f1", "risk_tier": "R1",
        "required_capabilities": ["draft", "validate"],
        "explicit_skill_priorities": [], "permitted_effects": [],
    }
    skills = [
        v151.Skill("combo", "1.0.0", "digest-combo",
                   frozenset({"draft", "validate"}), qualification=2),
    ]
    return request, skills


@pytest.mark.parametrize(
    "field_name,changed_value",
    [
        ("validation", frozenset({"schema", "security"})),
        ("qualification", 9),
        ("cost", 99),
        ("expires_at", "2098-01-01T00:00:00+00:00"),
    ],
)
def test_f1_selection_relevant_field_change_invalidates_route(field_name, changed_value):
    request, skills = _base_setup()
    plan = v151.route(request, skills, POLICY, NOW)
    changed = [replace(skills[0], **{field_name: changed_value})]
    with pytest.raises(v151.RouteHeld):
        v151.authorize_invocation(
            plan, "combo", request=request, skills=changed, policy_hash=POLICY
        )


def test_f1_unchanged_registry_still_authorizes():
    request, skills = _base_setup()
    plan = v151.route(request, skills, POLICY, NOW)
    warrant = v151.authorize_invocation(
        plan, "combo", request=request, skills=skills, policy_hash=POLICY
    )
    assert warrant  # the fix must not fail-closed the legitimate path


def test_v151_registry_hash_differs_from_sealed_for_scored_fields():
    """The sealed v1.5 hash treated cost-only differences as identical;
    v1.5.1 must not. Guard against the fix regressing to the old row shape."""
    _, skills = _base_setup()
    cheaper = [replace(skills[0], cost=1)]
    pricier = [replace(skills[0], cost=2)]
    assert v151.registry_hash(cheaper) != v151.registry_hash(pricier)
