"""CI checks are identified by function, not by number — `SECB-WP-FWK-068` (D1).

Two different steps were both named `"Gate 6"`, and Gates 2, 3 and 4 appeared nowhere.
The CI numbering was also a *second, unregistered* use of gate numbering: the registered
`GATE` ladder is `GATE-001..GATE-010`, bound to two-plane verdict rules. A duplicate
number is the same defect as the duplicate `SECB-WP-FWK-062` work-package ID — the label
stops identifying one thing, and a gate that cannot be named cannot be audited.

    Functional check name  ≠  gate-number ladder
    Missing number         ≠  missing implemented control
    Renaming a check       ≠  implementing a new gate
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"

REQUIRED_TRIGGER_TYPES = {"opened", "reopened", "synchronize", "edited", "ready_for_review"}


def workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def check_names() -> list[str]:
    names = re.findall(r'name: "([^"]+)"', workflow_text())
    assert names, "no quoted check names parsed — the workflow's shape changed"
    return names


def test_no_two_checks_share_a_name():
    names = check_names()
    duplicates = {n for n in names if names.count(n) > 1}
    assert not duplicates, (
        f"{duplicates} name more than one check. Two steps were both 'Gate 6'; a reader "
        "of a red run could not tell which control failed"
    )


def test_no_check_is_identified_by_a_bare_gate_number():
    offenders = [n for n in check_names() if re.search(r"\bGate\s*\d", n)]
    assert not offenders, (
        f"{offenders} identify a check by number. Numbering here collides with the "
        "registered GATE-001..GATE-010 ladder, which is bound to two-plane verdict "
        "rules, not to CI jobs"
    )


def test_historical_names_are_retained_as_aliases_for_readback():
    """Renaming without an alias table breaks every query that joins on name.

    Historical check-runs keep the names they were created with. A reader counting
    across time needs both, so the mapping is recorded in the workflow header.
    """
    text = workflow_text()
    for alias in (
        "Gate 5 — Test",
        "Gate 6 - prohibited-call scan",
        "Gate 6 - committed-secret scan",
        "Gate 1 — Authority (No Ticket, No Work)",
        "Budget circuit breaker",
        "Governance verdict (advisory)",
    ):
        assert alias in text, f"the historical alias {alias!r} is not recorded for readback"


def test_the_governance_check_still_matches_the_k09_counting_pattern():
    """`K-09`'s denominator depends on this name, and would fail silently.

    `docs/13-evidence/K09_LEDGER.md` counts observations with
    `check_runs[].name | grep -qi governance`. A rename dropping that token would count
    zero observations on every future merge while the ledger kept appending rows — the
    series would not break, it would quietly stop measuring.
    """
    matching = [n for n in check_names() if re.search(r"governance", n, re.I)]
    assert matching, (
        "no check name contains 'governance'. The K-09 ledger's recount would return 0 "
        "for every future merge, and nothing would report an error"
    )


def test_a_metadata_edit_can_trigger_re_evaluation():
    """Without `edited`, a title change fires nothing and the stale check stays green."""
    text = workflow_text()
    match = re.search(r"pull_request:\s*\n\s*types:\s*\[([^\]]+)\]", text)
    assert match, (
        "pull_request declares no explicit types. The default is "
        "[opened, synchronize, reopened], under which a metadata edit is invisible"
    )
    declared = {t.strip() for t in match.group(1).split(",")}
    missing = REQUIRED_TRIGGER_TYPES - declared
    assert not missing, f"trigger types missing: {sorted(missing)}"


def test_both_metadata_dependent_gates_record_what_they_evaluated():
    """Gate 1 and the budget gate read PR metadata, so both must bind it.

    Emission is what makes the staleness provable at all — the #122 defect was only
    detectable because Gate 1 happened to print `WP_TEXT`. Incidental readback is now
    deliberate.
    """
    text = workflow_text()
    assert text.count("scripts/emit_pr_input_binding.py") >= 2, (
        "the authority and budget gates must each emit their input binding; only "
        f"{text.count('scripts/emit_pr_input_binding.py')} emission step(s) found"
    )
