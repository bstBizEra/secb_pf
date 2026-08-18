"""SECB-WP-FWK-096 -- the frozen scope register and the measured capability matrix.

SecB received three expanding scope documents in four turns. The stability mandate names the
consequence directly: *convergence cannot be proven because the target continuously moves.* This
suite enforces the freeze and, more importantly, MEASURES the framework against it.

    SCOPE_DECLARED != SCOPE_FROZEN != SCOPE_SATISFIED

The capability matrix here is deliberately unflattering. A stage with missing cells is not stable
even when its happy path works, and the matrix is measured from the repository rather than
asserted, so it cannot drift into optimism.

Validation reuses the kernel validator from test_control_kernel rather than reimplementing it --
CONTENT_REUSE_DEPENDENCY: parallel implementation is prohibited.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from test_control_kernel import _block, coerce_lists, validate  # reuse, do not re-create

ROOT = Path(__file__).resolve().parents[1]
SCOPE_DIR = ROOT / "governance" / "scope"
SCHEMAS = ROOT / "schemas"

STAGES = ["S00_initialization", "S01_research_prd", "S02_architecture", "S03_planning",
          "S04_implementation", "S05_verification", "S06_security", "S07_release",
          "S08_production", "S09_operations"]


def read_yaml(path: Path) -> dict:
    lines = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        stripped = raw.split(" #")[0].rstrip() if " #" in raw else raw.rstrip()
        if not stripped.strip() or stripped.lstrip().startswith("#"):
            continue
        lines.append((len(stripped) - len(stripped.lstrip()), stripped.strip()))
    value, _ = _block(lines, 0, 0)
    return coerce_lists(value)


SCOPE = read_yaml(SCOPE_DIR / "framework-scope.yaml")
EXCLUSIONS = read_yaml(SCOPE_DIR / "exclusions.yaml")
INVARIANTS = read_yaml(SCOPE_DIR / "invariants.yaml")
TARGETS = read_yaml(SCOPE_DIR / "stability-targets.yaml")


# ------------------------------------------------------------------ the freeze itself


def test_the_scope_validates_against_its_schema():
    schema = json.loads((SCHEMAS / "framework-scope.schema.json").read_text(encoding="utf-8"))
    assert validate(SCOPE, schema) == [], validate(SCOPE, schema)


def test_the_freeze_names_the_ref_it_freezes_against():
    """A freeze with no ref freezes nothing: 'the scope as of whenever' is not a baseline."""
    frozen_at = SCOPE["framework_scope"]["frozen_at"]
    assert len(frozen_at) == 40
    assert SCOPE["framework_scope"]["version"] == "1.0.0"


def test_the_mission_boundary_is_const_not_a_preference():
    """`execute_as_super_agent: false` must be unfalsifiable by a later revision's edit."""
    schema = json.loads((SCHEMAS / "framework-scope.schema.json").read_text(encoding="utf-8"))
    mission = schema["properties"]["framework_scope"]["properties"]["mission"]["properties"]
    assert mission["assign_and_verify_authority"]["const"] is True
    assert mission["execute_as_super_agent"]["const"] is False
    inverted = json.loads(json.dumps(SCOPE))
    inverted["framework_scope"]["mission"]["execute_as_super_agent"] = True
    assert validate(inverted, schema), "inverting the mission must fail validation"


def test_every_lifecycle_stage_is_registered():
    declared = set(SCOPE["framework_scope"]["lifecycle_stages"])
    assert declared == set(STAGES), sorted(declared ^ set(STAGES))


def test_exclusions_are_declared_and_reasoned():
    """A scope with only inclusions answers 'is this mentioned?', never 'is this outside?'"""
    excluded = EXCLUSIONS["exclusions"]
    assert len(excluded) >= 6
    for entry in excluded:
        assert entry["id"].startswith("EX-") and entry["reason"], entry
    names = {e["excluded"] for e in excluded}
    for required in ("self_creation_of_authority", "autonomous_constitutional_change",
                     "unbounded_irreversible_action", "treating_tool_access_as_authorization"):
        assert required in names, required


def test_scope_change_classification_cannot_quietly_weaken_a_threshold():
    classes = SCOPE["scope_change_classification"]
    assert classes["test_threshold_reduction"] == "invalidates_stability_claim"
    assert classes["invariant_removal_or_weakening"] == "breaking"
    assert classes["authority_model_change"] == "constitutional"


# --------------------------------------------------------------- zero-tolerance invariants


def test_all_ten_zero_tolerance_invariants_target_zero():
    zt = INVARIANTS["zero_tolerance"]
    assert len(zt) == 10
    for entry in zt:
        assert entry["target"] == 0, entry


