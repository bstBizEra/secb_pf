# Template — Human Decision Packet

Source: HDG-EAB v1.0 · Authority classes: `docs/00-governance/DECISION_AUTHORITY.md`
Use for every `D2` and above. One to two pages; technical detail goes in annexes.

> **Write this for someone who will not read the diff.** If a section can only be
> understood by reading code, it belongs in an annex, not in the packet.

---

## 1. Decision required

One sentence. The choice, not the change.

## 2. Why now

What forces the decision at this moment rather than later.

## 3. What happens if no decision is made

**Never leave this blank.** Per the fail-safe defaults, silence means no
deployment, no governance amendment, no irreversible migration — state what that
concretely costs here.

## 4. Non-negotiable constraints

Policies, ceilings and prohibited actions that bound every option. An option that
violates one is `INELIGIBLE` and must be labelled so in §5 rather than offered.

## 5. Options and project-impact matrix

**Three-Option Requirement:** risk-minimising · balanced · speed/cost-optimising · plus
status-quo or defer where viable. Every option must be technically feasible, meet
non-waivable policy, be evidence-backed, and carry implementation, rollback and
validation plans. **A deliberately weak option is not an option** — if only one
course is viable, say so and explain why the others are `INELIGIBLE`.

| Dimension | A: risk-minimising | B: balanced | C: speed/cost |
|---|---|---|---|
| Business value | | | |
| Scope | | | |
| Schedule | | | |
| Cost (one-time · recurring · uncertainty) | | | |
| Customer impact | | | |
| Reliability (likelihood · blast radius · recovery) | | | |
| Security / privacy | | | |
| Data (migration · integrity · retention · reversibility) | | | |
| Maintainability | | | |
| Strategic fit | | | |
| Dependencies | | | |
| Reversibility (method · window · data-loss risk) | | | |
| Evidence confidence (`E0`–`E4`, with limitations) | | | |
| **Eligibility** | | | |

Raw measurements stay visible. **A summary score must never hide a trade-off, and
no score overrides a policy veto.**

## 6. Agent recommendation

Which option, and the reasoning in one paragraph.

## 7. Agent ballot result and dissent

Votes with conditions, plus **minority opinions carried forward verbatim.** Where
the ballot layer is inactive, state that plainly rather than omitting the section
— an absent quorum is information.

## 8. Evidence-confidence summary

Highest evidence level supporting each option, what is unverified, and what would
raise confidence.

## 9. Worst credible consequence

Not the worst imaginable. The worst that could plausibly happen if the chosen
option goes wrong.

## 10. Rollback and stop conditions

How to undo it, how long that window lasts, and the thresholds that trigger an
automatic stop.

## 11. Residual risks being accepted

Itemised, each with an owner. Approving the packet accepts these.

## 12. The exact human ballot

State the question in business terms — *"do we accept X to avoid Y"* — then:

- `APPROVE_OPTION_A` · `APPROVE_OPTION_B` · `APPROVE_OPTION_C`
- `APPROVE_WITH_CONDITIONS` — conditions stated by the approver
- `RETURN_FOR_MORE_EVIDENCE` — naming which claim is under-evidenced
- `DEFER_UNTIL <date or event>`
- `REJECT_ALL_OPTIONS`
- `ABSTAIN_CONFLICT_OF_INTEREST`

> **You are approving the project outcome, cost, schedule impact and residual
> risk. You are not certifying the source code. Technical feasibility is covered
> by the attached assurance evidence.**

---

## Invalidation

A material change to any option, to the evidence, or to cost, schedule or risk
**invalidates the packet** and requires re-issue. Do not amend a packet in place
after votes or a decision have been recorded — supersede it, and say which packet
it supersedes.
