# SecB Autonomous Loop Design

| Field | Value |
| :--- | :--- |
| Work package | `SECB-WP-FWK-094` |
| Status | **PROPOSED — NOT EFFECTIVE** |
| Adoption gate | Operator ratification. This document cannot adopt itself |
| Conformance measured at | `main@ace1e579597f768c34b222a91d66ed445dfe34d3`, 2026-08-18 |
| Supersedes | nothing |

> **This document is a target, not a description.** Section 3 measures how much of it exists
> today, and the answer is: one narrow band, deeply, and almost nothing else. Reading the design
> without reading the baseline would give a false impression of the framework's coverage.

## 1. Why this is `PROPOSED` and not adopted

The design defines the project's constitutional boundary — the lifecycle, the authority model, the
autonomy ceiling. Under the framework's own invariant, **a policy proposal cannot activate itself**,
and an agent may not enlarge its own authority. An agent writing "SecB now operates at A5" into a
governance document would be doing exactly that.

```text
DESIGN_RECORDED ≠ DESIGN_ADOPTED ≠ DESIGN_IMPLEMENTED
```

It is recorded here so it is greppable, versioned and diffable rather than living in conversation —
the same treatment `SECB-WP-FWK-063` (Auto-Merge Standard) receives while it remains proposed.

## 2. The invariant part: one loop, every stage

The stage-specific agents, tools, skills, schemas and evidence differ. The loop contract does not.

```text
Event → Admission → Context → Authority → Execution → Independent Evidence
      → Adversarial Challenge → Policy Verdict → Atomic Transition
      → Observation → Reconciliation → Governed Learning
```

Each step must terminate in a named machine-readable result — `Trigger Receipt`,
`Admission Verdict`, `Context Receipt`, `Execution Plan`, `Capability Grant`, `Execution Trace`,
`Evidence Set`, `Challenge Report`, `Stage Verdict`, `Transition Receipt`, `Observation Set`,
`Reconciliation Verdict`, `Learning Candidate` — never a generic "agent failed".

### Canonical states

```text
DETECTED → ADMISSION_PENDING → ADMITTED → CONTEXT_BOUND → PLANNED → AUTHORIZED
→ EXECUTING → CANDIDATE_READY → VERIFYING → CHALLENGING → ELIGIBLE → COMMITTING
→ EFFECTIVE → OBSERVING → RECONCILED → CLOSED
```

Exceptional states are terminal facts, not error strings: `DUPLICATE`, `SUPERSEDED`, `CONTENTION`,
`DEPENDENCY_BLOCKED`, `CONTEXT_INVALID`, `AUTHORITY_DENIED`, `BUDGET_EXCEEDED`,
`EVIDENCE_INCOMPLETE`, `VERIFICATION_FAILED`, `SECURITY_HOLD`, `STALE_CANDIDATE`,
`POLICY_CONFLICT`, `QUARANTINED`, `ROLLED_BACK`, `OUTSIDE_MANDATE`.

### The four separations that make it governable

```text
runtime identity ≠ role ≠ capability ≠ authority
```

All four resolve independently. Additionally: the producer may not issue its own final verdict, and
tool availability is not permission to use the tool.

## 3. Measured conformance baseline

Measured, not estimated. Commands are reproducible against the recorded ref.

### 3.1 The ten stage gates

```text
MANDATE_EFFECTIVE           executable: 0   documented: 0
PRD_READY                   executable: 0   documented: 0
DESIGN_EFFECTIVE            executable: 0   documented: 0
IMPLEMENTATION_AUTHORIZED   executable: 0   documented: 4
IMPLEMENTATION_COMPLETE     executable: 0   documented: 0
VERIFIED                    executable: 0   documented: 9   (the token appears in the shadow
                                                             queue as a receipt verdict, not
                                                             as a stage gate)
SECURITY_ACCEPTED           executable: 0   documented: 0
PRODUCTION_ELIGIBLE         executable: 0   documented: 0
PRODUCTION_EFFECTIVE        executable: 0   documented: 0
SERVICE_HEALTHY             executable: 0   documented: 0
```

