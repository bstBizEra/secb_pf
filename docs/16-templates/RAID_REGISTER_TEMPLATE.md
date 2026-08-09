# Template — RAID Register

Derived from `docs/01-requirements/RAID_REGISTER.md`. Risks · Assumptions ·
Issues · Dependencies, plus the standing constraints the project operates under.
One register, not four overlapping ones.

Reviewed at **every** stage gate. Entries are appended and struck through, never
overwritten — a register whose history is editable cannot support a gate record.

---

## Risks

| ID | Risk | Impact | Likelihood | Treatment | Owner |
|---|---|---|---|---|---|
| R-01 | | | | | |

A risk entry with an empty Treatment column is a worry. Treatment is either a
control now in force, or an accepted risk with a named compensating control and
a review date.

## Assumptions

| ID | Assumption | If false |
|---|---|---|
| A-01 | | |

The **If false** column is the point. An assumption whose falsity has no stated
consequence was not worth recording. Assumptions that would reopen a passed gate
should say so — they become that gate's revalidation trigger.

## Issues (open)

| ID | Issue | Effect |
|---|---|---|
| I-01 | | |

Open issues only. Closed issues stay in the table struck through with the date
and the artifact that closed them, so a later reader can see what was resolved
rather than wondering whether it was ever noticed.

## Dependencies

| ID | Dependency | Needed by | Status |
|---|---|---|---|
| D-01 | | Stage `<n>` gate | Outstanding / Met `<date>` |

"Needed by" is a **stage**, not a date. Dates slip; the gate does not move.

## Constraints

Standing limits the project cannot trade away — ceilings, immutable artifacts,
prohibited actions, expiry dates. Unlike risks, these are not treated; they are
obeyed.
