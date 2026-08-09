# Durable Workflow Implementation Backlog

Status: Implementation Ready  
Version: 1.0.0  
Work Package: `SECB-WP-ENGLOOP-003`

| Phase | Scope | Exit gate |
|---|---|---|
| P0 Contract Freeze | Event/effect IDs, envelopes, determinism, authority claims, compensation registry | Architecture and governance ballots pass |
| P1 Durable Kernel | Event append, snapshots, tasks, leases, timers, inbox/outbox, recovery replay | FIT-001–004 and FIT-012 pass |
| P2 Effect Safety | Gateway, idempotency, receipts, reconciliation, Git adapter | FIT-002, 007, 008 and 010 pass |
| P3 Compensation | Registry, planner/executor, Git and deployment handlers | FIT-009 and 013 pass |
| P4 Upgrade Safety | Replay corpus, nondeterminism, patches, state migration | FIT-005, 006 and 014 pass |
| P5 Production Hardening | HA/DR, integrity checkpoints, observability, retention, performance | All tests pass; restore/replay exercise evidenced |

Initial delivery tickets are `DWRC-001` through `DWRC-012`: contract freeze; history store; replay kernel; activities/leases/timers; inbox/outbox; effect gateway; reconciliation; compensation; warrant/ballot integration; Git reference workflow; replay CI corpus; and HA/DR/integrity proof.

Recommended first vertical slice:

`Authorized ticket → branch → change → test → commit → PR → independent review ballot → merge or compensate → evidence → close`
