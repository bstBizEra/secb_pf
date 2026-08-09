# Repository Intake Contract

Status: Implementation Ready | Version: 1.0.0 | Work Package: `SECB-WP-ENGLOOP-002`

Before mutable Git operations, verify repository provider, immutable repository ID, organization/owner, canonical remote URL, allowed protocols/hosts, default branch, protected-branch rules, expected signing policy, CI contexts, code-owner rules and credential audience.

Fetch uses an allowlisted remote and bounded refspec. Record remote-advertised object IDs, pin the approved starting commit SHA, verify its ancestry and signature requirements, and capture default-branch head. The worktree must be clean or all pre-existing changes must be explicitly inventoried and excluded; user work is never discarded.

Intake fails closed for redirected/unapproved remotes, repository identity mismatch, missing baseline object, shallow history insufficient for policy, unexpected submodule/LFS source, unsafe hooks, suspicious object replacement, unresolved working-tree changes, invalid credentials or unavailable policy services.

Output: signed repository-intake record containing repository ID, remote fingerprint, baseline SHA, default-branch SHA, worktree status, policy version, actor, timestamp and evidence hashes.
