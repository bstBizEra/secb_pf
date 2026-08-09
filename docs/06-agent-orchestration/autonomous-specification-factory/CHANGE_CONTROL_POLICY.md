# Post-Freeze Change-Control Policy

Status: Implementation Ready | Version: 1.0.0 | Work Package: `SECB-WP-ENGLOOP-002`

Every post-freeze amendment creates a change request with reason, affected requirement IDs, impact analysis, risk-tier change, revised RTM/tests, migration/rollback impact, owner and authority. Changes are classified as editorial, non-material corrective, material, or emergency.

Editorial changes that provably do not change meaning may use expedited review but still create a new baseline version and digest. Material changes return to review and ballot. Changes to scope, acceptance criteria, security controls, architecture, data, NFRs, dependencies or rollback invalidate the current readiness certificate and warrant.

Prohibited behavior:

- Editing the frozen object in place
- Weakening or deleting acceptance criteria because implementation failed
- Reclassifying a material change as editorial
- Reusing a warrant across baseline hashes
- Backdating approvals or closure evidence

An emergency amendment requires recorded emergency authority, narrow scope, time limit, compensating controls, retrospective review and a superseding normal baseline.
