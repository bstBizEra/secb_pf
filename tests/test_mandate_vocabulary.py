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


# The status must be structurally parseable, not merely start with the keyword. Checking only that
# the registered form text APPEARS anywhere in the status let a row name one base while deriving
# another: `EXTENDS \`A\` beyond registered form \`KN-001..KN-005\`` on prefix `KN-CAND` derived KN,
# found KN registered, found the KN form present -- and never rejected the false base `A`.
#
#     SUBSTRING_PRESENT != FIELD_BOUND
EXTENDS_STATUS = re.compile(
    r"EXTENDS\s+`([^`]+)`\s+beyond its registered form\s+`([^`]+)`\s*"
)


def base_prefix(prefix: str) -> str:
    """The longest REGISTERED prefix that `prefix` extends.

    Splitting on the first hyphen was wrong: `SECB-WP` is itself a registered prefix, so
    `SECB-WP-FWK` derived `SECB`, which is not registered -- refusing a legitimate row with a
    message blaming the wrong thing. Longest-match resolves against the registry rather than
    against punctuation.

    Falls back to the first-hyphen split when nothing matches, so the caller's assertion still
    reports a sensible base in its failure message.
    """
    candidates = [p for p in LADDERS
                  if prefix == p or prefix.startswith(p + "-")]
    if candidates:
        return max(candidates, key=len)
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
def test_an_EXTENDS_row_binds_the_base_and_form_it_declares(path: Path):
    """The declared base must BE the derived base, and the declared form the registered one.

    Substring presence is not binding. A row may name any base and any form and still contain the
    right characters somewhere; the fields have to be parsed and compared.
    """
    for prefix, purpose, status in vocabulary(path):
        if not status.startswith("EXTENDS"):
            continue
        parsed = EXTENDS_STATUS.fullmatch(status)
        assert parsed, (
            f"{path.name}: {prefix!r} has status {status!r}. An EXTENDS row must read exactly "
            "``EXTENDS `<base>` beyond its registered form `<form>` `` so both fields can be "
            "compared rather than searched for."
        )
        declared_base, declared_form = parsed.groups()
        derived = base_prefix(prefix)
        assert declared_base == derived, (
            f"{path.name}: {prefix!r} declares it extends {declared_base!r}, but the prefix "
            f"resolves to {derived!r}. A row that names one base while extending another is worse "
            "than an undeclared extension: it reads as verified."
        )
        assert declared_base in LADDERS, (
            f"{path.name}: declared base {declared_base!r} is not registered"
        )
        assert declared_form == LADDERS[declared_base]["form"], (
            f"{path.name}: {prefix!r} declares form {declared_form!r}; the registry records "
            f"{LADDERS[declared_base]['form']!r} for {declared_base!r}."
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


def _one_row_doc(tmp_path, prefix: str, status: str) -> Path:
    doc = tmp_path / "Z_MANDATE.md"
    doc.write_text(
        "# Z\n\n## Vocabulary\n\n| Prefix | Used for | Registry status |\n| :--- | :--- | :--- |\n"
        f"| `{prefix}` | x | {status} |\n",
        encoding="utf-8",
    )
    return doc


def test_an_extends_row_naming_a_false_base_is_refused(tmp_path):
    # The exact malformed row the operator's verdict produced. It derives KN, finds KN registered,
    # and contains the KN form -- and must still be refused for declaring base `A`.
    doc = _one_row_doc(tmp_path, "KN-CAND",
                       "EXTENDS `A` beyond its registered form `KN-001..KN-005`")
    prefix, _, status = vocabulary(doc)[0]
    parsed = EXTENDS_STATUS.fullmatch(status)
    assert parsed
    assert parsed.group(1) != base_prefix(prefix), "the probe is not exercising the false base"


def test_an_extends_row_naming_a_wrong_form_is_refused(tmp_path):
    doc = _one_row_doc(tmp_path, "KN-EP",
                       "EXTENDS `KN` beyond its registered form `KN-999..KN-000`")
    prefix, _, status = vocabulary(doc)[0]
    parsed = EXTENDS_STATUS.fullmatch(status)
    assert parsed and parsed.group(2) != LADDERS["KN"]["form"]


def test_an_unstructured_extends_status_is_refused(tmp_path):
    doc = _one_row_doc(tmp_path, "KN-EP", "EXTENDS KN a bit")
    _, _, status = vocabulary(doc)[0]
    assert EXTENDS_STATUS.fullmatch(status) is None


def test_the_base_of_a_hyphenated_registered_prefix_resolves_by_longest_match():
    # SECB-WP is registered and contains a hyphen. First-hyphen splitting derived "SECB", which is
    # not registered, so a legitimate SECB-WP extension was refused with the wrong reason.
    assert "SECB-WP" in LADDERS
    assert base_prefix("SECB-WP-FWK") == "SECB-WP"
    assert base_prefix("KN-CAND") == "KN"
    assert base_prefix("KL") == "KL"  # unregistered: falls back, still reports something usable
