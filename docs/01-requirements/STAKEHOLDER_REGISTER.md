# Stakeholder Register — SecB Engineer Loop

Status: Prepared for stage-1 gate (`SECB-WP-FWK-014`)
Stage: 1, PRD Review and Baseline
Product: SecB Engineer Loop (`PRD-ENGINEER-LOOP.md`)

Fields marked **`TBC-OPERATOR`** require knowledge no agent holds. They are
left unfilled deliberately: an invented stakeholder register is worse than an
empty one, because it looks complete and a later reader trusts it.

| Role | Party | Interest | Influence | Engagement |
|---|---|---|---|---|
| Product Sponsor | Operator (vily) | Delegating engineering to agents without losing control | Decisive — holds constitutional authority (`L0_ROOT_CONSTITUTION.md`) | Continuous; approves every gate to date |
| Business Owner | **Operator (vily)** — confirmed 2026-08-10 | Business value, acceptance | Decisive | Continuous |
| Product Owner | **Operator (vily)** — confirmed 2026-08-10; same party as sponsor | Scope, priorities, acceptance | High | Continuous |
| Governance owner | **Unassigned** — open placeholder since import (`AGENTS.md` §13) | Authority, policy, SoD, gate integrity | High | Blocking: several gate authorities name a body that does not exist |
| Executor (agent) | Claude (IDE session) | Correct, bounded execution | Operational only — creates no authority | Per work package |
| Prior executor | Codex sandbox agent | Author of the certified MVP slice | Historical | Not active in this repository |
| Independent reviewer | Filled ad hoc (Claude for `REV-SECB-ENGLOOP-MVP-001`) | Certification integrity | High at certification | No standing reviewer identity exists (deferred capability D3) |
| Security authority | `TBC-OPERATOR` | Threat model, security gates | High from stage 5 | Not engaged; no stage-5 record exists |
| QA authority | `TBC-OPERATOR` | Independent validation at stage 9 | High from stage 9 | Not engaged |
| Operations / Service owner | `TBC-OPERATOR` | Runbooks, monitoring, support model | Decisive at stages 11–13 | Not engaged; `docs/15-runbooks/` is empty |
| Business users | `TBC-OPERATOR` | UAT acceptance at stage 10 | Decisive at stage 10 | Not identified |
| Downstream BST agents | BST organism (per `AGENTS.md` mission) | SecB as the precursor framework they start from | Consumers of the outcome | Indirect; no interface agreed |

## Consequence for the stage-1 gate

Business owner and product owner are **confirmed** (both the operator), which
satisfied stage 1's exit condition. Six roles remain unassigned and each becomes
blocking at its own stage; their absence is recorded in `RAID_REGISTER.md`
rather than discovered later.

Several gate authorities named in `DELIVERY_LIFECYCLE_STAGES.md` (Architecture
Review Board, Security and Compliance Review Board, Change Advisory Board,
Business Acceptance Committee, Product Steering Committee) have no members and
collapse onto the operator. That collapse is now an **accepted risk with named
compensating controls and a review date** —
`docs/00-governance/SINGLE_IDENTITY_SOD_ACCEPTED_RISK.md` — valid for stages
1–8. **Stage 9 remains blocked**: its independence requirement cannot be met by
one identity.
