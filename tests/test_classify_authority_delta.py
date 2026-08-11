"""Subprocess tests for scripts/classify_authority_delta.py.

Invoked as CI invokes it — stdin numstat plus environment (KN-002). Each test
asserts both the exit code and the verdict name, because the exit code alone
cannot distinguish `AGENT_BALLOT_REQUIRED` from `CONSTITUTIONAL_REQUIRED`.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "classify_authority_delta.py"
REAL_ENVELOPE = ROOT / "config" / "delegation_envelope.json"

EXIT_OK = 0
EXIT_ESCALATE = 2
EXIT_REJECTED = 3

SEALED = (
    "docs/06-agent-orchestration/skill-router/"
    "SECB-WP-ENGLOOP-MVP-001 — Sandbox Evidence/router.py"
)


def run(
    numstat: str,
    envelope: Path | None = None,
    diff_text: str | None = None,
    diff_path: Path | str | None = None,
):
    env = {
        k: v
        for k, v in os.environ.items()
        if k not in ("ENVELOPE", "DIFF_TEXT", "DIFF_PATH")
    }
    env["ENVELOPE"] = str(envelope or REAL_ENVELOPE)
    if diff_text is not None:
        env["DIFF_TEXT"] = diff_text
    if diff_path is not None:
        env["DIFF_PATH"] = str(diff_path)
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=numstat,
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )


def verdict_of(result) -> str:
    text = result.stdout + result.stderr
    line = next(ln for ln in text.splitlines() if ln.startswith("VERDICT:"))
    return line.removeprefix("VERDICT:").strip().split("—")[0].strip()


@pytest.fixture
def custom_envelope(tmp_path):
    def build(**overrides):
        data = json.loads(REAL_ENVELOPE.read_text(encoding="utf-8"))
        for dotted, value in overrides.items():
            node = data
            *parents, leaf = dotted.split(".")
            for key in parents:
                node = node[key]
            node[leaf] = value
        path = tmp_path / "envelope.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path
    return build


# --- G0: auto-approved -------------------------------------------------------

def test_g0_docs_only_auto_approved():
    result = run("12\t3\tdocs/14-plans/SECB-WP-FWK-999.md\n")
    assert result.returncode == EXIT_OK
    assert verdict_of(result) == "AUTO_APPROVED"


def test_g0_mixed_docs_tests_src_auto_approved():
    numstat = (
        "20\t0\tdocs/13-evidence/RECORD.md\n"
        "30\t5\ttests/test_thing.py\n"
        "40\t1\tsrc/secb_router/helper.py\n"
    )
    result = run(numstat)
    assert result.returncode == EXIT_OK
    assert "3 path(s)" in result.stdout


def test_g0_binary_file_counts_no_lines():
    result = run("-\t-\tdocs/diagram.png\n")
    assert result.returncode == EXIT_OK


# --- G4: constitutional ------------------------------------------------------

@pytest.mark.parametrize(
    "path",
    [
        "docs/00-governance/L0_ROOT_CONSTITUTION.md",
        "config/delegation_envelope.json",
        "config/ballot.schema.json",
        "scripts/classify_authority_delta.py",
        "scripts/check_dual_policy.py",
        ".github/workflows/ci.yml",
        "AGENTS.md",
        SEALED,
    ],
)
def test_g4_root_authority_surface_is_constitutional(path):
    result = run(f"2\t1\t{path}\n")
    assert result.returncode == EXIT_ESCALATE
    assert verdict_of(result) == "CONSTITUTIONAL_REQUIRED"


def test_g4_wins_over_g0_when_mixed():
    result = run("5\t0\tdocs/plan.md\n1\t1\tAGENTS.md\n")
    assert verdict_of(result) == "CONSTITUTIONAL_REQUIRED"


def test_path_outside_envelope_is_constitutional():
    result = run("1\t0\tinfra/terraform/main.tf\n")
    assert result.returncode == EXIT_ESCALATE
    assert verdict_of(result) == "CONSTITUTIONAL_REQUIRED"


def test_absolute_ceiling_is_not_waivable():
    result = run("1500\t600\tdocs/enormous.md\n")  # 2100 > 2000
    assert verdict_of(result) == "CONSTITUTIONAL_REQUIRED"
    assert "absolute ceiling" in result.stderr


# --- G1/G2: ballot required (inert layer, so it escalates) --------------------

def test_g1_governance_implementation_requires_ballot():
    result = run("10\t2\tdocs/00-governance/SOME_POLICY.md\n")
    assert result.returncode == EXIT_ESCALATE
    assert verdict_of(result) == "AGENT_BALLOT_REQUIRED"
    assert "NOT_ACTIVE" in result.stderr


def test_g1_adr_is_governance_not_constitutional():
    # An ADR is non-executable evidence: it needs ballots, not the
    # constitutional authority, unless it edits L0 itself.
    result = run("40\t0\tdocs/12-decisions/ADR-SOMETHING.md\n")
    assert verdict_of(result) == "AGENT_BALLOT_REQUIRED"


def test_over_envelope_cap_but_under_ceiling_requires_ballot():
    result = run("400\t300\tdocs/large.md\n")  # 700 > 600, < 2000
    assert verdict_of(result) == "AGENT_BALLOT_REQUIRED"
    assert "exceeds the envelope cap" in result.stderr


def test_ballot_layer_active_changes_the_reason_not_the_verdict(custom_envelope):
    envelope = custom_envelope(**{"ballot_layer.state": "ACTIVE"})
    result = run("10\t2\tdocs/00-governance/P.md\n", envelope=envelope)
    assert verdict_of(result) == "AGENT_BALLOT_REQUIRED"
    assert "NOT_ACTIVE" not in result.stderr


# --- G5: rejected ------------------------------------------------------------

def test_g5_deleting_a_control_is_rejected():
    result = run("0\t80\tscripts/check_budget.py\n")
    assert result.returncode == EXIT_REJECTED
    assert verdict_of(result) == "REJECTED"


def test_g5_deleting_evidence_is_rejected():
    result = run("0\t40\tdocs/13-evidence/SECB-WP-ENGLOOP-001_RECORD.md\n")
    assert result.returncode == EXIT_REJECTED


def test_g5_removing_a_ci_enforcement_step_is_rejected():
    result = run(
        "3\t4\tdocs/note.md\n",
        diff_text="-        run: python scripts/check_work_package_ref.py",
    )
    assert result.returncode == EXIT_REJECTED
    assert "removes an enforcement step" in result.stderr


def test_quoting_an_enforcement_step_on_an_added_line_is_not_a_removal():
    """Regression: the first version scanned the whole diff as one string and
    rejected its own test fixture. An ADDED line quoting the marker — a test,
    or documentation of this rule — must not read as a removal."""
    added = (
        '+        diff_text="-        run: python scripts/check_work_package_ref.py",\n'
        "+# documents that removing `run: python scripts/check_budget.py` is prohibited\n"
    )
    result = run("3\t4\tdocs/note.md\n", diff_text=added)
    assert result.returncode == EXIT_OK
    assert verdict_of(result) == "AUTO_APPROVED"


def test_diff_file_header_is_not_read_as_a_removal():
    header = "--- a/.github/workflows/ci.yml\n+++ b/.github/workflows/ci.yml\n"
    result = run("3\t4\tdocs/note.md\n", diff_text=header)
    assert result.returncode == EXIT_OK


def test_editing_a_control_is_not_a_deletion():
    # Additions plus deletions on a control file is an edit -> G4, not G5.
    result = run("10\t8\tscripts/check_budget.py\n")
    assert verdict_of(result) == "AGENT_BALLOT_REQUIRED"


# --- fail-closed paths -------------------------------------------------------

def test_empty_diff_escalates():
    result = run("")
    assert result.returncode == EXIT_ESCALATE
    assert "no diff parsed" in result.stderr


def test_unparseable_numstat_escalates():
    result = run("garbage without tabs\n")
    assert result.returncode == EXIT_ESCALATE


def test_missing_envelope_escalates(tmp_path):
    result = run("1\t0\tdocs/a.md\n", envelope=tmp_path / "absent.json")
    assert result.returncode == EXIT_ESCALATE
    assert "envelope unusable" in result.stderr


def test_malformed_envelope_escalates(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    result = run("1\t0\tdocs/a.md\n", envelope=bad)
    assert result.returncode == EXIT_ESCALATE


def test_envelope_missing_required_key_escalates(tmp_path):
    partial = tmp_path / "partial.json"
    partial.write_text(json.dumps({"scope": {}}), encoding="utf-8")
    result = run("1\t0\tdocs/a.md\n", envelope=partial)
    assert result.returncode == EXIT_ESCALATE


def test_expired_envelope_escalates(custom_envelope):
    envelope = custom_envelope(expires_at="2020-01-01")
    result = run("1\t0\tdocs/a.md\n", envelope=envelope)
    assert result.returncode == EXIT_ESCALATE
    assert "expired" in result.stderr


def test_sealed_path_with_spaces_and_em_dash_read_whole():
    result = run(f"1\t1\t{SEALED}\n")
    assert verdict_of(result) == "CONSTITUTIONAL_REQUIRED"


# --- the diff body arrives by path (`SECB-WP-FWK-043`) -----------------------
#
# `DIFF_TEXT` cannot carry a large diff: Linux caps one environment string at
# MAX_ARG_STRLEN = 131072 bytes. Before this work package, `ci.yml` passed the
# whole diff that way, so a 160-line PR of long-line JSON made the shell fail
# with E2BIG **before the classifier started** -- the G5 prohibited-action scan
# never ran, `REJECTED` was unreachable, and the summary announced a routine
# escalation. These tests exist so that cannot recur silently.

ENV_STRING_LIMIT = 131072


def oversized_diff(tmp_path: Path, extra_line: str | None = None) -> tuple[Path, str]:
    """A diff over the env-string limit, built from this repo's own content.

    The long lines come from `route-plan.schema.json`, whose longest line is
    1053 bytes. Using real content keeps the fixture honest about where a diff
    like this comes from: not a contrived blob, but six schema files already
    sitting under `docs/`, which is an `auto_path`.
    """
    source = (
        ROOT
        / "docs/06-agent-orchestration/skill-router/route-plan.schema.json"
    ).read_text(encoding="utf-8").splitlines()
    longest = sorted(source, key=len, reverse=True)[:8]
    body, count = [], 0
    while count < 160:
        for line in longest:
            body.append("+" + line)
            count += 1
            if count >= 160:
                break
    if extra_line is not None:
        body.insert(len(body) // 2, extra_line)
    diff = (
        "diff --git a/docs/x.schema.json b/docs/x.schema.json\n"
        "new file mode 100644\n--- /dev/null\n+++ b/docs/x.schema.json\n"
        f"@@ -0,0 +1,{len(body)} @@\n" + "\n".join(body) + "\n"
    )
    assert len(diff) > ENV_STRING_LIMIT, "fixture must exceed the env-string limit"
    path = tmp_path / "big.diff"
    path.write_text(diff, encoding="utf-8")
    return path, diff


def test_oversized_diff_classifies_when_passed_by_path(tmp_path):
    """160 lines, over 131 KB, well inside the 600-line auto-merge cap."""
    path, diff = oversized_diff(tmp_path)
    result = run("160\t0\tdocs/x.schema.json\n", diff_path=path)
    assert result.returncode == EXIT_OK
    assert "AUTO_APPROVED" in result.stdout
    assert len(diff) > ENV_STRING_LIMIT


def test_g5_is_reachable_inside_an_oversized_diff(tmp_path):
    """The verdict that was unreachable. This is the whole point of FWK-043.

    A removed CI enforcement step buried in the middle of a 168 KB diff must
    still produce `REJECTED`. Passed by `DIFF_TEXT` this test cannot even
    start the interpreter.
    """
    path, _ = oversized_diff(
        tmp_path, extra_line="-          run: python scripts/check_work_package_ref.py"
    )
    result = run("161\t0\tdocs/x.schema.json\n", diff_path=path)
    assert result.returncode == EXIT_REJECTED
    assert "REJECTED" in result.stderr
    assert "removes an enforcement step" in result.stderr


def test_unreadable_diff_path_escalates_and_is_not_read_as_an_empty_diff(tmp_path):
    """The fail-open this fix could have introduced, closed deliberately.

    An empty diff means "no prohibited signature found". A diff that could not
    be read means nothing at all, and must never borrow the empty diff's
    meaning.
    """
    result = run("5\t0\tdocs/a.md\n", diff_path=tmp_path / "absent.diff")
    assert result.returncode == EXIT_ESCALATE
    assert "cannot be read" in result.stderr
    assert "not an empty diff" in result.stderr


def test_diff_path_wins_when_both_channels_are_set(tmp_path):
    """The file channel is authoritative, because only it can carry the diff.

    A caller that sets both -- a half-migrated workflow, say -- must get the
    complete body, not the truncatable one.
    """
    path = tmp_path / "d.diff"
    path.write_text("-          run: python scripts/check_budget.py\n", encoding="utf-8")
    result = run(
        "3\t0\tdocs/a.md\n",
        diff_path=path,
        diff_text="+ nothing prohibited here\n",
    )
    assert result.returncode == EXIT_REJECTED, (
        "DIFF_PATH holds a G5 signature and DIFF_TEXT does not; the path must win"
    )


def test_diff_text_still_works_for_callers_that_already_use_it():
    """Compatibility: the old channel is retained, only no longer preferred."""
    result = run(
        "4\t0\tdocs/a.md\n",
        diff_text="-          run: python scripts/check_work_package_ref.py\n",
    )
    assert result.returncode == EXIT_REJECTED
# --- config/ is governance implementation (`SECB-WP-FWK-044`) -----------------


def test_a_new_config_file_is_governance_implementation_not_ordinary_work():
    """The desired-behaviour regression that replaces `FPSA-03`'s fixture.

    `config/` used to be an `auto_path`, so a new file under it classified `G0`
    and auto-merged -- and `SECB-WP-FWK-041` landed
    `config/identifier_taxonomy.json` that way before `FWK-042` characterized
    the gap. Configuration is where authority lives here.
    """
    result = run("40\t0\tconfig/permissions.json\n")
    assert result.returncode == EXIT_ESCALATE
    assert "AGENT_BALLOT_REQUIRED" in result.stderr
    assert "governance implementation" in result.stderr


def test_the_two_named_config_files_stay_constitutional_not_merely_governance():
    """`G4` must still beat `G1` for the envelope and the ballot schema.

    Adding `config/` to the governance list must not *demote* the two files
    that were already constitutional -- the classifier checks `G4` first, and
    this asserts that ordering rather than trusting it.
    """
    for path in ("config/delegation_envelope.json", "config/ballot.schema.json"):
        result = run(f"1\t0\t{path}\n")
        assert result.returncode == EXIT_ESCALATE
        assert "CONSTITUTIONAL_REQUIRED" in result.stderr, path


def test_removing_config_from_the_governance_list_fails_closed(tmp_path):
    """The reason `config/` left `auto_paths` as well as joining the other list.

    Both edits produce `G1` today. They differ in how a future mistake fails:
    with `config/` still in `auto_paths`, dropping it from the governance list
    would silently restore `G0`. Removed from both, the same slip yields
    "outside the delegated envelope" -- stricter, not looser.
    """
    envelope = json.loads(REAL_ENVELOPE.read_text(encoding="utf-8"))
    envelope["scope"]["governance_implementation_paths"] = [
        p for p in envelope["scope"]["governance_implementation_paths"] if p != "config/"
    ]
    path = tmp_path / "envelope.json"
    path.write_text(json.dumps(envelope), encoding="utf-8")

    result = run("40\t0\tconfig/permissions.json\n", envelope=path)
    assert result.returncode == EXIT_ESCALATE
    assert "outside the delegated envelope" in result.stderr, (
        "with config/ in neither list the verdict must be constitutional, not G0"
    )


def test_docs_src_and_tests_still_auto_approve():
    """The blast radius, asserted rather than assumed."""
    result = run("10\t0\tdocs/a.md\n5\t0\tsrc/x.py\n3\t0\ttests/t.py\n")
    assert result.returncode == EXIT_OK
    assert "AUTO_APPROVED" in result.stdout


# --- the cap applies to the change family (`SECB-WP-FWK-046`) ----------------


def run_family(numstat: str, family: str | None = None):
    env = {
        k: v
        for k, v in os.environ.items()
        if k not in ("ENVELOPE", "DIFF_TEXT", "DIFF_PATH", "FAMILY_LINES")
    }
    env["ENVELOPE"] = str(REAL_ENVELOPE)
    if family is not None:
        env["FAMILY_LINES"] = family
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=numstat, capture_output=True, text=True, env=env, timeout=30,
    )


def test_a_split_change_escalates_when_its_family_is_reported():
    """The measured evasion, closed.

    `SECB-WP-FWK-042` locked the behaviour: one 1300-line change escalated
    while two ~550-line halves each auto-approved, because this script sees one
    diff at a time.
    """
    half = "300\t250\tdocs/a.md\n"
    alone = run_family(half)
    assert alone.returncode == EXIT_OK, "one half alone is inside the cap"

    with_sibling = run_family(half, family="550")
    assert with_sibling.returncode == EXIT_ESCALATE
    assert "change family totals 1100" in with_sibling.stderr
    assert "splitting a change does not lower its class" in with_sibling.stderr


def test_absence_of_a_family_is_stated_rather_than_silent():
    """`FAMILY_LINES` is caller-supplied, so its absence must be visible.

    It cannot be mandatory: every local self-check in this repository invokes
    the classifier without it, and making it required would fail those closed.
    So the verdict line distinguishes "no family reported" from "family of
    zero", and a reader can tell which kind of verdict they are holding.
    """
    quiet = run_family("5\t0\tdocs/a.md\n")
    assert "no concurrent family reported" in quiet.stdout

    reported = run_family("5\t0\tdocs/a.md\n", family="10")
    assert "family +10" in reported.stdout


def test_a_family_within_the_cap_still_auto_approves():
    """The control must discriminate, not merely refuse."""
    result = run_family("100\t0\tdocs/a.md\n", family="200")
    assert result.returncode == EXIT_OK
    assert "family +200" in result.stdout


def test_a_single_change_over_the_cap_keeps_its_own_reason():
    """The family check must not swallow the plain over-cap case.

    Two different findings deserve two different sentences, or a reader cannot
    tell whether the change or its family was the problem.
    """
    result = run_family("700\t600\tdocs/a.md\n", family="0")
    assert result.returncode == EXIT_ESCALATE
    assert "1300 lines exceeds the envelope cap" in result.stderr
    assert "change family" not in result.stderr


def test_a_malformed_family_size_fails_closed():
    """An unparseable family size is not a family of zero."""
    for bad in ("abc", "-5", "12.5"):
        result = run_family("5\t0\tdocs/a.md\n", family=bad)
        assert result.returncode == EXIT_ESCALATE, bad
        assert "CONSTITUTIONAL_REQUIRED" in result.stderr, bad
