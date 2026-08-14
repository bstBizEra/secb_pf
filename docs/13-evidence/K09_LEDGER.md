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
observations n = 40        (governance verdicts on merged PR heads, as of f1b2516)
downgrades   d = UNDER_REVIEW   (2 candidates, see below)
95% upper bound on the downgrade rate = WITHHELD
```

**The bound is withheld, and that is the finding.** Every `K-09` figure this
repository has published used the **zero-numerator** Wilson form `z²/(n+z²)`, which
is only valid when `d = 0`. `d` is no longer safely assertable, so no bound is
publishable:

| if `d` = | Wilson 95% upper at n=40 | meets ≤10%? |
|---:|---:|---|
| 0 | 8.76% | **yes** |
| 1 | 12.88% | no |
| 2 | 16.50% | no |

**The target's status flips entirely on `d`.** Publishing `8.76%` — which the
recount produces the moment you assume `d = 0` — would assert the target is met
while its numerator is disputed, and by an author who is implicated in both disputed
cases. That is the most flattering error available here, so the number is withheld
rather than qualified.

`A2`'s advance conditions remain "`A1` conditions met, security review pass,
defect-escape threshold held". A sample size satisfies none of them, and neither
does an unresolved numerator.

### `d = 0` is verified, and once it was luck

Each of the five observations added at `ae89b4f` was checked rather than assumed
(`SECB-WP-FWK-054`). Four are unremarkable: #100 and #107 were `docs/`-only and
rendered `AUTO_APPROVED`; #69 and #96 touched `scripts/` and `.github/` and
rendered `CONSTITUTIONAL_REQUIRED`. A human reviewing those diffs would have
required the same authority in each.

**#81 is a near-miss and is recorded as one.** Its final verdict was
`AGENT_BALLOT_REQUIRED — 859 lines exceeds the envelope cap 600`, so it escalated
and a human merged it — no downgrade occurred. But it escalated **on the line cap,
not on the path**: `config/` was still an `auto_path` then, so the path
classification inside that verdict was `G0`, and the pull request had opened at
`AUTO_APPROVED — G0, 487/600`. A smaller work package would have auto-merged a
governance-implementation artifact. `SECB-WP-FWK-044` has since moved `config/`
out of `auto_paths` so the path classification stands on its own merits.

So `d = 0` holds — but in 1 of 34 observations it holds because an unrelated
control fired. **A confidence metric that hides its near-misses manufactures the
false confidence this ledger was opened to end.**

**The instrument is now the Wilson upper bound, not `3/n`** (`SECB-WP-FWK-040`).
For a zero numerator it has a closed form, and it is the conservative of the two:

```text
upper = z² / (n + z²)        z = 1.96,  z² = 3.8416
```

| n | `3/n` | Wilson |
|---:|---:|---:|
| 29 (today) | 10.34% | **11.70%** |
| 30 | 10.00% | 11.35% |
| 35 | 8.57% | **9.89%** |
| 60 | 5.00% | 6.02% |

The two agree at **n ≈ 13.7**, and above that `3/n` is the **optimistic** one. Every
`K-09` figure this repository has published sat above that crossover, so every one
of them understated the bound. `3/n` is retained as a reference column because the
citation chain (Hanley & Lippman-Hand, Jovanovic & Levy, Tuyl) uses it — not
because it is the number we rely on.

Reproduce:

```bash
for sha in $(gh api "repos/bstBizEra/secb_pf/pulls?state=closed&per_page=100" \
              --jq '.[] | select(.merged_at != null) | .head.sha'); do
  gh api "repos/bstBizEra/secb_pf/commits/$sha/check-runs" \
    --jq '.check_runs[].name' | grep -qi governance && echo "$sha"
