# Review and Ballot Contract

Status: Implementation Ready | Version: 1.0.0 | Work Package: `SECB-WP-ENGLOOP-002`

## Review routing

Architecture review is mandatory for component, interface, data-boundary or NFR changes. Security review is mandatory for identity, secrets, external inputs, privileged actions, supply chain, regulated/sensitive data or infrastructure. Privacy, data, operations, legal and business reviews are triggered by declared scope.

Each finding contains ID, reviewer identity, independence status, severity, requirement/section reference, rationale, required disposition, owner, due date and evidence. `Critical` and `High-blocking` findings veto approval until independently verified closed or formally accepted by an authorized exception path.

## Ballot

The ballot record defines eligible voters, roles, quorum, threshold, veto roles, close time and options: `APPROVE`, `APPROVE_WITH_CONDITIONS`, `REJECT`, `ABSTAIN`. Identity and eligibility are verified at vote time. Duplicate, late, expired or unauthorized votes are rejected. Abstention does not count as approval.

Approval requires quorum, threshold, all veto checks clear, and every condition classified as pre-freeze, pre-build, pre-merge or pre-release. A machine may evaluate objective rules; it may not fabricate voter authority or override mandatory human approval.

## Condition closure

Each condition has stable ID, source, owner, due gate, closure evidence and independent verifier. A condition is `OPEN`, `IN_PROGRESS`, `VERIFIED_CLOSED`, `WAIVED_AUTHORIZED`, or `EXPIRED`. Only `VERIFIED_CLOSED` or a permitted, signed waiver satisfies the relevant gate.
