# Merge Warrant Contract

Status: Implementation Ready | Version: 1.0.0 | Work Package: `SECB-WP-ENGLOOP-002`

The Authority Engine issues a short-lived, single-use merge warrant only after deterministic eligibility evaluation. It contains warrant ID, ticket, repository ID, PR ID, target branch, expected base SHA, exact expected head SHA, permitted merge strategy, required check conclusions/digests, approvals, risk tier, issuer, issued/expiry time, nonce and signature.

Immediately before merge, the protected merge controller re-fetches repository/PR identity, base/head SHAs, approval freshness, check results, conflicts, branch protection and warrant status. Any mismatch rejects the operation and invalidates or consumes the warrant according to policy. Compare-and-swap/merge-queue semantics protect against base advancement and time-of-check/time-of-use races.

The controller records requested operation, provider response, resulting merge commit SHA and branch head. If the response is lost, it queries provider state and the side-effect ledger before retry. A warrant cannot authorize tagging, deployment or production release unless those independent authorities are explicitly and separately issued.
