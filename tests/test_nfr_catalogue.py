"""The NFR catalogue must agree with the tree it describes — `SECB-WP-FWK-069`.

`NFR-17`'s row said *"manual repository scan — still not mechanized"* and named
`scripts/check_committed_secrets.py` as unmerged in PR #101. The script merged, ran as
a continuous check on every pull request, and the row kept describing a manual process.
The row even carried its own instruction — *"Update this row when #101 merges"* — which
is a reminder, and a reminder is not a control.

**This is an underclaim, and it is the same fault as an overclaim.** The record and the
tree disagreed. Underclaims are the more comfortable half of that fault, because a
control that turns out to exist embarrasses nobody, so nothing forces the correction.
This module is what forces it.

The generalization is deliberately narrow: for every NFR row naming a `scripts/*.py`
control, the row's description of that control's *state* must match whether the script
is tracked and wired. It does not attempt to judge whether the control is any good.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOGUE = REPO_ROOT / "docs" / "01-requirements" / "NFR_CATALOGUE.md"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"

# Phrases that assert a control is not in force. If a row contains one of these while
# naming a script that is both tracked and wired, the row is describing a tree that no
# longer exists.
NOT_IN_FORCE = (
    "not mechanized",
    "unmerged",
    "still not",
    "verified by hand only",
)


def tracked(path: str) -> bool:
    """Tracked, not merely present.

    An untracked file is invisible to a fresh clone, so `Path.exists()` would let a
    local-only script satisfy a claim the repository cannot keep.
    """
    out = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files", "--error-unmatch", path],
        capture_output=True,
        text=True,
    )
    return out.returncode == 0


def nfr_rows() -> dict[str, str]:
    rows: dict[str, str] = {}
    for line in CATALOGUE.read_text(encoding="utf-8").splitlines():
        match = re.match(r"\|\s*`(NFR-\d+)`\s*\|", line)
        if match:
            rows[match.group(1)] = line
    assert rows, "no NFR rows parsed — the catalogue's table shape changed"
    return rows


def test_nfr_17_no_longer_describes_a_control_that_is_in_force_as_absent():
    """The defect this work package exists to close."""
    row = nfr_rows()["NFR-17"]
    script = "scripts/check_committed_secrets.py"
    assert tracked(script), f"{script} is not tracked; the correction rests on it being shipped"
    assert script in WORKFLOW.read_text(encoding="utf-8"), (
        f"{script} is not wired into ci.yml — if the check was removed, this row must go "
        "back to describing a manual process, deliberately and not by omission"
    )
    for phrase in NOT_IN_FORCE:
        assert phrase not in row.lower(), (
            f"NFR-17 still says {phrase!r} while the scanner is tracked and wired"
        )
    assert "PR #101" not in row, "the row still cites the pull request it was waiting for"


def test_no_nfr_row_calls_a_wired_script_absent():
    """The general form, so the next row cannot rot the same way.

    For each NFR row naming a `scripts/*.py` file: if that script is tracked **and**
    referenced by the workflow, the row may not also claim the control is not in force.
    """
    workflow = WORKFLOW.read_text(encoding="utf-8")
    for nfr_id, row in nfr_rows().items():
        for script in re.findall(r"scripts/[a-z_]+\.py", row):
            if tracked(script) and script in workflow:
                stale = [p for p in NOT_IN_FORCE if p in row.lower()]
                assert not stale, (
                    f"{nfr_id} names {script}, which is tracked and wired, yet the row "
                    f"still says {stale}. Either the row is stale or the control was "
                    "removed — both need a deliberate edit"
                )


def test_nfr_17_declares_what_the_scan_does_not_prove():
    """A pattern scanner cannot prove absence, only the absence of known shapes.

    Asserted because the correction's whole risk is over-shooting: replacing an
    underclaim with an overclaim would be a worse outcome than leaving it alone.
    """
    text = CATALOGUE.read_text(encoding="utf-8")
    for unproven in (
        "complete secret detection",
        "push protection",
        "provider-side revocation",
        "preventive enforcement",
    ):
        assert unproven in text, f"NFR-17's correction must state it does not prove {unproven!r}"
    assert "preventive_branch_enforcement: UNAVAILABLE" in text


def test_forward_vocabulary_is_marked_as_a_forward_reference():
    """`CS3` is defined in #124, which has not landed.

    Writing a term that no registry resolves is the defect #125 records. It is allowed
    here only because it is explicitly pointed at its unlanded source; if that pointer
    is dropped, the row is citing a vocabulary the repository does not have.
    """
    text = CATALOGUE.read_text(encoding="utf-8")
    if "CS3" in text:
        assert "forward reference" in text, (
            "CS3 appears without being marked as a forward reference to #124"
        )

    # Scoped to the projection block, not the whole document. Prose explaining *why* a
    # token is avoided has to be able to name it — the same allowance §2 of the
    # Auto-Merge Standard needs to quote the `max(...)` formula it discarded. A guard
    # that forbids the word everywhere forbids its own justification.
    match = re.search(r"```yaml\n(.*?)```", text[text.index("`NFR-17` correction"):], re.S)
    assert match, "the NFR-17 correction must carry a machine-readable projection block"
    projection = match.group(1)
    assert "ENF1" not in projection, (
        "the projection must record enforcement_level: DETECTIVE, not ENF1 — #125's "
        "ladder is not registered, and minting the token is what #125 corrects"
    )
    assert "enforcement_level: DETECTIVE" in projection
    assert "CS3_DETECTIVE" not in projection, (
        "evidence strength and enforcement level are two ladders; fusing them into one "
        "token is the C-AMS-04 defect"
    )
