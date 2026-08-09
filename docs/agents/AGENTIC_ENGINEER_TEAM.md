# Agentic Engineer Team — Accountability Model

Status: Draft
Work Package: `SECB-WP-FWK-001`

| Agent / Role | Primary accountability |
|---|---|
| Orchestrator | Workflow state, delegation, dependency coordination, budgets, and circuit breakers |
| Product / Requirements Agent | Convert authorized demand into build-ready requirements and acceptance criteria |
| Architect Agent | Architecture, interfaces, constraints, and ADRs |
| Engineer Agent | Implementation, refactoring, and technical documentation |
| Test Agent | Test strategy, automation, regression, and quality evidence |
| Security Agent | Threat analysis, security controls, scanning, and security gates |
| Reviewer Agent | Independent review of quality, correctness, risk, and evidence |
| Release Agent | Environment controls, release execution, verification, and rollback |
| Learning Agent | Engineering episode analysis and lesson extraction |
| Knowledge Curator | Validation, deduplication, conflict management, freshness, and provenance |
| Skill Engineer | Skill design, implementation, evaluation, versioning, and lifecycle management |
| Governance Agent | Authority, policy, segregation of duties, control gates, and evidence completeness |
| Human Approver | High-impact decisions, exceptions, knowledge promotion, and production authorization |

## Segregation of Duties

- An implementer must not independently approve a high-risk change.
- A skill author must not independently activate a high-impact skill.
- Governance checks must remain independent from delivery incentives.
- Production authorization remains with a verified human authority unless an approved policy explicitly delegates a bounded class of releases.

## Handoff Contract

Each handoff must state the work-package ID, current state, completed outputs, verification evidence, unresolved risks, required next authority, budget consumption, and rollback path.

