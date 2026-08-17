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
| `statement` | Put the three adopted measurement instruments into force: ODC `defect_type` + `defect_trigger` and IEEE 1044 `severity` recorded at defect close (`K-08`); the statistical rule-of-three (`3/n`) tally recorded per decision (`K-09`); the OpenTelemetry GenAI attribute names recorded per work package (`K-10`) |
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

Predicate (b) is **partly satisfied, and its evidence was defective.** Every
autonomous-merge announcement since `e76f8b4` carried a tally — *"0 downgrades in
N observations → 95% bound X%"* — sixteen times. But `SECB-WP-FWK-034` found the
denominator had **no definition**: the values were hand-incremented on an unstated
rule and over-stated confidence. With an observation now defined as one governance
verdict on a merged PR head, the reproducible figure is **0 downgrades in 22 → 13.6%**,
not the 8.1% last announced.

So the instrument was **in force in form and unreliable in substance.**

**Predicate (b) is now met** (`SECB-WP-FWK-035`): the series lives in
`docs/13-evidence/K09_LEDGER.md`, append-only, carrying the observation definition,
the reproduction command, and the corrections to the announced values. `C-3` is
therefore **one of three instruments closed** — predicates (a) ODC defect fields and
(c) OTel token attributes remain open, so the condition itself stays `OPEN`.

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

## `C-5` — replace `G-02` with a squash-aware content-and-provenance proof

| Field | Value |
|---|---|
| `condition_id` | `C-5` |
| `origin_decision` | `STAGE_GATE_REQUIREMENTS_READY_ADDENDUM_001.md` — operator's amended stage-2 verdict, 2026-08-13 |
| `statement` | `G-02` (`main == expected tested trunk SHA`) is incompatible with squash-merge and must be replaced by a proof of content **and** provenance |
| `status` | **`PARTIALLY_SATISFIED`** — the historical half is done, the forward half is not |
| `severity` | Major |
| `blocking_scope` | **Does not block a stage.** It blocks the next autonomous canonical merge being *provable*, not any stage transition |
| `owner` | Executor |
| `due_stage` | Before the next autonomous canonical merge |
| `closure_predicate` | `G-02S-HISTORICAL_SQUASH_EQUIVALENCE` grades the Genesis **and** `TR-01` is effective as the forward control, with `M ∧ H ∧ B ∧ T ∧ P ∧ C ∧ R ∧ E` evaluated per merge |
| `required_evidence` | The audit corrections at `f1b2516` (done) · a `TR-01` implementation with its test vectors passing (not done) |
| `closure_authority` | Operator |
| `supersedes / superseded_by` | — |
| `history` | 2026-08-13 created (amended verdict) · 2026-08-14 historical half satisfied at `f1b2516` (`SECB-WP-FWK-060`); forward half tracked as `TR-01`, issue #118 |

**Why `PARTIALLY_SATISFIED` and not `OPEN`.** Two distinguishable obligations sit
inside one condition: grade the Genesis correctly, and govern future merges. The
first is closed by evidence on `main`; the second cannot be until `TR-01` exists.
Recording it as `OPEN` would lose the first; recording it as `CLOSED` would claim
the second. **The register's arithmetic needs a state for a condition that is half
discharged**, and inventing one here is smaller than pretending the halves are one.

---

## `C-6` — prohibit non-fast-forward update of a canonical ref, with preventive enforcement

