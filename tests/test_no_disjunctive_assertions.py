"""No new `assert X or Y` in the test suite.

An assertion with a disjunction passes on its weakest arm BY CONSTRUCTION. That is not a judgement
call, which is what makes it a check rather than a review note.

WHAT IT COST TO LEARN. `test_deny_beats_allow_when_both_match` (SECB-WP-FWK-105) asserted

    assert "allow" in result["overridden_effects"] or result["matched_rules"] == ["POL-AUTH-002"]

and passed for the whole life of that pull request on the second arm. `overridden_effects` was
always `[]`: the facts set `issuer_independent: False`, which the allow rule requires true, so the
two rules never both matched. Exhaustive search over every boolean combination of every `when` key
showed no allow/deny overlap is reachable in the shipped bundle at all. The deny-wins precedence was
implemented, believed tested, and unexercised.

    PROPERTY_IMPLEMENTED != PROPERTY_EXERCISED

WHY MECHANICAL AND NOT A RULE. The repository already recorded this lesson in prose:

    scripts/check_shadow_merge_queue.py:75    #  ACTION_REFUSED != REFUSAL_REASON_CORRECT

and `tests/test_shadow_merge_queue.py:957` violates it — same repository, adjacent files, and the
docstring at line 1067 of the very file restates the aphorism. Prose did not prevent it.

    GUIDANCE_RECORDED != GUIDANCE_APPLIED

STRUCTURE, NOT TEXT. Matching `assert .* or ` with a regex reports SIX instances here; three are the
word "or" inside a string literal such as `"signature is absent or does not match"`. This walks the
AST and matches only `Assert` whose test is a `BoolOp(Or)`, so it counts assertions rather than
characters — the same correction the mutation probe and the identifier tokenizer both needed.

    MEASURED_BY_TEXT != MEASURED_BY_STRUCTURE

SCOPED TO tests/ DELIBERATELY. `or` in production code is ordinary control flow; `or` in an assertion
is a weakened claim. The same syntax means different things by position, and a guard that missed that
would raise false positives until someone switched it off — which would be this lesson again, one
level up.
"""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Instances present when this guard was written. Each carries a reason and a disposition, because an
# allowlist without them becomes permanent by default -- prose in a different costume.
KNOWN = {
    ("tests/test_check_work_package_ref.py", 107): (
        '"fail" in stderr.lower() already covers "FAIL"; the second arm is dead, not weak',
        "DELETE_THE_DEAD_ARM",
    ),
    ("tests/test_shadow_merge_queue.py", 476): (
        "both arms name the same fact in two spellings; weak but bounded",
        "NARROW_OR_LEAVE",
    ),
    ("tests/test_shadow_merge_queue.py", 957): (
        'MATERIAL: "REFUSED" is emitted by five scripts, so the second arm is satisfied by any '
        "refusal from any gate, including one for an unrelated reason",
        "ASSERT_THE_SPECIFIC_MESSAGE",
    ),
}


def disjunctive_assertions() -> list[tuple[str, int, str]]:
    listing = subprocess.run(
        ["git", "ls-files", "-z", "tests/"], cwd=REPO_ROOT, capture_output=True, check=True
    ).stdout.decode("utf-8", "replace")
    files = [n for n in listing.split("\0") if n.endswith(".py")]
    assert files, "git ls-files returned no test modules -- this guard would check nothing"
    found = []
    for name in files:
        source = (REPO_ROOT / name).read_text(encoding="utf-8", errors="replace")
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Assert) and isinstance(node.test, ast.BoolOp):
                if isinstance(node.test.op, ast.Or):
                    line = source.splitlines()[node.lineno - 1].strip()
                    found.append((name, node.lineno, line))
    return found


def test_no_new_disjunctive_assertion():
    new = [(n, ln, src) for n, ln, src in disjunctive_assertions() if (n, ln) not in KNOWN]
    assert not new, (
        "these assertions use `or`, which passes on the weaker arm by construction:\n"
        + "\n".join(f"  {n}:{ln}\n    {src[:100]}" for n, ln, src in new)
        + "\n\nAssert the specific fact. If two outcomes are genuinely both acceptable, name both "
        "explicitly (`value in {a, b}`) so each is a stated fact rather than one fact and a "
        "catch-all."
    )


def test_the_allowlist_has_no_stale_entries():
    """An allowlist that outlives its entries is guidance again.

    When one of the known instances is fixed, its entry must be removed in the same change. Without
    this, the list silently becomes a permanent exemption -- and a permanent exemption is exactly the
    prose-shaped prevention that failed at check_shadow_merge_queue.py:75.
    """
    present = {(n, ln) for n, ln, _ in disjunctive_assertions()}
    stale = sorted(k for k in KNOWN if k not in present)
    assert not stale, (
        f"these allowlist entries no longer correspond to a disjunctive assertion: {stale}. "
        "The instance was fixed or moved; remove the entry so the list records only live debt."
    )


def test_every_known_entry_states_a_reason_and_a_disposition():
    for key, value in KNOWN.items():
        reason, disposition = value
        assert reason and len(reason) > 20, f"{key}: reason is missing or too thin to act on"
        assert disposition.isupper() and "_" in disposition, (
            f"{key}: disposition {disposition!r} must be an explicit action token"
        )


def test_the_material_instance_is_recorded_as_material():
    # Named literally. If line 957 is fixed, test_the_allowlist_has_no_stale_entries fails first and
    # this entry is removed with it -- so this cannot outlive the defect it describes.
    reason, disposition = KNOWN[("tests/test_shadow_merge_queue.py", 957)]
    assert "MATERIAL" in reason
    assert disposition == "ASSERT_THE_SPECIFIC_MESSAGE"
