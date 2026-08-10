# Runbook — Gate Operations

Status: Written 2026-08-10 from observed incidents (`SECB-WP-FWK-028`)
Audience: whoever is on the hook when a gate behaves unexpectedly
Why it exists: the four enforcement gates are product surface that every merge
depends on, and they had **no runbook, no monitoring, no alerting and no
recovery procedure** — the one real documentation gap that measurement found
(`ANALYSIS-METRIC-001.md`).

Every failure mode below is either **observed**, with the run or commit that
produced it, or explicitly marked **anticipated**. A runbook that presents
imagination as experience is the defect this framework keeps finding.

## Monitoring, given that there is none

No monitoring service exists and none is justified at six surface items. What
exists instead — use these:

| Question | Command |
|---|---|
| Did every gate pass on a commit? | `gh api repos/bstBizEra/secb_pf/commits/<sha>/check-runs --jq '.check_runs[] \| "\(.name): \(.conclusion)"'` |
| What did the governance job decide? | Read the run's **job summary**, or `gh api .../actions/jobs/<id>/logs \| grep -E "VERDICT\|DUAL POLICY"` |
| Is the run itself green? | `gh api .../actions/runs/<id> --jq .conclusion` |
| Autonomy rate | Count announced autonomous merges against squash-merged PRs since `035b66d` |
| Classifier confidence (K-09) | Downgrades observed ÷ decisions; 95% bound is `3/n` while zero |

**Known API quirk:** a check-run can report `status: in_progress` with
`conclusion: success` for a short window. The authoritative read is the run's
`/jobs` endpoint, not the commit's check-runs. Observed repeatedly this session.

---

## Gate 1 — Authority · `scripts/check_work_package_ref.py`

**Enforces** `AGENTS.md` §4, *No Ticket, No Work*: the PR title or body must cite
a `SECB-WP-*` ID.

**Exit codes** `0` reference found · `2` missing, or input empty/absent
(fail-closed).

| Failure mode | Recovery |
|---|---|
| **Observed** — PR body edited to add the reference, gate still red. Workflow runs snapshot the PR title and body **at event time**, so a metadata edit does not re-evaluate. Seen on PR #23 and on the trial's PR #1 | Push an empty commit: `git commit --allow-empty -m "test: retrigger" && git push`. This issues a `synchronize` event carrying the updated metadata. Recorded as `KN-005` |
| **Observed** — a new project's gate rejects every PR because the regex still matches `SECB-WP-`. Seen in the bootstrap trial | Rename the prefix. It appears in **18 files**, not one — `grep -rl SECB-WP . \| xargs sed -i 's/SECB-WP/<PREFIX>-WP/g'` (`TRIAL-FR12-BOOTSTRAP.md` finding 1) |
| **Anticipated** — a title containing the literal string in prose passes without a real ticket | The regex requires the `-<AREA>-<NNN>` segments; a bare `SECB-WP-` does not match. Covered by `test_fail_on_lookalike_prefix_without_id` |

---

## Gate 5 — Test · `.github/workflows/ci.yml`

**Enforces** that the shipped surface is exercised: FIT-101–120 plus the repo
suite, on every push to `main` and every PR.

**Exit codes** pytest's own · `4` means *no tests collected*, which is a path
problem rather than a test failure.

| Failure mode | Recovery |
|---|---|
| **Observed** — `ERROR: file or directory not found … Sandbox Evidence/test_router.py`, `no tests ran`, exit 4. The step hard-codes the sealed-evidence path; in any repository that does not contain it, the gate is red before any product code exists. Seen in the bootstrap trial | Point the step at `tests/` only. In SecB the path is valid and must stay; in a copy it must be removed — the runbook's copy classification now says so |
| **Observed** — pytest writes `__pycache__/` and `.pytest_cache/` into the sealed evidence directory, whose digests must stay stable. Seen twice this session, both times by the executor | Always run with `-p no:cacheprovider` and `PYTHONDONTWRITEBYTECODE=1`. Both are set in CI. If artifacts appear, delete them and **re-verify the digests** with `sha256sum` before assuming no harm |
| **Anticipated** — a test depends on network or clock and fails intermittently | No such test exists; the router is verified side-effect-free by static scan. Treat any intermittent failure as a real defect, not as flake, until proven otherwise |

---

## Budget circuit breaker · `scripts/check_budget.py`

**Enforces** `AGENTS.md` §6/§7: the PR body declares exactly one
`BUDGET: max_files=N max_lines=N` and the diff stays inside it.

**Exit codes** `0` within budget · `2` missing, malformed, **duplicated**, or
exceeded.

