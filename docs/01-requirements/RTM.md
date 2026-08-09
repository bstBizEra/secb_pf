# Requirements Traceability Matrix — SecB Engineer Loop

Status: Stage 2 in progress (`SECB-WP-FWK-018`)
Standard: `REQUIREMENTS_TRACEABILITY_STANDARD.md` · Chain:
`DELIVERY_LIFECYCLE.md` §1
Pending since `SECB-WP-FWK-005`; this closes issue `I-03`.

The chain the framework claims to maintain:

`Business objective → PRD requirement → Detailed requirement → Design → Code
change → Test evidence → Release artifact → Production deployment`

**Downstream columns are present and empty by design.** Design is filled at
stages 3–4, code at stage 7, test evidence at stage 8, release artifact at
stage 12. An empty column means *that stage has not run*, which is different
from missing traceability — and reading it any other way is how a project
convinces itself it is further along than it is.

## Forward trace — objective → requirement → verification

| Objective | Requirement | Design (st. 3–4) | Code (st. 7) | Test evidence (st. 8) | Release (st. 12) |
|---|---|---|---|---|---|
| O1 | `FR-01` Ticketed intake | — | `scripts/check_work_package_ref.py` | 9 tests + run `31320436859` (fail proven) | — |
| O1 | `FR-02` Budget breaker | — | `scripts/check_budget.py` | 11 tests + run `31325014002` (fail proven) | — |
| O1 | `FR-03` Authority-delta classification | `L0_ROOT_CONSTITUTION.md` | `scripts/classify_authority_delta.py` | 23 tests | — |
| O1 | `FR-04` Dual-policy evaluation | `ADR-EVIDENCE-BACKED-AGENT-GOVERNANCE.md` | `scripts/check_dual_policy.py` | 8 tests incl. divergence | — |
| O1 | `FR-05` No self-widening of authority | `L0` layers L0–L3 | `scope.constitutional_paths` | Genesis verdict `CONSTITUTIONAL_REQUIRED` | — |
| O1 | `FR-06` Prohibited actions refused | `L0` G5 | `classify_authority_delta.py` G5 path | 4 G5 tests | — |
| O1 | `FR-10` Autonomous merges announced | `STANDING`-equivalent policy in `L0` | — *(procedural)* | 3 announcements: `e76f8b4`, `527b979`, `ebe7f30` | — |
| O1 | `FR-11` Delegation expires | `delegation_envelope.json` | `expires_at` check | `test_expired_envelope_escalates` | — |
| O1 | `FR-17` Pre-authorized ladder | `authority_ladder` | — *(config only)* | — **no test asserts ladder conditions** | — |
| O1 | `FR-18` Escalation not bypassable | `L0` verdicts | classifier exit codes | PR #29 escalated, merged only on instruction | — |
| O2 | `FR-14` Sealed evidence immutable | `EVIDENCE_PACKAGE_SCHEMA.md` | — *(discipline + `.gitignore`)* | Digests matched at FWK-009 and FWK-010 | — |
| O2 | `FR-15` Independent certification | `INDEPENDENT_REVIEW_REQUEST.md` | — | `REV-SECB-ENGLOOP-MVP-001-20260810` | — |
| O3 | `FR-09` Evidence from the shipped surface | — | `ci.yml` test-gate | 85 tests green per run | — |
| O3 | `FR-19` Defect attribution | — | — **not implemented** | — | — |
| O4 | `FR-07` Stage records with §3 fields | `DELIVERY_LIFECYCLE.md` §3 | — | `STAGE_GATE_PRD_BASELINED.md` | — |
| O4 | `FR-08` Unbroken chain, breaks recorded | §1 chain | — | This document; exception I-01 | — |
| O4 | `FR-12` Instantiable by procedure | `NEW_PROJECT_BOOTSTRAP.md` | — | **none — unverifiable here** | — |
| O5 | `FR-13` Knowledge cannot self-promote | `KNOWLEDGE_LAYER.md`, `LEARN_LOOP.md` | — | `KNOWLEDGE_REGISTER.md`, 5 objects `Proposed` | — |
| O6 | `FR-16` Deterministic minimum-sufficient routing | `SKILL_ROUTER*.md`, 7 schemas | `src/secb_router/router.py` v1.5.1 | FIT-101–120, 20/20, replayed | — |
| K-10 | `FR-20` Cost recordable | OTel GenAI conventions | — **not implemented** | — | — |

## Reverse trace — every artifact answers to a requirement

| Artifact | Serves |
|---|---|
| `scripts/check_work_package_ref.py` | `FR-01` |
| `scripts/check_budget.py` | `FR-02` |
| `scripts/classify_authority_delta.py` | `FR-03` `FR-05` `FR-06` `FR-11` `FR-18` |
| `scripts/check_dual_policy.py` | `FR-04` |
| `src/secb_router/router.py` | `FR-16` |
| `.github/workflows/ci.yml` | `FR-01` `FR-02` `FR-03` `FR-04` `FR-09` |
| `config/delegation_envelope.json` | `FR-11` `FR-17` `NFR-14` |
| `docs/08-workflows/DELIVERY_LIFECYCLE*.md` | `FR-07` `FR-08` |
| `docs/15-runbooks/NEW_PROJECT_BOOTSTRAP.md` | `FR-12` |
| `docs/13-evidence/KNOWLEDGE_REGISTER.md` | `FR-13` |
| Sealed MVP evidence package | `FR-14` `FR-15` `FR-16` |
| `config/ballot.schema.json` | **Nothing yet** — inert until identities exist. Orphan by design, recorded rather than hidden |

Every tracked artifact except the inert ballot schema answers to at least one
requirement. No orphaned code exists.

## Traceability exceptions

| ID | Exception | State |
|---|---|---|
| `I-01` | Artifacts exist at stages 7–8 while stages 2–6 have no recorded gate verdicts | **Narrowing.** Stage 1 closed at `06ed153`; stage 2 is in progress and this document is its central artifact. Stages 3–6 remain open |
| `TX-01` | `FR-12` has no verification and cannot acquire one in this repository | Accepted. Verifiable only by instantiating project #2 |
| `TX-02` | `FR-17` (authority ladder) has no test asserting its promotion conditions | **New, found by building this matrix.** The ladder is config the classifier reads for tier but never evaluates for advancement. Candidate requirement for stage 3 |
| `TX-03` | `FR-19` and `FR-20` are adopted methods with no implementation | Tracked as stage-1 condition C-3, due before stage 6 |

`TX-02` is the matrix earning its keep: writing the reverse trace surfaced that
the ladder's advance conditions are documented, read for the current tier, and
**never checked**. Nothing enforces that 30 clean merges precede `A2`. That is
exactly the class of gap a traceability matrix exists to expose, and it was
invisible while the ladder lived only in prose and JSON.
