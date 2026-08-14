# Auto-Merge Standard

```yaml
standard_id: SECB-AMS-001
version: 0.2.0
lifecycle_state: PROPOSED
binding: false
effective_event: null
ratification_receipt: null
supersedes: null
merge_effect:
  records_proposal: true
  activates_standard: false
  supplies_ratification: false
work_package: SECB-WP-FWK-063
authority: operator ruling of 2026-08-14 (the d=2 disposition and the Auto-Merge
  Standard Update issued with it), revised under the review verdict of the same day
```

> **The block above is the authority on this document's status, and a test parses it.**
> Prose elsewhere in this file describes history and may contain the words `PROPOSED`
> or `binds nothing` inside a historical passage — **a substring search would pass on
> those and prove nothing.** `lifecycle_state` and `binding` are the fields; the prose
> is commentary.

> **Why this document exists.** The rule it records was issued in session. Until it is
> in the repository it is an instruction someone has to remember, and the point of the
> ruling is that memory is not a control. **Its presence here is not force.**
>
> **Merging the pull request that adds this file records a proposal. It does not
> activate it.** See §12 — landing and effectuation are two transitions, and the
> earlier phrasing *"binding: false until an authority lands it"* left them fused,
> so a merge could have been read either way.

## The finding this standard answers

`K-09` at n=40 recorded `d = 2`:

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

| Authority | Grants | Does not grant |
|---|---|---|
| `TRANSCRIPTION_AUTHORITY` | Writing down a decision an authority already made | Putting it into force |
| `EFFECTUATION_AUTHORITY` | Making a recorded decision operative | — |

**A self-merge supplies neither.** This distinction was reached by correcting the
executor's own argument: it had claimed #120 was the lesser candidate *because* it
originated nothing.

## 2. Required authority is a lattice join, not a numeric maximum

**Corrected under review.** The first draft wrote:

```text
effective_class = max(path_class, semantic_materiality, state_transition_effect, …)
```

That takes `max` across **incommensurable domains** — a path class, a materiality
class and a state-transition effect are not points on one scale, so `max` has no
defined meaning over them. Each dimension instead **maps to an authority
requirement**, and the requirements have a partial order with a least upper bound:

```text
required_authority = join(
    authority_for(path_class),
    authority_for(semantic_effect),
    authority_for(state_transition),
    authority_for(authority_effect),
    authority_for(condition_effect)
)
```

`join` is the **least upper bound of authority requirements** — the weakest authority
that satisfies every dimension at once. It is not a comparison of classifications;
it is a comparison of what each classification *demands*.

A file under an `auto_path` therefore cannot be satisfied by `G0` when any dimension
demands more, and these six each demand more:

- opens, closes or changes a stage
- creates or modifies a condition
- **stamps an effective event**
- changes an authority decision
- records a ratification
- changes the evidence required for future autonomous merges

**All six describe things this repository has already shipped under `G0`.**

## 3. Eligibility — ten conjuncts, fail-closed

```text
AUTO_MERGE_ELIGIBLE =
    all_required_checks_completed_successfully
  ∧ zero_required_checks_skipped
  ∧ tested_head_sha == current_head_sha
  ∧ dependency_dag_satisfied
  ∧ condition_reconciliation_attested
  ∧ no_blocking_condition
  ∧ no_executor_authority_conflict
  ∧ required_authority_receipt_valid
  ∧ merge_policy_digest_pinned
  ∧ enforcement_level == PREVENTIVE
```

Two conjuncts settle the present case on their own. **`zero_required_checks_skipped`**
— because GitHub reports a skipped required check as success, and three of this
repository's four gates skip on non-`pull_request` events. And
**`enforcement_level == PREVENTIVE`** — SecB is `EL1_DETECTIVE`, so **auto-merge
cannot be eligible here at all until `EL2`**, whatever else is satisfied.

## 4. `condition_reconciliation_attested` — a register cannot certify itself

**Corrected under review.** `condition_register_complete` asked the register to vouch
for its own completeness, which it cannot do: a condition that never reached it is
invisible to it. Completeness is a **reconciliation** between the register and the
records that create conditions:

```text
condition_reconciliation_attested =
    conditions_extracted_from_authoritative_records == conditions_present_in_register
  ∧ every_condition_has_provenance
  ∧ every_transition_has_receipt
  ∧ no_unknown_or_unparsed_record
```

```text
UNKNOWN                        ≠ COMPLETE
UNPARSED                       ≠ COMPLETE
EXCLUDED_WITHOUT_JUSTIFICATION ≠ COMPLETE
```

This is exactly how `C-5`, `C-6` and `C-7` went missing: Addendum 001 created them,
the register never received them, and **nothing compared the two.** A reconciliation
would have failed; a self-certifying register reported nothing.

