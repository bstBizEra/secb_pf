# Sandbox Evidence Record — SECB-WP-ENGLOOP-MVP-001

Evidence ID: `EVD-SECB-ENGLOOP-MVP-001-20260809`  
Executed at: `2026-08-09T07:48:33Z`  
Runtime: Python 3.12.13 on Linux 6.18.35 x86_64  
Scope: Engineer Loop v1.5 Skill Router, FIT-101–120  
Risk tier: `R1`  
External effects: None

## Gate results

| Gate | Result | Evidence |
|---|---|---|
| Authority and scope | PASS | Work package limits execution to side-effect-free R1 sandbox |
| Compilation | PASS | `python -m py_compile router.py test_router.py` |
| FIT first run | PASS | 20/20 tests passed |
| FIT deterministic rerun | PASS | 20/20 tests passed again with identical routing expectations |
| FIT identifier continuity | PASS | `FIT-101` through `FIT-120`, unique and continuous |
| Schema parse | PASS | Seven v1.5 JSON schemas parsed successfully |
| Static side-effect inspection | PASS | No subprocess, socket, HTTP client, dynamic execution, direct file-open, OS deletion or process-launch path |
| Evidence integrity | PASS | SHA-256 digests recorded below |
| Independent architecture/security/evidence review | PENDING | Reviewer is not yet assigned |

## Defect and closure

`DEF-ENGLOOP-MVP-001`: the initial test run found that explicit named-skill priority was evaluated after the minimum-cardinality shortcut. The router was corrected so every explicitly named skill must be eligible and included; unavailable or revoked named skills now fail closed. FIT-101–120 then passed twice.

The initial static scan also matched the in-memory `set.remove()` operation as if it were filesystem deletion. The scanner was refined to resolve the call owner and distinguish container mutation from prohibited OS/file operations. The refined gate passed.

## Artifact digests

| Artifact | SHA-256 |
|---|---|
| `router.py` | `4d1dab78b30eff24b5b4a6202ef84d23c814fb9efed63da049d501eb53eecef2` |
| `test_router.py` | `8db87b0fe89fa3954f6fb1759d427f9b27da45fa993372b48fb51ecf996ec1d0` |
| `SECB-WP-ENGLOOP-MVP-001.md` | `261f506bc1a708aff0c90e4250eb49f3b56c6b7fa4cee7469ee5b2b720ab9f04` |
| `README.md` | `96001a35c1afdbf463299cb31f2bc93277e5a1ce49fa5ca9d42d4c9737681549` |

The seven schema and FIT specification digests remain recorded in the execution output. This record itself must be hashed after finalization and attached to the review decision.

## Certification decision

Automated sandbox gates: `PASS`  
Current status: `SANDBOX_TESTED_PENDING_INDEPENDENT_REVIEW`  
Final transition: `HELD_AT_INDEPENDENT_REVIEW_GATE`

The package must not be labelled final `SANDBOX_TESTED` until an independent reviewer accepts architecture, security and evidence with no blocking finding. Runtime `AGENTS.md` adoption, external/mutating routing and production autonomy remain `NOT_AUTHORIZED`.

