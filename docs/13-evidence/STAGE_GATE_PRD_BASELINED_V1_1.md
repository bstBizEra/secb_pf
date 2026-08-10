# Stage-Gate Decision Record — `PRD_BASELINED` (v1.1.0)

Prepared by: Claude (executor), `SECB-WP-FWK-029` (issue #54)
Template: `docs/16-templates/STAGE_GATE_RECORD_TEMPLATE.md`
Supersedes: `STAGE_GATE_PRD_BASELINED.md` (v1.0.0), retained and banner-marked
Occasion: ballot 001 added objective `O7`, a §4 material change, so stage 1 was
re-entered

> **Verdict issued by the gate authority — operator (vily), 2026-08-10.** The
> executor prepared this record and recorded the verdict; it did not supply it.
> Stage 1's authority is the Product Sponsor, who also holds Product Owner and
> constitutional authority under `SINGLE_IDENTITY_SOD_ACCEPTED_RISK.md`, cited per
> that record's condition 1.
>
> **Structural correction, on the authority's own finding.** An earlier draft read
> *"seven of eight met; the eighth is this decision"* — which made the verdict a
> criterion for itself. A verdict is the **output** of the criteria, never one of
> them. The correct count is **7 of 7 criteria passed**, and the decision is
> recorded on a separate plane below. Three related defects are corrected with it:
> *condition* now names either a gate criterion (`GC-nn`) or a carried obligation
> (`C-n`) but never both; disposition and obligation posture are separate fields
> rather than one overloaded status; and carried conditions live in
> `CONDITION_REGISTER.md`, where silence cannot close them.

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
| Votes / signatures | Operator (vily), sole eligible approver, in session 2026-08-10. No ballot layer exists (`ballot_layer.state = NOT_ACTIVE`) |
| Decision timestamp | 2026-08-10 |
| Effective status | See the two-plane disposition below — a single field cannot carry it |
| Expiry / revalidation | On any further change to scope, success metrics or acceptance criteria, or to assumption A-02 |

## Disposition — two planes, rendered verdict

A single status cannot answer both *"is the artifact good enough"* and *"are prior
obligations closed"*. They are independent, so they are recorded independently.

**Plane A — baseline decision**

```text
baseline_disposition: APPROVED
criteria_passed:      7
criteria_total:       7
```

**Plane B — obligation posture**

```text
obligation_posture: OPEN_NON_BLOCKING
open_conditions:    C-3, C-4
control_status:     each has owner, due stage, closure predicate,
                    required evidence, closure authority and blocking scope
                    -> CONDITION_REGISTER.md
```

**Rendered verdict**

| Dimension | Value |
|---|---|
| Evidence readiness | `PASS — 7/7 criteria` |
| PRD baseline disposition | `APPROVED` |
| Obligation posture | `OPEN_NON_BLOCKING — C-3, C-4` |
| **Rendered verdict** | **`APPROVED_WITH_CONDITIONS`** |
| Stage 2 | `AUTHORIZED_FOR_COMPOSITE_VERDICT` — one verdict across seven objectives, per ballot 002 |
| Stage 3 | `PENDING_STAGE_2_PASS` — opens only on a passing composite verdict with no condition blocking stage 3 |

`APPROVED` alone was available on the evidence and was **not** chosen, because
`C-3` and `C-4` are open and a verdict that omits a carried condition is how
conditions get lost. This is the posture NASA's review practice permits: items may
remain open where there is a disposition, a timely closure plan, and tracking
through to actual closure — rather than pretending they vanished so the review can
proceed ([NPR 7123.1D Appendix G](https://nodis3.gsfc.nasa.gov/displayDir.cfm?Internal_ID=N_PR_7123_001D_&page_name=AppendixG)).

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
**All seven criteria passed.** *Formal approval is not a criterion* — it is the
decision that follows from them, recorded on Plane A above. Its presence in an
earlier draft as an eighth row was the self-referential defect the authority
identified.

### `GC-03` — recorded in detail, because its strength was mistakable for closure

```text
GC-03:
  result:   PASS
  strength: IMPROVED
  measurable_kpi_previous: 6
  measurable_kpi_current:  8
  new_evidence: [K-06, K-11]
```

**This does not close `C-3` or `C-4`.** `C-3` requires three named instruments to
be in force; `K-06` and `K-11` are different metrics that were already computable.
`C-4` requires a named governance owner, on which no measurement bears. A
strengthened gate criterion closes a carried obligation only when its evidence
matches that obligation's closure predicate directly — reasoning recorded in
`CONDITION_REGISTER.md`.

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

## Effect, in force on merge

- PRD **v1.1.0 is the baseline**; stage 1 passed for the second time.
- Stage 2 is `AUTHORIZED_FOR_COMPOSITE_VERDICT`: **one** verdict across seven
  objectives, which is what ballot 002 bought. Aggregation is structured, not
  averaged — each objective is evaluated with its own evidence and a failing
  objective cannot be offset by passing ones.
- Stage 3 is `PENDING_STAGE_2_PASS`. It does not open because a document says
  "open"; it opens when the composite verdict passes and no open condition blocks
  it.
- `C-3` and `C-4` remain `OPEN`, tracked in `CONDITION_REGISTER.md` with the same
  IDs, blocking stages 6 and 5 respectively — **neither blocks stage 2 or 3.**
- `O7` is a tracked objective; `K-11` regressions are visible.
