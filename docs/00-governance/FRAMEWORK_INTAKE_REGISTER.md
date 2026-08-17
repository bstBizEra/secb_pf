# Framework Intake Register

Work package: `SECB-WP-FWK-057` · Issue: #112 · Opened: 2026-08-13
Authority: Operator disposition, 2026-08-13
Status: **`RATIFICATION_PENDING`** — effective on the merge of PR #113

```yaml
lifecycle: RATIFICATION_PENDING
binding: false                    # becomes true at the effective event, not by this text
effective_event: PR_113_MERGED
```

> **This register does not bind yet.** Every rule below is written in the
> present tense because that is how a register reads once effective — but until
> the merge, its status is `WILL_CLOSE_AT_EFFECTIVE_EVENT`, not closed. The
> defect this session kept finding was a record asserting its own force; moving
> that defect from the word `ISSUED` into the word *"binding"* would be the same
> error wearing different clothes.

> **Why this exists.** Five framework proposals accumulated in intake, each
> individually defensible, none adopted, all addressing overlapping territory:
> decision classes, autonomy tiers, ballots, evidence schemas. The risk was never
> any single proposal — it was that five unresolved ones would eventually be
> installed by accretion, each borrowing legitimacy from the others' presence.
> **The register makes "assessed" and "in force" impossible to confuse.**

## Rules while this register is open

- **No proposal may describe itself as a governing framework.** Being assessed,
  cited, or having its vocabulary borrowed is not adoption.
- **Only atomic control deltas are accepted** — a change that closes one proven
  gap and alters no authority.
- **Every accepted control names its source proposal**, so provenance survives.
- **Merging several proposals under a new name does not make them approved.** A
  rename is not a ratification.

## Register

| Proposal | Status | Extracted controls |
|---|---|---|
| `BACP-v1.1` | `NOT_ADOPTED` | — |
| `ADEC-v1.0` | `NOT_ADOPTED` | — |
| `RAAF-v0.1` | `NOT_ADOPTED` | — |
| `FPSA-v1.0` | `NOT_ADOPTED` | — |
| `DAAF-v2.0` | `NOT_ADOPTED_AS_FRAMEWORK` | `NORMATIVE_SURFACE_CLASSIFICATION` · `CLAIM_VERIFICATION` · `APPEND_ONLY_DECISIONS` · `AUTHORITY_CEILING` · `DIGEST_BOUND_EVIDENCE` |

**Extracted ≠ adopted, and extraction does not promote the source.** `DAAF-v2.0`
stays `NOT_ADOPTED_AS_FRAMEWORK` however many of its controls are eventually built.
The authority model that replaced its `D2` proposal —
[`AUTONOMOUS_AUTHORITY_MODEL.md`](AUTONOMOUS_AUTHORITY_MODEL.md), `AR0`–`AR4` and
EBTA — is a SecB decision under `CONFLICT-SECB-AUTONOMY-001`, **not** an adoption of
DAAF §4. DAAF proposed three ballots as sufficient; that specific proposal was
rejected, and EBTA's conjunction of machine-checkable proofs is a different
mechanism reached for a different reason.

**`NOT_ADOPTED` is not a rejection of the findings.** Each proposal's analysis
remains in `docs/17-references/` and its measurements stand. What is withheld is
governing force.

## What writing this register already surfaced

`ANALYSIS-DAAF-V2.md`'s first draft asserted that `FPSA v1.0` *"already binds"* the
DAAF proposal and was *"the right instrument"* for judging it. **FPSA is not
adopted** — it exists only as `docs/17-references/ANALYSIS-FPSA-V1.md`, with no
governance document behind it. Its taxonomy is used in places as analytical
vocabulary (`FPSA-03` in the envelope's `classification_notes`), and borrowed
vocabulary had been mistaken for binding rule.

That is precisely the confusion this register exists to prevent, and it was found
**by writing the register** — the first proposal it corrected was the executor's own
reasoning about a proposal.

## Adopted governance, for contrast

So that "in force" has an address. Everything normative in SecB lives here or in
`config/`:

`L0_ROOT_CONSTITUTION.md` · `DECISION_AUTHORITY.md` · `CONTROL_GATES.md` ·
`RISK_AUTHORITY_MATRIX.md` · `BUDGET_CIRCUIT_BREAKER_POLICY.md` ·
`TWO_PLANE_DECISION_MODEL.md` · `SPECIFICATION_CONFLICT_PROTOCOL.md` ·
`SINGLE_IDENTITY_SOD_ACCEPTED_RISK.md` · `config/delegation_envelope.json` ·
`config/identifier_taxonomy.json`

**If a document is not in that list and not in `config/`, it does not bind** — no
matter how carefully it is written or how often it is cited.

## Reopening

A proposal moves off `NOT_ADOPTED` only by a constitutional decision naming it, its
version, and the authority accepting it. Extracting a control from a proposal does
**not** change the proposal's status: `DAAF-v2.0` stays `NOT_ADOPTED_AS_FRAMEWORK`
however many of its controls are eventually adopted.
