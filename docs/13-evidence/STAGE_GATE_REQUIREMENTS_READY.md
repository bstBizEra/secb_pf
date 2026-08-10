# Stage-Gate Decision Record — `REQUIREMENTS_READY` (composite, 7 objectives)

Prepared by: Claude (executor), `SECB-WP-FWK-032` (issue #60)
Supersedes: the six-objective draft prepared under `SECB-WP-FWK-020`
Template: `docs/16-templates/STAGE_GATE_RECORD_TEMPLATE.md` · Model:
[`TWO_PLANE_DECISION_MODEL.md`](../00-governance/TWO_PLANE_DECISION_MODEL.md)
Authorized as composite by ballot 002 (`APPROVE_OPTION_A`, 2026-08-10)

> **Prepared, not issued.** Stage 2's authority is the Product Owner and the
> Architecture Lead, both collapsed onto the operator under
> `SINGLE_IDENTITY_SOD_ACCEPTED_RISK.md`, cited per that record's condition 1.
>
> First record written **under** the two-plane policy rather than corrected into
> it. `GATE-001` is respected by construction: **no criterion row is the verdict.**

## Evidence minimum (§3)

| Field | Value |
|---|---|
| Project / release identifier | SecB Engineer Loop · pre-release |
| Stage and gate identifier | Stage 2, Requirement Decomposition → gate `REQUIREMENTS_READY`, composite |
| Artifact versions | `PRD-ENGINEER-LOOP.md` **v1.1.0 baselined** · `REQUIREMENT_CATALOGUE.md` v2 (22 FRs, 7 objectives) · `NFR_CATALOGUE.md` v2 · `RTM.md` v2 · `BOOTSTRAP_STORY_DOR.md` v0.1 · `KPI_BASELINE.md` v2 |
| Evidence references | Merges `9045241` `29da444` `32252f3` `b99b0dc` `cb8fbec` `3237844` · ballots 001 and 002 · issues #32 #34 #54 #56 #58 #60 |
| Findings | All seven objectives pass. Two findings from the earlier draft persist and are re-stated below, neither at blocker level |
| Exceptions | `TX-01` narrowed · `TX-02` open · `TX-03` open · `I-01` narrowed to stages 3–6 |
| Risk assessment | `R-06` reduced (KPI measurability improved to 8 measurable). No High risk unique to this gate |
| Conditions | Cited from `CONDITION_REGISTER.md`; this decision creates none |
| Eligible approvers | Operator. No Architecture Review Board exists |
| Votes / signatures | **None. Unissued.** |
| Decision timestamp | — |
| Effective status | `PREPARED_AWAITING_VERDICT` |
| Expiry / revalidation | On any change to the PRD baseline, a `P1` requirement, or an accepted conflict disposition |

## Per-objective evaluation

Ballot 002 authorized **one** verdict, which is not the same as one judgement. Each
objective is evaluated with its own evidence; **a failing objective cannot be
offset by passing ones.**

| # | Objective | Requirements | Evaluation | Evidence |
|--:|---|---|---|---|
| `O1` | Every control gate mechanically fail-able | 10 FRs | **PASS** | 4 gates executable and each **proven failing** on a real PR: runs `31320436859`, `31325014002`, the Genesis verdict, and the trial's exit-4 |
| `O2` | Certify the router to `SANDBOX_TESTED` | `FR-14` `FR-15` | **PASS** | `REV-SECB-ENGLOOP-MVP-001-20260810`; digests re-verified at two later WPs |
| `O3` | 100% of merged PRs green | `FR-09` `FR-19` | **PASS** | `K-01` = 30/30. `FR-19` is adopted-not-implemented under `C-3`, which does not affect the objective's measure |
| `O4` | Unbroken traceability | `FR-01` `FR-07` `FR-08` `FR-12` | **PASS** | `RTM.md` with forward and reverse traces; breaks recorded as `TX-nn` rather than hidden — which is what the objective requires |
| `O5` | Learn Loop each round | `FR-13` | **PASS, thin** | `KNOWLEDGE_REGISTER.md`, 5 objects, all `Proposed`. The objective's *cadence* claim is unmet and was formally accepted as conflict 2 in the catalogue |
| `O6` | Reach an R0 read-only routing pilot | `FR-16` | **PASS for the requirement, objective not yet reached** | FIT-101–120 20/20, replayed against v1.5.1. The pilot **authorization** is a stage-6/11 act, formally accepted as conflict 3 |
| `O7` | Minimise human involvement | `FR-21` `FR-22` + 5 re-mapped | **PASS** | `K-11` = **14 autonomous of 19 post-Genesis merges = 74%**, recounted at this commit rather than carried from an earlier report. `FR-22` unimplemented — see below |

### `O7` passes with `FR-22` unimplemented, and why that is not a failure

`FR-22` requires ballot-dependent verdicts to be satisfiable. They are not:
`ballot_layer.state = NOT_ACTIVE`. But stage 2's criteria ask whether requirements
are **decomposed, owned and testable** — not whether they are built. A requirement
correctly recorded as unimplemented with its blocker named is a *decomposition
success*; treating it as an objective failure would confuse stage 2 with stage 7.

`O7`'s measure is `K-11`, which is measured and passing. `FR-22` is the path to
raising it, not a precondition for having it.

## Aggregate

```text
all seven hard objectives pass                 -> yes
quorum satisfied or not required               -> not required (ballot_layer NOT_ACTIVE)
no blocking objection                          -> none raised
only controlled obligations remain             -> C-3, C-4, both controlled
=> composite baseline disposition: APPROVED
```

Derived, not declared. Had any objective failed, the rule yields
`REWORK_REQUIRED` regardless of the other six.

## Gate-criteria assessment (`GC-nn`)

The seven exit criteria from `DELIVERY_LIFECYCLE_STAGES.md` §2, as amended by
`FWK-019-A`. Assessed against the committed tree.

| # | Criterion | State | Evidence |
|---|---|---|---|
| `GC-01` | Every PRD objective maps to ≥1 requirement | **Met** | Coverage table: `O1`→10, `O2`→2, `O3`→2, `O4`→4, `O5`→1, `O6`→1, `O7`→2+5 re-mapped |
| `GC-02` | Every requirement has an owner and acceptance method | **Met with qualification** | All 22 rows carry both. `FR-17`'s method remains descriptive rather than executable — finding 1, unchanged |
| `GC-03` | Critical business rules documented | **Met by recorded non-applicability** | No calculations exist; `L0` and the classifier are already normative. Finding 2, unchanged — the authority accepts the non-applicability explicitly |
| `GC-04` | NFRs carry measurable targets | **Met, improved** | 18 NFRs; `NFR-08` now has a measured basis (median 5.5 min) and a target derived from the distribution rather than a round number |
| `GC-05` | Dependencies and external interfaces identified | **Met** | `RAID` D-01…D-05; GitHub API and Actions in `NFR-13`/`NFR-16` |
| `GC-06` | `P1` items satisfy Bootstrap Story DoR v0.1, remaining items not at Blocker | **Met with a named gap** | 12 of 13 ready; `FR-12` now **partially verified** by the bootstrap trial, argued non-blocker. `FR-21` added since the draft and satisfies all ten criteria; `FR-22` is `P2` and out of DoR scope |
| `GC-07` | Material requirement conflicts resolved or formally accepted | **Met** | Four accepted in the catalogue; `CONFLICT-FWK-019` at `CANONICAL_RESOLVED` |

**Seven criteria, seven assessed.** The verdict is not among them.

## Disposition — two planes, then the rendered verdict

```text
baseline_disposition: APPROVED
criteria_passed: 7      criteria_total: 7

obligation_posture: OPEN_NON_BLOCKING
open_conditions:    C-3 (blocks stage 6), C-4 (blocks stage 5)
control_status:     both fully fielded in CONDITION_REGISTER.md
```

| Dimension | Value |
|---|---|
| Evidence readiness | `PASS — 7/7 criteria` |
| Objective aggregate | `7/7 objectives PASS` |
| Baseline disposition | `APPROVED` |
| Obligation posture | `OPEN_NON_BLOCKING — C-3, C-4` |
| **Rendered verdict** | **`APPROVED_WITH_CONDITIONS`** (recommended) |

`APPROVED` alone renders only when the posture is `CLEAR`. It is not.
`HELD_FOR_CONDITION_CLOSURE` renders only if a condition's `blocking_scope`
covered stage 3 — neither does. `DECISION_INCOMPLETE` renders only if a condition
were uncontrolled — both are fully fielded. **The matrix leaves exactly one
outcome available**, which is the point of having one.

## Transition guard for stage 3

Each conjunct with the value used:

```text
StageN_verdict ∈ {APPROVED, APPROVED_WITH_CONDITIONS}   -> pending this decision
ballot_quorum_met_or_not_required                        -> not required (NOT_ACTIVE)
every_required_objective_passed                          -> yes, 7/7
no_open_condition.blocking_scope covers Stage 3          -> yes: C-3→stage 6, C-4→stage 5
no_required_condition.is_overdue                         -> yes: due stages 6 and 5, neither entered
=> Stage 3 = OPEN on issue of a passing verdict
```

Stage 3 does not open because this document says so. It opens because four
conjuncts hold and the fifth is this decision.

## Carried conditions

Cited, not restated — `CONDITION_REGISTER.md` is authoritative.

| ID | Blocking scope | Status |
|---|---|---|
| `C-3` | Stage 6 | `OPEN` — one of three instruments in force |
| `C-4` | Stage 5 | `OPEN` — no progress; closure requires a `G4` act |

This decision creates **no new condition**. The two findings below are the same
ones the earlier draft raised; both already have owners through `D-1` and `D-3`
recorded there, and neither is promoted to a register condition because neither
blocks a stage.

## Findings carried, unchanged

1. **`FR-17`'s acceptance method is descriptive, not executable.** Nothing checks
   that 30 clean merges precede tier `A2` (`TX-02`). `K-09`'s bound has since
   crossed below 10% at n=33, which makes the unchecked precondition *closer to
   mattering*, not less relevant.
2. **`GC-03` is vacuously satisfied.** No business rules exist to document, so the
   criterion cannot fail. Defensible, and not evidence of work.

## To issue this verdict

State the verdict and the date — in session or on issue #60. The executor then
fills this record, applies the transition guard, and opens stage 3 with the entry
map already recorded here.
