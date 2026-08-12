# KPI Baseline — SecB Engineer Loop

Status: Baselined — stage 1 passed 2026-08-10 (`PRD_BASELINED`, `APPROVED_WITH_CONDITIONS`)
Stage: 1, PRD Review and Baseline
Source metrics: `PRD-ENGINEER-LOOP.md` §11 · Measurement rules:
`PERFORMANCE_INDICATORS.md`

`PERFORMANCE_INDICATORS.md` requires every KPI to have an **owner, formula,
source, cadence, target and guardrail**. Stage 1 requires success KPIs to be
*measurable*. The table below states, per metric, whether that standard is met
— because a KPI that cannot be computed is a slogan, and stage 14 will be
asked to measure it.

| # | KPI | Formula | Source | Cadence | Baseline | Target | Guardrail | Owner | Ready? |
|--:|---|---|---|---|---|---|---|---|---|
| K-01a | **Required-gate pass rate** | `merged_prs_all_required_checks_success / merged_prs` | GitHub check-runs API | Per merge | **37/37 (100%)** — recounted as of `e43fca8`; 37 merged PRs, all 37 carrying check runs, none with a non-`success` conclusion. **Counted with three retries per call** — the first pass reported 36 because a transient API timeout silently dropped a row | 100% | Never met by relaxing a gate. **Green is not the same as effective** — see `K-05b` | Operator | **Yes** |
| K-01b | **Advisory-job health** | `advisory_job_success / merged_prs` | Same | Per merge | **37/37** as of `e43fca8` — the governance-verdict job exits 0 by design, so this row measures that the job *ran*, never that a verdict was favourable | 100% | A row that cannot fail is a liveness check, not a gate. Recorded as such so it is never cited as assurance | Operator | **Yes** |
| K-02 | Unauthorized-action rate | count of merges without a passing Authority gate | Check-runs API + issue records | Per merge | **0** — every merged PR carrying an Authority check passed it | 0 | Any occurrence is an incident, not a metric movement | Operator | **Yes** |
| K-03 | Evidence completeness — **overall** | WPs whose gate results are recorded on the ticket / WPs merged | Issue comments | Per WP | **33/37 = 89.2%** as of `e43fca8`. The five merges of 2026-08-12 each carry an announcement with verdict, gates and SHA, which is what this row counts | 100% | Presence is not sufficiency; a comment must cite run IDs | Operator | **Yes** |
| K-03a | Evidence completeness — **autonomous class** | Same, restricted to autonomously merged WPs | Issue comments | Per WP | **33/33 = 100%** as of `e43fca8` | 100% | — | Operator | **Yes** |
| K-03b | Evidence completeness — **escalated class** | Same, restricted to escalated, operator-merged WPs | Issue comments | Per WP | **0/4 = 0%** — #28, #36, #48, #58 | 100% | **The overall figure hides this row.** Proposed promotion gate: `K-03b < 100%` blocks any autonomy advance. Recorded as *proposed* — a promotion gate lives on the authority surface and is the operator's to install | Operator | **Yes** |
| K-04 | First-pass budget compliance | WPs needing no budget amendment / WPs merged | Issue comments | Per WP | **34/37 = 91.9%** as of `e43fca8` — still 3 amendments: FWK-007, FWK-013, FWK-022; none of the five merged on 2026-08-12 needed one. **The unmerged queue holds four more amendments** (`BR-FWK-041-001/002`, `BR-FWK-044-001`, `BR-FWK-046-001`, `BR-FWK-047-001`, `BR-FWK-048-001/002`), one of which was a misdeclaration rather than discovered work — this row will fall when they land, and that is correct | ≥90% | Not met by inflating declared budgets | Executor | **Yes** |
| K-05a | **Enforcement coverage** | mechanically fail-able gates / 10 | `ci.yml` versus `CONTROL_GATES.md` | Per change to CI | **4/10 = 40%** as of `e43fca8` — Authority, Test, Budget, and **Gate 7 (Evidence)** via `SECB-WP-FWK-045`, which recomputes the five sealed digests and fails on any mismatch. Gate 6's two scans (`NFR-17`, `NFR-18`) are in `#96`/`#98` and **not on `main`**, so they are not counted: counting a control that is not in force is the defect this row exists to avoid. The governance-verdict job remains uncounted — it exits 0 by design | 10/10 | Counting a job that cannot fail would inflate this row | Operator | **Yes** |
| K-05b | **Negative-test pass rate** | enforcing gates proven to fail on a real PR / enforcing gates | Recorded failing run IDs | Per gate change | **4/4 = 100%** as of `e43fca8` — Gate 7's guard was demonstrated failing on a mutated copy before it was trusted | 100% | `KN-001`: a gate counts only once **observed** failing. `K-05a` says how many controls can block; this row says whether they do | Operator | **Yes** |
| K-06 | Loop lead time, ticket to merge | `merged_at − issue.created_at`, median | GitHub timestamps | Per WP | **n=23 · median 12.1 min · p90 1,142.5 min · max 1,240.6 min** as of `e43fca8` — **TARGET BREACHED on both figures.** See the note below | p50 ≤ 10 min · p90 ≤ 30 min | Speed must never be met by skipping evidence; the max is a human-decision wait, not slow execution | Operator | **COMPUTED** (`SECB-WP-FWK-028`) |
| K-07a | Autonomous merges under the envelope | count | Merge log + the mandatory announcements | Per merge | **23** as of `e43fca8` — 18 prior plus the five announced merges of 2026-08-12 (`#73` `#71` `#75` `#77` `#90`) | Ladder `A1 → A2` needs 30 — **7 to go** | One rollback resets the count | Operator | **Yes** |
| K-07b | Production rollbacks among them | count | Merge log | Per merge | **0** | 0 | **Zero is ambiguous:** it means either that nothing needed rolling back, or that rollback has never been exercised. This row alone cannot distinguish them — `K-07c` is what separates the two | Operator | **Yes** |
| K-07c | **Rollback drill pass rate** | successful drills / scheduled drills | Drill records | Per drill | **0/0 — undefined.** No drill has ever been scheduled or run | ≥3 successful drills before any autonomy advance | An untested rollback is a plan, not a capability. Recorded as `undefined` rather than as `100%`, which is what dividing zero by zero would flatter it into | Operator | **NO — instrument defined, never exercised** |
| K-08 | Defect escape rate | escapes / gates passed, where an escape is a defect whose ODC **trigger** is later than the stage that should have caught it | Three fields at defect close: ODC `defect_type` · ODC `defect_trigger` · IEEE 1044 `severity` | Per stage | 2 defects classifiable retroactively, both `checking` type | `TBC-OPERATOR` | Escapes are attributed to a stage, never averaged away | Operator | **ADOPTED** (`SECB-WP-FWK-016`, condition C-3) — recording not yet in force |
| K-09 | Constitutional-class recall — **not** accuracy | **Wilson 95% upper bound for a zero numerator: `z²/(n+z²)`**, `z=1.96`. The statistical rule of three (`3/n`) is retained as a reference column only — it is an approximation, and above n≈13.7 it is the **optimistic** one. **One observation = one governance verdict rendered on a merged PR's head SHA** — a definition that did not exist before `SECB-WP-FWK-034` and without which the series was not reproducible | Governance-verdict check-runs on merged PR heads | Per classifier change | **≤ 11.70%** — 0 downgrades in **29** observations, as of `e43fca8` · **instrument: Wilson 95% upper bound `z²/(n+z²)`**, not `3/n` · authoritative series: `docs/13-evidence/K09_LEDGER.md` | ≤10% requires **n ≥ 35** under Wilson, not n=30 — see the note below; ≤5% at n≈73 | No constitutional case may be downgraded — a single downgrade invalidates the bound | Operator | **ADOPTED and live** |
| K-11 | **Autonomy rate** | announced autonomous merges ÷ squash-merged PRs since `035b66d` | Merge record + the mandatory announcements | Per merge | **23/28 = 82.1%** as of `e43fca8`. Reported with its companion count as the guardrail requires: **9 changes correctly escalated and still open** — `#69` `#81` `#83` `#86` `#88` `#92` `#94` `#96` `#98`. The rate rose because low-risk work landed, not because escalation loosened | ~100% of `D0`/`D1` decisions | **Goodhart guard, binding: never reported without the count of decisions that were correctly escalated.** A rising rate achieved by classifying `D2` work as `D1` is a control failure, not an improvement. `L0` acts are excluded from the denominator | Operator | **Yes** |
| K-10 | Cost per accepted change | tokens × model price, derived not recorded | OpenTelemetry GenAI conventions: `gen_ai.client.token.usage` by `gen_ai.token.type`, `gen_ai.request.model` | Per WP | Unmeasured; **field names fixed** so future data is comparable | `TBC-OPERATOR` | Observational only — never a gate condition | Operator | **ADOPTED as a recording contract** (`SECB-WP-FWK-016`, condition C-3); collector deferred |
| K-12 | **Net surface change** (`FP-K02`, adopted from FPSA v1.0) | `files_added − files_deleted`, all history | `git log --diff-filter=A/D --name-only` | Per work package | **169 added / 5 deleted = +164**; a **3.0% retirement ratio**, and 113 of 164 tracked files are documents, as of `e43fca8` | No target — this is a **watch** metric | Never reported as a single net figure: added and retired are shown separately, because a healthy +2 and an unhealthy +40 have the same sign | Operator | **Yes, measured `SECB-WP-FWK-039`** |