done | wc -l
# 24 as of 3b61307. Then: python3 -c 'z2=1.96**2; print(z2/(24+z2))'  → 0.1380
```

## Bound as n grows

| n | Wilson upper bound | Milestone |
|---:|---:|---|
| 29 | 11.70% | the `e43fca8` row |
| 30 | 11.35% | the `A1 → A2` rung as written — **does not reach 10%** |
| 34 | 10.15% | the `ae89b4f` row |
| 40 | **8.76% *if* `d`=0** · 12.88% if `d`=1 · 16.50% if `d`=2 | today (`f1b2516`) — **bound withheld, `d` under review** |
| 35 | 9.89% | the smallest n that reaches ≤10% under Wilson — **one observation away** |
| 60 | 6.02% | — |
| 300 | 1.26% | — |

The bound is weak at this n **by the arithmetic, not by evasion.** At n=24 roughly
one decision in seven could be a downgrade and this evidence would not detect it.

**The rung and the instrument disagree.** `A1 → A2` requires *"≤10% at n=30"*, and
`30` was chosen because `3/30` is exactly 10.0%. Under Wilson, n=30 gives 11.35%;
reaching ≤10% needs

```text
n ≥ z²/0.10 − z² = 34.57  →  n ≥ 35
```

**This ledger records the disagreement and does not resolve it.** The ladder's
`advance_conditions` live in `config/delegation_envelope.json`, and moving a
promotion threshold on the authority surface is `G4` — the constitutional
authority's, not the executor's. Raising 30 to 35 is the *stricter* direction, but
"stricter" is not a licence to act; it is an argument to put in front of the
authority.

## `d` at n=40 — two candidates, both authored by the executor

Verified per-observation for the six merges added at `f1b2516` (`SECB-WP-FWK-061`).
Four are unremarkable: **#109** was `docs/`-only and rendered `AUTO_APPROVED`;
**#101** touched `ci.yml` and `scripts/` and rendered `CONSTITUTIONAL_REQUIRED`;
**#105** and **#103** touched `config/` and rendered `AGENT_BALLOT_REQUIRED`. A human
reviewing those four diffs would have required the same authority in each.

Two are not unremarkable.

### Candidate 1 — **#111, the stage-2 verdict itself**

```yaml
verdict_rendered: AUTO_APPROVED — G0, tier A1
change: docs/13-evidence/STAGE_GATE_REQUIREMENTS_READY.md — a stage-gate VERDICT
decision_class: D2 MATERIAL   (per PACKET-002)
outcome: operator merged it; the executor declined to self-merge
```

By this ledger's own definition — *"a verdict that classified a change as requiring
**less** authority than a human reviewing the same diff would have required"* — this
qualifies. A `D2 MATERIAL` stage-gate verdict was classified `G0 auto-merge`. **The
definition is about the verdict, not the outcome**, and the outcome was correct only
because the executor declined an autonomy the classifier had granted.

This is stronger than #81's near-miss. #81's *rendered* verdict escalated, on the
line cap. #111's rendered verdict was `AUTO_APPROVED` outright, and nothing
mechanical stood between it and `main`.

### Candidate 2 — **#120, the stamp and Addendum 001**

```yaml
verdict_rendered: AUTO_APPROVED — G0, tier A1
change: stamps stage 2 EFFECTIVE; records conditions C-5, C-6, C-7 for the first time
outcome: SELF-MERGED by the executor
```

Weaker than candidate 1 on one axis — it **originates** no decision, it records an
operator decision and stamps an event that had already occurred. Stronger on
another — **the executor merged it**, so no human stood in the path at all.

### Why the executor is not resolving this

`d` requires judging *what a human reviewing the same diff would have required*. For
these two cases that human is the operator, and the executor is the author of both
changes and the beneficiary of the lower answer. **An executor that grades its own
downgrades is measuring its own compliance**, which is the defect this ledger exists
to prevent, one level up.

So `d` is recorded as `UNDER_REVIEW` with the evidence attached, and the bound is
withheld until the authority rules. Three dispositions are available and all are
defensible: **both are downgrades** (`d=2`), **only #111** (`d=1`), or **neither,
because path-based `G0` on a `docs/` decision record is a classifier limitation
already documented rather than a misclassification** (`d=0`).

**Whichever way it goes, it is on the record before the number is.**

## A single downgrade invalidates the bound

The rule of three applies only to a zero numerator. The first observed downgrade
ends this series: the metric becomes an ordinary proportion with a wide interval,
and the appropriate response is to treat the classifier as unproven until the
cause is understood — not to continue the tally from `d = 1`.

> **This paragraph was written before it was needed, and it is now the operative
> rule.** It was added at `SECB-WP-FWK-035` as a hypothetical. If the authority rules
> `d ≥ 1`, the zero-numerator series ends here and the classifier is unproven until
> the cause is understood — and the cause is already named: **the classifier measures
> paths, not significance.**

## Corrections to the record

| Date | Correction |
|---|---|
| 2026-08-10 | Announcements had reported n up to 37 and a bound of 8.1%. Those values were hand-incremented on an unstated rule and **over-stated confidence.** Superseded by this ledger and by the `K-09` row |
| 2026-08-10 | The `K-09` row itself held `n=14` in one column and `n=16` in another. Corrected, and the observation unit defined for the first time |
| 2026-08-11 | **The instrument was an approximation biased in the flattering direction.** `3/n` understates the Wilson bound for every n above ≈13.7, and every published `K-09` figure sat above that crossover. Wilson is now the instrument (`SECB-WP-FWK-040`) |
| 2026-08-11 | `n` was recorded as **23** while the true count at the merge was **24**. Not a miscount: **a recount cannot count its own merge.** The figure was taken before PR #67 landed and was stale by one the moment it did. Values now carry an **as-of SHA** instead of a date |

Recorded rather than quietly replaced, because a corrected metric whose correction
is invisible teaches nobody.

## Append rule

One row per recount, never an edit of a prior row.

| Date | As of | n | d | Bound | Instrument | Recounted by | Note |
|---|---|---:|---:|---:|---|---|---|
| 2026-08-11 | `035b66d`…pre-#67 | 23 | 0 | 13.0% | `3/n` | `SECB-WP-FWK-035` | First ledger entry; supersedes all announced values |
| 2026-08-11 | `3b61307` | 24 | 0 | **13.80%** | **Wilson** | `SECB-WP-FWK-040` | Instrument corrected; `n` includes PR #67, which the prior row could not count |
| 2026-08-12 | `e43fca8` | 29 | 0 | **11.70%** | Wilson | `SECB-WP-FWK-050` | Five merges landed (#73 #71 #75 #77 #90). Counted with three retries per call — a first pass without them reported n=28 |
| 2026-08-14 | `f1b2516` | 40 | **UNDER_REVIEW** | **WITHHELD** | Wilson (zero-numerator form inapplicable while `d` is open) | `SECB-WP-FWK-061` | Six merges landed (#109 #111 #101 #105 #103 #120); 48 merged PRs, 0 heads unresolved after 3 retries. **The recount found n=40 and, verifying `d` per-observation, found two downgrade candidates — both authored by the executor.** Bound withheld because the zero-numerator Wilson form requires `d = 0`. `d` is the authority's call, not the executor's |
| 2026-08-12 | `ae89b4f` | 34 | 0 | **10.15%** | Wilson | `SECB-WP-FWK-054` | Five merges landed (#100 #69 #81 #96 #107); 42 merged PRs, 0 heads unresolved after 3 retries. `d=0` verified per-observation, not carried: #81 escalated on the **line cap** while its path classification was still `G0`, so it is recorded above as a near-miss rather than counted as a downgrade. One observation short of the ≤10% target |

## Remaining follow-up

The recount is a shell loop run by hand. A script would make it a gate rather than
a habit, and `scripts/` is `G4` — so it is a separate work package and the
operator's decision, not something to slip in here.
