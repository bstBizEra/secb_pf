"""Characterization fixtures for the two defect classes ruled `d = 2`.

`SECB-WP-FWK-063`. These tests assert **what the tree does today**, compared against
a *declared* status in `docs/09-testing/negative_test_status.json` — not against what
it ought to do. A test written to assert the correct behaviour would fail now and be
deleted or skipped; a test asserting the defect without a declared status reddens CI
the day someone fixes it. Both failure modes were paid for once already, in `§P1` of
the negative-test lifecycle.

Two corrections came out of the review of the first version, and both are the same
mistake in different places:

* the lifecycle check searched the standard's **prose** for `PROPOSED`, which a
  historical passage could satisfy. It now parses the canonical metadata block.
* the `AMS-02` fixture asserted that no receipt **artifact** existed, so a filename
  could have flipped the status. It now asserts that nothing **consumes** a receipt,
  and the flip requires proven enforcement behaviour.

*Presence is not enforcement* is the defect class the standard exists to eliminate,
so a fixture that accepts presence as evidence reproduces it while testing for it.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
STATUS_FILE = REPO_ROOT / "docs" / "09-testing" / "negative_test_status.json"
STANDARD = REPO_ROOT / "docs" / "00-governance" / "AUTO_MERGE_STANDARD.md"
CLASSIFIER = REPO_ROOT / "scripts" / "classify_authority_delta.py"

AUTO_APPROVED = 0
ESCALATE = 2


def scenario(scenario_id: str) -> dict:
    data = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
    for entry in data["scenarios"]:
        if entry["id"] == scenario_id:
            return entry
    raise AssertionError(f"{scenario_id} is not declared in negative_test_status.json")


VALID_LIFECYCLE_STATES = {"PROPOSED", "ACTIVE", "SUPERSEDED"}


def standard_metadata() -> dict:
    """Parse the standard's canonical metadata block, strictly.

    Not a substring search over the document, and not dependent on a YAML library
    the gates are not allowed to import. Hardened under review, because a parser
    that is merely *better* than grep still lets several things through:

    * the fence must be the **first** one and must follow the title immediately, so
      a later example block cannot be read as the document's status;
    * **duplicate top-level keys are rejected** — last-wins would let a second
      `binding:` silently override the first;
    * `standard_id` and a semantic `version` are required, so an unversioned
      document cannot claim a lifecycle.
    """
    return parse_metadata(STANDARD.read_text(encoding="utf-8"))


def parse_metadata(text: str) -> dict:
    """The parser proper, taking text so its guards can be exercised.

    `standard_metadata()` reads the file; this takes a string. Split under review
    for one reason: a parser that only ever sees a well-formed document has
    untested rejection paths, and "the guard exists" is not "the guard fires" —
    the precise substitution this standard was written to forbid.
    """
    lines = text.splitlines()

    assert lines and lines[0].startswith("# "), "the standard must open with a title"
    body_start = next(
        (i for i, line in enumerate(lines[1:], start=1) if line.strip()), len(lines)
    )
    assert lines[body_start].strip() == "```yaml", (
        "the metadata fence must immediately follow the title; found "
        f"{lines[body_start]!r}. A fence further down could be an example block."
    )

    meta: dict[str, str] = {}
    seen: set[str] = set()
    for line in lines[body_start + 1:]:
        if line.strip() == "```":
            break
        if line.startswith((" ", "\t")) or ":" not in line:
            continue  # nested value or continuation, not a top-level field
        key, _, value = line.partition(":")
        key = key.strip()
        assert key not in seen, (
            f"duplicate top-level metadata key {key!r}: last-wins parsing would let a "
            "second declaration silently override the first"
        )
        seen.add(key)
        meta[key] = value.strip()

    assert meta.get("standard_id"), "metadata must carry a standard_id"
    assert re.fullmatch(r"\d+\.\d+\.\d+", meta.get("version", "")), (
        f"version must be semantic, got {meta.get('version')!r}"
    )
    state = meta.get("lifecycle_state")
    assert state in VALID_LIFECYCLE_STATES, (
        f"unknown lifecycle_state {state!r}; valid: {sorted(VALID_LIFECYCLE_STATES)}"
    )
    if meta.get("binding") == "true":
        assert meta.get("ratification_receipt", "null") != "null", (
            "binding: true requires a ratification receipt"
        )
    if state == "PROPOSED":
        assert meta.get("effective_event", "null") == "null", (
            "a PROPOSED standard must not carry an effective event"
        )
    return meta


# --- the parser's guards, proven to fire -------------------------------------

GOOD = """# T

