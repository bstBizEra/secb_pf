# Skill Registry and Selection Contract

Each registry entry must declare stable ID, semantic version, instruction digest, status, owner, capabilities, triggers, prerequisites, conflicts, supported platforms/artifacts, risk ceiling, data classes, required tools/credentials, permitted effects, validation methods, budget hints, evidence, provenance and qualification expiry.

Statuses are `CANDIDATE`, `QUALIFIED`, `SUSPENDED`, `REVOKED` and `RETIRED`. Only unexpired `QUALIFIED` versions are routable.

Hard filters apply before ranking. Mandatory capability coverage is a set-cover problem with deterministic tie-breaking. Same frozen request, registry and policy must yield the same selected set and order. The route receipt records included and rejected candidates with reason codes.

Registry admission and modification require the Skill Factory, independent validation, baseline comparison, versioning, rollback and approval appropriate to impact. Runtime history cannot self-admit or silently promote a skill.
