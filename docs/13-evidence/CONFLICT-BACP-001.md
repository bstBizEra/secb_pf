# Specification Conflict Record — `BACP-001`

Status: **`SPEC_OWNER_REQUIRED`** (conflict-resolution vocabulary) — impact `C3`,
gate semantics, resolvable only by the authority that set the rule being changed
Raised by: `SECB-WP-FWK-041` (issue #80) · Protocol:
`docs/00-governance/SPECIFICATION_CONFLICT_PROTOCOL.md`
Assessment: issue #79

## Source assertions — quoted verbatim, neither paraphrased

**A — in force.** `AGENTS.md` header, made authoritative by `SECB-WP-FWK-003`:

> Status: Framework documented; three control gates executable
> (`SECB-WP-FWK-002`, `SECB-WP-FWK-004`); implementation started
> (`SECB-WP-FWK-010`)
>
> This header is the single source of truth for project status
> (`SECB-WP-FWK-003`). Other documents, including `docs/INDEX.md`, describe the
> state of their own domain and defer to this header for the state of the
> project. […] `src/secb_router/` holds router v1.5.1 (the F1 fix on the sealed
> baseline); the skill-router MVP package is `SANDBOX_TESTED` under review
> `REV-SECB-ENGLOOP-MVP-001-20260810` (`SECB-WP-FWK-009`); runtime adoption,
> external/mutating routing and production autonomy remain `NOT_AUTHORIZED`.

**B — proposed.** Operator-supplied *"BACP v1.1"* of 2026-08-11, §1.2:

> The canonical model SHALL NOT contain: […] a verdict about the present state of
> a particular implementation; […] an example that can be confused with an
> authorized production record.

and §21 rule 10:

> Present operational status SHALL never be inferred from the existence of a
> model.

## Classification

```yaml
conflict_id: BACP-001
types:
  - SC-03   # gate mismatch: two rules disagree about what a document may contain
impact_level: C3          # gate semantics -- artifact ownership changes
authority_change: false   # no authority boundary moves either way
security_reduction: false
resolution_authority: the authority that set FWK-003's rule
```

**Not `C4`.** Nothing about who may approve what changes. What changes is *which
file owns project status*, which is artifact ownership — `C3`.

## Both sides are deliberate, which is what makes this a conflict

This is not a defect found in careless work. `SECB-WP-FWK-003` **chose** to put
status in the constitution, and it chose correctly for the problem it had: status
had drifted across documents, and `docs/INDEX.md` overstating the baseline was
*"the first defect this repo ever found"*. A single authoritative header fixed
that, and it has held.

BACP §1.2 is equally deliberate, and its reasoning also holds: a canonical
document containing a present-tense verdict cannot be copied into a second project
without carrying a false claim. That is not hypothetical here — `AGENTS.md` is the
**first** file the bootstrap runbook tells a new project to take, and it is one of
the 13 files `NFR-15` measures as requiring an edit.

So the two rules are each right about a different failure, and they contradict on
one file.

## Measured scope — the rest of the governance layer is already compliant

Counted across `AGENTS.md`, `docs/00-governance/` and `docs/16-templates/` — the
canonical layer the bootstrap runbook copies as-is:

```bash
grep -oE "\(#[0-9]{1,3}\)|issue #[0-9]{1,3}|PR #[0-9]{1,3}|\b[0-9a-f]{7}\b" \
  AGENTS.md docs/00-governance/*.md docs/16-templates/*.md
```

**8 tokens, and all eight are ratification provenance:**

| File | Token |
|---|---|
| `DECISION_AUTHORITY.md:3` | *Adopted on merge of `SECB-WP-FWK-026` (issue #48)* |
| `L0_ROOT_CONSTITUTION.md:3` | *Ratified on merge of `SECB-WP-FWK-012` (issue #20)* |
| `SPECIFICATION_CONFLICT_PROTOCOL.md:3` | *Effective on merge of `SECB-WP-FWK-019-A` (issue #36)* |
| `TWO_PLANE_DECISION_MODEL.md:3` | *Effective on merge of `SECB-WP-FWK-031` (issue #58)* |
| + 4 more | same shape |

A record of **what authorized a document** is not a claim about present state, and
§1.2 does not prohibit it. **So the conflict is confined to one file and one
header** — a better result than the assessment expected, recorded because the
alternative was to imply a wider problem than the measurement supports.

## Provisional resolution — in force until the authority rules

**`A` prevails.** The header stays where it is and stays authoritative. `SC-03`
directs applying the stricter gate provisionally, and `A` is stricter in the sense
that matters: removing the single status authority before its replacement exists
would restore the drift `FWK-003` was created to stop.

**What this does not do:** it does not reject `B`. The portability defect is real
and measured.

## Recommended canonical resolution

Keep the principle, move the data:

1. `AGENTS.md` retains the rule — *"one file is the single source of truth for
   project status"* — and **points to** that file instead of being it.
2. Project status moves to one instance file, e.g. `docs/13-evidence/PROJECT_STATUS.md`,
   carrying the header's present content unchanged.
3. The bootstrap runbook's copy classification marks that file **do-not-copy**,
   alongside the sealed evidence package.

This satisfies both rules rather than trading one for the other: `FWK-003`'s
intent is preserved exactly — there is still exactly one authoritative place — and
`AGENTS.md` becomes copyable without carrying another project's status. It also
removes one file from `NFR-15`'s remaining 13.

**Not done in this work package.** It edits `AGENTS.md`, a `constitutional_path`,
and it reverses the placement chosen by a merged ruling. An executor proposing that
is correct; an executor landing it is not.

## Closing condition

This record closes when the authority states which holds:

1. **Adopt the pointer split** — the recommendation above. `AGENTS.md` change is
   `G4`; the new status file is `G0`.
2. **`A` stands unchanged** — status stays in the constitution, and BACP §1.2 is
   adopted with a recorded exemption for this header, so the exception is visible
   rather than a silent non-compliance.
3. **Neither** — BACP §1.2 is not adopted, and this record closes as
   `RESOLVED_BY_SPEC_OWNER` with no change.

Option 2 is the one worth naming explicitly: an adopted rule with an undeclared
exception is worse than an unadopted rule, because it looks enforced.

## Evidence pack

| Item | Location |
|---|---|
| The header in force | `AGENTS.md:1-19` |
| The ruling that made it authoritative | `SECB-WP-FWK-003` |
| The first defect it was created to stop | `docs/INDEX.md` overstatement, cited in `docs/15-runbooks/NEW_PROJECT_BOOTSTRAP.md:43` |
| Measured token count in the canonical layer | 8, all provenance — command above |
| Why `AGENTS.md` is the exposed file | `NEW_PROJECT_BOOTSTRAP.md`; `NFR-15`'s 13-file surface |
| Assessment of BACP v1.1 | issue #79 |

## What this record does not do

It does not amend `AGENTS.md`, and it does not treat having been written as a
resolution. It also does not adopt BACP v1.1 — that remains blocked on the `L0`
prefix collision recorded in `config/identifier_taxonomy.json`, which is a
separate decision from this one.
