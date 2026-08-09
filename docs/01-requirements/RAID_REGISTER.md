# RAID Register — SecB Engineer Loop

Status: Prepared for stage-1 gate (`SECB-WP-FWK-014`)
Stage: 1, PRD Review and Baseline · Covers Risks, Assumptions, Issues,
Dependencies, and the constraints the product operates under
Review cadence: at every stage gate; entries are appended, never overwritten

## Risks

| ID | Risk | Impact | Likelihood | Treatment | Owner |
|---|---|---|---|---|---|
| R-01 | The classifier reasons over paths and sizes, not semantics, so an `R2`-magnitude change confined to `src/` under the cap reads `G0` | Autonomous merge of a change that deserved review | Medium | Work-package tier declaration remains an honest obligation; test and budget gates are the substantive check | Operator |
| R-02 | The governance verifier runs inside the repository it judges | A PR could in principle edit its own judge | Low today, High if delegation widens | Any `.github/` or classifier change is `G4`; full fix needs an organization (deferred D1) | Operator |
| R-03 | No independent ballot council exists, so `AGENT_BALLOT_REQUIRED` is unsatisfiable | Governance work cannot be delegated; operator remains the bottleneck | Certain | Accepted for now; recorded as deferred D3 | Operator |
| R-04 | Seven of eleven stakeholder roles are unassigned, including the governance owner open since import | Gate authorities named in the lifecycle have no members; stages 5, 9, 10, 11 cannot pass as written | High | Confirm at least business and product owner for stage 1; assign others before their stages | Operator |
| R-05 | Stage-gate authorities (Architecture Review Board, Security Board, CAB) collapse onto one person | Segregation of duties becomes nominal at stages 3–11 | High | State the collapse explicitly; consider external review for stage 9 | Operator |
| R-06 | KPI targets in the PRD have no owners, formulas or cadence | "Success" cannot be measured at stage 14 | High | `KPI_BASELINE.md` records each metric's readiness; unowned metrics are marked, not assumed | Operator |
| R-07 | The 600-line envelope cap was exceeded by the first PR after ratification | Friction, or pressure to raise a ceiling for convenience | Medium | Split large documentation sets across work packages; raising the cap is a `G4` act needing evidence of a pattern | Executor |

## Assumptions

| ID | Assumption | If false |
|---|---|---|
| A-01 | The operator holds constitutional authority for this product and may ratify delegation | Every gate record since `SECB-WP-FWK-012` would need re-authorization |
| A-02 | SecB's first product is the Engineer Loop itself (dogfooding), not an external system | The PRD's problem statement and users change; stage 1 reopens |
| A-03 | Production for this product means an internal BST deployment, not a customer-facing service | Stage 9–11 obligations grow materially (availability, DR, regulatory) |
| A-04 | No regulated or personal data is in scope | Stage 5 gains privacy-impact obligations and a compliance matrix |
| A-05 | A single-operator deployment is acceptable for stages 1–8, with independent review sought before stage 9 | Stage 9's "independent" requirement cannot be met at all |
| A-06 | GitHub remains the delivery platform on a personal-account plan | Deferred capabilities D1, D2 and D4 change shape or become available |

## Issues (open, affecting stage 1)

| ID | Issue | Effect |
|---|---|---|
| I-01 | Traceability exception: artifacts exist at stages 7–8 while stages 1–6 have no recorded gate verdicts | Downstream states are not formally valid until stage 1 passes and 2–6 are addressed |
| I-02 | `PRD-ENGINEER-LOOP.md` is marked *Draft for operator review* with no approval record or version baseline | Stage 1 cannot pass; this WP prepares the fix |
| I-03 | RTM absent, so stage 2 cannot start | Recorded in `docs/INDEX.md` since `SECB-WP-FWK-005` |
| I-04 | Vocabulary overlap: stage-gate `HUMAN_REQUIRED` versus merge-level `CONSTITUTIONAL_REQUIRED` | Reconciliation note in place; a unifying decision is the operator's |
| I-05 | Governance owner unassigned since import (`AGENTS.md` §13, eight open placeholders) | Several gate authorities are nominally vacant |

## Dependencies

| ID | Dependency | Needed by | Status |
|---|---|---|---|
| D-01 | Operator confirmation of business owner and product owner | Stage 1 gate | Outstanding |
| D-02 | Operator decision on product scope assumption A-02 | Stage 1 gate | Outstanding |
| D-03 | Independent reviewer identity | Stage 9 | Not provisioned (deferred D3) |
| D-04 | Organization-level GitHub capability | Deferred D1, D2, D4 | Not available on the current plan |
| D-05 | Runbooks, monitoring, backup and rollback evidence | Stage 11 | Not started; `docs/15-runbooks/` empty |

## Constraints

- Delegation expires 2026-11-08 and lapses by default (`delegation_envelope.json`).
- Absolute ceiling: 2000 changed lines, unwaivable by any tier or ballot.
- The sealed MVP evidence directory is immutable; its certification voids on change.
- Prohibited actions (`L0_ROOT_CONSTITUTION.md`) are refused, never weighed.
- Production remains `NOT_AUTHORIZED` until stage 11 issues an explicit go decision.
