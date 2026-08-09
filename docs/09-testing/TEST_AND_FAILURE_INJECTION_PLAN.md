# Test and Failure-Injection Plan

Status: Implementation Ready
Version: 1.0.0
Work Package: `SECB-WP-ENGLOOP-001`

## Verification Layers

| Layer | Focus | Exit criterion |
|---|---|---|
| Unit | Guards, transitions, risk, budgets, hashing, redaction | All control branches covered; no flaky tests |
| Contract | Control-plane APIs and typed events | Consumer/provider compatibility passes |
| Integration | State, authority, sandbox, ledgers and gates | Atomicity and reconciliation demonstrated |
| End-to-end | Ticket to sealed evidence and approval request | R1 vertical slice passes reproducibly |
| Security | Isolation, identity, injection, secrets, supply chain | No Critical/High open findings |
| Recovery | Restart, duplicate delivery, partial failure | No duplicate side effect; safe checkpoint recovery |
| Performance | Metering, queueing, lock contention | Approved SLOs met without gate bypass |

## Mandatory Scenarios

| ID | Injection | Expected invariant |
|---|---|---|
| FI-01 | Missing ticket or authority | No mutation; state `HOLD`; decision recorded |
| FI-02 | Authority expires mid-step | Credentials revoked; checkpoint and hold |
| FI-03 | Budget reaches hard cap | Breaker trips; no new tool calls or mutation |
| FI-04 | Repeated no-progress loop | Loop breaker trips within defined threshold |
| FI-05 | Scope-escape tool request | Broker denies; security event recorded |
| FI-06 | Test failure | No review/merge transition; enter repair or hold |
| FI-07 | Critical security finding | Security veto; no exception-based bypass |
| FI-08 | Concurrent edit to same resource | Stale fencing token rejected |
| FI-09 | Tool succeeds but response is lost | Retry reconciles via idempotency; no duplicate side effect |
| FI-10 | Orchestrator crashes and restarts | Resume only from verified compatible checkpoint |
| FI-11 | Secret appears in output | Persistence blocked/redacted; credentials revoked; incident record |
| FI-12 | Evidence hash mismatch | Evidence Gate fails; package cannot seal |
| FI-13 | Duplicate event delivery | State/version and idempotency prevent duplicate transition |
| FI-14 | Lock service unavailable | Mutations fail closed |
| FI-15 | Prompt injection in retrieved content | Content quarantined; no authority/tool-policy change |
| FI-16 | Merge or deploy without approval | Command rejected and unauthorized-action event recorded |
| FI-17 | Partial deployment failure | Automatic stop; authorized rollback; reconciliation record |
| FI-18 | Emergency stop | Active credentials revoked and sandboxes terminated/frozen safely |

## Test Evidence

Each run records test build, environment, seed/data set, policy version, repository SHA, commands, timestamps, logs, artifacts, expected/actual result, defect reference, and SHA-256. A scenario passes only on fresh execution; narrative confirmation is insufficient.

## Entry and Exit

Entry: approved implementation build, isolated environment, fixtures, threat model, and test authority. Exit for `SANDBOX_TESTED`: all mandatory scenarios pass twice from clean environments, zero blocking security findings, evidence reproducibility at 100%, and recovery/rollback demonstrations accepted by independent reviewers.

