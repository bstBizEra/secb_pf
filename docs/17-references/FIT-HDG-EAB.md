# Fit Assessment — HDG-EAB v1.0 against SecB

Status: Assessment complete · **fits, adopt in three tiers** · nothing adopted here
Work Package: `SECB-WP-FWK-025` (issue #46)
Subject: Human Decision Gateway with Evidence and Agent Ballots v1.0, supplied
by the operator 2026-08-10

## Verdict

**It fits, and it corrects something this session has been doing wrong from the
start.** The framework's governing principle —

> *Agents prove what is technically viable. Humans choose which business
> consequence is acceptable. Policies prevent either side from authorizing what
> is outside its competence or authority.*

— is compatible with SecB's `L0`–`L3` layering, maps cleanly onto `G0`–`G5` and
`R0`–`R4`, and supplies the one thing SecB has never had: **a defined shape for
what an escalation to a human should contain.**

## 1. Verified citations

| Claim | Verified |
|---|---|
| NIST supports explicitly differentiated human–AI responsibilities and documented risk tolerance | **Yes.** The AI RMF requires that *"policies and procedures are in place to define and differentiate roles and responsibilities for human-AI configurations and oversight of AI systems"*, with roles, responsibilities and lines of communication documented and clear; it expects systems classified by potential impact so intensive human review concentrates on high-stakes decisions ([NIST AI RMF Core](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/), [Human-AI configuration](https://airc.nist.gov/airmf-resources/airmf/appendices/app-c-ai-risk-management-and-human-ai-interaction)) |
| Separation of duties means no single actor can propose, verify, authorize and execute its own change | **Yes, and more crisply than paraphrased.** NIST: *"no user should be given enough privileges to misuse the system on their own"*, enforceable **statically** by defining conflicting roles, or **dynamically** at access time such as a two-person rule ([NIST glossary, SP 800-192](https://csrc.nist.gov/glossary/term/separation_of_duty)) |

The static/dynamic distinction matters for SecB: the one-repository-per-role
design in `ANALYSIS-AUTONOMY-CEILING.md` is *static* enforcement. Sealed
independent voting is *dynamic*. HDG-EAB asks for both; SecB has neither yet.

## 2. The defect this exposes — evidenced from this session

**12 operator merges. 0 decision packets.**

Every escalation asked the operator to approve a technical artifact or issue a
gate verdict:

| Escalation | What was asked | HDG-EAB class of the question |
|---|---|---|
| PR #37 | "install the Specification Conflict Protocol" | Approve a governance artifact — **not a business outcome** |
| PR #29 | "record the stage-1 verdict" | Issue a gate verdict — technical vocabulary |
| Issue #38 | "`APPROVED_WITH_CONDITIONS` or `REWORK_REQUIRED`?" | Technical gate choice |
| PR #21 | "Genesis Ratification" | Correctly `D4`, but presented as an artifact review |

None of them contained:

- **Three viable options.** Every escalation carried one recommendation,
  take-it-or-leave-it. Where alternatives were listed, they were listed as
  *unavailable* (`REWORK_REQUIRED` is not indicated) rather than as choices.
- **What happens if no decision is made.** Never stated once.
- **A business-impact matrix.** Escalations carried line counts, verdicts and
  test totals — the technical assurance layer presented *as* the decision.
- **The exact question in business terms.** Never *"do you accept this
  consequence"*; always *"do you approve this change"*.

The executive verdict of HDG-EAB is that a human ballot should ask *"do we accept
a three-day delay to materially reduce outage risk"* and not *"should we approve
this migration algorithm"*. Measured against that, this session has been asking
the second question twenty times in a row, while telling itself the human gate
was working because the human kept saying yes.

## 3. Element-by-element gap

| HDG-EAB element | SecB today |
|---|---|
| `D0`–`D4` authority classes | Partly present as `G0`–`G5`, but keyed to *authority delta*, not to *business materiality*. Nothing distinguishes a costly reversible change from a cheap one |
| Mandatory human-decision triggers (budget, scope, date, customer-visible, SLO, lock-in, irreversible migration, accepted risk) | **Absent.** SecB triggers on *paths and size*, which is exactly the semantic blindness recorded in `ADR-EVIDENCE-BACKED-AGENT-GOVERNANCE.md` |
| Three-Option Requirement (HDG-EAB calls it "Rule of Three") | **Absent** |
| Project Impact Choice Matrix (13 dimensions) | **Absent** |
| Scoring with policy vetoes above score | Absent; no scoring exists |
| Agent Decision Council, 7 voting roles + 2 non-voting | `ballot_layer NOT_ACTIVE`; also SecB's proposer **is** its own recommender and merger — HDG-EAB makes the Proposal Agent **non-voting** |
| Sealed votes, no vote visible before submission | Absent |
| Evidence levels `E0`–`E4` | Evidence exists and is strong, but **unleveled**. `FWK-009`'s independent review was `E3`; the FIT suite is `E2`; no production telemetry, so nothing is `E4` |
| Evidence auditor separate from ballot compiler | Absent — the executor does both |
| Minority opinion carried into the packet | Absent; no dissent mechanism exists |
| Fail-safe no-response defaults | **Absent and worth fixing cheaply.** Today a non-response simply stalls; nothing states that silence means no deploy, no governance amendment, no irreversible migration |
| Ballot lifecycle with `INVALIDATED_BY_NEW_EVIDENCE` | Absent; SecB has stage states, not decision states |
| `D4` protected-governance list and no-self-approval | **Present and working** — `G4` on every governance path, proven by the Genesis PR's own verdict |

Two rows are already satisfied. The rest are gaps, and the largest are not
technical: they are about *what the human is asked*.

## 4. Three genuine conflicts to resolve before adoption

**C-1 — a fifth verdict vocabulary, and a sixth.** SecB already reconciles four
(merge authority, stage gate, conflict resolution, and the metric standard's
verdicts). HDG-EAB adds **human ballot choices** (`APPROVE_OPTION_A` …
`ABSTAIN_CONFLICT_OF_INTEREST`) *and* **agent vote types** (`SUPPORT`,
`POLICY_VETO`, `ABSTAIN_INSUFFICIENT_EVIDENCE` …) *and* **ballot lifecycle
states**. Adoption must extend the reconciliation table in
`SPECIFICATION_CONFLICT_PROTOCOL.md`, not overlap tokens. `REJECTED` and
`APPROVE_WITH_CONDITIONS` already appear in two other sets.

**C-2 — `D2` needs an authority SecB does not have.** `D2 MATERIAL` assigns final
authority to the *product/business owner*, and `D3` to *business owner + risk
owner*. In SecB all of these collapse onto one identity under
`SINGLE_IDENTITY_SOD_ACCEPTED_RISK.md`. HDG-EAB's classes are therefore
*nominally* distinguishable and *actually* identical here. That does not block
adoption — the packet shape is valuable even with one approver — but the class
distinction must be recorded as nominal until a second authority exists, or it
will be mistaken for a control.

**C-3 — thirteen artifacts against the Lean gate.** Three Python modules, six
schemas, two policy files, a template, a register and an ADR. SecB's measured
product surface is `WPS` 12.38 across 6 items. Building a `ballot_quorum_engine`
for a council that cannot convene, and a `decision_classifier` for a decision
volume of roughly five `D2`+ decisions in one session, is the over-engineering
the minimality ladder exists to prevent. **The decision model is cheap and
valuable; the machinery is not yet earned.**

## 5. Correction to `SECB-WP-FWK-024`

`FWK-024` claimed independent agent identities are *"one change [that] unblocks
four walls"*, including stage 9 and the ladder's `A3`/`A4`. **That claim was too
strong, and HDG-EAB shows why.**

Its quorum table states that for `D3`–`D4`, *"agents remain advisory only."* So
independent identities unblock:

- `D1 CONTROLLED` authority — **fully**
- the *technical assurance* layer of `D2`–`D4` — **fully**, including the `E3`
  evidence that stage 9's independence requirement needs, since §6 permits an
  *"independent model, tool, team or qualified technical assessor"*

They do **not** unblock:

- `D2`'s business-outcome authority, which is the product owner's by definition
- `D3`/`D4` final authority, which remains human by design

Restated correctly: **independent identities unblock the evidence and the `D1`
authority. They do not unblock the business decision.** Stage 9 becomes reachable
because its *evidence* can be independently produced — but the release decision
above it stays human. The four walls are not equally removable, and
`ANALYSIS-AUTONOMY-CEILING.md` should be read with this correction attached.

This also sharpens the autonomy target. `FWK-024` projected ~100% of
non-constitutional merges. Under HDG-EAB the honest projection is: ~100% of `D0`
and `D1`, with every `D2`+ decision reaching a human **by design, not by
limitation**. Given that most of this session's work was `D1`, that is still a
large gain — but the ceiling is a feature.

## 6. Recommendation — adopt in three tiers

| Tier | Content | Cost | When |
|---|---|---|---|
| **1 — now** | `D0`–`D4` authority matrix mapped onto `G0`–`G5`/`R0`–`R4`; the mandatory human-decision trigger list, with project thresholds set once in the charter and unchangeable inside a ballot; the Human Decision Packet template including the Three-Option Requirement and the twelve required sections; fail-safe no-response defaults; `E0`–`E4` evidence levels applied retroactively to existing evidence; vocabulary reconciliation | Documentation only, ~4 files | On approval |
| **2 — when identities exist** | Agent Decision Council roles, vote types, sealed voting, quorum table, non-voting proposer, evidence auditor separate from ballot compiler | Depends on the one-repo-per-role design | After the identity decision |
| **3 — trigger-gated** | `decision_classifier.py`, `ballot_quorum_engine.py`, `evidence_verifier.py`, six schemas, `decision_register.jsonl` | Substantial | When `D2`+ decision volume or a real quorum makes hand-running the model the bottleneck |

### The immediately actionable part

Two decisions are pending right now: the `REQUIREMENTS_READY` verdict (#38) and
the `O7` re-baseline. **Both should be re-issued as Decision Packets rather than
as verdict requests** — three options each, business-impact matrix, consequence
of not deciding, exact question. That is Tier 1 applied to live work rather than
described, and it is the cheapest possible proof that the fit is real.

## 7. What this record does not do

Nothing is adopted. The authority matrix and the trigger list change how
escalation decisions are classified, which makes their adoption `D4`/`G4` — the
operator's, and by this framework's own §11, an amendment the agent system may
propose but not approve.
