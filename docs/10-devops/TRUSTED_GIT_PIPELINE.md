# SecB Trusted Git and Delivery Pipeline

Status: Implementation Ready | Version: 1.0.0 | Work Package: `SECB-WP-ENGLOOP-002`

## Stages

1. Intake: verify repository identity, policy and baseline.
2. Workspace: create isolated branch with lease and path scope.
3. Change: commit attributable, atomic changes.
4. Validate: run deterministic tests, security, license and supply-chain gates.
5. Review: verify independent approvals bound to exact head SHA.
6. Merge: consume single-use warrant through protected merge/queue.
7. Release: sign tag; build once in trusted builder; produce SBOM/provenance.
8. Promote: reuse artifact digest under separate environment authorization.
9. Observe: evaluate declared health and business/technical indicators.
10. Close/recover: seal evidence or execute governed revert/rollback.

## Trust boundaries

Agent output, repository content, PR comments and external dependencies are untrusted input. Only the control plane may issue capabilities, accept approvals, transition durable state, seal evidence or authorize merge/release. CI runners use ephemeral task-bound identity and deny-by-default network/secrets. Production credentials are unavailable to implementation and PR workflows.

## Supply-chain controls

Dependencies and actions are version/digest pinned; builder images are approved and immutable; secrets are brokered just in time; logs are redacted; artifacts are scanned and content-addressed; provenance links source, workflow, builder, dependencies and artifact digest; promotion verifies signatures and policy.

## Reconciliation

Every mutable provider call is recorded before dispatch and reconciled afterward. Duplicate idempotency keys return the original result. Unknown outcomes block downstream work. Scheduled reconciliation detects drift among ticket, branch, PR, merged SHA, tag, artifact and deployment.
