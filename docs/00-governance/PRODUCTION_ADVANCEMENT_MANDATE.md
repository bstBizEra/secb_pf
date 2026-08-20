# SecB Production Advancement Mandate

**Record class:** operator-authored mandate, recorded verbatim in structure.
**Status:** `PROPOSED — RECORDED, NOT ADOPTED`
**Recorded by:** SECB-WP-FWK-107
**Recorded at:** 2026-08-19
**Source:** operator instruction, this repository's session channel.

> This document **records** a mandate. It does not enact one. Nothing here grants authority, adopts a
> stage model, or authorizes a deployment. It exists so that the mandate is referenceable by commit
> rather than by recollection, and so its vocabulary can be registered before it is used.
>
> Recording is deliberately separated from adoption because a proposal that arrives and is
> simultaneously acted upon has no reviewable moment. That separation is the same one
> `AUTONOMOUS_LOOP_DESIGN.md` (SECB-WP-FWK-094) makes for the loop design.

---

## 1. Goal, as given

Build, validate, secure, deploy and progressively operate SecB in production as a governed agent work
and learning control plane, advancing through:

```text
DISCOVERY → REQUIREMENTS → ARCHITECTURE → DESIGN → IMPLEMENTATION → VERIFICATION →
SECURITY ASSURANCE → RELEASE READINESS → DEPLOYMENT → PRODUCTION VALIDATION →
CONTROLLED OPERATION → CONTINUOUS IMPROVEMENT
```

The target is not a production-deployable codebase but a production SecB **service** that is
operational, secure, observable, recoverable, evidence-driven, authority-governed,
performance-measured, operationally supported, continuously validated, and capable of controlled
autonomous improvement.

The mandate states explicitly that SecB remains an authority and verification control plane, does not
become a super-agent, and that production capability does not grant unlimited authority.

## 2. Stage ladder, as given

Ten stages, each with a single exit verdict. **This is a new ladder in this repository** and is
**proposed but unregistered**; registration is deferred until an in-tree consumer exists, per
**home → use → register** — see §6.

| Stage | Name | Exit verdict |
| :--- | :--- | :--- |
| 0 | Governance and Bootstrap Foundation | `BOOTSTRAP_VERIFIED` |
| 1 | Integrated Control Plane | `CONTROL_PLANE_INTEGRATED` |
| 2 | Governed Agent Execution | `GOVERNED_EXECUTION_PROVEN` |
| 3 | Governed Learning and Reuse | `GOVERNED_LEARNING_PROVEN` |
| 4 | Production Engineering | `PRODUCTION_ENGINEERING_READY` |
| 5 | Security and Assurance | `SECURITY_ASSURANCE_PASSED` (blocked → `SECURITY_HOLD`) |
| 6 | Operational Readiness | `OPERATIONALLY_READY` |
| 7 | Controlled Production Release | `PRODUCTION_ACTIVATED` |
| 8 | Production Validation | `PRODUCTION_VALIDATED` |
| 9 | Governed Autonomous Operation | `GOVERNED_AUTONOMOUS_OPERATION` |

Stage 0 completion authorizes controlled implementation; it does **not** authorize production
deployment. Production activation must not be inferred from technical deployability — the mandate
requires an explicit, independently verifiable authorization.

## 3. Authority reservations, as given

SecB may act autonomously only where the action is explicitly delegated, inside the approved autonomy
envelope, reversible or covered by tested compensation, below the risk threshold, dependency-ready,
security-safe, evidence-producing, and deterministically validated.

Independent authorization is required for: constitutional or authority-model changes; production
activation; material scope expansion; acceptance of critical or high residual risk; irreversible data
operations; destructive recovery; secret or trust-root changes; compliance exceptions; business-policy
decisions; and any change that enlarges SecB's own authority.

> **Production access is execution capability, not governance authority.**

## 4. Measured baseline at recording time

Measured against `main@ace1e57`, not asserted. This section is the reason the document is worth
landing: the mandate spans a much larger distance than the open pull-request queue suggests, and a
stage model with no recorded starting point cannot measure advancement.

```text
EFFECTIVE ON MAIN
  scripts/                14 gate scripts (budget, authority delta, dual policy, control graph, …)
  tests/                  22 files, 439 passing
  config/                 delegation_envelope.json · control_surface.json · ballot.schema.json
                          identifier_taxonomy.json (26 ladders, 5 recorded collisions)
  src/                    2 files — secb_router/
  evidence/               sealed FWK-009 bundle
  infra/ templates/       EMPTY (.gitkeep only)

BUILT BUT NOT EFFECTIVE — 22 open pull requests
  schemas/                17 schemas (work package, context receipt, verdict, transition, authority …)
  config/state_machine.json   31 states, 50 edges
  governance/scope/       frozen scope, exclusions, invariants, stability targets
  work/                   transition ledger, framework iterations

NO SUBSTRATE
  service entrypoint      none — no pyproject, container, compose file or MCP server process
  deployment topology     none — infra/ is empty
  environments            secb.yaml records production: NONE_DECLARED
  operate capability      secb.yaml records deploy_and_operate: NO_SURFACE
```

