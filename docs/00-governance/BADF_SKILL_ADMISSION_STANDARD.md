# BADF Skill Admission Standard

Status: `PROPOSED_ON_PR_HEAD`
Work package: `SECB-WP-FWK-135`
Scope: external and internal reusable agent skills intended for BADF activation

## 1. Purpose

A skill is an executable instruction package, not merely documentation. Admission therefore evaluates both its semantic behaviour and its operational blast radius.

No skill is active because an upstream repository is reputable, widely used, or recommended by another agent.

## 2. Lifecycle

`DISCOVERED -> ASSESSED -> ADMITTED -> SANDBOXED -> VALIDATED -> APPROVED -> REGISTERED -> ACTIVATED -> MONITORED -> DEPRECATED/SUPERSEDED`

Every transition requires evidence. A transition may be `BLOCKED` or `REJECTED`; absence of a record is not acceptance.

## 3. Required admission record

Each candidate MUST have:

- `skill_id`, name, version;
- upstream repository URL and exact immutable commit/tag;
- license and compatibility decision;
- owner and maintainer;
- purpose, trigger, inputs, outputs, prerequisites;
- required models, packages, binaries, shell commands, subprocesses, network access, filesystem access, credentials, and external services;
- data classifications handled;
- declared authority and prohibited effects;
- prompt-injection/instruction-confusion assessment;
- supply-chain assessment;
- sandbox test results;
- routing/activation tests;
- output-to-BADF-evidence mapping;
- rollback/disable/upgrade strategy;
- known limitations and residual risks;
- approval and effective event;
- supersession/deprecation record when applicable.

## 4. Mandatory checks

### 4.1 Provenance

Pin the upstream source to an immutable commit. A moving branch or unpinned release is not an acceptable production provenance reference.

### 4.2 License

Record the license and compatibility with the downstream repository and distribution model. Unknown license status is a blocking condition.

### 4.3 Script and dependency inspection

Inspect installation scripts, lifecycle hooks, shell commands, subprocess calls, package managers, dynamic downloads, generated code, and transitive dependencies.

The admission reviewer MUST distinguish:

`declared_dependency != inspected_dependency != approved_dependency`

### 4.4 Capability declaration

Every network destination, filesystem root, executable command, credential, model/API, and external service must be declared before activation.

Undeclared capability is denied by default.

### 4.5 Prompt-injection assessment

Evaluate untrusted content boundaries. At minimum test whether repository files, issue/PR text, web pages, documents, model outputs, tool results, or skill-generated text can cause the skill to:

- reinterpret data as instructions;
- bypass authority checks;
- request undeclared tools;
- exfiltrate secrets;
- expand scope;
- modify protected paths;
- suppress or falsify evidence.

### 4.6 Sandbox

Initial execution MUST occur in a bounded environment with no production credentials and no uncontrolled external mutation.

The sandbox record MUST include command, input fixture, output, exit status, environment, and artifact digest.

### 4.7 Activation/routing

A skill MUST NOT be routable merely because it is present in a directory. Activation requires a registry record and an approved routing predicate.

Routing tests MUST include both positive and negative cases. A skill that activates for an unrelated request is a routing defect.

### 4.8 Evidence contract

Skill outputs MUST map to a BADF evidence type or explicitly be classified as non-evidence commentary.

A skill MUST NOT emit an output that looks like an authority receipt unless the output schema and authority contract explicitly permit it.

### 4.9 Authority boundary

Every skill declares:

- what it may decide;
- what it may recommend;
- what it may execute;
- what it may never execute;
- which effects require an external authority check.

The default is `confers_authority: false`.

### 4.10 Rollback and upgrade

Each admitted skill has a disable path and an upgrade procedure. An upstream update is a new candidate version unless the existing admission record explicitly proves the update is non-semantic.

## 5. Required verdict

Admission produces one of:

- `ADMIT` — all mandatory checks passed and authority boundary is bounded;
- `ADMIT_WITH_LIMITS` — activation is permitted only under explicit restrictions;
- `SANDBOX_ONLY` — useful for evaluation but not active;
- `BLOCKED` — prerequisite evidence or capability is missing;
- `REJECT` — unacceptable security, provenance, license, authority, or operational risk.

No `PASS` verdict may be produced when a required observation was skipped.

## 6. Independence

The skill author MUST NOT be the sole authority for its own admission. At minimum, security-sensitive or effect-capable skills require an independent review lens and a deterministic validation result.

Agent Council may provide the independent review. Council output is evidence and does not itself activate the skill.

## 7. Promotion

Promotion from `SANDBOX_ONLY` to `ACTIVATED` requires:

1. successful admission record;
2. passing routing tests;
3. evidence-schema mapping;
4. authority boundary verification;
5. rollback path verification;
6. version/provenance pin;
7. approval under the applicable authority class;
8. registry update;
9. effective-event record.

## 8. Required negative tests

Every admission suite MUST attempt at least:

- missing provenance;
- moving upstream ref;
- undeclared network destination;
- undeclared credential request;
- protected-path mutation;
- prompt injection that asks the skill to ignore BADF;
- output that claims authority it does not possess;
- stale routing rule;
- replay of an old activation record;
- rollback/disable failure.

## 9. Supersession

A new version does not silently replace an old version. The registry records both versions, the effective transition, and the reason for supersession.

Historical evidence remains addressable. `SUPERSEDED != DELETED`.

## 10. Initial BADF stack

The initial strategic candidate set is:

| Capability | Candidate pattern | Initial disposition |
|---|---|---|
| Skill format | Anthropic Skills specification | `ASSESS_REQUIRED` |
| Requirements | Matt grilling / to-spec / to-tickets | `ASSESS_REQUIRED` |
| Skill lifecycle | Addy Osmani Agent Skills | `ASSESS_REQUIRED` |
| Implementation | Superpowers + Matt TDD | `ASSESS_REQUIRED` |
| Governance | Agent Council + Codex Council patterns | `ASSESS_REQUIRED` |
| Context | Agent Skills for Context Engineering | `ASSESS_REQUIRED` |
| Specification | Spec Kit **or** OpenSpec | `CHOICE_REQUIRED` |
| Security | Trail of Bits practices | `ASSESS_REQUIRED` |
| Learning | Compound Engineering | `ASSESS_REQUIRED` |
| Specialists | selected wshobson agents / Orchestra Research skills | `SELECTIVE_ASSESSMENT` |

This table is a target intake queue, not an approval list.

## 11. Completion condition

The admission standard is implementation-ready when the registry schema, admission record schema, validator, sandbox fixture, routing tests, and promotion record are all present and exercised.

Until then, this document is normative policy with `binding: false` for activation decisions.