**Zero of ten stage gates are instrumented.**

### 3.2 Control surfaces

| Target surface | Present | Functional equivalent today |
| :--- | :--- | :--- |
| `docs/` | yes | 119 markdown documents at the measured ref; this document makes 120 |
| `evidence/` | directory only | `evidence/.gitkeep` — one file, no manifests |
| `.github/` | yes | 2 workflows (target names 14+) |
| `governance/` | no | `docs/00-governance/` — 9 documents |
| `schemas/` | no | `config/*.schema.json` — 5 of 19 target schemas |
| `tools/` | no | `scripts/*.py` — 12 |
| `work/` `agents/` `skills/` `policies/` `runbooks/` | no | none |
| `secb.yaml` | no | `config/delegation_envelope.json` covers authority only |

### 3.3 Autonomy level, measured on the merge axis

```text
A3  implement in isolated environments     DEMONSTRATED — every implementation this cycle
A4  merge verified low/medium-risk work    0 of 20 sampled merges agent-performed
A5  deploy and operate                     no deployment surface exists
```

SecB is at **A3**. The A3→A4 boundary is not a missing feature: `confers_merge_authority: false` is
asserted on every path deliberately, and every landing to date was an operator compare-and-swap.
That is **intentional retained authority**, not an autonomy defect, and it changes only by
ratification.

### 3.4 What genuinely works

Thirteen predicted landings, thirteen full-identity tree matches, zero drift, zero CAS failures.
Head/base/tree/toolchain evidence binding, ordered-prefix simulation, fail-closed admission gates,
and receipt readback are real and repeatedly demonstrated.

**All of it sits inside one band of Stage 7.** It proves that evidence binding and merge eligibility
work. It proves nothing about PRD → production, because no stage before or after that band is
instrumented.

```text
DEPTH_IN_ONE_BAND ≠ LIFECYCLE_COVERAGE
```

## 4. What adoption would require

Adoption is not a document edit. Before this becomes effective, the framework needs at minimum:

1. **A machine-readable project descriptor.** `MANDATE_EFFECTIVE` cannot be evaluated without one;
   `secb.yaml` plus `project.schema.json` and `mandate.schema.json` are the smallest thing that
   makes Stage 0 checkable rather than aspirational.
2. **A canonical state machine** with the states in §2 as data, so a transition is a validated
   object rather than a label.
3. **A transition ledger** — the atomic-transition receipt that already exists in spirit as the CAS
   handoff, generalised beyond merge.
4. **A reconciler**, which is the only component that can detect false closure across declared,
   repository, workflow and runtime state.

Items 2–4 have partial analogues in `check_shadow_merge_queue.py` and `check_startability.py`. Per
the design's own deduplication rule, they must be **extended, not re-created**: a second source of
truth for state would be worse than none.

## 5. Sequencing constraint the design does not yet account for

`config/control_surface.json` is a **serialisation point**. Every new script must be registered or
declared there, so every script-adding work package takes the same lock. Three open pull requests
write it concurrently, and appends to it have been measured to conflict.

The build order in the design (P0 control kernel → P1 engineering → …) adds many scripts. Executed
as written against today's repository, each one contends with the last. The structural remedy is the
control-surface shard migration (`SECB-WP-FWK-088`, issue #157), which is itself classified
`BLOCKED_BY_CONTENTION` for exactly this reason.

**The bottleneck blocks its own remedy.** Draining or sharding it is a precondition for P0, not a
parallel task.

## 6. Open questions for the ratifying authority

1. Is this design **ratified**, or does it remain proposed pending revision?
2. Path 1 — drain and shard the control surface first — or Path 2 — begin P0 with the project
   descriptor, which is uncontended because it adds no script?
3. Does A4 (autonomous merge of low-risk verified work) remain intentionally withheld? The design
   targets A5, and every gate needed for A4 except the authority grant already exists.

Until (1) is answered, this document is inert by construction.
