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


def test_a_step_without_an_if_is_recorded_as_observed_not_unconditional(tmp_path):
    """`C-CEG-04`. GitHub applies a default `success()` condition to every step.

    A previous step's failure skips it, so the absence of an explicit condition is an
    observation about the file — never a guarantee about execution. The word
    `UNCONDITIONAL` is gone from the vocabulary for that reason.
    """
    assert path_for(graph(tmp_path), "check_budget.py")["axes"]["CI_REACHABILITY"] == "NO_EXPLICIT_CONDITION_OBSERVED"


def test_a_job_level_condition_makes_the_path_conditional(tmp_path):
    """A conditionally-skipped job reports success and does not block a merge.

    So "the path exists" and "the path runs" are different claims, and collapsing them is
    how a required check comes to certify nothing.
    """
    assert path_for(graph(tmp_path), "check_dual_policy.py")["axes"]["CI_REACHABILITY"] == "EXPLICIT_CONDITION_PRESENT"


def test_a_step_level_condition_makes_the_path_conditional(tmp_path):
    workflow = WORKFLOW.replace(
        "      - name: Run the budget gate\n",
        "      - name: Run the budget gate\n        if: always()\n")
    assert path_for(graph(tmp_path, workflow), "check_budget.py")["axes"]["CI_REACHABILITY"] == "EXPLICIT_CONDITION_PRESENT"


def test_a_needs_edge_makes_the_path_conditional(tmp_path):
    """A dependency failure can skip the downstream job."""
    workflow = WORKFLOW.replace(
        "  plain-gate:\n    name: \"Plain\"\n",
        "  plain-gate:\n    name: \"Plain\"\n    needs: [guarded-gate]\n")
    assert path_for(graph(tmp_path, workflow), "check_budget.py")["axes"]["CI_REACHABILITY"] == "EXPLICIT_CONDITION_PRESENT"


# --- what a static parser must never claim ------------------------------------


def test_the_four_axes_are_separate(tmp_path):
    """`C-CEG-05`. Membership, reachability, consumption and enforcement are not one fact."""
    axes = path_for(graph(tmp_path), "check_budget.py")["axes"]
    assert set(axes) == {
        "CONTROL_SURFACE_MEMBERSHIP", "CI_REACHABILITY", "EXECUTION_OBSERVED",
        "RESULT_CONSUMPTION", "CI_ENFORCEMENT",
    }
    assert axes["CONTROL_SURFACE_MEMBERSHIP"] in {"TRACKED", "EXCLUDED", "UNACCOUNTED"}


def test_runtime_facts_are_never_inferred_from_the_graph(tmp_path):
    for record in graph(tmp_path)["paths"]:
        assert record["axes"]["EXECUTION_OBSERVED"] == "NOT_OBSERVED"
        assert record["axes"]["CI_ENFORCEMENT"] == "NOT_OBSERVED"


def test_continue_on_error_proves_only_direct_failure_propagation(tmp_path):
    """`C-CEG-03`. It does not prove nobody read the outcome.

    A later step can still read `steps.<id>.outcome`, so the two claims are recorded
    separately: one is proven, the other is not observed.
    """
    workflow = WORKFLOW.replace(
        "      - name: Run the budget gate\n",
        "      - name: Run the budget gate\n        continue-on-error: true\n")
    consumption = path_for(graph(tmp_path, workflow), "check_budget.py")["axes"]["RESULT_CONSUMPTION"]
    assert consumption["DIRECT_JOB_FAILURE_PROPAGATION"] is False
    assert consumption["DOWNSTREAM_RESULT_CONSUMPTION"] == "NOT_OBSERVED"


def test_a_normal_step_leaves_both_consumption_facts_unobserved(tmp_path):
    consumption = path_for(graph(tmp_path), "check_budget.py")["axes"]["RESULT_CONSUMPTION"]
    assert consumption["DIRECT_JOB_FAILURE_PROPAGATION"] == "NOT_OBSERVED"
    assert consumption["DOWNSTREAM_RESULT_CONSUMPTION"] == "NOT_OBSERVED"


def test_unrecognised_syntax_is_reported_and_forces_unproven_reachability(tmp_path):
    """`C-CEG-02`. Silently skipping an unknown key is what made the old claim untrue."""
    workflow = WORKFLOW.replace(
        "        run: python scripts/check_budget.py",
        "        run: python scripts/check_budget.py\n        unknown-future-key: yes")
    document = graph(tmp_path, workflow)
    kinds = {e["kind"] for e in document["unresolved_edges"]}
    assert "UNRECOGNISED_SYNTAX" in kinds
    assert path_for(document, "check_budget.py")["axes"]["CI_REACHABILITY"] == (
        "REACHABILITY_NOT_PROVEN"
    )


def test_a_yaml_alias_is_reported_as_a_blind_spot(tmp_path):
    """An alias can import an entire job, so an indentation parser may miss a path."""
    workflow = WORKFLOW.replace("  plain-gate:\n", "  plain-gate: &base\n")
    kinds = {e["kind"] for e in graph(tmp_path, workflow)["unresolved_edges"]}
    assert "YAML_ANCHOR_OR_ALIAS" in kinds


def test_a_statically_false_condition_is_unreachable(tmp_path):
    workflow = WORKFLOW.replace("    if: github.event_name == 'pull_request'", "    if: false")
    assert path_for(graph(tmp_path, workflow), "check_dual_policy.py")["axes"]["CI_REACHABILITY"] == (
        "STATICALLY_UNREACHABLE"
    )


def test_nested_mapping_keys_are_not_mistaken_for_step_keys(tmp_path):
    """Regression: `with:` and `env:` children are not unrecognised step keys.

    The first version flagged `python-version` and every environment variable, forcing
    REACHABILITY_NOT_PROVEN on every path in the real workflow. A guard that always says
    "not proven" is one nobody reads, and it was found by looking at the output rather
    than by a green test.
    """
    workflow = WORKFLOW.replace(
        "      - uses: actions/checkout@v4",
        "      - uses: actions/setup-python@v5\n        with:\n          python-version: \"3.12\"")
    document = graph(tmp_path, workflow)
    assert not [e for e in document["unresolved_edges"] if e["kind"] == "UNRECOGNISED_SYNTAX"]
    assert path_for(document, "check_budget.py")["axes"]["CI_REACHABILITY"] == (
        "NO_EXPLICIT_CONDITION_OBSERVED"
    )


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


def test_the_guard_uses_the_parser_rather_than_a_second_regex(tmp_path):
    """`C-CEG-01`. One discovery implementation, or the guard enforces the weaker one."""
    guard = (REPO_ROOT / "tests" / "test_control_surface.py").read_text(encoding="utf-8")
    assert "from check_control_graph import invoked_scripts" in guard
    assert "re.findall(r\"scripts/" not in guard, (
        "the guard must not re-derive the invoked set with its own pattern"
    )


def test_the_parser_declares_its_fidelity_rather_than_implying_completeness(tmp_path):
    fidelity = graph(tmp_path)["parse_fidelity"]
    assert fidelity["level"] == "SUBSET"
    assert "NFR-12" in fidelity["why"]
    assert set(fidelity["recognised"]) >= {"jobs", "steps", "run", "uses", "if", "needs"}
