# Autonomous Authority Model — `AR` routes, EBTA, and the agentic team

Work package: `SECB-WP-FWK-057` · Issue: #112 · Recorded: 2026-08-13
Authority: operator disposition of 2026-08-13, `CONFLICT-SECB-AUTONOMY-001`
Status: **`RATIFICATION_PENDING`** · `binding: false` until PR #113 merges
Design baseline only — **nothing here is implemented**

> **Read §9 before §5.** This document describes how autonomous material merges
> become authorized. The platform cannot yet satisfy any of it, and a reader who
> stops at the EBTA conjunction will believe SecB has a control it does not have.

## 1. Three namespaces, kept apart

```text
NS = what the change touches          (NS0-NS3, registered)
AR = how the change is authorized     (AR0-AR4, registered here)
BM = which outcomes are delegated     (config/business_mandate.json)
D  = historical decision classes      (D0-D4, meaning unchanged)
```

`D0`–`D4` is **not reinterpreted.** Every existing `D2` citation keeps its meaning.
Rebinding it would make every prior record ambiguous — the defect
`config/identifier_taxonomy.json` exists to prevent, and the reason `NS` took a free
prefix too.

## 2. Authorization routes

| Route | Change | Authorization |
|---|---|---|
| `AR0` | Deterministic or generated | Deterministic gates |
| `AR1` | Routine engineering | Agent + deterministic gates |
| `AR2` | Material engineering | Independent agent verification **+ EBTA certificate** |
| `AR3` | Impact reaching business outcomes | A standing mandate that **covers the impact** |
| `AR4` | Outside the mandate, or prohibited | **No autonomous path.** Preserve safe state and report |

**`AR4` is not an escalation route.** An agent meeting `AR4` does not ask for
permission and wait; it preserves state and reports, because a request to widen the
mandate is a business act the agent may not initiate.

The classifier assigns `NS`. The route follows from `NS` **and** the mandate. **A
classifier may never widen a mandate** — it may only route a decision to authority
that already exists.

## 3. Evidence-Backed Technical Authorization

An `AR2` change may merge autonomously when **every** conjunct holds:

```text
AUTHORIZED = E ∧ C ∧ T ∧ S ∧ A ∧ R ∧ B ∧ P ∧ F
```

| | Proof required |
|---|---|
| `E` | Inside the business mandate |
| `C` | Semantic classification complete, no `NS_REVIEW_REQUIRED` |
| `T` | Tests and acceptance criteria pass |
| `S` | Security and invariant checks pass |
| `A` | Adversarial verifier raised no unresolved veto |
| `R` | Rollback or compensation ready |
| `B` | Budget and absolute ceiling pass |
| `P` | Policy from the **base branch** passes |
| `F` | Final tree and post-merge state re-derivable |

It is a **conjunction, not a score.** Nine proofs, any one failing denies. No
weighting, no majority, nothing tradeable — because the failure mode being designed
against is exactly the plausible-sounding aggregate that hides one missing proof.

**Agent opinions are supporting evidence; a deterministic controller issues the
certificate.** This is the load-bearing distinction between EBTA and the
three-ballot proposal that was rejected: agents can fail in correlated ways —
identical training, identical framing, identical blind spots — so majority voting
and self-verification are least reliable exactly where they matter most. **More
votes is not more evidence.** A conjunction of machine-checkable proofs does not
average away a defect.

Every certificate binds `base_sha`, `head_sha`, `canonical_diff_sha256`,
`evidence_set_sha256`, `policy_bundle_sha256` and `business_mandate_sha256`. Any
head change staleness the whole certificate.

## 4. The agentic engineering team

| Agent | Owns | May not |
|---|---|---|
| Orchestrator | Task selection, decomposition, dependencies | Merge |
| Architect | ADRs, contracts, invariants, design | Approve its own work |
| Builder | Code, migrations, docs, first tests | Issue an EBTA |
| Independent verifier | Verification built and run from a clean context | Write to the production branch |
| Adversarial agent | Refuting claims, probing failure modes | Approve anything — **veto only** |
| Release controller | Evaluating EBTA, merging | Write implementation |
| Operations agent | Monitoring, rollback, incident repair | Widen the mandate |
| Knowledge agent | Turning defects into fixtures, tests, rules | Alter historical evidence |

The adversarial agent holds **veto without approval** on purpose. An agent that can
approve has an incentive to find the change acceptable; one that can only veto does
not.

## 5. Independence must be structural, not labelled

**Different roles on one principal are not independent principals.** Required:

