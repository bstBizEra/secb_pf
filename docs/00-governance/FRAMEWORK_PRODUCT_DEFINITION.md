# SecB PF — framework product definition

```yaml
product_id: SECB-PF
product_type: GOVERNANCE_AND_ENFORCEMENT_FRAMEWORK
unit_of_value: an executable, evidence-producing delivery loop
primary_consumers: downstream BST project instances
not_an_application_runtime: true
work_package: SECB-WP-FWK-072
canonical_status_reference: true
```

> **This document is the canonical status reference.** Any other document stating the
> framework's phase, maturity or counts must cite this file rather than restate it. Phase
> prose duplicated across documents is how `README.md` came to say *"Skeleton / Draft"*
> for a framework with 51 commits and seven executable gates.

## What the product is

SecB PF is not an application. Its product is the **governed delivery loop** — a reusable
governance, evidence and enforcement spine that a downstream project instantiates. An
instance receives authority classification, work-package binding, budget circuit-breaking,
evidence discipline, stage gates and explicit limits without rediscovering the control
model.

## Measured state of the effective base

```yaml
as_of_ref: f1b2516688f94c7aad9a0b1b9c060abd023c86bf
projection: EFFECTIVE_MAIN
binding: true
observation_boundary: "tracked files at as_of_ref; excludes open pull requests"
commits: 51
enforcement_scripts: 7
test_modules: 12
tests_passing: 175
numbered_documentation_domains: 18
json_schemas: 14
skill_registry_instances: 0
current_tier: A1
ballot_layer: NOT_ACTIVE

# How these counts were, and were not, checked (SECB-WP-FWK-078)
verification_status: NOT_VERIFIED_BY_CI
recomputation_evidence: LOCAL_FULL_CLONE_ONLY
required_checkout_profile: ANCESTRY_PATH
ci_checkout_profile: HEAD_ONLY
required_history_assertions_executed: 0/5
```

**The green Test job must not be cited as evidence for the counts above.** CI checks out
with `fetch-depth: 1`, so the cited commit is not in its object store and all five
recomputation assertions **skip**. They are named `test_advisory_*` for that reason, and a
required assertion in this repository may never skip its way to green:

```text
honest skip reason  ≠  verification
zero failures       ≠  zero required observations omitted
```

The counts are recomputed on a full clone, and that is the whole of their evidence today.
Two further boundaries, stated because each could be mistaken for coverage:

- `rev-list --count` and the ancestor proof need **ancestry**, not merely the objects.
  Fetching `as_of_ref` alone would fix `ls-tree` and still leave history unproven.
- On a `pull_request` event `actions/checkout` builds a **synthetic merge commit**, so the
  tree CI tested is not the PR head it is reported against.

Full history is not switched on here without measuring its cost, and the job that would
carry it lives in `ci.yml`, which PR #134 already claims. Tracked as `SECB-WP-FWK-078`.

```text
PROPOSED_HEAD evidence  ≠  EFFECTIVE_MAIN capability
```

Every count above is measurable from `as_of_ref` alone, and
`tests/test_framework_product_definition.py` recomputes them. **A count with no `as_of_ref`
is not a measurement**, and a count taken from an open pull request is not a property of
this framework: the 209 tests reported during review of PR #123 belong to that head, not
to `main`.

## Three readiness axes, measured separately

```text
FRAMEWORK_CONTROL_READINESS
  ≠ INSTANCE_POPULATION_READINESS
  ≠ RUNTIME_EXECUTION_READINESS
```

| Axis | Measures | State at `as_of_ref` |
|---|---|---|
| **Framework control** | Whether reusable contracts, gates, schemas, evidence rules and tests exist and work at their declared strength | **Substantial.** 7 gates wired into CI, 175 tests, fail-closed paths covered per `NFR-01`. Detective only — branch protection returns `403` on this plan (`NFR-13`) |
| **Instance population** | Whether a downstream project has named authority, its own envelope, populated registries, executor bindings, triggers, stage evidence and identity separation | **Empty for skills.** `skill_registry_instances: 0`. The router is tested against 20 sealed FIT cases and has nothing registered to route |
| **Runtime execution** | Whether executors, external effects, preventive admission control, rollback and telemetry exist | **Absent by design.** The 35-step engineer loop is specified; no executor runs it. SecB can be a reusable framework while remaining non-deployed |

**A tested router with no registry is mechanism-ready and population-empty.** Reporting one
axis as the other is the error this table exists to prevent — a strong mechanism does not
make an operational capability.

## Lifecycle position

```yaml
stage_2: EFFECTIVE          # 2026-08-12T17:33:16Z, ratified by c94e4da
stage_3: OPEN
authority_ceiling: ARCHITECTURE_APPROVED
open_conditions: [C-3, C-4, C-5, C-6, C-7]
auto_merge: CLOSED
```

`C-6` and `C-7` gate the next autonomous canonical merge. Nothing in this document closes,
advances or grants any of it.

## How it was built — measured construction timeline

Each entry cites work packages that are merged at `as_of_ref`, so the arc is reproducible
with `git log`.

| Window | Work packages | What landed |
|---|---|---|
| 2026-08-09 | `FWK-001`…`004` | Baseline under version control, **first two gates made executable**, budget circuit breaker. Enforcement preceded documentation |
| 2026-08-10 | `FWK-005`…`034` | PRD, router v1.5.1 with `registry_hash`, **Genesis Bootstrap (`FWK-012`)** — still the envelope's `authority_source` — the 12+2 stage lifecycle, requirement and NFR catalogues, Specification Conflict Protocol, Two-Plane Decision Model |
| 2026-08-11 – 12 | `FWK-035`…`054` | Recount of every KPI from source; **Wilson replaces `3/n`** after `3/n` proved optimistic above n≈13.7; identifier taxonomy; prohibited-call and committed-secret scans mechanized |
| 2026-08-13 – 14 | `FWK-049`…`060` | Stage-2 composite verdict, control-surface staleness, a false provenance claim stripped, stage 2 stamped `EFFECTIVE` |

Two habits define the framework more than any feature:

1. **Measure before adopting.** External frameworks are assessed against the framework in
   force before installation — the commit subjects say so verbatim.
2. **Improve by self-falsification.** A large share of work packages correct SecB's own
   prior claims. The recurring defect is a claim stronger than its mechanism; the mirror
   defect — `NFR-17` and this README's *"Skeleton / Draft"* — is a claim **weaker** than
   its mechanism, and is the same fault.

## Projection discipline

Every count, maturity statement or readiness claim in any governed document carries:

```yaml
as_of_ref: <full commit or immutable artifact digest>
projection: EFFECTIVE_MAIN | PROPOSED_HEAD | HISTORICAL
measured_at_utc: <timestamp>
binding: <true|false>
observation_boundary: <paths or data included>
```

## Known duplication, not yet removed

`docs/01-requirements/NFR_CATALOGUE.md` still carries `Status: Stage 2 in progress` in its
header, which contradicts stage 2 being `EFFECTIVE`. **Deliberately not corrected here.**
That file is claimed by two open pull requests (#121 and #132) at other hunks, and a third
claimant would create semantic contention for a one-line fix that is not urgent. It is
recorded so the duplication is visible rather than forgotten, and it is the reason this
document declares itself the canonical status reference.
