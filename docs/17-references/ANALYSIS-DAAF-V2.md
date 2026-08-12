# Analysis — DAAF v2.0 intake assessment

Work package: `SECB-WP-FWK-057` · Issue: #112 · Recorded: 2026-08-13
Subject: **SecB Decision-Aware Bounded Autonomy Framework v2.0**, operator-supplied
Status: **`RATIFICATION_PENDING`** — carries the operator's disposition of 2026-08-13,
which becomes effective on the merge of PR #113 and not before. No `DAAF-WP` is
implemented by this record

---

## 0. The verdict on the proposal, up front

**The diagnosis is correct and this repository's own record said so first.** DAAF's
central claim is that authority class must derive from *impact*, not from *file
path*. Before the proposal arrived, `STAGE_GATE_REQUIREMENTS_READY.md` recorded that
a stage-gate verdict classified `AUTO_APPROVED — G0` purely because it lives under
`docs/`, and that the executor's refusal to self-merge it was **"a habit, not a
control."** DAAF names that gap precisely. Nothing below disputes it.

What is contested is narrower and specific: **`D2` auto-ratification**, which
contradicts a standing reasoned ruling (`F2`), and the **scale** of the proposed
delta measured against the framework's own expansion invariant (`F6`).

| | |
|---|---|
| Diagnosis | **Accepted.** Confirmed independently, before the proposal |
| Evidence-side mechanisms (claims, digests, formula identity, semantic classification) | **Recommended.** These are the part that closes the proven gap |
| `D2` autonomous ratification | **Conflicts** with `DECISION_AUTHORITY.md` — see `CONFLICT-DAAF-001` |
| `D0–D3` naming | **Blocked** on an operator ruling; would be a third `D` meaning |
| Ten-work-package programme as a whole | **Fails minimal-delta** under `FPSA v1.0` |
| Signing, rulesets, merge queue | **Blocked** by capabilities this repository does not have |

---

## 1. Confirmed by independent check

Each verified against the tree or recomputed, not accepted on the proposal's word.

**The `K-09` arithmetic is right.** Wilson upper bound for x=0, `z²/(n+z²)`:
10.43% at n=33, 10.15% at n=34, 9.89% at n=35 — identical to this repository's
own computation. DAAF pins `z = 1.9599639845` against the ledger's `1.96`; see `F7`.

**Items 9.4–9.6 found a real defect, now fixed.** PR #111's record declared itself
`ISSUED` while the pull request said *"nothing is issued until you merge."* Both
could not be true. Corrected by the amendment PR #111 carries (pre-squash `6f57d91`; that SHA will not survive the squash, so the pull request is the durable reference): `verdict_generated_at` separated from
`ratified_at` / `effective_at`, status `RATIFICATION_PENDING`, stage 3's opening
deferred to `effective_at`, and authority ceiling `ARCHITECTURE_APPROVED` recorded
explicitly because **admission and authorized action are separate quantities.**
This is the single most valuable thing the review produced.

**The skipped-required-job hazard is present in shape.** `authority-gate`,
`budget-gate` and `governance-verdict` each carry
`if: github.event_name == 'pull_request'`, so each skips on a push event, and
GitHub can treat a skipped required check as success. **Not currently
exploitable** — `main` has no branch protection at all (403 on a private Free
repo), so there is no required check to bypass. The hazard becomes live the moment
protection is enabled, which is precisely when nobody would be looking for it.

---

## 2. Findings against the proposal

### `F1` — `D0–D3` collides with a registered `D0–D4` ladder

`config/identifier_taxonomy.json` records:

```json
{"prefix": "D", "form": "D0-D4",
 "bound_to": "Decision classes -- who decides, as distinct from who may land it (G) or how much damage (R)",
 "home": "docs/00-governance/DECISION_AUTHORITY.md"}
```

DAAF proposes `D0 CLERICAL` / `D1 OPERATIONAL` / `D2 MATERIAL` / `D3 CONSTITUTIONAL`
— **the same prefix, the same domain, different arity.** `D2 MATERIAL` agrees with
the existing ladder; `D3` and `D4` do not. `D` already carries two registered
meanings plus prefix containment with `DWRC`.

This is worse than a crowded prefix: a **redefinition of an existing ladder in
place** makes every prior `D2` citation ambiguous — including `PACKET-002`'s own
`Class: D2 MATERIAL`. The registry exists to catch exactly this, and it did.

