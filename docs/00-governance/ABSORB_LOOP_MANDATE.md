# SecB Agentic Absorb Loop — SECB-ABSORB-LOOP-001

**Record class:** operator-authored mandate, recorded in structure.
**Status:** `PROPOSED — RECORDED, NOT ADOPTED`
**Recorded by:** SECB-WP-FWK-116 · **Recorded at:** 2026-08-20

> This document **records** a mandate. It does not enact one. No closure gate, delivery receipt or
> knowledge snapshot may cite it as authority. Third in a series with
> `PRODUCTION_ADVANCEMENT_MANDATE.md` (#187) and `AGENTIC_LEARNING_LOOP_MANDATE.md` (#203); the
> separation between recording and adopting is the same, and required by `PA-03`.

## 1. Mandate, as given

Every implementation cycle includes a mandatory Absorb Loop capturing errors, bugs, successful
patterns, failed approaches, repair sequences and execution measurements.

> *"No implementation cycle is complete until its execution evidence has been absorbed, classified,
> reconciled, and delivered to the Knowledge Hub — or an explicit `NO_REUSABLE_LEARNING` receipt
> proves that no framework-relevant learning was found."*

**A — Acquire · B — Bind · S — Structure · O — Observe and evaluate · R — Reuse or recommend ·
B — Broadcast.** Broadcast means delivery to controlled Hub intake, never activation.

## 2. The structural argument, as given

Learning that runs only nightly loses what the cycle knew: failed approaches vanish from the final
pull request, retries overwrite the original failure, and repair rationale is reconstructed rather
than recorded. Hence three tiers — inline absorb during execution, closure absorb at Work Package
close, background consolidation across episodes.

## 3. The closure gate, as given

`G-ABSORB` blocks `CLOSED` until the episode exists, original failures were preserved, retries were
classified, root-cause status is explicit, candidates were delivered, secrets were checked, the
receipt binds to the result tree, no contradiction is hidden, and a `DELIVERED` or justified
`NO_REUSABLE_LEARNING` verdict exists.

```text
ABSORB_PASS · ABSORB_INCOMPLETE · ABSORB_CONTAMINATED · ABSORB_CONTRADICTED · ABSORB_DELIVERY_FAILED
```

Only `ABSORB_PASS` permits closure. The mandate is explicit that `if: always()` must not let the
absorb job report success when upstream evidence is missing — it must emit `ABSORB_INCOMPLETE`.

```text
JOB_RAN ≠ EVIDENCE_WAS_ABSORBED
```

## 4. Hub zones and snapshots, as given

```text
knowledge-hub/  intake/ (untrusted) → validated/ → compiled/ → active/
```

Execution observations are never written directly into `active/`. Every cycle binds an immutable
Knowledge Snapshot, and an active cycle never changes its configuration mid-execution — which is what
makes replay meaningful.

## 5. The escalation ceiling, as given

Never self-activating: authority changes, constitutional changes, removal of hard gates, weakening of
evidence, expansion of production permissions, acceptance of irreversible risk, or a policy that would
authorize its own adoption. Producer, validator and promoter are separate logical roles.

These match this repository's existing invariants rather than extending them.

## 6. Vocabulary

Declared so the claims below are checkable. Verified against `config/identifier_taxonomy.json` by
`tests/test_mandate_vocabulary.py`.

| Prefix | Used for | Registry status |
| :--- | :--- | :--- |
| `A` | A1–A5 inline absorb checkpoints | COLLIDES — registered `A0-A4`, authority ladder tiers |
| `G` | `G-ABSORB` closure gate | COLLIDES — registered `G0-G5`, change classes |
| `GATE` | *(unused by the mandate)* | REGISTERED `GATE-001..GATE-010` — the existing gate prefix |
| `IC` | IC-01…IC-03 cycle steps | NEW |
| `SECB-PAT` | SECB-PAT-GIT-004 pattern ids | NEW |
| `SECB-KS` | SECB-KS-00042 knowledge snapshots | NEW |
| `SECB-ABSORB` | SECB-ABSORB-0001 delivery receipts | NEW |
| `SKILL` | SKILL-SQUASH-EXPECTED-TREE-001 | NEW |

### 6.1 The `A` collision reuses a contested identifier

`A` is bound to the authority ladder `A0-A4`. The mandate's inline checkpoints run `A1` through
**`A5`** — and `A5` is the exact value issue #184 is about, where `secb.yaml` records
`target_autonomy: A5` above the envelope's `absolute_ceilings.max_tier: A4`.

So `A5` would carry three meanings in one repository: a tier the envelope cannot grant, a capability
target, and an absorb checkpoint.

### 6.2 A gate prefix already exists

`GATE-001..GATE-010` is registered for verdict validation rules. The mandate names its gate
`G-ABSORB`, taking the change-class prefix instead of the gate prefix.

## 7. Measured baseline

Measured against `main@ace1e57`.

```text
knowledge-hub/                ABSENT      framework/config/            ABSENT
policies/learning/            ABSENT      11 proposed workflows        0 exist
.github/workflows/reusable/   ABSENT      14 proposed learning agents  0 exist
```

The mandate also proposes eleven `.rego` policy files. **No OPA or Rego evaluator exists**, and
SECB-WP-FWK-105 (#181) deliberately declined to adopt one: NFR-12 restricts enforcement scripts to
the standard library and CI installs only pytest, so `.rego` files would be inert configuration for
an engine that is not present. `POLICY_INTERFACE_PRESERVED ≠ OPA_ADOPTED`.

## 8. What this document is not

- Not an adoption. No gate, receipt or snapshot may cite it as authority.
- Not a scope change against the frozen `SECB-SCOPE-001`.
- Not an authorization to build the Absorb plane. Under the Lean minimality ladder, eleven workflows
  and fourteen agents while Stage 0 has not exited is premature.
- Not a claim that §6 or §7 is complete — both are measured at one commit, by one agent, with no
  independent verification.
