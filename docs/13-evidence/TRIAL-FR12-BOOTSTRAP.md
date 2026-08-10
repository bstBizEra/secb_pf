# Trial Record — `FR-12`, Bootstrap of a Fresh Project

Executed: 2026-08-10 · Work Package: `SECB-WP-FWK-021` (issue #40)
Trial repository: `bstBizEra/secb-bootstrap-trial` (private, **disposable**)
Subject: `docs/15-runbooks/NEW_PROJECT_BOOTSTRAP.md`, which shipped marked
*never executed end to end*

## Why this was run

`FR-12` was the single priority-one requirement that failed the Bootstrap Story
DoR (criterion 3, testable acceptance). Its acceptance method cannot execute
inside SecB: instantiation is only provable by instantiating. The runbook was
transcribed from SecB's own history rather than replayed from a clean clone, so
its correctness was assumed, not known.

It is now known. The runbook works, and it was wrong in four places — one of
which makes a fresh instantiation's CI red before any product code exists.

## What was run, in order

| Step | Action | Result |
|--:|---|---|
| 1 | Copy the runbook's *reusable as-is* set — 26 files: `AGENTS.md`, `.gitignore`, 5 governance docs, 2 lifecycle docs, 4 templates, 4 enforcement scripts, 4 test modules, 2 config files, CI workflow, 2 issue templates | Copied |
| 2 | Verify the *do-not-copy* list is absent | `docs/06-agent-orchestration/`, `src/secb_router/`, `docs/13-evidence/`, `docs/14-plans/` — all absent ✔ |
| 3 | Run the copied suite before any edits | **58 passed** — the suite is portable |
| 4 | Rewrite project identity (`SECB-WP` → `TRIAL-WP`) | **18 files** — see finding 1 |
| 5 | Rewrite the envelope: `ENV-TRIAL-2026-001`, tier **`A0`**, 30-day expiry | Done; one dead entry removed — finding 4 |
| 6 | Re-run the suite after renaming | **2 failed, 56 passed** — finding 3 |
| 7 | `git init`, commit, create the GitHub repo, push | `3da0d3c`, 27 files |
| 8 | Runbook step 3: open a PR that should trip the gates | Three failed. **One of them should not have** — finding 2 |
| 9 | Fix the CI defect, re-run | Test gate green; Authority and Budget still failing as designed |
| 10 | Recovery leg: add the ticket reference and a real budget | **All four gates green** at `726ed96` |
| 11 | Runbook step 3's dual-policy probe | Produced a different output than the runbook predicts — finding 5 |

## What worked

- **The four-gate structure functioned end to end in a repository that had
  existed for minutes.** Authority and Budget both tripped with correct
  messages carrying the *new* project prefix — `AUTHORITY GATE FAIL: no
  TRIAL-WP-* work-package reference found` — proving the rename reached the
  enforcement path and not merely the documentation.
- **Recovery works.** Adding a work-package reference and an adequate budget
  turned all four gates green at `726ed96`, so the gates discriminate rather
  than simply refuse.
- **56 of 58 tests are portable** with no edits at all.
- **No step required operator input.** Steps 1–3 of the runbook's five ordered
  actions are genuinely product-agnostic, as claimed.

## Findings

### Finding 1 — the identity rewrite touches 18 files, not one

The runbook says: *"change the prefix regex in `check_work_package_ref.py` to
your project's ID scheme first."* Measured reality:

| Kind | Files |
|---|---:|
| Enforcement scripts | 3 (`check_work_package_ref.py`, `classify_authority_delta.py`, `check_dual_policy.py`) |
| Test modules | 2 |
| Config | 1 |
| CI + issue template | 2 |
| Documents the runbook classifies **reusable as-is** | **10** — including `AGENTS.md`, `L0_ROOT_CONSTITUTION.md`, `CONTROL_GATES.md`, `RISK_AUTHORITY_MATRIX.md`, `BUDGET_CIRCUIT_BREAKER_POLICY.md`, `SPECIFICATION_CONFLICT_PROTOCOL.md` |
| **Total** | **18** |

`NFR-15` claimed "0 edits to `scripts/` required — configuration and content
only" with one known exception. That is wrong by an order of magnitude, and the
error is in the direction that flatters the framework.

### Finding 2 — the copied CI is broken on arrival · **most severe**

`ci.yml` is classified *reusable as-is*. It hard-codes the sealed-evidence test
path, which is on the **do-not-copy** list. In a fresh repository that directory
does not exist, so:

```
ERROR: file or directory not found: docs/06-agent-orchestration/skill-router/…/test_router.py
no tests ran in 0.00s
##[error]Process completed with exit code 4
```

**The Test gate fails on arrival, before any product code exists.** A new
project's first CI run is red for a reason that has nothing to do with their
work — the most discouraging possible first impression, and the exact opposite
of what a starter kit is for. Two runbook statements are in direct contradiction
and neither noticed the other.

### Finding 3 — the copied test suite asserts SecB-specific envelope content

Two tests in `test_classify_authority_delta.py` assert that the sealed-evidence
path is `CONSTITUTIONAL_REQUIRED`. That path is on the do-not-copy list and its
envelope entry is therefore removed, so both fail after a correct rename. The
runbook says *"copy these too, an uncopied test is an unproven gate"* — true,
and incomplete: they are not portable without pruning.

### Finding 4 — the envelope ships a dead constitutional path

`scope.constitutional_paths` includes the sealed-evidence directory. A project
following the runbook never copies it, so the entry protects nothing. Harmless
but it is dead configuration in the file a new project is told to edit most
carefully.

### Finding 5 — the dual-policy probe cannot produce the output the runbook predicts

The runbook says: *"add a path to `scope.auto_paths` and change a file under it
in the same PR. Expect `DUAL POLICY: ESCALATE — base and head policies
disagree`. If it passes, the comparison is not running."*

Observed instead:

```
VERDICT: CONSTITUTIONAL_REQUIRED — root authority surface touched: config/delegation_envelope.json
DUAL POLICY: ESCALATE — both policies agree that this escalates
```

**Editing the envelope is `G4`, and `G4` dominates before the comparison
matters.** Both policies see the same constitutional verdict, so they agree —
divergence is unobservable through this probe, and through any single real PR,
because the classifier and envelope are themselves constitutional paths.

The anti-self-approval property still holds; it holds *earlier and harder* than
the runbook describes. But a new project following that instruction would see
"both agree" where they were told to expect "disagree", and could reasonably
conclude the mechanism is broken. Divergence is provable only in unit tests,
where the policy change and the judged diff can be separated —
`test_divergence_escalates_even_when_head_would_pass` does exactly that.

## `FR-12` verdict: partially verified

**Verified:** the procedure is followable; the copy classification is materially
correct for directories; the gates function, trip and recover in a fresh
repository within one session; no step needs operator input.

**Not verified:** steps 4–5 of the ordered actions — write the PRD and take the
stage-1 verdict — were not run, because they require a real product definition
and this trial deliberately invented none. The claim *"a new project can be
instantiated"* is proven for the framework layer and unproven for the product
layer.

**Residue carried forward:** `FR-12` remains short of full verification until a
real product traverses stages 1–2 in an instantiated repository. That is a
different act from this trial and it needs a product, not another trial.

## The trial repository is disposable

It exists as evidence for this record and for nothing else. To remove it:

```bash
gh repo delete bstBizEra/secb-bootstrap-trial --yes
rm -rf /mnt/c/laragon/www/secb-bootstrap-trial
```

Keeping it costs nothing and preserves the CI runs cited above; deleting it
loses that evidence but the findings are recorded here.
