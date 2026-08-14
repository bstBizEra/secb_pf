# Addendum 001 to the `REQUIREMENTS_READY` decision record

Work package: `SECB-WP-FWK-060` · Issue: #116 · Recorded: 2026-08-13
Amends: [`STAGE_GATE_REQUIREMENTS_READY.md`](STAGE_GATE_REQUIREMENTS_READY.md)
Authority: operator, amended stage-2 verdict of 2026-08-13

> **This is an addendum because the record it amends is `EFFECTIVE`.** The stage-2
> verdict took effect at 2026-08-12T17:33:16Z with the merge of PR #111 as `c94e4da`.
> `INV-04` forbids editing a decision record after effectivity, so the original is
> **not touched**: not one row, not one finding, not the verdict. An amended verdict
> that rewrote its predecessor would destroy the evidence of what was actually
> decided first — and the ability to see a decision reconsidered is the whole value
> of keeping both.

## What the amended verdict adds

The verdict itself is unchanged: **`APPROVED_WITH_CONDITIONS`**, 7/7 objectives, 7/7
criteria, baseline `APPROVED`, posture `OPEN_NON_BLOCKING`. Stage 3 stays `OPEN` with
authority ceiling `ARCHITECTURE_APPROVED`.

What changes is the **condition set**. Three conditions are added:

| # | Condition | Owner | Instrument |
|---|---|---|---|
| `C-5` | `G-02` is replaced by a squash-aware content-and-provenance proof | Executor | Corrections in `GENESIS_RATIFICATION_AUDIT.md`; forward control `TR-01` (#118) |
| `C-6` | An `L0` amendment prohibits non-fast-forward update of a canonical ref, **with preventive enforcement** | Operator (`G4`) | #117 — `RATIFIED_NOT_EFFECTIVE` until `NEG-01`…`AUD-01` pass live |
| `C-7` | Human/operator identity is separated from the agent's App identity | Operator + executor | #115 (`WP-05`) — before the next autonomous canonical merge |

**`C-6` and `C-7` are due before the *next autonomous canonical merge*, not before
stage 3 work.** Design and architecture proceed; what is gated is the next time an
agent lands a change on `main` without a human in the path.

## `C-3` and `C-4` remain open — not closed by omission

`GATE-005`: a condition absent from a new verdict stays `OPEN`. Both carry forward
unchanged, from `CONDITION_REGISTER.md`, which stays authoritative:

| ID | Blocking scope | Status |
|---|---|---|
| `C-3` | Stage 6 | `OPEN` |
| `C-4` | Stage 5 | `OPEN` |

So the obligation posture after this addendum is `OPEN_NON_BLOCKING` over **five**
conditions, none of which blocks stage 3.

## Binding

```yaml
amends_record: docs/13-evidence/STAGE_GATE_REQUIREMENTS_READY.md
amended_record_status: EFFECTIVE
amended_record_effective_at: "2026-08-12T17:33:16Z"
amended_record_ratified_by: c94e4da72ad04ec4d928f8268d96af20375cedad
amended_record_digest_at_amendment: sha256:77a34e955319c33cfcc3bee63a1c08efdd630dddc694983a3024c644f18550da
addendum_number: 001
verdict_unchanged: APPROVED_WITH_CONDITIONS
conditions_added: [C-5, C-6, C-7]
conditions_carried: [C-3, C-4]
conditions_closed: []
stage_3_admission: OPEN
authority_ceiling: ARCHITECTURE_APPROVED
```

The digest binds this addendum to the exact bytes of the record it amends. **If that
record changes, the pair has drifted and this binding is how a reader finds out** —
which is the property a prose cross-reference cannot provide.

## What this addendum does not do

- **It does not re-open stage 2.** The gate passed; conditions were added to a passing
  verdict, which is what `APPROVED_WITH_CONDITIONS` is for.
- **It does not close anything.** No condition, no finding, no exception.
- **It does not change the authority ceiling.** Stage 3 remains capped at
  `ARCHITECTURE_APPROVED`; `C-4` still blocks stage 5 and `C-3` still blocks stage 6.
- **It does not touch the traceability exception `I-01`.** The router still holds
  artifacts at stages 7–8 with no recorded verdicts beneath them.
- **It creates no new condition beyond the three named**, and it originates none of
  them — all three are the operator's, quoted from the amended verdict.
