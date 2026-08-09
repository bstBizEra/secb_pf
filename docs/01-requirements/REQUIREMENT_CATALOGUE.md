# Requirement Catalogue — SecB Engineer Loop

Status: Stage 2 in progress (`SECB-WP-FWK-018`)
Source: `PRD-ENGINEER-LOOP.md` v1.0.0 — objectives §7 (O1–O6), capabilities §9
Traceability: `RTM.md`

Every requirement cites the PRD objective or capability it decomposes. **A
requirement with no source is a requirement someone invented**, so the Source
column is mandatory and an empty one is a defect.

Priority: `P1` must exist for the product to be usable at all · `P2` needed
before production · `P3` improves the product.

Acceptance method: how the requirement is *proven*, not how it is described.

## Functional requirements

| ID | Requirement | Source | Owner | Acceptance method | Priority |
|---|---|---|---|---|---|
| `FR-01` | Every unit of work traces to a ticket carrying the ten §7 minimum fields; work without one is refused | O4, C-Core Workflow | Operator | Authority gate exits non-zero on a PR with no work-package reference — **proven failing**, run `31320436859` | P1 |
| `FR-02` | Every pull request declares a diff budget and is refused when it exceeds it | O1, AGENTS.md §6 | Operator | Budget gate exits `2` — **proven failing**, run `31325014002` | P1 |
| `FR-03` | Every change is classified by its authority delta into `G0`–`G5` and receives exactly one of five verdicts | O1 | Operator | 23 subprocess tests in `test_classify_authority_delta.py`; verdict recorded on every PR | P1 |
| `FR-04` | A change to the classifier or envelope is judged by both the incumbent and the proposed logic, and escalates when they disagree | O1, O4 | Operator | `test_divergence_escalates_even_when_head_would_pass`; dual-policy line in every governance job | P1 |
| `FR-05` | An executor cannot widen its own authority: governance, enforcement and constitution paths are never autonomously mergeable | O1 | Operator | Genesis PR's own verdict was `CONSTITUTIONAL_REQUIRED`; `test_g4_root_authority_surface_is_constitutional` | P1 |
| `FR-06` | Prohibited actions — disabling a control, destroying evidence, bypassing a verifier — are refused rather than weighed | O1 | Operator | `REJECTED` exit `3`; four G5 tests | P1 |
| `FR-07` | Each product traverses the 14-stage lifecycle, and every stage transition is a recorded decision citing evidence | O4 | Operator | A stage-gate record exists per passed gate, carrying the twelve §3 fields — `STAGE_GATE_PRD_BASELINED.md` | P1 |
| `FR-08` | The traceability chain from business objective to production deployment is unbroken, and any break is recorded as an exception | O4 | Operator | `RTM.md` plus recorded exceptions I-01 | P1 |
| `FR-09` | Test evidence is produced by executing the shipped surface, not by describing it | O3, C-Audit Trail | Operator | Test gate runs FIT-101–120 plus repo tests on every push and PR | P1 |
| `FR-10` | Every autonomous merge is announced with verdict, gates, merge SHA and issue | O1, C-Audit Trail | Executor | Three announcements to date: `e76f8b4`, `527b979`, `ebe7f30` | P1 |
| `FR-11` | Delegated authority expires and lapses by default rather than persisting | O1 | Operator | `expires_at` in the envelope; classifier escalates on an expired envelope (`test_expired_envelope_escalates`) | P1 |
| `FR-12` | A new project can be instantiated from the framework by following a documented procedure that classifies every path | O4 | Operator | `NEW_PROJECT_BOOTSTRAP.md`; **unverified until project #2** | P1 |
| `FR-13` | Engineering episodes yield knowledge objects that cannot become operational instructions without independent validation | O5 | Operator | `KNOWLEDGE_REGISTER.md`, five objects, all `Proposed`; §17 promotion path | P2 |
| `FR-14` | Evidence, once sealed, is immutable; a certification voids on any change to its artifacts | O2, C-Audit Trail | Operator | Sealed digests recomputed and matched at `SECB-WP-FWK-009` and again at `010` | P2 |
| `FR-15` | Independent certification is available for a sandbox slice, performed by a party that authored none of its artifacts | O2 | Operator | `REV-SECB-ENGLOOP-MVP-001-20260810` | P2 |
| `FR-16` | Skill routing selects a deterministic minimum-sufficient set, and selection never creates authority | O6 | Operator | FIT-101–120, 20/20; replayed against v1.5.1 unmodified | P2 |
| `FR-17` | Advancement of delegated authority follows a ladder whose rungs are pre-authorized, with conditions the agent cannot alter | O1 | Operator | `authority_ladder` in the envelope; `A3`/`A4` unreachable while the ballot layer is inactive | P2 |
| `FR-18` | An escalated change reaches a human with the reason stated, and the escalation path is not bypassable | O1 | Operator | `AGENT_BALLOT_REQUIRED` on PR #29, merged only on explicit instruction | P1 |
| `FR-19` | Defect classification supports attribution of an escape to the stage that should have caught it | O3, K-08 | Operator | ODC `defect_type`/`defect_trigger` + IEEE 1044 severity — **adopted, recording not yet in force** (condition C-3) | P2 |
| `FR-20` | Cost of agent work is recordable under a vendor-neutral contract without a collector | KPI K-10 | Operator | OTel GenAI attribute names adopted — **not yet recorded** (condition C-3) | P3 |

