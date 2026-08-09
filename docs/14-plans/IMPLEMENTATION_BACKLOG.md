# Engineer Loop Implementation Backlog

Status: Implementation Ready
Version: 1.0.0
Work Package: `SECB-WP-ENGLOOP-001`

## Delivery Strategy

Build an `R1` sandbox vertical slice first. Each story must include tests, threat controls, evidence, telemetry, rollback, and documentation. Production release capability is excluded from MVP.

| Order | Epic / story group | Deliverable | Acceptance summary | Depends on |
|---:|---|---|---|---|
| 1 | EP-01 Contract foundation | Canonical IDs, typed commands/events/errors | Schemas validate; incompatible versions fail closed | — |
| 2 | EP-02 Authority and risk | Policy decisions and `R0–R4` classifier | Expiry, scope, revocation and highest-tier rule tested | EP-01 |
| 3 | EP-03 Durable state machine | Legal transitions with optimistic concurrency | Invalid/stale transitions rejected and evidenced | EP-01,02 |
| 4 | EP-04 Budget and breakers | Reservation, metering, warning, trip, resume | Limits enforced across restarts | EP-01,03 |
| 5 | EP-05 Evidence and side effects | Append/seal/verify plus idempotency ledger | Hash mismatch and duplicate action safely blocked | EP-01,03 |
| 6 | EP-06 Sandbox and tool broker | Ephemeral workspace and scoped capability issuance | Scope/network/filesystem violations denied | EP-02,04,05 |
| 7 | EP-07 Engineer execution | Plan and controlled change step runner | R1 task completes with checkpoints and smallest diff | EP-03–06 |
| 8 | EP-08 Deterministic gates | Tests, scan adapters, RTM and veto handling | Failed gate cannot reach merge-ready | EP-05,07 |
| 9 | EP-09 Independent review/approval | Review records and approval request | Implementer cannot self-approve; expiry enforced | EP-02,08 |
| 10 | EP-10 Episode closure | Evidence package, resource revocation, Learn intake | Sealed reproducible episode and safe cleanup | EP-05,09 |
| 11 | EP-11 Recovery and concurrency | Leases, fencing, crash recovery, reconciliation | FI-08–10,13–14 pass | EP-03–06 |
| 12 | EP-12 Security hardening | Injection, secrets, SBOM, provenance, audit | Zero Critical/High and security suite passes | All MVP |
| 13 | EP-13 Pilot and metrics | 3–5 R1 episodes and KPI baseline | Evidence complete; outcomes reviewed | EP-01–12 |
| 14 | EP-14 Release controller | Staging-first deploy/verify/rollback | Separate authorization and FI-17 pass | Certification approval |

## MVP Exit Criteria

- Ticket-to-approval-request R1 flow completes from a clean environment.
- Illegal transition, expired authority, scope escape, budget exhaustion, duplicate side effect, failed test, and evidence mismatch all fail closed.
- Every acceptance criterion is linked to fresh evidence.
- Checkpoint restart and cleanup are demonstrated.
- No production access or autonomous merge/deploy capability exists.

## Definition of Done per Story

Approved contract; implementation; unit/contract/integration tests; threat-control mapping; telemetry; evidence artifact; rollback/disable path; reviewer sign-off; no blocking findings; documentation and traceability updated.

