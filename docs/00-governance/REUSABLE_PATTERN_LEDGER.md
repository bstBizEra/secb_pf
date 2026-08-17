# Reusable Pattern Ledger

**SECB-WP-FWK-090.** The durable home for the reusable patterns this framework has established.

This document is a **pointer, not a copy.** The patterns live in
[`config/reusable_patterns.json`](../../config/reusable_patterns.json), which is the single
source, and [`scripts/check_pattern_ledger.py`](../../scripts/check_pattern_ledger.py) validates
it. A second prose copy of thirty entries would drift from the first, and then two documents
would disagree about what the framework has learned.

## Why it exists

Roughly thirty patterns were established across FWK-079…089 — claim/mechanism ordering, the
shadow-queue prefix distinctions, compare-and-swap execution, reason integrity, dual-subject
binding, typed multi-path readback, cryptographic coverage closure. Every one of them lived
**only in a pull-request comment.**

That has three failure modes, and the third is the dangerous one:

```text
not greppable      the next agent cannot find what the last one learned
not auditable      a pattern with no cited origin is folklore
not verifiable     a comment can claim a guard that does not exist
```

The third is not hypothetical. A governing document in a sibling repository named a required
test that had never been written, and every agent that read the document concluded the
repository had a safety net it did not have. The ledger exists so that

```text
DOCUMENTED != ENFORCED
CITED != PRESENT
```

are enforced rather than merely observed.

## The contract

Every entry declares `id`, `name`, `rule`, `origin` and `guard`. Three things are refused:

| Refusal | Why |
| --- | --- |
| A `rule` with no distinction, implication, conjunction or ordering | A pattern with no stated relation is a slogan, and a slogan cannot be applied to a new case by anyone who was not in the conversation that produced it |
| An `origin` naming neither a PR nor an issue | Provenance is what makes a pattern falsifiable later |
| A `guard` that disagrees with this tree | See below — checked in **both** directions |

### Guard classes, checked against the tree

```text
MECHANICAL      every cited test must EXIST in this tree, by file AND by test name.
                A phantom citation is refused: it is worse than no citation, because
                every reader concludes the guard is in force.

PENDING_MERGE   at least one cited test must be ABSENT here, and an open PR must be
                named. If all of them have landed, the classification is stale and is
                ALSO refused -- under-claiming decays the ledger as surely as
                over-claiming, by training readers to ignore the field.

PROSE_ONLY      no test may be cited. An entry that cites a guard while calling itself
                prose understates its own enforcement, which is drift in the direction
                nobody audits.
```

The validator reports `mechanically_guarded / patterns` and **never rounds it up.** Honest prose
stays visibly prose. A ledger where every entry claimed enforcement would be this framework's
own `CLAIM_STRENGTH ≤ MECHANISM_STRENGTH` violation at the documentation layer.

## What it does not do

- It does **not** judge whether a cited test actually exercises the pattern it claims to guard.
  Only a human reviewer can say that. The tool proves the guard exists, not that it is apt.
- It does **not** treat absence of an entry as absence of a pattern. The ledger is extended as
  patterns are promoted; it is not a closed world.
- It confers **no authority**. `confers_merge_authority: false`, like every other observation in
  this framework.

## Adding an entry

Add it to `config/reusable_patterns.json` and run:

```bash
LEDGER=config/reusable_patterns.json python3 scripts/check_pattern_ledger.py
```

If the pattern has no mechanical guard yet, say so — `PROSE_ONLY` is a legitimate and honest
state. **Do not cite a test you have not written**; the validator will refuse it, which is the
point, and `RP-025` (counterexample-first verification) is the pattern that says why: a guard
whose removal breaks no test is a claim about the code rather than a property of it.

Two entries — `RP-025` and `RP-026` — are guarded by
[`tests/test_pattern_ledger.py`](../../tests/test_pattern_ledger.py), the suite for this very
tool. While those tests did not exist, the validator refused the ledger that named them. The
tool enforced counterexample-first order on its own author, which is the smallest possible
demonstration that the rule is load-bearing.
