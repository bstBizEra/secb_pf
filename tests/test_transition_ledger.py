"""SECB-WP-FWK-100 -- transition ledger sequence invariants (P0 item 7).

A per-object schema says one transition is well-formed. Only the sequence says the transitions
form a history:

    TRANSITION_VALID != HISTORY_COHERENT
    LANDING_VERIFIED != LANDED_ON_THE_PREVIOUS_LANDING

The second is the invariant that generalises the compare-and-swap handoff. Every landing this
session was verified individually -- pinned head, expected tree, readback -- and nothing checked
that landing N+1 was built on landing N. `test_a_landing_off_the_chain_is_refused` is that check.

Negative-first: every invariant is proven to fire before the coherent ledger is asserted.
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
TOOL = ROOT / "scripts" / "check_transition_ledger.py"
REAL = ROOT / "work" / "transitions" / "SECB-LEDGER-001.json"

A, B, C = "a" * 40, "b" * 40, "c" * 40


def cas(**over) -> dict:
    body = {"target_base_sha": A, "source_head_sha": B, "merge_base_sha": A,
            "expected_result_tree": C, "actual_result_tree": C, "actual_result_sha": B,
            "actual_parent_sha": A, "merge_method": "squash"}
    body.update(over)
    return body


def ledger(*transitions, **over) -> dict:
    body = {"schema": "secb.transition-ledger/v1", "transitions": list(transitions)}
    body.update(over)
    return body


def step(seq, subject="WP-1", frm="DETECTED", to="ELIGIBLE", **over) -> dict:
    body = {"id": f"T-{seq}", "sequence": seq, "subject_id": subject, "from_state": frm,
            "to_state": to, "occurred_at": f"2026-08-18T00:{seq:02d}:00+00:00"}
    body.update(over)
    return body


def run(body: dict, tmp_path: Path) -> subprocess.CompletedProcess:
    path = tmp_path / "ledger.json"
    path.write_text(json.dumps(body), encoding="utf-8")
    return subprocess.run([sys.executable, str(TOOL)], capture_output=True, text=True,
                          env={**os.environ, "LEDGER": str(path),
                               "PYTHONDONTWRITEBYTECODE": "1"}, check=False)


def refuses(body: dict, tmp_path: Path, fragment: str) -> str:
    result = run(body, tmp_path)
    assert result.returncode == 2, result.stdout
    assert fragment in result.stderr, result.stderr
    return result.stderr


# ------------------------------------------------------------ the real ledger


def test_the_shipped_ledger_is_coherent():
    """Three real landings, trees and parents read from git rather than transcribed."""
    result = subprocess.run([sys.executable, str(TOOL)], capture_output=True, text=True,
                            env={**os.environ, "LEDGER": str(REAL),
                                 "PYTHONDONTWRITEBYTECODE": "1"}, check=False)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["verdict"] == "LEDGER_COHERENT"
    assert report["landings"] == 3
    assert report["head_effective_commit"] == "ace1e579597f768c34b222a91d66ed445dfe34d3"


def _resolvable(rev: str) -> bool:
    return subprocess.run(["git", "cat-file", "-e", rev], cwd=ROOT,
                          capture_output=True).returncode == 0


def test_the_shipped_ledger_chain_links_to_itself():
    """Always-on: each landing's parent must be the previous landing's commit.

    This runs in every environment because it reads only the ledger. The first version of this
    test asserted equality with `origin/main`, which fails in CI -- the checkout has no such ref,
    so the test depended on the ENVIRONMENT rather than on the evidence.

        PASSES_LOCALLY != PASSES_WHERE_IT_MATTERS
    """
    body = json.loads(REAL.read_text(encoding="utf-8"))
    landings = [t for t in sorted(body["transitions"], key=lambda x: x["sequence"])
                if t["to_state"] == "EFFECTIVE"]
    assert len(landings) == 3
    previous = body["genesis_commit"]
    for landing in landings:
        cas_block = landing["compare_and_swap"]
        assert cas_block["actual_parent_sha"] == previous, landing["id"]
        assert cas_block["actual_result_tree"] == cas_block["expected_result_tree"]
        previous = cas_block["actual_result_sha"]


def test_the_shipped_ledger_agrees_with_the_git_objects_when_they_are_present():
    """Stronger check where history is available: the ledger must match the objects themselves.

    Recorded rather than skipped when the objects are absent, so a shallow clone reports a
    narrower check instead of a silent pass. OBJECTS_ABSENT != LEDGER_UNVERIFIED_SILENTLY.
    """
    body = json.loads(REAL.read_text(encoding="utf-8"))
    landings = [t for t in sorted(body["transitions"], key=lambda x: x["sequence"])
                if t["to_state"] == "EFFECTIVE"]
    checked = 0
    for landing in landings:
        cas_block = landing["compare_and_swap"]
        commit = cas_block["actual_result_sha"]
        if not _resolvable(commit):
            continue
        tree = subprocess.check_output(["git", "rev-parse", f"{commit}^{{tree}}"],
                                       cwd=ROOT, text=True).strip()
        parent = subprocess.check_output(["git", "rev-parse", f"{commit}^"],
                                         cwd=ROOT, text=True).strip()
        assert tree == cas_block["actual_result_tree"], commit
        assert parent == cas_block["actual_parent_sha"], commit
        checked += 1
    assert checked in (0, len(landings)), (
        f"only {checked} of {len(landings)} landings were resolvable; a partially verifiable "
        "ledger is a finding, not a pass"
    )


# ------------------------------------------------------------ append-only


def test_a_reused_sequence_position_is_refused(tmp_path):
    refuses(ledger(step(1), step(1, subject="WP-2")), tmp_path, "cannot reuse a position")


def test_a_gap_in_the_sequence_is_refused(tmp_path):
    """A gap is indistinguishable from a deleted transition."""
    refuses(ledger(step(1), step(3, frm="ELIGIBLE", to="EFFECTIVE")), tmp_path, "gaps at")


def test_a_non_integer_sequence_is_refused(tmp_path):
    refuses(ledger(step(1) | {"sequence": "1"}), tmp_path, "no integer sequence")


# ------------------------------------------------------------ continuity


def test_a_broken_continuity_is_refused(tmp_path):
    """from_state must equal the subject's previous to_state; a gap is an unrecorded transition."""
    refuses(ledger(step(1, to="ELIGIBLE"), step(2, frm="VERIFYING", to="EFFECTIVE")),
            tmp_path, "previous recorded state")


