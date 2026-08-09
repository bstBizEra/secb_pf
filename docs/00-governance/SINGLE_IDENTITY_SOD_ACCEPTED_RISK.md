# Accepted Risk — Single-Identity Segregation of Duties

Status: Accepted, stages 1–8 only
Risk IDs: `R-04`, `R-05` (`docs/01-requirements/RAID_REGISTER.md`)
Accepted by: Operator (vily), as constitutional authority and Product Sponsor,
2026-08-10, in the instruction recorded in `STAGE_GATE_PRD_BASELINED.md`
Work Package: `SECB-WP-FWK-016` (issue #28)
Review date: **2026-11-08** — the same date the delegation envelope expires
Basis: `docs/17-references/RESEARCH-STAGE1-GATE-INSTRUMENTS.md`, §C-4

## The risk being accepted

`DELIVERY_LIFECYCLE_STAGES.md` names an Architecture Review Board, a Security
and Compliance Review Board, a Change Advisory Board, a Business Acceptance
Committee and a Product Steering Committee. **None has members.** In this
deployment all of them collapse onto one identity — the operator — who is also
Product Sponsor, Product Owner, and the constitutional authority that ratified
the agent's delegation.

Read strictly, stages 3, 5, 9, 10 and 11 cannot pass, because each requires an
approval by a body distinct from the one proposing.

This record accepts that collapse for **stages 1–8**, deliberately and with
compensating controls, rather than leaving it as an implied equivalence to be
discovered at a gate.

## Why acceptance is a legitimate treatment

Recognized practice does not waive infeasible segregation; it requires
**documented compensating controls, independent review, increased oversight,
and records that name preparer and reviewer separately.** ISACA's SoD control
matrix is explicitly a guideline identifying which duties must not combine
**and which require compensating controls** rather than prohibition. Sources are
cited in the research record.

The unacceptable pattern is not "one person holds two roles" — it is "one
person holds two roles and nothing is written down."

## Compensating controls in force

These are not proposed; each is running today and each is verifiable in CI
history or the repository.

| # | Control | Evidence it is real |
|--:|---|---|
| 1 | Non-discretionary mechanical gates: Authority, Test, Budget | Each has been **proven to fail** on a real pull request — runs `31320436859` (authority), `31325014002` (budget) |
| 2 | An authority that cannot expand itself | Every governance and enforcement path classifies `G4`; the Genesis PR's own verdict was `CONSTITUTIONAL_REQUIRED` |
| 3 | A policy that cannot ratify itself | `scripts/check_dual_policy.py` — base and head logic must agree; divergence escalates |
| 4 | Preparer and reviewer recorded separately | `STAGE_GATE_PRD_BASELINED.md` shipped with `decision` empty and names recorder and authority distinctly |
| 5 | Prohibited actions refused, not weighed | `L0_ROOT_CONSTITUTION.md` `G5` — audit removal, evidence destruction and verifier bypass exit `3` |
| 6 | Every autonomous merge announced | Mandatory notification with verdict, gates, SHA and issue; silence is a policy violation |
| 7 | Independent review performed where identity permitted | `REV-SECB-ENGLOOP-MVP-001-20260810` — reviewed by a party that authored none of the artifacts |

Control 7 is the exception that proves the rule: independence was available for
the MVP certification because a different agent wrote the artifacts. Where it is
available, it is used.

## The limit of this acceptance — stage 9

**Not accepted, and not acceptable.** Stage 9's exit condition requires that
**QA and Security independently approve** the release candidate. Independence is
the substance of that gate, not its wording, and no compensating control
manufactures it from a single identity — the same reason `ballot_layer.state`
is `NOT_ACTIVE` in the delegation envelope.

Consequently:

- Stages 1–8 proceed under this accepted risk.
- **Stage 9 is blocked** until a second identity exists — an external reviewer,
  or a provisioned distinct agent identity (deferred capability `D3`).
- Since stages 10–12 are downstream of stage 9, **nothing reaches production**
  under this acceptance. That is the intended consequence, not an oversight.

## Conditions of acceptance

| # | Condition | Owner | Due |
|--:|---|---|---|
| 1 | Every stage-gate record from 3 onward names this collapse and cites this record | Executor | Each gate record |
| 2 | Governance owner assigned (`AGENTS.md` §13) — condition C-4 of stage 1 | Operator | Before stage 5 |
| 3 | A second identity provisioned, or an external reviewer engaged | Operator | Before stage 9 |
| 4 | This acceptance reviewed with the envelope | Operator | 2026-11-08 |

## Revocation

This acceptance lapses on its review date rather than persisting unexamined. It
may be withdrawn at any time by the constitutional authority, in session or by
comment on issue #28, effective immediately. On lapse or withdrawal, stages 3
onward require a distinct approving body.
