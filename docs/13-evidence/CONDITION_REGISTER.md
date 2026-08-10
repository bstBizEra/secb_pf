# Condition Register — authoritative

Status: Open register · opened by `SECB-WP-FWK-030` (issue #56)
Authority for the structure: operator, 2026-08-10 · Model adapted from NIST OSCAL
POA&M, which separates assessment results from the risk items, remediation plans,
status and evidence that track them
([NIST OSCAL POA&M](https://pages.nist.gov/OSCAL/learn/concepts/layer/assessment/poam/))

## Why this register is authoritative

Carried conditions previously lived only in the text of the verdict that created
them. A condition mentioned in one record and not the next then reads as closed —
which is closure by silence, and it is how obligations disappear.

**Two rules make that impossible.**

**No implicit closure.** A condition changes state only by an explicit
disposition event carrying an authority, a rationale and evidence. Not being
mentioned is not a state.

**Carry-forward is arithmetic, not judgement:**

```text
Open(t+1) = Open(t) ∪ New − Closed − Superseded − Waived
```

A condition absent from a new verdict remains `OPEN`. Verdict records **cite**
this register; they do not restate it, because two copies of an obligation drift
and then disagree about what is owed.

## Terminology, separated

The word *condition* was carrying two meanings. They are now distinct:

| Term | Meaning | Lives in |
|---|---|---|
| **Gate criterion** (`GC-nn`) | A readiness test a stage must pass to exit | The stage's definition; assessed in its gate record |
| **Carried condition** (`C-n`) | An obligation that survives a passed gate | **This register** |

A gate criterion is an input to a verdict. A carried condition is an output of
one. Conflating them produced the self-referential defect corrected in
`STAGE_GATE_PRD_BASELINED_V1_1.md`.

---

## `C-3` — implement the three adopted KPI instruments

| Field | Value |
|---|---|
| `condition_id` | `C-3` |
| `origin_decision` | `STAGE_GATE_PRD_BASELINED.md` (v1.0.0, superseded); carried to v1.1.0 by the verdict of 2026-08-10 |
| `statement` | Put the three adopted measurement instruments into force: ODC `defect_type` + `defect_trigger` and IEEE 1044 `severity` recorded at defect close (`K-08`); the rule-of-three tally recorded per decision (`K-09`); the OpenTelemetry GenAI attribute names recorded per work package (`K-10`) |
| `status` | **`OPEN` — partially in force** (see below) |
| `severity` | Major |
| `blocking_scope` | Stage 6 (`IMPLEMENTATION_AUTHORIZED`). **Does not block stages 2–5** |
| `owner` | Operator, executed by the agent |
| `due_stage` | Before stage 6 is entered |
| `closure_predicate` | All three hold: (a) at least one defect recorded with all three ODC/IEEE fields; (b) the `K-09` tally present in every decision announcement for a full stage; (c) at least one work package recording `gen_ai.usage.input_tokens`, `output_tokens` and `gen_ai.request.model` |
| `required_evidence` | (a) a defect record; (b) the announcement series; (c) a WP evidence comment carrying the three attributes |
| `closure_authority` | Operator |
| `supersedes / superseded_by` | — |
| `history` | 2026-08-10 created (v1.0.0 verdict) · 2026-08-10 carried forward to v1.1.0 · 2026-08-10 partial state recorded |

### `C-3` is one-third in force, and nobody had recorded it

Predicate (b) is **already satisfied in practice.** Every autonomous-merge
announcement since `e76f8b4` has carried the rule-of-three tally — *"0 downgrades
in N observations → 95% bound X%"* — thirteen times, currently at n=31 and 9.7%.
That instrument is in force.

Predicates (a) and (c) are not: no defect has been recorded with ODC fields, and
no work package has recorded token attributes.

This is exactly what the register exists to surface. Under the old arrangement
`C-3` was a single line of prose in a verdict, so a third of it being live was
invisible — and would have been re-litigated as if nothing had been done.

---

## `C-4` — assign the governance owner

| Field | Value |
|---|---|
| `condition_id` | `C-4` |
| `origin_decision` | `STAGE_GATE_PRD_BASELINED.md` (v1.0.0, superseded); carried to v1.1.0 by the verdict of 2026-08-10 |
| `statement` | Assign the governance owner left open since import (`AGENTS.md` §13, first of eight unchecked placeholders) |
| `status` | **`OPEN`** — no progress |
| `severity` | Major |
| `blocking_scope` | Stage 5 (`SECURITY_DESIGN_APPROVED`), whose gate authority is the Security and Compliance Review Board — a body with no members. **Does not block stages 2–4** |
| `owner` | Operator |
| `due_stage` | Before stage 5 is entered |
| `closure_predicate` | A named party holds the governance-owner role in `STAKEHOLDER_REGISTER.md`, **and** `AGENTS.md` §13's governance-owner placeholder is checked |
| `required_evidence` | The stakeholder-register entry, and the `AGENTS.md` edit — which is `G4` and therefore itself a constitutional act |
| `closure_authority` | Operator, as constitutional authority |
| `supersedes / superseded_by` | — |
| `history` | 2026-08-10 created (v1.0.0 verdict) · 2026-08-10 carried forward to v1.1.0 |

**Note on the closure path.** `C-4` cannot be closed by the agent even in
principle: editing `AGENTS.md` is `G4`, so its evidence requires a constitutional
act. That is recorded here rather than discovered at stage 5.

---

## Why `GC-03`'s improvement does not close either condition

The stage-1 gate criterion on measurable KPIs (`GC-03`) passed with
`strength: IMPROVED` — six measurable KPIs at v1.0.0, eight at v1.1.0, because
`K-06` was computed and `K-11` arrived measured.

**That improvement does not touch either closure predicate.** `C-3` asks for three
instruments to be *in force*; `K-06` and `K-11` are different metrics that were
already computable. `C-4` asks for a named owner; no measurement bears on it.

Per the operator's instruction: a strengthened gate criterion closes a carried
condition only when its evidence matches that condition's closure predicate
directly. Here it does not, so both remain `OPEN`.

## Register invariants

- Every open condition has an owner, a due stage, a closure predicate and a
  closure authority. A condition missing any of these is a **decision defect**,
  not a tracked obligation.
- A condition whose due stage is entered while it is still open is **overdue**,
  which is an escalation, not a delay.
- `blocking_scope` is the only field that stops a stage. A `Major` severity
  condition that blocks nothing does not block anything — severity communicates
  importance, `blocking_scope` communicates authority.