## 5. Authority routes

| Change class | Required authorization |
|---|---|
| Mechanical, reversible, non-authoritative | Deterministic delegation receipt |
| Transcribes an existing decision | Exact-source receipt **+ payload-equivalence proof** |
| **Creates, amends or effectuates authority** | **Independent human ratification** |
| Changes auto-merge controls or the classifier | Constitutional ratification |
| A `Critical` condition is open | **Auto-merge prohibited** |

## 6. The register is a state machine

| Status | Merge-gate effect |
|---|---|
| `OPEN` | Blocks according to `blocking_scope` |
| `PARTIALLY_SATISFIED` | **Blocks every undischarged sub-obligation** |
| `SATISFIED` | Awaits independently verified closure |
| `CLOSED` | Requires a closure receipt |
| `SUPERSEDED` | Requires a successor reference |
| `WAIVED` | Requires an authorized, scoped, **expiring** waiver |

```yaml
C-5: { status: PARTIALLY_SATISFIED, effect: PROOF_OF_NEXT_AUTONOMOUS_MERGE_BLOCKED }
C-6: { status: OPEN, effect: NEXT_AUTONOMOUS_CANONICAL_MERGE_BLOCKED }
C-7: { status: OPEN, severity: CRITICAL, effect: [AUTONOMOUS_MERGE_BLOCKED, STAGE_9_BLOCKED] }
```

```text
AUTO-MERGE:  CLOSED
HUMAN MERGE: PERMITTED AFTER HEAD-BOUND VERIFICATION
STAGE 9:     BLOCKED BY C-7
```

## 7. Ratification receipt, and why a schema is not a control

```yaml
schema: secb.ratification-receipt/v1
repository: bstBizEra/secb_pf
pull_request: <n>
head_sha: <full-40-hex>
decision: APPROVE
authority_class: HUMAN_RATIFICATION_REQUIRED
actor: { github_user_id: <independent-user-id>, login: <independent-login> }
review: { review_id: <id>, submitted_at: <ts>, commit_id: <must equal head_sha> }
stale_on_head_change: true
```

```text
Receipt schema exists  ≠  receipt is required
Receipt is required    ≠  enforcement cannot be bypassed
```

**Corrected under review.** The first draft's fixture treated the presence of a
receipt artifact as evidence the gap had closed. Presence of a schema proves only
that someone wrote a schema. Closure requires **enforcement behaviour**:

```text
missing receipt            → merge eligibility DENY
wrong actor                → DENY
COMMENT instead of APPROVE → DENY
receipt/head mismatch      → DENY
new push                   → previous receipt STALE
valid independent receipt  → authority conjunct PASS
```

## 8. The exception is a constitutional break-glass, or #113 is structurally blocked

**Corrected under review.** Three statements were left coexisting: a comment must
not substitute for a receipt; the receipt is unobtainable under `C-7`; and
`HUMAN_ASSERTED_BOOTSTRAP_EXCEPTION` remains an available path. **Those three are
consistent only if the exception is a defined break-glass**, and no such mechanism
exists in this repository.

Were one to exist it would have to carry:

```yaml
exception:
  authority: constitutional_authority
  exact_head_sha: required
  scope: one_pull_request
  decision: explicit
  reason: required
  expires_at: required
  reusable: false
  closes_C7: false
  grants_future_autonomy: false
```

It does not exist. Therefore:

```yaml
pr_113_status: STRUCTURALLY_BLOCKED    # not "ratification-ready, awaiting time"
reason: >
  The receipt requires an actor independent of the executor and decision APPROVE.
  One shared account cannot supply the first, and GitHub refuses an approving review
  from a pull request's own author, so it cannot supply the second. This is C-7.
unblocks_when: C-7 discharged, or a constitutional break-glass is defined
```

**"Ratification-ready" was the wrong status** and it read as waiting. It is not
waiting; it is blocked by a missing capability.

## 9. Counterfactual eligibility assessment

The historical rule needs a name so it cannot be mistaken for retroactive
enforcement:

```yaml
COUNTERFACTUAL_ELIGIBILITY_ASSESSMENT:
  assessed_under_later_standard: true
  original_merge_reopened: false
  original_merge_invalidated: false
  eligibility_if_standard_had_applied: INELIGIBLE
  corrective_use: [classifier_validation, control_design, KPI_recount]
```

> **A new rule may analyse the past to learn from it, and must never be quietly made
> retroactive.**

For the window Addendum 001 → `FWK-062`:

```yaml
condition_reconciliation_attested: false
historical_autonomous_merges:
  eligibility_under_AMS: INELIGIBLE
  legal_effect: UNCHANGED
  evidence_effect: DOWNGRADE_RECORDED
```

## 10. Observer contract — identifier meaning is shape plus context

