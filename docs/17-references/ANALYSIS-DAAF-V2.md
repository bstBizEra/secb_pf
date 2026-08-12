# Analysis — DAAF v2.0 intake assessment

Work package: `SECB-WP-FWK-057` · Issue: #112 · Recorded: 2026-08-13
Subject: **SecB Decision-Aware Bounded Autonomy Framework v2.0**, operator-supplied
Status: **assessment — nothing adopted.** No `DAAF-WP` is implemented by this record

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
could not be true. Corrected at `6f57d91`: `verdict_generated_at` separated from
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

### `F6` — `FPSA v1.0` already binds this, and is the right instrument

FPSA's invariant: *"no proven gap, no minimal delta, no bounded authority, no
rollback and retirement path — no framework expansion."*

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
