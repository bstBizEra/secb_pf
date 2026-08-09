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


def run(numstat: str, envelope: Path | None = None, diff_text: str | None = None):
    env = {k: v for k, v in os.environ.items() if k not in ("ENVELOPE", "DIFF_TEXT")}
    env["ENVELOPE"] = str(envelope or REAL_ENVELOPE)
    if diff_text is not None:
        env["DIFF_TEXT"] = diff_text
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
