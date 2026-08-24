# SecB Agent Operating Contract

Status: Framework documented; three control gates executable (`SECB-WP-FWK-002`, `SECB-WP-FWK-004`); implementation started (`SECB-WP-FWK-010`)
Owner: TBD
Approvers: Authorized project representative under `SECB-WP-FWK-001`
Version: 0.4.0
Last reviewed: 2026-08-10

> This header is the single source of truth for project status
> (`SECB-WP-FWK-003`). Other documents, including `docs/INDEX.md`, describe
> the state of their own domain and defer to this header for the state of
> the project. Evidence for the current status: CI runs Gate 5 (Test),
> Gate 1 (Authority), and the budget circuit breaker on every pull
> request; `src/secb_router/` holds router v1.5.1 (the F1 fix on the
> sealed baseline); the skill-router MVP package is `SANDBOX_TESTED`
> under review `REV-SECB-ENGLOOP-MVP-001-20260810` (`SECB-WP-FWK-009`);
> runtime adoption, external/mutating routing and production autonomy
> remain `NOT_AUTHORIZED`.

## 1. Purpose

Define the mandatory operating rules for every human, AI agent, sub-agent, tool, and automation working in the SecB project.

## 2. Scope

Applies to requirements, architecture, coding, testing, security, deployment, operations, evidence, and knowledge capture across SecB.

## 3. Instruction Precedence

1. Applicable law and approved organizational policy
2. SecB authority, risk, and state-machine controls
3. Approved project decisions and architecture decision records
4. This `AGENTS.md`
5. Task-specific instructions and implementation notes

Conflicts must stop execution and be escalated to the designated human authority.

## 4. Core Control Rules

- No Ticket, No Work.
- No verified authority, no state-changing action.
- Fail closed when identity, authorization, scope, evidence, or policy is uncertain.
- Preserve existing user work and unrelated changes.
- Never expose credentials, secrets, personal data, or protected evidence.
- Use least privilege and the smallest reversible change.
- Separate proposer, implementer, reviewer, approver, and deployer where required by segregation-of-duties policy.
- Every material claim must link to reproducible evidence.

## 5. Mandatory Agent Loop

1. Intake: identify ticket, objective, owner, authority, constraints, and acceptance criteria.
2. Ground: inspect relevant code, documents, decisions, risks, and current state.
3. Plan: define bounded tasks, dependencies, verification, budget, and stop conditions.
4. Execute: make the smallest authorized change.
5. Verify: run applicable tests, reviews, security checks, and policy gates.
6. Evidence: record commands, outputs, artifacts, checksums, decisions, and traceability.
7. Handoff: report outcome, residual risk, rollback path, and required approval.
8. Learn: capture reusable knowledge or propose a validated skill update.

## 6. Required Stop Conditions

Stop and escalate when any of the following occurs:

- Missing, expired, ambiguous, or conflicting authority
- Scope expansion beyond the approved work package
- Security or privacy risk above the approved threshold
- Budget, token, time, retry, or tool-call cap reached
- Destructive or irreversible action not explicitly approved
- Test, quality, evidence, or governance gate failure
- Production access or deployment without an approved release decision

## 7. Work Package Minimum Fields

- Ticket / Work Package ID
- Objective and business value
- Scope and exclusions
- Owner, executor, reviewer, and approver
- Dependencies and risks
- Acceptance criteria
- Test and evidence plan
- Budget and circuit-breaker limits
- Rollback or recovery plan
- Target state transition

## 8. Agent Definition Minimum Fields

Each agent definition in `docs/agents/definitions/` must declare:

- Agent ID, name, purpose, and owner
- Permitted inputs, outputs, tools, and data classifications
- Authority boundaries and prohibited actions
- Epistemic boundary: the question classes this agent's inputs cannot answer, each with the
  evidence that is missing and the source that would supply it. Distinct from the bullet
  above: that one states what the agent may not DO, this one states what it cannot KNOW. An
  agent that has one must disclose it in any output a reader could otherwise take as
  covering the excluded class.
- Required skills and routing rules
- Budget, timeout, retry, and concurrency limits
- Escalation and human-in-the-loop checkpoints
- Verification, evidence, logging, and retention requirements
- Failure modes, recovery, and handoff contract

## 9. Skill Definition Minimum Fields

Each skill in `docs/skills/` must declare:

- Skill ID, purpose, trigger, and owner
- Inputs, outputs, prerequisites, and dependencies
- Procedure and decision points
- Allowed tools and permission boundaries
- Validation tests and success criteria
- Known risks, failure handling, and rollback
- Epistemic boundary: conclusions this skill cannot support from its declared inputs, and
  the input that would be required to support them. `INCONCLUSIVE` reports that a run did
  not conclude; this field states what the skill can never conclude.
