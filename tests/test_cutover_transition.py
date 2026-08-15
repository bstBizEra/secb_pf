"""The cutover controller refuses what it cannot evidence — `SECB-WP-FWK-080` (#143).

    BUSINESS_DECISION_TO_DISCLOSE ≠ CAPABILITY_AVAILABLE ≠ CONTROL_CONFIGURED
      ≠ CONTROL_VERIFIED ≠ CONTROL_ENFORCED

Every refusal below is produced by **invoking the validator as a subprocess** against a
mutated manifest, and the permitted path is tested too, so no refusal is vacuous.

The controller performs no external effect. These tests therefore prove refusal logic and
nothing about GitHub: whether a ruleset can actually be created is unmeasured here, and
recorded as such.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check_cutover_transition.py"
MANIFEST = REPO_ROOT / "config" / "public_cutover_state.json"

OK = 0
FAIL = 2

CAPABILITIES = ("rulesets", "merge_queue", "artifact_attestations", "archival")


def manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def run(target: str, tmp_path=None, mutate=None, **env_extra) -> subprocess.CompletedProcess:
    data = manifest()
    if mutate:
        mutate(data)
    path = MANIFEST
    if mutate is not None:
        path = tmp_path / "manifest.json"
        path.write_text(json.dumps(data), encoding="utf-8")
    env = {"PATH": "/usr/bin:/bin", "MANIFEST": str(path)}
    env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(SCRIPT), target],
        capture_output=True, text=True, env=env, cwd=str(REPO_ROOT), timeout=30,
    )


BALLOT_ROLES = ("AUTHORITY_RESOLVER", "DISCLOSURE_CLASSIFIER", "SECRET_AUDITOR",
                "DEPENDENCY_VERIFIER", "ADVERSARIAL_REVIEWER")
EFFECT_ROLES = ("EFFECT_EXECUTOR", "READBACK_VERIFIER")

SNAPSHOT = {
    "repository_id": "R_kgDOsecb",
    "main_sha": "f1b2516688f94c7aad9a0b1b9c060abd023c86bf",
    "open_pr_head_digest": "sha256:aa11bb22",
    "mandate_digest": "sha256:cc33dd44",
    "credential_cutover_result": "PASSED",
}


def prove_separation(d: dict) -> None:
    """The one mutation that makes the accept path reachable at all.

    Set only in fixtures. On the shipped manifest this is `IDENTITY_SEPARATION_UNPROVEN`,
    and every route to `DISCLOSURE_AUTHORIZED` is refused because of it.
    """
    d["agentic_authorization"]["identity_separation"]["status"] = "PROVEN"


def write_receipt(tmp_path, roles=None, snapshot=None, schema=None, name="receipt.json"):
    receipt = {
        "schema": schema or "secb.agentic-decision-receipt/v1",
        "roles": roles if roles is not None else {
            **{r: {"actor_id": f"app/{r.lower()}", "decision": "AUTHORIZE"}
               for r in BALLOT_ROLES},
            **{r: {"actor_id": f"app/{r.lower()}"} for r in EFFECT_ROLES},
        },
        "snapshot": snapshot if snapshot is not None else dict(SNAPSHOT),
    }
    path = tmp_path / name
    path.write_text(json.dumps(receipt), encoding="utf-8")
    return str(path)


def write_snapshot(tmp_path, **overrides):
    observed = dict(SNAPSHOT)
    observed.update(overrides)
    path = tmp_path / "observed.json"
    path.write_text(json.dumps(observed), encoding="utf-8")
    return str(path)


def authorize(tmp_path, mutate=prove_separation, **env_extra):
    env = {
        "DECISION_RECEIPT": write_receipt(tmp_path),
        "OBSERVED_SNAPSHOT": write_snapshot(tmp_path),
    }
    env.update(env_extra)
    return run("DISCLOSURE_AUTHORIZED", tmp_path, mutate, **env)


# --- the shipped state --------------------------------------------------------


def test_the_manifest_ships_unapproved_and_performs_no_effect():
    data = manifest()
    assert data["lifecycle_state"] == "DISCLOSURE_UNAPPROVED"
    assert "PERFORMS NO EXTERNAL EFFECT" in data["$comment"]
    for name in CAPABILITIES:
        capability = data["capabilities"][name]
        assert capability["live_readback"]["status"] == "NOT_OBSERVED"
        assert capability["verified"] is False
        assert capability["enforced"] is False


def test_every_capability_is_tracked_separately():
    """One capability passing must never raise another.

    They are configured through different surfaces — rulesets, queue settings,
    attestation workflows, archival — and fail independently.
    """
    data = manifest()
    for name in CAPABILITIES:
        assert set(data["capabilities"][name]) >= {
            "configured_intent", "live_readback", "verified", "enforced"
        }, f"{name} does not carry the four separate facts"


# --- ordering ----------------------------------------------------------------


def test_the_shipped_state_refuses_on_identity_separation_first(tmp_path):
    """The real current answer, and the order matters.

    Every later check reads self-asserted receipt content. Passing them while the substrate
    is unproven would report a verified decision assembled from text one actor wrote — the
    self-approval-in-five-hats defect the ballot layer already refuses.
    """
    result = authorize(tmp_path, mutate=None)
    assert result.returncode == FAIL
    assert "IDENTITY_SEPARATION_UNPROVEN" in result.stderr
    assert "C-7" in result.stderr
    assert "self-asserted text" in result.stderr


def test_a_perfect_receipt_still_loses_to_unproven_identity(tmp_path):
    """A complete receipt does not substitute for the substrate it depends on."""
    result = authorize(tmp_path, mutate=None)
    assert result.returncode == FAIL
    assert "RECEIPT_STALE" not in result.stderr
    assert "IDENTITY_SEPARATION_UNPROVEN" in result.stderr


def test_the_authorized_path_is_reachable_once_separation_is_proven(tmp_path):
    """The accept path, so every refusal below is non-vacuous."""
    result = authorize(tmp_path)
    assert result.returncode == OK, result.stderr
    assert "PERMITTED" in result.stdout


def test_a_free_form_approval_string_is_no_longer_a_gate(tmp_path):
    """`APPROVAL_REF` was text the executor composes, so it gated nothing."""
    result = run("DISCLOSURE_AUTHORIZED", tmp_path, prove_separation,
                 APPROVAL_REF="I hereby approve", OBSERVED_SNAPSHOT=write_snapshot(tmp_path))
    assert result.returncode == FAIL
    assert "requires DECISION_RECEIPT" in result.stderr


def test_a_wrong_receipt_schema_is_refused(tmp_path):
    result = run("DISCLOSURE_AUTHORIZED", tmp_path, prove_separation,
                 DECISION_RECEIPT=write_receipt(tmp_path, schema="secb.something-else/v1"),
                 OBSERVED_SNAPSHOT=write_snapshot(tmp_path))
    assert result.returncode == FAIL
    assert "is not secb.agentic-decision-receipt/v1" in result.stderr


def test_a_missing_role_is_refused(tmp_path):
    roles = {r: {"actor_id": f"app/{r}", "decision": "AUTHORIZE"} for r in BALLOT_ROLES}
    result = run("DISCLOSURE_AUTHORIZED", tmp_path, prove_separation,
                 DECISION_RECEIPT=write_receipt(tmp_path, roles=roles),
                 OBSERVED_SNAPSHOT=write_snapshot(tmp_path))
    assert result.returncode == FAIL
    assert "omits roles" in result.stderr


def test_one_actor_wearing_every_role_is_refused(tmp_path):
    """Five hats, mechanized. The defect is structural, not stylistic."""
    roles = {r: {"actor_id": "app/one-account", "decision": "AUTHORIZE"}
             for r in BALLOT_ROLES + EFFECT_ROLES}
    result = run("DISCLOSURE_AUTHORIZED", tmp_path, prove_separation,
                 DECISION_RECEIPT=write_receipt(tmp_path, roles=roles),
                 OBSERVED_SNAPSHOT=write_snapshot(tmp_path))
    assert result.returncode == FAIL
    assert "one actor holds several roles" in result.stderr


def test_the_executor_may_not_also_be_a_ballot_agent(tmp_path):
    """Deciding and executing must not share a failure mode."""
    roles = {
        **{r: {"actor_id": f"app/{r.lower()}", "decision": "AUTHORIZE"} for r in BALLOT_ROLES},
        "EFFECT_EXECUTOR": {"actor_id": "app/adversarial_reviewer"},
        "READBACK_VERIFIER": {"actor_id": "app/readback"},
    }
    result = run("DISCLOSURE_AUTHORIZED", tmp_path, prove_separation,
                 DECISION_RECEIPT=write_receipt(tmp_path, roles=roles),
                 OBSERVED_SNAPSHOT=write_snapshot(tmp_path))
    assert result.returncode == FAIL
    assert "one actor holds several roles" in result.stderr


def test_the_readback_verifier_may_not_be_the_executor(tmp_path):
    """The producer/consumer boundary applied to an external effect."""
    roles = {
        **{r: {"actor_id": f"app/{r.lower()}", "decision": "AUTHORIZE"} for r in BALLOT_ROLES},
        "EFFECT_EXECUTOR": {"actor_id": "app/executor"},
        "READBACK_VERIFIER": {"actor_id": "app/executor"},
    }
    result = run("DISCLOSURE_AUTHORIZED", tmp_path, prove_separation,
                 DECISION_RECEIPT=write_receipt(tmp_path, roles=roles),
                 OBSERVED_SNAPSHOT=write_snapshot(tmp_path))
    assert result.returncode == FAIL
    assert "may not certify its own effect" in result.stderr


def test_a_ballot_role_that_did_not_authorize_is_refused(tmp_path):
    roles = {
        **{r: {"actor_id": f"app/{r.lower()}", "decision": "AUTHORIZE"} for r in BALLOT_ROLES},
        **{r: {"actor_id": f"app/{r.lower()}"} for r in EFFECT_ROLES},
    }
    roles["ADVERSARIAL_REVIEWER"]["decision"] = "ABSTAIN"
    result = run("DISCLOSURE_AUTHORIZED", tmp_path, prove_separation,
                 DECISION_RECEIPT=write_receipt(tmp_path, roles=roles),
                 OBSERVED_SNAPSHOT=write_snapshot(tmp_path))
    assert result.returncode == FAIL
    assert "ADVERSARIAL_REVIEWER did not record AUTHORIZE" in result.stderr


@pytest.mark.parametrize("field", list(SNAPSHOT))
def test_a_receipt_bound_to_a_changed_snapshot_is_stale(tmp_path, field):
    """A decision is about a state, not about a repository in general."""
    result = run("DISCLOSURE_AUTHORIZED", tmp_path, prove_separation,
                 DECISION_RECEIPT=write_receipt(tmp_path),
                 OBSERVED_SNAPSHOT=write_snapshot(tmp_path, **{field: "changed"}))
    assert result.returncode == FAIL
    assert "RECEIPT_STALE" in result.stderr
    assert field in result.stderr


def test_an_absent_observation_is_refused_not_assumed_current(tmp_path):
    result = run("DISCLOSURE_AUTHORIZED", tmp_path, prove_separation,
                 DECISION_RECEIPT=write_receipt(tmp_path))
    assert result.returncode == FAIL
    assert "OBSERVED_SNAPSHOT is required" in result.stderr


def test_a_failed_credential_cutover_is_refused(tmp_path):
    """A secret still live when logs become public is disclosed, not rotated."""
    snapshot = dict(SNAPSHOT, credential_cutover_result="PENDING")
    result = run("DISCLOSURE_AUTHORIZED", tmp_path, prove_separation,
                 DECISION_RECEIPT=write_receipt(tmp_path, snapshot=snapshot),
                 OBSERVED_SNAPSHOT=write_snapshot(tmp_path, credential_cutover_result="PENDING"))
    assert result.returncode == FAIL
    assert "#115" in result.stderr


def test_an_unreadable_receipt_fails_closed(tmp_path):
    result = run("DISCLOSURE_AUTHORIZED", tmp_path, prove_separation,
                 DECISION_RECEIPT=str(tmp_path / "absent.json"),
                 OBSERVED_SNAPSHOT=write_snapshot(tmp_path))
    assert result.returncode == FAIL
    assert "receipt unreadable or unparseable" in result.stderr


def test_skipping_a_state_is_refused(tmp_path):
    result = run("VISIBILITY_PUBLIC")
    assert result.returncode == FAIL
    assert "skips" in result.stderr


def test_a_backwards_transition_is_refused(tmp_path):
    result = run(
        "DISCLOSURE_UNAPPROVED", tmp_path,
        lambda d: d.update(lifecycle_state="VISIBILITY_PUBLIC"),
    )
    assert result.returncode == FAIL
    assert "does not advance" in result.stderr
    assert "disclosure is not undone" in result.stderr


@pytest.mark.parametrize("bogus", ["PUBLIC", "DONE", "", "disclosure_approved"])
def test_an_unknown_target_state_is_refused(bogus):
    result = run(bogus)
    assert result.returncode == FAIL
    assert "not a known state" in result.stderr or "no target state" in result.stderr


def test_an_unknown_current_state_is_refused(tmp_path):
    result = run("ORG_TRANSFERRED", tmp_path, lambda d: d.update(lifecycle_state="WHATEVER"))
    assert result.returncode == FAIL
    assert "not a known state" in result.stderr


# --- the transition an executor may never self-authorize ----------------------


def test_the_authority_model_is_agentic_not_human_per_instance():
    """`IDENTITY_SEPARATION_UNPROVEN` is a missing substrate, not a reversion."""
    separation = manifest()["agentic_authorization"]["identity_separation"]
    assert separation["status"] == "IDENTITY_SEPARATION_UNPROVEN"
    assert "NOT a reversion to per-instance human approval" in separation["consequence"]
    for unproven in ("Administration(write)", "OIDC", "attestation"):
        assert any(unproven in item for item in separation["not_proven"]), (
            f"{unproven} must be named as a capability or identity, not authority"
        )


def test_the_mandate_source_is_declared_absent_rather_than_stubbed():
    """A placeholder digest would make an unsatisfiable precondition look satisfied."""
    binding = manifest()["agentic_authorization"]["snapshot_binding"]
    assert binding["mandate_source"] == "config/business_mandate.json"
    assert "ABSENT FROM main" in binding["mandate_source_state"]


# --- observation, verification, enforcement ----------------------------------


def test_capabilities_observed_is_refused_while_readback_is_unobserved(tmp_path):
    """Unmeasured is not absent, and not available."""
    def advance(d):
        d["lifecycle_state"] = "VISIBILITY_PUBLIC"
    result = run("CAPABILITIES_OBSERVED", tmp_path, advance)
    assert result.returncode == FAIL
    assert "NOT_OBSERVED" in result.stderr
    assert "unmeasured" in result.stderr


def test_configured_intent_does_not_satisfy_verification(tmp_path):
    """The core substitution: intent is not a verified control."""
    def advance(d):
        d["lifecycle_state"] = "CONTROLS_CONFIGURED"
        for name in CAPABILITIES:
            d["capabilities"][name]["configured_intent"] = "required checks on main"
    result = run("CONTROLS_VERIFIED", tmp_path, advance)
    assert result.returncode == FAIL
    assert "Configured intent is not verification" in result.stderr


def test_one_verified_capability_does_not_carry_the_others(tmp_path):
    def advance(d):
        d["lifecycle_state"] = "CONTROLS_CONFIGURED"
        d["capabilities"]["rulesets"]["verified"] = True
    result = run("CONTROLS_VERIFIED", tmp_path, advance)
    assert result.returncode == FAIL
    assert "merge_queue is not verified" in result.stderr


def test_selective_activation_with_nothing_enforced_is_refused(tmp_path):
    def advance(d):
        d["lifecycle_state"] = "CONTROLS_VERIFIED"
    result = run("SELECTIVELY_ACTIVATED", tmp_path, advance)
    assert result.returncode == FAIL
    assert "nothing to activate" in result.stderr


def test_a_producer_may_not_record_a_consumer_stage(tmp_path):
    """`#134`'s boundary, enforced here rather than restated."""
    def advance(d):
        d["transition_evidence"]["CONSUMER_VERIFIED"] = "looks fine to me"
    result = authorize(tmp_path, mutate=lambda d: (prove_separation(d), advance(d))[0])
    assert result.returncode == FAIL
    assert "cannot certify" in result.stderr


