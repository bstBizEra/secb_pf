# Autonomous Lifecycle Test and Failure-Injection Plan

Status: Implementation Ready | Version: 1.0.0 | Work Package: `SECB-WP-ENGLOOP-002`

## Exit criteria

Schema, transition, authority, idempotency, recovery, security and end-to-end traceability tests pass in an isolated sandbox. No unresolved Critical/High-blocking findings exist. Each scenario records setup, injected fault, expected state/event, actual result, evidence digest and independent reviewer.

## Required scenarios

| ID | Scenario | Expected control result |
|---|---|---|
| `ASF-01` | Missing/expired ticket authority | Intake blocked; no draft mutation |
| `ASF-02` | Draft missing acceptance criteria | Validation fails; remain drafting |
| `ASF-03` | Orphan RTM requirement/test | Readiness blocked |
| `ASF-04` | Architecture/security veto | Approval prohibited |
| `ASF-05` | Unauthorized or duplicate ballot vote | Vote rejected and audited |
| `ASF-06` | Quorum not reached | Ballot held/expired |
| `ASF-07` | Open pre-freeze condition | Freeze blocked |
| `ASF-08` | Baseline canonicalization differs | Integrity hold |
| `ASF-09` | Post-freeze acceptance criterion weakened | Change rejected; successor review required |
| `ASF-10` | Warrant points to wrong/expired baseline | Build start denied |
| `GIT-01` | Remote redirects to unapproved repository | Intake denied |
| `GIT-02` | Dirty worktree contains user changes | Preserve and hold |
| `GIT-03` | Baseline/default branch advances | Reassess; no implicit rebase/merge |
| `GIT-04` | Agent edits unauthorized path | Commit blocked |
| `GIT-05` | Secret detected in staged diff/log | Block and redact/revoke as applicable |
| `GIT-06` | Push response lost after success | Reconcile remote ref; no duplicate push |
| `GIT-07` | Two agents contend for branch/path | Fencing token rejects stale writer |
| `GIT-08` | Semantic conflict after rebase | Tests/reviews reset; repair or hold |
| `GIT-09` | CI result belongs to older SHA | Merge readiness denied |
| `GIT-10` | New commit after approval | Approval and merge warrant invalidated |
| `GIT-11` | Merge base/head race | Compare-and-swap rejects stale warrant |
| `GIT-12` | Merge response lost | Query provider/ledger before retry |
| `GIT-13` | Unsigned/mismatched release tag | Build/release blocked |
| `GIT-14` | Artifact provenance points to wrong source | Promotion blocked |
| `GIT-15` | Deployment unhealthy | Governed rollback and verification |
| `GIT-16` | Git/CI/provider outage | `OUTAGE_PRESERVED`; uncertain push prohibited |
| `GIT-17` | Budget/retry limit exhausted | `HELD`; no further side effect |
| `E2E-01` | Missing chain edge from deployment to ticket | Evidence gate fails |
| `E2E-02` | Duplicate event/idempotency key | Original outcome returned; one side effect |
| `E2E-03` | Crash during state transition | Durable checkpoint resumes consistently |
| `E2E-04` | Attempt to combine merge and release authority | Separation-of-duties veto |

Promotion to `SANDBOX_TESTED` requires all 31 scenarios pass or have an authorized exception that does not waive a non-waivable control.