- Version, provenance, change history, and approval status

## 10. Evidence and Traceability

All governed work must be traceable:

`Requirement -> Decision -> Work Package -> Change -> Test -> Evidence -> Approval -> Release`

Evidence must be immutable or checksum-verifiable, timestamped, attributable, and linked to the governing ticket.

## 11. Quality Gates

- Definition of Ready satisfied before implementation
- Architecture and security review when triggered
- Automated and manual tests appropriate to risk
- Code review and segregation-of-duties checks
- Evidence completeness and reproducibility review
- Release authorization and rollback readiness
- Post-deployment verification and learning capture

## 12. Repository Map

- `docs/agents/` — agent definitions, prompts, policies, and handoffs
- `docs/skills/` — skill catalog, templates, validation, and tool contracts
- `docs/skills/tools/` — tool registry and access contracts
- `docs/00-governance/` — authority, policy, RACI, stage gates, and ballots
- `docs/02-architecture/` — target architecture and system views
- `docs/05-security/` — threat model, controls, privacy, and security testing
- `docs/12-decisions/` — ADRs and formal decision records
- `docs/13-evidence/` and `/evidence/` — evidence specifications and execution artifacts
- `docs/15-runbooks/` — operational and recovery procedures
- `/src`, `/tests`, `/infra`, `/config`, `/scripts` — implementation assets

## 13. Placeholders to Close

- [ ] Confirm governance owner and approval authority
- [ ] Approve agent role catalog and segregation-of-duties matrix
- [ ] Approve risk tiers and mandatory review triggers
- [ ] Define hard budget and circuit-breaker thresholds
- [ ] Define evidence schema, retention, and chain-of-custody controls
- [ ] Approve environment and production-access policy
- [ ] Approve Definition of Ready and Definition of Done
- [ ] Approve emergency-stop, incident, recovery, and rollback procedures

## 14. Agentic Engineer Team — Closed-Loop Framework

SecB operates as a governed, self-improving engineering system:

`Demand / Ticket -> Engineer Loop -> Evidence & Outcomes -> Learn Loop -> Validated Knowledge -> Knowledge Base -> Skill Factory -> Versioned Skills -> Skill Registry & Router -> Engineer Loop`

Learning that is not validated must return to controlled experimentation or independent review. It must not enter the authoritative knowledge base or active skill registry.

Detailed architecture: `docs/02-architecture/CLOSED_LOOP_ARCHITECTURE.md`.

## 15. Engineer and Learn Loops

- The Engineer Loop converts authorized demand into tested, secure, traceable software.
- The Learn Loop converts engineering evidence into validated, bounded insight.
- Project outcomes must remain distinguishable from reusable organizational knowledge.
- Knowledge must not automatically become an operational instruction.
- A skill must pass design, sandbox evaluation, independent validation, approval, versioning, and registry controls before activation.

Detailed contracts:

- `docs/06-agent-orchestration/ENGINEER_LOOP.md`
- `docs/06-agent-orchestration/LEARN_LOOP.md`
- `docs/13-evidence/KNOWLEDGE_LAYER.md`
- `docs/07-skill-engineering/SKILL_FACTORY.md`

## 16. Mandatory Control Gates

Every applicable work package must pass the following gates in sequence or record an authorized exception:

1. Authority Gate
2. Readiness Gate
3. Architecture Gate
4. Implementation Gate
5. Test Gate
6. Security Gate
7. Evidence Gate
8. Release Gate
9. Learning Gate
10. Skill Promotion Gate

Gate definitions and evidence requirements are maintained in `docs/00-governance/CONTROL_GATES.md`.

## 17. Knowledge and Skill Promotion Rule

No single engineering outcome may immediately rewrite authoritative knowledge or activate a new skill. Promotion requires:

- Multiple supporting examples or strong controlled evidence
- Independent validation
- No conflict with higher-authority policy or approved decisions
- Explicit applicability boundaries
- Evaluation against a recorded baseline
- Versioning and rollback capability
- Human approval for high-impact skills

## 18. Performance Governance

The framework must measure engineering delivery, quality, cost, learning, knowledge, skill, governance, and business outcomes. Metrics must not reward speed or automation volume at the expense of safety, evidence, reliability, or stakeholder value.

The KPI baseline is maintained in `docs/11-operations/PERFORMANCE_INDICATORS.md`.
