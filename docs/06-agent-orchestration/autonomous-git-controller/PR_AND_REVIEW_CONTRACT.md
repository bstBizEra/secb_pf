# Pull Request, CI and Review Contract

Status: Implementation Ready | Version: 1.0.0 | Work Package: `SECB-WP-ENGLOOP-002`

Every PR includes ticket/work package, frozen specification ID/hash, build warrant, risk tier, scope/exclusions, requirement/RTM coverage, change summary, ADRs, tests, security evidence, migration/deployment/rollback plan, residual risks, evidence package and expected head/base SHAs.

Required CI contexts are selected by risk and changed paths and must report result, exact commit SHA, workflow identity/version, environment, artifact/log digest and completion time. Cached or prior-commit results do not satisfy the gate.

Review policy verifies reviewer identity, eligibility, independence, quorum, code-owner coverage, security veto and freshness. Implementer approval does not satisfy independent review. Review decisions are bound to PR head SHA. Any new commit marks prior approval `STALE` unless the approved policy explicitly permits non-material generated changes and independently verifies them.

Merge readiness requires successful current checks, no unresolved threads or blocking findings, RTM/evidence completeness, mergeability against current base, valid warrant prerequisites, no unauthorized diff and no expired approval. Failure routes to `REPAIRING` or `HELD`.
