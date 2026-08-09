# Risk and Authority Matrix

Status: Implementation Ready
Version: 1.0.0
Work Package: `SECB-WP-ENGLOOP-001`

## Classification

| Tier | Typical work | Maximum automation | Mandatory approval |
|---|---|---|---|
| `R0` | Read-only inspection, formatting, generated draft with no system mutation | Execute within read-only envelope | Policy pre-authorization |
| `R1` | Reversible documentation, tests, lint, low-impact code in sandbox | Implement, test, open PR | Merge authority separate |
| `R2` | Material feature, API behavior, dependency or non-sensitive data change | Implement in sandbox; no autonomous merge | Product/architecture review and authorized merger |
| `R3` | Security-sensitive, migration, infrastructure, identity, regulated or sensitive data | Proposal and controlled implementation only | Security/architecture plus designated human approval |
| `R4` | Production, destructive/irreversible, high-impact policy, emergency or systemic change | No autonomous mutation | Explicit dual control and Release Gate |

## Action Matrix

| Action | R0 | R1 | R2 | R3 | R4 |
|---|---|---|---|---|---|
| Read approved context | Auto | Auto | Auto | Scoped | Scoped |
| Create plan/draft | Auto | Auto | Auto | Auto | Auto |
| Modify sandbox files | N/A | Auto | Auto | Approved | Explicit approval |
| Use external network | Deny by default | Allowlist | Allowlist | Explicit allowlist | Explicit dual control |
| Handle sensitive data | Deny | Deny | Masked only | Approved isolated controls | Explicit dual control |
| Open PR | N/A | Auto after gates | Approved | Human initiated | Human initiated |
| Merge | N/A | Policy may permit | Human authority | Human authority | Dual control |
| Change schema/infrastructure | Deny | Deny | Approved preview only | Human authority | Dual control |
| Deploy non-production | Deny | Approved preview | Approved staging | Human authority | Dual control |
| Deploy production | Deny | Deny | Deny | Deny by default | Release authority only |
| Delete/irreversible action | Deny | Deny | Deny | Explicit exception | Dual control with recovery plan |

## Classification Rules

Use the highest applicable tier. An agent cannot lower its own tier. Unknown scope, unclear data class, missing rollback, or control conflict results in `HOLD`. Changes to authentication, authorization, secrets, audit, evidence, policy, agent permissions, deployment, or production data are at least `R3`; production execution is `R4`.

## Segregation of Duties

The same identity must not implement and independently approve an `R2–R4` change. Merge and release authority are separate. Risk acceptance must be issued by the accountable risk owner, be time-bounded, identify compensating controls, and never override non-waivable controls.