### `F2` — `D2` auto-ratification contradicts a standing ruling

`DECISION_AUTHORITY.md` already decided this, with a reason:

> Everything at `D2` and above reaches a human **by design.** Independent agent
> identities would make `D1`'s ballot satisfiable and supply `E3` evidence; they
> would not move `D2`+ authority, because that authority is about business
> consequence rather than technical correctness.

DAAF §4 proposes three independent ballots as sufficient for `D2` auto-ratify, and
**does not engage that reason.** The gap is not evidentiary rigour — DAAF's ballot
protocol is stronger than anything SecB has. The gap is what a `D2` decision *is*:

**Three independent verifiers raise confidence that a claim is true. `D2` asks who
owns the consequence if it is false.** No quantity of agent verification supplies
an owner. `FACT_AUDITOR`, `POLICY_EVALUATOR` and `RISK_REVIEWER` can each be
perfectly correct and still leave that question unanswered.

Formalized as `CONFLICT-DAAF-001`. **This record does not resolve it and does not
edit `DECISION_AUTHORITY.md`** — a conflict *with* a rule is not a licence for the
executor to amend that rule.

### `F3` — the headline mechanism is unimplementable here today

DAAF requires ballots from three distinct principals, in distinct execution runs,
with the author excluded. **SecB has one identity.** This is the same unmet
precondition already blocking the ballot layer, tiers `A3`/`A4` and stage 9
(`SINGLE_IDENTITY_SOD_ACCEPTED_RISK.md`). DAAF does not create the blocker and
cannot route around it: a single principal casting three role-labelled ballots is
the self-approval the protocol exists to prevent.

### `F4` — four work packages are blocked by absent capabilities

| Dependency | State in SecB |
|---|---|
| in-toto / Sigstore signed attestations | Needs a trust anchor **outside** the repository. Already `DEFERRED` — the verifier runs inside the tree it judges |
| Pinning required-check source to an App | Needs **rulesets** — HTTP 403 on a private Free repo |
| `merge_group` events | Needs a **merge queue** — unavailable |
| OPA bundle signing | Same trust-anchor problem as signing |

These gate `DAAF-WP-04`, `-06`, `-07`, `-08`. Recording them as blocked is not a
rejection: it is the difference between a roadmap and a wish.

### `F5` — five overlapping frameworks, none adopted

`BACP v1.1` is also a bounded-autonomy control plane with layered classes and
ballots (`CONFLICT-BACP-001` open; `M0–M4` reserved pending an operator ruling on
layer prefixes). `ADEC v1.0` is also an agent decision system
(`CONFLICT-ADEC-001` open at `C4`). `RAAF v0.1`'s schema layer overlaps
`DAAF-WP-01`. `FPSA v1.0` governs expansion. DAAF v2.0 is the fifth.

**This is the loudest finding in the intake.** The accumulating risk is not any
single proposal but five unresolved ones addressing the same territory: each
individually defensible, collectively a vocabulary and authority collision waiting
to be installed. **The framework's throughput constraint is operator decisions,
not proposals** — and adding a sixth would not help.

### `F6` — the minimal-delta test fails; but I was wrong that `FPSA v1.0` *binds*

> **Corrected 2026-08-13.** The first version of this finding said FPSA *"already
> binds this proposal, and is the right instrument."* **FPSA is not adopted in
> SecB.** It exists only as `docs/17-references/ANALYSIS-FPSA-V1.md` — an intake
> assessment. There is no `docs/00-governance/FPSA-*.md`, and the operator's
> framework-disposition register confirms `FPSA-v1.0: NOT_ADOPTED`. Its taxonomy is
> used here as an analytical vocabulary (as `FPSA-03` is in the envelope's
> `classification_notes`), which is not the same as being in force.
>
> **This is the same defect class this session keeps finding** — asserting a
> document is binding when it is not, exactly like the constitution's retracted
> branch-protection claim and the envelope's *"#81 auto-merged"*. It was surfaced
> by the operator's register, not by me. The test below is still worth applying;
> it is applied as a **lens I chose**, carrying no authority of its own.

FPSA's invariant, applied as a lens: *"no proven gap, no minimal delta, no bounded
authority, no rollback and retirement path — no framework expansion."*

