# Mandatory Control Gates

Status: Draft
Work Package: `SECB-WP-FWK-001`

| # | Gate | Decision question | Minimum evidence |
|---:|---|---|---|
| 1 | Authority | Is the work authorized for this actor and scope? | Ticket, identity, authority, scope, expiry |
| 2 | Readiness | Are requirements and acceptance criteria sufficient? | Approved requirement, exclusions, dependencies, DoR |
| 3 | Architecture | Are significant decisions documented and compatible? | Architecture review and ADRs where triggered |
| 4 | Implementation | Do changes meet engineering and policy standards? | Change set, linting, review, traceability |
| 5 | Test | Are required tests complete and passing? | Test plan, results, coverage, regression evidence |
| 6 | Security | Are critical risks resolved or formally accepted? | Threat assessment, scan results, risk disposition |
| 7 | Evidence | Is the decision package complete and reproducible? | Evidence manifest, provenance, checksums, links |
| 8 | Release | Is deployment explicitly authorized and reversible? | Approval, release plan, rollback, readiness checks |
| 9 | Learning | Is the proposed lesson supported and bounded? | Episode evidence, diagnosis, validation, scope |
| 10 | Skill Promotion | Is the skill safe, reusable, benchmarked, and approved? | Evaluation, baseline, conflict check, owner, version |

## Gate Outcomes

Each gate returns one of: `PASS`, `PASS_WITH_CONDITIONS`, `HOLD`, or `REJECT`.

Conditions, exceptions, approvers, evidence references, and expiration dates must be recorded. A failed mandatory gate stops downstream state transitions.

