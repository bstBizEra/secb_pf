# Autonomous Git State Machine

Status: Implementation Ready | Version: 1.0.0 | Work Package: `SECB-WP-ENGLOOP-002`

```mermaid
stateDiagram-v2
    [*] --> AUTHORIZED
    AUTHORIZED --> REPOSITORY_VERIFIED
    REPOSITORY_VERIFIED --> BASELINE_PINNED
    BASELINE_PINNED --> BRANCH_CREATED
    BRANCH_CREATED --> IMPLEMENTING
    IMPLEMENTING --> LOCALLY_VERIFIED
    LOCALLY_VERIFIED --> COMMITTED
    COMMITTED --> PUSHED
    PUSHED --> PR_OPEN
    PR_OPEN --> CI_RUNNING
    CI_RUNNING --> REVIEWING: checks_pass
    CI_RUNNING --> REPAIRING: checks_fail
    REVIEWING --> MERGE_READY: approvals_current
    REVIEWING --> REPAIRING: changes_requested
    REPAIRING --> IMPLEMENTING: retry_allowed
    MERGE_READY --> MERGE_WARRANTED
    MERGE_WARRANTED --> MERGED
    MERGED --> TAGGED
    TAGGED --> BUILT
    BUILT --> DEPLOYED: release_authorized
    DEPLOYED --> OBSERVING
    OBSERVING --> COMPLETED: healthy
    OBSERVING --> REVERTING: unhealthy
    REVERTING --> ROLLED_BACK
```

## Universal transition envelope

Every transition supplies operation ID, idempotency key, expected state version, actor/workload identity, authority/warrant ID, repository ID, expected base/head SHA, precondition results, evidence references, timeout, retry limit and failure transition. The State Controller performs compare-and-swap; the Side-effect Ledger reconciles uncertain outcomes before retry.

## Mandatory guards

- Repository identity and remotes match allowlist.
- Worktree status matches policy and baseline SHA remains reachable.
- Branch is owned, unexpired and not protected.
- Commit tree contains only authorized paths and no detected secrets.
- PR head/base SHAs match recorded values.
- Required CI, security and review contexts are successful and current for the exact head SHA.
- Merge queue rechecks expected head and base immediately before protected merge.
- Release authorization is distinct, unexpired and artifact-digest bound.

Conflict, outage, integrity mismatch, stale approval, budget exhaustion or unknown side-effect result transitions to `HELD` or `OUTAGE_PRESERVED` until reconciliation.
