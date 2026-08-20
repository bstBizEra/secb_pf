"""Every recorded mandate declares its vocabulary, and the declaration is true.

WHY THIS IS A TEST AND NOT A TOOL. Three consecutive operator mandates introduced identifiers that
collide with `config/identifier_taxonomy.json`, and all three collisions were caught only because
someone checked by hand:

    production advancement (#187)   Stage 0-9, unregistered
    agentic learning (#203)         K0-K9 vs K-01..K-12 KPIs; risk_class C2 vs the R0-R4 risk
                                    ladder; a KN knowledge register that already ships
    absorb loop (this one)          A1-A5 vs the A0-A4 authority ladder; G-ABSORB vs G0-G5 change
                                    classes, while GATE-001..GATE-010 already exists

Three independent episodes is the threshold the absorb mandate itself sets for a general engineering
pattern (§17), so the fourth should not need a person. Per its §15, the weakest sufficient control
for a repeated finding is a diagnostic rule rather than a policy -- so this is a test.

WHAT IT CHECKS, AND WHAT IT CANNOT. It verifies a DECLARATION against the registry. It does not
discover identifiers a document failed to declare.

    DECLARED_VOCABULARY_VERIFIED != VOCABULARY_AUTO_DISCOVERED

That boundary is deliberate and matches the registry's own: `identifier_taxonomy.json` declares its
observation boundary as markdown declaration tables and states plainly that a ladder introduced
elsewhere "is in" its blind spot. Auto-extracting prefixes from prose would flag every document that
merely DISCUSSES a registered ladder -- including this one's own collision analysis -- which is a
false-positive machine, not a guard.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
GOVERNANCE = REPO_ROOT / "docs" / "00-governance"
TAXONOMY = json.loads(
    (REPO_ROOT / "config" / "identifier_taxonomy.json").read_text(encoding="utf-8")
)
LADDERS = {entry["prefix"]: entry for entry in TAXONOMY["ladders"]}
RESERVED = {entry["prefix"] for entry in TAXONOMY["reserved_unbound"]}

ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|([^|]*)\|\s*([A-Z][A-Z -]*[A-Z])\b([^|]*)\|", re.MULTILINE)


def mandates() -> list[Path]:
    found = sorted(GOVERNANCE.glob("*MANDATE*.md"))
    assert found, "no *MANDATE*.md found under docs/00-governance -- this test checks nothing"
    return found


def vocabulary(path: Path) -> list[tuple[str, str, str]]:
    """Return (prefix, purpose, status) rows from the document's Vocabulary table."""
    text = path.read_text(encoding="utf-8")
    if "## 6. Vocabulary" not in text and "## Vocabulary" not in text:
        return []
    marker = "## 6. Vocabulary" if "## 6. Vocabulary" in text else "## Vocabulary"
    section = text[text.index(marker):]
    return [(m.group(1).strip(), m.group(2).strip(), m.group(3).strip())
            for m in ROW.finditer(section)]


@pytest.mark.parametrize("path", mandates(), ids=lambda p: p.name)
def test_every_recorded_mandate_declares_a_vocabulary(path: Path):
    # A mandate that introduces identifiers without declaring them cannot be checked at all, which
    # is the condition all three collisions were found in.
    assert vocabulary(path), (
        f"{path.name} has no Vocabulary section. Every recorded mandate must declare the prefixes "
        "it introduces, with a registry status, so the declaration can be verified. Three "
        "mandates in a row introduced colliding identifiers; the section is what makes the fourth "
        "catchable without a person."
    )


@pytest.mark.parametrize("path", mandates(), ids=lambda p: p.name)
def test_a_prefix_declared_NEW_is_really_unregistered(path: Path):
    for prefix, purpose, status in vocabulary(path):
        if not status.startswith("NEW"):
            continue
        assert prefix not in LADDERS and prefix not in RESERVED, (
            f"{path.name} declares {prefix!r} as NEW, but the registry has it "
            f"({LADDERS.get(prefix, {}).get('bound_to', 'reserved')!r}). Either the prefix was "
            "registered since the document was written, or the declaration is wrong."
        )


@pytest.mark.parametrize("path", mandates(), ids=lambda p: p.name)
def test_a_prefix_declared_COLLIDES_really_collides(path: Path):
    # The direction that matters most: a document must not keep asserting a collision that has been
    # resolved. When someone registers the ladder or renames the identifier, this fails and the
    # document is updated in the same change.
    for prefix, purpose, status in vocabulary(path):
        if not status.startswith("COLLIDES"):
            continue
        assert prefix in LADDERS or prefix in RESERVED, (
            f"{path.name} declares {prefix!r} as COLLIDES, but the registry no longer binds it. "
            "The collision may have been resolved; re-derive the section."
        )


@pytest.mark.parametrize("path", mandates(), ids=lambda p: p.name)
def test_a_prefix_declared_REGISTERED_is_registered(path: Path):
    for prefix, purpose, status in vocabulary(path):
        if not status.startswith("REGISTERED"):
            continue
        assert prefix in LADDERS, (
            f"{path.name} cites {prefix!r} as an existing registered prefix; the registry disagrees"
        )


@pytest.mark.parametrize("path", mandates(), ids=lambda p: p.name)
def test_every_status_uses_the_closed_vocabulary(path: Path):
    # An unconstrained status column would let a document invent a word that means nothing to this
    # test, and the row would then be silently unchecked.
    for prefix, purpose, status in vocabulary(path):
        head = status.split()[0]
        assert head in {"COLLIDES", "NEW", "REGISTERED"}, (
            f"{path.name}: {prefix!r} has status {head!r}; expected COLLIDES, NEW or REGISTERED. "
            "An unrecognised status is not checked by anything."
        )


def test_the_absorb_mandate_records_the_A5_three_way_overlap():
    # The specific finding this round produced, pinned so it cannot quietly drop out of the record.
    path = GOVERNANCE / "ABSORB_LOOP_MANDATE.md"
    flat = " ".join(path.read_text(encoding="utf-8").split())
    assert "A5" in flat and "target_autonomy: A5" in flat, (
        "the ABSORB record no longer connects its A5 checkpoint to the contested A5 in #184"
    )
    assert LADDERS["A"]["form"] == "A0-A4", (
        "the authority ladder is no longer A0-A4, so the three-way overlap must be re-derived"
    )
