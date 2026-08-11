# `K-09` Ledger — constitutional-class recall

Status: Open, append-only · Opened by `SECB-WP-FWK-035` (issue #66)
Metric: `KPI_BASELINE.md` `K-09` · Method: statistical rule of three (`3/n`)

## Why this exists in the repository

The series lived only in GitHub issue comments. Seventeen autonomous-merge
announcements each carried a tally, so `C-3`'s predicate (b) looked satisfied —
but the values were hand-incremented on an unstated rule, they disagreed with the
KPI row, and none of it was reachable from the repository. A confidence metric
that cannot be recomputed is worse than an absent one, because it looks rigorous.

`NFR-10` requires every material claim to cite an artifact a third party can open.
This is that artifact.

## Definition of an observation

> **One observation = one governance verdict rendered on the head SHA of a merged
> pull request.**

Chosen because it is the only denominator that is (a) countable from an API
without judgement, (b) one-per-decision rather than one-per-invocation — the
classifier runs four times per PR: local self-check, CI, and both sides of the
dual-policy comparison — and (c) restricted to merged PRs, so abandoned branches
do not inflate the count.

**A downgrade** is a verdict that classified a change as requiring *less*
authority than a human reviewing the same diff would have required. Upgrades are
not downgrades: escalating something that need not have escalated costs a merge,
not a control.

## Count

```text
observations n = 23        (governance verdicts on merged PR heads, 2026-08-11)
downgrades   d = 0
95% upper bound on the downgrade rate = 3/n = 13.0%
```

Reproduce:

```bash
for sha in $(gh api "repos/bstBizEra/secb_pf/pulls?state=closed&per_page=100" \
              --jq '.[] | select(.merged_at != null) | .head.sha'); do
  gh api "repos/bstBizEra/secb_pf/commits/$sha/check-runs" \
    --jq '.check_runs[].name' | grep -q Governance && echo "$sha"
done | wc -l
```

## Bound as n grows

| n | 95% upper bound | Milestone |
|---:|---:|---|
| 23 | **13.0%** | today |
| 30 | 10.0% | the `A1 → A2` ladder threshold |
| 60 | 5.0% | — |
| 300 | 1.0% | — |

The bound is weak at this n **by the arithmetic, not by evasion.** At n=23 roughly
one decision in eight could be a downgrade and this evidence would not detect it.
That is the honest reading, and it is the reason the ladder's `A1 → A2` step sits
at thirty rather than at a feeling of readiness.

## A single downgrade invalidates the bound

The rule of three applies only to a zero numerator. The first observed downgrade
ends this series: the metric becomes an ordinary proportion with a wide interval,
and the appropriate response is to treat the classifier as unproven until the
cause is understood — not to continue the tally from `d = 1`.

## Corrections to the record

| Date | Correction |
|---|---|
| 2026-08-10 | Announcements had reported n up to 37 and a bound of 8.1%. Those values were hand-incremented on an unstated rule and **over-stated confidence.** Superseded by this ledger and by the `K-09` row |
| 2026-08-10 | The `K-09` row itself held `n=14` in one column and `n=16` in another. Corrected, and the observation unit defined for the first time |

Recorded rather than quietly replaced, because a corrected metric whose correction
is invisible teaches nobody.

## Append rule

One row per recount, never an edit of a prior row.

| Date | n | d | Bound | Recounted by | Note |
|---|---:|---:|---:|---|---|
| 2026-08-11 | 23 | 0 | 13.0% | `SECB-WP-FWK-035` | First ledger entry; supersedes all announced values |

## Remaining follow-up

The recount is a shell loop run by hand. A script would make it a gate rather than
a habit, and `scripts/` is `G4` — so it is a separate work package and the
operator's decision, not something to slip in here.
