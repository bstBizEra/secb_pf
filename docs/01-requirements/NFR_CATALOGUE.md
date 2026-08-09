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
| `NFR-02` | No constitutional-class change is ever downgraded to an autonomous verdict | 0 downgrades; 95% upper bound on the rate ≤10% | Rule of three at n=30, the `A1→A2` ladder threshold. Currently ≤16.7% at n=18 | Per-PR verdict versus the verdict a human would give |
| `NFR-03` | Gate decisions are deterministic: identical inputs yield an identical verdict | 100% reproducible | Observed: FIT suite run twice with identical results at certification, and again against v1.5.1 | Dual-policy job compares two evaluations of the same diff |
| `NFR-04` | Sealed evidence is bit-stable | SHA-256 unchanged across every subsequent operation | Observed: `router.py` `4d1dab78…` unchanged across five work packages | Digest recomputation in review records |

## Performance

| ID | NFR | Target | Basis | Verification |
|---|---|---|---|---|
| `NFR-05` | Full CI gate set completes fast enough not to change developer behaviour | ≤ 3 minutes wall clock | Observed: runs complete in 11–13 s; a 3-minute ceiling leaves headroom for a growing test suite | Workflow run duration |
| `NFR-06` | The test suite stays fast enough to run before every push | ≤ 30 s locally | Observed: 85 tests in ~3.4 s | Local `pytest` timing |
| `NFR-07` | Classifier evaluation cost is negligible relative to the change it judges | ≤ 2 s per PR, two evaluations included | Observed: sub-second per invocation | Governance job step duration |
| `NFR-08` | Loop lead time, ticket to merge | p50 < 1 hour | **Provisional** — K-06 has a formula but has never been computed; no basis until it is | GitHub timestamps |

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
| `NFR-15` | A new project can be instantiated without modifying framework logic | 0 edits to `scripts/` required — configuration and content only | Design: `NEW_PROJECT_BOOTSTRAP.md` classification. **Unverified until project #2** — one known exception: the work-package ID prefix is currently hard-coded in `check_work_package_ref.py` | Verified by instantiating |

`NFR-15` records a real defect rather than an aspiration: the authority gate's
regex hard-codes `SECB-WP-`, so a new project must edit a script after all. The
bootstrap runbook says so, and closing it is a candidate requirement for stage 3
(make the prefix configuration, not code).

## Security

| ID | NFR | Target | Basis | Verification |
|---|---|---|---|---|
| `NFR-16` | Attacker-controlled text never reaches a shell | PR titles and bodies pass through the environment only | Design: `WP_TEXT`, `BUDGET_TEXT`, `DIFF_TEXT` env vars; no interpolation into `run:` | `ci.yml` inspection; `test_env_var_takes_precedence_over_argv` |
| `NFR-17` | No credential or secret is committed | 0 occurrences | Control: `.gitignore` secret patterns; `AGENTS.md` §4 | Repository scan |
| `NFR-18` | The sandbox router performs no external effect | 0 network, subprocess, filesystem-write or dynamic-execution paths | Verified twice by static scan, at certification and independent review | Prohibited-call scan |

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
