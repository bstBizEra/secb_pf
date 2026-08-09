# Autonomous Skill Router and Orchestrator

Status: `IMPLEMENTATION_READY_SPECIFICATION`  
Ticket: `SECB-WP-ENGLOOP-004`  
Source: URE-Loop v1.5, Drive file `1meTS5PZBF8HlIvEkqG2XYOZbUn3vbMZr`  
Authorization: `AUTH-URE-SKILL-ROUTER-20260809-001`

## Objective

Select and sequence the minimum sufficient qualified skills for a frozen request while independently enforcing invocation and external-effect authority.

## Control flow

1. Freeze request profile and governing policy hashes.
2. Classify intent, domain, artifact, platform, risk, actions, side effects and validation.
3. Pin signed registry and compatibility snapshots.
4. Apply hard eligibility filters: status, version, digest, capability, risk ceiling, data class, environment, dependencies and conflicts.
5. Prioritize an explicitly named qualified skill without bypassing gates.
6. Select the deterministic minimum-sufficient set and record rejected candidates.
7. Resolve prerequisite DAG and typed handoffs.
8. Compile invocation, effect, credential, confirmation, validation and fallback contracts.
9. Authorize each invocation; authorize each effect separately.
10. Execute in isolated contexts with durable events and budgets.
11. Validate through tests, readback, provenance and reconciliation.
12. Complete, repair, select a qualified fallback, clarify or hold.

## Deterministic selection

After mandatory capability coverage and hard constraints, optimize lexicographically by: fewest skills, lowest unmitigated risk, strongest qualification, highest validation coverage, fewest external effects, lowest cost/latency, and stable skill ID/version ordering. Advisory outcome scores may break only otherwise equal candidates.

## Authority boundary

Routing can recommend and plan. It cannot create authority, install a plugin, accept terms, obtain credentials, select an unverified recipient/destination, publish, deploy, communicate externally, spend, transact, delete, weaken acceptance criteria or certify its own outcome.

## Completion

Completion requires validated output, reconciled effects, complete receipts, budget accounting, and an evidence chain that explains selection, rejection, execution, validation and outcome.
