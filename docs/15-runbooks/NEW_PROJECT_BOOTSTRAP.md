# Runbook — Bootstrapping a New Project From SecB

Status: **Executed 2026-08-10** through step 3 in a real fresh repository
(`bstBizEra/secb-bootstrap-trial`; record: `docs/13-evidence/TRIAL-FR12-BOOTSTRAP.md`).
The trial found four defects in this runbook, all corrected below. Steps 4–5
remain unexecuted — they need a real product definition
Work Package: `SECB-WP-FWK-017` (issue #30)
Audience: an engineer or agent starting a new BST project from this framework

Every step below is derived from an action this repository actually performed,
with the commit or run cited. Steps 1–3 have now been run in a fresh repository;
steps 4–5 are still marked **UNTESTED**, because a runbook that implies more than
it has done is the defect this framework keeps finding.

## What you are copying, and what you are not

`git ls-files` classifies into four kinds. **No path is unclassified** — if you
add one, classify it.

### Two kinds of instantiation — and this runbook was written from one of them

**Greenfield** — an empty repository. That is the trial cited at the top, and
every step below is derived from it.

**Retrofit** — porting the machinery into a repository that already exists, with
its own history, its own identifier prefixes and its own test runner. One has
happened, on 2026-08-10, and it is measured in
[`docs/13-evidence/INSTANTIATION_FIELD_REPORT.md`](../13-evidence/INSTANTIATION_FIELD_REPORT.md).
**A retrofit pays a cost a greenfield trial structurally cannot reveal:** an
empty repository has nothing to collide with, so no trial could ever discover
that this framework's `G0–G5`, `L0–L3` and `A0–A4` ladder tokens collide with
letters a live project may already be using. The retrofit had to rename all four
ladders before the machinery would fit.

If you are retrofitting, read the field report before step 1. Three things it
found that this runbook does not otherwise tell you:

- **Budget for identifier renames.** 130 lines were edited across the four
  enforcement scripts below, 45 of them mentioning a ladder token. `NFR-15`
  made the work-package *prefix* configuration; the ladders are still hard-coded
  in both code and prose.
- **Preflight your CI environment before the first real pull request.** First
  contact surfaced three environment gaps at once — an absent Python dependency,
  a shallow clone that silently broke a `git blame`-based check, and a check that
  reported "cannot run" because no database was available. Every one of them
  *looked* like a governance failure and was not. This is step 3's lesson
  applied to the environment rather than the gates.
- **Do not assume `pytest`.** The enforcement scripts are stdlib-only and are
  invoked as subprocesses, so they transfer to any runner. Their *tests* are
  `pytest`; the retrofit ran `unittest discover` and had to port them. Copy the
  tests either way — an uncopied test is an unproven gate.

### Reusable as-is — the framework

> **Corrected 2026-08-12 (`SECB-WP-FWK-052`).** "As-is" states an intent, and the
> field falsified it: all four enforcement scripts below were edited on the one
> retrofit that has happened — 130 lines. The heading is kept, with this
> correction attached, rather than softened to "mostly reusable": a vague heading
> would hide a defect that ought to be fixed instead of described. Per-control
> measured edit cost and current digests live in
> [`config/control_surface.json`](../../config/control_surface.json).
> **Check that manifest before you copy a control** — it is the only way to tell
> whether what you are about to copy has been fixed since an earlier project
> copied it. It was written because it had not been: a project instantiated two
> days before a classifier fix was still running the pre-fix logic, and nothing
> in this runbook could have told it so.

| Path | Why it transfers |
|---|---|
| `AGENTS.md` | The operating contract. Product-neutral |
| `docs/00-governance/L0_ROOT_CONSTITUTION.md` | Layers, ceilings, prohibited actions, the ladder |
| `docs/00-governance/CONTROL_GATES.md`, `RISK_AUTHORITY_MATRIX.md`, `BUDGET_CIRCUIT_BREAKER_POLICY.md` | Ten gates, R0–R4, budget policy |
| `docs/08-workflows/DELIVERY_LIFECYCLE*.md` | 14 stages, gate mapping, cross-stage rules |
| `scripts/check_work_package_ref.py`, `check_budget.py`, `classify_authority_delta.py`, `check_dual_policy.py` | The four enforcement scripts |
| `tests/test_check_*.py`, `tests/test_classify_*.py` | Their subprocess tests — **copy these too**, an uncopied test is an unproven gate |
| `.github/ISSUE_TEMPLATE/` | The work-package intake form (edit the ID placeholder) |
| `docs/16-templates/` | Templates |
| `config/ballot.schema.json` | Inert schema; keep for when identities exist |
| `.gitignore` | Keeps caches out of evidence directories |

### Rewrite before first use — same shape, your content

| Path | What to change |
|---|---|
| `config/delegation_envelope.json` | `envelope_id`, `authority_source`, `effective_from`, `expires_at`, `current_tier` (**start at `A0` or `A1`, never higher**), `scope.auto_paths`, `max_changed_lines`, `absolute_ceilings`. The ladder conditions are reusable. **Delete the `scope.constitutional_paths` entry for the sealed-evidence directory** — you never copy it, so the entry protects nothing (trial finding 4) |
| `.github/workflows/ci.yml` | **Must be edited before the first run.** Its test step hard-codes SecB's sealed-evidence test path, which is on the do-not-copy list. Left unchanged, `pytest` exits 4 and the Test gate is **red on arrival, before any product code exists** — trial finding 2. Replace that step with `python -m pytest -p no:cacheprovider -q tests/` |
| `tests/test_classify_authority_delta.py` | Prune the two assertions that reference the sealed-evidence path — they cannot hold once its envelope entry is removed (trial finding 3) |
| `config/control_surface.json` | Keep **your own** copy describing your controls: your digests, your owning work-package IDs, your measured edit costs. Do **not** just inherit SecB's digests — they describe SecB's tree, and a manifest that describes someone else's files answers your staleness question wrongly and confidently. Keep SecB's version too, unedited, somewhere you can diff against: that is the upstream reference this file exists to be (`SECB-WP-FWK-052`) |
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
| Authority | Omitting the work-package ID from title and body | `AUTHORITY GATE FAIL: no <PREFIX>-* work-package reference found` — **set `project.work_package_prefix` in the envelope first**, or the gate enforces SecB's scheme and rejects every PR you open |
| Budget | Declaring `max_lines=1` on a real diff | `BUDGET GATE FAIL: diff exceeds the declared budget` |
| Governance verdict | Touching a path listed in `scope.constitutional_paths` | `VERDICT: CONSTITUTIONAL_REQUIRED` |

Then confirm the dual-policy rule runs. **Do not expect to see divergence in a
real PR** — the earlier version of this runbook told you to, and the trial proved
it cannot happen. Editing the envelope is `G4`, and `G4` dominates before the
comparison matters, so both policies reach the same constitutional verdict and
report *"both policies agree that this escalates"*. Observed at trial:

```
VERDICT: CONSTITUTIONAL_REQUIRED — root authority surface touched: config/delegation_envelope.json
DUAL POLICY: ESCALATE — both policies agree that this escalates
```

That output **is** the healthy one. The anti-self-approval property holds earlier
and harder than divergence-hunting suggests. Divergence is observable only in
unit tests, where the policy change and the judged diff can be separated —
`test_divergence_escalates_even_when_head_would_pass` does that, and its passing
is the proof the comparison works (trial finding 5).

Record the failing run IDs. They are the evidence that your gates are real, and
the first entry in your project's evidence trail.

**Executed 2026-08-10 in a fresh repository.** Authority and Budget both tripped
with messages carrying the *new* project prefix, proving the rename reached the
enforcement path and not only the documentation; the recovery leg turned all four
gates green at trial commit `726ed96`. See `docs/13-evidence/TRIAL-FR12-BOOTSTRAP.md`.

## Decisions to make before writing code

| Decision | Consequence if deferred |
|---|---|
| Constitutional authority | No gate verdict is valid; nothing can be approved |
| Envelope tier and caps | Either every change needs a human merge, or too much does not |
| Work-package ID prefix | **One field, then a prose sweep.** Set `project.work_package_prefix` in `config/delegation_envelope.json` — the Authority Gate and its tests both read it, so **no enforcement script or test needs an edit** (`SECB-WP-FWK-036`). Then know what remains: **13 files still require an edit**, down from 18 at trial (20 still contain the string; 7 of those are provenance citations no new project should touch), and 11 of the 13 are prose — `AGENTS.md`, eight governance documents, two templates. The twelfth is `.github/ISSUE_TEMPLATE/work-package.yml`, which is irreducible because GitHub issue forms are static YAML with no interpolation. `grep -rl SECB-WP . \| xargs sed -i 's/SECB-WP/<PREFIX>/g'` still sweeps the prose; the point is that the *mechanical* surface is now one field and the prose surface is not (trial finding 1, re-measured 2026-08-11) |
| `auto_paths` and `constitutional_paths` | An unclassified path escalates — safe, but you will notice quickly |
| Whether a second identity exists | **Determines whether stage 9 is reachable at all.** One identity cannot satisfy an independence requirement; if your project must reach production, resolve this at bootstrap, not at stage 9 |

That last row is the most expensive thing in this runbook to learn late. SecB
learned it at stage 1 and recorded it; a project that discovers it with a
release candidate waiting has built something it cannot ship.

## What this runbook does not give you

- **No scaffolding script.** Two projects have now been instantiated by hand —
  and they differed *in kind* (greenfield trial, then retrofit), which is an
  argument for keeping this refusal rather than relaxing it. A generator built on
  two samples that share almost no failure modes would encode both sets of
  accidents. The trigger stands unchanged: **write it when the third project
  repeats the second.**
- **No propagation tooling.** `config/control_surface.json` makes control-surface
  staleness *computable*; a human still does the comparison. Nothing here reaches
  into an instantiated repository or checks what it is actually running — so a
  downstream running a superseded control is discoverable, not detected. Building
  the comparison tool at this `n` would encode one instantiation's accidents,
  which is the same reasoning as the paragraph above.
- **No templates for stages 3–14.** Three templates ship
  (`docs/16-templates/`). Add one when a stage actually blocks on it.
- **No external trust anchor.** The verifier runs inside the repository it
  judges; see `docs/14-plans/GOVERNANCE_DEFERRED_CAPABILITIES.md`. If your
  project lives in a GitHub organization, `D1` is available to you and worth
  doing at bootstrap.