## Readiness summary for the stage-1 gate

Updated after `SECB-WP-FWK-015` (research record:
`docs/17-references/RESEARCH-STAGE1-GATE-INSTRUMENTS.md`).

- **Every row was recounted from source on 2026-08-11** (`SECB-WP-FWK-035`), with
  the command recorded beside the value so the next recount is mechanical. **No
  value in this table is carried from a previous report.**

### `K-06` has breached its target, and the cause is queue wait (`SECB-WP-FWK-050`)

```text
                    target        as of 3b61307     as of e43fca8
median (p50)        ≤ 10 min      5.5 min           12.1 min      BREACHED
p90                 ≤ 30 min      26.2 min          1,142.5 min   BREACHED
max                 —             435.9 min         1,240.6 min
n                                 24                23
```

Nineteen hours at p90. **The cause is not slow execution.** The five merges of
2026-08-12 were of pull requests opened hours earlier, so the interval
`issue.created_at → merged_at` absorbed the time they spent waiting for a merge
decision.

This row's guardrail already anticipated that — *"the max is a human-decision
wait, not slow execution"* — but **the target does not distinguish the two, so it
is breached on the number as written.** Recording it as breached rather than
explaining it away, because a target that bends to accommodate its first real
excursion measures nothing afterwards.

**That makes it an instrument question, and the question belongs to the
authority.** Either `K-06` splits into agent time and decision wait — two rows,
two targets — or it stays breached whenever a queue forms. `SECB-WP-FWK-039` §7
argued that merge latency was this framework's binding constraint; this is that
argument arriving as a measurement rather than as prose.

