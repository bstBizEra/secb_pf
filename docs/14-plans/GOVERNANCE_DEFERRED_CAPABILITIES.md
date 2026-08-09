# Deferred Governance Capabilities

Status: Open register
Work Package: `SECB-WP-FWK-012`
Purpose: the Evidence-Backed Agent Governance design assumes capabilities this
deployment does not have. Each is recorded here with the blocking reason and
the action that would unblock it, so partial adoption is never mistaken for
full adoption.

Verified 2026-08-10 against `bstBizEra/secb_pf`:

| Probe | Result |
| --- | --- |
| `gh api users/bstBizEra` | `type=User` — a personal account, not an organization |
| `gh api user/orgs` | `0` organizations |
| `gh api repos/.../rulesets` | `403 Upgrade to GitHub Pro or make this repository public` |
| `gh api repos/.../branches/main/protection` | `403` — same message |

## D1 — External trusted verifier

**Design:** the governance check runs outside the repository it judges, bound
to a GitHub App identity via an organization ruleset, so a pull request cannot
edit the verifier or spoof its status.

**Blocked because:** organization rulesets and required workflows are
organization/enterprise features. This repository is owned by a personal
account with no organizations, and repository rulesets and branch protection
both return `403`.

**Compensating control in force:** any change under `.github/`, to the
classifier, or to the dual-policy script classifies as `G4`
(`CONSTITUTIONAL_REQUIRED`). The verifier can be edited, but not by an
autonomous merge.

**Unblocking action (operator):** create an organization, transfer the
repository, and configure an organization ruleset whose required check is
bound to a GitHub App; pin any reusable workflow by full commit SHA.

## D2 — Cryptographic signing and transparency log

**Design:** the delegation envelope and every ballot are signed with a
workload identity and recorded in a transparency log, so integrity and
authorship are verifiable independently of git.

**Blocked because:** signing is only as strong as the anchor that verifies it.
With D1 open, a signature verified by a script the same PR could edit adds
ceremony rather than assurance.

**Compensating control in force:** the envelope is marked `UNSIGNED`; its
integrity rests on git history and the human merge that ratified it, both of
which are auditable.

**Unblocking action:** resolve D1, then sign the envelope and ballots and
verify signer identity in the external verifier.

## D3 — Independent agent ballot council

**Design:** five role-scoped agents (architecture, governance, security, QA,
operations), each with a separate enforced service identity, vote on
governance changes; 4-of-5 to pass, 5-of-5 for `G2`–`G3`, governance and
security hold veto, and the proposer may not vote.

**Blocked because:** those agents do not exist here. There is one session.
One agent emitting five role-labelled ballots is self-approval in five hats:
role labels are self-asserted text, and a decision must never be gated on
text the deciding party writes about itself.

**Compensating control in force:** `ballot_layer.state` is `NOT_ACTIVE`,
quorum is enforced nowhere in code, and every verdict that would depend on it
escalates instead of resolving. Ladder tiers `A3` and `A4` are unreachable
while the layer is inactive.

**Unblocking action (operator):** provision distinct agent identities with
separate credentials, then flip `ballot_layer.state` — itself a `G4` act.

## D4 — Merge queue and two-epoch machinery

**Design:** a candidate gate merges inactive, runs in shadow mode for an
epoch, is compared against the incumbent, and only then activates; merges pass
through a queue only a merge App may enter.

**Blocked because:** merge queues depend on branch protection (see D1).

**Compensating control in force:** the dual-policy rule delivers the essential
property without infrastructure — base and head logic must reach the same
verdict, so no pull request is decided by the gate it introduces. Divergence
escalates.

**Unblocking action:** resolve D1, then add the queue and an epoch counter
that gates activation.

## D5 — Golden corpus and classifier accuracy evidence

**Design:** classifier changes are replayed against a historical corpus of
pull requests, with a confusion matrix and a proof that no constitutional case
was downgraded.

**Blocked because:** the corpus is twelve work packages, too small for a
meaningful matrix. Publishing accuracy figures from it would be numbers
without power.

**Compensating control in force:** hand-written negative tests for every
class, including a downgrade-resistance test that a widened head envelope
cannot approve its own widening.

**Unblocking action:** accumulate pull requests, then build the replay
harness and record the matrix.

## Review

This register is reviewed whenever the envelope is renewed. An entry may only
be closed by evidence that the capability exists and is verified — never by a
statement that it is planned.
