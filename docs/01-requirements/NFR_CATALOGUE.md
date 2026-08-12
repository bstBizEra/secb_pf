# Non-Functional Requirement Catalogue — SecB Engineer Loop

Status: Stage 2 in progress (`SECB-WP-FWK-018`)
Source: `PRD-ENGINEER-LOOP.md` v1.0.0 §5 (value axes), §11 (metrics);
`PERFORMANCE_INDICATORS.md`

Stage 2's exit gate requires NFRs to carry **measurable targets**. Each target
below states its **basis** — observed data, a standard, or *provisional* where
no basis exists yet. A round number with no basis is a guess wearing a target's
clothing, and is marked as such.

## Correctness and safety

| ID | NFR | Target | Basis | Verification |
|---|---|---|---|---|
| `NFR-01` | Every enforcement script fails closed: absent, empty, malformed or unparseable input escalates or rejects, never passes | 100% of fail-closed paths covered by a subprocess test | Observed: 65 repo tests, every gate has explicit fail-closed cases | `pytest tests/` in CI |
| `NFR-02` | No constitutional-class change is ever downgraded to an autonomous verdict | 0 downgrades; 95% upper bound on the rate ≤10%, reached at the `A1→A2` ladder threshold | **Instrument: Wilson 95% upper bound** (`SECB-WP-FWK-040`), which replaced the statistical rule of three because `3/n` is optimistic above n≈13.7. **The figure is not restated here** — `docs/13-evidence/K09_LEDGER.md` is the authoritative append-only series and its latest row governs; as of its 2026-08-12 row, 0 downgrades in n=29, bound **11.70%**. This row previously carried its own copy of the number and drifted two instruments behind, which is why it now cites rather than copies (`SECB-WP-FWK-053`) | Per-PR verdict versus the verdict a human would give; recount appended to the ledger, never edited in place |
| `NFR-03` | Gate decisions are deterministic: identical inputs yield an identical verdict | 100% reproducible | Observed: FIT suite run twice with identical results at certification, and again against v1.5.1 | Dual-policy job compares two evaluations of the same diff |
| `NFR-04` | Sealed evidence is bit-stable | SHA-256 unchanged across every subsequent operation | Observed: `router.py` `4d1dab78…` unchanged across five work packages | Digest recomputation in review records |

## Performance

| ID | NFR | Target | Basis | Verification |
|---|---|---|---|---|
| `NFR-05` | Full CI gate set completes fast enough not to change developer behaviour | ≤ 3 minutes wall clock | Observed: runs complete in 11–13 s; a 3-minute ceiling leaves headroom for a growing test suite | Workflow run duration |
| `NFR-06` | The test suite stays fast enough to run before every push | ≤ 30 s locally | Observed: 85 tests in ~3.4 s | Local `pytest` timing |
| `NFR-07` | Classifier evaluation cost is negligible relative to the change it judges | ≤ 2 s per PR, two evaluations included | Observed: sub-second per invocation | Governance job step duration |
| `NFR-08` | Loop lead time, ticket to merge | **p50 ≤ 10 min · p90 ≤ 30 min** | **Measured 2026-08-10** (`SECB-WP-FWK-028`): n=24, median **5.5 min**, p90 **26.2 min**, max 435.9 min. The original `p50 < 1 hour` was met by an order of magnitude and therefore carried no information; the target is now set just above observed performance so a regression is visible | GitHub timestamps: `issue.created_at → pull.merged_at` |

## Auditability

| ID | NFR | Target | Basis | Verification |
|---|---|---|---|---|
| `NFR-09` | Every merged change is reconstructible from the record: ticket, gate results, verdict, SHA | 100% of merges | Observed: 18 of 18 work packages carry an evidence comment | Issue audit |
| `NFR-10` | Every factual claim in a governed document cites an artifact a third party can open | 100% of claims in gate records and review records | Standard: `AGENTS.md` §4 — every material claim links to reproducible evidence | Review of the diff at each gate |
| `NFR-11` | Evidence survives independently of the tool that produced it | Verifiable by `git` and `sha256sum` alone | Design: digests and git history, no proprietary store | Digest recomputation from a clean clone |

