# Stage-Gate Decision Record — `PRD_BASELINED` (v1.0.0) — **SUPERSEDED**

> **Superseded, not withdrawn.** This record's verdict was issued against PRD
> **v1.0.0**. Ballot 001 (2026-08-10) added objective `O7`, which is a §4
> material change, so stage 1 was re-entered and a new record governs:
> `STAGE_GATE_PRD_BASELINED_V1_1.md`. This record is retained because the
> evidence chain must show what was approved when, not only what is current.
> Its conditions C-3 and C-4 carry forward to the new record rather than lapsing.

Prepared by: Claude (executor), `SECB-WP-FWK-014` (issue #24)
Verdict recorded by: Claude (executor), `SECB-WP-FWK-016` (issue #28)
Carries the twelve evidence-minimum fields of `DELIVERY_LIFECYCLE.md` §3.

> **Authorship boundary.** The verdict below was **issued by the gate
> authority**, not by the executor. Provenance: operator (vily) instruction in
> session on 2026-08-10 — *"จัดการตาม คุณแนะนำ ทำให้ SecB Project Framework
> สามารถใช้งานได้จริง เป็นสารตั้งต้นของ BST ในสร้างโปรเจ็คต่อๆไปได้จริง"* —
> adopting the executor's recommendation of `APPROVED_WITH_CONDITIONS` and
> confirming the product's purpose. The executor recommended and recorded; the
> authority decided. Conditions C-1…C-5 are the executor's recommendation as
> adopted, not independent operator statements.

## Evidence minimum (§3)

| Field | Value |
|---|---|
| Project / release identifier | SecB Engineer Loop · pre-release, no version tag |
| Stage and gate identifier | Stage 1, PRD Review and Baseline → gate `PRD_BASELINED` |
| Artifact versions | `PRD-ENGINEER-LOOP.md` (merged `2f26cca`, status *Draft*, unversioned) · `STAKEHOLDER_REGISTER.md` v1 · `RAID_REGISTER.md` v1 · `KPI_BASELINE.md` v1 |
| Evidence references | Issues #2–#24 · merge commits `cb03eba` → `19b5461` · review `REV-SECB-ENGLOOP-MVP-001-20260810` |
| Findings | Five of eight exit conditions met outright; condition 3 met in part (seven of ten KPIs measurable, the remaining two with adopted methods); conditions 1, 7 and 8 resolved by this verdict and its provenance |
| Exceptions | Traceability exception I-01: artifacts exist at stages 7–8 with no recorded stage 1–6 verdicts (`DELIVERY_LIFECYCLE.md` §1) |
| Risk assessment | Seven risks recorded, R-04 and R-05 (vacant roles, collapsed gate authorities) rated High and bearing directly on this gate |
| Conditions and owners | Proposed below; owners are the operator pending confirmation |
| Eligible approvers | Operator, as Product Sponsor and constitutional authority. No steering committee exists (deferred D3, risk R-05) |
| Votes / signatures | Operator (vily), sole eligible approver — instruction in session, quoted above. No ballot layer exists (`ballot_layer.state = NOT_ACTIVE`) |
| Decision timestamp | 2026-08-10 |
| Effective status | **`APPROVED_WITH_CONDITIONS`** — effective on merge of `SECB-WP-FWK-016` |
| Expiry / revalidation | On material change to scope, critical requirements, or the product-selection assumption A-02 (§4 change control) |

## Exit-condition assessment

Stage 1 passes when all eight hold. Assessed against the tree at this commit:

| # | Condition | State | Evidence |
|--:|---|---|---|
| 1 | Business owner and product owner identified | **Met** | Operator (vily) confirmed as Business Owner and Product Owner; the collapse of sponsor, owner and gate authority onto one identity is recorded as an accepted risk with named compensating controls (`SINGLE_IDENTITY_SOD_ACCEPTED_RISK.md`) |
| 2 | Scope and exclusions unambiguous | Met | `PRD-ENGINEER-LOOP.md` §8; Out-of-Scope reproduces the `NOT_AUTHORIZED` posture verbatim |
| 3 | Success KPIs measurable | **Met in part, method adopted** | `KPI_BASELINE.md`: seven measurable (K-09 now computable — 95% upper bound 18.75% on the downgrade rate, 0 in 16); K-08 and K-10 carry adopted instruments costing three recorded fields each (`SECB-WP-FWK-015`). Adoption is not implementation — condition C-3 tracks it |
| 4 | Acceptance criteria testable | Met | PRD §12 definition statement is testable against K-01…K-05 |
| 5 | Critical assumptions and dependencies documented | Met | `RAID_REGISTER.md` — six assumptions, five dependencies |
| 6 | Major regulatory concerns identified | Met, conditionally | Assumption A-04 states no regulated or personal data is in scope; if false, stage 5 obligations grow |
| 7 | PRD versioned | **Met** | PRD raised to **v1.0.0, baselined**, with a change-control block naming the re-baseline trigger |
| 8 | PRD formally approved | **Met** | This record, verdict `APPROVED_WITH_CONDITIONS`, issued by the gate authority 2026-08-10 |

## Conditions of approval

Owned and dated. Advancement past the stated milestone without the condition
closed is a change-control event (§4), not a matter of discretion.

| # | Condition | Owner | Due | Status |
|--:|---|---|---|---|
| C-1 | Business owner and product owner named | Operator | Before stage 2 | **Closed** — operator holds both; collapse accepted with compensating controls |
| C-2 | Assumption A-02 decided | Operator | Before stage 2 | **Closed** — confirmed 2026-08-10: the product is the SecB framework itself, whose users are BST's subsequent projects. PRD §2 and §4 reconciled |
| C-3 | Implement the three adopted KPI instruments — ODC `defect_type`/`defect_trigger` + IEEE 1044 `severity`; the rule-of-three tally; the OTel GenAI attribute names | Operator, executed by agent | Before stage 6 | **Open** — methods adopted, recording not yet in force |
| C-4 | Assign the governance owner open since import (`AGENTS.md` §13) | Operator | Before stage 5 | **Open** — the accepted-risk record covers stages 1–8 only |
| C-5 | PRD versioned with a change-control baseline | Executor | With the verdict | **Closed** — v1.0.0 |

### Standing limit carried forward from this gate

**Stage 9 is unreachable without a second identity.** Its exit condition
requires QA and Security to approve *independently*, and no compensating
control manufactures independence from a single identity
(`docs/17-references/RESEARCH-STAGE1-GATE-INSTRUMENTS.md`). This is recorded at
stage 1 so it is discovered now rather than when a release candidate waits.

## Available verdicts (§2)

`APPROVED` · `APPROVED_WITH_CONDITIONS` · `REWORK_REQUIRED` · `BLOCKED` ·
`REJECTED` · `HUMAN_REQUIRED`

**Issued: `APPROVED_WITH_CONDITIONS`.** `APPROVED` was not available while
conditions 1, 7 and 8 stood unmet; the authority's instruction resolved 1 and
8, the executor closed 7, and C-3 and C-4 remain open with owners and dates.
`REWORK_REQUIRED` was the alternative had the authority judged that a fully
measurable KPI set must precede any baseline.

## Effect of this verdict

- Stage 1 is **passed**; state advances to `PRD_BASELINED`.
- Stage 2 (Requirement Decomposition → `REQUIREMENTS_READY`) is **open**. Its
  first obligation is the RTM, pending since `SECB-WP-FWK-005`.
- The stage-1 portion of traceability exception **I-01 is cleared**. Stages 2–6
  remain without recorded verdicts, so the exception persists for them and is
  narrowed rather than closed.
- Re-baseline trigger: any change to scope, success metrics or acceptance
  criteria requires a new PRD version and a fresh pass of this gate (§4).

## Revalidation

This verdict expires if assumption A-02 changes — that is, if the first product
ceases to be the SecB framework itself — or on any material change listed in
§4. Conditions C-3 and C-4 are reviewed at their milestones; an unmet condition
at its milestone is a change-control event, not a discretionary delay.
