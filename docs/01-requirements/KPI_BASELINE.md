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
| K-01 | PRs merged with all gates green | `green_prs / merged_prs` | GitHub check-runs API | Per merge | 13/13 (100%) | 100% | Never met by relaxing a gate | Operator | **Yes** |
| K-02 | Unauthorized-action rate | count of merges without a passing Authority gate | Check-runs API + issue records | Per merge | 0 | 0 | Any occurrence is an incident, not a metric movement | Operator | **Yes** |
| K-03 | Evidence completeness | WPs whose gate results are recorded on the ticket / WPs merged | Issue comments | Per WP | 14/14 | 100% | Presence is not sufficiency; a comment must cite run IDs | Operator | **Yes** |
| K-04 | First-pass budget compliance | WPs needing no budget amendment / WPs merged | Issue comments | Per WP | 11/14 (79%) | ≥90% | Not met by inflating declared budgets | Executor | **Yes** |
| K-05 | Executable control gates | mechanized gates / 10 | `ci.yml` versus `CONTROL_GATES.md` | Per change to CI | 3/10 (Authority, Test, Budget) | 10/10 | A gate counts only once proven to fail on a real PR (`KN-001`) | Operator | **Yes** |
| K-06 | Loop lead time, ticket to merge | `merged_at − issue.created_at`, median | GitHub timestamps | Per WP | **n=24 · median 5.5 min · p90 26.2 min · max 435.9 min** | p50 ≤ 10 min · p90 ≤ 30 min | Speed must never be met by skipping evidence; the max is a human-decision wait, not slow execution | Operator | **COMPUTED** (`SECB-WP-FWK-028`) |
| K-07 | Autonomous merges under the envelope | count, and rollback rate among them | Governance-verdict job + merge log | Per merge | 0 (envelope ratified 2026-08-10) | Ladder `A1` needs 30 with zero rollback | One rollback resets the count | Operator | **Yes, from now** |
| K-08 | Defect escape rate | escapes / gates passed, where an escape is a defect whose ODC **trigger** is later than the stage that should have caught it | Three fields at defect close: ODC `defect_type` · ODC `defect_trigger` · IEEE 1044 `severity` | Per stage | 2 defects classifiable retroactively, both `checking` type | `TBC-OPERATOR` | Escapes are attributed to a stage, never averaged away | Operator | **ADOPTED** (`SECB-WP-FWK-016`, condition C-3) — recording not yet in force |
| K-09 | Constitutional-class recall — **not** accuracy | Rule of three: with 0 downgrades in *n* observations, 95% upper bound on the downgrade rate = `3/n` | Classifier verdict versus the verdict a human would give, per PR | Per classifier change | **≤ 21.4%** (0 downgrades in 14) | ≤10% at n=30; ≤5% at n=60 | No constitutional case may be downgraded — a single downgrade invalidates the bound | Operator | **ADOPTED and live** — 0 downgrades in 16 observations |
| K-10 | Cost per accepted change | tokens × model price, derived not recorded | OpenTelemetry GenAI conventions: `gen_ai.client.token.usage` by `gen_ai.token.type`, `gen_ai.request.model` | Per WP | Unmeasured; **field names fixed** so future data is comparable | `TBC-OPERATOR` | Observational only — never a gate condition | Operator | **ADOPTED as a recording contract** (`SECB-WP-FWK-016`, condition C-3); collector deferred |

## Readiness summary for the stage-1 gate

Updated after `SECB-WP-FWK-015` (research record:
`docs/17-references/RESEARCH-STAGE1-GATE-INSTRUMENTS.md`).

- **Six metrics are measurable today** (K-01…K-05, K-07) with real baselines
  taken from the fourteen merged work packages.
- **K-06 is now computed**, closing stage-2 condition `D-2`: median 5.5 minutes
  across 24 work packages. The old `p50 < 1 hour` target was met by an order of
  magnitude, which made it uninformative — a target no plausible regression can
  breach measures nothing. It is now set just above observed performance.
- **K-09 is now computable** and has a value: a 95% upper bound of **21.4%** on
  the downgrade rate, from zero downgrades in fourteen observations. The bound
  is weak by design of the arithmetic, not by evasion — it tightens to ≤10% at
  thirty observations, which is also the `A1 → A2` ladder threshold, giving that
  rung a statistical meaning it previously lacked.
- **K-08 and K-10 have named instruments** costing three recorded fields each,
  with no tooling: ODC type/trigger plus IEEE 1044 severity, and the
  OpenTelemetry GenAI attribute names as a recording contract. Neither is
  implemented; both are now adoption decisions rather than open research.

Stage 1 requires that success KPIs be measurable. Seven are measurable now,
and the remaining two have defined methods awaiting adoption.
`APPROVED_WITH_CONDITIONS` is therefore supportable with owners and dates that
mean something. **The choice of verdict still belongs to the gate authority,
not to the executor preparing this record.**

Cost-layer KPIs remain deliberately absent from any auto-merge criterion:
`PERFORMANCE_INDICATORS.md` requires that cost efficiency never override
safety, quality or authorization controls.
