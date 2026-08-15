"""The control execution graph is derived from the workflow — `SECB-WP-FWK-082` (#147).

    STATIC_EXECUTION_GRAPH ↔ RUNTIME_EXECUTION_RECEIPT ↔ CONTROL_SURFACE_REGISTRY

Discovery by filename was wrong in both directions and both were live: an `emit_*` script
invoked by CI escaped classification, and a `check_*` script no workflow invokes would be
claimed as CI enforcement. These tests assert the graph decides instead — and, just as
importantly, that a **static** graph never reports a runtime fact.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check_control_graph.py"
REGISTRY = REPO_ROOT / "config" / "control_surface.json"

OK = 0
FAIL = 2

WORKFLOW = """\
name: fixture
on:
  pull_request:

jobs:
  plain-gate:
    name: "Plain"
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run the budget gate
        run: python scripts/check_budget.py

  guarded-gate:
    name: "Guarded"
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - name: Run the dual policy check
        run: python scripts/check_dual_policy.py
"""


def graph(tmp_path, workflow: str = WORKFLOW, registry: str | None = None) -> dict:
    result = run(tmp_path, workflow, registry)
    assert result.returncode == OK, result.stderr
    return json.loads(result.stdout)


def run(tmp_path, workflow: str = WORKFLOW, registry: str | None = None):
    path = tmp_path / "ci.yml"
    path.write_text(workflow, encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True, text=True, timeout=30, cwd=str(REPO_ROOT),
        env={"PATH": "/usr/bin:/bin", "WORKFLOW": str(path),
             "REGISTRY": registry or str(REGISTRY)},
    )


def path_for(document: dict, script: str) -> dict:
    matches = [p for p in document["paths"] if p["path"].endswith(script)]
    assert matches, f"{script} not discovered: {[p['path'] for p in document['paths']]}"
    return matches[0]


# --- the real workflow --------------------------------------------------------


def test_the_repository_workflow_parses_and_every_invoked_control_is_accounted(tmp_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT)], capture_output=True, text=True, timeout=30,
        cwd=str(REPO_ROOT), env={"PATH": "/usr/bin:/bin"},
    )
    assert result.returncode == OK, result.stderr
    document = json.loads(result.stdout)
    assert len(document["paths"]) >= 7
    assert document["parse_fidelity"]["level"] == "SUBSET"


# --- reachability is three-valued ---------------------------------------------


def test_an_unguarded_step_is_unconditionally_reachable(tmp_path):
    assert path_for(graph(tmp_path), "check_budget.py")["status"]["REACHABLE"] == "UNCONDITIONAL"


def test_a_job_level_condition_makes_the_path_conditional(tmp_path):
    """A conditionally-skipped job reports success and does not block a merge.

    So "the path exists" and "the path runs" are different claims, and collapsing them is
    how a required check comes to certify nothing.
    """
    assert path_for(graph(tmp_path), "check_dual_policy.py")["status"]["REACHABLE"] == "CONDITIONAL"


def test_a_step_level_condition_makes_the_path_conditional(tmp_path):
    workflow = WORKFLOW.replace(
        "      - name: Run the budget gate\n",
        "      - name: Run the budget gate\n        if: always()\n")
    assert path_for(graph(tmp_path, workflow), "check_budget.py")["status"]["REACHABLE"] == "CONDITIONAL"


def test_a_needs_edge_makes_the_path_conditional(tmp_path):
    """A dependency failure can skip the downstream job."""
    workflow = WORKFLOW.replace(
        "  plain-gate:\n    name: \"Plain\"\n",
        "  plain-gate:\n    name: \"Plain\"\n    needs: [guarded-gate]\n")
    assert path_for(graph(tmp_path, workflow), "check_budget.py")["status"]["REACHABLE"] == "CONDITIONAL"


# --- what a static parser must never claim ------------------------------------


@pytest.mark.parametrize("field", ["EXECUTED", "NORMATIVELY_CONSUMED"])
def test_runtime_statuses_are_never_inferred_from_the_graph(tmp_path, field):
    """`DISCOVERED` is not `EXECUTED`. The field exists to stop that inference."""
    for record in graph(tmp_path)["paths"]:
        assert record["status"][field] == "NOT_OBSERVED"


def test_enforcement_is_not_claimed(tmp_path):
    for record in graph(tmp_path)["paths"]:
        assert record["status"]["ENFORCED"] == "NOT_OBSERVED"


def test_continue_on_error_proves_the_result_does_not_propagate(tmp_path):
    """The one runtime-ish fact that IS static: the step cannot fail its job."""
    workflow = WORKFLOW.replace(
        "      - name: Run the budget gate\n",
        "      - name: Run the budget gate\n        continue-on-error: true\n")
    record = path_for(graph(tmp_path, workflow), "check_budget.py")
    assert record["continue_on_error"] is True
    assert record["status"]["RESULT_PROPAGATED"] is False


def test_a_normal_step_leaves_propagation_unobserved(tmp_path):
    assert path_for(graph(tmp_path), "check_budget.py")["status"]["RESULT_PROPAGATED"] == "NOT_OBSERVED"


# --- edges the parser cannot follow are reported, never dropped ---------------


def test_an_external_action_is_reported_as_an_unresolved_edge(tmp_path):
    kinds = {e["kind"] for e in graph(tmp_path)["unresolved_edges"]}
    assert "EXTERNAL_ACTION" in kinds


def test_a_local_composite_action_is_reported(tmp_path):
    """It adds execution edges the calling workflow does not show."""
    workflow = WORKFLOW.replace("      - uses: actions/checkout@v4",
                                "      - uses: ./.github/actions/local-thing")
    edges = [e for e in graph(tmp_path, workflow)["unresolved_edges"]
             if e["kind"] == "COMPOSITE_ACTION"]
    assert edges and "local-thing" in edges[0]["value"]


def test_a_matrix_is_reported_as_dynamic(tmp_path):
    workflow = WORKFLOW.replace("    runs-on: ubuntu-latest\n",
                                "    strategy:\n      matrix:\n        v: [1, 2]\n    runs-on: ubuntu-latest\n", 1)
    kinds = {e["kind"] for e in graph(tmp_path, workflow)["unresolved_edges"]}
    assert "UNRESOLVED_DYNAMIC_EDGE" in kinds


def test_an_interpolated_invocation_is_reported_as_dynamic(tmp_path):
    """An interpolated target is not statically fixed, so it is not silently trusted."""
    workflow = WORKFLOW.replace(
        "        run: python scripts/check_budget.py",
        "        run: python scripts/check_budget.py ${{ github.event.number }}")
    edges = [e for e in graph(tmp_path, workflow)["unresolved_edges"]
             if e["kind"] == "UNRESOLVED_DYNAMIC_EDGE"]
    assert edges


# --- the registry cross-check, in the direction that was broken ---------------


def test_an_invoked_but_unclassified_control_is_refused(tmp_path):
    """The `emit_*` case: invoked by CI, invisible to a filename glob."""
    workflow = WORKFLOW.replace("scripts/check_budget.py", "scripts/emit_something_new.py")
    result = run(tmp_path, workflow)
    assert result.returncode == FAIL
    assert "emit_something_new.py" in result.stderr
    assert "does not match a pattern" in result.stderr


def test_a_script_no_workflow_invokes_is_not_claimed_as_enforcement(tmp_path):
    """The other direction: `check_*` on disk is not evidence of CI enforcement."""
    discovered = {p["path"] for p in graph(tmp_path)["paths"]}
    assert "scripts/check_identity_receipt.py" not in discovered
    assert "scripts/check_control_graph.py" not in discovered


# --- fail-closed --------------------------------------------------------------


def test_an_absent_workflow_fails_closed():
    result = subprocess.run(
        [sys.executable, str(SCRIPT)], capture_output=True, text=True, timeout=30,
        cwd=str(REPO_ROOT), env={"PATH": "/usr/bin:/bin", "WORKFLOW": "/nonexistent/ci.yml"},
    )
    assert result.returncode == FAIL
    assert "REFUSED (closed)" in result.stderr


def test_an_unparseable_registry_fails_closed(tmp_path):
    broken = tmp_path / "registry.json"
    broken.write_text("{not json", encoding="utf-8")
    result = run(tmp_path, registry=str(broken))
    assert result.returncode == FAIL
    assert "REFUSED (closed)" in result.stderr


def test_the_parser_declares_its_fidelity_rather_than_implying_completeness(tmp_path):
    fidelity = graph(tmp_path)["parse_fidelity"]
    assert fidelity["level"] == "SUBSET"
    assert "NFR-12" in fidelity["why"]
    assert set(fidelity["recognised"]) >= {"jobs", "steps", "run", "uses", "if", "needs"}
