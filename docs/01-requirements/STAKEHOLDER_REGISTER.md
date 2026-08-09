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
| Product Owner | `TBC-OPERATOR` — may be the same party as sponsor | Scope, priorities, acceptance | High | — |
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

Seven of eleven roles are unassigned or `TBC-OPERATOR`. Stage 1's exit
condition requires only that **business owner and product owner** be
identified, so those two must be confirmed for the gate to pass; the rest
become blocking at their own stages, and their absence is recorded in
`RAID_REGISTER.md` rather than discovered later.

Notably, several gate authorities named in `DELIVERY_LIFECYCLE_STAGES.md`
(Architecture Review Board, Security and Compliance Review Board, Change
Advisory Board) have no members. For a single-operator deployment these
collapse onto the operator, and that collapse should be stated explicitly
rather than left as an implied equivalence.
