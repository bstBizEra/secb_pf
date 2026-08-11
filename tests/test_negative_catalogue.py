"""Negative tests for the evasion scenarios in `docs/09-testing/NEGATIVE_TEST_CATALOGUE.md`.

`KN-001`: a gate counts only once proven to fail on a real pull request. Three
supplied specifications handed this project 33 evasion scenarios; the catalogue
maps them, and this module holds the ones implementable today.

Two kinds of test live here, and the first version of this module conflated
them — corrected under the operator's review of 2026-08-11 §P1:

- **Characterization fixture** — demonstrates that a gap exists today. It is
  *not* a conformance requirement, so closing the gap must not turn CI red.
- **Desired-behaviour regression** — asserts a control blocks the scenario.

The fix is that a characterization fixture compares observed behaviour against
the status **declared** in `negative_test_status.json`. Fixing a gap therefore
requires flipping the declared status, and CI stays meaningful in both states
instead of going red on an improvement. Same shape as `FWK-041`'s
"observed status agrees with the world".

A green suite here means *"the recorded coverage still holds"*, never *"no
evasion is possible"*.
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

STATUS_FILE = REPO_ROOT / "docs" / "09-testing" / "negative_test_status.json"


def declared(scenario_id: str) -> dict:
    import json

    data = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
    for row in data["scenarios"]:
        if row["id"] == scenario_id:
            return row
    raise AssertionError(f"{scenario_id} is not declared in {STATUS_FILE.name}")


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


def test_characterize_gap_splitting_evades_the_line_ceiling():
    """Characterization fixture for `FPSA-02`, not a conformance requirement.

    One change over the cap escalates; two halves each auto-approve, because
    the classifier sees one diff at a time and has no notion of a sibling
    ticket. FPSA `FP-05` and WICG rule 8 both prohibit this.

    The assertion compares observed behaviour to the **declared** status, so
    landing a splitting detector means flipping `FPSA-02` to `CONTROL_FIXED`
    — it does not turn CI red on an improvement.
    """
    row = declared("FPSA-02")
    whole = classify("700\t600\tdocs/a.md\n")
    assert whole.returncode == ESCALATES, "a 1300-line change must escalate"
    assert "exceeds the envelope cap" in verdict_text(whole)

    halves = [classify("300\t250\tdocs/a.md\n"), classify("300\t250\tdocs/b.md\n")]
    split_evades = all(h.returncode == AUTO_APPROVED for h in halves)

    if row["status"] == "GAP_REPRODUCED":
        assert split_evades, (
            "FPSA-02 is declared GAP_REPRODUCED but splitting no longer "
            "evades the ceiling. Flip the status to CONTROL_FIXED."
        )
        assert row["remediation"]["review_by"], "a gap must carry a review date"
    else:
        assert not split_evades, (
            f"FPSA-02 is declared {row['status']} but two halves still "
            "auto-approve -- the declared control is not in force"
        )


# --- FPSA §15 case 3: authority-shaped data smuggled into configuration ------


def test_characterize_gap_a_new_config_file_classifies_as_low_risk():
    """Characterization fixture for `FPSA-03`.

    `config/` is an `auto_path` and only two files in it are named
    constitutional, so `config/permissions.json` auto-merges. Not
    hypothetical: `SECB-WP-FWK-041` landed `config/identifier_taxonomy.json`
    at `G0` under exactly this rule, which is how the gap was found.

    Tightening `config/` is a `G4` act that would reclassify that registry —
    so when it happens, `FPSA-03` flips and this fixture asserts the new
    behaviour instead of reddening the build.
    """
    row = declared("FPSA-03")
    result = classify("40\t0\tconfig/permissions.json\n")
    auto = result.returncode == AUTO_APPROVED

    if row["status"] == "GAP_REPRODUCED":
        assert auto and "G0" in verdict_text(result), (
            "FPSA-03 is declared GAP_REPRODUCED but a new config file no "
            "longer auto-approves. Flip the status to CONTROL_FIXED, and "
            "re-check where FWK-041's registry now sits."
        )
    else:
        assert not auto, (
            f"FPSA-03 is declared {row['status']} but a new config file still "
            "auto-approves"
        )


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


def test_the_catalogue_agrees_with_the_machine_readable_status():
    """The guard that was missing, added because the two records did disagree.

    `SECB-WP-FWK-044` closed `FPSA-03` and flipped the status file to 5
    covered, while the catalogue's table still read 4 and 36.4%. Every test
    passed. Prose and machine-readable record must not be able to drift
    silently -- the whole point of having the second one.
    """
    import json

    data = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
    text = CATALOGUE.read_text(encoding="utf-8")

    for family in ("FPSA", "BACP"):
        cov = data["coverage"][family]
        counted = sum(
            1
            for r in data["scenarios"]
            if r["id"].startswith(family) and r["status"] != "DORMANT_ABSENT_CAPABILITY"
            and r["status"] in ("COVERED", "CONTROL_FIXED")
        )
        assert counted == cov["covered"], (
            f"{family}: coverage block says {cov['covered']} covered, the scenario "
            f"rows contain {counted}"
        )
        row = f"| {family} §{'15' if family == 'FPSA' else '14'} |"
        line = next((l for l in text.splitlines() if l.startswith(row)), None)
        assert line, f"{family} coverage row missing from the catalogue"
        for value in (str(cov["target"]), str(cov["covered"]),
                      f"{cov['covered_over_applicable_pct']}%"):
            assert value in line, (
                f"{family}: catalogue row does not carry {value!r} from the status "
                f"file — prose and record have drifted"
            )

    assert "GAP" in text and "DORMANT" in text
