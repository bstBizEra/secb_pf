# SecB Autonomous Git Controller

Status: Implementation Ready
Version: 1.0.0
Work Package: `SECB-WP-ENGLOOP-002`
Owner: Release Engineering
Approver: Authorized project representative
Last Updated: 2026-08-08

## Purpose

Govern the complete, recoverable Git chain from an implementation warrant to evidence closure: repository verification, baseline pin, branch, atomic commits, push, PR, CI/security/review, merge warrant, protected merge, signed release, build, deployment observation, revert/rollback and cleanup.

## Binding flow

`AUTHORIZED → REPOSITORY_VERIFIED → BASELINE_PINNED → BRANCH_CREATED → IMPLEMENTING → LOCALLY_VERIFIED → COMMITTED → PUSHED → PR_OPEN → CI_RUNNING → REVIEWING → MERGE_READY → MERGE_WARRANTED → MERGED → TAGGED → BUILT → DEPLOYED → OBSERVING → COMPLETED`

Recovery states are `CONFLICTED`, `REPAIRING`, `HELD`, `REVERTING`, `ROLLED_BACK`, and `OUTAGE_PRESERVED`.

## Invariants

1. Repository identity and remote URL are allowlisted before fetch or push.
2. Work starts from a clean, pinned commit SHA reachable from the approved default branch.
3. Branch ownership, TTL and path scope derive from the implementation warrant.
4. Commits are attributable, ticket-linked, atomic and signed where policy requires.
5. Force push to protected branches is prohibited; destination is revalidated at push time.
6. A PR identifies the frozen specification, RTM, risk, tests, evidence and rollback.
7. Any new PR-head commit invalidates prior CI conclusions, approvals and merge warrant unless policy explicitly proves them commit-bound and current.
8. A merge warrant references exact repository, PR, base SHA, expected head SHA, checks and expiry.
9. Merge and production-release authority remain separate.
10. Tags, artifacts, SBOM and provenance resolve to the merged source.
11. Git/CI uncertainty preserves checkout and enters hold; speculative retry is forbidden.
12. Cleanup revokes temporary credentials, destroys sandbox resources and retains evidence.

## Completion

This module is implementation-ready when transition contracts, operation schema, recovery procedures, deterministic gates and end-to-end traceability validate. It does not authorize access to a repository or production environment.
