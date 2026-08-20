# SecB Agentic Learning Loop — SECB-AGENTIC-LEARNING-LOOP-001

**Record class:** operator-authored mandate, recorded in structure.
**Status:** `PROPOSED — RECORDED, NOT ADOPTED`
**Recorded by:** SECB-WP-FWK-115 · **Recorded at:** 2026-08-20
**Source:** operator instruction, this repository's session channel.

> This document **records** a mandate. It does not enact one. No knowledge object, capability
> candidate or promotion verdict may cite it as authority. Recording is separated from adoption for
> the same reason `PRODUCTION_ADVANCEMENT_MANDATE.md` (SECB-WP-FWK-107) separates them: a proposal
> that arrives and is simultaneously acted upon has no reviewable moment, and `PA-03` forbids a
> policy proposal activating itself.

---

## 1. Objective, as given

Add a governed learning plane that converts execution experience into validated reusable knowledge
and controlled framework improvements.

> *"SecB shall learn from every authorized execution, but no learned output becomes authority merely
> because an agent generated it or because it improved one result."*

The invariant the mandate rests on:

```text
Knowledge ≠ policy      Policy ≠ authority      Authority ≠ tool access
```

## 2. The knowledge ladder, as given

Ten levels, K0 through K9 — raw event, observation, episode, lesson candidate, validated knowledge,
capability candidate, shadow-validated capability, active capability, stable capability,
deprecated/retired. Authority is `None` through K6, `Scoped operational` at K7, `Scoped reusable` at
K8, `None` again at K9.

**This ladder's prefix collides with a registered one. See §6.**

## 3. Two loops, as given

**Hot path** — during or immediately after execution. May modify only task-local working memory, the
temporary plan, the hypothesis queue, retry strategy, and tool selection within the existing
allowlist. Must not modify `AGENTS.md`, effective policies, authority grants, active schemas,
production runbooks, security thresholds, or merge and deployment gates.

**Cold path** — after closure or on schedule. Qualification → pattern detection → causal analysis →
lesson extraction → deduplication → contradiction analysis → knowledge candidate → capability
candidate → evaluation → shadow validation → promotion or rejection. This is the primary self-upgrade
mechanism.

## 4. Promotion, as given

```text
CANDIDATE → SCHEMA_VALID → SANDBOX_TESTED → ADVERSARIAL_TESTED → SHADOW_VALIDATED
          → CANARY_ACTIVE → ACTIVE_SCOPED → STABLE
failure:  REJECTED · REGRESSED · QUARANTINED · ROLLED_BACK · SUPERSEDED · EXPIRED
```

Promotion requires improvement above a minimum effect **and** zero hard regressions **and** no
authority expansion **and** complete evidence. A higher aggregate score cannot compensate for
unauthorized action, secret exposure, false closure, security regression, evidence loss, or a failed
production rollback.

The mandate's own escalation ceiling, which matches this repository's existing invariants:

```text
policy change     → no self-activation
authority change  → never through the learning loop
a learning agent  → cannot validate its own candidate
```

## 5. Measured baseline at recording time

Measured against `main@ace1e57`, not asserted.

```text
PROPOSED STRUCTURE                        STATE ON MAIN
knowledge/                                ABSENT
agents/learning/                          ABSENT   (agents/ itself absent)
tools/learning/                           ABSENT   (tools/ itself absent)
skills/learning/                          ABSENT   (skills/ itself absent)
schemas/learning/                         ABSENT   (schemas/ arrives with #171, unlanded)
.github/workflows/reusable/               ABSENT
13 proposed workflows                     0 exist
9 proposed learning schemas               0 exist
```

Nothing in the proposed learning plane exists. `schemas/learning/` in particular cannot be created
before `schemas/` does, and that directory arrives with unlanded #171 — so **LL-01 is blocked on the
same merge gate as Stage 0**.

## 6. Vocabulary collisions — measured against the identifier registry

`config/identifier_taxonomy.json` records 26 ladders and 5 collisions. Four findings:

### 6.1 `K` is already bound, to Key Performance Indicators

```text
registered   K-01..K-12 (with a/b/c splits) — "Key performance indicators"
             home docs/01-requirements/KPI_BASELINE.md
mandate      K0..K9 — the knowledge ladder
```

The mandate's **§18 also defines KPIs**, so both meanings of `K` would be live inside one document.

### 6.2 `risk_class: C2` uses the wrong ladder

```text
registered   R0-R4 — "Risk tiers -- how much damage a change can do"
             home docs/00-governance/RISK_AUTHORITY_MATRIX.md
registered   C0-C5 — "Conflict impact ladder", already carrying THREE recorded live meanings
mandate      capability_candidate.risk_class: C2
```

This is not only a collision. `R` is the registered ladder for exactly the concept `risk_class`
names, so `C2` appears to be a transcription of a risk tier onto a conflict-impact prefix.

### 6.3 A knowledge register already exists

```text
registered   KN-001..KN-005 — "Knowledge register entries"
             home docs/13-evidence/KNOWLEDGE_REGISTER.md
also present docs/13-evidence/KNOWLEDGE_LAYER.md
mandate      SECB-KNOW-001 objects under a new knowledge/ tree
```

The mandate proposes a parallel knowledge system without referencing the one that ships. Under the
mandate's own §14 conflict handling this is the `DUPLICATE` verdict, and under §6 of the production
mandate — *"avoid duplicate or superseded work"* — it is the case that rule exists for.

### 6.4 Five prefixes are new and unregistered

`KC` (knowledge candidate) · `CC` (capability candidate) · `LL` (implementation sequence) ·
`SECB-KNOW` · `EPISODE`.

Registration is owed under the sequence recorded in the identifier-registration issue: **home → use →
register**. This document is the home; none is in use yet.

## 7. What this document is not

- Not an adoption. No promotion verdict, knowledge object or capability candidate may cite it.
- Not a scope change. Reconciling it against the frozen scope `SECB-SCOPE-001` is a separate act.
- Not an authorization to build the learning plane. Under the Lean minimality ladder, building nine
  schemas and thirteen workflows while Stage 0 has not exited would be premature.
- Not a claim that §5 or §6 is complete. Both are measured at one commit by one agent, with no
  independent verification.