`secb.yaml`'s own `NO_SURFACE` and `NONE_DECLARED` lines are **accurate**, and they are the honest
answer to where Stages 4–8 stand: those stages govern a service that does not yet exist. SecB today is
a governance gate suite plus a two-file router.

### Stage assessment

```text
Stage 0   PARTIAL   — fail-closed admission, protected surfaces and a verification baseline are
                      effective; the Work Package contract, schemas, state machine, audit ledger and
                      repository validation are built and unlanded. Exit verdict NOT issuable.
Stage 1   BUILT_NOT_INTEGRATED — components exist as scripts and schemas. "Integrated control plane"
                      implies a running plane; there is no process to integrate into.
Stage 2   NOT_STARTED — no runtime to route work through.
Stage 3   PARTIAL_DESIGN — learning-candidate schema exists (adopted: const false). No intake path.
Stage 4-8 NO_SUBSTRATE — nothing to engineer, secure, operate, release or validate yet.
Stage 9   NOT_APPLICABLE.
```

## 5. The gate this mandate meets immediately

The mandate's §7 requires that a human decision gate block only the affected transition. Two
transitions are blocked at recording time, and they are named here so the block is legible rather than
rediscovered each round:

1. **Stage 0 exit** requires its artifacts to be effective. They are built and unlanded, and `PA-01`
   makes merge an operator act. The blocked action is `git merge`, not a build task.
2. **Stage 7 and beyond** require authority the current mandate does not contain.
   `config/delegation_envelope.json` caps at `absolute_ceilings.max_tier: A4`, its `current_tier` is
   `A1`, and its `ballot_layer.state` is `NOT_ACTIVE` for a structural reason. Deployment authority is
   not on that ladder at any tier. Granting it is an envelope amendment, which `PA-02` prohibits an
   agent from performing.

```text
MANDATE_RECEIVED ≠ AUTHORITY_GRANTED
```

Recording this mandate does not change either. See issue #184 for the ladder collision that makes the
autonomy fields ambiguous, which should be resolved before any stage verdict cites them.

## 6. Vocabulary registration

This mandate introduces a `Stage 0-9` ladder and ten exit verdicts. `config/identifier_taxonomy.json`
records 26 ladders and 5 collisions, and its guard requires every registered ladder to declare a home
and an enforcer. This document is that home. Registration is filed separately rather than performed
here, because the registry's own rule is that a ladder is recorded when it is **in use**, and nothing
uses this one yet.

Unregistered use is not hypothetical: the `A` prefix is registered as `A0-A4` bound to the envelope's
authority tiers, and `secb.yaml` rebinds it to a capability ladder with a value (`A5`) outside the
registered form. The registry did not catch it because its observation boundary covers markdown
declaration tables and explicitly excludes machine-readable carriers.

```text
REGISTRY_INTERNALLY_CONSISTENT ≠ TREE_FREE_OF_COLLISIONS
```

## 6. Vocabulary

Declared in the form `tests/test_mandate_vocabulary.py` (SECB-WP-FWK-116) verifies against
`config/identifier_taxonomy.json`. Status vocabulary is closed: `COLLIDES`, `NEW`, `REGISTERED`.

| Prefix | Used for | Registry status |
| :--- | :--- | :--- |
| `Stage` | Stage 0–9 and their ten exit verdicts | NEW — home is this document |
| `PA` | PA-01…PA-05 prohibited actions, cited from `secb.yaml` | NEW — see §6.1 |
| `A` | *(cited, not introduced — `max_tier: A4`, `current_tier: A1`)* | REGISTERED `A0-A4` |
| `G` | *(cited, not introduced — change classes in the authority analysis)* | REGISTERED `G0-G5` |

`A` and `G` are cited rather than coined: §5's blocking analysis reads the envelope's own ladder
values. Declaring them REGISTERED records that this document consumes the registered meaning and does
not rebind it — which is exactly what #184 shows `secb.yaml` did do with `A`.

### 6.1 `PA` is unregistered and already in use

```text
registry     no `PA` ladder, no `PA` reservation
in use       secb.yaml prohibited_actions PA-01 … PA-05, arriving with #171
cited by     this document (§3) and the agentic-learning record
```

A fifth unregistered prefix, and the only one of the five already bound to a file that ships with an
open pull request. It is not a collision — nothing else claims `PA` — but it is an identifier doing
governance work with no registry entry, which is the condition #188 exists to close.

Registration is owed under **home → use → register**: `PA` has a home (`secb.yaml`) and is in use, so
unlike `Stage` it is not speculative. Recorded here rather than registered, because
`config/identifier_taxonomy.json` is claimed by #113 and #123 and the ordering in #182 is undecided.

## 7. What this document is not

- Not an adoption of the stage model. No stage verdict may cite this document as authority.
- Not a scope change. The frozen scope is `SECB-SCOPE-001`; reconciling this mandate against it is a
  separate act requiring the scope's own change procedure.
- Not an authorization to build production infrastructure. Stage 4 work would be premature under the
  Lean Engineering minimality ladder while Stage 0 has not exited.
- Not a claim that the stage assessment in §4 is complete. It is measured at one commit, by one agent,
  against the checklists the mandate states — no independent verification.
