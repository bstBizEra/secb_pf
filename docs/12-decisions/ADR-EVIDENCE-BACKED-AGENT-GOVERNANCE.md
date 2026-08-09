# ADR — Evidence-Backed Agent Governance

Status: Accepted on merge of `SECB-WP-FWK-012` (issue #20) — the Genesis Ratification
Date: 2026-08-10
Authority: Operator (vily), design supplied in session 2026-08-10
Supersedes: the standing-authorization approach of `SECB-WP-FWK-011` (#18, PR #19 closed unmerged)

## Context

`SECB-WP-FWK-011` proposed a standing `R1` merge authorization guarded by a
path list: touch a protected file, a human merges. Its own pull request
classified as `HUMAN_REQUIRED` — correct, and also the signal that the design
answered the wrong question.

Path protection conflates two different changes. A refactor of a gate that
provably decides every case identically expands no authority; a two-line edit
to a ceiling expands all of it. Both touch `scripts/`. Meanwhile the binary
verdict named the *approver species* — "human" — which bakes in an assumption
that will be wrong as soon as the constitutional authority becomes a committee
or an external body.

The operator supplied a replacement model: separate governance into layers,
classify a change by the **authority delta** it produces, and let an agent
merge anything it can prove stays inside a delegation envelope ratified in
advance.

## Decision

Adopt the model, and install the half that is self-enforcing here.

**Four layers** (`docs/00-governance/L0_ROOT_CONSTITUTION.md`): L0 root
constitution, L1 delegation envelope, L2 policy implementation, L3 operational
change — each naming who may change it.

**Authority-delta classification** replaces path protection.
`scripts/classify_authority_delta.py` maps a diff to `G0`–`G5` and emits one of
five verdicts: `AUTO_APPROVED`, `AUTO_APPROVED_WITH_CONDITIONS`,
`AGENT_BALLOT_REQUIRED`, `CONSTITUTIONAL_REQUIRED`, `REJECTED`.
`HUMAN_REQUIRED` is retired: a verdict names the authority level required, not
who holds it.

**Dual-policy rule** (`scripts/check_dual_policy.py`) is the load-bearing
mechanism. Every PR is evaluated twice — once by the classifier and envelope on
the base ref, once by the versions the PR would leave behind. Both must pass
**and agree**. A head envelope that widens its own scope therefore cannot use
that widening to approve the widening: base says `CONSTITUTIONAL_REQUIRED`,
head says `AUTO_APPROVED`, and the divergence escalates. This delivers the
essential property of two-epoch activation with no infrastructure at all.

**Pre-authorized authority ladder** `A0`–`A4` with promotion conditions
recorded in the envelope. Advancing a rung is `G3` — exercising authority the
constitutional authority defined in advance. Inventing a rung is impossible.

**Genesis Ratification:** the operator's merge of this pull request is the one
human act that establishes delegation. After it, `G0` work inside the envelope
merges autonomously; the operator's attention moves to constitutional change.

## What is deliberately NOT built, and why

Recorded in full in `docs/14-plans/GOVERNANCE_DEFERRED_CAPABILITIES.md` with
the probe output that establishes each blocker. In summary:

- **External trusted verifier** — needs an organization ruleset. This account
  is a personal account with zero organizations; repository rulesets and
  branch protection both return `403`. Compensating control: any change under
  `.github/` or to the classifier is `G4`.
- **Signing and transparency log** — a signature verified by a script the same
  PR could edit is ceremony, not assurance. Deferred behind the anchor.
- **The five-role ballot council — not activated.** This is the most important
  refusal in this ADR. Five independent agents with separate enforced
  identities do not exist here. One session emitting five role-labelled
  ballots is self-approval in five hats, and role labels are self-asserted
  text that must never gate a decision. `ballot_layer.state` is `NOT_ACTIVE`,
  quorum is enforced nowhere in code, and `AGENT_BALLOT_REQUIRED` therefore
  escalates rather than resolving. The schema ships so the evidence format
  exists when identities do.
- **Merge queue** — depends on branch protection.
- **Golden corpus and confusion matrix** — twelve work packages is not a
  corpus; accuracy figures from it would be numbers without power.

## Consequences

**Accepted**

- Governance changes are judged by what they do to authority, not by which
  directory they live in. An identical-outcome refactor is `G1`, not
  constitutional.
- The self-approval hole is closed by construction, and the closure is tested:
  a widened head envelope cannot approve its own widening.
- The vocabulary survives a change in who holds constitutional authority.
- Every unbuilt capability has a named blocker and an unblocking action, so
  the gap between the model and the deployment is legible.

**Costs and residual risks**

- The classifier reasons over paths, sizes, and deletion signatures — not
  semantics. An `R2`-magnitude behavioural change confined to `src/` under the
  cap still reads `G0`. The work-package tier declaration remains an honest
  obligation, and the test and budget gates remain the substantive checks.
- `AGENT_BALLOT_REQUIRED` is currently unsatisfiable. Governance
  implementation work therefore still reaches the operator — less delegation
  than the model describes, and the honest amount given who exists.
- The verifier lives in the repository it judges. `G4` on `.github/` is a
  mitigation, not a solution.
- Two classifier invocations per PR roughly double the governance job's cost.
  Negligible at this scale, and it buys the anti-self-approval property.

## Alternatives considered

- **Merge `SECB-WP-FWK-011` first, then supersede it** — rejected. It would
  place a retracted design in `main` as active policy, the defect class this
  repository keeps fixing.
- **Activate the ballot council with one agent wearing five roles** — rejected
  as governance theatre. It would produce evidence that looks like SoD while
  providing none, which is worse than an honest escalation.
- **Keep `HUMAN_REQUIRED` as a generic verdict** — rejected; it names the
  species of approver and would need renaming the moment a council exists.
- **Wait for the external anchor before changing anything** — rejected. The
  dual-policy rule is the highest-value component and needs no anchor;
  deferring it would leave the self-approval hole open for no gain.

## Revocation

The constitutional authority may revoke or narrow delegation at any time by
statement in session or a comment on issue #20 — effective immediately, no
pull request required. Envelope expiry has the same effect by default:
delegation lapses rather than persisting unexamined.
