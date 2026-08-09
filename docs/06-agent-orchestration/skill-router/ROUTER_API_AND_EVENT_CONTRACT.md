# Skill Router API and Event Contract

## APIs

- `POST /skill-routes/classify`
- `POST /skill-routes/plan`
- `GET /skill-routes/{route_id}`
- `POST /skill-routes/{route_id}/authorize`
- `POST /skill-routes/{route_id}/execute`
- `POST /skill-routes/{route_id}/validate`
- `POST /skill-routes/{route_id}/fallback`
- `POST /skill-routes/{route_id}/hold`
- `GET /skill-registry/skills`
- `GET /skill-registry/skills/{skill_id}/versions/{version}`
- `POST /skill-registry/compatibility/check`

Commands require idempotency key, expected route version, request/registry/policy hashes and actor identity. Mutating commands also require effective authorization references.

Minimum events: `RequestClassified`, `RegistrySnapshotPinned`, `SkillCandidateRejected`, `RoutePlanned`, `RouteAuthorizationDenied`, `SkillInstructionLoaded`, `SkillInvocationStarted`, `SkillInvocationCompleted`, `TypedHandoffProduced`, `ValidationPassed`, `ValidationFailed`, `FallbackSelected`, `ClarificationRequired`, `RouteHeld`, `RouteCompleted`, `RoutingOutcomeRecorded`.
