# Knowledge Register

Status: Active — objects at confidence `Proposed`
Work Package: `SECB-WP-FWK-006` (Learn Loop round 1)
Governing contract: `KNOWLEDGE_LAYER.md`

> Per `AGENTS.md` §17 and `LEARN_LOOP.md`, nothing in this register is an
> operational instruction. Every object is `Proposed` until it has
> independent validation, a conflict check, and approval appropriate to
> its impact. Objects are appended, versioned, and superseded — never
> silently rewritten.

Episode base for round 1: work packages `SECB-WP-FWK-002` → `005`
(issues #2/#4/#6, PRs #3/#5/#7), the gate-proof exercise (PR #1), and
the session log of 2026-08-09/10.

---

## KN-001 — A gate is unproven until it has failed on the real surface

| Field | Value |
|---|---|
| Knowledge ID | `KN-001` v1 |
| Statement | A CI gate must be demonstrated to FAIL on its production surface (a real PR) before its green result is treated as meaningful. Green-only history is indistinguishable from a gate that is wired wrong. |
| Scope | Project (SecB CI gates); plausibly enterprise |
| Source | PR #1: authority gate tripped (run 31320436859) then passed (run 31320812146). PR #5: budget breaker passed at `1abf5f9`, tripped at `80a16cd` (run 31325014002, `4/1 files, 272/10 lines`), recovered at `75f1729`. |
| Confidence | Proposed (2 clean applications) |
| Owner | Operator (governance owner TBD, AGENTS.md §13) |
| Validity conditions | Applies to any mechanical gate whose wiring is new or changed. Does not require re-proof on every PR — once per gate per wiring change. |
| Version | 1 |
| Review date | 2026-11-08 |
| Supersedes | — |

## KN-002 — Enforcement scripts are tested as subprocesses, not imports

| Field | Value |
|---|---|
| Knowledge ID | `KN-002` v1 |
| Statement | Tests for a gate script must invoke it exactly as CI does (subprocess with stdin/env), never by importing its functions. A gate can pass import-level unit tests and still fail-open on the invoked surface. |
| Scope | Project; pattern inherited from a sibling system where import-only tests twice passed while the deployed hook failed |
| Source | `tests/test_check_work_package_ref.py` (9 tests) and `tests/test_check_budget.py` (11 tests), both green in runs on PRs #3/#5/#7. |
| Confidence | Proposed (2 clean applications in SecB; external precedent) |
| Owner | Operator |
| Validity conditions | Any script whose exit code CI interprets. Ordinary library code may still be tested by import. |
| Version | 1 |
| Review date | 2026-11-08 |
| Supersedes | — |

## KN-003 — Merging a work package can stale the status authority; check it at handoff

| Field | Value |
|---|---|
| Knowledge ID | `KN-003` v1 |
| Statement | Authoritative prose (status headers, baseline claims) goes stale the moment a WP merges. The handoff step of every WP should ask: "did this change what the status authority asserts?" — otherwise a follow-up WP is needed to repair the drift. |
| Scope | Project |
| Source | FWK-003 fixed a v0.2.0/v0.6.0 contradiction present since import; FWK-005 (`b722ca8`) was required immediately after FWK-004 merged because the header still said "first control gates" and INDEX claimed a PRD that does not exist. |
| Confidence | Proposed (2 occurrences of the drift, 2 repairs) |
| Owner | Operator |
| Validity conditions | Repos where status lives in hand-maintained prose. A future mechanical staleness check would supersede this object. |
| Version | 1 |
| Review date | 2026-11-08 |
| Supersedes | — |

## KN-004 — Anti-pattern: chaining state-changing git operations behind a fallible `gh` call

| Field | Value |
|---|---|
| Knowledge ID | `KN-004` v1 |
| Statement | `gh` CLI subcommands can fail for reasons unrelated to the intent (deprecated GraphQL fields, version drift such as missing `--event`), and an `&&` chain then silently skips the git operations behind them. State-changing steps must be separate calls with their outcomes verified individually; REST (`gh api`) is more version-stable than wrapper subcommands. |
| Scope | Project; any environment pinned to an older `gh` |
| Source | Session 2026-08-09: `gh pr edit` died on the projectCards deprecation, the chained retrigger commit never ran, and the gap surfaced only when the branch head was re-verified; `gh run list --event` unsupported on the installed version. Fix: `gh api -X PATCH .../pulls/1` succeeded. |
| Confidence | Proposed (1 incident, 1 verified workaround) |
| Owner | Operator |
| Validity conditions | Until the local `gh` is upgraded past the deprecations in question; re-evaluate at review date. |
| Version | 1 |
| Review date | 2026-11-08 |
| Supersedes | — |

## KN-005 — Skill candidate: retrigger PR gates with an empty commit after metadata edits

| Field | Value |
|---|---|
| Knowledge ID | `KN-005` v1 |
| Statement | Workflow runs snapshot the PR title/body at event time; editing metadata alone does not re-evaluate gates that read it. Pushing an empty commit (`git commit --allow-empty`) issues a `synchronize` event carrying the updated metadata. Candidate for the Skill Factory as a bounded procedure. |
| Scope | Project (GitHub Actions `pull_request` events) |
| Source | PR #1: title edit alone left the stale run authoritative; empty-commit push produced run 31320812146 with the corrected title. PR #5: same procedure drove the trip/recover proof (`80a16cd`, `75f1729`). |
| Confidence | Proposed (3 successful uses) |
| Owner | Operator |
| Validity conditions | Only for gates reading event metadata; gates reading the diff re-run on any push regardless. Not validated for `workflow_dispatch` or merge queues. |
| Version | 1 |
| Review date | 2026-11-08 |
| Supersedes | — |

---

## Register maintenance

- New objects append with the next `KN-` ID; corrections publish a new
  version and fill `Supersedes`.
- Confidence may rise only through the promotion path of `LEARN_LOOP.md`
  (test hypothesis → validate → promote) with independent review.
- Expired review dates quarantine an object: it must not be cited as
  current guidance until renewed (`KNOWLEDGE_LAYER.md` governance rules).