| Failure mode | Recovery |
|---|---|
| **Observed** — `BUDGET GATE FAIL: diff exceeds the declared budget`. Seen three times: PR #23 (766/320), PR #43-era 1322/1300, and the trial's deliberate 2/1 | **Renegotiate on the ticket with the cause, then update the PR body, then push an empty commit.** Never silently raise the number in the PR body — the breaker's own message says to renegotiate on the ticket, and the audit trail is the point |
| **Observed** — budget amended on the ticket and in the PR body, gate still red | Same event-time snapshot problem as Gate 1. Empty commit (`KN-005`) |
| **Anticipated** — a binary-heavy PR passes a line cap while adding large files | Binary files count toward `max_files` with zero lines, so the file cap bounds them. Covered by `test_binary_file_counts_toward_files_not_lines` |

---

## Governance verdict · `classify_authority_delta.py` + `check_dual_policy.py`

**Enforces** the `L0` constitution: classifies the authority delta `G0`–`G5` and
evaluates the change under both the incumbent and the proposed policy.

**Exit codes** classifier `0` auto-approved · `2` escalate · `3` rejected.
Dual policy the same. **The CI job always exits `0`** — the verdict goes to the
job summary, because `AGENT_BALLOT_REQUIRED` and `CONSTITUTIONAL_REQUIRED` are
expected answers, not build failures.

| Failure mode | Recovery |
|---|---|
| **Observed** — the job reported check conclusion `failure` while its documentation claimed it stayed green. `continue-on-error` keeps the *run* green but still fails the job's own check. Seen on PR #19's first run | Capture the exit code in the step, write the verdict to `$GITHUB_STEP_SUMMARY`, `exit 0`. Already fixed; do not reintroduce `continue-on-error` as the mechanism |
| **Observed** — `VERDICT: REJECTED — prohibited: removes an enforcement step from CI` on a PR that removed nothing. The G5 scan matched its own test fixture, which quoted the marker on an **added** line. Seen on the Genesis PR, run of `3548749` | Fixed: only lines beginning with `-` (excluding `---` headers) count as removals. If `REJECTED` appears unexpectedly, **check whether the diff merely quotes a marker** before assuming a real prohibited change |
| **Observed** — `DUAL POLICY: ESCALATE — base logic not recoverable`. Correct on a first installation, where no prior policy exists to compare | No action. This is the intended behaviour for genesis and bootstrap changes |
| **Observed** — local self-check passes while CI escalates or rejects. The local run omitted `DIFF_TEXT`, so the G5 body scan never executed | **Verify with the same inputs CI uses**: pass both the numstat *and* `DIFF_TEXT="$(git diff --cached origin/main)"` |
| **Anticipated** — divergence between base and head verdicts in a real PR | It cannot occur: touching the classifier or envelope is `G4`, which dominates, so both policies agree. Divergence is provable only in unit tests. Seeing *"both policies agree that this escalates"* is the healthy output (`TRIAL-FR12-BOOTSTRAP.md` finding 5) |

---

## Scheduled operational event — envelope expiry, **2026-11-08**

`config/delegation_envelope.json` sets `expires_at: 2026-11-08`. On that date the
classifier's expiry check fires and **every classification returns
`CONSTITUTIONAL_REQUIRED`**, whatever the change. Autonomous merges stop
entirely.

This is designed behaviour — delegation lapses rather than persisting
unexamined — and it is **not** a failure. But nothing else announces it, so:

| When | Action |
|---|---|
| Before 2026-11-08 | A work package reviews the autonomous-merge record — count, verdicts, any incident — and proposes renewal with an explicit new expiry. Renewal is `G4`/`D4`: the operator's |
| On the date, if not renewed | Expect `VERDICT: CONSTITUTIONAL_REQUIRED — envelope expired 2026-11-08`. Nothing is broken. Every merge needs the operator until renewed |
| Never do | Extend the date to unblock a specific pull request. That is raising a ceiling for convenience, which the `L0` prohibited-actions list refuses |

The same review closes the accepted-risk record on single-identity SoD, which
carries the same date deliberately.

## When a gate is wrong

If a gate blocks a change that should pass, the fix is **never** to weaken the
gate inside the change it is blocking. Options, in order:

1. Split the work package so it fits the envelope.
2. Renegotiate the budget on the ticket, with the cause recorded.
3. Escalate: an `AGENT_BALLOT_REQUIRED` or `CONSTITUTIONAL_REQUIRED` verdict is
   the system working, not an obstacle.
4. If the gate is genuinely defective, fix it in **its own** work package — which
   the classifier will escalate, because `scripts/` is `G4`. That escalation is
   the control that makes the other three trustworthy.
