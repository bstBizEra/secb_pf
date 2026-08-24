# Engineer Loop Security Threat Model

Status: Implementation Ready
Version: 1.0.0
Work Package: `SECB-WP-ENGLOOP-001`

## Protected Assets

Authority decisions, identities and credentials, source and build outputs, policy, state, budgets, evidence and side-effect ledgers, secrets, customer/regulated data, deployment environments, skills/tools/models, and audit history.

## Threats and Required Controls

| Threat | Primary controls | Security veto condition |
|---|---|---|
| Forged or stale authority | Signed/time-bound decisions, revalidation, revocation | Unverifiable identity/authority |
| Privilege or scope escalation | Capability broker, deny-by-default, scoped identity | Out-of-envelope request |
| Prompt/instruction injection | Source trust labels, quarantine, policy separation | Untrusted content influences authority or tools |
| Sandbox escape | Rootless isolation, restricted mounts/network, hardened images | Isolation control failure |
| Secret disclosure | Brokered credentials, redaction, secret scanning, revocation | Secret persisted or exposed |
| Evidence tampering | Append-only store, hashes, signed manifest, independent verification | Hash/provenance mismatch |
| Duplicate/ambiguous side effect | Idempotency ledger, reconciliation, compensation | Unreconciled external state |
| Concurrent overwrite | Leases, fencing tokens, optimistic versions | Stale writer accepted |
| Supply-chain compromise | Lockfiles, hashes, SBOM, trusted registry/runner, provenance | Untrusted dependency/build origin |
| Malicious or compromised agent/tool | Least privilege, typed contracts, output validation, audit | Deterministic gate bypass attempt |
| Agent output rendered to a human | Egress sanitization of active content (raw HTML, `javascript:`/`vbscript:`/`data:` URIs in links, images and autolinks); render agent output as inert text; no auto-execution in operator clients | Active content reaches an operator client unsanitized |
| Denial of service/cost exhaustion | Quotas, hard budgets, queue controls, breakers | Metering/control unavailable |
| Unauthorized merge/release | Separate identities and approvals, protected branches/environments | Missing/expired effective approval |
| Log/privacy leakage | Data minimization, classification, redaction, retention | Protected data outside approved store |
| Rollback sabotage | Immutable artifacts, tested runbooks, dual control | Recovery path unavailable for high-risk change |

## Security Requirements

- Agents are not trusted principals for binding approvals.
- Every tool invocation is policy-evaluated and linked to episode/state/budget.
- Production credentials are never available to implementation agents.
- Control-plane service outage blocks privileged mutations.
- High-impact risk acceptance cannot waive identity, authority, evidence integrity, or legal controls.
- Security findings use a defined severity model; Critical/High findings block promotion unless the approved policy explicitly permits a time-bound acceptance and the control is waivable.

## Security Review Triggers

Authentication/authorization, cryptography, secrets, sensitive data, external tools/MCP, network egress, sandbox changes, dependencies/build systems, policy/evidence logic, database migrations, infrastructure, merge automation, or release capability.

## Residual Risk

Implementation readiness does not prove isolation, cryptographic integrity, provider security, or recovery effectiveness. These remain open until control implementation, penetration/security testing, failure injection, and independent certification are completed.

