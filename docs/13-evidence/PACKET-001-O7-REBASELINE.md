# Decision Packet 001 — Does autonomy become a PRD objective?

Class: **`D4 CONSTITUTIONAL`** — it changes the product definition, which the PRD's
own change-control block makes a re-baseline trigger
Authority: operator (vily), as Product Sponsor and constitutional authority
Compiled by: Claude · Work Package: `SECB-WP-FWK-027` (issue #50)
**Status: `DECIDED` — `APPROVE_OPTION_A`**, by the operator, 2026-08-10.
Enacted under `SECB-WP-FWK-029` (issue #54). The ballot was answered by the
authority; the compiler recorded it and did not supply it.
Template: `docs/16-templates/DECISION_PACKET_TEMPLATE.md`

## 1. Decision required

Whether *"autonomous governance in every dimension, minimising human
involvement"* becomes PRD objective **`O7`** with a measurable autonomy KPI, or
stays outside the document that defines the product.

## 2. Why now

The operator stated this purpose on 2026-08-10 and it is already steering
decisions — the autonomy-ceiling analysis, the identity research and the HDG-EAB
adoption were all undertaken because of it. A purpose that steers work while
living outside the PRD steers it invisibly.

It is also newly **measurable**: autonomy rate is 77% of post-Genesis merges
(10 of 13), computed from git history.

## 3. What happens if no decision is made

Per the fail-safe defaults, no amendment: the PRD keeps six objectives.
Concretely —

- The purpose exists only in conversation and **is lost when this session ends.**
  The next agent reads a PRD in which minimising human involvement is not a goal,
  and will not weigh decisions against it.
- Autonomy rate stays a number in an analysis document rather than a tracked KPI
  with a target, so regressions are invisible.
- Packet 002 (stage-2 verdict) stays coupled and blocked — see that packet's §5.

## 4. Non-negotiable constraints

- `L0` absolute ceilings are untouchable; adding an objective must not imply
  authority to widen them.
- The `L0` floor stands: constitution, quorum, ceilings and trust anchor are not
  delegable, so `O7` can never mean *zero* humans.
- Re-baselining requires re-passing stage 1 — that is the mechanism, not a cost
  to be avoided.

## 5. Options and project-impact matrix

| Dimension | **A — full re-baseline** | **B — record in an ADR only** | **C — no change** |
|---|---|---|---|
| What happens | PRD → v1.1.0 with `O7` + autonomy KPI; re-pass stage 1; one stage-2 verdict then covers 7 objectives | An ADR records the purpose; PRD untouched | Purpose stays in conversation |
| Business value | Purpose becomes steerable and auditable; new projects inherit it | Partial — durable, but not where requirements trace from | None |
| Scope | +1 objective, ~2 new requirements, ~5 re-mapped | +1 decision record | — |
| Schedule | 1 PR + 2 gate records (stage 1 re-pass, then stage 2) | 1 small PR | 0 |
| Cost | Moderate — mostly re-mapping existing requirements (`FR-05` `FR-10` `FR-11` `FR-17` `FR-18` already are autonomy-governance requirements mapped to `O1`) | Low | 0 |
| Customer impact | None — nothing deployed | None | None |
| Reliability | Unaffected | Unaffected | Unaffected |
| Security / privacy | Unaffected. `O7` does **not** authorize widening authority | Unaffected | Unaffected |
| Data | None | None | None |
| Maintainability | Improves — the RTM gains the objective its autonomy requirements answer to | Neutral — requirements still answer to `O1`, which is a poorer fit | Degrades slowly: purpose and document diverge |
| Strategic fit | High — this is the framework's stated reason to exist | Medium | Low |
| Dependencies | Blocks Packet 002 until decided | None | None |
| Reversibility | High — revert the merge; stage-1 verdict returns to v1.0.0 | High | n/a |
| Evidence confidence | **`E2`** — autonomy rate reproducible from git; the objective's *value* is a judgement, not a measurement | `E2` | n/a |
| **Eligibility** | Eligible | Eligible | Eligible |

No option is `INELIGIBLE`. `DEFER` is viable but inherits option C's cost while
the session's context is still available, which is when this is cheapest to do.

## 6. Agent recommendation

**Option A.** Two reasons, and the second is the stronger one:

1. The objective is measurable now, so it can carry a target and be tracked.
2. Requirements trace to objectives. Five requirements already exist that are
   *about* autonomy governance and are currently mapped to `O1` (mechanise the
   gates) because there was nowhere better. That mapping is a small lie the RTM
   has been carrying; `O7` fixes it rather than adding to it.

## 7. Agent ballot result and dissent

**No agent ballot exists.** `ballot_layer.state = NOT_ACTIVE` — five independent
identities do not exist, and one session emitting five role-labelled votes would
be self-approval in five hats. The Agent Decision Council is HDG-EAB Tier 2 and
requires the identity decision first.

Recorded rather than omitted, because an absent quorum is information: **this
recommendation carries no independent technical attestation.** Its author is also
its compiler, which HDG-EAB §6 separates and this deployment cannot.

## 8. Evidence-confidence summary

| Claim | Level | Basis |
|---|---|---|
| Autonomy rate is 77% post-Genesis | `E2` | Reproducible: `git log` + the recorded verdicts |
| Five requirements are mis-mapped to `O1` | `E1` | Documentation inspection of `REQUIREMENT_CATALOGUE.md` |
| Adding `O7` will improve autonomy | **`E0`** | Assertion. No evidence exists that naming an objective changes an outcome |

The third row is the honest weakness of option A: it improves *traceability and
durability*, which are verifiable, and its effect on actual autonomy is unproven.

## 9. Worst credible consequence

`O7` is read by a future agent as authorization to reduce human involvement
*generally*, rather than within `L0`'s floor — leading it to propose narrowing a
gate to raise the autonomy number. Mitigated by stating in the objective itself
that `L0` acts are excluded, and by Goodhart-guarding the KPI: **autonomy rate is
reported only alongside the count of escalations that were correctly escalated.**

## 10. Rollback and stop conditions

Revert the merge; PRD returns to v1.0.0 and the stage-1 verdict to its current
record. Stop condition: if the re-baseline would require changing an `L0` ceiling
to accommodate `O7`, halt — that is a `C4` change and out of scope.

## 11. Residual risks being accepted

- The KPI can be gamed by classifying decisions as `D1` that should be `D2`.
  Guard: the trigger list is charter-level and unchangeable inside a ballot.
- Re-passing stage 1 produces a second gate record; the first must be marked
  superseded, not deleted.
- No independent attestation of this recommendation (see §7).

## 12. The exact human ballot

> **Do we put the autonomy purpose into the document that defines the product —
> accepting one PR and two gate records of rework now — or keep it outside the
> PRD and accept that it disappears when this session ends?**

- **`APPROVE_OPTION_A` — full re-baseline to v1.1.0 with `O7`** ← **selected**
- `APPROVE_OPTION_B` — ADR only, PRD untouched
- `APPROVE_OPTION_C` — no change
- `APPROVE_WITH_CONDITIONS` — state them
- `RETURN_FOR_MORE_EVIDENCE` — naming which claim
- `DEFER_UNTIL <date or event>`
- `REJECT_ALL_OPTIONS`

> You are approving the project outcome, cost, schedule impact and residual risk.
> You are not certifying the source code. Technical feasibility is covered by the
> attached assurance evidence.