```text
identifier meaning = token shape + carrier type + declaration context + parser version
```

| Carrier | Interpretation |
|---|---|
| JSON scenario ID | Data instance — does not declare a taxonomy |
| Markdown declaration table | **Declaration-shaped — registration required** |
| Prose citation | Mention only |
| Normative metadata | Binding declaration candidate |
| Test literal | Fixture unless explicitly promoted |

```text
INVISIBLE_AS_DATA → DECLARATION_SHAPED → REGISTRATION_REQUIRED
→ TAXONOMY_VERSION_BUMP → CURRENT_VERSION_ENUMERATION
```

**Never fabricate an enumeration block for a taxonomy version that was never
measured.** `AMS` demonstrated the whole chain: invisible in
`negative_test_status.json`, declaration-shaped the moment it entered a catalogue
table, registered at `1.3.1`.

### Applied to this document's own metadata

`parser version` is a term in that equation, so a loose parser makes the meaning of
this document's status loose. The gate reading the block at the top of this file
rejects six things, each proven by a test that feeds it the malformation:

| Rejected | Because |
|---|---|
| A fence that is not the first block after the title | A later block could be an example; the first version of the test searched prose for `PROPOSED`, which a historical passage would satisfy |
| Duplicate top-level keys | Last-wins parsing lets a second `binding:` override the first silently |
| A non-semantic `version` | An unversioned document cannot carry a lifecycle |
| An unknown `lifecycle_state` | `ISSUED` was the original defect's word; a parser that accepts any state re-admits it |
| `binding: true` with no receipt | Force asserted without authority |
| `PROPOSED` with an effective event | The state and its consequence contradict |

**Each rejection has a test that asserts it raises.** A validator whose failure paths
are never exercised is the artifact-presence substitution one layer up.

## 11. Three status dimensions, kept apart

"Human merge permitted" was one phrase carrying four facts that currently disagree:

```yaml
merge_policy:        { human_merge: PERMITTED }
evidence_provability:
  human_actor_attribution: UNPROVABLE
  reason: shared_GitHub_identity
platform_capability:
  independent_APPROVE_review: UNAVAILABLE
  reason: PR_author_cannot_approve_own_PR
effectuation:        { standard_activation: STRUCTURALLY_BLOCKED }
```

```text
TRANSITION_ALLOWED =
    policy_permits
  ∧ required_evidence_obtainable
  ∧ platform_capability_available
  ∧ receipt_valid
  ∧ enforcement_consumes_receipt
```

**`policy_permits = true` alone moves nothing.** A permission whose evidence is
unobtainable and whose platform capability is absent is not a permission that can be
exercised, and reporting it as "permitted" invites someone to try.

## 12. Landing is not activation — two transitions, not one

```text
Proposal PR merged
    ↓  records the artifact canonically; changes no authority
PROPOSED artifact canonically recorded
    ↓  independent ratification receipt issued
Receipt accepted
    ↓  a separate activation PR binds receipt + effective event
ACTIVE
```

**Merging #123 does the first arrow and nothing else.** After it lands, `main` still
carries `lifecycle_state: PROPOSED` and `binding: false` — which is the intended
outcome, not an oversight. Activation is a distinct change:

```yaml
standard_id: SECB-AMS-001
version: 1.0.0
lifecycle_state: ACTIVE
binding: true
effective_event:
  type: RATIFICATION_RECEIPT_ACCEPTED
  receipt_id: <id>
  effective_at: <timestamp>
ratification_receipt:
  head_sha: <activation-head>
  independent_actor_id: <id>
```

**That transition is `STRUCTURALLY_BLOCKED` under `C-7`**: `independent_actor_id`
cannot be filled from one account. So this standard can be *recorded* now and cannot
be *activated* until `C-7` is discharged — and the two-phase shape is what makes that
sentence expressible at all.

### Lifecycle cross-field invariants

```text
PROPOSED   → binding = false ∧ effective_event = null ∧ ratification_receipt = null
ACTIVE     → binding = true  ∧ effective_event ≠ null ∧ ratification_receipt ≠ null
SUPERSEDED → binding = false ∧ successor reference complete
```

No other `lifecycle_state` is valid. A parser that accepts an unknown state, or a
`binding: true` with no receipt, is not checking the thing that matters.

## 13. What this standard does not do

- **It does not implement anything.** `required_authority` needs the semantic
  classifier (`WP-02`); the eligibility conjunction needs the EBTA evaluator
  (`WP-04`); `enforcement_level == PREVENTIVE` needs `WP-06`. None is built.
- **It does not reopen the merges it assesses.** See §9.
- **It does not grant the executor a new route.** Every route requires either a
  receipt the executor cannot issue or a ratification only an authority can give.
