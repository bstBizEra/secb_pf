# Stage-Gate Decision Record — `PRD_BASELINED`

Prepared by: Claude (executor), `SECB-WP-FWK-014` (issue #24)
Carries the twelve evidence-minimum fields of `DELIVERY_LIFECYCLE.md` §3.

> **This record is prepared, not issued.** The `decision` field is
> deliberately empty. Stage 1's gate authority is the Product Steering
> Committee or an authorized ballot — in this deployment, the operator as
> Product Sponsor. An executor that filled in its own gate verdict would be
> performing the self-approval the framework exists to prevent, and the record
> would be worthless as evidence.

## Evidence minimum (§3)

| Field | Value |
|---|---|
| Project / release identifier | SecB Engineer Loop · pre-release, no version tag |
| Stage and gate identifier | Stage 1, PRD Review and Baseline → gate `PRD_BASELINED` |
| Artifact versions | `PRD-ENGINEER-LOOP.md` (merged `2f26cca`, status *Draft*, unversioned) · `STAKEHOLDER_REGISTER.md` v1 · `RAID_REGISTER.md` v1 · `KPI_BASELINE.md` v1 |
| Evidence references | Issues #2–#24 · merge commits `cb03eba` → `19b5461` · review `REV-SECB-ENGLOOP-MVP-001-20260810` |
| Findings | Seven of eight exit conditions are satisfiable from existing artifacts; **two are not** — see below |
| Exceptions | Traceability exception I-01: artifacts exist at stages 7–8 with no recorded stage 1–6 verdicts (`DELIVERY_LIFECYCLE.md` §1) |
| Risk assessment | Seven risks recorded, R-04 and R-05 (vacant roles, collapsed gate authorities) rated High and bearing directly on this gate |
| Conditions and owners | Proposed below; owners are the operator pending confirmation |
| Eligible approvers | Operator, as Product Sponsor and constitutional authority. No steering committee exists (deferred D3, risk R-05) |
| Votes / signatures | **None. Unissued.** |
| Decision timestamp | — |
| Effective status | **`PREPARED_AWAITING_VERDICT`** |
| Expiry / revalidation | On material change to scope, critical requirements, or the product-selection assumption A-02 (§4 change control) |

## Exit-condition assessment

Stage 1 passes when all eight hold. Assessed against the tree at this commit:

| # | Condition | State | Evidence |
|--:|---|---|---|
| 1 | Business owner and product owner identified | **Not met** | `STAKEHOLDER_REGISTER.md` — product owner is `TBC-OPERATOR`; only the sponsor is confirmed. Requires one operator statement. |
| 2 | Scope and exclusions unambiguous | Met | `PRD-ENGINEER-LOOP.md` §8; Out-of-Scope reproduces the `NOT_AUTHORIZED` posture verbatim |
| 3 | Success KPIs measurable | **Partially met** | `KPI_BASELINE.md`: six measurable with real baselines, one computable but never run, three not measurable |
| 4 | Acceptance criteria testable | Met | PRD §12 definition statement is testable against K-01…K-05 |
| 5 | Critical assumptions and dependencies documented | Met | `RAID_REGISTER.md` — six assumptions, five dependencies |
| 6 | Major regulatory concerns identified | Met, conditionally | Assumption A-04 states no regulated or personal data is in scope; if false, stage 5 obligations grow |
| 7 | PRD versioned | **Not met** | The PRD carries no version number and no change-control baseline |
| 8 | PRD formally approved | **Not met** | No approval record exists; that is this document |

## Proposed conditions, if the authority chooses `APPROVED_WITH_CONDITIONS`

| # | Condition | Owner | Due |
|--:|---|---|---|
| C-1 | Confirm business owner and product owner by name | Operator | Before stage 2 opens |
| C-2 | Decide assumption A-02 — is the first product the Engineer Loop itself? | Operator | Before stage 2 opens |
| C-3 | Either assign owners and formulas for K-08…K-10, or narrow the PRD's success definition to the six computable metrics | Operator | Before stage 6 |
| C-4 | Assign the governance owner open since import (`AGENTS.md` §13) | Operator | Before stage 5 |
| C-5 | Version the PRD and open its change-control baseline | Executor, on the verdict | Same day as the verdict |

## Available verdicts (§2)

`APPROVED` · `APPROVED_WITH_CONDITIONS` · `REWORK_REQUIRED` · `BLOCKED` ·
`REJECTED` · `HUMAN_REQUIRED`

On the evidence above, `APPROVED` is not available: conditions 1, 7 and 8 are
unmet and three of them cannot be met by an executor. The honest options are
`APPROVED_WITH_CONDITIONS` with C-1…C-5 owned and dated, or `REWORK_REQUIRED`
if the authority judges that a product owner and a measurable KPI set must
exist before any baseline is declared.

## To issue this verdict

The gate authority states the verdict, the date, and any conditions — in
session, or as a comment on issue #24. The executor then fills the record,
versions the PRD, and updates the lifecycle position table in the same change,
citing this record.