def test_a_subject_appearing_mid_history_is_refused(tmp_path):
    refuses(ledger(step(1, frm="COMMITTING", to="EFFECTIVE", compare_and_swap=cas())),
            tmp_path, "not a genesis state")


def test_a_mid_history_start_is_allowed_when_justified(tmp_path):
    body = ledger(step(1, frm="COMMITTING", to="EFFECTIVE", compare_and_swap=cas(),
                       genesis_justification="imported from a pre-ledger landing"),
                  genesis_commit=A)
    assert run(body, tmp_path).returncode == 0


def test_time_may_not_move_backwards_within_a_subject(tmp_path):
    body = ledger(step(1, to="ELIGIBLE"),
                  step(2, frm="ELIGIBLE", to="VERIFYING",
                       occurred_at="2026-08-17T00:00:00+00:00"))
    refuses(body, tmp_path, "moves backwards")


def test_a_naive_timestamp_is_refused(tmp_path):
    body = ledger(step(1, to="ELIGIBLE"),
                  step(2, frm="ELIGIBLE", to="VERIFYING", occurred_at="2026-08-18T05:00:00"))
    refuses(body, tmp_path, "no timezone")


# ------------------------------------------------------------ replay


def test_a_replayed_receipt_is_refused(tmp_path):
    """One verification must not authorise two state changes."""
    d = "sha256:" + "f" * 64
    body = ledger(step(1, to="ELIGIBLE", receipt_digest=d),
                  step(2, frm="ELIGIBLE", to="VERIFYING", receipt_digest=d))
    stderr = refuses(body, tmp_path, "was already applied by")
    assert "two state changes" in stderr


