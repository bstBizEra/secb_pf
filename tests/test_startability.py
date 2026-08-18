"""SECB-WP-FWK-075 -- startability resolution (issue #137).

The seven required negative tests are named in the work package and each is reproduced here as
an executable case. They exist because the 2026-08-15 decision -- decline FWK-074, select
FWK-070 -- was correct by reasoning, and reasoning leaves no artifact.

    DESIGNABLE != STARTABLE
    PROPOSED_HEAD_GREEN != LANDED
    CLEAN_MERGE != VALID_EXECUTION_ORDER
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "scripts" / "check_startability.py"

CLEAR_CONTENTION = {
    "same_file": False, "overlapping_hunks": False, "same_authoritative_object": False,
}
ALL_TRUE = {
    "work_package_defined": True,
    "required_dependencies_resolved_on_effective_base": True,
    "required_bytes_available_on_effective_base": True,
    "canonical_reuse_target_available": True,
    "semantic_preconditions_satisfied": True,
    "contention_assessed_at_hunk_and_object_level": True,
    "task_context_coherent": True,
    "authority_route_available_for_proposed_change": True,
    "no_unresolved_unknowns": True,
}


def record(**overrides) -> dict:
    base = {
        "schema": "secb.startability-assessment/v1",
        "work_package_id": "SECB-WP-FWK-070",
        "as_of_ref": "ace1e579597f768c34b222a91d66ed445dfe34d3",
        "projection": "EFFECTIVE_MAIN",
        "design_state": "DESIGNABLE",
        "dependencies": [],
        "contention": dict(CLEAR_CONTENTION),
        "conjuncts": dict(ALL_TRUE),
    }
    base.update(overrides)
    return base


def run(payload, tmp_path: Path, **env_extra: str) -> subprocess.CompletedProcess:
    path = tmp_path / "assessments.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(TOOL)], capture_output=True, text=True, check=False,
        env={**os.environ, "ASSESSMENTS": str(path), "PYTHONDONTWRITEBYTECODE": "1", **env_extra},
    )


def state_of(payload, tmp_path: Path) -> str:
    return json.loads(run(payload, tmp_path).stdout)["assessments"][0]["implementation_state"]


def refuses(payload, tmp_path: Path, fragment: str) -> str:
    result = run(payload, tmp_path)
    assert result.returncode == 2, result.stdout
    assert fragment in result.stderr, result.stderr
    return result.stderr


# --------------------------------------------------------------------- accept path


def test_a_fully_evidenced_package_is_startable(tmp_path):
    result = run(record(), tmp_path)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["assessments"][0]["implementation_state"] == "STARTABLE"
    assert report["assessments"][0]["blockers"] == []
    assert report["confers_work_authority"] is False


# ------------------------------------------- the seven required negative tests


def test_1_helper_only_on_an_open_pr_is_blocked_by_bytes(tmp_path):
    """FWK-074's actual situation: the parser existed only on unmerged #134."""
    payload = record(dependencies=[{
        "class": "BYTE_DEPENDENCY", "resolved": False, "projection": "EFFECTIVE_MAIN",
        "as_of_ref": "ace1e579", "description": "parser exists only on open PR #134",
    }], next_recheck_trigger="PR #134 merged or closed")
    assert state_of(payload, tmp_path) == "BLOCKED_BY_BYTES"


def test_2_copying_the_helper_into_a_new_branch_is_still_blocked(tmp_path):
    """Parallel implementation is prohibited, so the reuse target being 'available by copy'
    does not satisfy the conjunct -- it creates a competing source of truth."""
    payload = record(
        dependencies=[{
            "class": "CONTENT_REUSE_DEPENDENCY", "resolved": False,
            "projection": "EFFECTIVE_MAIN", "as_of_ref": "ace1e579",
            "description": "canonical parser copied into this branch rather than reused",
        }],
        conjuncts={**ALL_TRUE, "canonical_reuse_target_available": False},
        next_recheck_trigger="canonical parser lands on effective main")
    assert state_of(payload, tmp_path) == "BLOCKED_BY_BYTES"


