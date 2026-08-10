# PRD — SecB Engineer Loop v1.5

Version: **1.1.0 — baselined** 2026-08-10
Status: Stage 1 **passed** (second pass). Gate `PRD_BASELINED` rendered
`APPROVED_WITH_CONDITIONS` on 2026-08-10 — baseline disposition `APPROVED` on
7/7 criteria, obligation posture `OPEN_NON_BLOCKING` for `C-3` and `C-4`
(`STAGE_GATE_PRD_BASELINED_V1_1.md`; conditions tracked in
`CONDITION_REGISTER.md`). Stage 2 is `AUTHORIZED_FOR_COMPOSITE_VERDICT`; stage 3
is `PENDING_STAGE_2_PASS`.
Work Package: `SECB-WP-FWK-008` (issue #12); baseline preparation `SECB-WP-FWK-014` (issue #24)
Template: `docs/16-templates/PRODUCT_DEFINITION_TEMPLATE.md` (`SECB-WP-FWK-007`)
Product selection authority: operator decision, session 2026-08-10
Grounding sources: `docs/06-agent-orchestration/ENGINEER_LOOP.md` v1.5.0,
`docs/11-operations/PERFORMANCE_INDICATORS.md`, loop records FWK-002…007

## Change control

| Item | Value |
|---|---|
| Baseline status | **Baselined at v1.1.0**, 2026-08-10 |
| Change authority | Operator, as Product Sponsor |
| Change process | After baseline, any change to scope, success metrics or acceptance criteria requires a new version and re-passing stage 1 (`DELIVERY_LIFECYCLE.md` §4) |
| Approval record | `STAGE_GATE_PRD_BASELINED_V1_1.md` — `APPROVED_WITH_CONDITIONS` · prior: `STAGE_GATE_PRD_BASELINED.md` (v1.0.0, superseded) |
| Re-baseline trigger | Any change to scope, success metrics or acceptance criteria, or a change to assumption A-02 |
| Stage-1 companions | `STAKEHOLDER_REGISTER.md` · `RAID_REGISTER.md` · `KPI_BASELINE.md` |

## 1. Product Identity

- **Product Name:** SecB Engineer Loop
- **Product Type:** Internal System / AI Agent (governed autonomous engineering execution)
- **Product Stage:** MVP — specification `IMPLEMENTATION_READY` (v1.5.0); the skill-router MVP is sandbox-tested and `HELD_AT_INDEPENDENT_REVIEW_GATE`
- **Product Owner:** Operator (vily); governance owner TBD per `AGENTS.md` §13
- **Target Market:** Internal — BizEra engineering. **Primary use confirmed 2026-08-10: SecB is the precursor framework from which BST builds subsequent projects**; each new project instantiates it rather than reinventing governance. Reusable by any organization running AI agents under governance.

## 2. Product Overview

> **SecB Engineer Loop** is a **governed autonomous engineering execution
> system** for **operators who delegate software work to AI agents**,
> which lets them **turn authorized demand into tested, traceable,
> reversible software** — solving **the ungoverned-agent problem: fast
> AI-generated changes with no authority, no budget, and no audit
> trail** — through **a ticketed loop whose control gates run
> mechanically in CI and whose every step leaves verifiable evidence**.

## 3. Problem Statement

- **Current problem:** AI coding agents produce changes faster than any
  human process can audit; without mechanical controls their output is
  unbounded in scope, unattributable in authority, and unverifiable
  after the fact.
- **Who is affected:** the operator who must answer for every merged
  change; reviewers who cannot reconstruct why a change exists;
  downstream users of the software.
- **Current-process limits:** prose rules alone do not stop anything —
  this repo itself demonstrated the gap (ten gates existed as prose,
  zero could fail; two status authorities contradicted each other).
- **Business impact:** unaudited agent changes carry rework cost,
  compliance risk, and — in financial or customer-facing domains —
  direct monetary exposure.
- **Why now:** agent capability is compounding; the governance layer
  must exist *before* mutating and external-effect autonomy is granted,
  not retrofitted after an incident.

## 4. Target Users

| User Segment | Role | Primary need | Current pain point |
| --- | --- | --- | --- |
| Primary User | Operator delegating engineering demand | Ship real changes through agents without losing control | Must hand-audit every agent diff, or trust blindly |
| Secondary User | Reviewer / approver (human or independent agent) | Verdicts grounded in evidence, not agent self-reports | Agent claims lack reproducible proof |
| Administrator | Framework maintainer | Gates, budgets, and registries that are enforceable and testable | Prose policy drifts silently from reality |
| Stakeholder | Business owner / partner | Traceability from requirement to release | No chain linking demand to deployed change |

## 5. Value Proposition

- Reduce working time: demand→merge in minutes-scale loops (observed FWK-003…007)
- Reduce errors: fail-closed gates catch missing authority, missing budget, and over-budget diffs before review
- Increase transparency: every WP leaves ticket + gate results + evidence on the record
- Improve decisions: reviewers read CI verdicts and evidence, not assertions
- Elevate experience: the operator approves at exactly two points (plan, merge) instead of policing every step
- Support scale: the same loop governs one agent today and a routed multi-skill fleet under v1.5

## 6. Product Vision

> Build a **fully closed self-improving engineering loop** that enables
> **operators and their AI agent teams** to **convert authorized demand
> into deployed, evidenced software and validated organizational
> knowledge** in a way that is **fail-closed, auditable end-to-end, and
> scalable from one repo to an enterprise**.

## 7. Product Objectives

1. Make every control gate of `CONTROL_GATES.md` mechanically fail-able (3 of 10 executable today: Authority, Test, Budget)
2. Certify the skill router `IMPLEMENTATION_READY → SANDBOX_TESTED` via independent review of the held MVP evidence
3. Keep 100% of merged PRs green on all executable gates
4. Maintain unbroken traceability: Requirement → WP → Change → Test → Evidence → Approval → Release
5. Run the Learn Loop each cycle round; grow the knowledge register only through the §17 promotion path
6. Reach a separately-authorized R0 read-only routing pilot before any mutating or external-effect autonomy
7. **Minimise human involvement: drive every non-constitutional decision to autonomous execution, so that humans act on constitutional change and as the trust anchor rather than in the loop of each decision.** Measured by `K-11` autonomy rate; baseline 75% of post-Genesis merges, target ~100% of `D0` and `D1` decisions.

   **`L0` exclusion, binding:** `O7` never authorizes reducing a control to raise the number. The constitution, absolute ceilings, quorum and trust anchor are not delegable (`L0_ROOT_CONSTITUTION.md`), and every `D2`+ decision reaching a human is this objective **satisfied**, not obstructed — the ceiling is a feature. Added by ballot 001, 2026-08-10.

## 8. Product Scope

**In Scope**

- Ticketed intake (work-package form, ten §7 fields enforced)
- Authority, Test, and Budget gates in CI; remaining gates as they earn mechanization
- Engineer Loop execution over this repo's own backlog (dogfooding)
- Evidence records and the knowledge register (Learn Loop)
- Sandbox-only skill-router work toward FIT-101–120 certification

**Out of Scope** *(verbatim from the v1.5 governance posture — all `NOT_AUTHORIZED` / `NOT_IMPLEMENTED`)*

- Runtime `AGENTS.md` adoption of the router policy
- External or mutating routing
- Production autonomy
- Registry and compatibility data; router and orchestrator software beyond the sandbox MVP
- Plugin installation, credential grants, external-effect approval

## 9. Key Product Capabilities

| Capability | Description | Priority |
| --- | --- | --- |
| User Management | Segregation of duties: proposer / executor / reviewer / human approver (`AGENTIC_ENGINEER_TEAM.md`) | Must Have |
| Core Workflow | The §5 eight-step loop, ticket to learning | Must Have |
| Document Management | Governed docs tree with single status authority (FWK-003) | Must Have |
| Approval Workflow | Human merge gate; verdicts as evidence-backed comments | Must Have |
| Dashboard | KPI layers of `PERFORMANCE_INDICATORS.md` | Should Have |
| Integration | GitHub Issues/Actions today; router-mediated tools under v1.5 when authorized | As required |
| Audit Trail | Immutable evidence: run IDs, SHAs, checksums, budget receipts | Must Have |

## 10. Differentiation

- Gates are proven by failure, not asserted (KN-001: every gate tripped on a real PR before being trusted)
- Fail-closed by construction: missing ticket, missing budget, or empty input is a red build, not a warning
- Budget circuit breaker bounds every change mechanically (first WP fully bounded: FWK-005)
- Built-in Learn Loop: the system that ships changes also extracts and quarantines its own lessons
- Governance-first sequencing: autonomy is expanded only through separately authorized, evidence-gated transitions
- The framework governs itself — its own development runs through its own loop (7 WPs to date)

## 11. Success Metrics

| KPI | Baseline (observed, FWK-002…007) | Target | Measurement |
| --- | ---: | ---: | --- |
| Loop lead time (ticket → merge) | minutes-scale, unmeasured formally | p50 < 1 hour | Issue/PR timestamps |
| PRs merged with all gates green | 5/5 (100%) | 100% | Check-run API |
| Unauthorized-action rate | 0 incidents | 0 | Governance review of evidence |
| Evidence completeness (gate results on ticket) | 5/5 WPs | 100% | Issue audit |
| First-pass budget compliance | 4/5 (FWK-007 required amendment) | ≥90% | Budget-gate logs |
| Executable control gates | 3/10 | 10/10 | `ci.yml` vs `CONTROL_GATES.md` |

Per `PERFORMANCE_INDICATORS.md`: each KPI still needs owner, formula,
cadence, and guardrail before it is operational; cost-layer KPIs (tokens,
tool calls) await a runtime harness.

## 12. Definition Statement

> **Product Definition:**
> **SecB Engineer Loop** is an **internal governed AI-agent execution
> system** designed for **operators delegating software engineering to
> autonomous agents**, to solve **the absence of enforceable authority,
> budget, and audit controls over agent-produced changes**, by delivering
> **a ticketed, fail-closed, evidence-producing engineering loop with
> mechanical CI gates and a quarantined learning path**. The product
> creates value through **bounded, auditable, minutes-scale delivery**
> and is considered successful when **every merged change passes all
> executable gates with complete evidence and zero unauthorized
> actions, and the gate set reaches 10/10 mechanized**.
