# Work Package Record — SECB-WP-FWK-004

Status: Executed — Budget Circuit Breaker Executable
Date: 2026-08-09
Ticket: issue #4
Predecessors: `SECB-WP-FWK-002` (CI skeleton), `SECB-WP-FWK-003` (a WP that
declared "≤2 files, ≤40 lines" and had to be budget-checked by hand)

## Objective

Make the work-package budget a circuit breaker CI can trip. AGENTS.md §6
lists a reached budget cap as a mandatory stop condition; until this WP,
no cap could mechanically stop anything.

## Scope

- Every PR body must declare exactly one line
  `BUDGET: max_files=<n> max_lines=<n>`.
- `scripts/check_budget.py` — stdin is `git diff --numstat base...head`,
  `BUDGET_TEXT` is the PR body; exit `0` within budget, `2` otherwise.
  Fail-closed: missing, malformed, or ambiguous (duplicate) budgets fail.
  Binary files count toward `max_files` with unknown lines, so a
  binary-heavy PR is bounded rather than silently unbounded.
- `tests/test_check_budget.py` — eleven subprocess tests: pass, exact
  boundary, files exceeded, lines exceeded, missing, absent env,
  malformed, ambiguous, binary, empty diff, garbage numstat.
- `budget-gate` job in `ci.yml`, PR-only, three-dot diff from the PR base.

## Exclusions

Token / time / retry / tool-call caps (need a runtime harness), budgets
on issue bodies, and merge blocking — CI remains a signal a human reads.

## Fail-path proof

A gate proven only green is unproven. On this WP's own PR the declared
budget was temporarily shrunk to `max_files=1 max_lines=10`, the gate
tripped in CI, and the true budget was restored — run IDs are recorded
on issue #4.

## Target State

`BUDGET_PROSE_ONLY -> BUDGET_CIRCUIT_BREAKER_EXECUTABLE`
