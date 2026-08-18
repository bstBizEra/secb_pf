"""SECB-WP-FWK-105 -- external policy decisions (P0 item 8).

The scope names OPA. NFR-12 keeps gates stdlib-only and CI installs only pytest, so this preserves
what policy-as-code is FOR -- a decision computed from declared rules by a component the requester
does not control, returning the typed decision object -- and drops the language.

    POLICY_INTERFACE_PRESERVED != OPA_ADOPTED

Negative-first. Every way a requester could decide its own case is tested before the permit path.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "scripts" / "check_policy_decision.py"
BUNDLE = ROOT / "config" / "policies" / "core.policy.json"

sys.path.insert(0, str(ROOT / "scripts"))
from check_policy_decision import Refused, decide, load_bundle, matches  # noqa: E402

MERGE_CLEAN = {"checks_green": True, "head_unchanged": True, "expected_tree_proven": True,
               "contention_resolved": True}


def bundle():
    return load_bundle(BUNDLE)


def run(request: dict, tmp_path: Path, **env_extra: str) -> subprocess.CompletedProcess:
    path = tmp_path / "request.json"
    path.write_text(json.dumps(request), encoding="utf-8")
    return subprocess.run([sys.executable, str(TOOL)], capture_output=True, text=True,
                          env={**os.environ, "REQUEST": str(path), "REPO_ROOT": str(ROOT),
                               "PYTHONDONTWRITEBYTECODE": "1", **env_extra}, check=False)


def outcome(operation: str, facts: dict) -> dict:
    body, digest = bundle()
    from datetime import datetime, timezone
    return decide(body, digest, {"operation": operation, "facts": facts},
                  datetime.now(timezone.utc))


# --------------------------------------------------------------- default deny


def test_an_unmatched_request_is_denied_not_allowed():
    """Silence is not consent. An unmatched request is unclassified, not permitted."""
    result = outcome("admit_work", {"work_package_present": True, "duplicate": True,
                                    "contention": False})
    assert result["decision"] == "deny"
    assert result["reason_codes"] == ["NO_MATCHING_RULE"]
    assert result["default_applied"] is True


def test_an_unknown_operation_is_denied():
    assert outcome("delete_production", {})["decision"] == "deny"


# --------------------------------------------------------------- deny wins


def test_deny_beats_allow_when_both_match():
    """Resolving toward permission would make one permissive rule defeat every restrictive one."""
    result = outcome("grant_capability",
                     {"envelope_valid": True, "within_autonomy_ceiling": True,
                      "paths_within_scope": True, "issuer_independent": False})
    assert result["decision"] == "deny"
    assert "SELF_ISSUED_AUTHORITY" in result["reason_codes"]
    assert "allow" in result["overridden_effects"] or result["matched_rules"] == ["POL-AUTH-002"]


def test_an_expired_envelope_denies_regardless_of_everything_else():
    result = outcome("grant_capability",
                     {"envelope_valid": False, "within_autonomy_ceiling": True,
                      "paths_within_scope": True, "issuer_independent": True})
    assert result["decision"] == "deny"
    assert "ENVELOPE_INVALID_OR_EXPIRED" in result["reason_codes"]


# ------------------------------------------------- a request cannot decide its own case


def test_an_absent_fact_does_not_match_a_rule():
    """A request must not earn a permission by saying LESS."""
    rule = {"when": {"envelope_valid": True}}
    assert matches(rule, {"envelope_valid": True}) is True
    assert matches(rule, {}) is False
    assert matches(rule, {"envelope_valid": False}) is False


@pytest.mark.parametrize("smuggled", ["rules", "effect", "decision", "reason_codes",
                                      "policy_digest"])
def test_a_request_carrying_policy_is_refused(tmp_path, smuggled):
    request = {"operation": "admit_work", "facts": {"work_package_present": True},
               smuggled: "anything"}
    result = run(request, tmp_path)
    assert result.returncode == 2
    assert "deciding its own case" in result.stderr


def test_a_request_with_no_facts_is_refused(tmp_path):
    """An absent fact set would vacuously fail every rule into a default deny that hid a
    malformed request -- a right answer for the wrong reason."""
    result = run({"operation": "admit_work"}, tmp_path)
    assert result.returncode == 2
    assert "absent fact set is not an empty one" in result.stderr


def test_a_request_with_no_operation_is_refused(tmp_path):
    assert run({"facts": {}}, tmp_path).returncode == 2


# --------------------------------------------------------------- merge is never allow


def test_a_perfect_merge_candidate_is_conditional_never_allow(tmp_path):
    """Every mechanical precondition can hold and the merge still needs an authority this policy
    does not hold. A policy returning allow here would be granting what it cannot."""
    result = outcome("merge_candidate", MERGE_CLEAN)
    assert result["decision"] == "conditional"
    assert "human_merge_authority" in result["obligations"]
    assert "post_merge_tree_readback" in result["obligations"]


def test_no_rule_in_the_shipped_bundle_can_allow_a_merge():
    body, _ = bundle()
    merge_rules = [r for r in body["rules"] if r["operation"] == "merge_candidate"]
    assert merge_rules
    assert "allow" not in {r["effect"] for r in merge_rules}


def test_a_stale_candidate_is_denied():
    facts = {**MERGE_CLEAN, "head_unchanged": False}
    result = outcome("merge_candidate", facts)
    assert result["decision"] == "deny"
    assert "STALE_CANDIDATE" in result["reason_codes"]


def test_a_policy_cannot_adopt_itself():
    result = outcome("adopt_policy", {"proposal_is_self_referential": True})
    assert result["decision"] == "deny"
    assert "POLICY_CANNOT_ADOPT_ITSELF" in result["reason_codes"]


# --------------------------------------------------------------- bundle integrity


def test_an_unreadable_bundle_is_refused_not_treated_as_permissive(tmp_path):
    """Defaulting to allow would make an unreadable policy the most permissive one."""
    result = run({"operation": "admit_work", "facts": {}}, tmp_path,
                 POLICY_BUNDLE="config/policies/absent.json")
    assert result.returncode == 2
    assert "most permissive" in result.stderr


def test_an_empty_bundle_is_refused(tmp_path):
    empty = tmp_path / "empty.policy.json"
    empty.write_text(json.dumps({"schema": "secb.policy-bundle/v1", "rules": []}),
                     encoding="utf-8")
    with pytest.raises(Refused, match="decides nothing"):
        load_bundle(empty)


def test_a_conditional_rule_without_obligations_is_refused(tmp_path):
    """A conditional with no obligations is an allow that reads as a caveat."""
    body = json.loads(BUNDLE.read_text(encoding="utf-8"))
    for rule in body["rules"]:
        if rule["effect"] == "conditional":
            rule.pop("obligations", None)
    path = tmp_path / "b.json"
    path.write_text(json.dumps(body), encoding="utf-8")
    with pytest.raises(Refused, match="reads as a caveat"):
        load_bundle(path)


def test_a_duplicate_rule_id_is_refused(tmp_path):
    body = json.loads(BUNDLE.read_text(encoding="utf-8"))
    body["rules"].append(dict(body["rules"][0]))
    path = tmp_path / "b.json"
    path.write_text(json.dumps(body), encoding="utf-8")
    with pytest.raises(Refused, match="duplicate rule id"):
        load_bundle(path)


def test_the_digest_binds_the_decision_to_the_bundle(tmp_path):
    """A decision that did not name its policy version could outlive the rules that produced it."""
    _, first = bundle()
    body = json.loads(BUNDLE.read_text(encoding="utf-8"))
    body["version"] = "9.9.9"
    path = tmp_path / "b.json"
    path.write_text(json.dumps(body), encoding="utf-8")
    _, second = load_bundle(path)
    assert first != second


# --------------------------------------------------------------- the interface


def test_the_decision_declares_it_is_not_opa(tmp_path):
    """Claiming OPA compliance for a stdlib evaluator would be the overstatement this framework
    keeps finding. The engine field says what it is."""
    report = json.loads(run({"operation": "merge_candidate", "facts": MERGE_CLEAN},
                            tmp_path).stdout)
    assert "NOT OPA" in report["engine"]
    assert report["policy_digest"].startswith("sha256:")
    assert report["valid_until"] > report["evaluated_at"]
    assert report["confers_merge_authority"] is False


def test_the_decision_states_it_verifies_no_facts(tmp_path):
    """The evaluator decides on supplied facts. Whoever supplies a false fact gets a decision
    computed correctly from a lie, and the report says so rather than implying verification."""
    report = json.loads(run({"operation": "admit_work",
                             "facts": {"work_package_present": True, "duplicate": False,
                                       "contention": False}}, tmp_path).stdout)
    assert any("verifies none" in n for n in report["not_proven"])


def test_exit_code_follows_the_decision(tmp_path):
    permitted = run({"operation": "merge_candidate", "facts": MERGE_CLEAN}, tmp_path)
    denied = run({"operation": "merge_candidate",
                  "facts": {**MERGE_CLEAN, "head_unchanged": False}}, tmp_path)
    assert permitted.returncode == 0 and denied.returncode == 2
