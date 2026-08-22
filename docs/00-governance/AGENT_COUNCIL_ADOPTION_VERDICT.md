# Agent Council — adoption verdict

**Record class:** operator verdict, recorded in structure.
**Verdict as given:** `APPROVED_WITH_CONDITIONS`
**Recorded by:** SECB-WP-FWK-120 · **Recorded at:** 2026-08-23

> This records an operator decision. Unlike the four mandate records (#187, #203, #204, #205) it is
> **not** `PROPOSED` — the adoption decision was made. What is recorded here is its content and the
> conditions attached, so that "approved with conditions" names conditions someone can check rather
> than a sentiment.

## 1. The role assigned, as given

```text
Artifact Author → Agent Council Review → Deterministic Validation
                → SecB Authority / Policy Gate → Promotion or Remediation
```

Agent Council is adopted as a **Multi-Perspective Review & Assurance Layer** between the artifact
author and the Stage Gate. It is explicitly **not** the final approver, not a System of Record, and
not permitted to change project state.

```text
Agent Council          analyse · dissent · recommend · produce review evidence
SecB                   authority · policy · evidence · state transition
CI / validators        the deterministic facts
Authorized principal   accepts risk, approves beyond mandate
```

The verdict's own reasoning for the boundary: a persona holds no authority by title, so a Council
result is an **evidence input**, never an approval. `Council verdict → SecB gate computes eligibility.`

## 2. Verdict vocabulary, as given

```text
RECOMMEND_PASS · RECOMMEND_PASS_WITH_CONDITIONS · BLOCKED · INCONCLUSIVE
```

With rules that matter more than the tokens: a `BLOCK` from a mandatory domain reviewer yields
`BLOCKED`; a missing member or incomplete input yields `INCONCLUSIVE` rather than a pass; the Council
Lead synthesises and **holds no tie-break**; no agent may override a `Block`; and majority does not
decide truth.

## 3. Staleness, as given

A Council result becomes `STALE` when the source SHA, artifact digest, API contract, migration, or
test-set epoch changes, and a stale result may not promote a new revision.

That is the same binding this repository already enforces for shadow-queue receipts, arrived at
independently — `expires_on_change: true` is the receipt's cohort rule under another name.

## 4. Vocabulary

Verified by `tests/test_mandate_vocabulary.py`. Status vocabulary is closed.

| Prefix | Used for | Registry status |
| :--- | :--- | :--- |
| `L` | L0–L4 risk levels: Mechanical, Local, Significant, Critical, Irreversible | COLLIDES — registered `L0-L3`, governance layers |
| `P` | P0/P1 findings, in the auto-trigger list | NEW |

### 4.1 `L0` would invert the repository's most authoritative identifier

```text
registered   L0-L3   governance layers — "L0 root constitution, L1 delegation envelope,
                     L2 policy implementation, L3 operational"
             home    docs/00-governance/L0_ROOT_CONSTITUTION.md
verdict      L0-L4   risk levels — L0 = "Mechanical: typo, formatting, generated index"
```

In this repository **`L0` denotes the root constitution**, and it is the constitution's filename. The
verdict makes `L0` denote the most trivial class of change there is. Not two unrelated meanings — an
inversion, from maximum authority to minimum consequence, on the same token.

### 4.2 This is the third claimant to `L0-L4`, and the registry already refused the second

The recorded collision reads:

```text
meanings          L0-L3 = governance layers, and L0 is the constitution's filename (in force)
                  L0-L4 = BACP v1.1 artifact layers (proposed, NOT adopted)
observed_status   SECOND_CLAIMANT_NOT_ADOPTED
disposition       BLOCKED -- may not enter SecB as bare L-n. Reserved alternative below.
reserved          M0-M4, for BACP's artifact layers
```

Same prefix, same form, same arity of five. The registry refused the second claimant and reserved a
free prefix for it. By that precedent — the one applied to `A` in issue #184 — the risk ladder is a
**BLOCKED-class** collision, and the disposition is: set-qualify at every use, or bind it to a free
prefix. **`M` is not available**; it is already reserved for BACP.

### 4.3 `P` is unregistered and already in use

`P0`/`P1` appear in the verdict's auto-trigger list. `P` has no registry entry, and `P1`/`P2` already
occur 35 times across the declared carriers. Registration is owed under **home → use → register**.

## 5. What the verdict already resolves, and what it leaves open

Resolved by the verdict itself, and worth recording because each closes a question this repository had
open:

- Council output is evidence, not approval — the separation `may_delegate: const false` enforces for
  grants, stated for reviews.
- A reviewer that edits a candidate invalidates its own review: *"SHA and evidence binding changed."*
- `security-audit` is not a penetration test, and production infrastructure sits outside its scope.
- The upstream package's defaults are project-specific and must not be copied wholesale.

Left open, and not decidable here: the `L` prefix, the eight new personas, the eleven proposed review
workflows, and which stages gain them first. The verdict states Stages **02, 07, 09, 11** are not yet
covered to production depth.

## 5.1 This record's Vocabulary table is currently unverified

`tests/test_mandate_vocabulary.py` (SECB-WP-FWK-116) selects its subject set by **filename glob**:

```python
GOVERNANCE.glob("*MANDATE*.md")
```

This document is a **verdict**, not a mandate, so it does not match — and the table in §4 is checked
by nothing. The gap is in the control, not in this record: a governance document's coverage should
not depend on whether its title happens to contain a word.

```text
SUBJECT_SET_BY_FILENAME ≠ SUBJECT_SET_BY_KIND
```

Filed against the control rather than worked around by renaming the file, because renaming a verdict
to "mandate" would make the filename lie in order to satisfy a check — which is the failure mode the
check exists to prevent, inverted.

## 6. What this document is not

- Not an adoption of the `L0–L4` ladder. §4.2 records why.
- Not an authorization to build the eleven review workflows.
- Not a claim that §4 is complete — measured at one commit, by one agent, no independent verification.
