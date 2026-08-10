# Two-Plane Decision Model

Status: Effective on merge of `SECB-WP-FWK-031` (issue #58)
Authority: operator, 2026-08-10 · First applied in
`STAGE_GATE_PRD_BASELINED_V1_1.md` before being made policy
Amendment: `D4` — this document defines how verdicts are rendered, so changing it
is a constitutional act

## The defect this prevents

One record produced four structural defects at once, and they share a root: a
single status field was asked to carry a decision, its inputs, and its
unfinished business simultaneously.

| Defect | Why it happened |
|---|---|
| The verdict was listed as its own eighth criterion | No separation between *inputs to a decision* and *the decision* |
| *Condition* meant both a readiness test and a carried obligation | One word, two roles |
| One status tried to answer both "is the artifact ready" and "are obligations closed" | Two independent questions, one field |
| Not mentioning a condition read as closing it | No register, so absence looked like resolution |

## Plane A — baseline decision

Answers only: **is the artifact good enough?**

```text
baseline_disposition: APPROVED | CHANGES_REQUIRED | REJECTED
criteria_passed: <n>
criteria_total:  <n>
```

**The verdict is never a criterion.** Criteria are readiness tests defined by the
stage; the verdict is what they produce. A record whose `criteria_total` includes
"formally approved" is self-referential and invalid (`GATE-001`).

A criterion may be recorded with detail beyond pass/fail where its strength is
mistakable for something else:

```text
GC-03:
  result: PASS
  strength: IMPROVED
  measurable_kpi_previous: 6
  measurable_kpi_current:  8
  new_evidence: [K-06, K-11]
```

**A strengthened criterion does not close a carried obligation** unless its
evidence satisfies that obligation's closure predicate directly. Recorded because
this exact inference was available and wrong at the first application.

## Plane B — obligation posture

Answers only: **what remains owed?**

```text
obligation_posture: CLEAR | OPEN_NON_BLOCKING | OPEN_BLOCKING | OPEN_UNCONTROLLED
```

| Value | Meaning |
|---|---|
| `CLEAR` | No open condition applies to this decision's scope |
| `OPEN_NON_BLOCKING` | Conditions open, each fully controlled, none blocking the next stage |
| `OPEN_BLOCKING` | A condition's `blocking_scope` covers the next stage |
| `OPEN_UNCONTROLLED` | A condition lacks an owner, due stage, closure predicate or closure authority — a **decision defect**, not a posture to accept |

Posture is computed from `CONDITION_REGISTER.md`, never from the verdict's prose.

## Rendering matrix

| Plane A | Plane B | Rendered verdict |
|---|---|---|
| `APPROVED` | `CLEAR` | `APPROVED` |
| `APPROVED` | `OPEN_NON_BLOCKING`, fully controlled | `APPROVED_WITH_CONDITIONS` |
| `APPROVED` | `OPEN_BLOCKING` | `HELD_FOR_CONDITION_CLOSURE` |
| `APPROVED` | `OPEN_UNCONTROLLED` | `DECISION_INCOMPLETE` |
| `CHANGES_REQUIRED` | any | `REWORK_REQUIRED` |
| Evidence or authority in conflict | any | `HUMAN_REQUIRED` |

### `SC-04` terminology collision — resolved, operator to confirm

The operator's Plane A names the middle disposition `CHANGES_REQUIRED`; the
installed stage-gate vocabulary already renders that outcome as
`REWORK_REQUIRED`. Under `SPECIFICATION_CONFLICT_PROTOCOL.md` this is
`SC-04 terminology collision`, default action *split the name and define each*.

**Resolution applied:** `CHANGES_REQUIRED` is a **Plane A disposition** — a
property of the artifact. `REWORK_REQUIRED` is the **rendered verdict** it
produces — a property of the decision. Both are kept, each scoped to its layer,
and the matrix maps between them. The alternative — adding `CHANGES_REQUIRED` as
a seventh rendered verdict — would put a synonym into a vocabulary that already
carries three shared tokens across six sets.

Recorded as the executor's resolution of a `C1`-class clarification. The operator
may override it; doing so changes only which word appears in the rendered row.

## Transition guard

A stage does not open because a document says it is open. It opens when a
predicate holds:

```text
Stage(n+1) = OPEN  iff
     StageN_verdict ∈ {APPROVED, APPROVED_WITH_CONDITIONS}
 AND ballot_quorum_met_or_not_required
 AND every_required_objective_passed
 AND no_open_condition.blocking_scope covers Stage(n+1)
 AND no_required_condition.is_overdue
 ELSE BLOCKED
```

**Currently evaluated by hand.** No code computes this, and the record says so
rather than implying automation that does not exist. `ballot_quorum_met` reads as
*not required* while `ballot_layer.state = NOT_ACTIVE`, because a quorum that
cannot convene cannot be a precondition — that substitution is itself a
governance decision and is recorded here rather than assumed.

## Composite verdicts across multiple objectives

Where one verdict covers several objectives — as ballot 002 authorized for stage
2 — the structure is per-objective evaluation with a computed aggregate, **never
an average**:

```text
BALLOT-nnn
├── Objective 1: evaluation + evidence
├── ...
├── Objective k: evaluation + evidence
└── Composite verdict
```

```text
all hard objectives pass + quorum + no blocking objection      -> APPROVED
all hard objectives pass + only controlled obligations remain   -> APPROVED_WITH_CONDITIONS
any hard objective fails                                        -> REWORK_REQUIRED
```

A failing objective **cannot** be offset by passing ones. A composite verdict that
does not show each objective's own evaluation is not composite; it is an average
wearing a structure.

## Validation rules

| ID | Rule | What it prevents | Motivated by a real incident? |
|---|---|---|---|
| `GATE-001` | A verdict must not appear among the gate criteria | Self-referential records | **Yes** — `STAGE_GATE_PRD_BASELINED_V1_1.md`, first draft, "seven of eight … the eighth is this decision" |
| `GATE-002` | `APPROVED` requires zero applicable open obligations | A clean verdict hiding owed work | **Yes** — plain `APPROVED` was available at v1.1.0 with `C-3`/`C-4` open |
| `GATE-003` | `APPROVED_WITH_CONDITIONS` must name the condition IDs | Conditions that exist only as a phrase | No incident yet |
| `GATE-004` | Every carried condition needs owner, due stage, required evidence and blocking scope | Obligations nobody can close or check | **Yes** — `C-3`/`C-4` had none of these until the register |
| `GATE-005` | A previously open condition cannot disappear without a disposition event | Closure by silence | **Yes** — `C-3` was one-third satisfied and unrecorded; the register found it |
| `GATE-006` | A stage transition fails while a blocking condition is open | Stages opening on prose | No incident yet |
| `GATE-007` | An overdue condition triggers escalation or stage suspension | Due dates that mean nothing | No incident yet |
| `GATE-008` | Ballot scope, quorum, authority and evidence digest must be valid | Ballots that decide the wrong thing | No incident yet |
| `GATE-009` | Closure requires independent evidence verification | Self-certified closure | **Structurally blocked** — no independent identity exists, so any closure today is self-verified. Recorded as a known gap, not a satisfied rule |
| `GATE-010` | Policy or authority exceptions render `HUMAN_REQUIRED` | Agents waiving controls | No incident yet |

**Five of ten are motivated by defects that actually occurred**, all in the last
few work packages. `GATE-009` is the honest outlier: it cannot be satisfied here
at all, and saying so is better than listing it as if it were in force.

Implementation is `SECB-WP-FWK-032`, argued separately, because *which* rules earn
code should rest on incident evidence rather than on the list being ten items
long. Until then these are review obligations, and this table is what a reviewer
checks a decision record against.

## What this model does not do

- It does not make a decision easier. It makes an incoherent decision harder to
  record.
- It does not close conditions. Only a disposition event in
  `CONDITION_REGISTER.md` does.
- It does not automate the transition guard. A human or an agent evaluates the
  predicate and cites the values used.