def test_3_mergeable_and_green_but_unmerged_is_proposed_only(tmp_path):
    """The sharpest one: the dependency IS resolved, but only on a proposed head."""
    payload = record(dependencies=[{
        "class": "BYTE_DEPENDENCY", "resolved": True, "projection": "PROPOSED_HEAD",
        "as_of_ref": "34bc9b86760b", "description": "#161 is mergeable and green, and unmerged",
    }], next_recheck_trigger="#161 merged to main")
    assert state_of(payload, tmp_path) == "BLOCKED_BY_BYTES"


def test_4_same_file_non_overlapping_hunks_is_not_automatically_contended(tmp_path):
    payload = record(contention={
        "same_file": True, "overlapping_hunks": False, "same_authoritative_object": False})
    assert state_of(payload, tmp_path) == "STARTABLE"


def test_5_different_files_one_authoritative_object_is_contended(tmp_path):
    """different files != independent authoritative objects."""
    payload = record(
        contention={"same_file": False, "overlapping_hunks": False,
                    "same_authoritative_object": True},
        next_recheck_trigger="the concurrent change to that object lands or closes")
    assert state_of(payload, tmp_path) == "BLOCKED_BY_CONTENTION"


def test_6_clean_merge_with_reversed_execution_order_is_blocked(tmp_path):
    """Git being happy is evidence about text, not about ordering."""
    payload = record(
        contention={**CLEAR_CONTENTION, "valid_execution_order": False},
        next_recheck_trigger="predecessor control becomes effective")
    result = run(payload, tmp_path)
    assert json.loads(result.stdout)["assessments"][0]["implementation_state"] == \
        "BLOCKED_BY_CONTENTION"
    assert any("clean textual merge" in b
               for b in json.loads(result.stdout)["assessments"][0]["blockers"])


def test_7_designable_but_blocked_may_not_report_startable(tmp_path):
    """The guard-failure case: design readiness must not be fused with implementation readiness."""
    refuses(record(design_state="BLOCKED"), tmp_path, "DESIGNABLE != STARTABLE runs both ways")


# ------------------------------------------------------- unknown is not satisfied


@pytest.mark.parametrize("missing", sorted(ALL_TRUE))
def test_an_absent_conjunct_is_unknown_and_blocks(tmp_path, missing):
    conjuncts = {k: v for k, v in ALL_TRUE.items() if k != missing}
    payload = record(conjuncts=conjuncts, next_recheck_trigger="the conjunct is evidenced")
    result = run(payload, tmp_path)
    assessment = json.loads(result.stdout)["assessments"][0]
    assert assessment["implementation_state"] != "STARTABLE"
    assert any(f"{missing} is UNKNOWN" in b for b in assessment["blockers"])


@pytest.mark.parametrize("untruthy", ["true", 1, "assumed", None, "PROPOSED"])
def test_only_an_explicit_boolean_true_satisfies_a_conjunct(tmp_path, untruthy):
    """A string, a number and a null are all NOT satisfied. Assumed is not evidenced."""
    payload = record(conjuncts={**ALL_TRUE, "task_context_coherent": untruthy},
                     next_recheck_trigger="task context is evidenced")
    assert state_of(payload, tmp_path) == "BLOCKED_BY_TASK_CONTEXT"


def test_unassessed_contention_blocks(tmp_path):
    payload = record(contention=None, next_recheck_trigger="contention is assessed")
    result = run(payload, tmp_path)
    assert json.loads(result.stdout)["assessments"][0]["implementation_state"] == \
        "BLOCKED_BY_CONTENTION"
    assert any("unassessed boundary" in b
               for b in json.loads(result.stdout)["assessments"][0]["blockers"])


def test_a_partial_contention_report_is_refused(tmp_path):
    refuses(record(contention={"same_file": True}), tmp_path, "missing dimension")


# ---------------------------------------------------------- reassessment triggers


