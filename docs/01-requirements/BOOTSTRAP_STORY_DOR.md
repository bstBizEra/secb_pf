# Bootstrap Story Definition of Ready — v0.1

Status: In force for stage 2 (`SECB-WP-FWK-019`), as a bridge under conflict
record `CONFLICT-FWK-019.md`
Scope: **priority-one items only**, assessed before entry to Architecture Design
Authority: Operator (vily), spec owner, 2026-08-10

## What this is, and what it is not

This checks whether a priority-one requirement is ready for **architecture and
planning** — not whether a work package is ready for **coding**. Those are
different levels of readiness, which is why one document cannot serve both.

> **It does not replace the Implementation DoR v1.0**, which belongs to stage 6
> and additionally confirms approved architecture and ADRs, API and data
> contracts, mapped security and privacy controls, test scenarios and data,
> dependencies and environments, estimates and accountable owners, rollback and
> migration approach, observability requirements, RTM coverage through design and
> test, and no blocker above the accepted risk threshold.
>
> Passing this document authorizes entry to stage 3. It authorizes **nothing**
> about development.

## Criteria

A priority-one item is ready when all ten hold:

| # | Criterion |
|--:|---|
| 1 | Business objective and stakeholder identified |
| 2 | A requirement statement or user story exists |
| 3 | Acceptance criteria are testable |
| 4 | Priority and owner assigned |
| 5 | Preliminary dependencies identified |
| 6 | Known constraints stated |
| 7 | Relevant NFRs identified |
| 8 | Traceability back to the PRD |
| 9 | No unresolved ambiguity at blocker level |
| 10 | Preliminary risk classification present |

## Evaluation — the thirteen priority-one requirements

Source: `REQUIREMENT_CATALOGUE.md`. Criteria 1, 4 and 8 are satisfied
structurally by the catalogue's mandatory Source, Owner and Priority columns;
criteria 5–7 and 10 by the RAID register, NFR catalogue and risk tiers. The
columns below therefore show the criteria that can actually differ per item.

| Req | 2 statement | 3 testable acceptance | 9 no blocker ambiguity | Verdict |
|---|---|---|---|---|
| `FR-01` Ticketed intake | ✔ | ✔ gate proven failing, run `31320436859` | ✔ | **Ready** |
| `FR-02` Budget breaker | ✔ | ✔ gate proven failing, run `31325014002` | ✔ | **Ready** |
| `FR-03` Authority-delta classification | ✔ | ✔ 23 subprocess tests | ✔ | **Ready** |
| `FR-04` Dual-policy evaluation | ✔ | ✔ divergence test | ✔ | **Ready** |
| `FR-05` No self-widening of authority | ✔ | ✔ Genesis verdict + test | ✔ | **Ready** |
| `FR-06` Prohibited actions refused | ✔ | ✔ four G5 tests | ✔ | **Ready** |
| `FR-07` Stage records with §3 fields | ✔ | ✔ `STAGE_GATE_PRD_BASELINED.md` | ✔ | **Ready** |
| `FR-08` Unbroken chain, breaks recorded | ✔ | ✔ `RTM.md` + exceptions | ✔ | **Ready** |
| `FR-09` Evidence from the shipped surface | ✔ | ✔ 85 tests per CI run | ✔ | **Ready** |
| `FR-10` Autonomous merges announced | ✔ | ✔ four announcements to date | ✔ | **Ready** |
| `FR-11` Delegation expires | ✔ | ✔ `test_expired_envelope_escalates` | ✔ | **Ready** |
| `FR-12` Instantiable by procedure | ✔ | **✘ not testable here** — provable only by instantiating a second project | ✔ ambiguity is absent; verifiability is | **NOT READY** |
| `FR-18` Escalation not bypassable | ✔ | ✔ PR #29 escalated and merged only on instruction | ✔ | **Ready** |

**Twelve of thirteen ready. One is not, and it is not waived.**

## The failure, carried rather than waived

`FR-12` — *a new project can be instantiated from the framework by following a
documented procedure* — fails criterion 3. Its acceptance method cannot be
executed inside this repository: instantiation is only provable by instantiating.
`NEW_PROJECT_BOOTSTRAP.md` exists and is marked *never executed end to end*.

This is recorded as traceability exception `TX-01` and carried into stage 3 as a
**known gap with a named closing condition** — the first bootstrap of a second
project — rather than being marked ready on the strength of the document
existing. A requirement whose acceptance method has never been run is not ready;
saying otherwise would make this checklist decorative.

Stage 2's exit condition, as amended by the canonical resolution, reads
*"priority-one stories satisfy the Bootstrap Story DoR v0.1 and remaining
unresolved items are not at Blocker level."* `FR-12`'s gap is **not** at blocker
level: nothing in stages 3–8 depends on it, and it blocks only the claim that the
framework is instantiable, which no downstream stage consumes. The gate can pass
with this gap named.

## Review

Re-evaluated whenever a priority-one requirement is added or its acceptance
method changes. Superseded, not extended, by the Implementation DoR v1.0 at
stage 6 — the two coexist, each governing its own transition.
