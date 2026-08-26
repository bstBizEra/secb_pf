# SecB PF / BADF — repository adapter

Claude Code loads `CLAUDE.md` automatically and never loads `AGENTS.md`. Until this
file existed, the 210-line operating contract bound a session only when a human
remembered to say "read AGENTS.md first" — so the rules applied by luck rather than
by default. This file exists to close that gap and for no other reason.

**It is a pointer, not a copy.** A second copy of the rules would drift from the
first, and then two documents would disagree about what the contract is. Everything
normative lives in `AGENTS.md`.

@AGENTS.md

## Read before acting

| Document | What it governs |
| :--- | :--- |
| [`AGENTS.md`](AGENTS.md) | The operating contract. Precedence, control rules, stop conditions, gates |
| [`docs/00-governance/`](docs/00-governance/) | Authority, policy, stage gates, ballots |
| [`docs/06-agent-orchestration/ENGINEER_LOOP.md`](docs/06-agent-orchestration/ENGINEER_LOOP.md) · [`LEARN_LOOP.md`](docs/06-agent-orchestration/LEARN_LOOP.md) | The two closed loops (§14–§15) |
| [`docs/06-agent-orchestration/autonomous-git-controller/PR_AND_REVIEW_CONTRACT.md`](docs/06-agent-orchestration/autonomous-git-controller/PR_AND_REVIEW_CONTRACT.md) | What a PR and a review must carry |
| [`docs/12-decisions/`](docs/12-decisions/) | ADRs and formal decision records |
| [`docs/15-runbooks/`](docs/15-runbooks/) | Operational and recovery procedures |

## Four things worth surfacing here

These are in `AGENTS.md` already. They are repeated only because violating them is
silent — nothing fails loudly at the moment you get them wrong.

- **No ticket, no work** (AGENTS.md §4). Every PR body must carry a `SECB-WP-*`
  reference. Note what the gate actually checks: `check_work_package_ref.py` matches
  the *shape* of a reference and never resolves it, so a well-formed ID for a work
  package that does not exist passes. The gate cannot tell you your ticket is real.
- **Every PR body needs exactly one budget line** — `BUDGET: max_files=<n>
  max_lines=<n>` (AGENTS.md §6/§7). Two lines, or none, fails closed. The ceiling is
  a stop condition, not a target: on reaching it, stop and renegotiate on the ticket.
- **Check the verdict; do not guess it from the path.** The delegated envelope has
  edges that do not match intuition — measured on this tree:

  | Path | Verdict |
  | :--- | :--- |
  | `docs/INDEX.md`, `src/**`, `tests/**` | `AUTO_APPROVED` |
  | `scripts/**`, `config/control_surface.json`, `docs/12-decisions/**` | `AGENT_BALLOT_REQUIRED` |
  | `README.md`, `.github/workflows/**`, `scripts/classify_authority_delta.py` | `CONSTITUTIONAL_REQUIRED` |

  `README.md` escalates while `docs/INDEX.md` does not. `src/**` auto-approves even
  for authorization components, which is a known inversion (issue #210) and not a
  licence to merge them unreviewed. The ballot layer is **not active**, so anything
  above `AUTO_APPROVED` needs a human. Run the classifier rather than assuming.
- **Conflicts stop execution** (AGENTS.md §3). Escalate rather than resolving a
  conflict between instruction sources yourself.

## What CI does and does not do

`test-gate`, `authority-gate` and `budget-gate` propagate failure. `governance-verdict`
is **advisory by design** — it captures exit codes and ends `exit 0`, so it renders a
verdict for a human to read and never blocks. A green run is a signal, not a
permission: `main` is not branch-protected and no status check is required, so CI will
not stop a merge. Read it before merging; it will not stop you.

## Merging

A human merges. Agents do not. `AUTONOMOUS_MERGE_SUSPENDED_CLASSIFIER_UNTRUSTED` is in
force until the authority-classifier repair lands.
