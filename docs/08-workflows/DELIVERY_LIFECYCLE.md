# Delivery Lifecycle — PRD to Production

Status: Adopted on merge of `SECB-WP-FWK-013` (issue #22)
Authority: Operator (vily), structure supplied 2026-08-10
Scope: the delivery lifecycle for every product built on SecB. Steps 1–12 are
the **delivery lifecycle**; steps 1–14 are the **complete production
lifecycle**.

This document **maps onto** the ten gates of
[`CONTROL_GATES.md`](../00-governance/CONTROL_GATES.md) and the tiers of
[`RISK_AUTHORITY_MATRIX.md`](../00-governance/RISK_AUTHORITY_MATRIX.md). It
adds no new gate and no new tier. A step is *where you are*; a gate is *what
must be satisfied to leave*.

## The rule that matters most

> **`BUILT` and `SANDBOX_TESTED` do not mean production-ready.**
> Steps 9, 10 and 11 must each be passed before production is authorized, and
> no step may be skipped or merged into another. Passing a step means its exit
> criteria are evidenced, not asserted.

A slice that compiles, has green tests, and carries a sandbox certification is
at step 8 for that slice. It has not been performance-tested, not
penetration-tested, not accepted by a business user, and has no runbook. Those
are steps 9–11 and they are the difference between working code and a system
someone else depends on.

## Delivery lifecycle (steps 1–12)

| # | Step | Primary output | Exit gate(s) | Tier |
|--:|---|---|---|---|
| 1 | **PRD Review and Baseline** | Approved PRD and acceptance criteria | Gate 1 Authority, Gate 2 Readiness | R0–R1 |
| 2 | **Requirement Decomposition** | Epics, user stories, NFRs, RTM | Gate 2 Readiness | R0–R1 |
| 3 | **Architecture Design** | System architecture, data model, ADRs | Gate 3 Architecture | R1–R2 |
| 4 | **Detailed Solution Design** | API contracts, workflows, UX, RBAC and audit design | Gate 3 Architecture | R1–R2 |
| 5 | **Security and Compliance Design** | Threat model, privacy controls, security requirements | Gate 6 Security *(design-time)* | R2–R3 |
| 6 | **Implementation Planning** | Work packages, estimates, environments, release plan | Gate 1 Authority, Gate 2 Readiness | R1 |
| 7 | **Development** | Working code, migrations, configuration, documentation | Gate 4 Implementation | R1–R2 |
| 8 | **Engineering Verification** | Code review, unit, integration and end-to-end tests | Gate 5 Test | R1–R2 |
| 9 | **Quality and Security Validation** | Performance, resilience, vulnerability and penetration testing | Gate 6 Security *(validation-time)* | R2–R3 |
| 10 | **UAT and Pilot** | Business acceptance, defect closure, pilot evidence | Gate 7 Evidence | R2–R3 |
| 11 | **Production Readiness Review** | Runbooks, monitoring, backup, rollback, operational approval | Gate 8 Release *(readiness)* | R3 |
| 12 | **Production Deployment** | Controlled release, smoke testing, deployment evidence | Gate 8 Release *(authorization)* | **R4 — dual control** |

## Post-production (steps 13–14)

| # | Step | Purpose | Exit gate(s) | Tier |
|--:|---|---|---|---|
| 13 | **Hypercare and Stabilization** | Closely monitor incidents, performance and user adoption | Gate 7 Evidence *(post-deployment verification)* | R3–R4 |
| 14 | **Post-Implementation Review** | Measure KPIs, document lessons, authorize normal operations | Gate 9 Learning, Gate 10 Skill Promotion | R1–R2 |

Step 14 feeds the Learn Loop: lessons enter
[`KNOWLEDGE_REGISTER.md`](../13-evidence/KNOWLEDGE_REGISTER.md) as `Proposed`
and are promoted only through the path in
[`LEARN_LOOP.md`](../06-agent-orchestration/LEARN_LOOP.md).

## Governance state flow

```text
PRD_APPROVED → DESIGN_READY → IMPLEMENTATION_READY → BUILT → TESTED
  → SECURITY_VALIDATED → UAT_ACCEPTED → PRODUCTION_READY → DEPLOYED → STABILIZED
```

| State | Reached by completing | Meaning |
|---|---|---|
| `PRD_APPROVED` | Step 1 | The product definition and acceptance criteria are baselined |
| `DESIGN_READY` | Steps 2–5 | Requirements, architecture, solution and security design are approved |
| `IMPLEMENTATION_READY` | Step 6 | Work packages, environments and the release plan exist and are authorized |
| `BUILT` | Step 7 | Code exists. **Nothing about production is implied.** |
| `TESTED` | Step 8 | Engineering verification passed |
| `SECURITY_VALIDATED` | Step 9 | Performance, resilience and security validation passed |
| `UAT_ACCEPTED` | Step 10 | The business accepted it and pilot defects are closed |
| `PRODUCTION_READY` | Step 11 | Operations can run, monitor, back up and roll it back |
| `DEPLOYED` | Step 12 | Released under dual control with smoke-test evidence |
| `STABILIZED` | Steps 13–14 | Hypercare complete, KPIs measured, normal operations authorized |

Every transition is a claim that must cite the evidence establishing it, per
`AGENTS.md` §10. A declared state without evidence is not a state.

## How this relates to the Engineer Loop

[`ENGINEER_LOOP.md`](../06-agent-orchestration/ENGINEER_LOOP.md) describes the
*binding sequence* for a single unit of authorized demand — request profile,
route, warrants, build, merge, release. This lifecycle describes the *product's
journey*. One product traverses steps 1–14 once per release; the Engineer Loop
runs many times inside steps 6–8, once per work package.

The two must not be conflated. `ENGINEER_LOOP.md` reaching
`FULL_LIFECYCLE_IMPLEMENTATION_READY` is a statement about the *specification*
of the loop, not about any product's position on this map.

## Where SecB stands today (2026-08-10)

Recorded with citations so present position is a fact, not an impression.

| Item | Position | Evidence |
|---|---|---|
| SecB framework itself | **Step 1, in progress** — PRD drafted, not baselined | `PRD-ENGINEER-LOOP.md` (`SECB-WP-FWK-008`, merged `2f26cca`); no approval record yet |
| Requirements decomposition | **Not started** — RTM absent | `docs/INDEX.md` records RTM as pending authorization |
| Skill-router v1.5 specification | Design steps 3–5 documented | `ENGINEER_LOOP.md` v1.5.0 §7 governance posture |
| Skill-router MVP slice | **Step 8 for one sandbox slice** — engineering verification only | `SANDBOX_TESTED` under `REV-SECB-ENGLOOP-MVP-001-20260810` (`SECB-WP-FWK-009`, merged `663984a`) |
| Router v1.5.1 (`src/`) | **Step 7 → 8** — code plus replayed FIT suite | `SECB-WP-FWK-010`, merged `de31bb3` |
| Steps 9–11 for anything | **Not begun.** No performance test, no penetration test, no UAT, no runbook, no rollback drill | `docs/15-runbooks/` is empty; `PERFORMANCE_INDICATORS.md` KPIs lack owners and formulas |
| Production authorization | `NOT_AUTHORIZED` | `ENGINEER_LOOP.md` §7; unchanged by any merge to date |

Consequence, stated plainly: **SecB has no product at `PRODUCTION_READY` and
nothing deployed.** The twelve merged work packages built the governance and
verification machinery that steps 6–8 run on. That is real progress and it is
not the same as being close to production.

## Instantiating this for a new product

Each product built on SecB records its own lifecycle position in a work
package, citing the artifact that establishes each state it claims. The
lifecycle is not copied per product — it is referenced, so a change to the
lifecycle applies everywhere at once.

A machine-readable lifecycle state and a transition validator are deliberately
**not built yet**: no work package has been blocked without them. Build them
when one is (`AGENTS.md` Lean gate — minimum that correctly solves the task).
