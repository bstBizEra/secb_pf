# Retroactive Audit — SecB's Genesis Ratification against `G-01`…`G-10`

Audited: 2026-08-10 · Work Package: `SECB-WP-FWK-033` (issue #62)
Subject: `SECB-WP-FWK-012`, the Genesis Ratification — PR #21, head `668ac49`,
merge `035b66d`, merged by `bstBizEra` at 2026-08-09T19:17:46Z
Gate set: supplied by the operator for a different repository's ratification, and
applied here because SecB's own Genesis was ratified **without any such
checklist** — four green CI gates and an operator instruction

Every row is measured with the command shown. Two gates are recorded
**unverifiable** and one **false as written**; none is graded generously.

## Result

| Gate | Requirement | SecB's Genesis | How measured |
|---|---|---|---|
| `G-01` | `default_branch == main` | **PASS** | `gh api repos/bstBizEra/secb_pf --jq .default_branch` → `main` |
| `G-02` | `main == expected tested trunk SHA` | **FALSE AS WRITTEN** — see below | `git merge-base --is-ancestor 668ac49 origin/main` → **no** |
| `G-03` | Legacy `main` preserved under an immutable archive ref | **N/A** | Only one branch has ever existed; the pre-Genesis history is an ancestor of `main`, not a displaced branch. Nothing was rewritten, so nothing needed archiving |
| `G-04` | All required CI checks `SUCCESS` | **PASS** | Four checks on `668ac49`: Authority, Test, Budget, Governance verdict — all `success` |
| `G-05` | PR base == `main` | **PASS** | `gh api …/pulls/21 --jq .base.ref` → `main` |
| `G-06` | PR head SHA == recorded Genesis candidate SHA | **PASS, weakly** | `668ac49` appears in the issue #20 evidence comment as the SHA the gates ran on. It was **never labelled** "the Genesis candidate SHA", so the identification is inferable rather than stated |
| `G-07` | Branch ruleset enforced | **UNVERIFIABLE — structurally impossible** | `gh api repos/…/rulesets` → `403 Upgrade to GitHub Pro or make this repository public`. No ruleset, no branch protection, on this plan |
| `G-08` | No unauthorized bypass event | **UNVERIFIABLE** | A bypass event is a ruleset concept. With no ruleset there is nothing to bypass and no audit stream to inspect — absence of evidence, not evidence of absence |
| `G-09` | Ephemeral CI signing key classified `TEST_ONLY` | **N/A** | No signing exists anywhere in SecB. The envelope is explicitly `UNSIGNED` |
| `G-10` | Authorized human ratification recorded | **PASS, with a caveat** | `merged_by` = `bstBizEra`, timestamp recorded, and the operator's instruction is quoted in the WP. The caveat: `bstBizEra` is the **shared account both the operator and the agent use**, so the actor field does not by itself distinguish which party merged. The instruction quote is what carries the attribution |

> **Corrected 2026-08-13 (`SECB-WP-FWK-060`).** The sentence above read *"Six pass
> (two weakly), two N/A, two unverifiable, one false as written."* That is **eleven
> results from ten gates**: `G-02` was counted twice — graded `FALSE AS WRITTEN` in
> the table *and* silently included in the six passes as its squash-aware
> replacement. **A defect finding and the result under its replacement rule are not
> two gates.** Two ledgers below, rows never merged, each summing to ten.

## `G-02` is incompatible with squash-merge, and here is the fix

SecB squash-merges every PR and deletes the branch. Consequently:

```text
git merge-base --is-ancestor 668ac49 origin/main   ->  no
```

The tested head is **not** an ancestor of `main`. `G-02` as phrased — *"main ==
expected tested trunk SHA"* — cannot hold for any squash-merged Genesis, and
stating it as a gate would make every such ratification fail a check it can never
pass.

What `G-02` actually protects is that **`main` contains exactly what was tested.**
That is verifiable, and it holds:

```text
git rev-parse 035b66d^{tree}   ->  bab3c70e5e5a398c7a4e697e24bf118235e4c1d5
git rev-parse 668ac49^{tree}   ->  bab3c70e5e5a398c7a4e697e24bf118235e4c1d5
```

**Squash-aware `G-02`:** the merge commit's tree equals the tested head's tree.

This is *stronger* than the ancestry form in one respect — it proves the content
identical rather than merely reachable — and weaker in another: it says nothing
about history. Both are true and the trade is deliberate under a
squash-and-delete convention.

**Operational consequence, and it has a deadline.** The proof requires the head
SHA to remain resolvable. `668ac49` is still resolvable only because this clone
retains the deleted branch's objects; on a fresh clone it is unreachable from
`main` and GitHub may eventually garbage-collect it. **A squash-merged
ratification must record `source_head_sha`, `result_sha` and the shared tree hash
in the evidence at merge time**, or the proof expires quietly. The operator's own
guidance says exactly this; SecB recorded the SHAs but not the tree hash, which
this audit now fixes for the Genesis.

```yaml
genesis_ratification:
  work_package:    SECB-WP-FWK-012
  pull_request:    21
  source_head_sha: 668ac49
  result_sha:      035b66d
  shared_tree:     bab3c70e5e5a398c7a4e697e24bf118235e4c1d5
  merged_by:       bstBizEra   # shared account; attribution rests on the quoted instruction
  merged_at:       2026-08-09T19:17:46Z
  gate_runs:       Authority, Test, Budget, Governance verdict — all success on 668ac49
```

## What this audit changes about SecB's foundation

**Nothing is invalidated.** The Genesis was ratified on four green gates, an
explicit operator instruction, and a merge whose content is now proven identical
to the tested tree. That is a defensible foundation.

**Two things are now known that were not:**

1. `G-07` and `G-08` are **permanently unverifiable on this plan**, not merely
   unimplemented. Every claim SecB makes about branch integrity rests on
   convention and the absence of anyone attempting otherwise — not on
   enforcement. That is already recorded as deferred capability `D1`; this audit
   attaches the Genesis to it.
2. `G-10`'s actor field does not distinguish operator from agent, because both use
   `bstBizEra`. Attribution rests entirely on quoted instructions in work-package
   records. **That is the same structural weakness as the ballot layer** — a
   shared identity cannot self-differentiate — and it is one more thing the
   identity decision would fix.

## Recommendation

Adopt the squash-aware `G-02` and the `genesis_ratification` record shape as the
form for any future ratification — SecB's own, and any project instantiated from
it. Record `G-07`/`G-08` as unverifiable rather than omitting them, so a reader
can tell a control that is absent from one that is merely unmentioned.


---

# Corrections — `SECB-WP-FWK-060`

## Two ledgers, never merged

| Ledger | Result | Applicable | Satisfied |
|---|---|---:|---|
| `original_gate_results` | 5 PASS · 1 FALSE · 2 UNVERIFIABLE · 2 N/A = **10** | 8 | **5 = 62.5%** |
| `effective_predicate_results` | 6 PASS · 2 UNVERIFIABLE · 2 N/A = **10** | 8 | **6 = 75%** |

**62.5% is the audited state; 75% is the state after remediation.** Reporting only
the second describes a repair as though it were a finding.

```yaml
g02_false_negative:
  false_negative_count: 1
  eligible_squash_cases: 1
  observed_rate: 1/1
  sample_size: 1
  generalization_prohibited: true
```

`100%` without its denominator converts one field observation into a claim about
squash merges in general. One eligible case, one failure — enough to replace the
rule, **not** enough to state a rate.

## `G-02S` is renamed and confined

`G-02S` → **`G-02S-HISTORICAL_SQUASH_EQUIVALENCE`**. It grades the Genesis and
**governs nothing forward.** Letting a predicate derived inside an audit become the
rule for every future merge would be policy created by measurement rather than
ratified. The forward control is **`TR-01`** (issue #118), which is
merge-method-parametric and carries two conjuncts this one lacks: *which subject CI
tested*, and *whether the tested base is the base that shipped*.

## The Genesis transition, proven by recomputation

```yaml
observed_result_parent_sha:        de31bb35b7b5a26cde6448197cb54fd67823c39c
reconstructed_execution_base_sha:  de31bb35b7b5a26cde6448197cb54fd67823c39c
source_head_sha:                   668ac492429e61763471eef94406177c6263eaed
expected_transition_tree:          bab3c70e5e5a398c7a4e697e24bf118235e4c1d5
actual_result_tree:                bab3c70e5e5a398c7a4e697e24bf118235e4c1d5
transition_recomputation:          PASS
expected_tree_algorithm:
  id: git_merge_squash_write_tree_v1
  git_version: 2.34.1
  strategy: ort
  hooks: disabled
  global_config: disabled
```

Recomputed from the execution base and the source head with real merge semantics —
stronger than comparing two *recorded* trees, because it would have caught a drift
silently absorbed into the squash.

**`de31bb3` is NOT an "approved base".** It is the parent of the result commit.
Nothing here shows CI tested against it, and nothing shows an authority approved it.
`approved_base_sha` is a field about authority; `result_parent_sha` is about
execution, and using the first name for the second manufactures an approval.

```yaml
tested_base_sha: UNKNOWN
tested_base_equals_execution_base: NOT_RECONSTRUCTABLE_RETROACTIVELY
B: UNKNOWN     # not FAIL — FAIL would assert the bases differed
```

`TR-01 = NOT_APPLICABLE_RETROACTIVELY`. It requires evidence captured **at merge
time**, and no recomputation substitutes for a record never written. `B` is exactly
the conjunct that cannot be recovered afterwards.

## `G-07` / `G-08` — grade unchanged, reason corrected

The original text called these *"permanently unverifiable on this plan."* Both halves
were wrong. **Not permanent:** GitHub's own response names two remedies — upgrade, or
**make the repository public**, which is the selected `GITHUB_PUBLIC_FREE_ORG`
profile. **And the root cause is stated, not proven:** a bare `403` would establish
nothing, since that endpoint documents `200`/`404`/`500`; what raises it above
inference is the response **body**, which is GitHub's own text.

```text
HTTP_403_OBSERVED → PROVIDER_STATED_CAUSE → DOCUMENTED_REMEDY_CONFIRMED
→ CONFIGURED → NEGATIVE_TESTED → OPERATIONALLY_CONFIRMED
```

```yaml
root_cause: STATED_BY_API_RESPONSE_BODY
documented_remedy: CONFIRMED
operational_verification: PENDING
grade: UNVERIFIABLE          # unchanged
```

**A change from `403` to `200` does not close these gates.** Configuration is not
enforcement; only negative tests proving a bad push or merge is *rejected* can.

## Ratification record — the full shape

The audit warned a squash proof expires once the source head is garbage-collected,
then recorded three fields. The complete shape, so no future ratification can be
recorded incompletely:

```yaml
ratification_record:
  ratification_id:
  pr_number:
  merge_method: SQUASH
  approved_base_sha:            # authority — may be UNKNOWN, never inferred
  source_head_sha:
  source_head_tree_sha:         # mandatory: the proof expires without it
  tested_subject_kind:          # SOURCE_HEAD | SYNTHETIC_MERGE | MERGE_GROUP
  tested_subject_sha:
  tested_base_sha:
  required_check_run_ids: []
  result_sha:
  result_tree_sha:
  result_parent_sha:
  decision_authority:           # four identity dimensions, per G-10's caveat
  execution_actor:
  credential_subject:
  initiating_principal:
  merged_at:
  policy_version:
  evidence_digest:
```

`source_head_tree_sha` and `result_tree_sha` are **separate fields** — equal for the
Genesis, not equal by definition.

## Evidence preservation — the proof is already expiring

```
git merge-base --is-ancestor 668ac49 origin/main  →  NOT reachable
```

**`668ac49` is unreachable from `main`.** It survives only in one working clone, so
**a fresh clone cannot verify SecB's Genesis today.** Preserved locally:

```yaml
evidence_state: LOCAL_QUARANTINED     # step 2 of 7, see EP-01 (#119)
local_tag: evidence/genesis-source-668ac49
bundle_bytes: 167705
bundle_sha256: 112e73521834a4726b5b55ef2dd7dbc1158660522be45e39e87f12c566b4d262
bundle_verify: "The bundle records a complete history."
remote_reachability: PENDING
external_non_equivocation: PENDING
```

Not committed to this repository: without an external append-only store a bundle
held here is tamper-**evident** only, since the same principal can rewrite both the
bundle and the digest describing it. **The repository is not the archive.**
