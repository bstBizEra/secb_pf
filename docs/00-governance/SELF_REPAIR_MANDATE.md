# SecB Autonomous Self-Research and Self-Repair — integration-first

**Record class:** operator-authored design mandate, recorded in structure.
**Status:** `PROPOSED — RECORDED, NOT ADOPTED`
**Recorded by:** SECB-WP-FWK-117 · **Recorded at:** 2026-08-20

> Records a mandate; does not enact one. No repair grant, compatibility verdict or promotion may cite
> it as authority. Fourth in the series with #187, #203 and #204.

## 1. Objective, as given

> *"Self-repair means restoring a declared integration contract within an existing mandate. It does not
> mean redesigning the framework, creating parallel modules, or expanding authority."*

```text
Reuse → Configure → Adapt → Extend → Create new component only when no existing capability fits
```

The named anti-pattern is *failure detected → invent new module → invent new directory → invent new
identifier → duplicate existing capability*.

## 2. The existing-first rule, as given

Sixteen surfaces must be searched before any external research or file edit — `AGENTS.md`, scope, the
Work Package registry, the identifier taxonomy, the control surface, the knowledge register and layer,
schemas, scripts, tests, policies, **active and unlanded PRs**, superseded branches, ADRs, contracts,
runbooks and manifests.

```text
EXISTING_CAPABILITY_FOUND · PARTIAL_CAPABILITY_FOUND · EXTENSION_POINT_FOUND
ACTIVE_CONTENTION · SUPERSEDED_IMPLEMENTATION · NO_CAPABILITY_WITHIN_BOUNDARY · INVENTORY_INCOMPLETE
```

`INVENTORY_INCOMPLETE` blocks repair planning. Research begins only after the inventory names a precise
unresolved question, and *"research is complete when it closes a declared uncertainty — not when a
token or source-count quota is exhausted."*

## 3. Reproduce before research, as given

```text
REPRODUCED · CONDITIONALLY_REPRODUCED · ENVIRONMENT_SPECIFIC · NONDETERMINISTIC · NOT_REPRODUCED
```

Only the first two may proceed to autonomous code repair. The producer of a repair may not issue its
own compatibility verdict.

## 4. Vocabulary

Verified by `tests/test_mandate_vocabulary.py` (#204). Status vocabulary is closed.

| Prefix | Used for | Registry status |
| :--- | :--- | :--- |
| `R` | R0–R4 repair risk tiers, `risk_tier: R1` | REGISTERED `R0-R4` — used with its registered meaning |
| `KN` | the existing knowledge register, extended | REGISTERED `KN-001..KN-005` |
| `SECB-WP` | `SECB-WP-FWK-095` module provenance | REGISTERED |
| `C` | *(named only to forbid it for repair risk)* | REGISTERED `C0-C5`, conflict impact |

### 4.1 This is the first mandate that introduces no colliding vocabulary

```text
#187  Stage 0-9 unregistered
#203  K0-K9 vs K-01..K-12 KPIs · risk_class C2 vs R0-R4 · a KN register that already ships
#204  A1-A5 vs A0-A4 authority · G-ABSORB vs G0-G5 · GATE-001..010 unused
#117  none
```

Measured: **zero new ladder prefixes**, and every prefix used carries its registered meaning. §5 of the
mandate says *"do not introduce a new identifier ladder … register any new prefix before use"*, and §20
says *"use `R0–R4`, not `C0–C5`, for repair risk"* — naming the exact substitution #203's disposition
resolved.

Three episodes produced the standing check in #204. The fourth mandate arrived clean. Recorded because
a control that changes behaviour is worth more than one that only reports.

The three proposed `secb.module/v1`, `secb.integration-contract/v1` and `secb.repair-profiles/v1` are
**schema ids, not ladders** — the same shape as the six kernel schemas in #171, and outside the
registry's ladder boundary.

## 5. The integration matrix, verified

§10 asserts four verdicts. Measured against `main@ace1e57` and the live pull requests:

| Consumer → Provider | Asserted | Measured |
| :--- | :--- | :--- |
| Verdict evaluator → Context Receipt | `DEPENDENCY_BLOCKED` | **CONFIRMED** — `schemas/context-receipt.schema.json` absent on `main`, present in #171 |
| Learning schema → base `schemas/` | `ORDERING_BLOCKED` | **CONFIRMED** — `schemas/` absent on `main` |
| Rego policies → OPA evaluator | `INCOMPATIBLE_DESIGN` | **CONFIRMED, with a refinement** — see §5.1 |
| Knowledge candidates → KN register | `DUPLICATE_CAPABILITY` | **CONFIRMED, with a refinement** — see §5.1 |

### 5.1 Two rows describe proposals, not present states

```text
.rego files in the repository            0
OPA or Rego evaluator                    0 files
.rego files added by #204                0
knowledge/ paths in the repository       0
```

Both verdicts are correct about the **mandates' proposals** and would be wrong if read as descriptions
of the tree.

```text
PROPOSED_INCOMPATIBILITY ≠ PRESENT_INCOMPATIBILITY
```

Both are also already dispositioned: #204's record states the eleven `.rego` files would be inert
configuration for an absent engine, and #203's operator disposition resolves the parallel tree to
*extend `KN-*`, do not create*. So the matrix reflects the state before those dispositions, and its
`DUPLICATE_CAPABILITY` row is now a closed finding rather than an open one.

## 6. A circuit breaker already in force

§25 stops autonomous repair when *"external platform failure is misclassified as code failure"*, and §8
gives the example directly:

> *"GitHub billing prevents workflow startup ≠ application integration failure ≠ test failure"*

That is the condition currently in force. GitHub Actions has refused every job since 2026-08-19T09:25
with *"recent account payments have failed or your spending limit needs to be increased"*, and no
product code was edited in response — the block was reported as an external dependency under the
production mandate's §7.5. The breaker describes behaviour the loop already exhibited rather than
behaviour it needs to acquire.

## 7. What this document is not

- Not an adoption. No repair grant or compatibility verdict may cite it as authority.
- Not a scope change against the frozen `SECB-SCOPE-001`.
- Not an authorization to build the integration plane. §24 says so itself: *"this workflow is a target
  design only. Building it before #171 lands and the mandates are adopted would violate the established
  Lean sequencing."* §23 repeats it for the skills.
- Not a claim that §4 or §5 is complete — measured at one commit, by one agent, no independent
  verification.
