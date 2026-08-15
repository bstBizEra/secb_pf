"""The L0 layer table must not outlive the capability state it describes.

`SECB-WP-FWK-070` (issue #129).

The table's single `Who may change it` column fused two different facts: the route the
constitution *intends*, and the route that can be *taken today*. Under that fusion,
`L1`'s "agent action … once the ballot layer is active" read as a live agent route while
`ballot_layer.state` has never left `NOT_ACTIVE`, and `L3`'s "agent auto-merge by risk
class" read the same way while no pull request here has ever carried auto-merge.

    DECLARED_ROUTE  ≠  CAPABILITY_AVAILABLE  ≠  LIVE_ROUTE

**What this module can and cannot check.** The ballot layer has a machine-readable state
in the delegation envelope, so the `L1`/`L2` capability cells are checked against it: if
someone activates ballots, the table must be updated or these tests fail. Auto-merge has
**no** equivalent flag in any config file on `main`, so `L3`'s capability cell is
asserted for shape and internal consistency only, not derived from a source of truth. That
gap is stated rather than papered over — a test claiming to verify auto-merge capability
from a file that does not exist would be the defect this repository keeps recording.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CONSTITUTION = REPO_ROOT / "docs" / "00-governance" / "L0_ROOT_CONSTITUTION.md"
ENVELOPE = REPO_ROOT / "config" / "delegation_envelope.json"

LAYERS = ("L0", "L1", "L2", "L3")
FIELDS = ("contents", "declared", "capability", "live_route", "blocker")


def layer_rows() -> dict[str, dict[str, str]]:
    """Parse the layer table into one record per layer."""
    rows: dict[str, dict[str, str]] = {}
    for line in CONSTITUTION.read_text(encoding="utf-8").splitlines():
        match = re.match(r"\|\s*\*\*(L[0-3]) —", line)
        if not match:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        assert len(cells) == 6, (
            f"{match.group(1)} has {len(cells)} cells; the projection requires 6 "
            "(layer, contents, declared, capability, live route, blocker)"
        )
        rows[match.group(1)] = dict(zip(FIELDS, cells[1:]))
    assert set(rows) == set(LAYERS), f"expected rows for {LAYERS}, parsed {sorted(rows)}"
    return rows


def ballot_state() -> str:
    return json.loads(ENVELOPE.read_text(encoding="utf-8"))["ballot_layer"]["state"]


@pytest.mark.parametrize("layer", LAYERS)
def test_every_layer_carries_all_five_operational_fields(layer):
    row = layer_rows()[layer]
    for field in FIELDS:
        assert row[field], f"{layer} has an empty {field!r} cell"


@pytest.mark.parametrize("layer", ("L1", "L2"))
def test_ballot_dependent_rows_agree_with_the_envelope(layer):
    """The guard that makes a capability change impossible to leave silent.

    `L1` and `L2` both depend on the ballot layer. If it is activated in the envelope
    and this table still reports it unavailable, the table is describing a deployment
    that no longer exists — and a reader would under-use authority that had been
    granted. The failure is symmetric, which is the point.
    """
    row = layer_rows()[layer]
    combined = f"{row['capability']} {row['blocker']}".lower()

    # Any wording that asserts ballots are unavailable, not only the literal token.
    # The first version of this guard matched `NOT_ACTIVE` alone and therefore caught
    # L1 while letting L2 -- which says "ballots are not" -- go stale unnoticed. A
    # guard that covers one of the two rows it names is a half-guard.
    claims_unavailable = any(
        phrase in combined
        for phrase in ("not_active", "ballots are not", "ballot layer inactive", "ballots are unavailable")
    )

    if ballot_state() == "ACTIVE":
        assert not claims_unavailable, (
            f"the envelope reports ballot_layer ACTIVE while {layer} still says "
            f"{row['capability']!r} / {row['blocker']!r}. Update the table with the "
            "capability change, not after it"
        )
    else:
        assert claims_unavailable, (
            f"{layer} depends on the ballot layer, which is {ballot_state()}, but the "
            "row names neither the state nor the blocker"
        )


def test_no_agent_route_is_presented_as_live_while_ballots_are_inactive():
    """A live route means executable now, by the actor named.

    `L1`'s declared route is agent action once ballots are active. While they are not,
    no row's *live* cell may hand a route to an agent alone — every reachable path ends
    at a human merge.
    """
    if ballot_state() == "ACTIVE":
        pytest.skip("ballot layer is active; this constraint no longer applies")
    for layer, row in layer_rows().items():
        live = row["live_route"].lower()
        if "agent" in live:
            assert "human" in live, (
                f"{layer}'s live route names an agent without a human merge while "
                f"ballot_layer is {ballot_state()}: {row['live_route']!r}"
            )


def test_declared_routes_are_preserved_not_deleted():
    """Unreachable is not the same as abandoned.

    Recording a route as declared-but-blocked is what makes the blocker actionable.
    Deleting it would lose the design and quietly narrow the constitution.
    """
    rows = layer_rows()
    assert "ballot layer is active" in rows["L1"]["declared"], (
        "L1's declared authority must still name the ballot-gated agent route"
    )
    assert "auto-merge" in rows["L3"]["declared"].lower(), (
        "L3's declared authority must still name agent auto-merge by risk class"
    )


def test_every_unavailable_capability_names_its_blocker():
    """`UNAVAILABLE` with no blocker is a dead end rather than a work item."""
    for layer, row in layer_rows().items():
        if "UNAVAILABLE" in row["capability"] or "PARTIAL" in row["capability"]:
            assert row["blocker"] and "None" not in row["blocker"], (
                f"{layer} reports {row['capability']!r} but names no blocker"
            )


def test_the_correction_does_not_close_an_open_condition():
    """`C-6` and `C-7` are the operator's to close, not a table edit's.

    A rewrite of an authority surface is exactly where a condition could be closed by
    implication, so it is asserted explicitly.
    """
    text = CONSTITUTION.read_text(encoding="utf-8")
    for closed in ("C-6 is closed", "C-7 is closed", "C-6 satisfied", "C-7 satisfied"):
        assert closed not in text, f"the constitution now asserts {closed!r}"
    assert "`C-6` and `C-7` remain open" in text
