# Template — Stage-Gate Decision Record

Derived from `docs/13-evidence/STAGE_GATE_PRD_BASELINED.md`, the first gate
record this framework issued. Carries the twelve evidence-minimum fields of
`DELIVERY_LIFECYCLE.md` §3.

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
| Effective status | `PREPARED_AWAITING_VERDICT` until issued |

## Exit-condition assessment

One row per exit condition from `DELIVERY_LIFECYCLE_STAGES.md` for this stage.
Assess against the **committed** tree and cite the artifact — not the intention.

| # | Condition | State | Evidence |
|--:|---|---|---|
| 1 | | Met / Not met / Met in part | |

## Conditions of approval

| # | Condition | Owner | Due | Status |
|--:|---|---|---|---|

Advancement past a stated milestone with the condition open is a change-control
event (§4), not discretion.

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