| Field | Value |
|---|---|
| `condition_id` | `C-6` |
| `origin_decision` | `STAGE_GATE_REQUIREMENTS_READY_ADDENDUM_001.md` — operator's amended stage-2 verdict, 2026-08-13 |
| `statement` | An `L0` amendment prohibits non-fast-forward update, deletion-and-recreation or forced replacement of a canonical branch ref, **and preventive enforcement exists** |
| `status` | **`OPEN`** |
| `severity` | Major |
| `blocking_scope` | Blocks the next autonomous canonical merge. **Does not block stages 3–4** |
| `owner` | Operator (`G4` — amends `L0_ROOT_CONSTITUTION.md`) |
| `due_stage` | Before the next autonomous canonical merge |
| `closure_predicate` | `L0-GIT-004` ratified as a **state invariant** (`new_sha != ZERO ∧ is_ancestor(old,new) ∧ release_certificate.result_sha == new_sha ∧ receipt_chain_valid`) **and** `NEG-01`…`AUD-01` pass against live enforcement with bypass disabled |
| `required_evidence` | The ratified `L0` text · a ruleset requiring PR and status checks, blocking force-push and deletion, with no bypass actors · eight negative-test results |
| `closure_authority` | Operator, as constitutional authority |
| `supersedes / superseded_by` | — |
| `history` | 2026-08-13 created (amended verdict) · drafted at issue #117, status `RATIFIED_NOT_EFFECTIVE` pending live enforcement |

**Ratifying the text does not close this.** `L0` prose alone is a *documentary*
control; the closure predicate requires enforcement that rejects a bad push
server-side. And a change from `403` to `200` on the rulesets endpoint does not
close it either — **configuration is not enforcement.**

---

## `C-7` — separate human/operator identity from the agent's App identity

| Field | Value |
|---|---|
| `condition_id` | `C-7` |
| `origin_decision` | `STAGE_GATE_REQUIREMENTS_READY_ADDENDUM_001.md` — operator's amended stage-2 verdict, 2026-08-13 |
| `statement` | The operator's identity and the agent's identity are distinct principals, with separate credentials and separate key custody |
| `status` | **`OPEN`** |
| `severity` | **Critical** — it is the same unmet precondition behind the inert ballot layer, tiers `A3`/`A4`, and stage 9 |
| `blocking_scope` | Blocks the next autonomous canonical merge **and** stage 9 (`RELEASE_CANDIDATE_VALIDATED`), whose independence requirement one identity cannot satisfy. Does not block stages 3–4 |
| `owner` | Operator |
| `due_stage` | Before the next autonomous canonical merge; **and structurally before stage 9** |
| `closure_predicate` | `HUMAN_GITHUB_CREDENTIAL_PRESENT_IN_AGENT_RUNTIME = false` ∧ App keys held outside the agent domain ∧ role custody separated ∧ short-lived tokens only ∧ the `WP-05` negative tests pass |
| `required_evidence` | The credential-cutover receipts of `WP-05` (issue #115): server-side revocation, destroyed runtime, clean-runtime attestation, broker-issued tokens |
| `closure_authority` | Operator |
| `supersedes / superseded_by` | Subsumes the identity half of `C-3`'s ballot-layer blocker; neither is closed by the other |
| `history` | 2026-08-13 created (amended verdict) · 2026-08-13 measured `FAIL`: the agent runtime holds the owner's GitHub credential (`gh auth status` → `bstBizEra`) |

**This is the highest-severity condition in the register**, and unlike the others it
cannot be discharged by engineering. Recorded as `Critical` because three separate
capabilities wait on it and none of them has an alternative path.

---

## The register nearly lost three conditions, one merge after being cited

`Addendum 001` (`SECB-WP-FWK-060`, merged `f1b2516`) added `C-5`, `C-6` and `C-7` —
**and stated them only in the verdict record.** They were absent from this register
until `SECB-WP-FWK-062`.

That is precisely the defect this register was opened to prevent. Its own opening
paragraph reads: *"Carried conditions previously lived only in the text of the
verdict that created them. A condition mentioned in one record and not the next then
reads as closed — which is closure by silence."*

**The addendum even quoted the rule while breaking it**, writing "cited, not
restated" about `C-3` and `C-4` in the same document that restated three new
conditions with no register entry. Carry-forward is arithmetic —
`Open(t+1) = Open(t) ∪ New − Closed − …` — and `New` has to be written down
somewhere for the arithmetic to have inputs.

Recorded rather than silently fixed, because a register that quietly absorbs the
conditions it nearly lost teaches nobody how it nearly lost them.

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