def test_a_blocked_assessment_must_name_its_recheck_trigger(tmp_path):
    """Polling without a state change must not turn BLOCKED into STARTABLE."""
    payload = record(contention={"same_file": False, "overlapping_hunks": True,
                                 "same_authoritative_object": False})
    stderr = refuses(payload, tmp_path, "no next_recheck_trigger")
    assert "polling alone turns BLOCKED into STARTABLE" in stderr


def test_a_dependency_without_an_as_of_ref_is_refused(tmp_path):
    payload = record(dependencies=[{
        "class": "BYTE_DEPENDENCY", "resolved": True, "projection": "EFFECTIVE_MAIN"}])
    refuses(payload, tmp_path, "no as_of_ref")


def test_an_unknown_dependency_class_is_refused(tmp_path):
    payload = record(dependencies=[{
        "class": "VIBES", "resolved": False, "projection": "EFFECTIVE_MAIN",
        "as_of_ref": "ace1e579"}])
    refuses(payload, tmp_path, "is not one of")


# -------------------------------------------------------- the selection rule


def test_selection_never_picks_a_blocked_item_when_nothing_is_startable(tmp_path):
    """Rule 5: never select a blocked item merely because no startable item remains."""
    blocked = record(work_package_id="SECB-WP-FWK-074",
                     dependencies=[{"class": "BYTE_DEPENDENCY", "resolved": False,
                                    "projection": "EFFECTIVE_MAIN", "as_of_ref": "ace1e579",
                                    "description": "parser on unmerged #134"}],
                     next_recheck_trigger="#134 merged")
    result = run([blocked], tmp_path, EFFECTIVE_REF="ace1e579597f768c34b222a91d66ed445dfe34d3")
    selection = json.loads(result.stdout)["selection"]
    assert selection["selected"] is None
    assert selection["blocking_frontier"][0]["work_package_id"] == "SECB-WP-FWK-074"
    assert result.returncode == 2, "nothing startable is a non-success outcome, not a quiet pass"


def test_selection_prefers_the_startable_item_and_reports_the_frontier(tmp_path):
    """The 2026-08-15 decision, reproduced: decline FWK-074, select FWK-070."""
    ref = "ace1e579597f768c34b222a91d66ed445dfe34d3"
    blocked = record(work_package_id="SECB-WP-FWK-074", as_of_ref=ref,
                     dependencies=[{"class": "BYTE_DEPENDENCY", "resolved": False,
                                    "projection": "EFFECTIVE_MAIN", "as_of_ref": ref,
                                    "description": "parser on unmerged #134"}],
                     next_recheck_trigger="#134 merged")
    startable = record(work_package_id="SECB-WP-FWK-070", as_of_ref=ref)
    selection = json.loads(run([blocked, startable], tmp_path,
                               EFFECTIVE_REF=ref).stdout)["selection"]
    assert selection["selected"] == "SECB-WP-FWK-070"
    assert selection["startable"] == ["SECB-WP-FWK-070"]
    assert [f["work_package_id"] for f in selection["blocking_frontier"]] == ["SECB-WP-FWK-074"]


def test_a_stale_assessment_is_excluded_from_selection(tmp_path):
    """Rule 2: an assessment made against a superseded ref cannot select work now."""
    stale = record(work_package_id="SECB-WP-FWK-070", as_of_ref="f5aa26aef862")
    selection = json.loads(run([stale], tmp_path,
                               EFFECTIVE_REF="ace1e579597f").stdout)["selection"]
    assert selection["selected"] is None
    assert selection["excluded_stale"] == ["SECB-WP-FWK-070"]


def test_the_resolver_confers_no_authority(tmp_path):
    report = json.loads(run(record(), tmp_path).stdout)
    assert report["confers_work_authority"] is False
    assert any("recommends and grants nothing" in n
               for n in report["assessments"][0]["not_proven"])


def test_missing_assessments_input_is_refused(tmp_path):
    result = subprocess.run([sys.executable, str(TOOL)], capture_output=True, text=True,
                            check=False, env={**os.environ, "ASSESSMENTS": "",
                                              "PYTHONDONTWRITEBYTECODE": "1"})
    assert result.returncode == 2
    assert "ASSESSMENTS is required" in result.stderr
