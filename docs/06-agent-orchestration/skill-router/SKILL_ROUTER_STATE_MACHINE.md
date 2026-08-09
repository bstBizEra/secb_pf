# Skill Router State Machine

```mermaid
stateDiagram-v2
    [*] --> Classified
    Classified --> Planned: qualified route
    Classified --> ClarificationRequired: material ambiguity
    Planned --> Authorized: preflight passes
    Planned --> Held: gate denied
    Authorized --> Executing
    Executing --> Validating
    Validating --> Completed: acceptance passes
    Validating --> Repairing: bounded correction
    Repairing --> Executing
    Repairing --> Fallback: qualified alternative
    Fallback --> Authorized
    Repairing --> ClarificationRequired: decision required
    Repairing --> Held: limits exceeded
    ClarificationRequired --> Classified: clarified
    Held --> Classified: blocker resolved
```

Every transition binds actor identity, request and registry hashes, route version, preconditions, current authority, budget, expected state, idempotency key, event type, evidence references, failure state and timeout. A registry, policy, skill digest, request, destination or effect change invalidates unconsumed authorization and returns the route to classification or hold.
