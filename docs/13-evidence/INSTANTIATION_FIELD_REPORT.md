# Field report — what it actually cost to instantiate this framework

**Work package:** `SECB-WP-FWK-052` · **Issue:** #104 · **Recorded:** 2026-08-12
**Status:** measurement · **`n`:** 2 instantiations, 1 retrofit — every number
below is from the retrofit, so each magnitude is a single sample
**Method:** reproducible from the commands in §2

---

## 0. Why this document exists, and what it is not allowed to be

This framework's stated purpose is to be instantiated. Until now the only
recorded instantiation was a **greenfield trial** — an empty repository, written
up in `docs/15-runbooks/NEW_PROJECT_BOOTSTRAP.md`, and the source of that
runbook's `n=1` and its refusal to ship a scaffolding generator.

A second one happened on 2026-08-10 and differs in kind: a **retrofit into a
live repository** with its own history, its own phase prefixes and a different
test runner. That difference is the whole value of it — a greenfield trial
*cannot* surface an identifier collision, because an empty repository has
nothing to collide with. Everything in §3 comes from the retrofit and could not
have come from the trial.

**The observed project is example data, not an authority.** It is cited as an
*observation of what instantiation costs* — never as precedent, never as
justification for a decision here. `SECB-WP-FWK-051` removed three citations
that crossed that line, and the distinction it settled is the one this report
runs on: **naming what you observed is provenance and is required; treating it as
ratified precedent is an appeal to a non-authority.** Every finding below is a
measurement from a tree, with the command that takes it.

**`n=1`.** A defect is a defect once, so findings 2 and 3 stand at this `n` — but
every *magnitude* here is a single sample, and none of it is a law.

## 1. The three findings, in one paragraph each

**1 — "Reusable as-is" is falsified by the field.** The runbook classifies the
four enforcement scripts as transferring unedited. All four were edited: **130
lines**, 45 of them (34%) mentioning a governance ladder token that had to be
renamed. `NFR-15` (`SECB-WP-FWK-036`) made the work-package prefix
configuration, and the field shows that was the *smallest* part — `G0–G5`,
`L0–L3` and `A0–A4` are still hard-coded in code and prose, and the retrofit
renamed **all four ladders** because the host repository already used those
letters. Exactly the collision `config/identifier_taxonomy.json`
(`SECB-WP-FWK-041`) predicted and declared it could not measure. Now measured.

**2 — a control drifted 215 lines upstream and the downstream cannot learn
that.** Two of the four controls changed since the port
(`classify_authority_delta.py` +123, `check_work_package_ref.py` +92), two did
not. **No mechanism existed, here or in the runbook, by which an instantiated
project could compute whether a control it copied had been fixed since** —
staleness was not unmanaged, it was inexpressible. Closed by
`config/control_surface.json`, for `verbatim`-class controls.

**3 — the drift includes a severity defect, live downstream.**
`SECB-WP-FWK-047/048` moved the diff body to a file (`DIFF_PATH`) because the
environment truncates it. The instantiation carries the pre-fix shape. §4 states
the consequence narrowly, because the obvious overstatement is wrong.

## 2. Method — how to reproduce every number

The naive comparison is worthless: diffing the downstream copy against this
repository's *current* tree conflates **downstream renames** with **upstream
drift since the port** and reports their sum as one quantity. My first pass did
that and produced numbers I discarded. Both are recovered by pinning the commit
the copy was taken from (`035b66d`, the genesis commit that shipped the
classifier and the dual-policy check):

```
downstream edit  =  diff( SecB@035b66d ,  downstream copy today )
upstream drift   =  diff( SecB@035b66d ,  SecB today            )
```

Attribution of a downstream edit to the identifier problem is by **token
presence** — a changed line counts as ladder-attributable if it matches
`\b(AD[0-5]|GL-[0-3]|AT[0-4]|G[0-5]|L[0-3]|A[0-4]|BOPEN|bOPEN|SECB|SecB)\b`.

> **A rejected method, recorded because it looked convincing.** I first tried
> normalising the downstream copy by substituting its tokens back
> (`AD`→`G`, `GL-`→`L`, `AT`→`A`, …) and diffing the normalised text, expecting a
> small residue. The residue came out *larger* than the raw diff on three of the
> four files — because plain substring substitution also rewrites unrelated
> words. The transform was unsound, so the numbers were meaningless and are not
> in this report. Token presence is weaker but it is honest: it counts lines
> that *mention* a renamed token without claiming the rename was the only reason
> the line changed.

## 3. The measurements

### 3.1 Downstream edit cost — controls the runbook says transfer unedited

| Control | lines changed downstream | ladder-attributable |
| :--- | ---: | ---: |
| `classify_authority_delta.py` | 63 | 31 (49%) |
| `check_work_package_ref.py` | 32 | 8 (25%) |
| `check_budget.py` | 24 | 2 (8%) |
| `check_dual_policy.py` | 11 | 4 (36%) |
| **total** | **130** | **45 (34%)** |

