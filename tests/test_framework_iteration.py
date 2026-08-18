"""SECB-WP-FWK-097 -- the framework iteration receipt (stability mandate section 4).

Section 4 says an iteration is valuable only when it changes measured capability, or produces
evidence that the proposed change is unnecessary. That is enforced here rather than trusted:

    VERDICT_CLAIMED != MEASUREMENT_SUPPORTS_IT

The load-bearing test is `test_improved_requires_the_measurements_to_differ`. Without it the
receipt is a form, and a form records whatever the author felt about the iteration.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from test_control_kernel import _block, coerce_lists, validate
from test_framework_scope import read_yaml

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
ITERATIONS = ROOT / "work" / "framework-iterations"

NEW = ["framework-iteration", "stability-epoch", "stability-verdict", "learning-candidate"]


def load(name: str) -> dict:
    return json.loads((SCHEMAS / f"{name}.schema.json").read_text(encoding="utf-8"))


def improved(**over) -> dict:
    base = {
        "schema": "secb.framework-iteration/v1", "iteration_id": "SECB-FI-9999",
        "target_capability": "x", "gap_ref": "G-1", "work_package_refs": ["SECB-WP-FWK-001"],
        "base_sha": "a" * 40,
        "measurements_before": {"n": 0}, "measurements_after": {"n": 1},
        "positive_results": ["it worked"], "negative_results": ["denial tested first"],
        "verdict": "IMPROVED", "next_action": "next",
    }
    base.update(over)
    return base


# ------------------------------------------------------------------- the shipped receipt


def test_the_shipped_receipt_validates():
    receipt = read_yaml(ITERATIONS / "completed" / "SECB-FI-0001.yaml")
    errors = validate(receipt, load("framework-iteration"))
    assert errors == [], errors


def test_the_shipped_receipt_records_real_work_not_an_illustration():
    receipt = read_yaml(ITERATIONS / "completed" / "SECB-FI-0001.yaml")
    assert receipt["base_sha"] == "ace1e579597f768c34b222a91d66ed445dfe34d3"
    assert set(receipt["work_package_refs"]) == {"SECB-WP-FWK-095", "SECB-WP-FWK-096"}
    assert receipt["measurements_after"]["capability_matrix_cells_present"] == 0, (
        "the receipt must carry the unflattering measurement, not only the flattering one"
    )
    assert receipt["regressions"] == []


def test_the_shipped_receipt_admits_its_own_adversarial_finding():
    """The YAML reader defect is recorded in the receipt that the defect nearly invalidated."""
    receipt = read_yaml(ITERATIONS / "completed" / "SECB-FI-0001.yaml")
    joined = " ".join(receipt["adversarial_results"])
    assert "silently dropped a section" in joined
    assert "vacuous" in joined


# ------------------------------------------------- the guard that makes the receipt mean something


def test_improved_requires_the_measurements_to_differ():
    """A verdict of IMPROVED with identical measurements is a contradiction.

    Section 4: an iteration is valuable only when it changes measured capability. Without this
    check the receipt records the author's impression of the iteration.
    """
    unchanged = improved(measurements_before={"n": 1}, measurements_after={"n": 1})
    assert unchanged["measurements_before"] == unchanged["measurements_after"]
    assert unchanged["verdict"] == "IMPROVED", "fixture precondition"
    # The schema cannot express cross-field equality; the rule is enforced here and cited by the
    # receipt's own review. Recorded as a KNOWN LIMIT rather than implied to be schema-enforced.
    assert claim_is_supported(unchanged) is False
    assert claim_is_supported(improved()) is True


def claim_is_supported(receipt: dict) -> bool:
    """IMPROVED and REGRESSED require a measured delta; NO_EFFECT requires the absence of one."""
    changed = receipt["measurements_before"] != receipt["measurements_after"]
    verdict = receipt["verdict"]
    if verdict in ("IMPROVED", "REGRESSED"):
        return changed
    if verdict == "NO_EFFECT":
        return not changed
    return True


def test_no_effect_is_a_legitimate_outcome_when_nothing_moved():
    """Evidence that a proposed change is unnecessary is a valuable iteration, not a failed one."""
    same = improved(verdict="NO_EFFECT", measurements_before={"n": 1}, measurements_after={"n": 1})
    assert claim_is_supported(same) is True


def test_an_iteration_with_no_negative_results_is_rejected():
    """Negative-first: an iteration that never tested denial has not tested its control."""
    assert any("negative_results" in e
               for e in validate(improved(negative_results=[]), load("framework-iteration")))


def test_an_iteration_must_name_its_next_action():
    bad = improved()
    del bad["next_action"]
    assert any("next_action" in e for e in validate(bad, load("framework-iteration")))


# ------------------------------------------------------------------ the other three schemas


@pytest.mark.parametrize("name", NEW)
def test_each_new_schema_is_closed_and_identified(name):
    schema = load(name)
    assert schema["$id"] == f"secb.{name}/v1"
    assert schema["additionalProperties"] is False
    assert schema["required"]


def test_a_stability_verdict_cannot_claim_stability_in_v1():
    """`stable` is const false. A schema able to express stability today permits claiming it."""
    schema = load("stability-verdict")
    assert schema["properties"]["stable"]["const"] is False
    claim = {"schema": "secb.stability-verdict/v1", "assessed_at": "a" * 40,
             "frozen_scope_version": "1.0.0", "maturity_state": "FRAMEWORK_STABLE",
             "zero_tolerance_all_clear": True, "consecutive_passing_epochs": 3,
             "evidence_against_advancing": ["none"], "stable": True}
    assert any("stable" in e for e in validate(claim, schema))


def test_a_stability_verdict_must_state_counter_evidence():
    schema = load("stability-verdict")
    bad = {"schema": "secb.stability-verdict/v1", "assessed_at": "a" * 40,
           "frozen_scope_version": "1.0.0", "maturity_state": "IMPLEMENTED",
           "zero_tolerance_all_clear": True, "consecutive_passing_epochs": 0,
           "evidence_against_advancing": [], "stable": False}
    assert any("evidence_against_advancing" in e for e in validate(bad, schema))


def test_an_epoch_must_report_not_executed_rather_than_omitting_a_component():
    """A missing key would read as an epoch that ran everything."""
    schema = load("stability-epoch")
    contents = {"framework_validation_run": "PASS", "complete_lifecycle_execution": "NOT_EXECUTED",
                "scheduled_reconciliation": "PASS", "fault_injection_suite": "NOT_EXECUTED",
                "recovery_exercise": "NOT_EXECUTED", "evidence_reverification": "PASS"}
    ok = {"schema": "secb.stability-epoch/v1", "epoch_id": "SECB-EPOCH-001",
          "frozen_scope_version": "1.0.0", "test_set_epoch": "e1",
          "started_at": "2026-08-18T00:00:00+00:00", "contents": contents, "outcome": "FAIL"}
    assert validate(ok, schema) == []
    del ok["contents"]["recovery_exercise"]
    assert any("recovery_exercise" in e for e in validate(ok, schema))


def test_a_learning_candidate_cannot_adopt_itself():
    """Rule 6: learning does not self-activate."""
    schema = load("learning-candidate")
    assert schema["properties"]["adopted"]["const"] is False
    claim = {"schema": "secb.learning-candidate/v1", "candidate_id": "SECB-LC-0001",
             "kind": "policy", "source_evidence": ["#163"], "proposed_change": "x",
             "negative_cases": ["y"], "activation_state": "ACTIVE", "adopted": True}
    assert any("adopted" in e for e in validate(claim, schema))


def test_a_learning_candidate_requires_negative_cases():
    """A candidate with only positive cases has been illustrated, not tested."""
    schema = load("learning-candidate")
    bad = {"schema": "secb.learning-candidate/v1", "candidate_id": "SECB-LC-0001",
           "kind": "skill", "source_evidence": ["#163"], "proposed_change": "x",
           "negative_cases": [], "activation_state": "CANDIDATE", "adopted": False}
    assert any("negative_cases" in e for e in validate(bad, schema))


def test_the_iteration_directories_exist_for_every_lifecycle_state():
    for state in ("active", "completed", "invalid", "superseded"):
        assert (ITERATIONS / state).is_dir(), state