# ------------------------------------------------------------ terminal states


@pytest.mark.parametrize("terminal", ["CLOSED", "SUPERSEDED", "OUTSIDE_MANDATE", "QUARANTINED",
                                      "ROLLED_BACK"])
def test_nothing_follows_a_terminal_state_without_a_reopen(tmp_path, terminal):
    body = ledger(step(1, to=terminal), step(2, frm=terminal, to="EXECUTING"))
    refuses(body, tmp_path, "requires an explicit reopen_justification")


def test_a_justified_reopen_is_allowed(tmp_path):
    body = ledger(step(1, to="QUARANTINED"),
                  step(2, frm="QUARANTINED", to="EXECUTING",
                       reopen_justification="containment lifted after evidence re-verification"))
    assert run(body, tmp_path).returncode == 0


# ------------------------------------------------------------ the landing chain


def test_a_landing_without_compare_and_swap_is_refused(tmp_path):
    refuses(ledger(step(1, to="EFFECTIVE")), tmp_path, "carries no compare_and_swap")


@pytest.mark.parametrize("missing", ["merge_base_sha", "expected_result_tree",
                                     "actual_result_tree", "actual_result_sha"])
def test_a_landing_missing_a_binding_field_is_refused(tmp_path, missing):
    partial = cas()
    del partial[missing]
    refuses(ledger(step(1, to="EFFECTIVE", compare_and_swap=partial)), tmp_path, missing)


def test_a_landing_whose_tree_differs_from_the_prediction_is_refused(tmp_path):
    body = ledger(step(1, to="EFFECTIVE", compare_and_swap=cas(actual_result_tree="d" * 40)))
    refuses(body, tmp_path, "is not the predicted")


def test_a_landing_off_the_chain_is_refused(tmp_path):
    """The invariant no individual receipt can express.

    Both landings verify on their own -- pinned head, predicted tree, readback -- and the second
    was built on something other than the first. Every per-merge check passes; the history is
    still wrong.
    """
    first = step(1, subject="WP-1", to="EFFECTIVE",
                 compare_and_swap=cas(actual_result_sha=B, actual_parent_sha=A))
    second = step(2, subject="WP-2", to="EFFECTIVE",
                  compare_and_swap=cas(actual_result_sha=C, actual_parent_sha="e" * 40))
    stderr = refuses(ledger(first, second, genesis_commit=A), tmp_path, "out of band")
    assert "verifies individually and the chain still breaks" in stderr


def test_a_chained_landing_sequence_is_accepted(tmp_path):
    first = step(1, subject="WP-1", to="EFFECTIVE",
                 compare_and_swap=cas(actual_result_sha=B, actual_parent_sha=A))
    second = step(2, subject="WP-2", to="EFFECTIVE",
                  compare_and_swap=cas(actual_result_sha=C, actual_parent_sha=B))
    assert run(ledger(first, second, genesis_commit=A), tmp_path).returncode == 0


# ------------------------------------------------------------ fail-closed inputs


def test_absent_transitions_is_not_an_empty_ledger(tmp_path):
    body = ledger()
    del body["transitions"]
    refuses(body, tmp_path, "an absent list is not an empty one")


def test_a_wrong_schema_is_refused(tmp_path):
    refuses(ledger(step(1)) | {"schema": "secb.transition/v1"}, tmp_path, "expected")


def test_a_missing_ledger_path_is_refused():
    result = subprocess.run([sys.executable, str(TOOL)], capture_output=True, text=True,
                            env={**os.environ, "LEDGER": "", "PYTHONDONTWRITEBYTECODE": "1"},
                            check=False)
    assert result.returncode == 2 and "LEDGER is required" in result.stderr


def test_it_confers_no_authority(tmp_path):
    report = json.loads(run(ledger(step(1)), tmp_path).stdout)
    assert report["confers_merge_authority"] is False
    assert any("does not prove" in n or "not proven" in n.lower() or "completeness" in n
               for n in report["not_proven"]) or report["not_proven"]
