# Stage-Gate Decision Record — `REQUIREMENTS_READY`

Prepared by: Claude (executor), `SECB-WP-FWK-020` (issue #38)
Template: `docs/16-templates/STAGE_GATE_RECORD_TEMPLATE.md`
Carries the twelve evidence-minimum fields of `DELIVERY_LIFECYCLE.md` §3.

> **This record is prepared, not issued.** The `decision` field is empty. Stage
> 2's gate authority is the Product Owner and the Architecture Lead. In this
> deployment both collapse onto the operator, under
> `docs/00-governance/SINGLE_IDENTITY_SOD_ACCEPTED_RISK.md` — cited here as that
> record's condition 1 requires of every gate record from stage 3 onward, applied
> from stage 2 because the collapse is already in effect.

## Evidence minimum (§3)

| Field | Value |
|---|---|
| Project / release identifier | SecB Engineer Loop · pre-release, no version tag |
| Stage and gate identifier | Stage 2, Requirement Decomposition → gate `REQUIREMENTS_READY` |
| Artifact versions | `PRD-ENGINEER-LOOP.md` **v1.0.0 baselined** · `REQUIREMENT_CATALOGUE.md` v1 (20 FRs) · `NFR_CATALOGUE.md` v1 (18 NFRs) · `RTM.md` v1 · `BOOTSTRAP_STORY_DOR.md` **v0.1** · `RAID_REGISTER.md` (7 risks, 6 assumptions, 6 issues, 5 dependencies, 5 constraints) |
| Evidence references | Merge commits `9045241` (catalogues + RTM), `29da444` (bridge + DoR), `32252f3` (canonical DoR split) · issues #32 #34 #36 #38 |
| Findings | All seven exit conditions assessed; **five met, two met with qualification.** Two findings recorded below, neither at blocker level |
| Exceptions | `TX-01` `FR-12` unverifiable here · `TX-02` authority-ladder conditions never checked · `TX-03` `FR-19`/`FR-20` adopted but unimplemented · `I-01` narrowed: stages 3–6 still hold no recorded verdicts |
| Risk assessment | Bearing on this gate: `R-06` (KPI measurability, reduced to Medium) and `R-04`/`R-05` (collapsed authorities, accepted for stages 1–8). No High risk is unique to this gate |
| Conditions and owners | Four recommended below, each with an owner and a milestone |
| Eligible approvers | Operator, as Product Owner and Architecture Lead. **No Architecture Review Board exists** — the collapse is accepted, not ignored |
| Votes / signatures | **None. Unissued.** |
| Decision timestamp | — |
| Effective status | **`PREPARED_AWAITING_VERDICT`** |
| Expiry / revalidation | On any change to the PRD baseline, to a priority-one requirement, or to an accepted conflict disposition (§4 change control) |

## Exit-condition assessment

Verbatim from `DELIVERY_LIFECYCLE_STAGES.md` §2, assessed against the tree at
this commit.

| # | Condition | State | Evidence |
|--:|---|---|---|
| 1 | Every approved PRD objective maps to one or more requirements | **Met** | `REQUIREMENT_CATALOGUE.md` objective-coverage table: O1→10 requirements, O2→2, O3→2, O4→4, O5→1, O6→1. O5 and O6 are flagged as thin in the catalogue itself rather than counted as robust |
| 2 | Every requirement has an owner and acceptance method | **Met with qualification** | All 20 rows carry both. **But `FR-17`'s acceptance method is descriptive, not executable** — see finding 1 |
| 3 | Critical business rules are documented | **Met by recorded non-applicability** | The catalogue records that no financial, pricing or domain calculations exist; the applicable rules are `L0_ROOT_CONSTITUTION.md` and the classifier, already normative. **This is a vacuous satisfaction and the authority should rule on it explicitly**, not inherit it |
| 4 | NFRs carry measurable targets | **Met with qualification** | 18 NFRs, each with a target and a stated basis. `NFR-08` (loop lead time) is marked *provisional* — a target with no basis, because K-06 has never been computed. Seventeen of eighteen have real bases |
| 5 | Dependencies and external interfaces are identified | **Met** | `RAID_REGISTER.md` D-01…D-05; external interfaces are the GitHub API and GitHub Actions, both in `NFR_CATALOGUE.md` (`NFR-13`) |
| 6 | Priority-one items satisfy the Bootstrap Story DoR v0.1, and remaining unresolved items are not at Blocker level | **Met with a named gap** | 12 of 13 ready. `FR-12` fails criterion 3 — its acceptance method cannot execute here. Argued non-blocker: nothing in stages 3–8 consumes it. Recorded as `TX-01`, not waived |
| 7 | Material requirement conflicts are resolved or formally accepted | **Met** | Four conflicts formally accepted in the catalogue: six of ten gates still prose · O5's cadence claim · O6's pilot authorization · `FR-12`'s unverifiability. Plus `CONFLICT-FWK-019` at `CANONICAL_RESOLVED` |

## Findings

**Finding 1 — `FR-17`'s acceptance method cannot be executed.**
`FR-17` requires that authority advancement follow a ladder whose rungs are
pre-authorized. Its acceptance column cites the envelope's `authority_ladder`
and the fact that `A3`/`A4` are unreachable — both true, and neither a test.
`TX-02` in the RTM records the underlying gap: **nothing checks that 30 clean
merges precede `A2`.** The ladder is read for the current tier and never
evaluated for advancement.

Exit condition 2 is satisfied in form — the column is filled — and a filled
cell that names an unexecutable method is not the same as an acceptance method.
Recorded rather than smoothed, because the alternative is a catalogue where the
column means "someone wrote something".

**Finding 2 — condition 3 is vacuously satisfied.**
There are no critical business rules to document, so the condition cannot fail.
That is a defensible pass and it is not the same as evidence of work. The
authority should accept the non-applicability explicitly; inheriting a vacuous
pass is how a checklist quietly stops meaning anything.

## Recommended conditions, if the authority chooses `APPROVED_WITH_CONDITIONS`

| # | Condition | Owner | Due |
|--:|---|---|---|
| D-1 | Make `FR-17` executable: a test asserting the ladder's advance conditions, or an explicit record that advancement is a manual `G4` act with no automated check | Executor | Before any tier advance is proposed |
| D-2 | Give `NFR-08` a basis by computing K-06 once from existing GitHub timestamps, or withdraw the target | Executor | Before stage 6 |
| D-3 | Accept, in the verdict, that condition 3 is satisfied by non-applicability | Operator | With the verdict |
| D-4 | Carry `FR-12` into stage 3 as a known gap with its closing condition (first bootstrap of a second project) | Executor | At stage 3 entry |

## Available verdicts (§2)

`APPROVED` · `APPROVED_WITH_CONDITIONS` · `REWORK_REQUIRED` · `BLOCKED` ·
`REJECTED` · `HUMAN_REQUIRED`

**`REWORK_REQUIRED` and `BLOCKED` are not indicated**: no condition is unmet, no
external dependency prevents progression. **`APPROVED` is available but weak** —
it would absorb findings 1 and 2 silently, and both deserve an owner.
`APPROVED_WITH_CONDITIONS` with D-1…D-4 is the recommendation.

## Stage 3 entry map

Stage 3's entry criteria name artifacts stage 2 either folded in or recorded as
not applicable. Mapped here so Architecture Design does not open by hunting for
a document that was deliberately never written.

| Stage 3 entry criterion | Satisfied by | Note |
|---|---|---|
| Approved requirements baseline | `REQUIREMENT_CATALOGUE.md` + this gate's verdict | The verdict is what makes it *approved* |
| NFR catalogue | `NFR_CATALOGUE.md` | 18 NFRs, 17 with real bases |
| Integration inventory | `NFR_CATALOGUE.md` `NFR-13`, `NFR-16` | **No separate document.** Two integrations — GitHub API, GitHub Actions. Recorded as folded-in, not missing |
| Data and security requirements | Data: recorded not applicable (no user data; git objects, CI records, JSON config). Security: `NFR-16`…`NFR-18` | Security *design* is stage 5; security *requirements* exist now, which is what stage 3 entry asks for |

## Effect of this verdict, once issued

- Stage 2 passes; state advances to `REQUIREMENTS_READY`.
- Stage 3 (Architecture Design → `ARCHITECTURE_APPROVED`) opens, with the entry
  map above as its handoff.
- Traceability exception `I-01` narrows again: stages 3–6 remain without
  recorded verdicts.
- The `FR-12` gap and findings 1–2 travel forward as conditions, not as
  resolved items.

## To issue this verdict

The gate authority states the verdict, the date and any conditions — in session
or as a comment on issue #38. The executor then fills this record and updates
the lifecycle position table in the same change, citing it.
