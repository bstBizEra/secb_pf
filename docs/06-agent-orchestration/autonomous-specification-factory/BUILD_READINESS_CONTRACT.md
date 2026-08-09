# Build-Readiness and Implementation-Warrant Contract

Status: Implementation Ready | Version: 1.0.0 | Work Package: `SECB-WP-ENGLOOP-002`

## Readiness gate

Readiness passes only when the frozen baseline and signatures validate; requirements and RTM are complete; architecture/ADRs and interfaces are settled; security/privacy/data reviews pass; implementation slices and dependency pins exist; test, evidence, migration and rollback plans are executable; budget and staffing are assigned; all pre-build conditions close; and repository/environment prerequisites are known.

The certificate records `certificate_id`, baseline digest, assessment ruleset/version, result, conditions, assessor identity, evidence bundle, issued/expiry times and revocation status.

## Implementation warrant

The warrant records warrant ID, ticket/work package, exact baseline digest, repository allowlist, path scope, risk tier, permitted tools/actions, budget, branch policy, actor identities, required gates, exclusions, issue/expiry times, revocation conditions and target state. It is signed by the configured authority and accepted only after signature, freshness and scope validation.

Any baseline change, authority expiry, risk escalation, scope drift, dependency integrity failure or certificate revocation suspends execution and moves the episode to `HELD`. Resume requires a newly valid certificate/warrant; warrants are never self-renewed by an executing agent.