```yaml
standard_id: SECB-AMS-001
version: 0.2.0
lifecycle_state: PROPOSED
binding: false
effective_event: null
ratification_receipt: null
```
"""


def test_parser_accepts_the_canonical_shape():
    """The baseline, so the rejections below are not vacuous."""
    assert parse_metadata(GOOD)["standard_id"] == "SECB-AMS-001"


@pytest.mark.parametrize(
    "mutation,replacement,why",
    [
        ("binding: false", "binding: false\nbinding: true", "duplicate key overrides"),
        ("version: 0.2.0", "version: 0.2", "non-semantic version"),
        ("lifecycle_state: PROPOSED", "lifecycle_state: ISSUED", "unknown state"),
        ("standard_id: SECB-AMS-001", "standard_id:", "empty standard_id"),
        (
            "binding: false",
            "binding: true",
            "binding without a receipt",
        ),
        (
            "effective_event: null",
            "effective_event: RATIFIED",
            "PROPOSED with an effective event",
        ),
    ],
)
def test_parser_rejects_malformed_metadata(mutation, replacement, why):
    with pytest.raises(AssertionError):
        parse_metadata(GOOD.replace(mutation, replacement))
    assert why  # the label is the point of the row


def test_parser_rejects_a_fence_that_is_not_the_first_block():
    """A prose paragraph before the fence means the block may be an example."""
    displaced = GOOD.replace("# T\n", "# T\n\nSome prose about a past state.\n")
    with pytest.raises(AssertionError, match="immediately follow the title"):
        parse_metadata(displaced)


def test_lifecycle_cross_field_invariants_hold():
    """A state and its consequences must agree, in both directions."""
    meta = standard_metadata()
    state = meta["lifecycle_state"]
    binding = meta["binding"]
    effective = meta["effective_event"]
    receipt = meta["ratification_receipt"]

    if state == "PROPOSED":
        assert binding == "false", "PROPOSED implies binding: false"
        assert effective == "null", "a PROPOSED standard has no effective event"
        assert receipt == "null", "a PROPOSED standard has no ratification receipt"
    elif state == "ACTIVE":
        assert binding == "true", "ACTIVE implies binding: true"
        assert effective != "null", "ACTIVE requires an effective event"
        assert receipt != "null", (
            "ACTIVE requires a ratification receipt — binding: true with no receipt is "
            "force asserted without authority, which is the defect this file records"
        )
    elif state == "SUPERSEDED":
        assert binding == "false", "SUPERSEDED implies binding: false"
        assert meta.get("supersedes", "null") != "null", (
            "SUPERSEDED requires a successor reference, or the chain breaks"
        )


def test_merge_records_the_proposal_and_does_not_activate_it():
    """`C-AMS-02`: landing and effectuation are separate transitions.

    Merging the pull request that adds this file must not be readable as
    ratification. The metadata says so as data rather than leaving it to prose.
    """
    text = STANDARD.read_text(encoding="utf-8")
    assert "records_proposal: true" in text
    assert "activates_standard: false" in text
    assert "supplies_ratification: false" in text, (
        "merge_effect must state all three, because a merge that could be read as "
        "activation is exactly the ambiguity the review flagged"
    )


def run_classifier(numstat: str, diff_text: str = "") -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k not in ("DIFF_PATH", "DIFF_TEXT")}
    env["DIFF_TEXT"] = diff_text
    return subprocess.run(
        [sys.executable, str(CLASSIFIER)],
        input=numstat,
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )


# --- the standard's own status is machine-readable ---------------------------


def test_standard_declares_its_lifecycle_in_parseable_metadata():
    """A governance document must not read as binding because it is present."""
    meta = standard_metadata()
    for field in ("standard_id", "version", "lifecycle_state", "binding"):
        assert field in meta, f"the standard's metadata block is missing {field!r}"
    assert meta["lifecycle_state"] == "PROPOSED", (
        f"lifecycle_state is {meta['lifecycle_state']!r}. If an authority has landed "
        "this standard, that is a governance event with a receipt — update the "
        "metadata and this assertion together, deliberately."
    )
    assert meta["binding"] == "false", (
        "binding must be false while lifecycle_state is PROPOSED; a document that "
        "claims force it has not been granted is the ISSUED defect in a file path"
    )
    assert meta["effective_event"] == "null" and meta["ratification_receipt"] == "null", (
        "a PROPOSED standard has no effective event and no ratification receipt"
    )


def test_lifecycle_is_not_asserted_by_prose_search():
    """Guards the guard: the words alone must not be able to satisfy the check.

    The first version of this module searched the document for `PROPOSED`. This
    asserts the document still contains that word in commentary — so that if someone
    later replaces the metadata parse with a substring search, the weaker check would
    pass on prose and the reviewer has this test to point at.
    """
    text = STANDARD.read_text(encoding="utf-8")
    assert text.count("PROPOSED") > 1, (
        "the word appears in commentary as well as metadata, which is exactly why the "
        "metadata block rather than the prose is authoritative"
    )


# --- AMS-01 — authority requirement is a lattice join, not a path lookup -----

DECISION_RECORD_NUMSTAT = "27\t5\tdocs/13-evidence/STAGE_GATE_REQUIREMENTS_READY.md\n"


def test_gap_decision_record_under_docs_still_grades_g0():
    """`AMS-01`: reproduces the #111 class against its declared status."""
    declared = scenario("AMS-01")["status"]
    result = run_classifier(DECISION_RECORD_NUMSTAT)

    if declared == "GAP_REPRODUCED":
        assert result.returncode == AUTO_APPROVED and "G0" in result.stdout, (
            "AMS-01 is declared GAP_REPRODUCED, meaning a stage-gate decision record "
            "still grades G0 on its path alone. It no longer does — good news and a "
            "status update: flip AMS-01 to CONTROL_FIXED and this assertion inverts.\n"
            f"stdout: {result.stdout.strip()}"
        )
    elif declared == "CONTROL_FIXED":
        assert result.returncode == ESCALATE, (
            "AMS-01 is declared CONTROL_FIXED, so a decision record must no longer "
            f"satisfy G0. It still does: {result.stdout.strip()}"
        )
    else:
        pytest.fail(f"AMS-01 carries an unhandled status: {declared!r}")


