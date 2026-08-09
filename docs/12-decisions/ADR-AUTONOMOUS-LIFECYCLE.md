# ADR — Autonomous Specification and Git Lifecycle

Status: Accepted for Documentation Implementation | Version: 1.0.0
Decision ID: `SECB-ADR-ENGLOOP-002`
Work Package: `SECB-WP-ENGLOOP-002`
Date: 2026-08-08

## Context

The core Engineer Loop defined authority, implementation, verification and release controls but did not provide a complete specification lifecycle or Git operating protocol. Calling the entire lifecycle implementation-ready would overstate coverage.

## Decision

Add two subordinate control-plane modules: Autonomous Specification Factory and Autonomous Git Controller. Keep `ENGINEER_LOOP.md` as the governing end-to-end lifecycle. Bind build warrants to one frozen specification digest; bind merge warrants to exact repository/PR/base/head identities; keep merge and production release authorization separate; fail closed on uncertainty.

## Consequences

The Engineer Loop gains explicit draft/review/ballot/freeze/readiness/change-control and repository/branch/commit/PR/CI/merge/tag/build/deploy/recovery contracts. More evidence, state and approval services are required. Automation becomes safer and reproducible but cannot be considered runtime certified until sandbox tests and independent reviews pass.

## Alternatives rejected

- Embed all details in the main Engineer Loop: rejected for maintainability and unclear ownership.
- Treat CI success as merge/release authority: rejected because technical success does not create authorization.
- Permit mutable approved specifications: rejected because traceability and warrant integrity would fail.