Not fixed here: splitting a KPI's definition and target is a change on the
authority surface, and an executor proposing it is correct while an executor
landing it is not.

### An API-derived count without retries understates itself silently

The first pass of this recount reported **36** merged heads carrying check runs
and `K-09` **n=28**. With three retries per call the true values are **37** and
**29** — a transient API timeout had dropped rows.

The false version was the interesting one: 36 of 37 would have meant *a merged
head lost its check runs*, which would have read as a durability failure in the
evidence chain `K-01a` and `K-09` both depend on. **It was not true.** Recorded
because a claim being more interesting than its alternative is exactly when it
needs re-deriving, and every count in this table is now taken with retries.

### Values carry an as-of SHA, not a date (`SECB-WP-FWK-040`)

`FWK-035` recorded `K-01` as `31/31` and `K-09` as `n=23`, dated 2026-08-11. Both
were correct when written and wrong when merged: **a recount cannot count its own
merge.** PR #67 landed as `3b61307` and made them `32/32` and `n=24`.

This is structural, not carelessness, and it cannot be fixed by being more careful.
So values now state the commit they were counted at. *"Recounted 2026-08-11"*
cannot be checked; *"as of `3b61307`"* can.

### The instruments changed, not just the numbers

Three analyses (`FWK-037`, `FWK-038`, `FWK-039`) found defects in this table rather
than in the frameworks they were analysing:

| Row | Was | Is | Why |
|---|---|---|---|
| `K-09` | `3/n` = 12.50% at n=24 | **Wilson `z²/(n+z²)` = 13.80%** | `3/n` is an approximation, **optimistic for every n above ≈13.7** — and every figure this repository ever published sat above that crossover |
| `K-03` | `88%` | **`87.5%`** | The rounding went **up**, in the flattering direction. A metric that rounds toward its target should not round |
| `K-01` | one number | `K-01a` / `K-01b` | *Green* and *effective* are different claims. `K-01b` measures a job that **cannot fail**, and says so |
| `K-05` | one number | `K-05a` / `K-05b` | How many controls **can** block, versus whether they **do** |
| `K-07` | `17 merges, 0 rollbacks` | `K-07a` / `K-07b` / `K-07c` | **`0` rollbacks is ambiguous.** It means either nothing needed rolling back, or rollback has never been exercised — and `K-07c` is `0/0`, undefined, because no drill has ever run |

