# Analysis — ADEC v1.0 against the framework already in force

Status: Analysis complete · **nothing installed by this document** · `SECB-WP-FWK-037` (issue #70)
Occasion: the operator supplied *"ADEC v1.0 — Agent Decision, Evidence & Control
Kernel"* on 2026-08-11 with a constraint attached: **accept the work, do not
duplicate what exists, do not conflict with the system or with the work in
flight.**
Method: every ADEC element mapped onto the artifact that already holds its slot,
with a verdict per row. Arithmetic re-derived. The one external claim verified
against the specification rather than restated.

## Verdict up front

| Finding | Count |
|---|---:|
| ADEC elements **already in force** under a different name | 11 |
| Elements that **extend** something in force — real improvements to an existing design | 6 |
| Elements that are **genuinely new** | 5 |
| Elements that **conflict** with policy in force | 2 |
| Factual corrections — one to ADEC, two to SecB's own records | 3 |

**ADEC is roughly two-thirds a re-description of the framework already installed
by `FWK-012`, `FWK-019-A`, `FWK-026` and `FWK-031`.** That is not a criticism of
the proposal: it converges on the same architecture from outside, which is
corroboration. But *installing* it as written would create a second vocabulary
for slots that already have one — the `SC-04` collision this repository has
already paid for twice — and one of the two conflicts would **widen agent
authority by a full decision class while looking like a naming tidy-up.**

The recommendation is therefore: **adopt the six extensions and the five new
elements, resolve the two conflicts first, and import none of the renames.**

## 1. Component map

`docs/00-governance/` unless noted. "In force" means a merged artifact, not a plan.

| ADEC element | Slot already held by | Verdict |
|---|---|---|
| `D0`–`D4` decision classes | `DECISION_AUTHORITY.md:29-42` (HDG-EAB Tier 1, `FWK-026`) | **CONFLICTS** — see §2 |
| Human retained only for authority / legal / financial / constitutional change | `DECISION_AUTHORITY.md:55-71` — nine mandatory human triggers, of which 7, 8, 9 are exactly those | Already in force |
| Human out of the routine coding loop | `DECISION_AUTHORITY.md:121-125` — `D0`/`D1` autonomous today; measured at 77% of post-Genesis merges (`K-11`) | Already in force |
| Deterministic Policy Kernel, not an LLM | `scripts/classify_authority_delta.py` — a deterministic, stdlib-only classifier; `L0_ROOT_CONSTITUTION.md:55-70` fixes the verdict set | Already in force |
| Kernel computes from pre-approved rules | `config/delegation_envelope.json` — machine-readable scope, caps, tier, expiry (`NFR-14`) | Already in force |
| Evidence levels tied to what actually exists | `DECISION_AUTHORITY.md:91-105` — `E0`–`E4`, with `E4` recorded as **none** | Already in force |
| Sealed ballots bound to a commit and evidence root | `config/ballot.schema.json` — `subject_commit`, `evidence_root` Merkle root, `expires_at`, `signature` | Already in force (inert) |
| `proposer_is_not_verifier` | `ballot.schema.json` `signer_identity`: *"MUST differ from the proposer's identity; a ballot whose signer cannot be distinguished from the proposer is void"*; envelope `ballot_layer.proposer_may_vote: false` | Already in force |
| Five voting domains (architecture, governance, security, QA, operations) | `ballot.schema.json` `role` enum; envelope `ballot_layer.required_roles` | Already in force |
| Governance and security hold veto | envelope `ballot_layer.quorum_when_active`; `ballot.schema.json` `decision` includes `VETO` | Already in force |
| Independent OIDC workload identity per role | `GOVERNANCE_DEFERRED_CAPABILITIES.md` §D3 — designed, blocked, with the unblocking action named | Already specified, deferred |
| Signing + transparency log (Sigstore) | `GOVERNANCE_DEFERRED_CAPABILITIES.md` §D2 | Already specified, deferred |
| Shadow mode before enforcing | `L0_ROOT_CONSTITUTION.md:81-88` two-epoch activation; `GOVERNANCE_DEFERRED_CAPABILITIES.md` §D4 | Already in force (via dual-policy) |
| Ballot invalidated when evidence changes after the vote | `ballot.schema.json` `subject_commit`: *"A new push changes this value and invalidates every ballot bound to the old one"* | Already in force |
| Hard controls evaluated **before** scoring; no score compensates | `L0_ROOT_CONSTITUTION.md:44-53` — prohibited actions are *"not risks to be balanced against benefit"* | **EXTENDS** — see §4 |
| Domain quorum instead of headcount | envelope has headcount (`4 of 5`) | **EXTENDS** — and corrects it, see §4 |
| Evidence Auditor as a hard gate | `GOVERNANCE_DEFERRED_CAPABILITIES.md` §D1 external verifier, deferred | **EXTENDS** |
| Six ballot decision types | `ballot.schema.json` `decision`: `APPROVE`/`REJECT`/`ABSTAIN`/`VETO` | **CONFLICTS** on names, **EXTENDS** on the abstain split — §3 |
| `POLICY_VETO` must carry control ID, evidence, impact, remediation, exception path | Nothing requires veto justification today | **EXTENDS** |
| Red-Team agent | No counterpart | **NEW** |
| Option scoring `Value − Cost − Delay − ExpectedLoss − UncertaintyPenalty` | No counterpart. `RISK_AUTHORITY_MATRIX.md:35` says unknown scope → `HOLD`, but never ranks options | **NEW** |
| `ExpectedLoss = Likelihood × Impact × BlastRadius × Irreversibility` | `RISK_AUTHORITY_MATRIX.md` `R0`–`R4` is a tier ladder, not a product | **NEW** |
| Monotonic Hardening Clause | No counterpart. `L0` §30-33 forbids widening; it says nothing about *narrowing* | **NEW — highest value, see §5** |
| Rollback drills as a promotion precondition | `DELIVERY_LIFECYCLE_STAGES.md` mentions canary/rollback at stages 9–11; no drill requirement, no counter | **NEW** |
| Uncertainty → canary / simulation / controlled experiment instead of asking a human | `DECISION_AUTHORITY.md:107-119` sends unresolved decisions to a fail-safe default, never to an experiment | **NEW** |
| `n ≥ 30 AND upper_confidence_bound ≤ threshold` for promotion | `KPI_BASELINE.md` `K-09` uses the rule of three at `n=30` | **EXTENDS**, and exposes an inconsistency — §6 |
| Risk-weighted evidence completeness | `KPI_BASELINE.md` `K-03` is one flat ratio | **EXTENDS** — §7 |
| Split green-vs-effective, enforcement-vs-negative-test, outcome-vs-capability | `K-01`, `K-05`, `K-07` are single figures | **EXTENDS** — §7 |
| Pin the OpenTelemetry semantic-convention version | `K-10` cites attribute names with no version | **EXTENDS**, and finds two real defects — §8 |

## 2. The conflict that matters — `D`-class renumbering

Both tables use `D0`–`D4`. They do not mean the same thing.

| Class | In force (`DECISION_AUTHORITY.md`, `FWK-026`) | Final authority in force | ADEC v1.0 | Agent may decide, per ADEC |
|---|---|---|---|---|
| `D0` | `ROUTINE` | Agent | `OBSERVATIONAL` | Yes |
| `D1` | `CONTROLLED` | Agent under existing policy | `REVERSIBLE` | Yes |
| `D2` | `MATERIAL` | **Product / business owner** | `CONTROLLED` | **Yes, on ballot + evidence** |
| `D3` | `HIGH_RISK` | **Business owner + risk owner** | `HIGH-IMPACT` | Yes, on pre-authorized playbook |
| `D4` | `CONSTITUTIONAL` | Constitutional authority | `CONSTITUTIONAL` | No self-approval |

Read the `D2` row twice. **In force, `D2` is the first class an agent may not
decide.** In ADEC, `D2` is the last class it may. The label `CONTROLLED` moves
from `D1` to `D2`, so both tables can be quoted as authority for opposite
answers to *"may an agent land this?"*

`SPECIFICATION_CONFLICT_PROTOCOL.md` classifies this as `SC-04` (terminology
collision) compounded by `SC-05` (authority conflict), at impact **`C4` —
authority or safety**, which is *"constitutional authority only"*. It is recorded
in `docs/13-evidence/CONFLICT-ADEC-001.md` and is **`OPEN`**.

ADEC's stated reason for `D0`–`D4` was *"so as not to be confused with autonomy
levels `A1`–`A4`"*. That confusion was already resolved the same way five work
packages ago, and `DECISION_AUTHORITY.md:39-42` goes further: it separates
**three** axes — `D` who decides, `G` who may land it, `R` how much damage —
and takes the strictest. ADEC's table collapses `D` and `G` back into one
column, which is the distinction that was expensive to draw.

**Recommended resolution: keep the `D`-class names in force; import ADEC's
column of *"can agents decide this"* as a separate, explicitly named column, so
the aspiration is visible without overwriting the authority in force.** The gap
between the two columns then becomes the roadmap rather than a silent edit.

## 3. Vocabulary — ADEC adds a ninth set, and three tokens collide

Eight verdict vocabularies are in force and the standing rule is **always name
the set** (`SPECIFICATION_CONFLICT_PROTOCOL.md:131-137`). ADEC introduces tokens
across three different decision layers without naming which set each belongs to:

| ADEC token | Collides with | Nature |
|---|---|---|
| `AUTO_APPROVED` | Merge-authority set (`L0` §55-70) — same token, different object | Bare reuse. ADEC applies it to *option selection*; in force it names *who may land a change* |
| `APPROVED_WITH_OPEN_CONDITIONS` | Stage-gate `APPROVED_WITH_CONDITIONS` | Near-synonym one word apart, not in any set |
| `AUTO_APPROVE_WITH_OPEN_CONDITIONS` | Both of the above | Third variant of the same idea |
| `SUPPORT`, `OPPOSE` | `ballot.schema.json` `APPROVE`, `REJECT` | Rename of an enum in a **constitutional-path file** |
| `POLICY_VETO` | `ballot.schema.json` `VETO` | Rename |
| `ABSTAIN_INSUFFICIENT_EVIDENCE`, `ABSTAIN_OUTSIDE_COMPETENCE` | `ballot.schema.json` `ABSTAIN` | **Genuine refinement** — splits one token into its two distinct causes |
| `BLOCKED_NO_SAFE_OPTION`, `CONTROLLED_EXPERIMENT_REQUIRED`, `POLICY_BLOCKED`, `EXTERNAL_AUTHORITY_REQUIRED`, `BALLOT_INVALIDATED` | Nothing | **New, and they need a named set** — proposed: the *option-selection* set |
| `AUTHORIZED_BY_GUARD` | Transition guard yields `OPEN` / `BLOCKED` (`TWO_PLANE_DECISION_MODEL.md:97-111`) | New token for an existing binary |

The abstain split is worth taking: *"I lack evidence"* and *"this is outside my
competence"* have different remedies, and collapsing them loses which one
applies. Everything else in the rename column should be dropped — a rename of a
constitutional-path enum buys nothing and costs a fourth shared token.

## 4. What the two extensions actually fix

**Domain quorum over headcount is a real correction, not a preference.** The
envelope specifies `4 of 5`. ADEC's argument — that several agents may be the
same model and therefore share correlated error, so counting them is counting
one opinion five times — is sound and applies directly to this deployment, where
`ballot_layer.state = NOT_ACTIVE` precisely because the five roles would be one
session. Headcount quorum is the weaker design **even after** identities exist,
because identity separation does not create error independence. `A3`/`A4` should
require at least one reviewer on a different model or provider, as ADEC proposes.

**Hard-controls-before-scoring generalizes a rule that currently covers only the
prohibited list.** `L0` §44-53 already refuses to weigh five prohibited
signatures against benefit. ADEC applies the same structure to eight
preconditions — reproducible source, evidence complete for the risk class,
evidence unexpired, valid independent identity, no unresolved veto, proven
rollback where required, decision inside the envelope, proposer ≠ verifier — of
which **seven already exist as separate controls** and are simply not written as
one conjunction that gates option ranking. Writing them as a conjunction is the
contribution.

## 5. The Monotonic Hardening Clause — the single most valuable new element

`L0` forbids an agent from widening its own authority and says nothing about
narrowing it. The asymmetry is real: today, tightening a rule carries the same
`G4` escalation cost as loosening one, so the cheapest safe action and the most
dangerous action are priced identically. ADEC's clause prices them differently,
gated on a machine-checkable predicate:

```text
Allow_new     ⊆ Allow_old
Deny_new      ⊇ Deny_old
bypass_new    == bypass_old
quorum_new    == quorum_old
authority_new ⊆ authority_old
protected_new ⊇ protected_old
```

Two observations before it is adopted:

1. **ADEC's own caveat is correct and load-bearing.** A system cannot author this
   clause and then use it to approve itself. It requires one root authorization,
   after which it is self-applying. That ordering must be preserved.
2. **The predicate is checkable but not yet checked.** `Deny_new ⊇ Deny_old` over
   prose is a judgement; over the envelope's JSON sets it is a computation. The
   clause should be scoped to the machine-readable surfaces first — envelope
   sets, the prohibited-action list, `protected paths` — and treated as
   `SPEC_OWNER_REQUIRED` for prose. A hardening claim that cannot be computed is
   an assertion, and asserting monotonicity is exactly the move an authority
   expansion would disguise itself as.

## 6. `K-09` — the supplied figure is wrong, and correcting it strengthens the conclusion

The supplied KPI table reads `K-09 = 3/23 ≈ 13.04%`, then computes a Wilson 95%
interval of `4.5%–32.1%` from it.

**That reads 3 as an observed downgrade count. The record is zero.**
`docs/13-evidence/K09_LEDGER.md` holds `n = 23`, `d = 0`, and the `3` is the
numerator of the *rule-of-three upper bound* `3/n`, not a count of events. The
distinction is not pedantic:

- Three downgrades would mean three constitutional-class changes were classified
  as autonomous — each an incident under `K-02`, not a metric movement.
- The ledger states that **the first observed downgrade ends the series**: the
  rule of three applies only to a zero numerator, and the correct response to
  `d = 1` is to treat the classifier as unproven, not to continue the tally.

So `3/23` as a proportion would simultaneously invalidate the bound it is quoted
as computing.

**But ADEC's underlying instinct is right, and the arithmetic supports it more
strongly than the version it used.** For zero events the Wilson 95% upper bound
has a closed form:

```text
upper = z² / (n + z²)   with z = 1.96, z² = 3.8416
```

| n | rule of three `3/n` | Wilson upper, `d=0` |
|---:|---:|---:|
| 23 (today) | 13.04% | **14.31%** |
| 30 | 10.00% | 11.35% |
| 35 | 8.57% | **9.89%** |
| 60 | 5.00% | 6.02% |

The two agree at `n ≈ 13.7`; **above that the rule of three is the more
optimistic of the two.** At today's `n = 23` our published bound understates the
Wilson bound by 1.3 points.

### The consequence nobody had noticed

The `A1 → A2` ladder rung is *"≤10% at n=30"*, and `30` was chosen because
`3/30 = 10.0%` exactly. Under Wilson, `n = 30` gives **11.35%** — the rung
becomes unreachable at its own threshold. Reaching ≤10% requires

```text
n ≥ z²/0.10 − z² = 34.57  →  n ≥ 35
```

So adopting ADEC's promotion rule as written — `n ≥ 30 AND upper bound ≤
threshold` — would silently make the rung unsatisfiable. **Either keep `3/n` and
`n = 30`, or adopt Wilson and move the rung to `n = 35`.** Recommended: adopt
Wilson and move the rung, because the conservative instrument is the point of
having one — and note that raising a threshold is itself monotonic hardening
under §5.

Meanwhile ADEC's conclusion `A1 → A2 = HOLD` holds either way, and for a reason
neither version cites: `K-07` records **17** autonomous merges against a rung
that requires 30.

## 7. The `K-03` split is correct and already measured

ADEC proposes reporting evidence completeness three ways and blocking promotion
while the escalated class is below 100%. That matches what `FWK-035` measured and
recorded (`KPI_BASELINE.md:37-51`):

```text
K03_OVERALL    = 28/32 = 87.5%
K03_AUTONOMOUS = 28/28 = 100%
K03_ESCALATED  =  0/4  = 0%
```

Two notes. First, the four misses are **exactly** the four escalated,
operator-merged work packages (#28, #36, #48, #58) — so the deficit is
systematic, and inverted against authority: evidence is worst where it matters
most. Second, the flat figure in the catalogue reads **88%** where the exact
value is **87.5%**; ADEC's arithmetic is right and ours rounds up. A metric that
rounds in the flattering direction should not round at all — a correction for the
KPI work package.

`FWK-036`'s evidence comment on issue #68 is the first escalated work package to
carry a full gate table, so the forward fix has begun. The count stays 0/4 until
those merges age out of the window, and back-posting to the four would be
back-dating evidence.

## 8. OpenTelemetry — verified, and ADEC is half right

Checked against the specification on 2026-08-11 rather than restated:

| Claim | Verified state |
|---|---|
| `gen_ai.usage.input_tokens` / `output_tokens` exist and supersede `prompt_tokens` / `completion_tokens` | **True.** The registry page lists both replacements explicitly ([registry](https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/)) |
| The GenAI conventions moved to a new repository | **True** — [`open-telemetry/semantic-conventions-genai`](https://github.com/open-telemetry/semantic-conventions-genai); the entries at the old location are marked moved |
| SecB's `K-10` contract therefore names deprecated attributes | **False.** `K-10` never used `prompt_tokens`/`completion_tokens`. It names the **metric** `gen_ai.client.token.usage`, which is **still current** in the new repository at **Development** stability ([metrics doc](https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-metrics.md)) |

So the correction ADEC implies does not apply. **Two real defects in our own
contract turned up while checking, both of which ADEC's "pin the version" advice
would have caught:**

1. **`K-10` records two attributes the metric does not require and omits two it
   does.** The specification requires `gen_ai.operation.name`,
   `gen_ai.provider.name` and `gen_ai.token.type`; `gen_ai.request.model` is
   *conditionally* required. `KPI_BASELINE.md` names `gen_ai.token.type` and
   `gen_ai.request.model` only. Data recorded to that contract would not satisfy
   the convention it claims to follow — and `K-10` was adopted specifically so
   that *"future data is comparable"*.
2. **No version is pinned, and the conventions have already moved once at
   Development stability.** An unpinned citation to a moving target will rot
   silently.

Both belong to `C-3` predicate (c), which is `OPEN`. This is the first evidence
that the predicate is not merely unimplemented but **mis-specified**, which is
worth more than the implementation would have been.

## 9. Why ADEC cannot be switched on, whatever is approved

ADEC's closing position is that humans should stop reviewing source code. The
blocker is not policy — `DECISION_AUTHORITY.md` already grants `D0`/`D1` to
agents and 77% of post-Genesis merges are autonomous. The blocker is structural:

```text
ballot_layer.state           = NOT_ACTIVE     (no independent identities exist)
tiers requiring active layer = A3, A4         (unreachable)
E3 evidence artifacts        = 2
E4 evidence artifacts        = 0              (nothing is deployed)
rollback drills run          = 0
```

Every ADEC component that votes, audits, or red-teams requires an identity that
does not exist here. Until then a seven-role ADEC ballot is one session wearing
seven hats — the failure the envelope already names in its own `ballot_layer`
reason field. **ADEC is therefore installable as a specification with an
activation predicate, and not as active policy.** Its own §10 agrees: identities
are step 2.

This also means ADEC's promise — humans out of code review — is not what the
next change delivers. What it delivers is that the framework is *ready* for it.
Stating that plainly is the difference between a roadmap and a claim.

## 10. Recommended ordering, corrected from ADEC §10

ADEC's step 1 is *record the stage-2 verdict*. **That should not be first.** The
verdict cites the KPI table, and this analysis found an error in it (§6) plus a
rounding bias (§7). Recording a verdict that cites uncorrected figures makes the
correction retroactive to a decision record, which the extend-only rule then
preserves forever.

| # | Step | Class | Why here |
|--:|---|---|---|
| 1 | Resolve `CONFLICT-ADEC-001` — the `D`-class collision | `C4`, operator | Nothing referencing `D2` is unambiguous until this is closed |
| 2 | Correct `K-09`'s instrument and `K-03`'s rounding; add the `K-01`/`K-05`/`K-07` splits | `G0`–`G1` | Fixes the inputs the verdict cites |
| 3 | Record the stage-2 verdict; open stage 3 | Gate record | Now cites corrected figures |
| 4 | Provision independent agent identities | Operator | Unblocks every remaining ADEC component |
| 5 | Monotonic Hardening Clause, by one root authorization | `G4` | Must precede the amendments that would use it |
| 6 | Raw force-push prohibition, as a hardening under §5 | `G4` | The first clean test of the clause |
| 7 | `K-09` recount script in shadow mode | `G4` | ADEC's two-phase shadow → enforcing is right |
| 8 | `K-10` contract correction and version pin; ODC fields | `G1` | Closes `C-3` (a) and (c) |
| 9 | Install the ADEC kernel spec with its activation predicate | `G1` | Depends on 1, 4, 5 |
| 10 | Rollback drills, then re-evaluate `A1 → A2` at `n ≥ 35` | Operator | Per §6, not `n = 30` |

Only step 3 and step 2 are cheap. Steps 1, 4 and 5 are the operator's, and
nothing downstream of them can be honestly done first.

## What this document does not do

It installs nothing, resolves nothing, and approves nothing. The two conflicts
are `OPEN`; the recommendations are recommendations. It deliberately does not
touch `docs/00-governance/`, `config/`, `scripts/` or `.github/` — an analysis
that quietly amended the policy it was analysing would be the self-approval
pattern this framework exists to prevent.

Sources for §8: [OTel GenAI attribute registry](https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/) ·
[open-telemetry/semantic-conventions-genai](https://github.com/open-telemetry/semantic-conventions-genai) ·
[GenAI metrics](https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-metrics.md) ·
[NIST AI RMF](https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf) and
[NIST separation of duty](https://csrc.nist.gov/glossary/term/separation_of_duty), as cited by the operator.
