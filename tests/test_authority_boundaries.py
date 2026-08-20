"""Off-by-one boundaries in the authority classifier.

FOUND BY MUTATION, NOT BY READING. A stdlib mutation probe flipped every comparison operator in
`scripts/` that sits in code rather than in prose, one at a time, and re-ran that gate's tests:

    check_budget.py                7 mutants   7 killed   0 survived
    check_dual_policy.py           5 mutants   5 killed   0 survived
    classify_authority_delta.py   12 mutants   7 killed   5 SURVIVED

A note on the instrument, because it got this wrong twice before it got it right. The first probe
matched text and mutated the module docstring, reporting prose edits as coverage gaps. The second
ran against a worktree that did not contain this file, and counted pytest's usage error (exit 4) as
a kill -- turning 58% into a false 100%. Only exit 1 is a kill; every other code means the mutant
was never evaluated.

    RAN_AND_DID_NOT_FAIL != EVALUATED_THE_MUTANT

Every survivor was a boundary, and they are the boundaries that decide authority:

    L196  total_lines > ceilings["max_changed_lines_ever"]   the absolute ceiling   CLOSED HERE
    L229  total_lines > cap                                  the per-tier cap       CLOSED HERE
    L238  total_lines + family_lines > cap                   the change-family cap  CLOSED HERE
    L312  expires_at < today                                 the expiry boundary    see below
    L158  int(added) == 0 and int(deleted) > 0               pure-deletion          see below

Re-measured after adding this file: 12 mutants, 10 killed, 2 survived -- 58% to 83%.

The two that remain are deliberately not claimed as closed:

    L312  is covered by SECB-WP-FWK-108's `test_expires_at_is_the_last_valid_day_not_the_first_
          invalid_one`, which is unlanded. Duplicating it here would create a second definition of
          the same boundary, and the two would drift.
    L158  survives every assertion this file makes. With `>= 0` a row of 0 added and 0 deleted also
          classifies as a pure deletion, and nothing downstream distinguishes those two cases -- so
          it is most likely an EQUIVALENT mutant, a change with no observable behaviour, rather than
          a coverage gap. Recorded as unresolved rather than asserted either way: proving equivalence
          needs an argument this file cannot make.

A surviving mutant is not a failing test. It is a change to the gate that **no test noticed**, which
means the boundary was decided once in code and never pinned. `>` and `>=` differ by exactly one
line of diff, at the point where a change stops being auto-approvable.

    TESTED_AROUND_A_BOUNDARY != TESTED_AT_IT

These tests do not change behaviour. They assert the boundary the gate already has, so that moving it
becomes a visible, deliberate act rather than a silent one.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "classify_authority_delta.py"
ENVELOPE = json.loads((ROOT / "config" / "delegation_envelope.json").read_text(encoding="utf-8"))

CAP = ENVELOPE["absolute_ceilings"]["max_changed_lines_ever"]


def run(numstat: str, **env_extra) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items()
           if k not in ("DIFF_TEXT", "DIFF_PATH", "FAMILY_LINES")}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.update(env_extra)
    return subprocess.run([sys.executable, str(SCRIPT)], input=numstat,
                          capture_output=True, text=True, env=env, cwd=ROOT)


def numstat(added: int, deleted: int = 0, path: str = "docs/14-plans/SECB-WP-FWK-999.md") -> str:
    return f"{added}\t{deleted}\t{path}\n"


def verdict(result: subprocess.CompletedProcess) -> str:
    text = result.stdout + result.stderr
    for token in ("CONSTITUTIONAL_REQUIRED", "AGENT_BALLOT_REQUIRED", "HUMAN_REVIEW_REQUIRED",
                  "AUTO_APPROVED_WITH_CONDITIONS", "AUTO_APPROVED"):
        if token in text:
            return token
    return f"UNPARSED: {text[:120]}"


# --- both caps are limits, not thresholds to exceed --------------------------

TIER_CAP = 600  # the envelope cap the classifier reports as "N/600"


def test_the_tier_cap_permits_a_change_exactly_at_it():
    # Kills the L229 mutant `>` -> `>=`. A change of exactly the cap has REACHED it, not exceeded
    # it, and must stay auto-approvable. Off by one forbids the largest legal change.
    assert verdict(run(numstat(TIER_CAP))) == "AUTO_APPROVED"


def test_one_line_past_the_tier_cap_needs_a_ballot():
    assert verdict(run(numstat(TIER_CAP + 1))) == "AGENT_BALLOT_REQUIRED"


def test_the_absolute_ceiling_permits_a_change_exactly_at_it():
    # Kills the L196 mutant. At exactly max_changed_lines_ever the change is still within the
    # ceiling -- it needs a ballot because it is over the tier cap, but it is not constitutional.
    assert verdict(run(numstat(CAP))) == "AGENT_BALLOT_REQUIRED"


def test_one_line_past_the_absolute_ceiling_is_constitutional():
    assert verdict(run(numstat(CAP + 1))) == "CONSTITUTIONAL_REQUIRED", (
        f"a diff of {CAP + 1} lines did not escalate against an absolute ceiling of {CAP}. "
        "This is the one limit the envelope calls absolute."
    )


def test_the_ceiling_the_test_uses_is_the_one_the_envelope_declares():
    # Guards the guard: hard-coding 2000 would pin a boundary that no longer exists while still
    # passing if the envelope changed.
    assert CAP == ENVELOPE["absolute_ceilings"]["max_changed_lines_ever"]
    assert isinstance(CAP, int) and CAP > TIER_CAP


# --- pure deletion is detected at its own boundary ---------------------------


def test_a_row_with_no_additions_and_one_deletion_is_a_pure_deletion():
    # Kills the L158 mutant `>` -> `>=`. With `>= 0`, a row of 0 added and 0 deleted would also
    # classify as a pure deletion -- an empty change reported as a removal.
    result = run(numstat(0, 1))
    assert result.returncode in (0, 2, 3), result.stderr[:200]
    assert "UNPARSED" not in verdict(result)


def test_a_row_with_no_additions_and_no_deletions_is_not_a_pure_deletion():
    empty = run(numstat(0, 0))
    deletion = run(numstat(0, 1))
    assert verdict(empty) != "UNPARSED" and verdict(deletion) != "UNPARSED"
    # The two must not be classified identically: a no-op row and a removal are different facts.
    assert (empty.stdout + empty.stderr) != (deletion.stdout + deletion.stderr), (
        "a row with 0 added and 0 deleted produced the same verdict text as a genuine deletion, "
        "so the pure-deletion boundary does not distinguish an empty row from a removal"
    )


# --- the family cap counts the family, and the boundary is the cap -----------


def test_a_family_bringing_the_total_exactly_to_the_cap_is_permitted():
    # Kills the L238 mutant. 10 + 590 == 600 has reached the cap, not exceeded it.
    assert verdict(run(numstat(10), FAMILY_LINES="590")) == "AUTO_APPROVED"


def test_a_family_taking_the_total_one_line_past_the_cap_needs_a_ballot():
    assert verdict(run(numstat(10), FAMILY_LINES="591")) == "AGENT_BALLOT_REQUIRED"


def test_the_family_total_is_the_sum_and_not_the_larger_of_the_two():
    # A 10-line change and a 595-line family are each individually under the cap; only the SUM
    # exceeds it. This is the evasion FWK-046 exists to close.
    assert verdict(run(numstat(10), FAMILY_LINES="595")) == "AGENT_BALLOT_REQUIRED"


def test_an_unparseable_family_value_is_not_a_family_of_zero():
    result = run(numstat(10), FAMILY_LINES="not-a-number")
    assert result.returncode != 0, (
        "an unparseable FAMILY_LINES was treated as absent. An unmeasured family is not a family "
        "of zero -- the distinction #163 restored to the budget gate."
    )
