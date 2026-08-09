# Skill Orchestration and Typed Handoff Contract

The orchestrator converts selected skills into a version-pinned DAG. Each node declares input schema, output schema, instruction digest, authority requirement, isolation boundary, budget, timeout, retry class, idempotency strategy, validation contract and failure transition.

Handoffs contain producer/consumer IDs, payload schema and digest, provenance, taint, data classification, redactions, authority constraints, freshness, validation status and evidence references. Consumers must reject mismatched schemas, stale or untrusted provenance, prohibited classifications, or payloads attempting to become privileged instructions.

Parallel execution is allowed only for independent nodes with compatible locks and budgets. Side effects execute through the durable Side-Effect Gateway. Unknown outcomes are reconciled before retry. A fallback creates a new route version and requires fresh authorization.
