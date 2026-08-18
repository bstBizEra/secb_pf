"""SECB-WP-FWK-099 -- the reconciler (P0 item 10).

Closure is the claim that decays silently. A work package declared CLOSED stays closed in every
report after the head it was measured against is superseded, the branch is deleted, or its evidence
stops resolving. The mandate ranks false closure third in the gap-selection order, above production
gaps and non-deterministic gates.

    DECLARED_CLOSED != OBSERVABLY_CLOSED
    RECEIPT_EXISTS != RECEIPT_STILL_APPLIES

Negative-first, as the mandate requires: every divergence class is proven detectable before the
clean path is asserted, because a reconciler that reports RECONCILED for everything is worse than
none -- it converts unknown state into apparent agreement.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "scripts" / "check_reconciliation.py"

BASE = "a" * 40
OTHER = "b" * 40


def snapshot(*subjects, **over) -> dict:
    body = {
        "schema": "secb.reconciliation-snapshot/v1",
        "observed_at": "2026-08-18T00:00:00+00:00",
        "effective_base_sha": BASE,
        "subjects": list(subjects),
    }
    body.update(over)
    return body


def subject(sid="WP-1", **over) -> dict:
    body = {"id": sid, "declared_state": "CLOSED", "observed_landed": True,
            "observed_subject_exists": True}
    body.update(over)
    return body


def run(snap: dict, tmp_path: Path) -> subprocess.CompletedProcess:
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(snap), encoding="utf-8")
    return subprocess.run([sys.executable, str(TOOL)], capture_output=True, text=True,
                          env={**os.environ, "SNAPSHOT": str(path),
                               "PYTHONDONTWRITEBYTECODE": "1"}, check=False)


def classes(snap: dict, tmp_path: Path) -> list[str]:
    return [d["class"] for d in json.loads(run(snap, tmp_path).stdout)["divergences"]]


def refuses(snap: dict, tmp_path: Path, fragment: str) -> str:
    result = run(snap, tmp_path)
    assert result.returncode == 2, result.stdout
    assert fragment in result.stderr, result.stderr
    return result.stderr


# ------------------------------------------------------- every class is detectable


def test_false_closure_is_detected(tmp_path):
    """The class this tool exists for: declared closed, not observably landed."""
    found = classes(snapshot(subject(declared_state="CLOSED", observed_landed=False)), tmp_path)
    assert found == ["FALSE_CLOSURE"]


@pytest.mark.parametrize("state", ["CLOSED", "EFFECTIVE", "RECONCILED"])
def test_every_closed_state_is_checked_not_only_the_word_closed(tmp_path, state):
    found = classes(snapshot(subject(declared_state=state, observed_landed=False)), tmp_path)
    assert "FALSE_CLOSURE" in found


def test_orphaned_work_is_detected(tmp_path):
    found = classes(snapshot(subject(declared_state="EXECUTING", observed_landed=False,
                                     observed_subject_exists=False)), tmp_path)
    assert "ORPHANED_WORK" in found


def test_a_superseded_head_is_detected(tmp_path):
    """Evidence bound to a head the subject has moved past."""
    found = classes(snapshot(subject(declared_state="ELIGIBLE", observed_landed=False,
                                     evidence_head_sha=OTHER, observed_head_sha=BASE)), tmp_path)
    assert "SUPERSEDED_HEAD" in found


def test_a_stale_receipt_is_detected(tmp_path):
    found = classes(snapshot(subject(declared_state="ELIGIBLE", observed_landed=False,
                                     receipt_base_sha=OTHER)), tmp_path)
    assert "STALE_RECEIPT" in found


def test_an_unverifiable_release_is_detected(tmp_path):
    """Closure is valid only while its evidence remains verifiable."""
    found = classes(snapshot(subject(released=True, evidence_resolvable=False)), tmp_path)
    assert "UNVERIFIABLE_RELEASE" in found


def test_dependency_inversion_is_detected(tmp_path):
    """Ready on paper, dependency not landed in fact."""
    snap = snapshot(
        subject("WP-DEP", declared_state="CANDIDATE_READY", observed_landed=False),
        subject("WP-1", declared_state="ELIGIBLE", observed_landed=False,
                declared_dependencies=["WP-DEP"]))
    assert "DEPENDENCY_INVERSION" in classes(snap, tmp_path)


def test_a_landed_dependency_is_not_an_inversion(tmp_path):
    snap = snapshot(
        subject("WP-DEP", declared_state="CLOSED", observed_landed=True),
        subject("WP-1", declared_state="ELIGIBLE", observed_landed=False,
                declared_dependencies=["WP-DEP"]))
    assert "DEPENDENCY_INVERSION" not in classes(snap, tmp_path)


# ------------------------------------------------------------- the clean path


def test_a_consistent_snapshot_reconciles(tmp_path):
    result = run(snapshot(subject(evidence_head_sha=BASE, observed_head_sha=BASE,
                                  receipt_base_sha=BASE)), tmp_path)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["verdict"] == "RECONCILED"
    assert report["divergences"] == []


def test_divergence_is_a_non_success_outcome(tmp_path):
    """A reconciler that exits 0 on divergence reports into a void."""
    assert run(snapshot(subject(observed_landed=False)), tmp_path).returncode == 2


# ------------------------------------------------ the snapshot must be trustworthy


def test_a_snapshot_without_an_observation_instant_is_refused(tmp_path):
    snap = snapshot(subject())
    del snap["observed_at"]
    refuses(snap, tmp_path, "no observed_at")


def test_a_snapshot_without_an_effective_base_is_refused(tmp_path):
    """Without it STALE_RECEIPT cannot be evaluated, and a clean report would be a claim
    about a comparison that never happened."""
    snap = snapshot(subject())
    del snap["effective_base_sha"]
    refuses(snap, tmp_path, "cannot be evaluated")


def test_absent_subjects_is_not_an_empty_list(tmp_path):
    snap = snapshot()
    del snap["subjects"]
    refuses(snap, tmp_path, "an absent list is not an empty one")


def test_a_subject_without_a_declared_state_is_refused(tmp_path):
    snap = snapshot({"id": "WP-1", "observed_landed": True})
    refuses(snap, tmp_path, "UNKNOWN is not CLOSED")


def test_a_naive_observation_instant_is_refused(tmp_path):
    refuses(snapshot(subject(), observed_at="2026-08-18T00:00:00"), tmp_path, "no timezone")


# --------------------------------------------------------------- it repairs nothing


def test_the_reconciler_repairs_nothing_and_says_so(tmp_path):
    """A reconciler able to edit the state it audits could make its own report clean."""
    report = json.loads(run(snapshot(subject()), tmp_path).stdout)
    assert report["repairs_nothing"] is True
    assert report["confers_merge_authority"] is False


def test_it_declares_what_an_absent_field_did_not_prove(tmp_path):
    """A subject omitting evidence_head_sha cannot report SUPERSEDED_HEAD, and the report says so
    rather than letting silence read as a clean check."""
    report = json.loads(run(snapshot(subject()), tmp_path).stdout)
    assert any("cannot report SUPERSEDED_HEAD" in n for n in report["not_proven"])
