# Release and Tagging Policy

Status: Implementation Ready | Version: 1.0.0 | Work Package: `SECB-WP-ENGLOOP-002`

Release version follows the approved versioning policy and is unique. The annotated tag is signed and points to the authorized merged commit. Changelog entries trace to tickets/PRs and declare security, migration, deprecation and rollback notes.

Trusted build inputs are pinned: source commit/tag, dependencies, builder image, workflow definition and toolchain. Build outputs are immutable and content-addressed. The pipeline generates artifact digest, SBOM, vulnerability results and signed provenance linking builder, inputs and source SHA. Promotion across environments reuses the same artifact digest; rebuilding for production is prohibited unless treated as a distinct, re-certified artifact.

Deployment requires a separate release warrant bound to environment and artifact digest, health criteria, observation window and rollback target. Successful observation produces release evidence. Failed or uncertain health enters `REVERTING`/`HELD`; rollback must be idempotent and independently verified.
