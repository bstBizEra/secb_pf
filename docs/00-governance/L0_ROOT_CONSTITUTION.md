# L0 — Root Constitution

Status: Ratified on merge of `SECB-WP-FWK-012` (issue #20) — the Genesis Ratification
Constitutional authority: Operator (vily), until amended by that authority
Amendment rule: **any change to this file is `CONSTITUTIONAL_REQUIRED`** and may
never be enacted by an agent, whatever the ballot outcome
Supersedes: `STANDING_MERGE_AUTHORIZATION.md` approach of `SECB-WP-FWK-011`

## Why a constitution rather than a file list

`SECB-WP-FWK-011` protected governance by naming files: touch one, a human
merges. That answered the wrong question. The question is not *which files did
this change touch* but **how does it change authority**. A refactor of a gate
that provably decides every case identically expands nothing; a two-line edit
to a ceiling expands everything.

So authority is split into four layers. Each layer names the route its design
intends, **and separately whether that route can be taken today**:

```text
DECLARED_ROUTE  ≠  CAPABILITY_AVAILABLE  ≠  LIVE_ROUTE
```

| Layer | Contents | Declared authority | Capability state | Live route | Blocker |
| --- | --- | --- | --- | --- | --- |
| **L0 — Root Constitution** | This file. Trust anchor, absolute ceilings, prohibited actions, quorum rules, the ladder itself | Constitutional authority only | `AVAILABLE` — the authority exists and is exercisable | Constitutional authority, by human merge | None. This row's declared and live routes coincide |
| **L1 — Delegation Envelope** | `config/delegation_envelope.json` — the scope, caps and tier delegated in advance | Agent action inside L0 maxima, once the ballot layer is active | `UNAVAILABLE` — `ballot_layer.state` is `NOT_ACTIVE` | Constitutional authority, by human merge | Ballot layer inactive: five independently-identified agents do not exist in this deployment |
| **L2 — Policy Implementation** | Classifier, dual-policy check, gate logic, governance docs | Agent action with evidence and ballots | `PARTIAL` — evidence is available; ballots are not | Agent authors, **human merges**; the classifier escalates constitutional paths | Ballot layer inactive. Also `C-7`: one GitHub identity cannot supply an independent approval |
| **L3 — Operational Changes** | Documentation, tests, application and sandbox code, CI mechanics | Agent auto-merge by risk class | `UNAVAILABLE` — no auto-merge has ever been enabled on a pull request here, and branch protection returns `403` on this plan (`NFR-13`) | Agent authors, **human merges** | Platform capability absent, and auto-merge is closed by operator posture |

**Three of the four declared routes are not reachable today, and the table says
so rather than leaving a reader to discover it.** The previous version of this
table had one column — *"who may change it"* — which fused constitutional design
with present execution, so `L1`'s *"agent action … once the ballot layer is
active"* read as a live agent route while the ballot layer has never been
active. `L3`'s *"agent auto-merge by risk class"* read the same way while no
pull request in this repository has ever carried auto-merge.

**Nothing here grants, removes, or advances any authority.** The declared column
is reproduced unchanged from the version this replaces; what is added is a
statement of what the machinery currently permits. `C-6` and `C-7` remain open,
the ballot layer remains `NOT_ACTIVE`, and no route becomes live by being
described accurately (`SECB-WP-FWK-070`).

**A declared route is not dead because it is unreachable.** These are the routes
the design intends once the capability exists — recording them as
declared-but-blocked is what makes the blocker actionable, and deleting them
would lose the design.

An agent operating under this constitution never *creates* authority. It
exercises authority the constitutional authority delegated in advance, and
every exercise is measurable against the envelope.

## Absolute ceilings — not waivable by any tier, ballot, or emergency

1. No change may raise a ceiling in this file, lower a quorum, widen the
   prohibited-action list's exceptions, or alter the trust anchor.
2. No agent may advance beyond tier `A4`, or invent a tier above it.
3. No change exceeding `absolute_ceilings.max_changed_lines_ever` in the
   envelope auto-merges, whatever its class.
4. Tiers `A3` and `A4` require an **active** ballot layer. While
   `ballot_layer.state` is `NOT_ACTIVE`, those tiers are unreachable.
5. A pull request is never judged solely by the policy it proposes
   (`scripts/check_dual_policy.py`). Base and head must agree.
6. Evidence, once recorded, is append-only. Sealed evidence packages are
   immutable; their certifications void on change.

## Prohibited actions — verdict `REJECTED`, never weighed

- Disabling, deleting, or neutering an enforcement control or its CI step
- Destroying, rewriting, or detaching evidence from the commit it describes
- Bypassing a verifier, or making a required check optional
- Granting an identity the power to approve its own change
- Reducing a quorum or veto, or removing an expiry, to unblock a specific PR

These are not risks to be balanced against benefit. A change carrying one of
these signatures is refused, and the correct response is to withdraw it.

## Change classes and verdicts

| Class | Meaning | Verdict |
| --- | --- | --- |
| `G0` | Non-governance work wholly inside the envelope | `AUTO_APPROVED` |
| `G1` | Governance implementation; authority and outcomes unchanged | `AGENT_BALLOT_REQUIRED` |
| `G2` | Adjustment inside the delegated envelope | `AGENT_BALLOT_REQUIRED` |
| `G3` | Pre-authorized ladder advance with conditions met | `AUTO_APPROVED_WITH_CONDITIONS` |
| `G4` | Root authority expansion, or any L0/envelope/classifier change | `CONSTITUTIONAL_REQUIRED` |
| `G5` | Prohibited action per the list above | `REJECTED` |

`HUMAN_REQUIRED` is deliberately **not** in this vocabulary. The verdict names
the *authority level* a change needs, not the species of approver. Today the
constitutional authority is one operator; it may later be a steering
committee, a threshold-signature council, or an external body, and the
verdicts must not have to be renamed when that happens.

## Pre-authorized authority ladder

Tiers, their authority, and the conditions for advancing are recorded in
`config/delegation_envelope.json` under `authority_ladder`. Advancement is
`G3`: the agent may take a step the constitutional authority defined in
advance, **only** when the recorded conditions are objectively met. It may not
define a new step. This is what makes raising a ceiling an exercise of
delegated authority rather than the creation of new authority.

## Two-epoch activation for gate changes

A change to gate logic merges **inactive** and takes effect in the following
governance epoch. No pull request is ever decided by the gate it introduces.
Today this is enforced by the dual-policy rule — base and head logic must
reach the same verdict — with full epoch machinery deferred
(`docs/14-plans/GOVERNANCE_DEFERRED_CAPABILITIES.md`).

## What this constitution does not yet have

Stated plainly, because a governance document that overstates its own
enforcement is the failure it exists to prevent:

- **No external trust anchor.** The verifier runs inside the repository it
  judges. A change to `.github/` is therefore `G4` — the only available
  compensating control. Moving the verifier out requires an organization,
  which this account does not have.
- **No cryptographic signing.** The envelope is `UNSIGNED`; its integrity
  rests on git history and the human merge that ratified it.
- **No ballot council.** One agent cannot constitute a five-role quorum.
  Every verdict that would depend on quorum escalates instead of resolving.

Each gap has a deferred-capability entry naming the operator action required.

## Revocation

The constitutional authority may revoke or narrow all delegation at any time,
by statement in session or a comment on issue #20, effective immediately and
without a pull request. Expiry of the envelope has the same effect by default:
delegation lapses rather than persisting unexamined.
