# `CONFLICT-SECB-AUTONOMY-001` — a blanket human-ratification rule contradicts the mission

Work package: `SECB-WP-FWK-057` · Issue: #112 · Recorded: 2026-08-13
Protocol: [`SPECIFICATION_CONFLICT_PROTOCOL.md`](../00-governance/SPECIFICATION_CONFLICT_PROTOCOL.md)
Type: **`SC-05` Authority conflict** · Impact: **`C4` — Authority or safety**
Status: **`RATIFICATION_PENDING`** — operator disposition of 2026-08-13; effective on
the merge of PR #113, not on this text

> **Supersedes `CONFLICT-DAAF-001` §9 before it took effect.** That disposition
> ruled *"Statement A stands — `D2+` requires human ratification."* It was recorded
> on this same pull request and **never became effective**, so this is an amendment
> to a proposal, not a retraction of a governing rule. That distinction exists only
> because `SECB-WP-FWK-056` separated `PROPOSED` from `EFFECTIVE` the day before;
> under the collapsed field this reversal would have required retracting something
> the record claimed was already in force.

## The two statements

**Statement A — proposed yesterday, never effective.** `DECISION_AUTHORITY.md` and
`CONFLICT-DAAF-001` §9: everything at `D2` and above reaches a human by design,
because that authority concerns business consequence rather than technical
correctness.

**Statement B — the mission.** SecB exists so that an Agentic Engineering Team
designs, builds, verifies, merges, deploys and repairs **without depending on a
human who holds no engineering competence.** `PRD-ENGINEER-LOOP.md` objective `O7`:
*"Minimise human involvement: drive every non-constitutional decision to autonomous
execution, so that humans act on constitutional change and as the trust anchor
rather than in the loop of each decision."*

They cannot both hold. `A` routes every material engineering decision to a human
reviewer; `B` says that reviewer is the wrong authority for engineering questions
and the loop's purpose is to remove them from it.

## Why `A` was wrong, precisely

`A`'s reasoning was that `D2` asks *who owns the consequence if the decision is
wrong*, and no quantity of agent verification supplies an owner. **That reasoning is
correct and it does not imply `A`'s conclusion.**

The error is a conflation: it treated *owning the consequence* and *reviewing the
engineering* as the same act. They are not.

| | Owns the consequence | Reviews the engineering |
|---|---|---|
| Business intent owner | **Yes** — budget, legal exposure, risk tolerance, mandate | **No** — holds no engineering competence |
| Agentic team | No | **Yes** — architecture, tests, security design, merge readiness |

An owner can accept consequence **once, in advance, over a bounded domain** — which
is what a standing mandate is. Requiring them to re-accept it per pull request does
not increase their ownership; it forces an engineering judgement onto the party
least equipped to make it, and calls the resulting rubber stamp a control.

## Disposition — operator, 2026-08-13

```yaml
decision:
  blanket_d2_human_ratification: REJECTED
  three_agent_ballots_alone: REJECTED
  evidence_backed_agent_authorization: APPROVED_FOR_DESIGN
  human_engineering_review: NOT_REQUIRED
  business_mandate_boundary: REQUIRED
```

**Three agent ballots alone are still rejected**, and this is not a compromise
position — it is the one finding from `CONFLICT-DAAF-001` that survives intact.
Agents can fail in *correlated* ways: identical training, identical prompt framing,
identical blind spots. Majority voting and self-verification are unreliable exactly
where they are most needed, and a weak verification mechanism is the dominant
failure mode in multi-agent systems. **More votes is not more evidence.**

What replaces human engineering review is therefore not a larger ballot but
**Evidence-Backed Technical Authorization** — a deterministic controller evaluating
a conjunction of machine-checkable proofs, with agent opinions admitted as
*supporting evidence* rather than as the decision. See
[`AUTONOMOUS_AUTHORITY_MODEL.md`](../00-governance/AUTONOMOUS_AUTHORITY_MODEL.md).

## What each party owns after this

| Business intent owner | Agentic engineering team |
|---|---|
| Business objective · priority · acceptance outcome · KPIs · financial and resource envelope · risk tolerance · prohibitions · legal or external commitments not pre-approved | Architecture correctness · security design · test sufficiency · code quality · merge readiness · deployment mechanics · incident remediation · technical governance |

The human is the **trust anchor and the mandate author**, not the reviewer. That is
`O7` as written, and `A` had inverted it.

## `D0`–`D4` is not reinterpreted

The historical ladder keeps its meaning; every existing `D2` citation continues to
mean what it meant. Authorization routing moves to a **new namespace `AR0`–`AR4`**,
registered in `config/identifier_taxonomy.json`. Rebinding `D` would have made every
prior record ambiguous — the defect the registry exists to prevent, and the reason
`F1` was resolved the same way for `NS`.

```text
NS  = what the change touches
AR  = how the change is authorized
BM  = which outcomes are already delegated
D   = historical decision-class ladder, unchanged
```

## This does not become exercisable on ratification

Ratifying this changes the **model**, not the **capability**. §9 of
`AUTONOMOUS_AUTHORITY_MODEL.md` records why the platform cannot yet back autonomous
material merges: no branch protection, three gates that skip on push, `skipped`
counted as success, one principal, no expected-source required checks, and no
release controller separate from the builder. **A green 4/4 is not an EBTA
certificate**, and no agent may treat it as one.

## Why one human ratification is still required

The agent cannot widen its own authority — that prohibition is upstream of this
conflict and is untouched by it. So the mandate must be granted **once**, by the
authority that holds it. **That act is not an engineering review**: it states which
outcomes the organization delegates and within what envelope, which is precisely
the business decision the disposition assigns to the human.

After that single act, the engineering loop needs no human in it.
