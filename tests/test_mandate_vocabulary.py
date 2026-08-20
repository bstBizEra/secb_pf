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


HEADING = re.compile(r"^##+\s*(?:[\d.]+\s*)?Vocabulary\s*$", re.MULTILINE)


def vocabulary(path: Path) -> list[tuple[str, str, str]]:
    """Return (prefix, purpose, status) rows from the document's Vocabulary table.

    The heading is matched by its TEXT, at any depth and with any section number. The first
    version of this function hard-coded "## 6. Vocabulary", and the very next mandate recorded
    numbered its section "## 4" -- so the parser extracted zero rows and every row-iterating test
    below passed while checking nothing.

        PARSER_FOUND_NOTHING != DOCUMENT_DECLARES_NOTHING

    Only test_every_recorded_mandate_declares_a_vocabulary caught it, because it is the one
    assertion that fails on an empty result rather than iterating over it. That is why it exists,
    and why the row count is asserted separately below.
    """
    text = path.read_text(encoding="utf-8")
    found = HEADING.search(text)
    if not found:
        return []
    # The status is returned WHOLE, not just its leading keyword. The first version returned only
    # group 3 (`[A-Z][A-Z -]*[A-Z]`), so "EXTENDS `KN` beyond its registered form `KN-001..KN-005`"
    # arrived as bare "EXTENDS" -- and the assertion that an EXTENDS row must name the form it
    # departs from could never pass. It passed anyway, because no document had an EXTENDS row yet.
    #
    #     ASSERTION_NEVER_EXERCISED != ASSERTION_SATISFIED
    return [(m.group(1).strip(), m.group(2).strip(),
             (m.group(3) + m.group(4)).strip())
            for m in ROW.finditer(text[found.start():])]


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
        assert head in {"COLLIDES", "NEW", "REGISTERED", "EXTENDS"}, (
            f"{path.name}: {prefix!r} has status {head!r}; expected COLLIDES, NEW, REGISTERED or "
            "EXTENDS. An unrecognised status is not checked by anything."
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


def test_a_differently_numbered_vocabulary_heading_is_still_found(tmp_path):
    # The regression that produced the heading fix. A mandate numbering its section "## 4" must not
    # silently extract zero rows.
    doc = tmp_path / "X_MANDATE.md"
    doc.write_text(
        "# X\n\n## 4. Vocabulary\n\n"
        "| Prefix | Used for | Registry status |\n| :--- | :--- | :--- |\n"
        "| `R` | risk tiers | REGISTERED `R0-R4` |\n",
        encoding="utf-8",
    )
    rows = vocabulary(doc)
    assert rows == [("R", "risk tiers", "REGISTERED `R0-R4`")], rows


@pytest.mark.parametrize("path", mandates(), ids=lambda p: p.name)
def test_the_parser_extracted_rows_from_every_mandate(path: Path):
    # Asserted separately from the declaration test so a parser that stops matching is
    # distinguishable from a document that stopped declaring. Both are failures; they need
    # different fixes.
    assert len(vocabulary(path)) >= 1, (
        f"the parser found no vocabulary rows in {path.name}. Either the document dropped its "
        "table, or the heading/table shape drifted out of what HEADING and ROW match -- and the "
        "row-iterating tests above would then pass while checking nothing."
    )


# --- EXTENDS: a new FORM under an already-registered prefix ------------------
#
# The check above validates prefix STRINGS. It does not read the registered FORM, and the registry
# records one: `KN` is `KN-001..KN-005`. So a row declaring `KN` REGISTERED silently covers
# `KN-CAND-001` and `KN-EP-001`, which are outside that form.
#
#     PREFIX_REGISTERED != IDENTIFIER_FORM_REGISTERED
#
# Declaring such a form NEW is also wrong: it is not a new prefix, it is an extension of one, and
# calling it NEW hides that the base already has an owner and a shape. EXTENDS names it exactly.


def base_prefix(prefix: str) -> str:
    return prefix.split("-", 1)[0]


@pytest.mark.parametrize("path", mandates(), ids=lambda p: p.name)
def test_an_EXTENDS_row_names_a_registered_base(path: Path):
    for prefix, purpose, status in vocabulary(path):
        if not status.startswith("EXTENDS"):
            continue
        base = base_prefix(prefix)
        assert base in LADDERS, (
            f"{path.name}: {prefix!r} is declared EXTENDS, but its base {base!r} is not registered. "
            "An extension of nothing is a new prefix; declare it NEW."
        )
        assert prefix != base, (
            f"{path.name}: {prefix!r} declares EXTENDS but is the bare registered prefix. Use "
            "REGISTERED for the prefix itself and EXTENDS only for a new form under it."
        )


@pytest.mark.parametrize("path", mandates(), ids=lambda p: p.name)
def test_an_EXTENDS_row_states_the_form_it_departs_from(path: Path):
    # The reader has to be able to see WHAT is being extended without opening the registry. Without
    # the registered form in the row, EXTENDS is just a nicer-looking NEW.
    for prefix, purpose, status in vocabulary(path):
        if not status.startswith("EXTENDS"):
            continue
        registered_form = LADDERS[base_prefix(prefix)]["form"]
        assert registered_form in status, (
            f"{path.name}: {prefix!r} is declared EXTENDS but the row does not name the registered "
            f"form it departs from ({registered_form!r}). Include it so the extension is legible."
        )


def test_the_form_gap_is_recorded_rather_than_implied():
    # This suite validates prefixes. It cannot validate that a document's identifiers MATCH the
    # registered form, because it never sees the identifiers -- only the declaration. Stated here
    # so the limit is part of the control rather than folklore.
    assert "PREFIX_REGISTERED != IDENTIFIER_FORM_REGISTERED" in Path(__file__).read_text(
        encoding="utf-8"
    )


def test_an_extends_row_round_trips_its_full_status(tmp_path):
    # The regression: the status must arrive whole, or the form assertion above is unfalsifiable.
    doc = tmp_path / "Y_MANDATE.md"
    doc.write_text(
        "# Y\n\n## Vocabulary\n\n| Prefix | Used for | Registry status |\n| :--- | :--- | :--- |\n"
        "| `KN-EP` | episodes | EXTENDS `KN` beyond its registered form `KN-001..KN-005` |\n",
        encoding="utf-8",
    )
    rows = vocabulary(doc)
    assert len(rows) == 1
    prefix, _, status = rows[0]
    assert prefix == "KN-EP"
    assert status.startswith("EXTENDS")
    assert LADDERS["KN"]["form"] in status, status
