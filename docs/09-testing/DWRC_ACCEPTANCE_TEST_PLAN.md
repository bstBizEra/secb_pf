# Durable Workflow, Replay and Compensation Acceptance Test Plan

Status: Implementation Ready  
Version: 1.0.0  
Work Package: `SECB-WP-ENGLOOP-003`

The module cannot become `SANDBOX_TESTED` until all scenarios pass with hash-verifiable evidence.

| ID | Scenario | Required result |
|---|---|---|
| DWRC-FIT-001 | Worker stops before activity execution | Task is reassigned once |
| DWRC-FIT-002 | Worker stops after external commit before acknowledgement | Reconciliation prevents duplicate effect |
| DWRC-FIT-003 | Orchestrator restarts during durable timer | Timer fires once at/after deadline |
| DWRC-FIT-004 | Replay completed workflow | No model, tool or external API is invoked |
| DWRC-FIT-005 | Incompatible workflow code is deployed | Nondeterminism is detected; scheduling stops |
| DWRC-FIT-006 | Replay from snapshot and event zero | Final state hashes match |
| DWRC-FIT-007 | Warrant expires while paused | Replay succeeds; new effects remain blocked |
| DWRC-FIT-008 | Retry/cost budget exhausts | Restart does not reset counters |
| DWRC-FIT-009 | Release verification fails | Registered deployment compensation restores verified artifact |
| DWRC-FIT-010 | Resource changed externally before compensation | Preconditions prevent unsafe reversal |
| DWRC-FIT-011 | History event is removed/corrupted in test replica | Integrity verification fails closed |
| DWRC-FIT-012 | Outbox message is delivered twice | Consumer applies message once |
| DWRC-FIT-013 | Compensation repeatedly fails | Manual remediation opens; dependencies freeze |
| DWRC-FIT-014 | State schema migrates | Old histories replay identically through upcasters |
| DWRC-FIT-015 | Audit query starts from final result | Ticket-to-effect-to-evidence chain resolves completely |

Each evidence package contains test version, exact workflow/build/policy hashes, controlled fault, timestamps, event/effect IDs, expected/actual result, logs, integrity checks and reviewer decision.