Read the un-attributed 85 lines honestly: **unattributed edit is not the same as
no defect — it is an unmeasured one.** `check_budget.py` is the sharpest case,
24 lines edited with only 2 mentioning a ladder token. Why the other 22 changed
is not established here and is not investigated in this work package.

### 3.2 Upstream drift since the port — invisible to the downstream

| Control | drift since `035b66d` | shipped in |
| :--- | ---: | :--- |
| `classify_authority_delta.py` | 123 lines | `2250469` (`FWK-047`/`048`) |
| `check_work_package_ref.py` | 92 lines | `728d45d` (`FWK-036`) |
| `check_budget.py` | 0 | — |
| `check_dual_policy.py` | 0 | — |

Two of four controls drifted; two are still byte-current after two days. The
framework is not churning uniformly — which is what makes per-control digests
worth having rather than a single version stamp on the whole surface.

## 4. Finding 3 in full — and the overstatement it invites

The downstream's gate step:

```bash
git diff "$BASE_SHA...$HEAD_SHA" > /tmp/pr.diff
single=$(DIFF_TEXT="$(cat /tmp/pr.diff)" \
  python scripts/classify_authority_delta.py < /tmp/pr.numstat 2>&1)
```

Linux caps a single environment string at `MAX_ARG_STRLEN` = **131,072 bytes**.
Verified on this machine, on the exact shape above:

```
$ DIFF_TEXT="$(cat 140000-byte-file)" python3 -c '...'
Argument list too long
exit 126
```

**The classifier does not run at all.** Not on truncated input — it does not run.

The downstream's summary step tests only for exit `0` and exit `3`, so `126`
falls to its `else` branch and renders as:

> **Escalation required.** Normal for governance, constitutional, oversized, or
> judgement-altering changes.

**What this is not.** Not a fail-open into auto-merge: merges at that tier are
operator-only there, so nothing self-merges through this hole. I checked before
writing the finding, and the dramatic version — "an oversized prohibited change
could auto-merge" — is false.

**What it is.** The most severe verdict in the ladder becomes unreachable, and
its absence is rendered to the operator as routine business. A change carrying a
prohibited signature *and* exceeding 131 KB reads exactly like an ordinary
governance escalation, so an operator reasonably believes a classification
happened and escalated on the merits. None happened, and `REJECTED` — the one
verdict meaning *withdraw this* — cannot be produced. Two facts make it
survivable rather than serious: the job always exits 0 by design, and the human
gate sits downstream. **Both are compensating controls, not a reason the defect
is acceptable** — this repository's own `DIFF_PATH` fix, plus the
`INVALID GATE OUTPUT` branch rejecting any exit code outside `{0,2,3}`, exists
because that same reasoning was rejected here.

**Whose problem it is.** Not this repository's — the observed project is a worked
example and its own operator decides. **What was SecB's problem is that the fix
was unknowable downstream**, which is what `SECB-WP-FWK-052` closes. Reported,
not reached into.

## 5. Dispositions

| # | Finding | Disposition in this work package |
| :--- | :--- | :--- |
| 1 | Four "Reusable as-is" controls were all edited; ladder tokens unportable | Runbook classification corrected; each control's measured edit cost recorded in `config/control_surface.json` as `field_observation`. **The ladder tokens are NOT made configurable here** — that is a separate change to enforcement-path code and needs its own work package and its own plan. Deferred, named, not silently dropped. |
| 2 | Staleness not expressible | **Closed** — `config/control_surface.json` + `tests/test_control_surface.py`, for `verbatim`-class controls. |
| 3 | Live severity defect downstream | **Reported, not fixed.** Out of scope by ownership; it is the evidence for finding 2, not a task here. |
| 4 | Runbook assumes greenfield | Retrofit-vs-greenfield distinction added to the runbook, with the CI-environment preflight the retrofit paid for at first contact. |
| 5 | Branch protection unavailable — second occurrence | Recorded here as a second independent observation. The accepted-risk record in `docs/00-governance/SINGLE_IDENTITY_SOD_ACCEPTED_RISK.md` is **not amended by this work package**; changing a governance record on the strength of one more sample is the kind of edit that should be its own decision. |

### Deliberately not done

- **Ladder tokens stay hard-coded.** Making them configurable touches
  `classify_authority_delta.py` — constitutional path, enforcement logic, where a
  mistake is a wrong authority verdict rather than a wrong message. Plan first.
- **No propagation tooling.** The manifest makes staleness *computable*; a human
  does the comparison. Nothing reaches into a downstream or checks what it runs.
- **No generator, still.** `n` is 2, and the trigger says *when the third project
  repeats the second*. Two instantiations differing in kind argue for keeping the
  refusal, not relaxing it.

## 6. What would falsify this

- A third instantiation paying a *different* edit cost ⇒ finding 1's magnitude is
  project-specific, not a property of this framework.
- A **greenfield** instantiation needing ladder renames ⇒ the collision is not a
  retrofit artifact, which *raises* finding 1's priority, since greenfield is the
  case the runbook is actually written for.
- Any instantiation copying a control unedited ⇒ first evidence that `verbatim`
  is achievable, making digest comparison a clean signal instead of a mixed one.
