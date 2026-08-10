# Stage-Gate Decision Record — `PRD_BASELINED` (v1.1.0)

Prepared by: Claude (executor), `SECB-WP-FWK-029` (issue #54)
Template: `docs/16-templates/STAGE_GATE_RECORD_TEMPLATE.md`
Supersedes: `STAGE_GATE_PRD_BASELINED.md` (v1.0.0), retained and banner-marked
Occasion: ballot 001 added objective `O7`, a §4 material change, so stage 1 was
re-entered

> **Prepared, not issued.** The `decision` field is empty. Stage 1's authority is
> the Product Sponsor — the operator, who also holds Product Owner and
> constitutional authority under `SINGLE_IDENTITY_SOD_ACCEPTED_RISK.md`, cited per
> that record's condition 1. An executor that supplied the approval for a baseline
> it wrote would make the record worthless as evidence.

## Evidence minimum (§3)

| Field | Value |
|---|---|
| Project / release identifier | SecB Engineer Loop · pre-release, no version tag |
| Stage and gate identifier | Stage 1, PRD Review and Baseline → gate `PRD_BASELINED`, second pass |
| Artifact versions | `PRD-ENGINEER-LOOP.md` **v1.1.0 candidate** · `REQUIREMENT_CATALOGUE.md` v2 (22 FRs) · `NFR_CATALOGUE.md` v2 (18 NFRs, `NFR-08` measured) · `KPI_BASELINE.md` v2 (11 KPIs, 8 measurable) · `RTM.md` v2 · `STAKEHOLDER_REGISTER.md` v1 · `RAID_REGISTER.md` v1 |
| Evidence references | Ballots on `PACKET-001` and `PACKET-002`, both `APPROVE_OPTION_A`, 2026-08-10 · merges `06ed153` (v1.0.0 verdict, superseded) → `2391f46` |
| Findings | The only change since the v1.0.0 verdict is the addition of `O7` and its two requirements. **Every condition met at v1.0.0 remains met**; one is now met *better* — see below |
| Exceptions | `TX-01` narrowed (framework layer verified by trial) · `TX-02` open · `TX-03` open · `I-01` narrowed to stages 3–6 |
| Risk assessment | The `O7`-specific risk from Packet 001 §9 — `O7` read as licence to weaken a control — is mitigated inside the objective text and by `K-11`'s binding Goodhart guard |
| Conditions and owners | C-3 and C-4 **carry forward** from the superseded record; C-1, C-2, C-5 remain closed. No new condition is proposed |
| Eligible approvers | Operator, as Product Sponsor. No Product Steering Committee exists |
| Votes / signatures | **None. Unissued.** |
| Decision timestamp | — |
| Effective status | **`PREPARED_AWAITING_VERDICT`** |
| Expiry / revalidation | On any further change to scope, success metrics or acceptance criteria, or to assumption A-02 |

## Exit-condition assessment against v1.1.0

| # | Condition | State | What changed since v1.0.0 |
|--:|---|---|---|
| 1 | Business owner and product owner identified | **Met** | Unchanged — operator holds both, collapse recorded |
| 2 | Scope and exclusions unambiguous | **Met** | `O7` carries an explicit `L0` exclusion, so the new objective narrows rather than widens scope |
| 3 | Success KPIs measurable | **Met, and improved** | Was: 6 measurable, 1 uncomputed, 3 not measurable. Now **8 measurable** — K-06 computed at median 5.5 min, and `K-11` added already measured at 75%. K-08 and K-10 remain adopted-not-implemented under C-3 |
| 4 | Acceptance criteria testable | **Met** | `O7`'s criterion is `K-11`, which is computed from the merge record |
| 5 | Critical assumptions and dependencies documented | **Met** | Unchanged |
| 6 | Major regulatory concerns identified | **Met, conditionally** | Unchanged — A-04 still asserts no regulated data |
| 7 | PRD versioned | **Met** | v1.1.0 with an updated change-control block |
| 8 | PRD formally approved | **Pending — this record** | The v1.0.0 approval does not carry forward across a material change |

**Seven of eight met; the eighth is this decision.** Condition 3 is stronger than
at v1.0.0 rather than weaker, which is the unusual case: a re-baseline that
improves the evidence it is judged on.

## Available verdicts (§2)

`APPROVED` · `APPROVED_WITH_CONDITIONS` · `REWORK_REQUIRED` · `BLOCKED` ·
`REJECTED` · `HUMAN_REQUIRED`

**`REWORK_REQUIRED` and `BLOCKED` are not indicated** — no condition is unmet and
nothing external blocks progression. **`APPROVED` plain is now defensible**, which
it was not at v1.0.0: the two findings that made it weak then were condition 3's
partial state and the vacuous business-rules pass, and condition 3 has since
improved to eight measurable KPIs. The remaining open items (C-3, C-4) already
have owners and milestones from the superseded record, so
`APPROVED_WITH_CONDITIONS` carrying them forward is the tidier option and
`APPROVED` with them noted is also honest.

Recommendation: **`APPROVED_WITH_CONDITIONS`**, carrying C-3 and C-4 unchanged —
because those conditions are still open and a verdict that silently drops a
carried condition is how conditions get lost.

## Effect once issued

- PRD v1.1.0 becomes the baseline; stage 1 passes for the second time.
- **Stage 2's deferred verdict becomes issuable**, once against seven objectives
  (`SECB-WP-FWK-030`), which is what ballot 002 chose.
- `O7` becomes a tracked objective, so `K-11` regressions are visible.

## To issue this verdict

State the verdict, the date and any conditions — in session or on issue #54. The
executor then fills this record, sets the PRD to baselined, and prepares the
stage-2 verdict against seven objectives in one change.