# --- fail-closed on the manifest itself --------------------------------------


def test_post_effect_readback_mismatch_is_declared_unverified():
    """A 200 proves a call was accepted, not that the state is the one decided."""
    post = manifest()["agentic_authorization"]["post_effect"]
    assert post["effect_succeeded_readback_mismatch"] == "EFFECT_UNVERIFIED"
    assert "separate actor" in post["why"]


def test_an_absent_manifest_fails_closed():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "DISCLOSURE_AUTHORIZED"],
        capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=30,
        env={"PATH": "/usr/bin:/bin", "MANIFEST": "/nonexistent/manifest.json"},
    )
    assert result.returncode == FAIL
    assert "unreadable or unparseable" in result.stderr


def test_a_malformed_manifest_fails_closed(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text('{"lifecycle_state": "DISCLOSURE_UNAPPROVED"', encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "DISCLOSURE_AUTHORIZED"],
        capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=30,
        env={"PATH": "/usr/bin:/bin", "MANIFEST": str(path)},
    )
    assert result.returncode == FAIL


def test_a_manifest_missing_a_capability_fails_closed(tmp_path):
    def break_it(d):
        d["lifecycle_state"] = "VISIBILITY_PUBLIC"
        del d["capabilities"]["merge_queue"]
    result = run("CAPABILITIES_OBSERVED", tmp_path, break_it)
    assert result.returncode == FAIL
    assert "malformed manifest" in result.stderr


