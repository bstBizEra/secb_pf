# Template — Stage-Gate Decision Record

Derived from `docs/13-evidence/STAGE_GATE_PRD_BASELINED.md`, the first gate
record this framework issued. Carries the twelve evidence-minimum fields of
`DELIVERY_LIFECYCLE.md` §3 and the two planes of
[`TWO_PLANE_DECISION_MODEL.md`](../00-governance/TWO_PLANE_DECISION_MODEL.md).

> **Ship this with `decision` empty.** The executor prepares and records; the
> gate authority decides. A record that arrives pre-approved is self-approval
> and is worthless as evidence — which is the whole reason the record exists.

---

# Stage-Gate Decision Record — `<GATE_STATUS>`

Prepared by: `<executor>`, `<WP-ID>`
Verdict recorded by: `<executor>`, `<WP-ID>` *(fill when the verdict is issued)*

> **Authorship boundary.** The verdict below was issued by the gate authority,
> not the executor. Provenance: `<quote the authority's instruction verbatim,
> with date>`. Conditions are the executor's recommendation as adopted, not
> independent statements by the authority.

## Evidence minimum (§3)

| Field | Value |
|---|---|
| Project / release identifier | |
| Stage and gate identifier | Stage `<n>`, `<name>` → gate `<GATE_STATUS>` |
| Artifact versions | Every artifact by name **and version**; "latest" is not a version |
| Evidence references | Issues, merge SHAs, CI run IDs — things a third party can open |
| Findings | What is met, what is not. Count them |
| Exceptions | Traceability or control exceptions, with IDs |
| Risk assessment | Which recorded risks bear on *this* gate |
| Conditions and owners | Each with an owner and a milestone |
| Eligible approvers | Who may issue this. If a named body has no members, say so |
| Votes / signatures | Empty until issued |
| Decision timestamp | |
| Effective status | `PREPARED_AWAITING_VERDICT` until issued; afterwards **see the two-plane disposition** — a single field cannot carry a decision, its inputs and its unfinished business at once |

## Disposition — two planes, then the rendered verdict

```text
baseline_disposition: APPROVED | CHANGES_REQUIRED | REJECTED
criteria_passed: <n>    criteria_total: <n>

obligation_posture: CLEAR | OPEN_NON_BLOCKING | OPEN_BLOCKING | OPEN_UNCONTROLLED
open_conditions:    <IDs, from CONDITION_REGISTER.md>
```

| Dimension | Value |
|---|---|
| Evidence readiness | `PASS — n/n criteria` |
| Baseline disposition | |
| Obligation posture | |
| **Rendered verdict** | per the rendering matrix |
| Next stage | `OPEN` or `PENDING_…`, from the **transition guard**, never asserted |

## Gate-criteria assessment (`GC-nn`)

One row per exit criterion from `DELIVERY_LIFECYCLE_STAGES.md` for this stage.
Assess against the **committed** tree and cite the artifact — not the intention.

> **The verdict is not a criterion** (`GATE-001`). Do not add a row for "formally
> approved"; that is Plane A's output, recorded above. A record whose criteria
> count includes its own decision is invalid.

| # | Criterion | State | Evidence |
|--:|---|---|---|
| `GC-01` | | Met / Not met / Met in part | |

## Carried conditions (`C-n`)

**Do not restate the register here.** Cite `CONDITION_REGISTER.md`, which is
authoritative, and list only the IDs in scope with their blocking scope:

| ID | Blocking scope | Status |
|---|---|---|

New conditions created by *this* decision are added to the register with all
thirteen fields (`GATE-004`). A condition open at a previous gate and not
mentioned here **remains open** — absence is not a disposition (`GATE-005`).
Advancement past a due stage with the condition open is a change-control event
(§4), not discretion.

## Available verdicts (§2)

`APPROVED` · `APPROVED_WITH_CONDITIONS` · `REWORK_REQUIRED` · `BLOCKED` ·
`REJECTED` · `HUMAN_REQUIRED`

State which verdicts the evidence makes **unavailable**, and why. A record that
lists only the recommended verdict hides the judgement.

## Effect of this verdict

What advances, what opens, which exceptions clear or narrow, and the
re-baseline trigger.

## Revalidation

What invalidates this verdict — the assumptions it rests on, and the §4 material
changes that would send the project back to the earliest affected stage.
