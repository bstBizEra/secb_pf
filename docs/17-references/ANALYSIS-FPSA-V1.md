# Analysis — FPSA v1.0 against the framework's measured surface

Status: Analysis complete · **nothing installed by this document** · `SECB-WP-FWK-039` (issue #74)
Occasion: the operator supplied *"WICG-FPSA v1.0 — Framework Protection,
Self-Audit & Controlled Evolution"* on 2026-08-11 — five protection layers,
sixteen `FP` controls, thirteen self-audit verdicts, twelve `FP-K` KPIs, eight
audit modes, fifteen golden negative tests, a Framework Contract Registry and a
five-phase roadmap — to stop the framework expanding without proof of need.
Companions: `ANALYSIS-ADEC-V1.md` (`FWK-037`) · `ANALYSIS-WICG-V1.md` (`FWK-038`)

## Verdict up front

**FPSA's diagnosis is correct, confirmed by measurement — and FPSA as written is
an instance of the thing it diagnoses.** Both halves of that sentence are
measured below, not asserted.

| | |
|---|---|
| **Confirmed by measurement** — real, quantified gaps FPSA names | 3 |
| **Adopt now** — closes a measured gap at near-zero cost | 4 items |
| **Defer with a named activation trigger** | 8 items |
| **Already in force** | 7 items |
| **Contradicts something** — including two internal contradictions | 4 |
| **Namespace collisions** — one against policy in force, one internal | 2 new, 2 pre-existing |

## 1. FPSA is right about the surface, and the number is stark

```bash
git log --diff-filter=A --name-only --format="" origin/main | grep -c .   # 164
git log --diff-filter=D --name-only --format="" origin/main | grep -c .   #   5
git ls-files | wc -l                                                     # 159
git ls-files 'docs/*.md' | wc -l                                         # 109
```

```text
files ever added        164
files ever deleted        5
retirement ratio         3%
documents               109  of 159 tracked files
```

`FP-K02` (net surface change, added minus retired) is not a hypothetical metric
here. **This framework has retired 3% of what it created**, and two-thirds of it
is prose. `FP-15` (orphan prevention) also lands:

```bash
git grep -l "secb_router" -- . | grep -v "^src/secb_router" | grep -v test
# → AGENTS.md, RTM.md, TRIAL-FR12-BOOTSTRAP.md, NEW_PROJECT_BOOTSTRAP.md, ANALYSIS-METRIC-001.md
```

Every reference is documentation. **SecB's only production code — 669 SLOC, the
certified MVP router — has no runtime consumer.** It is not dead: it is a
certified proof artifact. But nothing records whether it should be *promoted* or
*retired*, which is exactly the decision `FP-14`'s retirement contract would have
forced at the time it was built. Three confirmed findings, then:

| FPSA claim | Measured |
|---|---|
| `FP-K02` net surface grows unchecked | **164 added / 5 deleted** |
| `FP-15` components accumulate without consumers | **1 confirmed** — `src/secb_router/` |
| `FP-09` complete mediation — no direct path may bypass enforcement | **A direct path exists.** `main` is not branch-protected: the API returns `403 Upgrade to GitHub Pro`, recorded in `AGENTS.md` at #407. A direct push bypasses every gate |

`FP-09` deserves particular credit: it independently names the hole this
repository documented by correcting its own constitution. It is also
**unsatisfiable here** — protection cannot be enabled on this plan — so the
compensating control remains the human merge rule, and FPSA should record that
rather than assert mediation it cannot have.

## 2. And FPSA is an instance of the disease it describes

FPSA §1 lists *"Policy expansion — so many rules they conflict or cannot be
maintained"* and *"Evidence expansion — many reports and KPIs with no user or
decision linkage"* as risks to prevent. Measured against the three proposals
supplied in the last three messages:

| Surface | In force | After ADEC + WICG + FPSA |
|---|---:|---:|
| Verdict vocabularies | 8 | **11** |
| KPI definitions | 11 | **~41** (`K` splits + `WI-01…10` + `FP-K01…K12`) |
| Named controls / prohibitions | 5 `L0` prohibitions + 10 `GATE` + 8 `SC` | **+15 WICG prohibitions + 16 `FP` controls** |
| Deployed surfaces the KPIs describe | 0 | 0 |
| Executing agents | 1 | 1 |

`K-10` has been an adopted recording contract since `FWK-016` and has **recorded
nothing**. Adding twelve `FP-K` metrics to a framework whose eleventh KPI has
never produced a value is the evidence-expansion risk FPSA names, realized by
FPSA.

This is not a reason to reject it. It is the reason to install the parts that
close a measured gap and defer the parts that instrument a surface that does not
exist yet — which is FPSA's own `GAP`/`REUSE`/`DELTA` proof applied to FPSA.

## 3. Namespace collisions — the third in three messages

**`E0`–`E4` is taken.** `DECISION_AUTHORITY.md:91-105` defines it as **evidence
levels**: `E0` agent assertion … `E4` canary or production telemetry. FPSA §5
reuses `E0`–`E4` for **expansion classes**: `E0 NO_EXPANSION` … `E4
CONSTITUTIONAL`.

The consequence is worse than ambiguity. Evidence-`E4` is the level SecB has
**zero** of — it is the recorded reason production is unreachable. Expansion-`E4`
is the *highest authority class*, and `E4_EXTERNAL_AUTHORITY_REQUIRED` is a
verdict FPSA expects to issue routinely. So `"E4"` would simultaneously mean *the
strictest authority tier* and *evidence we do not possess*, and sentences like
*"`E3` requires independent assurance"* become unreadable — evidence-`E3` and
expansion-`E3` both say that, about different objects.

**`P1` collides with itself, inside FPSA.** §3 defines `P1 Baseline Protection`
through `P5 Recertification`; §16 defines `P0 Canonical Foundation` through `P4
Adaptive Governance`. `P1`, `P2`, `P3` and `P4` each name two different things in
one document.

**Two collisions already exist in force**, which is what makes this structural
rather than a slip:

| Prefix | Meaning A | Meaning B |
|---|---|---|
| `D` | `D0`–`D4` decision classes (`DECISION_AUTHORITY.md`) | `D1`–`D5` deferred capabilities (`GOVERNANCE_DEFERRED_CAPABILITIES.md`) |
| `C` | `C0`–`C5` conflict impact ladder (`SPECIFICATION_CONFLICT_PROTOCOL.md`) | `C-1`–`C-4` carried conditions (`CONDITION_REGISTER.md`) |
| `E` | `E0`–`E4` evidence levels | `E0`–`E4` expansion classes — **proposed** |

The `C` pair is distinguished **only by a hyphen**, and both appear in authority
contexts: `FWK-037` wrote *"impact `C4`"* and *"`C-4` governance owner"* in the
same work package. That is a live ambiguity this analysis has already been
producing.

**The cheapest fix is a rule, not a tool:** a single-letter prefix, once bound to
a meaning, is never rebound; new ladders take a distinct prefix (`X0`–`X4` for
expansion classes, for instance) and the `C`/`D` pairs are qualified at every use.
This is the same discipline as *always name the set* for verdict tokens, applied
to identifier ladders — and it is a precondition for installing any of FPSA,
because the `E` collision would otherwise enter policy.

## 4. Component map

| FPSA element | Status | Verdict |
|---|---|---|
| Negative tests required for any control claiming to block (`FP-16`, `FP-K07`) | `KN-001` in force — *"a gate counts only once proven to fail on a real PR"*; `K-05`'s guardrail says the same | Already in force |
| Fail closed on unverifiable baseline, evidence or identity (`FP-10`) | `AGENTS.md` §4; every gate exits 2 | Already in force |
| Constitutional isolation of authority, quorum, bypass, classifier (`FP-07`) | `L0` change classes: all are `G4`; `scripts/` and `config/` are `constitutional_paths` | Already in force |
| Framework may not approve its own authority expansion (§17 rule 9) | `L0` absolute ceilings; the dual-policy rule enforces it mechanically | Already in force |
| Expiring exceptions with owner and expiry (`FP-13`) | `SINGLE_IDENTITY_SOD_ACCEPTED_RISK.md` review 2026-11-08; envelope `expires_at` | Already in force |
| Append-only decision history (§17 rule 11) | `L0` — evidence is append-only; `K09_LEDGER.md` corrections table | Already in force |
| Independent proposer / auditor / approver at `E2`+ (`FP-08`) | `ballot.schema.json` `signer_identity`; `SINGLE_IDENTITY_SOD_ACCEPTED_RISK.md` records it as **accepted risk**, not satisfied | Already specified, **structurally blocked** |
| Reuse before adding (`FP-04`) · minimum required delta (§6) | Practised: ADEC's 24 elements became 5 new + 6 extensions, 11 discarded | **New as a written rule** |
| `FP-K02` net surface change | Not measured before this document | **Adopt — one command** |
| `FP-14` retirement contract on new components | No counterpart. Nothing has ever been retired by decision | **Adopt — one field** |
| Golden negative tests, 15 cases (§15) | The classifier has `G5` prohibited-action tests covering roughly cases 6, 7, 8 and 12 | **Adopt as a test backlog** — the remaining ~11 are a real gap list |
| Monotonic hardening fast path (§9) | ADEC proposed it; FPSA **improves** it by adding `classifier_new == classifier_old`, forbidding the candidate from redefining *monotonic*, and requiring rollback if hardening blocks legitimate work | **Extends ADEC's version — take FPSA's** |
| Expansion Vector `[S,A,I,D,O,R]` with `class = max(...)` | `DECISION_AUTHORITY.md:39-42` already takes the strictest of three axes (`D`, `G`, `R`) | **Extends** — same rule, more axes |
| Framework Contract Registry, Expansion Manifest schema | No counterpart | **Defer** |
| Five protection layers `P1`–`P5` as distinct machinery | No counterpart | **Defer** |
| Execution-envelope runtime enforcement, drift detection, lease suspension | No counterpart; and `FWK-038` measured **0 contention in 36 PRs** | **Defer** |
| OSCAL control catalogue, signed OPA bundles, SLSA provenance | `GOVERNANCE_DEFERRED_CAPABILITIES.md` §D2 already covers signing and transparency logs, blocked | **Defer** — already deferred once |
| `FP-K01`–`FP-K12` KPI family | 11 KPIs in force; one has never recorded a value | **Defer** — §2 |
| Eight self-audit modes | No counterpart | **Defer** |
| Thirteen self-audit verdicts | 8 vocabularies in force, +2 proposed | **11th set — resolve the `E` collision first** |
| `FP-05 No Ticket Fragmentation` | Contradicts §6's own delta rule | **Contradicts — §5** |
| §17 rule 1: every mutation from an `ADMITTED` work item | Inherits WICG rule 1's retroactivity defect | **Rewrite — §5** |

## 5. Four contradictions to settle before installation

**(a) FPSA contradicts itself on splitting.** `FP-05` requires related changes to
be *combined* to prevent evading a class or budget. §6 requires `OPTIONAL_DELTA`
to be *removed or made a separate work item*. One control forbids splitting; the
other mandates it.

The resolution is the test proposed for WICG rule 8 one message ago, and it works
for both: **direction of authority, not size.** A split that lowers the resulting
class is evasion (`FP-05` applies); a split that preserves or raises it is
deferral (§6 applies). `FWK-037` split an analysis at `G0` from consequences that
escalate to `G4` — the class went up. Writing that test once settles `FP-05`, §6
and WICG rule 8 together.

**(b) §17 rule 1 is retroactively self-invalidating**, exactly as WICG rule 1 is:
no work package here has an admission state, so all 38 become non-compliant on
merge. Fix is the same — an **in-force-from epoch**, as `L0`'s two-epoch
activation already provides.

**(c) `FP-08` requires independent auditor identity at `E2`+, which cannot be met
here.** `SINGLE_IDENTITY_SOD_ACCEPTED_RISK.md` records single-identity separation
of duties as an accepted risk for stages 1–8 with seven compensating controls.
Installing `FP-08` as a hard control would make every `E2`+ change inadmissible —
which is either an accidental freeze or an argument for provisioning identities.
It should say which.

**(d) `FP-09` complete mediation is unsatisfiable** on this plan (§1). State the
compensating control instead of asserting the property.

## 6. The lean cut — four items, each closing a measured gap

| # | Adopt | Cost | Measured gap it closes |
|--:|---|---|---|
| 1 | **Prefix-uniqueness rule**: a single-letter identifier prefix is never rebound; FPSA's expansion classes take a free prefix; `C`/`D` uses are qualified | 1 paragraph | 2 collisions in force, 2 more proposed (§3) |
| 2 | **`FP-K02` net surface change**, added minus retired, per work package | 1 command | 164 added / 5 deleted, never measured (§1) |
| 3 | **Retirement trigger field** for any new component, policy or integration — owner, review date, removal condition | 1 template field | 1 confirmed orphan; nothing ever retired by decision (§1) |
| 4 | **The 15 golden negative tests as a recorded test backlog**, with the ~4 already covered marked | 1 document section | `KN-001` already says a gate counts only when proven to fail; this is that rule's missing checklist |

Item 4 is the highest-value one, because it is the only part of FPSA that
*hardens what already exists* rather than adding a layer. Items 1–3 cost a
paragraph, a command and a field.

Eight items deferred **with triggers**, so each expires on evidence:

| Deferred | Activation trigger |
|---|---|
| `FP-08` independent audit as a hard control | A second executing identity exists |
| Framework Contract Registry, Expansion Manifest | The framework is instantiated into a **second project** |
| Five protection layers as distinct machinery | Two of the four lean items prove insufficient — i.e. a framework change escapes them |
| Execution envelope, drift detection, lease suspension | The first non-empty file-set intersection between concurrent PRs (same trigger as `FWK-038`) |
| OSCAL, signed bundles, SLSA provenance | Whatever unblocks `GOVERNANCE_DEFERRED_CAPABILITIES.md` §D2 — they are the same capability |
| `FP-K` KPI family | `K-10` records its first value. A framework that cannot feed one KPI does not need twelve |
| Eight self-audit modes | `PERIODIC_STRUCTURAL` alone, run once by hand, finds nothing new |
| Monotonic hardening fast path (FPSA's improved version) | The root authorization ADEC's §3 requires — unchanged prerequisite |

## 7. The measurement that outranks all of this

While three control-plane specifications arrived, three pull requests sat
unmerged:

```text
#69  opened 05:41Z   waiting 102 min
#71  opened 05:58Z   waiting  85 min
#73  opened 07:09Z   waiting  14 min
K-06 median, ticket to merge, n=24            5.5 min
```

**#69 has waited 18× the historical median.** `FWK-038` measured that concurrency
in this repository is a function of merge latency rather than of agent count —
peak concurrency of 2 has only ever arisen from blockage. The framework's
measured bottleneck today is not a missing control layer; it is that finished,
green, verdict-carrying work is not landing.

Recorded because FPSA's own `GAP` proof demands it: *"which requirement, incident,
control failure or KPI proves the gap exists?"* For the four lean items, the
answer is in §1. For the five protection layers, the answer is currently the
`K-06` row above — and it points at merging, not at building.

## What this document does not do

It installs nothing and rejects nothing. It does not treat a measured *"not yet"*
as *"not ever"* — §6's triggers are the mechanism for that. It touches no file
under `AGENTS.md`, `docs/00-governance/`, `scripts/`, `config/` or `.github/`, and
no file touched by PR #69, #71 or #73.

Sources cited by the operator, retained for provenance:
[OWASP LLM06 excessive agency](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/) ·
[NIST least privilege](https://csrc.nist.gov/glossary/term/least_privilege) ·
[NIST SP 800-53 Rev. 5](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) ·
[NIST SP 800-137](https://nvlpubs.nist.gov/nistpubs/legacy/sp/nistspecialpublication800-137.pdf) ·
[NIST OSCAL](https://pages.nist.gov/OSCAL/) ·
[NIST CSF 2.0](https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.pdf) ·
[OWASP SAMM](https://owasp.org/www-project-samm/) ·
[OPA bundles](https://www.openpolicyagent.org/docs/management-bundles) ·
[SLSA v1.2](https://slsa.dev/spec/v1.2/)
