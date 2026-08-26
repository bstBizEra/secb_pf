# BADF Readiness

Status: `PROPOSED_ON_PR_HEAD`
Work package: `SECB-WP-FWK-135`
Canonical authority: `AGENTS.md`

## Readiness model

BADF readiness is a conjunction, not a score:

`READY = ENTRYPOINTS ∧ AUTHORITY ∧ LOOP ∧ EVIDENCE ∧ MEMORY ∧ SESSION ∧ SKILLS ∧ MCP ∧ SECURITY ∧ LIFECYCLE ∧ RELEASE ∧ POST_DEPLOY ∧ REGRESSION`

One unmet mandatory capability prevents `READY`.

## Current assessment

| Domain | Requirement | Current state | Evidence / next action |
|---|---|---|---|
| Repository entrypoint | Normative `AGENTS.md` | **READY-ON-BRANCH** | Charter updated in this work package |
| Claude adapter | Automatic harness entrypoint | **READY-ON-BRANCH** | `CLAUDE.md` points to `AGENTS.md` |
| Canonical framework status | One status source | **READY** | `FRAMEWORK_PRODUCT_DEFINITION.md` |
| Authority | Machine-checkable authority envelope | **PARTIAL** | Existing controls are substantial; authority classifier limitations remain documented |
| Decision/execution separation | Independent decision object consumed by executor | **PARTIAL** | Existing design separates concepts; runtime authority substrate remains bounded |
| Agent Council | Independent review protocol | **DEFINED** | Charter §8; executable council implementation/admission remains a follow-up |
| BSA boundary | Authority/context separation | **DEFINED** | Charter §9; BSA integration is not runtime capability yet |
| Advanced engineering loop | PRD -> production + assurance closure | **DEFINED** | Charter §6/§17/§18; stage instrumentation remains incomplete |
| Evidence | Provenance and composed-tree binding | **SUBSTANTIAL** | Existing evidence controls and traceability schema; coverage boundaries remain explicit |
| Memory | Classification/promotion/supersession | **DEFINED** | Charter §10; promotion implementation required |
| Sessions | Checkpoints/handoff/crash recovery/idempotency | **DEFINED** | Charter §12; executable session controller required |
| Skills | Admission lifecycle | **DEFINED** | `BADF_SKILL_ADMISSION_STANDARD.md`; registry/validator required |
| MCP/tools | Deny-by-default mutation | **DEFINED** | Charter §15; registry + enforcement required |
| Security | Secret/privacy/supply-chain/prompt-injection controls | **SUBSTANTIAL** | Existing security surfaces plus BADF admission controls; integration tests required |
| Release | Release decision + evidence + rollback | **DEFINED** | Charter §18; executable release gate required |
| Production | Deployment + post-deploy assurance | **DEFINED** | Charter §18; production substrate is intentionally absent from SecB PF |
| Regression | Charter claims protected by tests | **INCOMPLETE** | Add executable BADF contract tests before activation |

## Hard blockers to `READY`

1. The BADF registry and schemas are not yet executable as a complete admission system.
2. Skill admission is defined but no external skill has completed the full admission lifecycle.
3. MCP/tool mutation policy is defined but the complete registry/enforcement path is not yet activated.
4. Session/checkpoint/idempotency controls are defined but not yet implemented as a runtime controller.
5. PRD-to-production lifecycle coverage remains incomplete; SecB's current product definition explicitly distinguishes framework control from runtime execution.
6. Post-deployment SLO/assurance evidence is a downstream capability and must not be claimed as present in SecB PF merely because the policy is documented.
7. Repository/platform constraints still limit preventive enforcement in places; detective controls must not be reported as preventive.

## Readiness transitions

`NOT_READY -> ENGINEERING_READY -> GOVERNANCE_READY -> ACTIVATION_READY -> PRODUCTION_READY`

### ENGINEERING_READY

Requires charter, schemas, validators, test harness, evidence format, and repository entrypoints.

### GOVERNANCE_READY

Requires ratified authority model, ownership/RACI, risk triggers, memory/skill/MCP policies, and explicit exceptions.

### ACTIVATION_READY

Requires populated registries, admitted skills, tool permissions, session controller, council protocol, and deterministic gates.

### PRODUCTION_READY

Requires preventive enforcement where mandated, release/rollback capability, independent post-deployment verification, SLO acceptance, and assurance closure.

## False-readiness protections

The following are explicitly prohibited:

- treating a document as an implemented control;
- treating a schema as enforced without an executing validator;
- treating a registered skill as an admitted/activated skill;
- treating a tool as authorized because credentials exist;
- treating a council majority as approval;
- treating CI green as branch protection;
- treating deployment success as production acceptance;
- treating a successful post-deploy smoke test as SLO acceptance;
- treating an observation with missing provenance as evidence;
- treating a proposed branch as effective main capability.

## Exit evidence

A future `READY` declaration MUST cite:

- immutable repository tree/ref;
- readiness assessment version;
- all mandatory gate results;
- registry digests;
- test-set epoch;
- security assessment;
- evidence root/digest;
- authority receipt;
- release/deployment receipt where applicable;
- post-deployment verification and SLO evidence;
- unresolved-risk disposition.

Until those artifacts exist, the correct status is `NOT_READY` or the more specific bounded readiness state above.
