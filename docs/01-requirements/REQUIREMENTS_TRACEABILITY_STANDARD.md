# SecB Requirements Traceability Standard

Status: Implementation Ready | Version: 1.0.0 | Work Package: `SECB-WP-ENGLOOP-002`

The RTM is the authoritative mapping from governed demand to released outcome:

`Demand → Requirement → Acceptance Criterion → Decision/ADR → Implementation Unit → Test → Evidence → Approval → Artifact → Deployment → Outcome`

Every node has a stable ID, version, owner, status and evidence reference. Every edge declares relationship type and source. Requirements may not be marked complete without at least one passing verification edge and evidence digest. Tests may cover multiple criteria, but coverage must be explicit. Orphans, dangling references, duplicate IDs, circular supersession and links to mutable unpinned artifacts are validation errors.

Mandatory statuses are `PROPOSED`, `APPROVED`, `IMPLEMENTED`, `VERIFIED`, `RELEASED`, `DEFERRED`, `REJECTED`, and `SUPERSEDED`. Status transitions record actor, authority, time and reason.

Change impact analysis traverses both directions from a changed requirement. A post-freeze change must identify affected design decisions, code paths, tests, risks, evidence, release items and operating controls. Acceptance criteria cannot be edited by the implementation actor during repair; changes return to the Specification Factory.

Readiness requires 100% of in-scope approved requirements mapped to acceptance criteria and verification methods. Merge readiness requires all in-scope criteria mapped to passing evidence or a formally authorized, non-blocking disposition.
