# Work Package Record — SECB-WP-FWK-002

Status: Executed — First Executable Gates
Date: 2026-08-09
Predecessor: `SECB-WP-FWK-001` (framework documented, placed under version control at commit `cb03eba`)

## Objective

Convert the first two of the ten Mandatory Control Gates from prose into
mechanisms that can actually fail, and give "No Ticket, No Work" a place
where tickets exist.

## Authority

Operator instruction in session 2026-08-09: proceed with the ordered plan
(Test Gate CI → intake → authority check).

## Scope

- `.github/workflows/ci.yml` — Gate 5 (Test): FIT-101..120 plus repo tests
  run on every push to `main` and every pull request.
- `.github/ISSUE_TEMPLATE/work-package.yml` — intake form carrying the ten
  minimum fields of `AGENTS.md` §7; blank issues disabled.
- `scripts/check_work_package_ref.py` — Gate 1 (Authority), minimal form:
  a pull request must cite a `SECB-WP-*` ID. Fail-closed: empty or missing
  input exits `2`.
- `tests/test_check_work_package_ref.py` — nine subprocess-level tests.
  The gate is tested by invoking the command, not by importing the module,
  because a gate that only passes under import can still be broken on the
  surface CI actually uses.

## Exclusions

- No runtime budget/circuit-breaker enforcement (policy remains prose).
- No branch protection or merge blocking — CI is a signal a human reads,
  not a mechanical gate on `main`.
- No change to the v0.2.0 / v0.6.0 status inconsistency noted at import.
- No skill-router runtime adoption; `SECB-WP-ENGLOOP-004` remains
  `HELD_AT_INDEPENDENT_REVIEW_GATE`.

## Acceptance Criteria

- CI runs on push and PR; the test-gate job executes FIT-101..120 and the
  new authority-gate tests, all green.
- A PR without a `SECB-WP-*` reference fails the authority-gate job.
- Issue creation offers only the Work Package form with all ten §7 fields
  required.
- pytest cache artifacts are not written into the sandbox-evidence
  directory (`-p no:cacheprovider`, `PYTHONDONTWRITEBYTECODE`).

## Risk and Rollback

Risk is limited to CI configuration; no runtime or production surface is
touched. Rollback: revert the commit; the repository returns to the
documented-only state of `SECB-WP-FWK-001`.

## Target State

`CLOSED_LOOP_FRAMEWORK_DOCUMENTED -> FIRST_GATES_EXECUTABLE`