# --- what the controller cites rather than restates --------------------------


def test_the_evidence_lifecycle_is_cited_not_copied():
    """Criterion 4 without a competing definition.

    The stage vocabulary belongs to `secb.pr-input-binding/v1` (#134, unmerged). Copying
    the list here would create a second source that drifts from the first — the defect
    #135 records for parser duplication, one layer up.
    """
    lifecycle = manifest()["evidence_lifecycle"]
    assert lifecycle["restated_here"] is False
    assert "scripts/emit_pr_input_binding.py" in lifecycle["canonical_source"]
    assert "UNMERGED" in lifecycle["canonical_source_state"]
    assert set(lifecycle["producer_may_not_certify"]) == {
        "CONSUMER_VERIFIED", "ENFORCEMENT_APPLIED"
    }


def test_the_referenced_obligations_are_not_closed_by_this_manifest():
    """Pointing at an obligation must not discharge it."""
    obligations = {o["issue"]: o for o in manifest()["independent_obligations"]}
    assert set(obligations) == {117, 118, 119}
    for issue, obligation in obligations.items():
        assert obligation["closed_by_this_manifest"] is False, (
            f"#{issue} must remain open on its own terms"
        )


def test_the_merge_queue_prerequisite_names_the_skipped_checks_defect():
    """Enabling the queue before `ci.yml` handles `merge_group` produces skipped checks."""
    capability = manifest()["capabilities"]["merge_queue"]
    assert "merge_group" in capability["blocking_prerequisite"]
    assert "SKIPPED" in capability["blocking_prerequisite"]
    assert capability["membership_proof"].startswith("NOT_PROVEN")
