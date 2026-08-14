# Auto-Merge Standard

Work package: `SECB-WP-FWK-063` · Recorded: 2026-08-14
Authority: **operator ruling of 2026-08-14** (the `d = 2` disposition and the
Auto-Merge Standard Update issued with it)
Status: **`PROPOSED`** — this document is a draft. It binds nothing until an
authority with `G1` over `docs/00-governance/` lands it.

> **Why this document exists.** The rule it records was issued in session. Until it
> is in the repository it is an instruction someone has to remember, and the whole
> point of the ruling is that memory is not a control.

## The finding this standard answers

`K-09` at n=40 recorded `d = 2` — two governance verdicts granted less authority
than the change required:

| PR | What the classifier said | What the change was |
|---|---|---|
| #111 | `AUTO_APPROVED — G0` | a stage-gate **verdict**, class `D2 MATERIAL` |
| #120 | `AUTO_APPROVED — G0`, self-merged | made an authoritative **addendum effective** |

```yaml
classifier_status: NOT_PROVEN_FOR_AUTONOMOUS_MERGE
cause: PATH_BASED_CLASSIFICATION_IGNORES_MATERIAL_EFFECT
```

## 1. Transcription authority is not effectuation authority

> ### "did not create a new decision" ≠ "has authority to make a decision effective"

This is the load-bearing distinction, and it was reached by correcting the
executor's own argument. The executor had claimed #120 was the lesser of the two
candidates **because** it originated nothing — it transcribed conditions the
operator had stated. The ruling separates the two authorities:

| Authority | Grants | Does not grant |
|---|---|---|
| `TRANSCRIPTION_AUTHORITY` | Writing down a decision an authority already made | Putting it into force |
| `EFFECTUATION_AUTHORITY` | Making a recorded decision operative | — |

**A self-merge supplies neither.** Recording is not effectuating, and effectuating
without an independent receipt bound to the exact head is the act #120 performed.

## 2. Effect outranks file path

```text
effective_class = max(
    path_class,
    semantic_materiality,
    state_transition_effect,
    authority_effect,
    condition_effect
)
```

A file under an `auto_path` **must not** receive `G0` merely for its path when it:

- opens, closes or changes a stage
- creates or modifies a condition
- **stamps an effective event**
- changes an authority decision
- records a ratification
- changes the evidence required for future autonomous merges

Every one of those six describes something this repository has already shipped
under `G0`.

## 3. Eligibility is a conjunction and fails closed

```text
AUTO_MERGE_ELIGIBLE =
    technical_gates_pass
  ∧ tested_head_sha == current_head_sha
  ∧ dependency_dag_satisfied
  ∧ condition_register_complete
  ∧ no_open_blocking_condition
  ∧ no_active_self_review_conflict
  ∧ authority_route_satisfied
  ∧ merge_policy_version_pinned
```

Eight conjuncts, no weighting, nothing tradeable. **`condition_register_complete`
is the one that indicts the recent past:** the register omitted `C-5`, `C-6` and
`C-7` from Addendum 001 until `SECB-WP-FWK-062`, so **every autonomous merge in that
window was ineligible under this standard — #120 included.** The rule reaches
backwards without being applied retroactively: the merges stand, and they would not
have been eligible.

## 4. Authority routes

| Change class | Required authorization |
|---|---|
| Mechanical, reversible, non-authoritative | Deterministic delegation receipt |
| Transcribes an existing decision | Exact-source receipt **+ payload-equivalence proof** |
| **Creates, amends or effectuates authority** | **Independent human ratification** |
| Changes auto-merge controls or the classifier | Constitutional ratification |
| A `Critical` condition is open | **Auto-merge prohibited** |

## 5. The register is a state machine, not narrative context

| Status | Merge-gate effect |
|---|---|
| `OPEN` | Blocks according to `blocking_scope` |
| `PARTIALLY_SATISFIED` | **Blocks every undischarged sub-obligation** |
| `SATISFIED` | Awaits independently verified closure |
| `CLOSED` | Requires a closure receipt |
| `SUPERSEDED` | Requires a successor reference |
| `WAIVED` | Requires an authorized, scoped, **expiring** waiver |

Against the current register:

```yaml
C-5: { status: PARTIALLY_SATISFIED, effect: PROOF_OF_NEXT_AUTONOMOUS_MERGE_BLOCKED }
C-6: { status: OPEN, effect: NEXT_AUTONOMOUS_CANONICAL_MERGE_BLOCKED }
C-7: { status: OPEN, severity: CRITICAL, effect: [AUTONOMOUS_MERGE_BLOCKED, STAGE_9_BLOCKED] }
```

```text
AUTO-MERGE:  CLOSED
HUMAN MERGE: PERMITTED AFTER HEAD-BOUND VERIFICATION
STAGE 9:     BLOCKED
```

## 6. Ratification receipt

```yaml
schema: secb.ratification-receipt/v1
repository: bstBizEra/secb_pf
pull_request: <n>
head_sha: <full-40-hex>
decision: APPROVE
authority_class: HUMAN_RATIFICATION_REQUIRED
actor:
  github_user_id: <independent-user-id>
  login: <independent-login>
review:
  review_id: <github-review-id>
  submitted_at: <timestamp>
  commit_id: <must equal head_sha>
stale_on_head_change: true
```

**A comment, a label, a prior conversation or an unbound instruction must not
substitute for this receipt.**

### The receipt is currently unobtainable, and that is `C-7`

Two of its required fields cannot be produced under one shared account:

- `actor.github_user_id` must be **independent** of the executor. One account, one id.
- `decision: APPROVE` — **GitHub refuses an approving review from a pull request's
  own author.**

So #113's ratification is gated on `C-7` **structurally**, not by delay. The earlier
instrument chose `COMMENT` under `HUMAN_ASSERTED_BOOTSTRAP_EXCEPTION` for exactly
this reason, and that exception remains the only available path until a second
identity exists. **Recording the impossibility here is the point** — a schema whose
fields cannot be filled looks like a process failure until someone writes down that
it is a capability failure.

## 7. What this standard does not do

- **It does not implement anything.** `effective_class` needs the semantic
  classifier (`WP-02`, issue #114/#118); the eligibility conjunction needs the EBTA
  evaluator (`WP-04`). Both are corridor-gated and neither is built.
- **It does not reopen the merges it indicts.** #111 and #120 are recorded as
  downgrades in `K09_LEDGER.md`; nothing here reverts them.
- **It does not grant the executor a new route.** Every route above either requires a
  receipt the executor cannot issue, or a ratification only an authority can give.
