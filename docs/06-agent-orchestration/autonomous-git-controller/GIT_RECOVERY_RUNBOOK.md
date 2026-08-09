# Git Recovery Runbook

Status: Implementation Ready | Version: 1.0.0 | Work Package: `SECB-WP-ENGLOOP-002`

## General rule

Preserve checkout, refs, logs and operation records. Do not reset, delete branches, force-push, repeat an uncertain side effect or destroy a sandbox until provider state and the side-effect ledger reconcile.

## Recovery cases

- Conflict: record both SHAs and conflicting paths; create a successor working state; apply the approved rebase/merge policy; rerun semantic tests; invalidate stale CI/reviews/warrants.
- Push response lost: query remote ref; if it equals intended SHA, record success; if unchanged, retry with the same idempotency context; otherwise hold.
- PR/merge response lost: query PR and target branch by operation nonce/expected SHA; never submit a second merge until reconciled.
- Git/provider outage: enter `OUTAGE_PRESERVED`, revoke unnecessary credentials, maintain leases/checkpoint, prohibit pushes and resume only after identity/state revalidation.
- Bad merge before release: use a governed revert PR; do not rewrite protected history.
- Bad release: deploy the last known-good artifact or execute the approved forward-fix; capture recovery evidence and incident link.
- Compromised credential or signature: revoke credential, hold affected refs/artifacts, investigate provenance and require replacement authority.
- Expired branch: preserve evidence, revoke credentials/lease and require explicit extension or successor branch before work resumes.

Cleanup occurs only after closure: delete eligible remote branch per retention policy, expire branch registry and lease, destroy sandbox, revoke temporary credentials, retain logs/diffs/evidence and verify no orphan resources.
