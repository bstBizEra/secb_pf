# Research — "Rule of Three": three claimants, one name

Status: Research complete · **decision applied** in `SECB-WP-FWK-034` (issue #64)
Conflict class: `SC-04 terminology collision` — default action *split the name and
define each*
Occasion: the operator supplied a third meaning on 2026-08-10 while two were
already live in the repository, and instructed research to cut to one

## The three claimants

| # | Concept | Where it lives in SecB |
|--:|---|---|
| A | **Arithmetic** — find the fourth proportional from three knowns | Nowhere. Proposed 2026-08-10 |
| B | **Statistical** — zero events in *n* trials ⇒ 95% upper bound `3/n` | `K-09`, and cited in seven documents |
| C | **Three options** — a decision packet must offer three viable choices | Packet template, `DECISION_AUTHORITY.md`, both issued packets |

## Provenance, which is what decides this

### A — arithmetic: the oldest and the primary sense

It is not merely old, it is the origin of the phrase. **Trairāśika** is the Sanskrit
term for it, attested in the **Bakhshali manuscript**, believed composed in the
early centuries CE
([Trairāśika](https://en.wikipedia.org/wiki/Trair%C4%81%C5%9Bika)). In early modern
English arithmetic it was **the Golden Rule** — Hodder's *Arithmetick* (1702):
*"for as Gold transcends all other metals, so doth this Rule all others in
Arithmetick."* It was the standard measure of numeracy: eighteenth-century
apprenticeship indentures and wills required that a son or apprentice be taught
*"to cipher to the rule of three"*
([NCpedia](https://www.ncpedia.org/rule-three),
[Resourceaholic](https://www.resourceaholic.com/2020/02/the-rule-of-three.html)).

**Claim to the bare name: strongest.** Unqualified "rule of three" means this.

### B — statistical: a citable named result, conventionally qualified

Origin is a single landmark paper: **Hanley & Lippman-Hand, *"If nothing goes
wrong, is everything all right?"*, JAMA 249(13):1743–5, 1983**
([paper](https://jhanley.biostat.mcgill.ca/c607/ch08/zero_numerator.pdf)), whose
point was that observing zero events does **not** justify concluding the risk is
zero. Later literature keeps the name and the qualifier: Jovanovic & Levy, *A Look
at the Rule of Three*, *The American Statistician* (1997)
([paper](http://www.nicksun.fun/assets/misc_papers/Jovanovic_1997_A_look_at_the_rule_of_three_The_American_Statistician.pdf));
Tuyl, *The Rule of Three, its Variants and Extensions*, *International Statistical
Review* (2009)
([abstract](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1751-5823.2009.00078.x)).

Derivation, for the record: `(1−p)^n = 0.05` gives `n ln(1−p) = ln 0.05 ≈ −2.996`;
rounding to `−3` and approximating `ln(1−p) ≈ −p` yields `3/n`
([Rule of three (statistics)](https://en.wikipedia.org/wiki/Rule_of_three_(statistics))).

**Claim: strong but explicitly qualified.** The reference literature's own
disambiguation title is *"Rule of three (statistics)"* — the qualifier is not
decoration, it is how the field distinguishes this sense from A.

### C — three options: no canonical claim

This is a popular-management framing, grounded in the rhetorical **tricolon** and
in working-memory limits of roughly three to four chunks
([LearnMentalModels](https://learnmentalmodels.co/models/rule-of-three-model),
[Getting Results](https://gettingresults.com/explained-the-rule-of-3/)). It has no
single citable origin, and the nearest established construct with a real name is
the **Triple Constraint** / good-fast-cheap, which already has its own.

**Claim: weakest.** Nothing is lost by renaming it, because there is no citation
chain to preserve.

## Decision

| Claimant | Disposition |
|---|---|
| **A — arithmetic** | **Not imported.** Never enters the repository |
| **B — statistical** | **Keeps the name**, always qualified on first use per document: *the statistical rule of three (`3/n`)* |
| **C — three options** | **Renamed** to **Three-Option Requirement** |

### Why A is not imported, on SecB's own evidence

The only place proportional estimation looked applicable was work-package budget
forecasting — more files, more lines. Measured across all 30 merged work packages:

```text
correlation r = +0.62        (proportional estimation needs r near +1)
least-squares fit: lines = 25 + 66.7 × files
```

And a decisive counter-example: `SECB-WP-FWK-029` changed **8 files in 144 lines**
while `SECB-WP-FWK-032` changed **1 file in 243 lines**. Estimating the former from
the latter by proportion predicts **1,944** lines against an actual **144** — wrong
by **13×**. Observed lines-per-file ranges from 6 to 243, a fortyfold spread.

This is what §8 of the operator's own arithmetic document predicts: fixed costs
plus variable costs. The fit's intercept is the per-work-package overhead — ticket,
gate record, PR body — while the real variable is *depth of content*, not file
count. So SecB's two budget caps are **independent constraints, not a proportion**,
and importing A would add the name that owns the bare phrase in exchange for a
method the data rejects.

### Why B keeps it rather than C

B has a citation chain — Hanley & Lippman-Hand through Jovanovic & Levy to Tuyl —
and `NFR-10` requires every material claim to cite an artifact a third party can
open. Renaming B would break that chain for a naming convenience. C has no chain
to break.

## The stricter alternative, considered and not chosen

**Name none of them "rule of three."** Call B *the `3/n` bound* and C *the
Three-Option Requirement*, and reserve the bare phrase for nothing.

That is arguably cleaner: it removes the collision permanently rather than
resolving it in favour of one sense, and it would survive someone later importing
A. It was not chosen because the sources for B use the phrase, and a citation is
easier to follow when the cited name is the name used.

**The trade is recorded rather than hidden:** SecB keeps a name whose primary
meaning elsewhere is a different concept, and pays for that with a mandatory
qualifier on first use. If the qualifier is ever found missing in practice, adopt
the stricter alternative — the evidence for it is already here.

## Convention now in force

- The bare phrase "rule of three" refers to **B** and appears **only** with its
  qualifier on first use in a document.
- **C** is the **Three-Option Requirement**. Not "rule of three", not "rule of 3".
- **A** is called **proportional estimation** if it must be referred to at all, and
  it is not an approved estimation method in SecB.
- This is the same discipline already in force for verdict vocabularies: **name the
  set, never rely on a bare token.**

## Two deliberate exemptions from the rename

A grep for the bare phrase should return exactly these, and finding anything else
is a regression:

| Location | Why it is not renamed |
|---|---|
| `STAGE_GATE_PRD_BASELINED.md` (v1.0.0, **superseded**) | It is retained history. Rewriting the text of a superseded decision record to satisfy a later naming convention would alter what the record says was approved at the time — the exact reason it was banner-marked rather than deleted |
| `RESEARCH-STAGE1-GATE-INSTRUMENTS.md` source list | The line is a **citation title** — *"A Concise Guide to the Statistical Rule of Three"*. A cited title is quoted as published, never edited to match local convention |

Both already carry the qualifier in substance: one refers to `K-09`, the other is a
statistics source.
