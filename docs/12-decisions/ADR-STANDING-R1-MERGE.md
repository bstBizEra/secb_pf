# ADR — Standing R1 Merge Authorization

Status: Accepted (on merge of `SECB-WP-FWK-011`)
Date: 2026-08-10
Work Package: `SECB-WP-FWK-011` (issue #18)
Authority: Operator (vily), session instruction 2026-08-10
Policy: `docs/00-governance/STANDING_MERGE_AUTHORIZATION.md`

## Context

Across ten work packages the operator approved every merge individually.
The pattern was uniform: an `R1` change (documentation, tests, sandbox
code), three green gates, evidence on the ticket, then a human merge whose
content was never in doubt. The per-instance approval was carrying no
information for that class of change, while still costing a round trip.

`RISK_AUTHORITY_MATRIX.md` already contemplated this. The `R1` row sets
Merge to *"Policy may permit"* — an explicit reservation — and Segregation
of Duties §39 forbids implement-and-approve only for `R2–R4`. The framework
was built expecting a policy to occupy that space.

The risk is not the delegation itself; it is delegation that drifts. A
policy written only in prose is enforced by the executor's self-restraint,
which is precisely the control this framework rejects (`KN-001`: a gate is
unproven until it has failed on the real surface).

## Decision

Grant a **standing, bounded, expiring** authorization for an executor to
merge its own `R1` pull request when a **mechanical classifier** says the
change is in scope and all gates are green.

Two halves, neither sufficient alone:

1. **Policy** (`STANDING_MERGE_AUTHORIZATION.md`) — scope, guard
   conditions, notification duty, revocation, expiry, renewal.
2. **Classifier** (`scripts/check_merge_autonomy.py`) — exits `0` only for
   an all-`R1`, no-protected-path, within-cap diff; exits `2`
   (`HUMAN_REQUIRED`) on anything else, including empty or unparseable
   input. Reported on every PR by the advisory `merge-autonomy` CI job.

Bounds, per operator decision:

- **Tier:** full `R1` — `docs/`, `tests/`, `src/`, `config/`, `evidence/`
- **Protected paths** (always human): `AGENTS.md`, `README.md`,
  `docs/00-governance/`, `docs/12-decisions/`, `scripts/`, `.github/`, and
  the sealed MVP evidence directory
- **Size cap:** 600 changed lines
- **Expiry:** 2026-11-08, renewal by work package
- **Notification:** every autonomous merge announced with verdict, gates,
  SHA, and closed issue

## Consequences

**Accepted:**

- `R1` work ships without a human round trip; the operator's attention moves
  to `R2`+ and to governance, where the decision actually carries content.
- The authorization's boundary is testable. Fifteen subprocess tests assert
  each protected class, the cap boundary, and every fail-closed path.
- Self-limiting by construction: because governance and enforcement paths
  are protected, **this PR is itself `HUMAN_REQUIRED`** — the classifier
  refuses to authorize its own creation, and any future attempt to widen the
  policy, raise the cap, or edit the gate scripts is equally excluded.

**Costs and residual risks:**

- The classifier judges *paths and size*, not semantics. An `R2`-sized
  behavioral change confined to `src/` under 600 lines would read
  `ELIGIBLE`. The tier declaration on the work package remains the
  executor's honest obligation, and CI gates remain the substantive check.
- The audit surface grows: merge decisions must be reconstructed from CI
  history plus session notifications rather than from a human's click.
- Expiry creates a cliff. That is deliberate — a lapsed authorization is a
  safe state, and renewal forces a periodic look at the record.

## Alternatives considered

- **Docs-only scope** — safer, but excludes `tests/` and sandbox `src/`,
  which is most of the observed `R1` traffic; the round trip would remain
  for the majority of changes.
- **Policy without a classifier** — rejected outright: prose-only control,
  the exact failure mode `SECB-WP-FWK-002` was created to end.
- **Blocking CI job / auto-merge automation** — rejected for now. The
  classifier informs an explicit act; making CI perform merges would move
  release mechanics into the gate layer without a governed release decision.
- **GitHub branch protection with required reviews** — unavailable on this
  plan for private repositories, and orthogonal: it constrains *who*
  approves, not *which class* of change needs approving.

## Revocation

Operator utterance ("standing authorization revoked"), a comment on issue
#18, or revert of this ADR. Effective immediately, no PR required.
