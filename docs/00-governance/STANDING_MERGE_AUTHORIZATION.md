# Standing Merge Authorization — Tier R1

Status: Active on merge of `SECB-WP-FWK-011`
Decision record: `docs/12-decisions/ADR-STANDING-R1-MERGE.md`
Authority source: Operator (vily) instruction, 2026-08-10, recorded on issue #18
Effective: on merge of the PR enacting `SECB-WP-FWK-011`
**Expires: 2026-11-08** (90 days) — lapses silently into per-merge approval

## What is authorized

An executor may merge its own pull request **without a per-instance human
approval** when, and only when, **all** of the following hold:

1. `scripts/check_merge_autonomy.py` returns `ELIGIBLE` for the PR's diff
2. Every CI gate is `success`: Gate 1 (Authority), Gate 5 (Test), Budget
3. The PR declares and stays within its work-package budget
4. This authorization has not expired or been revoked

This is the policy the risk matrix already anticipated: `R1` Merge reads
*"Policy may permit"*, and Segregation of Duties §39 restricts the
implement-and-approve prohibition to `R2–R4`. Nothing here modifies the
matrix; it exercises a permission the matrix reserved.

## Eligibility test (mechanical, fail-closed)

`ELIGIBLE` requires all three:

| Condition | Rule |
| --- | --- |
| Tier | Every changed path is `R1`: under `docs/`, `tests/`, `src/`, `config/`, or `evidence/` |
| Protected paths | **No** changed path under `AGENTS.md`, `README.md`, `docs/00-governance/`, `docs/12-decisions/`, `scripts/`, `.github/`, or the sealed MVP evidence directory |
| Size | Diff ≤ **600** changed lines |

Anything else — including an unclassified path, an empty diff, or
unparseable input — returns `HUMAN_REQUIRED`. `HUMAN_REQUIRED` is a normal
verdict, not a failure.

The protected list encodes one rule: **an executor may not widen its own
authority.** Governance documents, decision records, the gate scripts, the
workflow definitions, and the sealed evidence package are all off-limits to
autonomous merge, because each is a lever over the controls themselves.

## What remains human-only, always

- Any `R2`–`R4` change (material feature, API behavior, security, identity,
  migration, infrastructure, production, destructive or irreversible)
- Every path on the protected list above
- Deploy, release, and production authority (`R4`, Release Gate, dual control)
- Raising the size cap, widening the tier scope, editing this policy, or
  renewing it past expiry

## Mandatory notification

Every autonomous merge is announced in the same turn it happens: the
classifier verdict, the three gate results, the merge SHA, and the issue it
closes. Silence is a policy violation — an autonomous merge the operator
cannot see is indistinguishable from one that never should have happened.

## Revocation

Immediate, by either route:

- The operator states revocation (e.g. "standing authorization revoked") in
  session or on issue #18 — effective on utterance, no PR required
- The ADR or this file is reverted

On revocation or expiry, merge authority returns to per-instance operator
approval with no further ceremony.

## Renewal

Before 2026-11-08, a work package must review the autonomous-merge record
(count, classifier verdicts, any incident) and propose renewal with an
explicit expiry. Absent that, the authorization lapses. Renewal is itself a
governance change and therefore human-merged.

## Audit

The classifier's verdict is recorded on every PR by the advisory
`merge-autonomy` CI job, so the eligibility decision for every merge —
autonomous or not — is reconstructible from CI history.
