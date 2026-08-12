# Analysis — WICG v1.0 against measured contention

Status: Analysis complete · **nothing installed by this document** · `SECB-WP-FWK-038` (issue #72)
Occasion: the operator supplied *"WICG v1.0 — Work Intake, Deduplication &
Conflict Guard"* on 2026-08-11, proposing to upgrade `AGENTS.md` §4 from *"No
Ticket, No Work"* to *"No admitted ticket, no valid scope, no active lease — no
work and no mutation"*, with a portfolio-level registry, resource taxonomy, lease
manager and scheduler.
Companion: `ANALYSIS-ADEC-V1.md` (`FWK-037`, PR #71) — the same intake discipline
applied to the previous supplied specification.

## Verdict up front

**WICG diagnoses a real class of failure and aims it at the layer where SecB has
never failed.** Measured below: the contention its lease manager, scheduler and
resource taxonomy exist to prevent has occurred **0 times in 36 pull requests**,
at a concurrency ceiling of **2**. Meanwhile the duplication that has actually
cost this project sits one layer up, at **specification intake**, where the last
two supplied documents scored **2 for 2**.

So the recommendation is neither adopt nor reject:

| | |
|---|---|
| **Adopt now** — cheap, evidence-backed | 3 items, ~1 script and 2 template fields |
| **Defer with a named activation trigger** | 7 items, including the registry, leases and scheduler |
| **Rewrite before installing** | 2 items — one would make every prior work package retroactively non-compliant |
| **Already in force** | 6 items |
| **Vocabulary** | a 10th verdict set, with 4 collisions to resolve first |

## 1. The measurement that decides the shape

Contention requires two work items open at once. Across every pull request the
repository has ever had:

```bash
gh api --paginate "repos/bstBizEra/secb_pf/pulls?state=all&per_page=100" \
  --jq '.[] | [.number, .created_at, (.closed_at // "OPEN")] | @tsv'
# swept as an interval overlap
```

```text
pull requests, all time            36
maximum simultaneously open         2      (never 3)
times a PR opened while another was open   3      (#23, #31, #71)
```

For each of those three episodes, the file sets of the concurrent pair:

```bash
comm -12 <(gh api repos/bstBizEra/secb_pf/pulls/$A/files --jq '.[].filename' | sort) \
         <(gh api repos/bstBizEra/secb_pf/pulls/$B/files --jq '.[].filename' | sort)
```

```text
#21 (10 files) ∩ #23 (4 files)  =  0
#69  (6 files) ∩ #71 (2 files)  =  0
```

**Zero write-write contention in the project's history.** Not "handled well" —
never occurred. One executing agent produces one writer, and the peak
concurrency of 2 arose from *merge blockage*, not from parallel agents: #69 and
#71 are both mine, opened sequentially, and both are waiting on a human.

That is the trigger worth naming. **Concurrency here is a function of how long
work waits to merge, not of how many agents exist.** `K-06`'s median is 5.5
minutes; at that latency two items rarely coexist. The two open today have been
waiting hours.

## 2. Where SecB actually bleeds — one layer up

| Incident | Layer | Cost |
|---|---|---|
| `FWK-011` superseded by `FWK-012`; PR #19 closed unmerged | Specification | One PR's work discarded |
| ADEC v1.0 restated 11 of 24 elements already installed | Specification intake | One full analysis work package (`FWK-037`) |
| WICG v1.0 proposes `EXTERNAL_AUTHORITY_REQUIRED`, which ADEC proposed one message earlier for a different set | Specification intake | Caught here, at analysis cost |
| `K-09` series maintained in issue comments *and* the KPI row, disagreeing | Duplicate ownership (`SC-02`) | Corrected in `FWK-034`/`FWK-035` |
| Work-execution write-write contention | Execution | **0 in 36** |

**Duplicate-work incidents in SecB are concentrated where a specification
arrives, not where work executes.** The last two intakes both contained material
already installed — a rate of 2 for 2 — and both were caught by a human-driven
mapping pass costing a work package each.

WICG's registry, leases and scheduler address the row with a zero. Its
*canonical-key and delta discipline* addresses the rows with the incidents. The
lean cut follows from that split, not from a preference about complexity.

## 3. Component map

| WICG element | Status in SecB | Verdict |
|---|---|---|
| *No ticket, no work* | `AGENTS.md` §4, enforced by `scripts/check_work_package_ref.py` | Already in force |
| Mandatory intake fields (objective, deliverables, acceptance criteria, non-goals) | `AGENTS.md` §7 + `.github/ISSUE_TEMPLATE/work-package.yml`, **10 required fields** including *Scope and exclusions* (= non-goals) and *Target state transition* | Already in force |
| Stop on scope expansion | `AGENTS.md` §6 — *"Scope expansion beyond the approved work package"* is a stop condition | Already in force |
| Fail closed on uncertain scope | `AGENTS.md` §4 — *"Fail closed when identity, authorization, scope, evidence, or policy is uncertain"* | Already in force |
| Supersession record instead of silent replacement | In force in practice: `STAGE_GATE_PRD_BASELINED.md` v1.0.0 carries a superseded banner and is retained; `CONDITION_REGISTER.md` has a `Superseded` state in its set algebra | Already in force |
| Append-only correction of prior verdicts | `L0` §*"Evidence, once recorded, is append-only"*; `K09_LEDGER.md` corrections table | Already in force |
| `DUPLICATE` / `OVERLAP` / `DEPENDENCY` / `CONFLICT` as four distinct dispositions | `SPECIFICATION_CONFLICT_PROTOCOL.md` distinguishes `SC-02` duplicate ownership and `SC-08` circular dependency — but for **specifications**, not work items | **Extends** — same taxonomy shape, new object |
| `INTENTIONAL_OVERLAP` with separation of duties | No counterpart in SecB. The sibling project's constitution has earned an equivalent rule — *"One pane per task… a parallel draft requires an explicit cross-pane handshake declaring which output is canonical"* | **New here, proven there** |
| `idempotency_key` = source system + request ID | No counterpart. GitHub issue numbers serve accidentally | **New, cheap** |
| `canonical_work_key` = objective + deliverables + targets + acceptance version | No counterpart | **New, cheap** |
| Delta rule `NEW_SCOPE = REQUESTED − EXISTING` | Practised by hand — the ADEC analysis imported 5 new elements and 6 extensions from 24, discarding 11 | **New as a written rule** |
| `baseline: commit_sha + policy_version + adr_versions` | Not an intake field. PRs carry a head SHA; no work item records the policy version it was admitted against | **New, cheap, and the highest-value field** |
| `read_set` / `write_set` / `interface_set` | Not an intake field. Computed post-hoc from `git diff --name-only` | **New — worth one field, not a taxonomy** |
| File-set intersection against open work | Done by hand for #69↔#71 and #71↔#72 | **New, one command, should be a gate** |
| Work lease with holder identity, expiry, renew | No counterpart, and **no contention to arbitrate** (§1) | **Defer** |
| Global Work Registry, Project Contract Registry | No counterpart. One project exists | **Defer** |
| Resource taxonomy with hierarchical locks (`schema:core` ⊃ `table:property`) | No counterpart. No database, no deployed service, no API | **Defer** |
| Scheduler with priority and capacity | No counterpart. Capacity is one agent | **Defer** |
| Semantic duplicate detection with a weighted score | No counterpart. The proposal's own rule — *LLM proposes candidates, never rejects alone* — is right, and calibration needs history that does not exist | **Defer, `SHADOW` first** |
| Cross-project conflict graph, integration contracts | No second project | **Defer** |
| `WI-01`–`WI-10` KPI family | 11 KPIs in force; `WI-05` overlaps `K-06` | **Defer, and dedupe first** — §6 |
| Deterministic policy engine for the final verdict, LLM only for normalization | Already the architecture: `classify_authority_delta.py` is deterministic and stdlib-only | Already in force |
| Twelve admission verdicts | Eight vocabularies in force; ADEC proposed a ninth | **10th set — resolve collisions first**, §5 |
| §7 rule 1: no work without `ADMITTED` and an active lease | Would invalidate all prior work | **Rewrite before installing**, §4 |
| §7 rule 8: no splitting tickets to evade a gate | Conflicts with the deferral practice in use | **Rewrite before installing**, §4 |

## 4. Two rules that must be rewritten before they are installed

**Rule 1 — *"no work without an `ADMITTED` Work ID and an active lease"* is
retroactively self-invalidating.** No work package in this repository has an
admission state or a lease, because neither exists. Installed as written, all 37
become non-compliant the moment it merges, and the first PR after it would be the
only compliant one. A control that declares the entire history illegal cannot be
enforced, and an unenforceable rule in `AGENTS.md` is the defect class this
project has recorded twice — a document asserting a control that is not in force
(#407) is worse than no document.

Fix: the rule carries an **in-force-from** epoch, exactly as `L0`'s two-epoch
activation already does for gate changes. *"From governance epoch N, no work
without…"* is enforceable; the unqualified form is not.

**Rule 8 — *"no splitting tickets to evade a risk class, WIP limit or approval
gate"* — is right in intent and, as written, forbids the practice in use.** This
project defers out-of-scope findings into their own work packages constantly:
`FWK-036` deferred an 11-document prose sweep; `FWK-037` deferred the ADEC
install, the KPI corrections and the hardening clause. Every one of those splits
is exactly what rule 8 prohibits on its face.

The distinguishing property is **direction of authority, not size**: a split that
lowers the resulting class is evasion; a split that preserves or raises it is
deferral. `FWK-037` split an analysis (`G0`) out from consequences that
**escalate** (`G4`) — the class went up, not down. Rule 8 should say so
explicitly, or it will be cited against the discipline it is meant to protect.

## 5. Vocabulary — a tenth set, and four collisions

Eight verdict vocabularies are in force; ADEC proposed a ninth one message ago;
WICG's twelve admission verdicts would be the tenth. The standing rule is
**always name the set**.

| WICG token | Collides with | Resolution |
|---|---|---|
| `EXTERNAL_AUTHORITY_REQUIRED` | **ADEC's proposed option-selection set**, one message earlier | Two proposals introduced the same token into two different sets. Pick one owner or qualify both |
| `POLICY_REJECTED` | ADEC's proposed `POLICY_BLOCKED` — same concept, different word | Choose one before either is installed |
| `REPLAN_REQUIRED` | Stage-gate `REWORK_REQUIRED` in force — near-synonyms one word apart | Qualify, or reuse the token in force |
| `SUPERSEDED` | `CONDITION_REGISTER.md`'s `Superseded` state, in force | Same word, different object — name the set |
| `OPTION_BALLOT_REQUIRED` | Nothing in force; appears in WICG §6 **and** §9 for the same decision | Fine, once the set is named |

`ACCEPT_PARALLEL`, `ACCEPT_INTENTIONAL_OVERLAP`, `RETURN_EXISTING_WORK`,
`MERGE_INTO_EXISTING`, `SPLIT_DELTA_AND_LINK`, `LINK_AS_DEPENDENCY`,
`QUEUE_SERIALIZED` and `COORDINATION_PLAN_REQUIRED` collide with nothing and are
the genuinely new content of the set.

## 6. `WI-05` duplicates `K-06`, and WICG's own §11 demonstrates its thesis

`K-06` measures `merged_at − issue.created_at`. `WI-05` measures
`admitted_at − submitted_at`, a **proper sub-interval of the same span on the same
event stream**. Two lead-time metrics over one interval, with no boundary event
defined between them, is the `SC-02` duplicate-ownership shape — and `K-09`
already taught this project what an undefined denominator costs.

Of the ten `WI` metrics, measurable today: `WI-10` (unauthorized start; currently
0). Structurally unmeasurable at one agent and one project: `WI-06` resource
contention (0 by construction), `WI-09` orphan lease (no leases), `WI-07`
cross-project rework (no second project). `WI-02` duplicate precision needs a
calibration corpus that does not exist.

**This is the strongest evidence for WICG's thesis and against installing WICG as
written.** A proposal designed to catch duplication arrived containing a
duplicated KPI and a token duplicated from the previous proposal. The mechanism
that would have caught both is not a registry, a lease or a scheduler — it is a
mapping pass over what is already installed, which is what this document and
`FWK-037` are.

## 7. The lean cut — three items, with evidence

By the minimality ladder, stopping at the first step that suffices:

| # | Adopt | Cost | Evidence it is needed |
|--:|---|---|---|
| 1 | **`baseline` intake field** — `commit_sha` + policy version + governing ADR versions, recorded at admission | 1 template field | `L0` already voids ballots when the commit changes; work items have no equivalent. Rule 11 of WICG (*no stale baseline*) is unenforceable without it |
| 2 | **`write_set` intake field** — the paths the work package expects to touch, declared before coding | 1 template field | Makes the intersection check below computable at intake instead of at PR time, and makes scope creep visible as a diff against the declaration |
| 3 | **File-set intersection against every open PR**, as a gate | ~1 script; already run by hand 3 times | 3 concurrency episodes, and the check is one `comm -12`. This is the whole of WICG's conflict engine that current scale justifies |

Everything else waits. Each deferral carries a trigger, so it expires on evidence:

| Deferred | Activation trigger |
|---|---|
| Work leases, holder identity, expiry | The first **non-empty** file-set intersection between concurrent PRs, **or** a second executing identity |
| Scheduler, priority, capacity | Concurrency reaching **3**, which has never happened |
| Global Work Registry, cross-project conflict graph | A **second project** built from this framework |
| Resource taxonomy with hierarchical locks | The first deployed service, database or public API |
| Semantic duplicate detection | 30 admitted work items with recorded canonical keys — enough to calibrate, and no fewer |
| `WI` KPI family | After `WI-05`/`K-06` is deduped and an admission boundary event is defined |
| Portfolio/control-plane placement | A second project, per above |

This is the same treatment `GOVERNANCE_DEFERRED_CAPABILITIES.md` gives the
external verifier, signing and ballot council: designed, blocked, with the
unblocking action named. Deferral with a trigger is a decision; deferral without
one is drift.

## 8. What WICG gets right that nothing in SecB says

Three ideas are worth writing down even while the machinery waits:

- **`INTENTIONAL_OVERLAP` is a first-class disposition, not a violation.**
  Independent validation, red-team review and rollback drills *require* two work
  items over one artifact. A guard that forbids all overlap forbids assurance —
  and the sibling project's constitution reached the same conclusion by incident,
  requiring a handshake that declares which output is canonical.
- **An LLM may propose duplicate candidates and may never reject alone.** This is
  the same separation `L0` already draws between reasoning and authority, applied
  to intake. Worth stating before any detector is built, because it is the rule
  that keeps the detector from becoming an unaccountable gate.
- **Rule 15 — no auto-cancel on priority alone; a supersession record and a
  preservation plan are required.** SecB did this correctly once by instinct
  (PR #19, `FWK-011` → `FWK-012`) and has never written it down.

## What this document does not do

It installs nothing, amends no rule, and does not treat a measured *"not yet"* as
*"not ever"* — the triggers in §7 are the mechanism for that. It touches no file
under `AGENTS.md`, `docs/00-governance/`, `scripts/`, `config/` or `.github/`,
and no file touched by PR #69 or #71: intersection with both, verified by the
command in §1, is **empty**.

Sources cited by the operator, retained for provenance:
[PMI portfolio alignment](https://www.pmi.org/learning/library/strategically-aligning-project-portfolios-7197) ·
[NIST SP 800-128](https://csrc.nist.gov/pubs/sp/800/128/upd1/final) ·
[GitHub issue dependencies](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-issue-dependencies) ·
[Kubernetes coordinated leader election](https://kubernetes.io/docs/concepts/cluster-administration/coordinated-leader-election/) ·
[PostgreSQL explicit locking](https://www.postgresql.org/docs/current/explicit-locking.html) ·
[GitHub Actions concurrency](https://docs.github.com/en/enterprise-cloud@latest/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency) ·
[OPA decision logs](https://www.openpolicyagent.org/docs/management-decision-logs)
