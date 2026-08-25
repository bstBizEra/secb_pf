# RACI and Role Crosswalk

Status: Draft — proposed, not approved
Owner: TBD
Approvers: the governance owner named by `AGENTS.md` §13 item 1
Closes: `AGENTS.md` §13 item 2, "Approve agent role catalog and segregation-of-duties matrix"

`AGENTS.md:133` and `docs/INDEX.md:9` both list a RACI/SoD matrix as living in
`docs/00-governance/`. Until this file, it did not exist there. This is that artifact.

It **introduces no new roles and no new stages**. Every row is a mapping between vocabularies
already in the repository, and every mapping is citable. Where a mapping cannot be made from an
existing artifact, the cell says so rather than guessing.

## 1. Why a crosswalk was needed

Three role vocabularies are in use, and no document connected them. Measured: zero roster role
names appear in `DELIVERY_LIFECYCLE_STAGES.md`, and zero stage exit-states appear in
`AGENTIC_ENGINEER_TEAM.md`. The two documents that between them define *who does the work* and
*what the work is* share no terms in either direction.

| Vocabulary | Source | Members |
| :--- | :--- | :--- |
| Agent roster | `docs/agents/AGENTIC_ENGINEER_TEAM.md` | 13 roles |
| Engineer-loop letters | `docs/06-agent-orchestration/ENGINEER_LOOP_STEP_CONTRACTS.md:7` | `O G P A E T S V R` |
| Organizational roles | `docs/08-workflows/DELIVERY_LIFECYCLE_STAGES.md` | Product Sponsor, Service Owner, Business Owner, Deployment Commander, Architecture Review Board, Change Advisory Board |

**The first two are nested, not conflicting.** The nine loop letters are the build-path subset of
the thirteen roster roles:

| Letter | Roster role | | Letter | Roster role |
| :--- | :--- | :--- | :--- | :--- |
| `O` | Orchestrator | | `S` | Security Agent |
| `G` | Governance Agent | | `V` | Reviewer Agent — the loop calls it "Independent Reviewer" |
| `P` | Product / Requirements Agent | | `R` | Release Agent |
| `A` | Architect Agent | | | |
| `E` | Engineer Agent | | | |
| `T` | Test Agent | | | |

The four roster roles outside the engineer loop are **Learning Agent**, **Knowledge Curator** and
**Skill Engineer** (they operate in the Learn Loop and Skill Factory, not the 35-step build path)
and **Human Approver** (the gate, not a worker). `V` and "Reviewer Agent" are one role under two
names; that synonym should be retired in favour of one term.

The third vocabulary is **organizational, not agent-level**. Those names denote accountable
humans or boards. They are not agent roles and must not be implemented as agents.

## 2. Stage-to-role crosswalk

`A` = accountable (one per stage). `C` = consulted. Human column cites who must decide.

| # | Stage → exit state | Accountable | Consulted | Human decision |
| ---: | :--- | :--- | :--- | :--- |
| 1 | PRD Review and Baseline → `PRD_BASELINED` | Product / Requirements | Architect, Governance | Product Sponsor |
| 2 | Requirement Decomposition → `REQUIREMENTS_READY` | Product / Requirements | Architect, Test | Product Sponsor |
| 3 | Architecture Design → `ARCHITECTURE_APPROVED` | Architect | Security, Engineer | Architecture Review Board |
| 4 | Detailed Solution Design → `SOLUTION_DESIGN_APPROVED` | Architect | Engineer, Test, Security | Architecture Review Board |
| 5 | Security and Compliance Design → `SECURITY_DESIGN_APPROVED` | Security | Architect, Governance | Security authority |
| 6 | Implementation Planning → `IMPLEMENTATION_AUTHORIZED` | Orchestrator | Engineer, Product / Requirements | Governance owner |
| 7 | Development → `BUILD_COMPLETE` | Engineer | Test, Architect | — see §4 |
| 8 | Engineering Verification → `ENGINEERING_VERIFIED` | Test | Engineer, Reviewer | — see §4 |
| 9 | Quality and Security Validation → `RELEASE_CANDIDATE_VALIDATED` | Reviewer | Test, Security | Security authority |
| 10 | UAT and Pilot → `BUSINESS_ACCEPTED` | Product / Requirements | Test | Business Owner |
| 11 | Production Readiness Review → `PRODUCTION_AUTHORIZED` | Governance | **see §3 — two dimensions unowned** | Change Advisory Board |
| 12 | Production Deployment → `DEPLOYED` | Release | Governance | Deployment Commander |
| 13 | Hypercare and Stabilization → `STABILIZED` | **UNOWNED — no operations role exists** | Release, Engineer | Service Owner |
| 14 | Post-Implementation Review → `CLOSED_TO_BAU` | Learning | Knowledge Curator, Governance | Service Owner |