- **Proven gap: PASSES.** #111 is the proof, and it is this repository's own.
- **Minimal delta: FAILS as a whole.** Ten work packages, a semantic classifier, a
  claim compiler, an OPA decision matrix, a ballot protocol, a capability issuer,
  signed attestations, a merge controller, a record migration and an adversarial
  FIT suite. The gap #111 proves is that **path is a poor proxy for weight**. The
  minimal delta closing *that* is `DAAF-WP-02` alone.
- **Bounded authority: PASSES in design** — `INV-01` (policy cannot approve
  itself) is exactly SecB's dual-policy rule generalized, and is well specified.
- **Rollback and retirement: PARTIAL.** The `SHADOW_MODE → ENFORCED_FOR_D0_D1 →
  ENFORCED_FOR_D2` transition is a sound rollout, but no retirement path is given
  for the classes and vocabulary once installed.

### `F7` — DAAF's own rule would flag SecB's ledger, correctly

DAAF requires `formula_id` + `implementation_sha256` and forbids hand-written
numerics without a `claim_ref`. It pins `z = 1.9599639845`; `K09_LEDGER.md` uses
`z = 1.96`. **Nothing published is wrong** — displayed values are identical across
n=29–35 — but an unpinned constant is a non-conformance under DAAF's rule. **This
is a point in DAAF's favour.** Three fabricated-figure defects were found in this
repository in two days (`NFR-02`'s retired `3/n`; the envelope's *"#81
auto-merged"*; the stage-2 record's `n=33`), every one in a *supporting* sentence
rather than the claim, which is why review kept missing them. A machine-checkable
`claim_ref` is the control that would have caught all three.

### `F8` — the budget gate already implements a fragment of `INV-05`

`ci.yml` binds `BUDGET_TEXT: ${{ github.event.pull_request.body }}` — the body **as
of the event**, not as of job execution. Observed live on #111 this session: the
declared budget was corrected 147→178 and the gate still failed until a new push
refreshed the payload. **It failed closed**, which is the correct direction.

Two conclusions. `INV-05`'s binding discipline is **achievable without new
machinery** — an event-bound declaration is already how one gate works. And a
declaration edited without a push is *not* the declaration being judged, which is
a property worth stating in the runbook rather than rediscovering.

---

## 3. Recommended sequencing

Ordered by what is buildable now, and honest about what is not.

| # | Item | State |
|---|---|---|
| 1 | **Operator ruling on `F2`** — may `D2` ever be autonomously ratified? | Blocks `DAAF-WP-05`, `-06`. Nothing else in the proposal depends on it |
| 2 | **Operator ruling on the `D` prefix** (`F1`), together with BACP's `M0–M4` | One decision covering both avoids two collisions |
| 3 | **`DAAF-WP-02` semantic classifier, `SHADOW_MODE`** | **Buildable now.** Closes the proven gap. It is also the deferred `NormativeSurfaceManifest` already named in the envelope's `classification_notes`, whose trigger this proposal arguably satisfies |
| 4 | **`DAAF-WP-03` claim compiler for numeric claims** | **Buildable now**, stdlib-only. Directly targets the three fabricated-figure defects; smaller than `WP-02` and independently useful |
| 5 | `INV-03` scope-relative conditions | Buildable; low value while `C-3`/`C-4` are the only conditions and both are already scope-annotated in prose |
| 6 | `INV-04` append-only after effectivity | **Already practised**, unwritten. Cheapest formalization in the proposal |
| 7 | Everything requiring ballots or signing | **Blocked** on a second identity and a trust anchor (`F3`, `F4`) |

**Two work packages are worth building now** — `WP-02` in shadow mode and `WP-03`.
Both close proven defects, neither needs a capability SecB lacks, and neither
requires the `D2` ruling. Everything else waits on decisions or identities.

---

## 4. What this record refuses to do, and why

- **Adopt anything.** No classifier, schema, policy or ballot code. An intake
  assessment that begins implementing has stopped being an assessment.
- **Rule on the `D` prefix.** That would install a third `D` meaning in the registry
  built to prevent it, on the executor's own authority.
- **Edit `DECISION_AUTHORITY.md`.** `F2` is a conflict with that document. Amending
  the rule that constrains the executor, to accommodate a proposal that widens the
  executor's authority, is the shape of self-widening this framework refuses.
- **Grade the proposal as a whole.** DAAF is right about the disease and partly
  contested on the treatment; a single verdict on the bundle would hide both.

## 5. What would change these conclusions

- **A second independent identity** retires `F3` outright and makes `F2` a genuine
  design question rather than a moot one.
- **An operator ruling that `D2` is about evidence, not ownership,** would overturn
  `F2` — it is a question about what `D2` *means*, and the operator owns that.
- **A fourth fabricated-figure defect** would move `F7` from "a point in DAAF's
  favour" to a proven need, satisfying FPSA's gap test for `WP-03` on its own.
- **Enabling branch protection** makes the `if:`-skip hazard live and promotes it
  from latent to urgent.

---

# 6. Operator disposition — 2026-08-13

Recorded verbatim in effect, not paraphrased into agreement. **`RATIFICATION_PENDING`
until PR #113 is merged.**

> **คง `D2+ = HUMAN_RATIFICATION_REQUIRED` ตาม `DECISION_AUTHORITY.md` เดิม.** Agent
> ballots เพิ่มความเชื่อมั่นต่อหลักฐาน แต่ไม่โอนความรับผิดชอบต่อผลลัพธ์จาก accountable
> owner ไปยัง Agent.

**DAAF v2.0 is `NOT_ADOPTED_AS_FRAMEWORK`. Its findings are not rejected** — they are
decomposed into control deltas that change no authority.

The two planes, kept apart:

| Plane | Question | Answered by |
|---|---|---|
| Evidence assurance | Is the claim true? | Agent verifiers |
| Consequence authority | Who answers if the decision is wrong? | Accountable human owner |

`FACT_AUDITOR`, `POLICY_EVALUATOR` and `RISK_REVIEWER` may agree unanimously and
still hold no budget ownership, no legal accountability and no organizational
mandate. **Accountability follows role, context and capacity to act — not verifier
count.**

## Component disposition

| DAAF component | Disposition |
|---|---|
| Semantic impact detection | `ACCEPT_INCREMENTALLY` |
| Normative Surface Manifest | `ACCEPT_SHADOW_MODE` |
| Claim compiler | `ACCEPT_AS_NEXT_ATOMIC_DELTA` |
| `INV-04` append-only decisions | `ACCEPT_FORMALIZATION` |
| `INV-05` digest-bound evidence | `ACCEPT_WITH_CORRECTION` |
| Admission / action separation | `ACCEPT` |
| Authority ceiling | `ACCEPT` |
| **Three ballots auto-ratify `D2`** | **`REJECT_AUTHORITY_CHANGE`** |
| Ten-work-package rollout | `REJECT_MINIMAL_DELTA` |
| Mandatory signing | `DEFER_CAPABILITY_UNAVAILABLE` |
| Ruleset / merge-queue enforcement | `DEFER_ADMIN_CAPABILITY` |
| OPA introduction | `DEFER_NOT_MINIMUM_SUFFICIENT` |
| DAAF as a sixth framework | `NOT_ADOPTED` |

## `F1`–`F8` resolution register

| Finding | Resolution |
|---|---|
| `F1` `D` namespace collision | **`D0–D4` stays "who decides"; the new classifier uses `NS0–NS3`.** The collision is resolved by giving the new concept a free prefix rather than rebinding an occupied one |
| `F2` conflicts with `DECISION_AUTHORITY.md` | **Existing rule preserved** — `D2+` requires human ratification. `CONFLICT-DAAF-001` closes on this |
| `F3` one principal | **No independent-quorum claim may be made.** Posture is `MULTI_ROLE_SINGLE_PRINCIPAL` — three role labels on one principal is not a quorum and must never be recorded as one |
| `F4` signing / rulesets / queue | Current posture is **`EL1_DETECTIVE`**, not preventive enforcement. Say so rather than implying gates prevent |
| `F5` five frameworks in intake | **No sixth framework.** A central disposition register is created |
| `F6` minimal delta | **`WP-02` alone, in shadow mode** |
| `F7` `1.96` vs exact z | **Keep `1.96` under a versioned formula ID.** Substituting the constant silently is an instrument change, even when displayed values are identical |
| `F8` body bound to event | **Move authoritative budget into a version-controlled manifest** — the PR body is a mutable input outside the commit SHA |

# 7. Corrected namespace — `NS0`–`NS3`

Materiality is **not** re-expressed as `D0–D3`. `D` remains the authority tier.

| Class | Normative surface |
|---|---|
| `NS0` | Non-normative formatting, or a generated projection |
| `NS1` | Operational documentation changing no state and no authority |
| `NS2` | Decision-bearing artifact — verdict, condition, or stage transition |
| `NS3` | Governance constitution, authority matrix, classifier, gate, or policy mechanism |
| `NS_REVIEW_REQUIRED` | The classifier cannot prove a class |

```text
NS classifier describes WHAT the artifact changes.
DECISION_AUTHORITY decides WHO may ratify it.
The classifier may never widen authority.
```

That third line is the load-bearing one. A classifier that could raise its own
output into an authority grant would be the self-widening the whole disposition
refuses; it may only ever route a decision to an authority that already exists.

| Artifact | `NS` | Authority outcome |
|---|---:|---|
| Typo in a non-authoritative guide | `NS0` | Existing authority matrix |
| Lifecycle status projection | `NS1` | Existing authority matrix |
| A stage-2 verdict | `NS2` | `D2` — human ratification |
| `DECISION_AUTHORITY.md` | `NS3` | Human constitutional approval |
| The classifier's own source | `NS3` | **The classifier may not approve itself** |

**`EXPECTED_CLASSIFICATION_ONLY`.** A stage-gate verdict under `docs/` *would*
classify `NS2` by content, so a path-based `G0` could not have made it
self-mergeable and the executor's restraint would not have had to be the control.

**That is a prediction about a classifier that does not exist.** `WP-02` is
authorized for `SHADOW_MODE` and is not built; `NS` classifies nothing today and
blocks nothing. It begins *detecting* when `WP-02` enters shadow, and it never
*prevents* a merge until `EL2_PREVENTIVE` — which needs branch protection this
repository cannot enable. Stating it as an accomplished control would be the
`ISSUED` defect relocated into the word "implemented".

# 8. `WP-02` — authorized for `SHADOW_MODE` only

Approved to implement with **no effect on any merge verdict or authority**.

## Classifier invariants

1. Path is **one signal** and may never lower a class the content establishes.
2. Effective class is the **strictest** of manifest, artifact type and semantic effects.
3. `docs/` is never a reason to downgrade to `NS0`.
4. Unknown or contradictory input yields **`NS_REVIEW_REQUIRED`**, never a guess.
5. Changing the classifier or the manifest schema is at least `NS3`.
6. The classifier is evaluated at the **base-branch** version.
7. A new classifier has **no authority over the PR that creates it**.
8. Shadow output is an annotation and an artifact — **never a merge authorization**.

Invariants 5–7 are SecB's existing dual-policy rule generalized: a policy may not
approve its own introduction. That rule is already mechanized in
`scripts/check_dual_policy.py`, which is why this part costs little.

## Exit gate

The #111 fixture must classify `NS2` · `DECISION_AUTHORITY.md` must classify `NS3` ·
classifier source and CI gate must classify `NS3` · an ordinary formatting fixture
must classify `NS0` · **no false downgrade anywhere in the golden corpus** · every
`NS_REVIEW_REQUIRED` reaches a human · and **promotion from shadow to enforced is a
separate human ratification**, never a consequence of the corpus passing.

# 9. `WP-03` — claim compiler, as the *next* atomic delta

Deliberately the PR after `WP-02`, to hold the minimal-delta line.

## Formula contract — do not substitute the constant

The ledger's `z = 1.96` is **kept**, under an explicit ID:

```yaml
formula:
  id: wilson_upper_95_z1_96_v1
  method: WILSON_SCORE
  confidence_level: "0.95"
  z: "1.96"
  arithmetic: DECIMAL
  threshold_comparison: RAW_UNROUNDED
  display_rounding: { decimal_places: 2, mode: HALF_UP }
```

Moving to the exact quantile later means a **new** ID —
`wilson_upper_95_normaldist_v2` — ratified as an instrument change on its own.
Swapping `1.96` for `1.9599639845` under the existing ID would be an instrument
substitution disguised as a precision improvement, **and the fact that every
displayed value is identical at n=29–35 is exactly what makes it dangerous**: it
would pass unnoticed, which is the property that lets an instrument drift.

Threshold comparison uses the **raw** value, not the rounded one — the displayed
`10.15%` and the predicate must never be evaluated from the same rounded string.

## Claim record rules

`n` derives from a ledger selection and is never typed in · no manual observation
top-ups · prose cites a `claim_id` · **a material numeric assertion without a claim
reference fails CI** · every claim binds the ledger digest, the formula ID and the
implementation digest.

Had this existed, all three fabricated figures found this week — `NFR-02`'s retired
`3/n`, the envelope's *"#81 auto-merged"*, the stage-2 record's `n=33` — would have
failed at the gate instead of at a reader's attention.

# 10. Enforcement level — stop calling detection prevention

| Level | Meaning |
|---|---|
| `EL0_DOCUMENTED` | Policy text only |
| `EL1_DETECTIVE` | CI detects; cannot prevent merge or push |
| `EL2_PREVENTIVE` | Branch protection / ruleset enforces required checks |
| `EL3_ATTESTED` | Expected-source checks, signed evidence, merge reconciliation |

```yaml
enforcement_level: EL1_DETECTIVE
branch_protection: UNAVAILABLE_403
merge_queue: UNAVAILABLE
signed_attestation: UNAVAILABLE
human_merge_control: REQUIRED
```

**SecB is `EL1_DETECTIVE`.** The four gates detect; they prevent nothing, because
nothing stops a merge. The `if: github.event_name == 'pull_request'` guards make
this concrete — a skipped job can count as success — but the deeper reason is that
`main` has no protection at all. The fix is a wrapper job that runs on every event
and returns one of `PASS` / `FAIL` / `VALIDATED_NOT_APPLICABLE` /
`UNSUPPORTED_EVENT_FAIL_CLOSED`, so **a gate never communicates "passed" by not
running**. `.github/` is constitutional: separate work package.

# 11. Merge order is a prerequisite relation, not a queue

Green and `clean` do not order anything. Measured against the tracked files rather
than assumed:

| PR | Depends on | Why |
|---|---|---|
| #111 stage-2 verdict | — | Independent |
| #113 this assessment | **#111** | It states #111's contradiction is fixed; that claim is only true on `main` once #111 is there |
| #103 identifier registry | — | Touches only `config/identifier_taxonomy.json` |
| #101 secret scan | — | Adds a new script; touches none of #105's tracked controls |
| #105 control surface | — | Its digests cover 4 scripts + the envelope; **none of #101, #103, #111, #113 modifies any of them**, so its manifest survives any order |
| #110 envelope correction | **#105** | It edits `config/delegation_envelope.json`, which #105 tracks by digest — it must bump the manifest in the same PR |

So exactly two edges exist: **#111 → #113** and **#105 → #110**. Everything else is
free. I checked this against the diffs rather than inferring it from PR numbers or
age, which is what the disposition asked for.

# 12. Size disclosure — precedence selects a verdict, it must not hide findings

```yaml
size_assessment:
  changed_lines: 797
  autonomous_merge_cap: 600
  absolute_ceiling: 2000

  autonomous_cap_result: EXCEEDED
  absolute_ceiling_result: PASS

  effect:
    auto_merge_eligible: false
    human_ratification_permitted: true

  disposition: ABOVE_AUTONOMY_CAP_BELOW_ABSOLUTE_CEILING
```

**This is not a waiver of the absolute ceiling**, and it is not correct to write
that the cap "was never evaluated" merely because `G1` decided the verdict first.
The governing principle:

> **Precedence selects the final verdict. It must never suppress a finding that
> lost to precedence.**

The current classifier short-circuits: it finds a governance path, returns
`AGENT_BALLOT_REQUIRED`, and never evaluates size. The verdict is right and the
evidence output is incomplete. A future atomic delta should make evaluation
**exhaustive** — every applicable rule produces a finding, the verdict is the most
restrictive consequence among them, and all findings survive into the output with
a `dominant_reason` and `additional_reasons`. Recorded here rather than built:
`scripts/classify_authority_delta.py` is a constitutional path and this is not
that work package.

Conditions under which this size is acceptable, all met: everything is decision
record, intake register, taxonomy and the tests they require · **no `WP-02`
implementation is mixed in** · `DECISION_AUTHORITY.md` is untouched · the count is
below the absolute ceiling after rebase · and the human reviewer is told the
number explicitly, which is this section.

Separately, `config/delegation_envelope.json` names both limits `max_changed_lines`
— one under `scope`, one under `absolute_ceilings`. The bare name does not say
which is the delegation limit and which is repository-wide. Renaming them
(`change_limits.autonomous_merge` / `change_limits.absolute.waivable: false`) is a
later atomic delta on a constitutional path, not this one.
