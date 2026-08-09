# Work Package — SECB-WP-ENGLOOP-MVP-001

Title: Engineer Loop v1.5 Skill Router Sandbox Certification  
Status: `AUTHORIZED_FOR_R1_SANDBOX_EXECUTION`  
Target State: `IMPLEMENTATION_READY → SANDBOX_TESTED`  
Date: 2026-08-09

## Objective and value

Implement and verify a side-effect-free reference vertical slice of the v1.5 Autonomous Skill Router so that the design can be assessed against FIT-101–120 using reproducible sandbox evidence.

## Scope and exclusions

In scope: deterministic minimum-sufficient selection, named-skill priority, prerequisites, typed handoff gates, invocation/effect separation, confirmation, recovery, budget hold, event integrity and anti-poisoning.

Excluded: plugin installation, external communication, credentials, payments, deployment, repository push/merge, production data, production policy adoption and production autonomy.

## Roles and authority

- Owner / approver: Authorized SecB project representative
- Executor: Codex sandbox implementation agent
- Independent reviewer: Required before final certification; unassigned at execution start
- Risk tier: `R1`
- Authority source: User instruction dated 2026-08-09 to proceed with `IMPLEMENTATION_READY → SANDBOX_TESTED`

## Dependencies and risks

Dependencies: Engineer Loop v1.5 contracts, FIT-101–120, Python 3.12 standard library. Risks: reference-model divergence, incomplete negative tests, self-review bias, and accidental overstatement of production readiness.

## Acceptance criteria

1. FIT-101–120 execute with unique, continuous identifiers and all pass.
2. Repeated runs are deterministic.
3. No network, credential, subprocess, repository mutation or external side effect is used by the router.
4. Evidence contains commands, outputs, timestamps, hashes and environment identity.
5. Static safety inspection finds no prohibited effect path.
6. Independent review accepts architecture, security and evidence, with zero blocking findings.

## Test and evidence plan

Run Python unit tests twice, compile all Python files, parse all seven v1.5 JSON schemas, inspect imports and prohibited calls, hash governed inputs and outputs, and seal an evidence manifest. A failed or inconclusive gate results in `HOLD` or `SANDBOX_TESTED_PENDING_INDEPENDENT_REVIEW`.

## Budget and circuit breakers

Maximum 60 minutes, 25 agent turns, 80 tool calls, six retries and one worker. Stop immediately on authority, scope, integrity, secret, or uncontrolled-side-effect failure.

## Rollback and recovery

The sandbox is additive and isolated under `sandbox_mvp/`. Recovery is deletion or archival of this directory after preserving evidence. No baseline file is replaced until certification gates pass.

## Promotion decision rule

Automated test success alone cannot produce final `SANDBOX_TESTED`. Independent architecture/security/evidence review is a mandatory certification dependency.

