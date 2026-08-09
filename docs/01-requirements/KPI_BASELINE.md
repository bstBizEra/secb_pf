# KPI Baseline — SecB Engineer Loop

Status: Prepared for stage-1 gate (`SECB-WP-FWK-014`)
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
| K-06 | Loop lead time, ticket to merge | `merged_at − issue.created_at`, median | GitHub timestamps | Per WP | Not computed | p50 < 1 hour | Speed must never be met by skipping evidence | Operator | **Formula ready, never computed** |
| K-07 | Autonomous merges under the envelope | count, and rollback rate among them | Governance-verdict job + merge log | Per merge | 0 (envelope ratified 2026-08-10) | Ladder `A1` needs 30 with zero rollback | One rollback resets the count | Operator | **Yes, from now** |
| K-08 | Defect escape rate | defects found after a gate passed / gates passed | Issue labels | Per stage | **Unmeasured** — no defect taxonomy exists | `TBC-OPERATOR` | — | Unassigned | **No** |
| K-09 | Classifier accuracy | confusion matrix over a labelled PR corpus | Golden corpus | Per classifier change | **Not computable** — 14 WPs is not a corpus (deferred D5) | `TBC-OPERATOR` | No constitutional case may be downgraded | Unassigned | **No** |
| K-10 | Cost per accepted change | tokens and tool calls per merged WP | **No instrumentation exists** | — | Unmeasured | `TBC-OPERATOR` | Cost must never override safety | Unassigned | **No** |

## Readiness summary for the stage-1 gate

- **Six metrics are measurable today** (K-01…K-05, K-07) with real baselines
  taken from the fourteen merged work packages.
- **One has a formula but has never been run** (K-06). It is computable from
  data that already exists; nothing blocks it but the doing.
- **Three are not measurable** (K-08, K-09, K-10): they need a defect
  taxonomy, a labelled corpus, and cost instrumentation respectively. K-09's
  blocker is recorded as deferred capability D5; K-10 has no instrumentation in
  the framework at all.

Stage 1 requires that success KPIs be measurable. Six are, and three are not.
The honest options for the gate are `APPROVED_WITH_CONDITIONS` — naming owners
and dates for K-08 to K-10 — or narrowing the PRD's success definition to the
six that can actually be computed. **That choice belongs to the gate
authority, not to the executor preparing this record.**

Cost-layer KPIs remain deliberately absent from any auto-merge criterion:
`PERFORMANCE_INDICATORS.md` requires that cost efficiency never override
safety, quality or authorization controls.