## Objective coverage

| Objective | Requirements |
|---|---|
| O1 — every control gate mechanically fail-able | `FR-01` `FR-02` `FR-03` `FR-04` `FR-05` `FR-06` `FR-10` `FR-11` `FR-17` `FR-18` |
| O2 — certify the router to `SANDBOX_TESTED` | `FR-14` `FR-15` |
| O3 — 100% of merged PRs green | `FR-09` `FR-19` |
| O4 — unbroken traceability | `FR-01` `FR-07` `FR-08` `FR-12` |
| O5 — Learn Loop each round | `FR-13` |
| O6 — reach an R0 read-only routing pilot | `FR-16` |

**Every objective has at least one requirement.** O5 and O6 have exactly one
each, which is thin: O5's single requirement covers capture but not the cadence
the objective claims ("each cycle round"), and O6 covers routing behaviour but
not the pilot authorization itself. Both are recorded as conflicts below rather
than papered over.

## Requirement conflicts and formal acceptances

| # | Conflict | Disposition |
|--:|---|---|
| 1 | O1 requires all ten gates mechanically fail-able; four are (`FR-01`…`FR-04` plus the advisory verdict). Six gates — Readiness, Architecture, Implementation, Evidence, Release, Learning, Skill Promotion — remain prose | **Accepted for now.** Mechanizing a gate before its stage is exercised would encode a guess. Each becomes a requirement when its stage is first entered |
| 2 | O5 claims the Learn Loop runs "each cycle round"; `FR-13` guarantees capture, not cadence. The loop has run once, at `SECB-WP-FWK-006` | **Accepted, tracked.** A cadence requirement is meaningless until there is a defined cycle; stage 14 defines one |
| 3 | O6 requires an R0 read-only pilot authorization; no requirement covers the authorization act, because it is a stage-6/11 decision, not a product capability | **Accepted.** Recorded here so the objective is not read as satisfied by `FR-16` alone |
| 4 | `FR-12` cannot be verified in this repository — instantiation is only provable by instantiating | **Accepted as an unverified requirement**, marked in the RTM. It becomes verifiable at project #2 |

## Artifact classes recorded as not applicable

Stage 2 lists artifact classes this product does not have. Recorded with reasons
rather than omitted, so a reader can tell "absent" from "overlooked":

| Class | Why not applicable |
|---|---|
| Business rules and calculation rules catalogue | No financial, pricing or domain calculations exist. The applicable rules are `L0_ROOT_CONSTITUTION.md` and the classifier, which are already normative documents; restating them would create a second source of truth |
| Epics, features, user stories | The users are agents and one operator. A story hierarchy over 20 requirements would be ceremony; the priority column is the prioritization record |
| Data requirements catalogue | The product stores no user data. Its data are git objects, CI run records and JSON config — covered in the NFR catalogue |
| Integration requirements catalogue | Two integrations: the GitHub API and GitHub Actions. Both appear in the NFR catalogue; two rows do not justify a document |
