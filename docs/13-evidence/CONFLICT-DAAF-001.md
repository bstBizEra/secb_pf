# `CONFLICT-DAAF-001` — may a `D2` decision be autonomously ratified?

Work package: `SECB-WP-FWK-057` · Issue: #112 · Recorded: 2026-08-13
Protocol: [`SPECIFICATION_CONFLICT_PROTOCOL.md`](../00-governance/SPECIFICATION_CONFLICT_PROTOCOL.md)
Type: **`SC-05` Authority conflict** · Impact: **`C4` — Authority or safety**
Status: **`RESOLVED` — pending ratification.** Operator disposition given 2026-08-13;
**effective on the merge of PR #113, not on this text**

> **Resolved by the constitutional authority, not by the executor.** `C4` is
> *constitutional authority only*, and the executor is the party whose authority the
> proposal would have widened — so recording the conflict was the whole of what the
> executor could do. The operator has now ruled; §9 carries the disposition. The
> status is `RESOLVED` **pending ratification**: this document does not become
> effective by asserting that it is, and the merge of PR #113 is the ratifying act.

## The two statements, verbatim

**Statement A — in force.** `docs/00-governance/DECISION_AUTHORITY.md`:

> Everything at `D2` and above reaches a human **by design.** Independent agent
> identities would make `D1`'s ballot satisfiable and supply `E3` evidence; they
> would not move `D2`+ authority, because that authority is about business
> consequence rather than technical correctness.

**Statement B — proposed.** DAAF v2.0 §4, `D2 MATERIAL` — *"stage verdict,
acceptance, condition posture, risk acceptance"*:

> Auto-ratify ได้เฉพาะ 3 independent ballots ภายใน authority envelope

with roles `FACT_AUDITOR`, `POLICY_EVALUATOR`, `RISK_REVIEWER`, unanimous quorum,
author excluded, ballots bound to `head_sha` + `decision_digest` +
`evidence_digest` + `policy_bundle_sha256`, and stale on any head change.

They cannot both hold. `A` says agent identities *do not* move `D2` authority; `B`
makes three of them sufficient for it.

## Why this is `SC-05` and not `SC-04`

It is tempting to file this as a terminology collision — two `D2`s — and settle it
by renaming. **That would hide it.** DAAF's `D2 MATERIAL` and SecB's `D2` denote the
same class over the same domain, and DAAF's examples (*stage verdict, acceptance,
condition posture, risk acceptance*) are exactly SecB's `D2` cases. The proposal is
not using the token differently; it is **proposing a different authority for the
same class.** Renaming would leave the authority change intact and unexamined.

The separate naming problem — `D0–D3` against a registered `D0–D4` — is real and is
recorded as `F1` in `ANALYSIS-DAAF-V2.md`. It is not this conflict.

## The unaddressed reason

Statement A gives a reason, and the proposal does not answer it. Stated as sharply
as possible:

**Three independent verifiers raise confidence that a claim is true. A `D2`
decision asks who owns the consequence if it is false.**

`FACT_AUDITOR` can confirm every claim, `POLICY_EVALUATOR` can run a deterministic
matrix correctly, `RISK_REVIEWER` can enumerate every consequence — and the
question of who is accountable for accepting a risk on the organization's behalf is
untouched by all three. That is what statement A means by *"business consequence
rather than technical correctness."*

**This is not an argument that DAAF's mechanism is weak.** Its ballot protocol —
digest-bound, author-excluded, stale-on-push — is stronger than anything this
repository has, and if `D2` were an evidence question it would be the right answer.
The dispute is over what kind of question `D2` is.

## What the resolution formula yields

`SPECIFICATION_CONFLICT_PROTOCOL.md` prefers the resolution changing original
intent least. Applied here:

| Option | Changes intent | Verdict |
|---|---|---|
| Adopt `B` for all `D2` | Reverses a stated design decision and its reason | Requires constitutional authority |
| Reject `B` | Preserves `A`; DAAF's evidence-side mechanisms remain available and are recommended separately | Least change, and the default if no decision is taken |
| **Split `D2`** — evidence-determined vs ownership-determined | Preserves `A`'s reason while allowing autonomy where no ownership question exists | Smallest change that satisfies both, **and it is a new class, so `C4` still** |

The third option is the interesting one and is offered, not recommended: if some
`D2` decisions turn out to be purely evidentiary — a condition-posture update whose
inputs are all machine-checked, say — then `A`'s reason does not reach them, and
they could be autonomously ratified without contradicting it. **That requires
someone to partition `D2` by whether a decision carries ownership**, which is a
constitutional act and not an engineering one.

