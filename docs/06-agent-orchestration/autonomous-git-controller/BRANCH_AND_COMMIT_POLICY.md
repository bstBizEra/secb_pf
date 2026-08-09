# Branch and Commit Policy

Status: Implementation Ready | Version: 1.0.0 | Work Package: `SECB-WP-ENGLOOP-002`

Branch name: `secb/<ticket>/<short-purpose>` using normalized lowercase tokens. Its registry entry contains branch, repository, owner, baseline SHA, path scope, risk tier, created/expiry times, lease/fencing token and warrant ID. Default TTL is seven days unless the work package defines a stricter limit. Protected branches are never direct implementation targets.

Commits must be focused, reproducible, reviewable and attributable. Each message includes the ticket/work-package ID; authorship uses verified workload or human identity. Signing is mandatory for merge-bound commits where repository policy supports it. Generated code, dependency updates, migrations and binary assets require declared provenance.

Before commit, enforce authorized path diff, secret scan, formatting/lint applicable to changed paths, generated-file consistency, test selection and clean staging review. Before push, revalidate remote identity, destination branch, credential scope, branch lease and non-fast-forward policy. Force push is prohibited unless an explicit recovery policy authorizes a non-protected branch and records replaced SHAs; default behavior is create a successor branch.
