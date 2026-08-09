# Independent Review Decision — SECB-WP-ENGLOOP-MVP-001

Review ID: `REV-SECB-ENGLOOP-MVP-001-20260810`
Work Package: `SECB-WP-FWK-009` (issue #14)
Requested by: `INDEPENDENT_REVIEW_REQUEST.md` in the sandbox evidence package

## Required decision fields

| Field | Value |
|---|---|
| Reviewer identity | Claude (Opus), IDE agent session of 2026-08-10 |
| Reviewer role | Independent reviewer — wrote none of the reviewed artifacts; executor of record for the MVP is "Codex sandbox implementation agent" (`SECB-WP-ENGLOOP-MVP-001.md`, Roles) and the artifacts predate this repository's history (imported at `cb03eba`) |
| Review timestamp | 2026-08-10 (UTC), session-recorded |
| Decision | **CONDITIONALLY APPROVE** — promote `HELD_AT_INDEPENDENT_REVIEW_GATE → SANDBOX_TESTED`; conditions below bind future work packages, not this transition |
| Attestation reference | This document, merged by the human approver through PR review — the merge commit is the attestation |
| Expiry | Review valid for the artifacts at the hashes below only; any change to `router.py` or `test_router.py` voids it |

## Artifact hashes reviewed (recomputed by the reviewer, 2026-08-10)

| Artifact | SHA-256 |
|---|---|
| `router.py` | `4d1dab78b30eff24b5b4a6202ef84d23c814fb9efed63da049d501eb53eecef2` |
| `test_router.py` | `8db87b0fe89fa3954f6fb1759d427f9b27da45fa993372b48fb51ecf996ec1d0` |
| `SECB-WP-ENGLOOP-MVP-001.md` | `261f506bc1a708aff0c90e4250eb49f3b56c6b7fa4cee7469ee5b2b720ab9f04` |
| `README.md` | `96001a35c1afdbf463299cb31f2bc93277e5a1ce49fa5ca9d42d4c9737681549` |
| `EVIDENCE_RECORD.md` (pinned per its own closing requirement) | `505bd433b5b2b95845f559a13794552a98cc16af57ccd653a34f37c00f7d2d12` |

All four package digests match the values recorded in `EVIDENCE_RECORD.md`.

## Automated gates — re-executed, not read

| Gate | Reviewer result |
|---|---|
| Compilation (`py_compile`, both files) | PASS |
| FIT run A | 20 passed |
| FIT run B (determinism) | 20 passed, identical |
| FIT identifier continuity | 20 unique IDs, `fit_101`–`fit_120` |
| Seven v1.5 JSON schemas parse | 7/7 PASS |
| Static prohibited-call scan (`subprocess`, sockets, HTTP, `os.remove/system`, `shutil`, `eval/exec`, `open`) | none found |
| Digest recomputation | all match |

## Ten assessment areas

1. **FIT coverage / negative tests** — PASS. Every routing invariant has at least one negative test (revoked named skill, cycle, digest change, risk ceiling, unwarranted effect, unconfirmed high-impact, taint, schema mismatch, weakened acceptance, unknown outcome, weakened fallback floor, budget exhaustion, chain tamper, self-admission).
2. **Deterministic selection / explicit precedence** — PASS. FIT-103 proves order-independence; named-skill priority fails closed on ineligible names (`router.py:143-145`) — the defect `DEF-ENGLOOP-MVP-001` fix is present and tested.
3. **Invalidation** — PASS with finding F1 (below). Request/registry/policy hashes re-checked at invocation (`router.py:192-197`).
4. **Prerequisite cycles, typed handoff, taint** — PASS. DFS cycle detection fails closed; `untrusted_instruction` taint is rejected as instruction (`router.py:225-226`).
5. **Selection / invocation / effect separation** — PASS with finding F2. Selection creates no warrants (FIT-110); effects require a prior invocation warrant.
6. **High-impact confirmation / prohibited effects** — PASS with finding F4. Eight high-impact effect classes require separate confirmation (`router.py:212-213`).
7. **Reconciliation, fallback floors, circuit breaker** — PASS. Unknown outcomes block retry; fallback cannot lower any of four floors; budget exhaustion holds except containment.
8. **Event-chain integrity / anti-poisoning** — PASS with finding F3. Tamper detection works (FIT-119); learning never mutates the registry (FIT-120, verified by deep-compare).
9. **Evidence reproducibility** — PASS. Every gate above reproduced from the committed tree; digests stable across the review.
10. **Blocking findings** — **none.** All findings are conditions on *future* authorization steps, not on this side-effect-free R1 sandbox transition.

## Findings

| ID | Severity | Finding | Bound condition |
|---|---|---|---|
| F1 | Medium | `registry_hash` (`router.py:68-78`) pins id/version/digest/status/capabilities/risk/prerequisites/conflicts/effects but **omits `validation`, `qualification`, `cost`, `expires_at`** — all of which feed the selection score (`router.py:166-170`). Two registries differing only in those fields hash identically, so `authorize_invocation` would not invalidate a route after they change. | Must be fixed before any registry-qualification work package (the "taxonomy and registry" step named in `ENGINEER_LOOP.md` §7) and before any re-scoring of live routes. |
| F2 | Low | `authorize_effect` (`router.py:206-215`) validates against plan state only; it does not re-pin request/registry/policy at effect time. A registry change between invocation and effect authorization is undetected. | Effect-time re-verification or warrant expiry required before any external or mutating effect authorization. |
| F3 | Low | The event chain has no external trust anchor: an actor who can rewrite the whole list can recompute every hash and `verify_event_chain` passes. Adequate for a sandbox evidence model; not for adversarial settings. | Anchoring (signature or write-once store) required before evidence chains are relied on outside the sandbox. |
| F4 | Observation | `confirmation: bool` (`router.py:206`) models high-impact confirmation as a boolean; production requires a verifiable authority artifact (warrant/signature), not a flag. | Bind at runtime-adoption design time. |
| F5 | Observation | `route()` enumerates capability combinations (`router.py:149-174`); the smallest-size-first break bounds typical cases but worst case remains exponential in eligible-skill count. | Registry-scale bound or solver required before large-registry use. |

## What this decision does and does not do

- **Does:** certify the MVP package `SANDBOX_TESTED` for the artifacts at the pinned hashes, upon human merge of this record.
- **Does not:** authorize runtime `AGENTS.md` adoption, registry/compatibility data, external or mutating routing, FIT-101–120 *runtime* certification, or production autonomy — all remain `NOT_AUTHORIZED` per `ENGINEER_LOOP.md` §7.

The sandbox evidence directory was not modified by this review; its digests are identical before and after.
