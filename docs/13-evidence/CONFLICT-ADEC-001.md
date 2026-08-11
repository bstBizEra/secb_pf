# Specification Conflict Record — `ADEC-001`

Status: **`SPEC_OWNER_REQUIRED`** (conflict-resolution vocabulary) — impact `C4`,
reserved to the constitutional authority
Raised by: `SECB-WP-FWK-037` (issue #70) · Protocol:
`docs/00-governance/SPECIFICATION_CONFLICT_PROTOCOL.md`
Analysis: `docs/17-references/ANALYSIS-ADEC-V1.md` §2

## Source assertions — quoted verbatim, neither paraphrased

**A — in force.** `docs/00-governance/DECISION_AUTHORITY.md:35-36`, merged as
`SECB-WP-FWK-026` (`93ac85d`):

> | `D2 MATERIAL` | Material scope, cost, release date, UX or SLO impact | Agent
> ballot + technical attestation | **Product / business owner** | `G1`–`G2` ·
> `R2` |
> | `D3 HIGH_RISK` | Production migration, sensitive data, security boundary,
> external commitment | Independent technical assessment (`E3`+) | **Business
> owner + risk owner** | `G2` · `R3` |

**B — proposed.** Operator message of 2026-08-11, *"ADEC v1.0"* §3, table
*"Decision Authority Classes"*:

> | D2 CONTROLLED | Code/CI change ภายใน architecture และ authority เดิม |
> ได้เมื่อ ballot และ evidence ผ่าน |
> | D3 HIGH-IMPACT | Production, migration, security boundary | ได้เฉพาะ
> pre-authorized playbook + canary + rollback |

with the preamble:

> เพื่อไม่ให้สับสนกับ autonomy level A1–A4 ให้ใช้ชื่อ `D0–D4`

## Classification

```yaml
conflict_id: ADEC-001
types:
  - SC-04   # terminology collision: one term, two meanings
  - SC-05   # authority conflict: an agent is told it may decide what it may not
impact_level: C4          # authority or safety
authority_change: true    # D2 moves from business-owner authority to agent-decidable
security_reduction: false # no control is removed; the authority boundary shifts
resolution_authority: constitutional  # C4 is not agent-resolvable
```

`authority_change: true` is the field that decides the handling. `C1`–`C3`
conflicts are resolvable by ballot; `C4` is *"constitutional authority only"*
(`SPECIFICATION_CONFLICT_PROTOCOL.md:60`). An agent may raise this record and may
not resolve it — including this one.

## The collision, stated plainly

The two tables label the same five slots and disagree about one boundary:

| Class | A — in force | B — ADEC | Agreement |
|---|---|---|---|
| `D0` | `ROUTINE`, agent | `OBSERVATIONAL`, agent | Same authority, different name |
| `D1` | `CONTROLLED`, agent under policy | `REVERSIBLE`, agent | Same authority, **name moved** |
| `D2` | `MATERIAL`, **product / business owner** | `CONTROLLED`, **agent on ballot + evidence** | **Disagree** |
| `D3` | `HIGH_RISK`, business + risk owner | `HIGH-IMPACT`, agent on pre-authorized playbook | Disagree in degree |
| `D4` | `CONSTITUTIONAL` | `CONSTITUTIONAL`, no self-approval | Agree |

**`D2` is the first class an agent may not decide under A, and the last class it
may decide under B.** The token `CONTROLLED` names `D1` under A and `D2` under B,
so a future document citing *"`D2 CONTROLLED`"* can be read as granting or
withholding agent authority depending on which table the reader holds.

`D3` disagrees in degree rather than in kind: A requires two named human owners,
B requires a pre-authorized playbook with canary and rollback. B's condition is
stricter *machinery* under weaker *authority* — and SecB has zero canary
evidence (`E4` = none) and zero rollback drills, so B's condition is currently
unsatisfiable anyway.

## Why this is not editorial

An `SC-04` collision alone would be `C0`–`C1`: split the name, define each, done.
This one carries `authority_change: true`, and the change is invisible at the
point of use. Nothing fails when the tables are swapped — a document keeps citing
`D2`, the classifier keeps returning `G`-verdicts, CI stays green. The only
observable difference is that a class of decision which previously reached a
human stops reaching one.

That is the same failure shape as the two defects this repository has already
recorded: `AGENTS.md` asserting branch protection that did not exist (#407), and
a gate record counting its own verdict among its criteria (`GATE-001`). In all
three, the document and the reality diverge silently and the divergence favours
the agent.

## Impact analysis

| Question | Answer |
|---|---|
| Affected gate | None mechanically — no code reads the `D` classes. They gate **human escalation**, which is enforced by reading |
| Affected artifacts | `DECISION_AUTHORITY.md`; `docs/16-templates/DECISION_PACKET_TEMPLATE.md`; both issued packets (001, 002); any future ADEC kernel document |
| Blocked downstream | The ADEC kernel specification cannot be installed while two `D2` definitions exist — it would ship the ambiguity into policy |
| Blocked stages | None. Stages 2 and 3 do not depend on the `D` classes |
| Existing decisions affected | None retroactively: packets 001 and 002 both name their class explicitly and were both escalated |

## Provisional resolution — in force until the authority rules

**`A` prevails.** The `D`-class names and authority boundaries in
`DECISION_AUTHORITY.md` remain the ones in force. Any document referring to a
decision class uses A's names, and `SC-03`'s *"apply the stricter gate
provisionally"* selects A at `D2` because A escalates where B does not.

**What this does not replace:** it does not reject ADEC's proposal. B's column is
a legitimate target state, and the analysis recommends importing it **as a
separate, explicitly named column** — *"agent-decidable under ADEC, when
activated"* — beside the authority in force, so the gap is visible as a roadmap
instead of overwriting the boundary.

**What it does not do:** it does not settle `D3`. B's canary-and-rollback
condition is stricter machinery than A requires and is unsatisfiable here today;
whether it eventually *replaces* two human owners or merely *precedes* them is an
authority question, not a wording one.

## Closing condition

This record closes when the constitutional authority states, in an appendable
decision record, which of the following holds:

1. **A stands, B is a roadmap** — B's authority column is imported as a distinct
   labelled column and no boundary moves. *No `L0` change needed.*
2. **B replaces A at `D2`** — `D2` becomes agent-decidable on ballot + evidence.
   This is an authority expansion: `G4`, and it cannot take effect while
   `ballot_layer.state = NOT_ACTIVE`, because the ballot it depends on cannot
   convene.
3. **A different split** — e.g. B's names with A's boundaries, which the analysis
   advises against because it moves `CONTROLLED` one class without moving the
   authority, maximising the ambiguity rather than removing it.

Until then the provisional resolution above is what agents follow, and the status
of this record stays `SPEC_OWNER_REQUIRED`.

## Evidence pack

| Item | Location |
|---|---|
| Authority in force | `docs/00-governance/DECISION_AUTHORITY.md:29-53` |
| Three-axis separation the collapse would undo | `DECISION_AUTHORITY.md:39-42` |
| Impact ladder placing `C4` with the constitutional authority | `SPECIFICATION_CONFLICT_PROTOCOL.md:56-61` |
| `SC-03` stricter-gate rule used for the provisional resolution | `SPECIFICATION_CONFLICT_PROTOCOL.md:41` |
| Why B's `D3` condition is unsatisfiable today | `DECISION_AUTHORITY.md:99` (`E4` = none) |
| Why B's `D2` ballot cannot convene | `config/delegation_envelope.json` `ballot_layer.state` |
| Full component mapping | `docs/17-references/ANALYSIS-ADEC-V1.md` |

## What this record does not do

It does not resolve the conflict, and it does not treat having been written as a
resolution. It also does not amend `DECISION_AUTHORITY.md` — the provisional
resolution is *"the existing text stands"*, which requires no edit, and editing
governance to record that governance was not changed would be the churn the
anti-annotate rule forbids.
