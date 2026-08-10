# Decision Authority — HDG-EAB Tier 1

Status: Adopted on merge of `SECB-WP-FWK-026` (issue #48)
Source: operator-supplied HDG-EAB v1.0, 2026-08-10 · Fit assessment:
`docs/17-references/FIT-HDG-EAB.md`
Amendment: `D4` under its own table; an agent may propose, never approve

## The principle this encodes

> **Agents prove what is technically viable. Humans choose which business
> consequence is acceptable. Policies prevent either side from authorizing what
> is outside its competence or authority.**

Concretely: do not ask a human to approve a migration algorithm. Ask whether a
three-day delay is worth removing an outage risk. NIST expects exactly this
differentiation — *"policies and procedures are in place to define and
differentiate roles and responsibilities for human-AI configurations"* — with
impact-based classification so intensive human review concentrates where the
stakes are ([NIST AI RMF](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/)).

## Why this was needed here

Measured before adoption: **12 operator merges, 0 decision packets.** Every
escalation asked for approval of an artifact or a gate verdict. None offered
options, none stated the cost of not deciding, none named the business
consequence. The human gate appeared to work because the human kept agreeing —
which is not evidence that the right question was asked.

## Decision classes

| Class | Typical decision | Technical assurance | Final authority | Maps to |
|---|---|---|---|---|
| `D0 ROUTINE` | Formatting, documentation, tested internal refactor | Automated checks | **Agent** | `G0` · `R0`–`R1` |
| `D1 CONTROLLED` | Reversible implementation inside approved architecture | Agent ballot + evidence verifier | **Agent under existing policy** | `G0`–`G1` · `R1` |
| `D2 MATERIAL` | Material scope, cost, release date, UX or SLO impact | Agent ballot + technical attestation | **Product / business owner** | `G1`–`G2` · `R2` |
| `D3 HIGH_RISK` | Production migration, sensitive data, security boundary, external commitment | Independent technical assessment (`E3`+) | **Business owner + risk owner** | `G2` · `R3` |
| `D4 CONSTITUTIONAL` | Governance policy, classifier, approval gate, CI protection, authority model | Simulation, adversarial review, independent attestation | **Constitutional authority** | `G4` · `R4` |

The `G` column is the authority-delta classifier's verdict; the `R` column is the
risk tier. **The three axes answer different questions** — `D` asks *who decides*,
`G` asks *who may land it*, `R` asks *how much damage it can do* — and a change
takes the strictest of the three.

### The authority collapse, recorded rather than implied

`D2` names a product owner and `D3` adds a risk owner. In this deployment **both,
and the constitutional authority, are the same identity** — the operator — under
`SINGLE_IDENTITY_SOD_ACCEPTED_RISK.md`, accepted for stages 1–8 only.

So `D2` and `D3` are **nominally distinct and actually identical here.** The table
above is a target shape, not a control in force. Reading the class distinction as
separation of duties would be the same error as reading a role banner as
authorization. It becomes a real control when a second authority exists.

## Mandatory human-decision triggers

A decision is **at least `D2`** when it:

1. Exceeds the approved budget-materiality threshold
2. Changes committed scope or delivery date
3. Changes customer-visible behaviour
4. Consumes material SLO or error budget
5. Introduces vendor lock-in or long-term operating cost
6. Requires irreversible or difficult-to-reverse data migration
7. Accepts a known security, privacy or compliance risk
8. Changes production access, release authority or governance controls
9. Creates an external legal, financial or stakeholder commitment

**These are project-charter thresholds. An agent may not modify them inside an
individual ballot** — doing so would be self-classification, which is the
`D4`-reserved act of changing the authority model.

### SecB's thresholds, set once

| Trigger | SecB threshold |
|---|---|
| Budget materiality | Any change exceeding the envelope's `max_changed_lines` **or** requiring a budget renegotiation on the ticket |
| Committed scope or date | Any change to a PRD objective, or to a stage-gate exit condition |
| Customer-visible behaviour | Not yet applicable — no deployed surface (`WPS` 12.38, no UI, no API) |
| SLO / error budget | Not yet applicable — no SLOs defined |
| Lock-in or operating cost | Any new third-party dependency, any paid plan requirement |
| Irreversible migration | Any change to the sealed evidence package; any history rewrite |
| Accepted risk | Any new accepted-risk record, or any change to an existing one |
| Production access, release or governance authority | Any change under `docs/00-governance/`, `scripts/`, `.github/`, or the envelope |
| External commitment | Any repository made public; any published artifact |

Three triggers are marked not-yet-applicable **with the reason**, so their
absence is distinguishable from oversight and they activate automatically when
the condition arises.

## Evidence levels

| Level | Evidence | Permitted use | Anchored in SecB |
|---|---|---|---|
| `E0` | Agent assertion or reasoning only | Drafting only | Any un-cited claim — and by `AGENTS.md` §4 it may not support a material claim |
| `E1` | Documentation, static analysis, traceability check | Low-risk screening | `RTM.md`; the static prohibited-call scan on the router |
| `E2` | Reproducible test, benchmark or validation run | Normal engineering decision | FIT-101–120, 20/20 twice; the 65-test repo suite |
| `E3` | Independent reproduction, security scan, adversarial assessment | Material / high-risk decision | `REV-SECB-ENGLOOP-MVP-001-20260810` — the only `E3` artifact SecB holds; and `TRIAL-FR12-BOOTSTRAP.md`, which reproduced the runbook in a fresh repository |
| `E4` | Canary, pilot or production telemetry with rollback evidence | Production-scale authorization | **None. Nothing is deployed** — which is why stage 12 is unreachable regardless of who approves it |

Required minimum: `D1` needs `E2` · `D2` needs `E2` with attestation · `D3`–`D4`
need `E3` · production authorization needs `E4`.

**The `E4` row is the honest statement of SecB's ceiling.** No amount of ballot
machinery substitutes for evidence that does not exist.

## Fail-safe defaults on no response

Silence is never consent. If a decision is not made:

| Domain | Default |
|---|---|
| Production deployment | **No deployment** |
| Governance amendment | **No amendment** — the existing policy stays effective |
| Irreversible migration | **No migration** |
| Everything else | The existing approved state remains in force |

A packet that expires without a decision goes to `EXPIRED`, not to its
recommended option.

## What an agent may do without a human

`D0` and `D1`, when the classifier returns `AUTO_APPROVED`, dual policy passes,
every gate is green and the envelope is unexpired — and every such merge is
announced. That is the current 77% of post-Genesis merges.

Everything at `D2` and above reaches a human **by design.** Independent agent
identities would make `D1`'s ballot satisfiable and supply `E3` evidence; they
would not move `D2`+ authority, because that authority is about business
consequence rather than technical correctness.