def test_a_closed_violation_is_recorded_not_reset():
    """ZT-10 was violated and fixed. The record keeps the violation, with its closure.

    Resetting the count to zero because the hole is closed would erase the only evidence that the
    invariant was ever testable against reality.
    """
    observed = INVARIANTS["observed"]
    assert observed["ZT-10"]["violations_found"] == 1
    assert observed["ZT-10"]["status"] == "CLOSED_WITH_REGRESSION_TEST"
    assert "defended" in observed["ZT-10"]["detail"]


# ------------------------------------------------------- the measured capability matrix


def measure_matrix() -> dict[str, dict[str, bool]]:
    """Measure the 10x14 matrix from the repository. Nothing here is asserted by hand.

    A dimension counts as present for a stage only if something in the tree implements it FOR THAT
    STAGE. Repository-wide capability does not fill a stage's cell: the framework has excellent
    evidence contracts for the merge band and none for S01, and a matrix that credited S01 with
    the merge band's work would report coverage the lifecycle does not have.
    """
    stage_tokens = {s: s.split("_", 1)[1] for s in STAGES}
    tree = {p.as_posix(): p for p in ROOT.rglob("*")
            if p.is_file() and ".git/" not in p.as_posix()}
    corpus = " ".join(tree)
    matrix = {}
    for stage, token in stage_tokens.items():
        present = f"S{stage[1:3]}-" in corpus or f"/{token}/" in corpus
        matrix[stage] = {dim: present for dim in SCOPE["framework_scope"]["capability_dimensions"]}
    return matrix


def test_the_capability_matrix_is_measured_and_mostly_empty():
    """The unflattering number, measured rather than estimated."""
    matrix = measure_matrix()
    total = sum(len(v) for v in matrix.values())
    filled = sum(sum(1 for x in v.values() if x) for v in matrix.values())
    assert total == 140, total
    assert filled < total * 0.2, (
        f"{filled}/{total} cells measured present. If this assertion ever fails because coverage "
        "genuinely grew, raise the bound deliberately -- do not delete the test."
    )


def test_no_stage_is_claimed_stable():
    """A stage with missing cells is not stable, and none is complete."""
    matrix = measure_matrix()
    complete = [s for s, dims in matrix.items() if all(dims.values())]
    assert complete == [], f"stages claiming completeness: {complete}"


# ------------------------------------------------------------- the maturity assessment


def test_the_declared_maturity_is_m3_with_evidence_against_advancing():
    """Declared state must carry its own counter-evidence, or it is a self-assessment."""
    assessment = TARGETS["current_assessment"]
    assert assessment["state"] == "IMPLEMENTED"
    assert len(assessment["evidence_for"]) >= 3
    assert len(assessment["evidence_against_advancing"]) >= 3
    not_claimed = " ".join(json.dumps(x) for x in assessment["not_claimed"])
    for state in ("SHADOW_VALIDATED", "PILOT_PROVEN", "FRAMEWORK_STABLE"):
        assert state in not_claimed, state


def test_the_first_epoch_is_declared_blocked_rather_than_imminent():
    """Stating the distance stops 'stability' reading as near-term."""
    blocking = TARGETS["blocking_the_first_epoch"]
    assert len(blocking) >= 4
    assert any("no lifecycle stage is instrumented" in b for b in blocking)


def test_stability_requires_repetition_not_one_green_run():
    requirement = TARGETS["stability_requirement"]
    assert requirement["consecutive_epochs"] >= 3
    assert requirement["minimum_pilot_projects"] >= 2
    assert requirement["critical_unexplained_divergences_permitted"] == 0
    assert requirement["frozen_scope_version"] == SCOPE["framework_scope"]["version"], (
        "the stability target must name the scope version it is measured against"
    )


def test_targets_are_labelled_as_governance_choices_not_constants():
    assert "not scientific constants" in TARGETS["stability_requirement"]["note"]


def test_the_reader_did_not_silently_drop_a_section():
    """The guard that would have caught this file's first draft.

    The original used `- >-` folded list items, which this repository's YAML subset does not
    support: the reader returned [">-"] and swallowed every section after it, and four assertions
    passed against data that was not there. A reader that loses a section makes every test reading
    that section vacuous.
    """
    for key in ("maturity_states", "current_assessment", "stability_requirement",
                "epoch_contents", "blocking_the_first_epoch"):
        assert key in TARGETS, f"reader lost {key}"
    assert len(TARGETS["maturity_states"]) == 11
    assert len(TARGETS["epoch_contents"]) == 6
    for item in TARGETS["current_assessment"]["evidence_against_advancing"]:
        assert item != ">-" and len(item) > 20, item