**`K-09`'s correction moves a rung, and this work package does not move it.** The
`A1 → A2` requirement *"≤10% at n=30"* was set because `3/30` is exactly 10.0%.
Under Wilson, n=30 gives 11.35%; ≤10% needs **n ≥ 35**. The ladder's
`advance_conditions` live in `config/delegation_envelope.json` — the authority
surface, `G4`. The disagreement is recorded in `K09_LEDGER.md` and put to the
constitutional authority. Raising a threshold is the *stricter* direction, and
"stricter" is an argument to bring to the authority, not a licence to act.

**`NFR-02` cites the old bound and is not corrected here.** It lives in
`NFR_CATALOGUE.md`, which PR #69 is currently changing. Editing it now would create
the overlap the standing intake constraint forbids, so it is deferred to the first
work package after #69 merges — named, not forgotten.

### `K-03`'s four misses are systematic, not scatter

Evidence completeness is **28/32**, and the four work packages missing a gate-result
table on their ticket are **#28, #36, #48 and #58** — which are **exactly the four
that escalated and were operator-merged.** For each, an authorization note was
posted and a gate table was not.

So evidence completeness is **worse for higher-authority changes than for
autonomous ones**, which is inverted from what the control exists for: the escalated
class is the one whose evidence matters most.

Not fixed by back-posting tables to those four tickets — that would be back-dating
evidence. **Fixed forward:** an escalated merge gets the same gate table an
autonomous merge does, and the omission is recorded here so the four gaps stay
visible rather than being papered over.
- **Eleven rows are measurable today** (`K-01a`/`K-01b`, `K-02`, `K-03`/`K-03a`/`K-03b`, `K-04`, `K-05a`/`K-05b`, `K-06`, `K-07a`/`K-07b`, `K-11`, `K-12`) with real
  baselines taken from the merged work packages. `K-11` was added by ballot 001 as
  objective `O7`'s measure; it is the only KPI carrying a binding Goodhart guard,
  because it is the only one whose numerator the measured party controls directly.
- **K-06 is now computed**, closing stage-2 condition `D-2`: median 5.5 minutes
  across 24 work packages. The old `p50 < 1 hour` target was met by an order of
  magnitude, which made it uninformative — a target no plausible regression can
  breach measures nothing. It is now set just above observed performance.
- **K-09 is computable, reproducible, and no longer computed with an
  approximation.** Wilson 95% upper bound **13.80%** from zero downgrades in **24**
  observations as of `3b61307`, where an observation is one governance verdict on a
  merged PR's head SHA. Before `SECB-WP-FWK-034` the denominator had **no
  definition**: this row carried `n=14` in one column and `n=16` in another while
  announcements had reached `n=37`, all hand-incremented on an unstated rule. The
  bound is weak by the arithmetic, not by evasion. It reaches ≤10% at **n=35**, not
  at the n=30 the ladder names — that discrepancy is the substantive finding of
  `SECB-WP-FWK-040` and is put to the constitutional authority rather than resolved
  here. **Both the announced series and the `3/n` figures that replaced it
  understated the bound.**
- **K-08 and K-10 have named instruments** costing three recorded fields each,
  with no tooling: ODC type/trigger plus IEEE 1044 severity, and the
  OpenTelemetry GenAI attribute names as a recording contract. Neither is
  implemented; both are now adoption decisions rather than open research.

Stage 1 requires that success KPIs be measurable. Eleven rows are measurable now (`K-01a` … `K-07b`, `K-09`, `K-11`, `K-12`), one is
defined and never exercised (`K-07c`), and two have defined methods awaiting
adoption (`K-08`, `K-10`).
`APPROVED_WITH_CONDITIONS` is therefore supportable with owners and dates that
mean something. **The choice of verdict still belongs to the gate authority,
not to the executor preparing this record.**

Cost-layer KPIs remain deliberately absent from any auto-merge criterion:
`PERFORMANCE_INDICATORS.md` requires that cost efficiency never override
safety, quality or authorization controls.