## 3. Two gaps this crosswalk exposes rather than fixes

`DELIVERY_LIFECYCLE_STAGES.md:436-445` requires eight go/no-go decisions at stage 11. Six map to
roster roles — Product, Engineering, QA (Test), Security, Business, Governance. **Two do not:**

- **Operations** — "operationally supportable". No roster role owns operability, and stage 13
  (Hypercare) has no accountable role at all for the same reason.
- **Data** — "migration and reconciliation ready". No roster role owns data. `docs/03-data/` is
  empty, while a migration is `R3` under `RISK_AUTHORITY_MATRIX.md`.

These are recorded, not filled. Adding roles is an `AGENTS.md` §13 item-2 decision for the
governance owner, and both bind only at stages 11-13, which are unreachable while stages 1-10
remain unentered. Filling them now would be building for a state the framework has not reached.

## 4. The autonomy boundary — the practical answer

**No stage gate in this table can be closed by an agent.** A stage-gate verdict is a `D2 MATERIAL`
decision (`docs/13-evidence/STAGE_GATE_REQUIREMENTS_READY.md:267`), and
`DECISION_AUTHORITY.md:127` states that everything at `D2` and above reaches a human by design.
The first mandatory human gate is therefore **stage 1**, not stage 11.

Agent autonomy in BADF is real but operates *inside* stages 6-8, at work-package granularity,
under the 35-step engineer loop. The dashes in the Human column for stages 7 and 8 mean the
work is agent-executable; the stage *exit* still requires the gate above it.

This is not a limitation to be engineered away. `AGENTS.md`'s header records that production
autonomy is `NOT_AUTHORIZED`, and `FRAMEWORK_PRODUCT_DEFINITION.md:94` records runtime execution
as "absent by design". A crosswalk that showed agents closing stage gates would be describing a
different framework.

## 5. Segregation of duties

`SINGLE_IDENTITY_SOD_ACCEPTED_RISK.md` records that every board in this deployment has no members
and every duty lands on one operator. Under that condition the following pairs collapse, and the
first three are the ones that matter:

| Pair | Why it matters |
| :--- | :--- |
| Engineer ↔ Reviewer | The author reviews their own work; `V` exists to prevent exactly this |
| Engineer/Test ↔ Security | The repository's own risk register calls this collapse "not acceptable" |
| Release ↔ Human Approver | Production authorization and production execution in one identity |
| Governance ↔ delivery roles | The only collapse with a mechanism — `check_dual_policy.py` |
| Product ↔ Human Approver | Demand and acceptance in one identity |
| Skill Engineer ↔ Human Approver | Inert while `skill_registry_instances: 0` |

The Governance↔delivery mechanism should not be read as sufficient: that script reads its input
once and passes the same bytes to both sides, so it varies policy while holding transport
constant.

## 6. What this file does not do

It does not close `AGENTS.md` §13. Item 2 is *approve* the role catalog and SoD matrix; this
document proposes one and cannot approve itself. Item 1 — confirm the governance owner — gates
every other item including this one, and no agent, template or automation can close it.