# --- AMS-02 — nothing consumes a receipt, which is the actual gap ------------

RECEIPT_TOKENS = ("ratification_receipt", "ratification-receipt", "RATIFICATION_RECEIPT")


def _consumers_of_a_receipt() -> list[str]:
    """Files in the *enforcement* surface that read a ratification receipt.

    Scoped to `scripts/` and `.github/` on purpose. A receipt named in a governance
    document is a description; a receipt read by a gate is a control.
    """
    hits = []
    for directory in ("scripts", ".github"):
        base = REPO_ROOT / directory
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if any(token in text for token in RECEIPT_TOKENS):
                hits.append(str(path.relative_to(REPO_ROOT)))
    return sorted(hits)


def test_gap_no_enforcement_consumes_a_receipt():
    """`AMS-02`: reproduces the #120 class — and does not accept presence as proof."""
    entry = scenario("AMS-02")
    declared = entry["status"]
    consumers = _consumers_of_a_receipt()

    if declared == "GAP_REPRODUCED":
        assert not consumers, (
            "AMS-02 is declared GAP_REPRODUCED — nothing in scripts/ or .github/ "
            f"consumes a ratification receipt. These now do: {consumers}. That is not "
            "yet grounds to flip the status: see flip_requires, which asks for six "
            "enforcement behaviours, not for a consumer to exist."
        )
    elif declared == "CONTROL_FIXED":
        proof = REPO_ROOT / "tests" / "test_ratification_enforcement.py"
        assert proof.is_file(), (
            "AMS-02 cannot be CONTROL_FIXED without the enforcement proof named in "
            f"its enforcement_proof field: {proof.name} is absent"
        )
        text = proof.read_text(encoding="utf-8")
        for behaviour in ("missing", "wrong actor", "COMMENT", "mismatch", "STALE", "PASS"):
            assert behaviour.lower() in text.lower(), (
                f"the enforcement proof does not exercise {behaviour!r}; all six "
                "behaviours in flip_requires must be covered before the flip"
            )
    else:
        pytest.fail(f"AMS-02 carries an unhandled status: {declared!r}")


def test_ams_02_flip_criteria_are_behavioural_not_artifactual():
    """The scenario must state what closing it *does*, not what it *contains*."""
    entry = scenario("AMS-02")
    flip = entry.get("flip_requires") or []
    assert len(flip) == 6, "AMS-02 must carry the six enforcement behaviours"
    joined = " ".join(flip).upper()
    assert "DENY" in joined and "STALE" in joined and "PASS" in joined, (
        "flip_requires must name outcomes — DENY, STALE, PASS — because a criterion "
        "phrased as 'a receipt exists' is satisfied by writing a file"
    )
    assert "C-7" in entry.get("blocked_by", ""), (
        "AMS-02 must cite C-7: the receipt is unobtainable under one identity, and a "
        "gap recorded without its blocker reads as neglect rather than as capability"
    )


# --- both scenarios must remain honest about what they are -------------------


@pytest.mark.parametrize("scenario_id", ["AMS-01", "AMS-02"])
def test_scenarios_declare_fix_fixture_and_non_conformance(scenario_id):
    entry = scenario(scenario_id)
    assert entry.get("named_fix"), f"{scenario_id} must name the fix that closes it"
    assert entry.get("characterization_fixture"), f"{scenario_id} must point at its fixture"
    assert entry.get("flip_requires"), f"{scenario_id} must state its flip criteria"
    assert "not_a_conformance_requirement" in entry, (
        f"{scenario_id} is GAP_REPRODUCED; without this field a later reader treats "
        "the reproduced defect as the required behaviour"
    )