## Portability and operability

| ID | NFR | Target | Basis | Verification |
|---|---|---|---|---|
| `NFR-12` | Enforcement scripts depend on the Python standard library only | 0 third-party imports in `scripts/` | Observed: `json`, `os`, `re`, `sys`, `subprocess`, `datetime` only. CI installs `pytest` for tests, not for the gates | Import inspection |
| `NFR-13` | The framework runs on a personal GitHub account with no organization, no paid plan, and no branch protection | All gates functional under those constraints | Observed and forced: rulesets and protection both return `403` | Every CI run is the evidence |
| `NFR-14` | Governance configuration is machine-readable and editable without code changes | Scope, caps, tier and expiry live in `config/delegation_envelope.json` | Design decision, `SECB-WP-FWK-012` | Classifier reads the envelope at runtime; `test_missing_envelope_escalates` |
| `NFR-15` | A new project can be instantiated without modifying enforcement **logic** | **Met on the logic clause, re-measured 2026-08-11** (`SECB-WP-FWK-036`): **0 of 3** enforcement scripts now require an edit, down from 3. Total files still requiring an edit: **13**, of which 1 is the intended configuration change and 12 are prose or identity strings. The original "no framework logic" target stays **withdrawn as false** | **Measured twice**: `TRIAL-FR12-BOOTSTRAP.md` finding 1 (18 files, 2026-08-10) and the re-measurement below | Custom prefix proven **by invoking the gate**: `test_custom_prefix_from_envelope_passes`, `test_foreign_prefix_rejected_under_custom_configuration` |

`NFR-15`'s original target claimed zero `scripts/` edits with one known
exception. The bootstrap trial found **eighteen** files, and the error was in the
direction that flattered the framework. The target was withdrawn rather than
defended, and narrowed to a clause that could be met: no change to enforcement
*logic*.

### Re-measurement, 2026-08-11 (`SECB-WP-FWK-036`)

The work-package prefix moved from a regex inside `check_work_package_ref.py` to
`project.work_package_prefix` in the delegation envelope.

Both measurements use the same scope — the files a new project copies:
`AGENTS.md`, `README.md`, `docs/00-governance/`, `docs/16-templates/`,
`.github/`, `config/`, `scripts/`, `tests/`. The trial's total reproduces exactly
at its own commit `d52968b`, which is why the comparison is meaningful:

```bash
git grep -l SECB-WP d52968b -- AGENTS.md README.md docs/00-governance \
    docs/16-templates .github config scripts tests | wc -l   # 18
git grep -l SECB-WP        -- AGENTS.md README.md docs/00-governance \
    docs/16-templates .github config scripts tests | wc -l   # 20
```

| Kind | Trial, 2026-08-10 | Contains it now | **Requires an edit now** | Why |
|---|---:|---:|---:|---|
| Enforcement scripts | 3 | 3 | **0** | Each remaining `SECB-WP` in `scripts/` is a docstring citation of the work package that created the file (`SECB-WP-FWK-012`, `-011`, `-036`). Renaming a provenance citation would falsify it, so a new project leaves it alone |
| Test modules | 3 | 3 | **0** | The gate's own tests derive the prefix from the envelope the gate reads. The other two name the sealed-evidence path (pruned, not renamed) or synthetic fixture filenames the classifier never parses as prefixes |
| CI workflow | 1 | 1 | **0** | The step name and header comment no longer name a prefix. The single remaining occurrence is the sealed-evidence test path — a *different* defect, trial finding 2 |
| Config | 1 | 1 | **1** | The intended edit point. One string |
| Issue template | 1 | 1 | **1** | Irreducible: GitHub issue forms are static YAML with no interpolation, so the title format and placeholder must be literal |
| Documents naming the prefix in prose | 9 | 11 | **11** | Not addressed here, and it **grew** |
| **Total** | **18** | **20** | **13** | |

The trial's own per-kind split read *"2 test modules"* and *"10 documents"* where
the reproduction gives 3 and 9. Its **total of 18 is exact**; the internal split
was off by one in two rows. Recorded rather than quietly re-cast, because the
number this entry now compares against has to be the one that can be re-derived.