## Blocking scope

```yaml
blocks:
  - DAAF-WP-05   # Independent Ballot Protocol
  - DAAF-WP-06   # Capability Issuer and Router Admission Control
does_not_block:
  - DAAF-WP-02   # Semantic Impact Classifier -- closes the proven gap, needs no D2 ruling
  - DAAF-WP-03   # Claim Compiler and Statistical Verifier
  - INV-03       # scope-relative conditions
  - INV-04       # append-only after effectivity
```

**The conflict does not block the part of DAAF worth building.** Semantic
classification and claim verification make decisions *better evidenced* at every
class; neither moves authority, so neither depends on this ruling.

## Also unmet, independently of the ruling

Even decided in DAAF's favour, `B` is **unimplementable today**: it requires three
distinct principals and SecB has one identity
(`SINGLE_IDENTITY_SOD_ACCEPTED_RISK.md`). A single principal casting three
role-labelled ballots is precisely the self-approval the protocol exists to
prevent. So a ruling for `B` would authorize a mechanism that cannot yet run — which
is a reason to rule deliberately rather than urgently.

## What the operator is deciding

> **Is `D2` authority a question about evidence quality, or about ownership of
> consequence?**

If evidence — statement A's reason fails, and DAAF's ballot protocol is the correct
mechanism once identities exist. If ownership — statement A stands, and `D2` stays
human regardless of how good the verification becomes. **A third answer, that some
`D2` decisions are one and some the other, requires partitioning the class.**

Recorded for decision. Not decided here.


# 9. Disposition — operator, 2026-08-13

**Statement A stands. Statement B is rejected.**

> คง `D2+ = HUMAN_RATIFICATION_REQUIRED` ตาม `DECISION_AUTHORITY.md` เดิม — Agent
> ballots เพิ่มความเชื่อมั่นต่อหลักฐาน แต่ไม่โอนความรับผิดชอบต่อผลลัพธ์จาก accountable
> owner ไปยัง Agent.

The question this record put — *is `D2` about evidence quality or ownership of
consequence?* — is answered: **ownership.** Agent ballots raise confidence in the
evidence; they do not transfer responsibility for the outcome from the accountable
owner to an agent. Verifier count is not a source of accountability.

**The third option is not taken.** `D2` is not partitioned into evidentiary and
ownership halves. That option remains available to a future constitutional decision
and is not foreclosed — but it is not adopted here, and no `D2` case becomes
autonomously ratifiable.

| | |
|---|---|
| `D2+` ratification | **Human. Unchanged** |
| Agent autonomy ceiling for `D2+` | **`RATIFICATION_READY`** — full autonomy up to it, none through it |
| Three-ballot auto-ratify | **`REJECT_AUTHORITY_CHANGE`** |
| DAAF v2.0 as a framework | **`NOT_ADOPTED_AS_FRAMEWORK`** |
| DAAF's evidence-side mechanisms | Accepted as control deltas — see `ANALYSIS-DAAF-V2.md` §6 |
| `F3` posture, recorded | **`MULTI_ROLE_SINGLE_PRINCIPAL`** — three role labels on one principal is not a quorum and may never be recorded as one |

## What the agent may do, and where it stops

```text
Agent drafts verdict → evidence verified → policy result determined
  → RATIFICATION_READY  ←  the autonomy ceiling for D2+
       ↓ human merges                    ↓ human rejects or amends
    EFFECTIVE                          RETURNED
```

Autonomy is **not reduced** by this ruling: everything up to `RATIFICATION_READY`
is the agent's, including drafting the verdict, verifying every claim and running
the deterministic matrix. What is withheld is the final transition — and that was
already withheld. The ruling declines to move it, rather than moving it back.

## Why this closes without self-widening

The executor recorded the conflict, refused to resolve it, and did not edit
`DECISION_AUTHORITY.md` while the question was open. The rule that constrains the
executor was changed by nobody — **which is the outcome, not a technicality.** A
proposal to widen agent authority was assessed by the agent it would widen, and the
only thing the agent did with it was write it down and hand it over.

## Remaining scope of this record

None. `CONFLICT-DAAF-001` closes on ratification. It creates no condition, blocks
no stage, and its `blocking_scope` on `DAAF-WP-05` / `-06` is discharged by those
work packages not being adopted.
