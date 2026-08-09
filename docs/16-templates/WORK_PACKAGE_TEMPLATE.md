# Template — Work Package

Derived from the seventeen work packages this repository has run (`SECB-WP-FWK-001`…`017`).
Fields are the ten minimum of `AGENTS.md` §7; the notes are what actually went
wrong when a field was written carelessly.

---

### Ticket / Work Package ID

`<PREFIX>-WP-<AREA>-<NNN>`

### Objective and business value

Why this exists *now*. State the gap in the current state, not the desired
feature. If the objective is "add X", ask what breaks without X — that is the
objective.

### Scope and exclusions

In scope: the deliverables.
Out of scope: **and the reason for each.** An exclusion without a reason gets
re-litigated. Exclusions that name a Lean-gate rationale ("no tooling until a
task is blocked without it") hold; bare exclusions do not.

### Owner, executor, reviewer, and approver

Owner · Executor · Reviewer · Approver. State plainly if any two collapse onto
one identity, and cite the accepted-risk record if so. Silent collapse is the
failure; documented collapse is a treatable condition.

### Dependencies and risks

Each risk gets a mitigation in the same line, or it is not a risk entry, it is a
worry. The most useful risks name a *specific* failure this WP could cause.

### Acceptance criteria

Verifiable statements. "Green" is defined here, before code exists. A criterion
you cannot check by running something is a hope.

### Test and evidence plan

Which command proves which criterion, and where the evidence is recorded.
**Verify with the same inputs CI uses** — a local check that omits an input CI
supplies is weaker than the CI it predicts.

### Budget and circuit-breaker limits

`BUDGET: max_files=N max_lines=N`

Copy this line verbatim into the PR body; the breaker reads it there. Overruns
are **renegotiated by comment on this ticket, with the cause**, never silently
restated in the PR.

### Rollback or recovery plan

Usually "revert the merge commit" — say what state that returns to.

### Target state transition

`CURRENT_STATE -> TARGET_STATE`

---

## Closing checklist

- [ ] Local run with CI-identical inputs, green
- [ ] Budget self-checked against `git diff --numstat origin/main`
- [ ] Governance verdict known before pushing
- [ ] PR body carries the BUDGET line and `Closes #N`
- [ ] Gate results recorded as a comment on this ticket, citing run IDs
- [ ] Worktree switched off the feature branch before handoff
- [ ] If merged autonomously: verdict, gates, SHA and issue announced
