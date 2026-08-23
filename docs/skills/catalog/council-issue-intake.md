# Skill — `council.issue-intake`

Status: `CANDIDATE` · Risk ceiling: `R0` · Permitted effects: **none (read-only)**
Adapted from `openclaw/openclaw` `skills/gh-issues/SKILL.md` (upstream, MIT-licensed project).

## What this is

Agent Council needs subjects. Today they are chosen by hand. This skill enumerates open issues,
detects which already have work in flight, and emits a **routing record** the operator reads.

It stops there. It opens nothing, branches nothing, merges nothing.

## What was adopted, and what was not

Upstream runs six phases. Phases 1–3 observe; phases 4–6 act. **Only 1–3 are adopted.**

| upstream phase | adopted | why |
|---|---|---|
| 1 — resolve repo, validate auth | yes | read-only |
| 2 — fetch issues (`gh issue list`) | yes | read-only |
| 3 — detect existing PRs/branches | yes | read-only; this is the duplicate-work check Council needs |
| 4 — confirm selection, configure fork remotes | **no** | writes a remote; `--yes`/`--cron` skip the human |
| 5 — spawn ≤8 workers, branch, fix, test, **open PRs** | **no** | see below |
| 6 — collect worker results | **no** | nothing to collect |
| watch mode (continuous poll) | **no** | unbounded loop, no budget meter exists |
| reviews-only mode (process PR comments) | **no** | writes comments |

### Why phase 5 is not adopted

It is not a preference. Measured state of this framework:

```
current_tier          A1
ballot_layer          NOT_ACTIVE
auto_merge            CLOSED
production autonomy   NOT_AUTHORIZED
C-7                   OPEN, severity Critical — one GitHub identity; the agent runtime holds
                      the owner's credential, so no approval here is independent
```

Autonomous branch-and-PR is roughly `AC4`–`AC5` on the council autonomy ladder. This framework is
at `AC1` (shadow, non-authoritative), and the governing mandate states that advancement between
stages requires measured evidence and that the Council may not grant itself authority. Importing
phase 5 would move four rungs in one commit, under a single identity, with no budget meter — the
`BUDGET_CIRCUIT_BREAKER_POLICY` declares eleven domains of which one is executable, and worker
count is not among them.

    CAPABILITY_AVAILABLE != CAPABILITY_AUTHORIZED

The excluded phases are **deferred and named**, not dropped. They become reachable when the
council autonomy ladder is registered and advanced on evidence, and when C-7 closes.

## Contract

Inputs — all optional, all filters: `label`, `milestone`, `assignee`, `state`, `limit`.
Effects — **none**. Reads `gh issue list` and `gh pr list`; writes no file, ref, comment or remote.
Output — a routing record: for each candidate issue, its number, title, labels, and whether an open
PR or branch already claims it.
Refusal — if `gh` is unauthenticated, or the repository cannot be resolved, it refuses. An empty
candidate list is reported as empty, never as "nothing to do": `NO_CANDIDATES != NOT_QUERIED`.

## Provenance

Upstream: `openclaw/openclaw`, `skills/gh-issues/SKILL.md`. Adapted, not vendored — no upstream
file is copied into this repository. The phase decomposition and the duplicate-work check are the
ideas taken; the effect boundary, the refusal semantics and the registry entry are this framework's.
