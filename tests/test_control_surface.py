"""Drift guard for `config/control_surface.json` (`SECB-WP-FWK-052`).

The manifest lets an instantiated project compute whether a control it copied
has been fixed since -- which only works if the digests describe the tree that
actually ships. A manifest recording a control's state as of three fixes ago
answers the staleness question wrongly and confidently: worse than not
answering it. So every declared digest is recomputed here, on the pattern of
`tests/test_sealed_evidence.py`.

The two guards differ in kind. Sealed evidence protects bytes that must NEVER
change (a certification voids if they do); this protects a *description* of
bytes that change often, so a mismatch is not a violation -- it is an un-bumped
manifest, and the failure message says so.

The rest is the `§P1` lesson from the negative-test catalogue: a test asserting
a hole exists reddens CI the day someone fixes the hole. Deliberate exclusions
are therefore checked against the manifest's *declared* list rather than a
literal set written here, so covering `ci.yml` later is one deliberate edit
instead of an unexpected failure.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "config" / "control_surface.json"

MANIFEST = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
CONTROLS = MANIFEST["controls"]
EXCLUSIONS = MANIFEST["declared_exclusions"]

# The four scripts `docs/15-runbooks/NEW_PROJECT_BOOTSTRAP.md` lists under
# "Reusable as-is -- the framework". Written literally rather than parsed out of
# the markdown: a test that derives its expectations from the document it is
# checking passes whatever that document says, which is no check at all.
RUNBOOK_REUSABLE_SCRIPTS = {
    "scripts/check_work_package_ref.py",
    "scripts/check_budget.py",
    "scripts/classify_authority_delta.py",
    "scripts/check_dual_policy.py",
}

REQUIRED_CONTROL_FIELDS = (
    "path",
    "sha256",
    "bytes",
    "owning_work_package",
    "last_changed_commit",
    "portability_class",
    "field_observation",
    "staleness_consequence",
)


def digest(path: Path) -> tuple[str, int]:
    payload = path.read_bytes()
    return hashlib.sha256(payload).hexdigest(), len(payload)


def by_class(name: str) -> list[dict]:
    return [c for c in CONTROLS if c["portability_class"] == name]


# --- the manifest describes the tree that ships -----------------------------


@pytest.mark.parametrize("control", CONTROLS, ids=lambda c: c["path"])
def test_every_declared_control_exists(control):
    target = REPO_ROOT / control["path"]
    assert target.is_file(), (
        f"{control['path']} is declared in config/control_surface.json but is not "
        "in the tree. Either the control was moved or removed and the manifest was "
        "not updated, or the path is a typo -- in both cases a downstream comparing "
        "digests against this manifest gets a wrong answer."
    )


@pytest.mark.parametrize("control", CONTROLS, ids=lambda c: c["path"])
def test_declared_digests_match_the_tree(control):
    sha, size = digest(REPO_ROOT / control["path"])
    assert sha == control["sha256"] and size == control["bytes"], (
        f"\n{control['path']} has changed since config/control_surface.json was "
        f"written.\n"
        f"  recorded: {control['sha256']} ({control['bytes']} bytes)\n"
        f"  actual:   {sha} ({size} bytes)\n\n"
        f"This is not a violation -- it means the manifest was not bumped with the "
        f"change. Update the sha256, bytes, owning_work_package and "
        f"last_changed_commit for this entry in the same pull request that changed "
        f"the control. Until you do, any project instantiated from this framework "
        f"that compares its copy against this manifest is told it is up to date "
        f"when it is not, which is the exact failure SECB-WP-FWK-052 exists to "
        f"remove.\n"
        f"  currently recorded as owned by: {control['owning_work_package']}"
    )


def test_mismatch_message_names_the_owning_work_package():
    # Acceptance criterion 2. A drift guard whose failure does not say what to
    # do is a puzzle rather than a guard, so the diagnostic content is itself
    # part of the deliverable and is asserted rather than assumed.
    for control in CONTROLS:
        assert control["owning_work_package"].startswith("SECB-WP-"), (
            f"{control['path']} records owning_work_package="
            f"{control['owning_work_package']!r}; the drift-failure message quotes "
            "this field, so a value that is not a work-package ID sends the reader "
            "nowhere."
        )
        assert control["last_changed_commit"], (
            f"{control['path']} has no last_changed_commit, so a reader cannot "
            "find the change the digest describes."
        )


# --- the vocabulary is closed ----------------------------------------------


def test_portability_class_vocabulary_is_closed():
    declared = set(MANIFEST["portability_classes"])
    assert declared == {"verbatim", "configure", "adapt", "do_not_copy"}, (
        "The portability vocabulary changed. Adding a class is a governance edit: "
        "every consumer of this manifest branches on these four values, and a "
        "fifth one silently means 'unhandled'."
    )
    for entry in [*CONTROLS, *EXCLUSIONS]:
        assert entry["portability_class"] in declared, (
            f"{entry['path']} declares portability_class="
            f"{entry['portability_class']!r}, which is not in the manifest's own "
            f"vocabulary {sorted(declared)}."
        )


def test_manifest_required_fields_are_non_empty():
    for control in CONTROLS:
        for field in REQUIRED_CONTROL_FIELDS:
            assert control.get(field) not in (None, "", 0), (
                f"{control.get('path', '<no path>')} is missing a value for "
                f"{field!r}. Every field here is read by a human deciding whether "
                "to re-apply an upstream change; an empty one makes that decision "
                "on incomplete information."
            )


# --- the manifest covers what the runbook tells people to copy -------------


def test_runbook_reusable_scripts_are_all_tracked():
    # Acceptance criterion 4, and the whole point of the work package: a control
    # the runbook tells you to copy but the manifest does not track is precisely
    # the gap that let a fixed defect stay live in an instantiated project.
    tracked = {c["path"] for c in CONTROLS}
    missing = RUNBOOK_REUSABLE_SCRIPTS - tracked
    assert not missing, (
        "docs/15-runbooks/NEW_PROJECT_BOOTSTRAP.md lists these under 'Reusable "
        f"as-is' but config/control_surface.json does not track them: "
        f"{sorted(missing)}. A downstream copying them cannot compute whether they "
        "have been fixed since."
    )


def test_every_enforcement_script_is_either_tracked_or_declared_excluded():
    # No path unclassified -- the runbook's rule, applied to the manifest. A new
    # enforcement script must be a deliberate decision (tracked, or excluded
    # with a trigger), never an omission nobody noticed.
    #
    # Discovery is by EXECUTION PATH, not by filename (SECB-WP-FWK-082, #147). The
    # previous version globbed `check_*.py`, which was wrong in both directions and
    # both were live: `scripts/emit_pr_input_binding.py` is invoked by ci.yml on #134
    # and escaped classification entirely, while `scripts/check_identity_receipt.py`
    # matches the glob although no workflow invokes it. What a control IS cannot be
    # decided by what it is called.
    # The graph parser IS the discovery implementation; this guard does not re-derive
    # the set with a second regex. Two implementations of "which controls does CI
    # invoke" disagree eventually, and the guard would enforce the weaker one (C-CEG-01).
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from check_control_graph import invoked_scripts_in

    # The UNION over all tracked workflows, not ci.yml alone (SECB-WP-FWK-082, #147).
    # A control invoked only by a second workflow would otherwise be invisible, and
    # SECB-WP-FWK-083 adds exactly such a workflow.
    on_disk = invoked_scripts_in(REPO_ROOT / ".github" / "workflows")
    assert on_disk, "no invoked scripts parsed -- the workflow directory shape changed"
    accounted = {c["path"] for c in CONTROLS} | {e["path"] for e in EXCLUSIONS}
    unaccounted = on_disk - accounted
    assert not unaccounted, (
        f"These enforcement scripts are in the tree but neither tracked nor "
        f"declared excluded in config/control_surface.json: {sorted(unaccounted)}. "
        "Add an entry to `controls` with its digest, or to `declared_exclusions` "
        "with a reason and a trigger to cover it."
    )


# --- deliberate exclusions are declared, not implicit ----------------------


def test_ci_workflow_exclusion_is_declared_not_implicit():
    # Acceptance criterion 5. Asserted against the manifest's declaration rather
    # than against a literal expectation, so that covering ci.yml later is one
    # deliberate edit and not a surprise CI failure (the §P1 lesson).
    paths = {e["path"] for e in EXCLUSIONS}
    assert ".github/workflows/ci.yml" in paths, (
        "The workflow is not covered by a digest and its exclusion is not "
        "declared, which makes the omission indistinguishable from an oversight."
    )
    for excluded in EXCLUSIONS:
        assert excluded.get("reason") and excluded.get("trigger_to_cover"), (
            f"{excluded['path']} is excluded without both a reason and a "
            "trigger_to_cover. An exclusion with no trigger is permanent by "
            "accident."
        )


def test_configure_class_controls_are_not_reported_as_staleness():
    # The envelope is meant to differ downstream. If the manifest ever claimed a
    # digest mismatch there implied staleness, it would flag every instantiated
    # project on day one -- and a guard that always fires is one nobody reads.
    assert MANIFEST["staleness_is_computable_only_for"] == "verbatim"
    for control in by_class("configure"):
        consequence = control["staleness_consequence"].lower()
        assert "none derivable" in consequence, (
            f"{control['path']} is configure-class, so nothing about staleness "
            "follows from its digest; its staleness_consequence must say so "
            "plainly rather than imply a downstream should re-apply anything."
        )


def test_the_deferred_normative_surface_manifest_is_not_quietly_being_built():
    # config/delegation_envelope.json defers a NormativeSurfaceManifest that
    # classifies AUTHORITY, behind a named trigger. This manifest classifies
    # PORTABILITY. Building the deferred thing without its trigger is the
    # over-engineering the minimality policy exists to refuse, so the boundary
    # is asserted rather than left to good intentions.
    boundary = MANIFEST["what_this_is_not"]["normative_surface_manifest"]
    assert "NOT the NormativeSurfaceManifest" in boundary
    authority_words = {"constitutional", "governing", "operational", "factual"}
    for control in CONTROLS:
        assert control["portability_class"] not in authority_words, (
            f"{control['path']} carries an authority classification in a "
            "portability field. The two vocabularies are separate on purpose."
        )
