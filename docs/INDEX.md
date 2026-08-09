# SecB Documentation Index

Documentation baseline: 0.6.0 — full-lifecycle documentation drafted; the modules below are documentation-ready for implementation  
Project status: governed solely by the `AGENTS.md` header (`SECB-WP-FWK-003`) — "implementation ready" here describes the documents, not an authorization to build or run  
Last Updated: 2026-08-09

| Path | Purpose | Governed baseline |
|---|---|---|
| `00-governance/` | Authority, RACI/SoD, gates, ballots, policies | Control Gates + risk/budget policies |
| `01-requirements/` | Requirements and traceability | Requirements Traceability Standard + PRD (Engineer Loop, `SECB-WP-FWK-008`); RTM pending authorization |
| `02-architecture/` | System and runtime architecture | Closed-Loop + Runtime Control Architecture |
| `03-data/` | Data model, classification and invariants | Data Architecture |
| `04-api-and-integrations/` | APIs, events, errors and contracts | API Baseline |
| `05-security/` | Threats, controls, privacy and testing | Engineer Loop Threat Model |
| `06-agent-orchestration/` | Engineer/Learn loops, durable lifecycle and skill routing | Core + Specification + Git + Durable Workflow + Skill Router |
| `07-skill-engineering/` | Skill Factory, registry, lifecycle and evaluation | Skill Factory + Registry Contract |
| `08-workflows/` | State machines and workflows | Workflow Catalogue |
| `09-testing/` | Test, recovery and failure injection | Core + Lifecycle + DWRC + FIT-101–120 |
| `10-devops/` | CI/CD, trusted build and release controls | Trusted Git Pipeline |
| `11-operations/` | SLOs, monitoring, incident and continuity | Performance Indicators |
| `12-decisions/` | ADRs and formal decisions | Lifecycle + DWRC decisions |
| `13-evidence/` | Evidence and traceability | Evidence Package + Work Package Records |
| `14-plans/` | Roadmaps, work packages and certification | Lifecycle + DWRC + Skill Router backlogs |
| `15-runbooks/` | Operational and recovery procedures | Runbook Index |
| `16-templates/` | Controlled document templates | Template Catalogue |
| `17-references/` | External standards and references | Reference Register |
| `agents/` | Agent definitions and handoffs | Agentic Engineer Team |
| `skills/` | Skill catalog, validation and tools | Versioned Skill Registry |

## Implementation-ready modules

- `SECB-WP-ENGLOOP-001`: Core Engineer Loop contracts.
- `SECB-WP-ENGLOOP-002`: Specification Factory, Git Controller and traceability.
- `SECB-WP-ENGLOOP-003`: Durable history, replay, reconciliation and compensation.
- `SECB-WP-ENGLOOP-004`: Autonomous Skill Routing and Orchestration.

## Skill Router Upgrade — `SECB-WP-ENGLOOP-004`

- `06-agent-orchestration/skill-router/SKILL_ROUTER.md`
- `SKILL_ROUTER_STATE_MACHINE.md`
- `SKILL_REGISTRY_AND_SELECTION_CONTRACT.md`
- `SKILL_ORCHESTRATION_AND_HANDOFF_CONTRACT.md`
- `AUTHORIZATION_CONFIRMATION_VALIDATION_POLICY.md`
- `ROUTER_API_AND_EVENT_CONTRACT.md`
- `AGENTS_AUTOMATIC_SKILL_ROUTING_POLICY_TEMPLATE.md`
- Seven JSON schemas for request, registry, route, handoff, execution, events and outcomes
- `09-testing/SKILL_ROUTER_FIT_101_120.md`
- `14-plans/SKILL_ROUTER_IMPLEMENTATION_BACKLOG.md`
- `13-evidence/SECB-WP-ENGLOOP-004_RECORD.md`

Target-state decision: `PROPOSED → IMPLEMENTATION_READY` for the documented Skill Router module. Runtime adoption, FIT certification, external/mutating routing and production autonomy remain unauthorized.
