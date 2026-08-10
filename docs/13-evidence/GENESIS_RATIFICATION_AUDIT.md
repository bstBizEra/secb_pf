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

**Six pass (two weakly), two N/A, two unverifiable, one false as written.**

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
