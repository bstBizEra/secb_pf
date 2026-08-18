"""The production mandate is recorded, not adopted -- and its measured claims are pinned.

Two distinct jobs. The first four tests hold the RECORD/ADOPT separation: a mandate that
arrives and is simultaneously acted upon has no reviewable moment, so the document must keep
saying it grants nothing.

The rest pin the *measurable* assertions in its baseline section. A governance document that
states a measurement will drift out of truth silently as the tree moves -- eight open pull
requests in this repository were found stating diff and test figures that matched no
measurement of anything. A stated measurement with no guard is a claim waiting to become false.

    STATED_AS_MEASURED ∧ UNGUARDED → SILENTLY_FALSIFIABLE

So each pinned claim fails HERE, in this suite, at the moment the tree stops matching the
document -- which is also the moment the document should be updated.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC = REPO_ROOT / "docs" / "00-governance" / "PRODUCTION_ADVANCEMENT_MANDATE.md"
TEXT = DOC.read_text(encoding="utf-8")


# --- the record/adopt separation --------------------------------------------


def test_the_document_records_the_mandate_without_adopting_it():
    assert "PROPOSED — RECORDED, NOT ADOPTED" in TEXT, (
        "the status line no longer marks this as recorded-not-adopted. A mandate document "
        "that reads as adopted confers a stage model nobody ratified."
    )
    assert "It does not enact one" in TEXT


def test_no_stage_verdict_may_cite_this_document_as_authority():
    assert "No stage verdict may cite this document as authority" in TEXT


def test_the_document_separates_receiving_a_mandate_from_being_granted_authority():
    assert "MANDATE_RECEIVED ≠ AUTHORITY_GRANTED" in TEXT, (
        "the distinction between a mandate arriving and authority existing is the one this "
        "document exists to keep visible"
    )


def test_the_document_names_its_own_limits():
    for claim in (
        "Not an adoption of the stage model",
        "Not a scope change",
        "Not an authorization to build production infrastructure",
        "no independent verification",
    ):
        assert claim in TEXT, f"the limits section no longer states: {claim!r}"


# --- the pinned measurements ------------------------------------------------


def test_infra_and_templates_are_still_empty_as_the_baseline_states():
    # The baseline says Stages 4-8 have NO SUBSTRATE, and rests that partly on these being
    # empty. The day someone adds a deployment topology, this test fails and the baseline
    # must be re-measured -- which is the correct moment to revisit the stage assessment.
    for name in ("infra", "templates"):
        entries = {p.name for p in (REPO_ROOT / name).iterdir()} - {".gitkeep"}
        assert not entries, (
            f"{name}/ now contains {sorted(entries)}, but the mandate's baseline records it as "
            f"EMPTY and concludes NO_SUBSTRATE for Stages 4-8 partly on that basis. Re-measure "
            f"§4 and the stage assessment in the same change."
        )


def test_there_is_still_no_service_entrypoint_as_the_baseline_states():
    present = [
        n for n in ("pyproject.toml", "Dockerfile", "docker-compose.yml", "compose.yaml", "Makefile")
        if (REPO_ROOT / n).exists()
    ]
    assert not present, (
        f"the baseline records 'no pyproject, container, compose file or MCP server process' and "
        f"{present} now exists. A service entrypoint changes the Stage 4 assessment materially."
    )


def test_the_baseline_source_count_for_src_still_holds():
    files = sorted(p.relative_to(REPO_ROOT).as_posix() for p in (REPO_ROOT / "src").rglob("*.py"))
    assert len(files) == 2, (
        f"the baseline records src/ as 2 files (secb_router); found {len(files)}: {files}. "
        "Update §4 rather than leaving the document asserting a stale figure."
    )


def test_the_declared_no_surface_lines_are_quoted_from_the_real_descriptor_when_it_lands():
    # secb.yaml is not on main yet -- it arrives with SECB-WP-FWK-095. This test is written to
    # start enforcing the moment it does, rather than being added later and forgotten. Until
    # then it records WHY it is inert instead of silently passing.
    descriptor = REPO_ROOT / "secb.yaml"
    if not descriptor.is_file():
        assert "production: NONE_DECLARED" in TEXT and "deploy_and_operate: NO_SURFACE" in TEXT, (
            "the baseline quotes two secb.yaml fields; if the quotes are removed while the "
            "descriptor is still absent, nothing anchors the NO_SUBSTRATE conclusion"
        )
        return
    body = descriptor.read_text(encoding="utf-8")
    for quoted in ("NONE_DECLARED", "NO_SURFACE"):
        assert quoted in body, (
            f"the mandate baseline quotes {quoted!r} from secb.yaml, which no longer contains it. "
            "A document quoting a descriptor that has changed is the metadata-coherence defect "
            "this suite exists to prevent."
        )


def test_the_envelope_ceiling_the_document_cites_is_the_real_one():
    envelope = json.loads((REPO_ROOT / "config" / "delegation_envelope.json").read_text(encoding="utf-8"))
    assert envelope["absolute_ceilings"]["max_tier"] == "A4", (
        "the document blocks Stage 7+ on the envelope capping at A4. The envelope now caps "
        f"elsewhere ({envelope['absolute_ceilings']['max_tier']}), so that reasoning must be redone."
    )
    assert envelope["current_tier"] == "A1"
    assert envelope["ballot_layer"]["state"] == "NOT_ACTIVE", (
        "the document rests on the ballot layer being NOT_ACTIVE. If it is now active, the "
        "Stage 7 blocking analysis changes and §5 must be re-derived."
    )


def test_every_stage_in_the_ladder_declares_exactly_one_exit_verdict():
    verdicts = [
        "BOOTSTRAP_VERIFIED", "CONTROL_PLANE_INTEGRATED", "GOVERNED_EXECUTION_PROVEN",
        "GOVERNED_LEARNING_PROVEN", "PRODUCTION_ENGINEERING_READY", "SECURITY_ASSURANCE_PASSED",
        "OPERATIONALLY_READY", "PRODUCTION_ACTIVATED", "PRODUCTION_VALIDATED",
        "GOVERNED_AUTONOMOUS_OPERATION",
    ]
    assert len(verdicts) == len(set(verdicts)) == 10
    for v in verdicts:
        assert v in TEXT, f"stage ladder is missing its exit verdict {v}"