**The prediction in the previous version of this entry was wrong.** It said this
change "would reduce the eighteen to roughly six." Thirteen files still require an
edit, because the prediction counted only the code and assumed the prose surface
would hold still. It did not: two governance documents written after the trial —
`DECISION_AUTHORITY.md` and `TWO_PLANE_DECISION_MODEL.md` — each name `SECB-WP`
in prose, so the document count rose from nine to eleven while the code count
fell to zero.

That is the durable finding, and it is more useful than the number: **the
mechanical surface is now closed and the prose surface grows with the
framework.** Every governance document added from here adds instantiation cost
unless it refers to "the work-package prefix" rather than spelling `SECB-WP`.
Left open deliberately rather than fixed in this work package — a sweep of
eleven governance documents is its own change with its own review, and
`AGENTS.md` plus `docs/00-governance/` are constitutional paths.

**The logic clause is verified by invocation, not by reading.** A gate that reads
its prefix from configuration has a failure mode the hard-coded one did not: a
missing or malformed envelope. All six such paths — absent file, invalid JSON,
absent `project` block, empty prefix, non-string prefix, and a prefix containing
regex metacharacters such as `.*` that would match every title — exit `2`. A
configurable gate that fails **open** when its configuration is absent would be
worse than the hard-coded gate it replaced.

## Security

| ID | NFR | Target | Basis | Verification |
|---|---|---|---|---|
| `NFR-16` | Attacker-controlled text never reaches a shell | PR titles and bodies pass through the environment or a file, never through interpolation into `run:` | Design: `WP_TEXT` and `BUDGET_TEXT` env vars. **The diff body moved from `DIFF_TEXT` to a file read via `DIFF_PATH`** (`SECB-WP-FWK-047/048`) — not a preference but a measured limit: Linux caps a single environment string at `MAX_ARG_STRLEN` = 131,072 bytes, above which `execve` fails with `Argument list too long` and the classifier never runs, making `REJECTED` unreachable. A file has no such cap, so the change *strengthens* this NFR rather than trading it | `ci.yml` inspection; `test_env_var_takes_precedence_over_argv`; `DIFF_PATH` precedence and unreadable-path escalation covered in `tests/test_classify_authority_delta.py` |
| `NFR-17` | No credential or secret is committed | 0 occurrences | Control: `.gitignore` secret patterns; `AGENTS.md` §4 | **Manual repository scan — still not mechanized.** `scripts/check_committed_secrets.py` exists but is **unmerged, in PR #101**, so it is deliberately not cited as a basis here: naming a control that is not on `main` is how a record comes to claim a check it does not have. Update this row when #101 merges |
| `NFR-18` | The sandbox router performs no external effect | 0 network, subprocess, filesystem-write or dynamic-execution paths | Was two point-in-time static scans (certification and independent review); **now a continuous control** — `scripts/check_prohibited_calls.py` runs as Gate 6 on every PR (`SECB-WP-FWK-048`, merged `2250469`). The scan is `ast`-based and receiver-aware, because a name-only matcher reproduced `DEF-ENGLOOP-MVP-001` by flagging `set.remove()` as a filesystem write | Gate 6 in `ci.yml`; `tests/test_check_prohibited_calls.py` |

## Known NFR gaps

Recorded because an absent NFR is easier to miss than a failing one:

- **No availability or recovery NFR.** Nothing is deployed; RTO and RPO are
  meaningless before stage 11. They become requirements when stage 11 is
  entered, not now.
- **No scalability NFR beyond `NFR-07`.** The classifier's route search is
  combinatorial in eligible skills (review finding `F5`); a bound is needed
  before a large registry exists, and that is a stage-3 concern.
- **No cost NFR.** K-10's instrumentation is adopted but not recording, so any
  target would be unmeasurable. Deliberately absent rather than provisional.
- **One outlier is not explained.** The 435.9-minute maximum belongs to the
  Specification Conflict Protocol work package, which waited on an operator
  decision. Lead time as currently defined measures the whole wall clock
  including human wait, so it conflates agent throughput with decision latency.
  Splitting the two is a candidate refinement, recorded rather than done.
