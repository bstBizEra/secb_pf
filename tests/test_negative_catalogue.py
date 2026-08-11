"""Negative tests for the evasion scenarios in `docs/09-testing/NEGATIVE_TEST_CATALOGUE.md`.

`KN-001`: a gate counts only once proven to fail on a real pull request. Three
supplied specifications handed this project 33 evasion scenarios; the catalogue
maps them, and this module holds the ones implementable today.

Two of these tests **document a hole rather than defend against one.** They
assert current behaviour, so they fail if the hole is ever closed — and the
failure message says the catalogue is stale rather than that something broke.
A green suite here means *"the recorded coverage still holds"*, never *"no
evasion is possible"*. That distinction is the correction `SECB-WP-FWK-041`
was put through, applied to test semantics.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLASSIFIER = REPO_ROOT / "scripts" / "classify_authority_delta.py"

AUTO_APPROVED = 0
ESCALATES = 2


def classify(numstat: str, envelope: Path | None = None):
    env = {k: v for k, v in os.environ.items() if k not in ("ENVELOPE", "DIFF_TEXT")}
    if envelope:
        env["ENVELOPE"] = str(envelope)
    return subprocess.run(
        [sys.executable, str(CLASSIFIER)],
        input=numstat,
        capture_output=True,
        text=True,
        env=env,
        cwd=REPO_ROOT,
        timeout=30,
    )


def verdict_text(result) -> str:
    """The classifier prints a pass to stdout and an escalation to stderr.

    Reading only stdout is how a test can assert an escalation and pass on an
    empty string -- so the helper reads both, deliberately.
    """
    return result.stdout + result.stderr


# --- FPSA §15 case 2 / WICG rule 8: splitting to evade a class ---------------


def test_known_gap_splitting_a_change_evades_the_line_ceiling():
    """One change over the cap escalates; two halves each auto-approve.

    FPSA `FP-05` and WICG rule 8 both prohibit this, and nothing detects it:
    the classifier sees one diff at a time and has no notion of a sibling
    ticket. Recorded as a **gap**, locked by this test.

    If this test fails, a splitting detector has been added — update
    `NEGATIVE_TEST_CATALOGUE.md` scenario `FPSA-02` from GAP to COVERED.
    """
    whole = classify("700\t600\tdocs/a.md\n")
    assert whole.returncode == ESCALATES, "a 1300-line change must escalate"
    assert "exceeds the envelope cap" in verdict_text(whole)

    half_a = classify("300\t250\tdocs/a.md\n")
    half_b = classify("300\t250\tdocs/b.md\n")
    assert half_a.returncode == AUTO_APPROVED
    assert half_b.returncode == AUTO_APPROVED
    # 1100 lines of the same work, landed with no escalation, in two pieces.


# --- FPSA §15 case 3: authority-shaped data smuggled into configuration ------


def test_known_gap_a_new_config_file_classifies_as_low_risk():
    """`config/` is an `auto_path`; only two files in it are constitutional.

    So a new `config/permissions.json` auto-merges. This is not hypothetical:
    `SECB-WP-FWK-041` landed `config/identifier_taxonomy.json` at `G0` under
    exactly this rule, which is how the gap was found.

    If this test fails, `config/` classification has been tightened — update
    scenario `FPSA-03` and re-check that `FWK-041`'s registry still lands
    where its work package said it would.
    """
    result = classify("40\t0\tconfig/permissions.json\n")
    assert result.returncode == AUTO_APPROVED, (
        "gap closed: a new config file no longer auto-approves. Update the "
        "catalogue — and note that this changes where FWK-041's registry sits."
    )
    assert "G0" in verdict_text(result)


def test_the_two_named_config_files_are_still_constitutional():
    """The other half of the same rule, and this one is a defence.

    The gap above exists *because* the protection is enumerated by filename.
    That enumeration must at least hold for the two files it names.
    """
    for path in ("config/delegation_envelope.json", "config/ballot.schema.json"):
        result = classify(f"1\t0\t{path}\n")
        assert result.returncode == ESCALATES, f"{path} must not auto-approve"
        assert "CONSTITUTIONAL_REQUIRED" in verdict_text(result)


# --- FPSA §15 cases 6-8: authority, quorum, classifier, protected paths ------


def test_lowering_a_quorum_or_ceiling_cannot_auto_approve():
    """The envelope holds quorum and ceilings, and it is constitutional."""
    result = classify("2\t2\tconfig/delegation_envelope.json\n")
    assert result.returncode == ESCALATES
    assert "CONSTITUTIONAL_REQUIRED" in verdict_text(result)


def test_editing_the_classifier_to_lower_its_own_risk_cannot_auto_approve():
    """FPSA case 7. The classifier judging its own change is the core hazard."""
    result = classify("10\t4\tscripts/classify_authority_delta.py\n")
    assert result.returncode == ESCALATES
    assert "CONSTITUTIONAL_REQUIRED" in verdict_text(result)


def test_editing_ci_so_a_gate_stops_running_cannot_auto_approve():
    """FPSA case 12, first half: `.github/` is constitutional wholesale."""
    result = classify("0\t12\t.github/workflows/ci.yml\n")
    assert result.returncode == ESCALATES


# --- BACP §14 case 17: squash merge falsifies an ancestry check --------------


def git(*args: str, cwd: Path) -> str:
    out = subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", *args],
        cwd=cwd, capture_output=True, text=True, timeout=60,
    )
    assert out.returncode == 0, f"git {args} failed: {out.stderr}"
    return out.stdout.strip()


def test_squash_merge_breaks_ancestry_but_preserves_the_tree(tmp_path):
    """The property SecB relies on, proven rather than asserted.

    `G-02` originally read *"main == tested SHA"*. Under squash merge the
    tested head is **never** an ancestor of `main`, so that check is false
    for every merge this repository makes. The valid substitute is tree
    equality, and this test demonstrates both halves in a throwaway
    repository — not against real history, because the head objects of merged
    pull requests are pruned when their branches are deleted (verified: PR
    #67's head `d6cdbe8` is no longer present locally).
    """
    repo = tmp_path / "r"
    repo.mkdir()
    git("init", "-q", "-b", "main", cwd=repo)
    (repo / "f.txt").write_text("base\n", encoding="utf-8")
    git("add", "-A", cwd=repo)
    git("commit", "-qm", "base", cwd=repo)

    git("checkout", "-q", "-b", "feat", cwd=repo)
    (repo / "f.txt").write_text("changed\n", encoding="utf-8")
    git("add", "-A", cwd=repo)
    git("commit", "-qm", "step 1", cwd=repo)
    (repo / "g.txt").write_text("added\n", encoding="utf-8")
    git("add", "-A", cwd=repo)
    git("commit", "-qm", "step 2", cwd=repo)
    tested_head = git("rev-parse", "HEAD", cwd=repo)
    tested_tree = git("rev-parse", "HEAD^{tree}", cwd=repo)

    git("checkout", "-q", "main", cwd=repo)
    git("merge", "--squash", "feat", cwd=repo)
    git("commit", "-qm", "squashed (#1)", cwd=repo)
    merged_tree = git("rev-parse", "HEAD^{tree}", cwd=repo)

    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", tested_head, "HEAD"],
        cwd=repo, capture_output=True, timeout=30,
    )
    assert ancestry.returncode != 0, (
        "the tested head must NOT be an ancestor of main after a squash merge "
        "-- if it is, the merge was not a squash and G-02's original wording "
        "would be salvageable"
    )
    assert tested_tree == merged_tree, (
        "tree equality is the valid substitute for the ancestry check, and it "
        "must hold: the squash preserves content while discarding lineage"
    )


def test_a_squash_that_changes_content_is_detectable_by_the_tree(tmp_path):
    """The substitute check must also be able to fail.

    Tree equality is only evidence if an altered squash breaks it. A check
    that cannot fail is not a control (`K-05b`).
    """
    repo = tmp_path / "r"
    repo.mkdir()
    git("init", "-q", "-b", "main", cwd=repo)
    (repo / "f.txt").write_text("base\n", encoding="utf-8")
    git("add", "-A", cwd=repo)
    git("commit", "-qm", "base", cwd=repo)

    git("checkout", "-q", "-b", "feat", cwd=repo)
    (repo / "f.txt").write_text("changed\n", encoding="utf-8")
    git("add", "-A", cwd=repo)
    git("commit", "-qm", "work", cwd=repo)
    tested_tree = git("rev-parse", "HEAD^{tree}", cwd=repo)

    git("checkout", "-q", "main", cwd=repo)
    git("merge", "--squash", "feat", cwd=repo)
    (repo / "f.txt").write_text("changed, and then tampered with\n", encoding="utf-8")
    git("add", "-A", cwd=repo)
    git("commit", "-qm", "squashed with an extra edit", cwd=repo)

    assert tested_tree != git("rev-parse", "HEAD^{tree}", cwd=repo), (
        "an altered squash must break tree equality, or the substitute check "
        "proves nothing"
    )


# --- the catalogue itself ----------------------------------------------------


CATALOGUE = REPO_ROOT / "docs" / "09-testing" / "NEGATIVE_TEST_CATALOGUE.md"


def test_every_covered_scenario_names_a_test_that_exists():
    """A coverage claim citing a test that does not exist is worse than a gap.

    This is the `#407` defect class in test form: a document asserting a
    control that is not there.
    """
    import re

    text = CATALOGUE.read_text(encoding="utf-8")
    cited = set(re.findall(r"`(test_[a-z0-9_]+)`", text))
    available = set()
    for module in REPO_ROOT.glob("tests/test_*.py"):
        available |= set(
            re.findall(r"^def (test_[a-z0-9_]+)", module.read_text(encoding="utf-8"), re.M)
        )
    missing = sorted(cited - available)
    assert not missing, f"catalogue cites tests that do not exist: {missing}"


def test_the_catalogue_states_its_coverage_as_a_measured_fraction():
    text = CATALOGUE.read_text(encoding="utf-8")
    assert "4 of 15" in text, (
        "the catalogue must state measured coverage, not a qualitative claim"
    )
    assert "GAP" in text and "NOT_APPLICABLE" in text
