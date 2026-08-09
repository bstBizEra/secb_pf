# Budget and Circuit-Breaker Policy

Status: Implementation Ready
Version: 1.0.0
Work Package: `SECB-WP-ENGLOOP-001`

## Default Episode Limits

These conservative defaults apply until a stricter approved policy is configured. A work package may lower them. Increasing a hard limit requires approval from the budget owner and risk authority.

| Limit | R0 | R1 | R2 | R3 | R4 |
|---|---:|---:|---:|---:|---:|
| Wall-clock execution | 15 min | 60 min | 120 min | 120 min | Per approved runbook |
| Agent turns | 8 | 25 | 40 | 30 | Per approved runbook |
| Tool calls | 20 | 80 | 150 | 120 | Per approved runbook |
| Model tokens | 50k | 250k | 500k | 400k | Per approved runbook |
| Same-step retries | 1 | 2 | 2 | 1 | 0 unless authorized |
| Total retries | 2 | 6 | 8 | 4 | 0 unless authorized |
| Concurrent workers | 1 | 2 | 3 | 2 | Per dual-control plan |
| Parallel mutations per resource | 0 | 1 | 1 | 1 | 1 with fencing |
| Cost cap | Configured project rate card; hard reservation required before paid execution |

## Thresholds

- At 70% of any hard limit: emit `BUDGET_WARNING` and re-estimate remaining work.
- At 90%: stop starting new optional work, checkpoint, and prepare handoff.
- At 100%: emit `BREAKER_TRIPPED`, revoke mutation capability, release or freeze leases safely, and enter `HOLD`.
- A single non-retryable security, authority, integrity, or scope event trips immediately regardless of consumption.

## Breaker Domains

Budget, repetition/loop detection, authorization, scope, security, evidence integrity, control-plane health, lease/lock health, side-effect duplication, secret exposure, and deployment health each have independent breakers.

Loop detection trips when the same failure signature repeats twice without a changed falsifiable hypothesis, the same patch is applied twice, or three consecutive iterations make no measurable acceptance-criteria progress.

## Resume Contract

Resume requires a verified checkpoint, resolved trip cause, new or reconfirmed authority, refreshed budget reservation, valid lease, reconciled side effects, and a recorded decision. Counters never reset silently; the prior consumption remains attached to the episode.

## Cost Governance

Before implementation, the Orchestrator records estimated usage and maximum accepted cost using the approved rate card. If a rate card or cost owner is unavailable, paid execution is `HOLD`; read-only planning may continue. Cost per accepted change and abandoned-work cost are recorded for learning but cannot weaken safety gates.

