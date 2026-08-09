# Engineer Loop Step Contracts

Status: Implementation Ready
Version: 1.0.0
Work Package: `SECB-WP-ENGLOOP-001`

Each step is atomic, idempotent, traceable, time-bounded, and produces a decision or evidence object. `O` means Orchestrator, `G` Governance, `P` Product/Requirements, `A` Architect, `E` Engineer, `T` Test, `S` Security, `V` Independent Reviewer, and `R` Release.

| # | Contract | Owner | Input | Output / evidence | Gate |
|---:|---|---|---|---|---|
| 1 | Verify intake envelope | G | Ticket, actor, authority | Authority decision, risk tier | Authority |
| 2 | Retrieve minimum context | O | Approved sources | Context manifest with hashes | Readiness |
| 3 | Classify source trust | G | Context manifest | Trust labels, quarantines | Readiness |
| 4 | Resolve requirement gaps | P | Demand, constraints | Build-ready requirements, AC | Readiness |
| 5 | Decide intake readiness | G | Steps 1–4 | Gate decision | Readiness |
| 6 | Produce bounded plan | O | Requirements, context | Plan, dependencies, risks, tests, evidence, rollback | Readiness |
| 7 | Detect triggered reviews | G | Risk and change profile | Review obligations | Architecture |
| 8 | Draft required ADRs | A | Trade-offs | Proposed ADRs | Architecture |
| 9 | Reserve budgets | O | Risk tier, plan | Budget reservation | Implementation |
| 10 | Acquire resource leases | O | Change set | Lease IDs, fencing tokens | Implementation |
| 11 | Validate preflight | O | Repo, tools, dependencies | Preflight report | Implementation |
| 12 | Open isolated workspace | O | Preflight, identity | Sandbox ID and policy | Implementation |
| 13 | Execute TDD cycle | E | AC, tests | Red/green/refactor evidence | Implementation |
| 14 | Debug systematically | E | Reproduction | Hypothesis, fix, regression test | Implementation |
| 15 | Apply smallest diff | E | Plan | Scoped source change | Implementation |
| 16 | Record side effects | O | Mutation request | Idempotency and compensation record | Implementation |
| 17 | Save verified checkpoint | O | Verified step state | Checkpoint manifest | Implementation |
| 18 | Renew leases | O | Active locks | Heartbeat/fencing record | Implementation |
| 19 | Run applicable tests | T | Candidate change | Test report | Test |
| 20 | Run quality/security checks | T/S | Candidate and dependencies | Lint, type, SAST, SCA, secret, SBOM results | Test/Security |
| 21 | Map AC and RTM | P/T | Results and AC | Traceability matrix | Test |
| 22 | Perform independent reviews | A/S/V | Change/evidence | Review findings and decision | Architecture/Security |
| 23 | Enforce advisory boundary | G | Agent reviews | Binding/advisory classification | Evidence |
| 24 | Calculate quality score | V | Passed hard gates | Scorecard | Evidence |
| 25 | Create commits and PR | E | Accepted candidate | Commit SHA, PR ID | Evidence |
| 26 | Evaluate merge eligibility | G/V | Score, risk, gates | Merge eligibility decision | Evidence |
| 27 | Execute authorized merge | Authorized merger | Effective approval | Merge SHA | Merge authority |
| 28 | Evaluate Release Gate | R/G | Release package | Release or hold decision | Release |
| 29 | Deploy reversibly | R | Release authority | Deployment ID, telemetry | Release |
| 30 | Reconcile desired/actual state | R/T | Deployment state | Reconciliation report | Release |
| 31 | Remediate permitted drift | R/G | Drift record | Repair or escalation record | Release |
| 32 | Assemble evidence package | O | All episode artifacts | Signed/checksummed manifest | Evidence |
| 33 | Record episode outcome | O | Execution/verification data | Episode log, residual risks | Evidence |
| 34 | Handoff to Learn Loop | Learning Agent | Sealed evidence | Learning intake, not knowledge | Learning |
| 35 | Close resources and task | O/G | Completion decision | Revocation, lease/sandbox closure | Closure |

## Universal Preconditions

Before any step: ticket exists; actor identity is valid; authority permits the action; scope and state match; budget remains; policy/control services are healthy; required predecessor evidence verifies.

## Universal Failure Contract

On failure, write a typed error containing `error_code`, `step_id`, `state`, `retryable`, `evidence_refs`, `safe_state`, `residual_side_effects`, and `required_authority`. Retry only when classified retryable and within the step and episode retry caps. Otherwise transition to `HOLD`, `REPAIR`, or `ROLLING_BACK` as defined by the state machine.

