# Baseline and Freeze Policy

Status: Implementation Ready | Version: 1.0.0 | Work Package: `SECB-WP-ENGLOOP-002`

## Canonical baseline

The Baseline Service orders files by normalized relative path, normalizes approved text encoding/line endings, excludes non-governed transient data, hashes every file with SHA-256, creates a manifest, hashes the manifest, and records producer identity, timestamp, tool version and source revisions. The approver signs the manifest digest.

Freeze succeeds only when approvals are valid, blocking findings and pre-freeze conditions are closed, all links resolve to immutable versions, RTM validation passes, and the canonicalization run is reproducible. The output is `baseline_id`, `specification_version`, `manifest_sha256`, signature set and evidence reference.

## Freeze rules

- Frozen bytes are immutable and retained.
- Mutable external references must be snapshotted or pinned by digest/version.
- Re-running canonicalization over the same inputs must produce the same digest.
- Any hash or signature mismatch enters `HELD` and opens an integrity incident.
- The baseline remains usable only while its approvals, dependencies and build-readiness certificate are current.

An implementation warrant must carry the exact baseline digest; prefix matching, latest-version lookup and implicit upgrades are prohibited.
