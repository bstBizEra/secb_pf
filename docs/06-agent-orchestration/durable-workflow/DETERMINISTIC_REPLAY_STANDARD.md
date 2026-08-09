# Deterministic Replay Standard

Status: Implementation Ready  
Version: 1.0.0  
Work Package: `SECB-WP-ENGLOOP-003`

## Decision

Workflow orchestration is deterministic. Replay reconstructs state from accepted history and never re-invokes a model, tool, network API, database mutation, Git operation, deployment, or other recorded side effect.

## Permitted orchestration behavior

- Read ordered events and pinned deterministic configuration.
- Schedule activities, timers, ballots, signals and child workflows.
- Produce commands derived only from recorded state.
- Load a verified compatible snapshot and replay later events.

## Prohibited orchestration behavior

- Reading wall-clock time, mutable environment variables or machine-local files.
- Generating unrecorded random identifiers.
- Direct model, provider, database, Git, CI/CD or cloud calls.
- Depending on unordered iteration or unpinned policy/tool/model versions.

LLM inference is an activity. History records provider/model identity, prompt-template hash, input/output hashes, tool-schema version, decoding configuration, policy result, token/cost metrics and evidence locator.

## Replay modes

| Mode | Effects | Authority |
|---|---|---|
| Recovery | None | Automatic within current workflow authority |
| Verification | None | CI gate |
| Forensic | None | Auditor warrant |
| Simulation | Sandbox only | Experiment warrant |
| Reset-and-replay | New commands after fork only | Change ballot and warrant |

## Algorithm

1. Resolve pinned workflow and state-schema versions.
2. Load the latest valid compatible snapshot.
3. Stream subsequent events in sequence order and verify the hash chain.
4. Run deterministic orchestration against recorded activity results.
5. Compare produced commands with recorded commands.
6. Advance without external execution when equivalent.
7. Emit `NondeterminismDetected` and hold on divergence.
8. At the history frontier, revalidate authority, policy and durable budgets before scheduling new work.

## Evolution gate

Every workflow-code release must replay a corpus containing normal, retry, timeout, ballot, compensation and long-running histories. State changes require versioned upcasters; semantic changes require version pinning or an approved patch marker. Reset creates a new history branch and never erases prior events.