- Separate container or worktree per role
- Separate context and prompt mandate
- The builder cannot see the verifier's scratch reasoning
- The verifier derives evidence from repository state, not from the builder's claims
- Model diversity where available; where a single model family is used, declare
  **`CORRELATED_MODEL_RISK`** rather than implying independence
- The final controller reads structured artifacts only
- Builder, verifier and merger hold **distinct workload identities**
- Every ballot binds the same SHA and digests

Target identity separation:

```yaml
builder_app:   { feature_branch: write, main: none }
verifier_app:  { contents: read, checks: write }
release_app:   { contents: read, merge: conditional, implementation_write: none }
```

**None of this exists.** SecB has one identity, which is why `MULTI_ROLE_SINGLE_PRINCIPAL`
is the honest label for anything attempted today.

## 6. Meta-governance — the agent may improve the framework, with delayed activation

An agent may autonomously land a governance change only when it does **not** widen
the mandate, add external privilege, raise a spending ceiling, or reduce a security
or rollback requirement — and when:

```text
PROPOSE POLICY N+1 → EVALUATE WITH POLICY N → SHADOW → COMPARE → ACTIVATE N+1 → RETAIN N
```

Policy `N+1` never judges the pull request that introduces it, and activation is the
**next epoch**. This generalizes `scripts/check_dual_policy.py`, which already
evaluates every change under both incumbent and proposed logic — the mechanism
exists, the epoch discipline does not.

Raising the mandate envelope needs a **new mandate**. It does not need a human to
review the implementation that follows.

## 7. What the human does after ratification

Business objective · priority · acceptance outcome · KPIs · financial and resource
envelope · risk tolerance · prohibitions · legal and external commitments.

**Not** architecture, security design, test sufficiency, code quality, merge
readiness, deployment mechanics, or incident remediation.

## 8. What is kept from the earlier assessment

`DAAF v2.0` remains **`NOT_ADOPTED_AS_FRAMEWORK`** · `NS0`–`NS3` stands ·
append-only decisions after effectivity · claim references for numeric assertions ·
the authority-ceiling / admission separation · the 797-line size disclosure ·
`EL1_DETECTIVE` as the honest enforcement label. The reversal is confined to the
`D2+` human-ratification rule; nothing else in the assessment is disturbed.

## 9. The platform cannot back this yet — and the same doubt reaches backwards

```yaml
logical_autonomy: PARTIAL
platform_enforcement: EL1_DETECTIVE
branch_protection: ABSENT
independent_workload_identities: ABSENT
expected_source_required_checks: ABSENT
release_controller_separate_from_builder: ABSENT
autonomous_merge_trustworthy: false
```

`main` has no protection; three of four gates carry
`if: github.event_name == 'pull_request'` and **were observed `skipped` on `main` at
`c94e4da`** with only the test gate running; a `skipped` required check counts as
success; there is one principal; nothing pins which principal may report a check.

**So a green 4/4 is not an EBTA certificate, and no agent may treat it as one.**

**The uncomfortable part.** This assessment does not only constrain future
autonomous merges — it applies to the ones already made. Every autonomous `G0`
merge under the `A1` envelope, including several in this session, rested on the same
platform. They were authorized by the ratified envelope and remain so; what §9 says
is that the *evidence* behind them was weaker than the green panel implied. Recorded
rather than quietly scoped to the future, because a risk disclosure that exempts the
author's own past work is advocacy.

## 10. Work packages

`WP-02` NS classifier, shadow · `WP-03` claim compiler and formula registry ·
`WP-04` EBTA schema and exhaustive policy evaluator · `WP-05` builder / verifier /
release workload identities · `WP-06` rulesets, non-skippable checks, expected
sources · `WP-07` autonomous merge canary · `WP-08` deployment, monitoring,
automatic rollback · `WP-09` meta-governance epoch activation · `WP-10` continuous
learning and governance garbage collection.

One PR each. `WP-05` and `WP-06` are the gating pair — until they are effective,
`AR2` autonomy is a design, not a capability.

## 11. Promotion states, gated on evidence not elapsed time

```text
RATIFICATION_PENDING → AUTONOMY_MANDATE_EFFECTIVE → SHADOW_VERIFICATION
→ AUTONOMOUS_SANDBOX → AUTONOMOUS_MAIN_MERGE → AUTONOMOUS_CANARY
→ AUTONOMOUS_PRODUCTION → AUTONOMOUS_META_GOVERNANCE
```

Each promotion requires: all golden fixtures pass · no false downgrade · no
unresolved critical finding · EBTA replay reproduces · a rollback drill passes · no
required check skipped · workload identities genuinely separate · main readback and
post-merge reconciliation pass · observed error bound below the mandate's risk
tolerance.

**No state promotes itself**, and no new control governs the pull request that
creates it.
