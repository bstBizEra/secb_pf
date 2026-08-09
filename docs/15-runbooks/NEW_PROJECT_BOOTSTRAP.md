# Runbook — Bootstrapping a New Project From SecB

Status: Written 2026-08-10 · **Never executed end to end** — SecB is project #1
Work Package: `SECB-WP-FWK-017` (issue #30)
Audience: an engineer or agent starting a new BST project from this framework

Every step below is derived from an action this repository actually performed,
with the commit or run cited. Steps that have never been run in a *new* repo are
marked **UNTESTED**, because a runbook that implies more than it has done is the
defect this framework keeps finding.

## What you are copying, and what you are not

`git ls-files` classifies into four kinds. **No path is unclassified** — if you
add one, classify it.

### Reusable as-is — the framework

| Path | Why it transfers |
|---|---|
| `AGENTS.md` | The operating contract. Product-neutral |
| `docs/00-governance/L0_ROOT_CONSTITUTION.md` | Layers, ceilings, prohibited actions, the ladder |
| `docs/00-governance/CONTROL_GATES.md`, `RISK_AUTHORITY_MATRIX.md`, `BUDGET_CIRCUIT_BREAKER_POLICY.md` | Ten gates, R0–R4, budget policy |
| `docs/08-workflows/DELIVERY_LIFECYCLE*.md` | 14 stages, gate mapping, cross-stage rules |
| `scripts/check_work_package_ref.py`, `check_budget.py`, `classify_authority_delta.py`, `check_dual_policy.py` | The four enforcement scripts |
| `tests/test_check_*.py`, `tests/test_classify_*.py` | Their subprocess tests — **copy these too**, an uncopied test is an unproven gate |
| `.github/workflows/ci.yml`, `.github/ISSUE_TEMPLATE/` | The gates and the work-package intake form |
| `docs/16-templates/` | Templates |
| `config/ballot.schema.json` | Inert schema; keep for when identities exist |
| `.gitignore` | Keeps caches out of evidence directories |

### Rewrite before first use — same shape, your content

| Path | What to change |
|---|---|
| `config/delegation_envelope.json` | `envelope_id`, `authority_source`, `effective_from`, `expires_at`, `current_tier` (**start at `A0` or `A1`, never higher**), `scope.auto_paths`, `max_changed_lines`, `absolute_ceilings`. The ladder conditions are reusable |
| `README.md` | Your project |
| `docs/INDEX.md` | Keep the directory map; replace every "governed baseline" claim with what you actually have — **an INDEX that overstates is the first defect this repo ever found** |
| `docs/01-requirements/PRD-*.md` | Your product. Use `docs/16-templates/PRODUCT_DEFINITION_TEMPLATE.md` |
| `docs/11-operations/PERFORMANCE_INDICATORS.md` | KPI layers transfer; targets do not |

### Project-specific — read as worked examples, then delete or archive

| Path | Note |
|---|---|
| `docs/13-evidence/*RECORD*.md`, `STAGE_GATE_*.md`, `*INDEPENDENT_REVIEW*.md` | SecB's evidence. Useful as models of the required shape; **not yours** |
| `docs/14-plans/SECB-WP-*.md` | SecB work packages |
| `docs/17-references/RESEARCH-*.md` | SecB research; the K-09 and SoD findings generalize, the numbers do not |
| `docs/01-requirements/{STAKEHOLDER_REGISTER,RAID_REGISTER,KPI_BASELINE}.md` | Rewrite from the templates; SecB's risks are not yours |
| `docs/00-governance/SINGLE_IDENTITY_SOD_ACCEPTED_RISK.md` | Only if your project has the same collapse — and then re-accept it explicitly, never inherit an acceptance |

### Do not copy

| Path | Why |
|---|---|
| `docs/06-agent-orchestration/skill-router/SECB-WP-ENGLOOP-MVP-001 — Sandbox Evidence/` | A **sealed** evidence package whose certification voids on change. Copying it into another repo produces an artifact that claims a certification it does not have |
| `src/secb_router/` | SecB's product code |
| `docs/06-agent-orchestration/{durable-workflow,autonomous-specification-factory,autonomous-git-controller}/` | 48 files of heavyweight design for one product. Pull individual contracts if a real task needs them; wholesale copying is how a starter kit becomes unusable |

## The first five actions, in order

1. **Decide who holds constitutional authority.** One named party. Everything
   downstream — the envelope, every gate verdict, the merge rule — resolves to
   this. Record it in `L0_ROOT_CONSTITUTION.md`.
2. **Write the envelope at the lowest tier you can live with.** `A0`
   (documentation only) or `A1`. It is a `G4` act to raise it later, which is
   the point; starting low costs a few human merges, starting high costs the
   control. Set `expires_at` — a delegation that never lapses is never
   re-examined.
3. **Prove the gates fail.** See below. Do this before writing product code.
4. **Write the PRD** from the template, then open stage 1 and prepare its gate
   record — with the `decision` field **empty**. The authority issues; the
   executor records.
5. **Take the stage-1 verdict**, then open stage 2. You are now on the
   lifecycle and every later state has an evidence trail behind it.

At the end of step 5 your project is at `PRD_BASELINED` with stage 2 open. That
is the same position SecB reached at commit `afddd5a`, and it took SecB sixteen
work packages to get there mostly because it was building the machinery you are
copying.

## Step 3 in detail — prove the gates can fail

A copied gate is an **unproven** gate. Green CI proves nothing: a gate wired to
nothing is also green (`KN-001`, from the review that found the authority gate
had never been observed failing).

For each of the three enforcement gates, open a throwaway PR that should fail,
confirm it does, then fix it:

| Gate | Make it fail by | Expect |
|---|---|---|
| Authority | Omitting the work-package ID from title and body | `AUTHORITY GATE FAIL: no SECB-WP-* reference` — **change the prefix regex in `check_work_package_ref.py` to your project's ID scheme first** |
| Budget | Declaring `max_lines=1` on a real diff | `BUDGET GATE FAIL: diff exceeds the declared budget` |
| Governance verdict | Touching a path listed in `scope.constitutional_paths` | `VERDICT: CONSTITUTIONAL_REQUIRED` |

Then confirm the dual-policy rule works, which is the control that prevents a
policy from approving its own widening: add a path to `scope.auto_paths` and
change a file under it in the same PR. Expect
`DUAL POLICY: ESCALATE — base and head policies disagree`. If it passes, the
comparison is not running and the anti-self-approval property is absent.

Record the failing run IDs. They are the evidence that your gates are real, and
the first entry in your project's evidence trail.

**UNTESTED in a fresh repository.** In SecB these were proven on runs
`31320436859` (authority), `31325014002` (budget) and on the Genesis PR
(constitutional). The procedure is transcribed from those; it has not been
re-run from a clean clone.

## Decisions to make before writing code

| Decision | Consequence if deferred |
|---|---|
| Constitutional authority | No gate verdict is valid; nothing can be approved |
| Envelope tier and caps | Either every change needs a human merge, or too much does not |
| Work-package ID prefix | The authority gate matches `SECB-WP-*`; yours will not match until changed |
| `auto_paths` and `constitutional_paths` | An unclassified path escalates — safe, but you will notice quickly |
| Whether a second identity exists | **Determines whether stage 9 is reachable at all.** One identity cannot satisfy an independence requirement; if your project must reach production, resolve this at bootstrap, not at stage 9 |

That last row is the most expensive thing in this runbook to learn late. SecB
learned it at stage 1 and recorded it; a project that discovers it with a
release candidate waiting has built something it cannot ship.

## What this runbook does not give you

- **No scaffolding script.** One project has been bootstrapped, by hand. A
  generator built from n=1 would encode this project's accidents. Write it when
  the third project repeats the second.
- **No templates for stages 3–14.** Three templates ship
  (`docs/16-templates/`). Add one when a stage actually blocks on it.
- **No external trust anchor.** The verifier runs inside the repository it
  judges; see `docs/14-plans/GOVERNANCE_DEFERRED_CAPABILITIES.md`. If your
  project lives in a GitHub organization, `D1` is available to you and worth
  doing at bootstrap.
