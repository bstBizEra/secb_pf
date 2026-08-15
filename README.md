# SecB Project Framework

Status: **canonical status lives in
[`docs/00-governance/FRAMEWORK_PRODUCT_DEFINITION.md`](docs/00-governance/FRAMEWORK_PRODUCT_DEFINITION.md)**
— read it there rather than here, so one file can go stale instead of several.

Summarised on three separate axes, measured at `f1b2516`:

| Axis | State |
| --- | --- |
| Framework control | Substantial — 7 executable gates, 175 tests, fail-closed paths covered. Detective only |
| Instance population | Empty for skills — the router is tested against 20 sealed cases and has nothing registered |
| Runtime execution | Absent by design — the delivery loop is specified; no executor runs it |

This line previously understated the framework by a wide margin; the prior wording and
why it survived are recorded once, in the canonical status reference
(`SECB-WP-FWK-072`). The front door states the current position and nothing else —
history kept on a live surface is how a stale claim gets read as a current one.

This folder is the controlled project framework for SecB. It separates governance, design, agent and skill specifications, implementation, verification, operations, and evidence.

## Start Here

1. Read `AGENTS.md`.
2. Establish governance ownership and authority.
3. Approve project scope, requirements, architecture, and risk controls.
4. Register agents, skills, and tools before activation.
5. Execute work only through authorized work packages with verifiable evidence.

## Top-Level Structure

- `AGENTS.md` — mandatory agent operating contract
- `docs/` — governed project documentation
- `src/` — product and platform source code
- `tests/` — automated and manual test assets
- `config/` — non-secret configuration and schemas
- `infra/` — infrastructure as code and environment definitions
- `scripts/` — controlled developer and operational scripts
- `evidence/` — immutable or checksum-verifiable execution evidence
- `templates/` — reusable project artifact templates

## Current Phase

Folder owners, normative documents, controls and implementation artifacts remain subject
to formal review and approval. Stage 2 is `EFFECTIVE` and stage 3 is open with the
authority ceiling at `ARCHITECTURE_APPROVED`; conditions `C-3`…`C-7` are open and
auto-merge is closed. Current values are in the canonical status reference above — not
restated here, because two copies of a status drift.

