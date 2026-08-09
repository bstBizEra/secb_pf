# Delivery Lifecycle — Stage Definitions

Status: Adopted on merge of `SECB-WP-FWK-013` (issue #22)
Authority: Operator (vily), deep definition supplied 2026-08-10
Companion: [`DELIVERY_LIFECYCLE.md`](DELIVERY_LIFECYCLE.md) — state model,
cross-stage governance, and SecB's current position

Every stage must produce verifiable evidence and pass an explicit gate before
the project advances. Gate names are the state names: passing stage *n* sets
the state to that stage's gate.

---

## 1. PRD Review and Baseline → `PRD_BASELINED`

**Purpose.** Convert the draft product concept into an approved, controlled
product baseline that clearly defines the problem, expected value, scope and
measurable outcomes.

**Entry criteria.** Identified business problem or opportunity · named product
sponsor · initial stakeholder list · draft product concept or PRD ·
preliminary funding and delivery assumptions.

**Core activities.** Confirm the business problem and target users · define
the value proposition · validate strategic alignment · define in-scope and
out-of-scope capabilities · establish measurable business and product
objectives · identify assumptions, constraints and dependencies · define
high-level functional requirements · define initial non-functional
expectations · establish product acceptance criteria · identify legal,
regulatory and data considerations · record unresolved decisions and risks ·
obtain stakeholder review and formal approval.

**Required artifacts.** Product Requirements Document · product vision and
value proposition · business objectives and KPIs · scope statement ·
stakeholder register · assumption and constraint register · initial RAID
register · product acceptance criteria · approval record · PRD change-control
baseline.

**Key questions.** What specific problem is being solved? Who receives the
value? How will success be measured? What is explicitly excluded? Which
assumptions could invalidate the business case? Who has authority to approve
scope changes?

**Exit gate passes when.** Business owner and product owner are identified ·
scope and exclusions are unambiguous · success KPIs are measurable ·
acceptance criteria are testable · critical assumptions and dependencies are
documented · major regulatory concerns are identified · the PRD is versioned
and formally approved.

**Accountability.** Accountable: Product Sponsor · Responsible: Product
Manager/Owner · Consulted: Business, Architecture, Security, Legal,
Operations · Gate authority: Product Steering Committee or authorized ballot.

---

## 2. Requirement Decomposition → `REQUIREMENTS_READY`

**Purpose.** Translate the approved PRD into detailed, traceable and
implementation-ready requirements.

**Entry criteria.** Approved PRD · defined product scope · identified
stakeholders · initial acceptance criteria.

**Core activities.** Decompose into domains, capabilities and modules · define
epics, features and user stories · document business and calculation rules ·
capture functional and non-functional requirements · define data and reporting
requirements · identify integration requirements · define personas and
authorization expectations · specify error, exception and alternative flows ·
prioritize by an agreed method · establish requirement dependencies · create
bidirectional traceability · review for ambiguity, conflicts and gaps.

**Required artifacts.** Requirement catalogue · epic and feature map · user
stories with acceptance criteria · NFR catalogue · business rules catalogue ·
data requirements · integration requirements · Requirements Traceability
Matrix · dependency map · prioritization record · open-question and decision
register · **Bootstrap Story Definition of
Ready v0.1**, for assessing priority-one items before entry to Architecture
Design (`SECB-WP-FWK-019-A`; see `SPECIFICATION_CONFLICT_PROTOCOL.md` for why
the DoR is split across two stages).

**Requirement quality standard.** Every requirement is necessary,
unambiguous, feasible, testable, traceable, prioritized, owned, and version
controlled.

**Exit gate passes when.** Every approved PRD objective maps to one or more
requirements · every requirement has an owner and acceptance method · critical
business rules are documented · NFRs carry measurable targets · dependencies
and external interfaces are identified · priority-one stories satisfy the
**Bootstrap Story DoR v0.1** and remaining unresolved items are not at Blocker
level · material requirement conflicts are resolved or formally accepted.

**Accountability.** Accountable: Product Owner · Responsible: Business
Analyst/Requirements Engineer · Consulted: Architecture, Engineering, QA,
Security, Operations · Gate authority: Product Owner and Architecture Lead.

---

## 3. Architecture Design → `ARCHITECTURE_APPROVED`

**Purpose.** Define the system structure and technology decisions needed to
meet functional, operational and strategic requirements.

**Entry criteria.** Approved requirements baseline · NFR catalogue ·
integration inventory · data and security requirements.

**Core activities.** Define system context and trust boundaries · select
architecture patterns · decompose into services and components · define
deployment topology · design tenant isolation where applicable · define data
ownership and flows · select databases, queues, caches and storage · define
integration patterns · establish identity and access architecture · design
observability and audit architecture · define availability, scalability and
disaster-recovery patterns · analyze build-versus-buy · record significant
decisions as ADRs · conduct architecture risk assessment.

**Required artifacts.** System context diagram · logical, component and
deployment architecture · data-flow diagrams · integration architecture ·
data model baseline · identity and access architecture · infrastructure
topology · ADRs · technology standards and constraints · architecture risk
register · capacity and scalability assumptions.

**Architecture concerns.** Modularity and maintainability · performance and
scalability · availability and resilience · security and privacy · data
integrity · interoperability · vendor dependency · operational complexity ·
cost sustainability · exit and migration strategy.

**Exit gate passes when.** Architecture covers all critical requirements ·
technology choices are documented and justified · data ownership and trust
boundaries are explicit · high-risk decisions have approved ADRs ·
scalability, availability and recovery targets are feasible · Security and
Operations have reviewed the design · no unresolved critical architecture risk
remains.

**Accountability.** Accountable: Chief/Lead Architect · Responsible: Solution
Architect · Consulted: Product, Engineering, Security, Data, DevOps,
Operations · Gate authority: Architecture Review Board.

---

## 4. Detailed Solution Design → `SOLUTION_DESIGN_APPROVED`

**Purpose.** Transform the approved architecture into build-ready technical
specifications for engineering teams.

**Entry criteria.** Approved architecture · baselined requirements · approved
technology decisions · identified services and integrations.

**Core activities.** Define detailed component behavior · specify APIs and
event contracts · design database schemas and migrations · define state
machines and workflow transitions · design user journeys and interface
behavior · define RBAC and permission matrices · specify validation and
business-rule execution · define error codes and exception handling · design
audit events and logging requirements · define notification and reporting
behavior · document concurrency and idempotency controls · create interface
mockups or prototypes · review designs for consistency and testability.

**Required artifacts.** Detailed solution design · API specifications · event
schemas · logical and physical data models · workflow and state-transition
matrices · UX flows and approved designs · RBAC/ABAC matrix · error-contract
catalogue · audit-event catalogue · integration sequence diagrams · migration
design · data-retention design · configuration catalogue · technical
acceptance criteria.

**Exit gate passes when.** Priority-one stories have build-ready designs ·
APIs and events are versioned · database changes and rollback paths are
defined · authorization is specified for sensitive operations · error,
exception and recovery paths are documented · designs trace back to
requirements · Engineering and QA confirm the solution is implementable and
testable.

**Accountability.** Accountable: Solution Architect · Responsible: Technical
Leads and UX Lead · Consulted: Engineering, QA, Security, Product, Data ·
Gate authority: Technical Design Authority.

---

## 5. Security and Compliance Design → `SECURITY_DESIGN_APPROVED`

**Purpose.** Integrate security, privacy, regulatory and compliance controls
into the solution **before** implementation.

**Entry criteria.** Approved architecture · detailed solution design · data
classification · identity and integration design · applicable regulatory
obligations.

**Core activities.** Classify data and critical assets · conduct threat
modeling · identify abuse and fraud scenarios · define authentication and
authorization controls · design secrets and key management · specify
encryption requirements · define privacy and consent controls · establish
audit and evidence requirements · define secure coding requirements · identify
third-party and supply-chain risks · define vulnerability-management
requirements · establish security monitoring and incident-response needs · map
controls to applicable regulations or standards · define risk-treatment plans
and approved exceptions.

**Required artifacts.** Threat model · security requirements specification ·
data classification register · privacy impact assessment · compliance control
matrix · abuse-case catalogue · security architecture · secrets-management
design · security test plan · dependency and supply-chain policy ·
risk-treatment plan · security exception register.

**Exit gate passes when.** Threats have documented mitigations · sensitive
data is classified and protected · privileged operations have authorization
controls · privacy and retention obligations are addressed · security testing
requirements are incorporated into the delivery plan · critical risks are
resolved, transferred or formally accepted · security approval is recorded.

**Accountability.** Accountable: Security or Risk Owner · Responsible:
Security Architect · Consulted: Legal, Compliance, Architecture, Engineering,
Operations · Gate authority: Security and Compliance Review Board.

---

## 6. Implementation Planning → `IMPLEMENTATION_AUTHORIZED`

**Purpose.** Convert the approved design into an executable, resourced and
controlled implementation roadmap.

**Entry criteria.** Baselined requirements · approved architecture ·
build-ready solution design · approved security design · known dependencies
and constraints.

**Core activities.** Break work into implementation packages · estimate
effort, duration and cost · sequence dependencies and critical-path
activities · assign accountable owners · define release and iteration plans ·
establish development, test and staging environments · define branching and
pull-request strategies · define Definition of Ready and Definition of Done ·
prepare the test strategy · define CI/CD quality gates · plan data migration
and cutover · define rollout, rollback and feature-flag strategy · establish
delivery budgets and operational limits · update the RAID register · obtain
implementation authorization.

**Required artifacts.** Work Breakdown Structure · prioritized backlog ·
release roadmap · sprint or iteration plan · resource and responsibility
plan · cost and budget estimate · test strategy · environment plan · CI/CD
design · migration and cutover plan · release and rollback strategy ·
**Implementation Definition of Ready v1.0**, which extends the Bootstrap Story
DoR with architecture, security, testing, dependency, environment, deployment
and rollback readiness · Definition of Done · updated RAID register ·
implementation authorization record.

**Exit gate passes when.** Work packages are sized, prioritized and owned ·
environments and access controls are ready · test and security activities are
funded and scheduled · dependencies have owners and target dates · rollback
and recovery approaches are feasible · budget and capacity are approved · the
authorized body approves development commencement · **every work package bound
for Development satisfies the Implementation DoR v1.0 with complete
traceability**. Work packages that passed only the Bootstrap Story DoR must be
revalidated against v1.0 — the two certify different transitions.

**Accountability.** Accountable: Delivery Manager · Responsible: Engineering
Manager and Product Owner · Consulted: Architecture, QA, Security, DevOps,
Finance, Operations · Gate authority: Delivery Steering Committee.

---

## 7. Development → `BUILD_COMPLETE`

**Purpose.** Build the approved solution while maintaining traceability, code
quality, security and change control.

**Entry criteria.** Implementation authorization · ready backlog · available
development environment · approved designs and standards · operational CI
pipeline.

**Core activities.** Implement application code · implement infrastructure as
code · create database migrations · develop APIs and event handlers ·
implement security and audit controls · write unit and component tests ·
conduct peer code reviews · update technical documentation · run static
analysis and dependency scanning · maintain requirement-to-code traceability ·
record deviations from approved design · update ADRs when architecture
decisions change · produce reproducible builds · maintain release notes and
change records.

**Required artifacts.** Source code · automated tests · database migrations ·
infrastructure definitions · configuration templates · API implementations ·
technical documentation · code-review records · build artifacts · Software
Bill of Materials · static-analysis results · updated traceability records ·
release notes.

**Development controls.** No unreviewed direct changes to protected
branches · no embedded credentials · mandatory test coverage for critical
logic · mandatory review for sensitive components · reproducible and signed
build artifacts where required · separation between code author and final
approver · controlled exception process for failed checks.

**Exit gate passes when.** Committed scope is implemented · required code
reviews are completed · unit and component tests pass · critical
static-analysis findings are resolved · migrations include verification and
rollback procedures · documentation and release notes are updated · a
versioned release candidate can be generated.

**Accountability.** Accountable: Engineering Manager · Responsible:
Development Team · Consulted: Architecture, QA, Security, DevOps · Gate
authority: Engineering Lead.

---

## 8. Engineering Verification → `ENGINEERING_VERIFIED`

**Purpose.** Verify that the implemented system behaves according to its
technical specifications and that components work correctly together.

**Entry criteria.** Build-complete release candidate · deployed test
environment · approved test cases · stable interfaces and test data.

**Core activities.** Execute unit-test suites · perform component testing ·
execute integration and contract tests · perform database migration tests ·
execute end-to-end workflow tests · test RBAC and authorization boundaries ·
verify error and exception handling · test idempotency and concurrency
behavior · validate API and event compatibility · run regression tests ·
measure code coverage · record and triage defects · re-test defect
corrections · update the RTM with test evidence.

**Required artifacts.** Test execution report · unit and integration test
results · contract test results · end-to-end test evidence · regression
report · code-coverage report · defect register · migration test report ·
Requirements Traceability Matrix · engineering verification sign-off.

**Exit gate passes when.** All critical workflows pass · requirements have
mapped verification evidence · no open blocker or critical engineering defect
remains · accepted residual defects have owners and target dates · regression
tests pass · release candidate integrity is verified.

**Accountability.** Accountable: Engineering Lead · Responsible: Developers
and Test Engineers · Consulted: QA, Product, Architecture, Security · Gate
authority: Engineering Verification Authority.

---

## 9. Quality and Security Validation → `RELEASE_CANDIDATE_VALIDATED`

**Purpose.** **Independently** validate that the release candidate is secure,
resilient, performant and operationally fit for its target environment.

**Entry criteria.** Engineering-verified release candidate · production-like
validation environment · test data and security authorization · defined
performance and resilience targets.

**Core activities.** Conduct system and exploratory testing · execute
performance, load and stress tests · test availability and fault tolerance ·
perform backup and recovery testing · validate disaster-recovery procedures ·
conduct vulnerability scanning · perform penetration testing where required ·
test dependency and container security · verify privacy and data-retention
controls · validate monitoring, alerting and audit events · test
infrastructure and configuration security · verify regulatory control
implementation · conduct residual-risk assessment.

**Required artifacts.** System quality report · performance test report ·
resilience and failover report · backup/restore evidence · disaster-recovery
test report · vulnerability assessment · penetration-test report ·
privacy-control verification · compliance-validation matrix · security
remediation register · residual-risk statement · release-candidate validation
record.

**Severity policy.**

| Severity | Gate treatment |
|---|---|
| Critical | Mandatory failure |
| High | Normally failure; exception requires authorized risk acceptance |
| Medium | Remediation plan and risk-based decision |
| Low | May enter managed backlog |
| Informational | Document and monitor |

**Exit gate passes when.** Performance targets are achieved · recovery
objectives are demonstrated · no unaccepted critical or high security finding
remains · monitoring and audit controls are functional · required compliance
controls are verified · residual risks have authorized owners · QA and
Security **independently** approve the candidate.

**Accountability.** Accountable: Quality and Security Authorities ·
Responsible: QA, Security Testing and Platform Teams · Consulted:
Engineering, Operations, Compliance, Product · Gate authority: QA and Security
Review Board.

---

## 10. UAT and Pilot → `BUSINESS_ACCEPTED`

**Purpose.** Confirm that the system satisfies real business processes, user
expectations and operational scenarios.

**Entry criteria.** Validated release candidate · approved UAT plan · trained
business testers · representative test data · stable UAT environment.

**Core activities.** Execute business acceptance scenarios · validate
end-to-end user journeys · confirm reports and business calculations · test
role-specific access · validate exception and escalation processes · conduct
usability and accessibility review · run pilot operations with controlled
users · capture user feedback · record and classify UAT defects · confirm
operational procedures · validate training and support materials · obtain
business acceptance.

**Required artifacts.** UAT plan · business test scenarios · UAT execution
evidence · pilot report · user feedback register · UAT defect register ·
training materials · business process confirmation · acceptance conditions
register · business acceptance record.

**Exit gate passes when.** Critical business scenarios pass · business
calculations are confirmed · users can complete priority workflows · no
blocker or critical UAT defect remains · conditional acceptance items have
owners and deadlines · Product Owner and authorized business representatives
approve release.

**Accountability.** Accountable: Business Owner · Responsible: Product Owner
and Business Testers · Consulted: QA, Engineering, Operations, Support · Gate
authority: Business Acceptance Committee.

---

## 11. Production Readiness Review → `PRODUCTION_AUTHORIZED`

**Purpose.** Determine whether the organization, technology, support model and
governance controls are ready for production operation.

**Entry criteria.** Business-accepted release · quality and security
approval · completed deployment package · proposed production schedule.

**Core activities.** Review deployment and cutover procedures · verify
rollback strategy · confirm backup and restore readiness · validate production
configurations · verify monitoring, dashboards and alerts · confirm incident
and escalation processes · establish support ownership and service hours ·
validate capacity and scaling settings · confirm credentials, certificates and
secrets · review change-management records · confirm data-migration
reconciliation · verify user communication and training · conduct go/no-go
assessment · record the production authorization decision.

**Required artifacts.** Production readiness checklist · deployment runbook ·
cutover plan · rollback plan · operational runbooks · incident-response plan ·
support and escalation matrix · monitoring and alert catalogue · backup and
recovery evidence · capacity plan · migration reconciliation plan ·
communication plan · go/no-go ballot · production authorization record.

**Mandatory go/no-go dimensions.**

| Dimension | Required decision |
|---|---|
| Product | Accepted |
| Engineering | Release candidate stable |
| QA | Quality approved |
| Security | Security approved |
| Operations | Operationally supportable |
| Data | Migration and reconciliation ready |
| Business | Deployment window accepted |
| Governance | Authorized change record exists |

**Exit gate passes only when.** All mandatory readiness controls are
satisfied · release artifact identity is immutable and verified · deployment
and rollback procedures have been tested · operational ownership is accepted ·
required risk acceptances are signed · authorized decision-makers issue an
explicit go decision.

> `BUILD_COMPLETE`, `SANDBOX_TESTED` or `BUSINESS_ACCEPTED` must never be
> interpreted as production authorization.

**Accountability.** Accountable: Service Owner · Responsible: Release
Manager · Consulted: Product, Engineering, QA, Security, Operations,
Business · Gate authority: Change Advisory Board or Production Ballot
Authority.

---

## 12. Production Deployment → `DEPLOYED`

**Purpose.** Release the authorized version into production through a
controlled, observable and reversible process.

**Entry criteria.** Valid production authorization · approved deployment
window · verified immutable artifacts · deployment and rollback teams
available · production monitoring active.

**Core activities.** Confirm final go/no-go status · freeze unauthorized
changes · back up affected data and configuration · deploy infrastructure and
application changes · execute database migrations · perform data
reconciliation · run production smoke tests · verify security, monitoring and
audit events · observe error rate, latency and resource consumption · enable
features progressively where possible · communicate deployment status · roll
back if defined thresholds are breached · capture complete deployment
evidence.

**Preferred deployment strategies.** Canary release · blue-green deployment ·
rolling deployment · feature-flag activation · ring-based deployment. A
big-bang release is reserved for situations where safer progressive strategies
are technically impossible.

**Required artifacts.** Deployment execution log · artifact checksums and
versions · migration results · smoke-test evidence · production monitoring
evidence · data reconciliation report · deployment incident record if
applicable · release communication · final deployment status · rollback
evidence if invoked.

**Exit gate passes when.** The approved version is running · critical smoke
tests pass · data integrity is confirmed · monitoring and alerting operate
correctly · no rollback threshold is breached · business and operational
owners receive deployment confirmation · deployment evidence is stored in the
audit record.

**Accountability.** Accountable: Release Manager · Responsible:
DevOps/SRE/Platform Team · Consulted: Engineering, QA, Security, Product,
Operations · Gate authority: Deployment Commander.

---

## 13. Hypercare and Stabilization → `STABILIZED`

**Purpose.** Provide enhanced monitoring and rapid response immediately after
deployment until the service reaches an agreed stable operating condition.

**Entry criteria.** Successful production deployment · hypercare team
activated · monitoring and support channels operational · stabilization
criteria defined.

**Core activities.** Monitor availability, errors, latency and resource
usage · track production incidents and user complaints · reconcile migrated or
generated data · review security alerts and suspicious behavior · monitor
business transaction success · conduct frequent operational checkpoints ·
apply controlled hotfixes where authorized · track user adoption and support
volume · compare actual performance with baseline targets · confirm downstream
integrations remain stable · update operational documentation · decide whether
to extend or close hypercare.

**Required artifacts.** Hypercare dashboard · incident and defect register ·
daily stabilization report · KPI comparison · user-support report ·
data-integrity report · hotfix records · known-issues register ·
stabilization acceptance record.

**Example stabilization criteria.** No severity-one incident for the defined
observation period · error rate below approved threshold · service-level
objectives achieved · no unresolved data-integrity issue · support volume
within operational capacity · critical integrations stable · security
monitoring shows no release-related critical event.

**Exit gate passes when.** Stability thresholds are continuously achieved ·
critical deployment-related incidents are closed · remaining defects can be
managed through normal backlog processes · Operations accepts normal service
ownership · hypercare closure is approved.

**Accountability.** Accountable: Service Owner · Responsible:
Operations/SRE · Consulted: Product, Engineering, Support, Security,
Business · Gate authority: Service Operations Review.

---

## 14. Post-Implementation Review → `CLOSED_TO_BAU`

**Purpose.** Evaluate whether the initiative delivered its intended value,
capture lessons, and formally transition the service into business-as-usual
operations.

**Entry criteria.** Stabilized production service · sufficient operational and
business data · updated financial and delivery records · closed or transferred
hypercare issues.

**Core activities.** Compare actual outcomes against PRD objectives · measure
business, product and operational KPIs · review budget and schedule
performance · analyze incidents, defects and rework · evaluate architecture
and technology decisions · assess security and compliance outcomes · review
user adoption and stakeholder satisfaction · identify technical debt and
improvement opportunities · document lessons learned · transfer remaining
actions to accountable owners · update organizational knowledge and reusable
skills · authorize formal project closure or next-phase investment.

**Required artifacts.** Post-Implementation Review report · benefits
realization report · KPI scorecard · budget and schedule variance analysis ·
lessons-learned register · technical-debt register · improvement roadmap ·
residual-risk register · operational ownership confirmation · project closure
record · next-phase recommendation.

**Exit gate passes when.** Outcomes have been assessed against the approved
PRD · benefits and variances are documented · residual risks and technical
debt have owners · knowledge and operational documentation are transferred ·
remaining work is assigned to BAU or a new approved initiative · project
closure is formally authorized.

**Accountability.** Accountable: Executive Sponsor · Responsible: Product and
Delivery Managers · Consulted: all delivery and operational functions · Gate
authority: Steering Committee.

Lessons from this stage enter
[`KNOWLEDGE_REGISTER.md`](../13-evidence/KNOWLEDGE_REGISTER.md) as `Proposed`
and are promoted only through the path in
[`LEARN_LOOP.md`](../06-agent-orchestration/LEARN_LOOP.md) — a
post-implementation finding does not become an operational instruction by
being written down.
