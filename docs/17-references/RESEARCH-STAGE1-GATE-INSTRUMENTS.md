# Research Record — Instruments for the Stage-1 Gate Blockers

Status: Research complete, awaiting adoption decision
Work Package: `SECB-WP-FWK-015` (issue #26)
Researched: 2026-08-10 · Addresses conditions **C-3** and **C-4** of
`docs/13-evidence/STAGE_GATE_PRD_BASELINED.md`
Scope note: this record identifies instruments. It implements none of them.

## Why these two conditions blocked the gate

C-1, C-2 and C-5 need operator knowledge — who owns the product, which
product it is, and the verdict itself. No research can supply those.

C-3 and C-4 are different. They were recorded as blockers because SecB had no
*method*, not because the operator lacked an opinion. Both are solved problems
outside this repository. That is what makes them researchable, and it is why
the gate was stuck on something avoidable.

---

## K-08 — Defect taxonomy

**Problem.** Defect escape rate is unmeasurable because no defect
classification exists, so "a defect found after a gate passed" cannot be
counted by type or attributed to a stage.

**Two candidate standards.**

[IEEE 1044-2009](https://standards.ieee.org/ieee/1044/4607/) classifies
software anomalies independently of when they arise in the lifecycle. It
separates four concepts that this repository has been using loosely —
**problem, failure, fault, defect** — and defines eight anomaly classes
(computational, interface/timing, logic, data, data-processing,
document-quality, documentation, and enhancement/reinforcement), each further
divisible. It also carries impact schemes for **severity, priority and
customer value**.

[Orthogonal Defect Classification](https://en.wikipedia.org/wiki/Orthogonal_Defect_Classification)
(Chillarege, IBM Research, late 1980s–90s) is not a taxonomy of defects but a
measurement of the *process*. Its two load-bearing attributes are **defect
type** — what was changed in the code to fix it, with seven empirically
established values — and **defect trigger** — the force that surfaced the
fault. Type measures the product through the process; trigger measures the
*testing* process. IBM's implementation uses four attributes: type, trigger,
source and impact.

**Recommendation for SecB: ODC's two-attribute core, with IEEE 1044 severity.**

The KPI SecB actually wants (K-08, defect escape by stage) is a *process*
measurement, which is exactly what ODC was designed to produce; a
defect-nature taxonomy alone cannot say which gate should have caught it. IEEE
1044's severity scheme is already in use — `DELIVERY_LIFECYCLE_STAGES.md`
stage 9 has a five-level severity policy with gate treatments — so adopting
its severity vocabulary formalizes something present rather than adding a
layer.

**Minimum viable implementation: three fields per defect**, recorded as issue
labels or a table row:

| Field | Values | Purpose |
|---|---|---|
| `defect_type` | ODC: assignment/initialization · checking · algorithm · function · interface · timing/serialization · relationship | Which kind of change fixed it |
| `defect_trigger` | what surfaced it: unit test · integration · CI gate · review · classifier · production | Which activity earns credit — and which stage should have caught it |
| `severity` | IEEE 1044: critical · high · medium · low · informational | Already the stage-9 gate treatment |

Escape rate then falls out: a defect whose trigger is later than the stage that
should have caught it is an escape, attributable to that stage.

**Cost.** Three fields at defect-close time. No tool. The two defects this
repository has already found (`DEF-ENGLOOP-MVP-001` — named-skill priority
evaluated after the minimum-cardinality shortcut; and the G5 scan that rejected
its own test fixture) are both classifiable retroactively: type `checking`,
trigger `unit test` and `CI gate` respectively — and notably **both were
`checking` defects surfaced by a gate, which is a pattern after two
occurrences.**

---

## K-09 — Classifier accuracy at n = 14

**Problem.** `GOVERNANCE_DEFERRED_CAPABILITIES.md` D5 records that fourteen
work packages is not a corpus and a confusion matrix from it would be "numbers
without power". That reasoning was right, and it stopped at the wrong
conclusion — that nothing can be measured.

**Finding 1: a confusion matrix is the wrong instrument here, and not only
because n is small.** The governance classifier has a strongly asymmetric cost
structure. A false `CONSTITUTIONAL_REQUIRED` costs one unnecessary human
merge. A false `AUTO_APPROVED` on a change that expands authority is the
failure the entire framework exists to prevent. Balanced metrics — accuracy,
F1 — average across those two, which is exactly wrong: in safety-critical
settings, evaluation should target the reduction of false negatives rather
than balanced performance, and default thresholds are unsuitable
([Galileo, F1/precision/recall](https://galileo.ai/blog/f1-score-ai-evaluation-precision-recall);
[Reasoning's Razor, on recall at critical operating points](https://arxiv.org/pdf/2510.21049)).

**So the metric is one-sided: recall on the constitutional class. Zero
downgrades, or the classifier is broken.**

**Finding 2: with zero observed failures, the honest instrument is the rule of
three.** If zero events occur in *n* independent trials, one can be
approximately 95% confident the true rate is below **3/n**
([Statology](https://www.statology.org/a-concise-guide-to-the-statistical-rule-of-three/);
[pmean, confidence intervals with zero events](http://www.pmean.com/01/zeroevents.html)).
This converts "not measurable" into a number that exists today and tightens
automatically as work accrues:

| Observations with zero downgrades | 95% upper bound on downgrade rate |
|---:|---:|
| 14 (today) | **≤ 21.4%** |
| 30 (ladder `A1` → `A2` threshold) | ≤ 10.0% |
| 60 | ≤ 5.0% |
| 300 | ≤ 1.0% |

The bound at fourteen is weak — a fifth of decisions could be wrong and this
evidence would not notice. **That is the correct thing to publish**, because it
prices the current confidence honestly and shows exactly what more evidence
buys. It also gives the authority ladder a statistical meaning it did not have:
the `A1 → A2` condition of 30 clean merges corresponds to a 10% bound, not to a
feeling of readiness.

**Finding 3: for any proportion at this n, use Wilson, not Wald.** The Wilson
score interval inverts a score test rather than relying on asymptotic
normality, and has substantially better coverage at small n and near 0 or 1
([Wilson score interval](https://www.bohrium.com/en/sciencepedia/feynman/keyword/wilson_score_interval)).
Relatedly, [*Don't Use the CLT in LLM Evals With Fewer Than a Few Hundred
Datapoints*](https://arxiv.org/pdf/2503.01747) argues the same for
agent-evaluation samples of this size — directly applicable, since SecB's
sample is a few dozen.

**Minimum viable implementation.** Record, per PR: the classifier verdict, the
verdict a human would have given, and whether they differ in the downgrading
direction. Three fields, appended to the existing evidence comment. The bound
is then one division. **No corpus, no harness, no matrix.**

---

## K-10 — Agent cost instrumentation

**Problem.** No instrumentation exists, so cost per accepted change is
unmeasurable, and `PERFORMANCE_INDICATORS.md`'s cost layer (tokens, tool
calls, compute cost, budget exceptions) is entirely unpopulated.

**Finding: there is now a vendor-neutral standard, so SecB should not invent
field names.** The OpenTelemetry GenAI semantic conventions, developed by the
GenAI SIG since April 2024, standardize attributes for LLM calls, agent steps,
token usage and cost. The relevant instruments are
`gen_ai.client.token.usage` — a histogram filterable by `gen_ai.token.type` to
separate input from output — and `gen_ai.client.operation.duration`, filterable
by `gen_ai.request.model`. Cost is derived from token counts combined with
model identity rather than recorded directly
([OpenTelemetry GenAI observability](https://opentelemetry.io/blog/2026/genai-observability/);
[implementation guide](https://hidekazu-konishi.com/entry/opentelemetry_genai_semantic_conventions_guide.html)).
Datadog, New Relic and Dynatrace consume these natively, so instrumented code
needs no vendor SDK.

**Recommendation: adopt the attribute names now as the recording contract,
defer the collector.** The expensive part of observability is not the
collector — it is discovering later that historical data used incompatible
field names and cannot be compared. Recording
`gen_ai.usage.input_tokens` / `output_tokens` / `gen_ai.request.model` per work
package in the evidence comment costs nothing today and makes a future
collector a drop-in.

**Constraint that must survive.** `PERFORMANCE_INDICATORS.md` requires that
cost efficiency never override safety, quality or authorization controls, and
`KPI_BASELINE.md` already excludes cost from every auto-merge criterion. Cost
instrumentation must remain observational: it may inform planning and must
never become a gate condition.

---

## C-4 / R-05 — Segregation of duties with one person

**Problem.** `STAKEHOLDER_REGISTER.md` records that the Architecture Review
Board, Security and Compliance Review Board, and Change Advisory Board named in
`DELIVERY_LIFECYCLE_STAGES.md` have no members and collapse onto the operator.
Read strictly, stages 3, 5, 9, 10 and 11 cannot pass as written.

**Finding: SoD is not binary in recognized practice, and infeasible
segregation has a defined treatment rather than a waiver.** Where segregation
is not feasible, management is expected to implement **compensating controls
providing independent review and increased oversight** — commonly supervisory
review or rotation — and to keep audit-ready documentation: approval records,
system logs, and sign-offs identifying **preparer and reviewer separately**
([Sikich, on SoD as a key internal control](https://www.sikich.com/insight/why-segregation-of-duties-is-a-key-internal-control-and-how-to-implement-it/);
[SOX SoD practice](https://www.securends.com/blog/segregation-of-duties-for-sox-compliance/)).
ISACA's SoD control matrix is explicitly a guideline naming which duties must
not combine **and which require compensating controls**
([ISACA Journal, implementing SoD](https://www.isaca.org/resources/isaca-journal/issues/2016/volume-3/implementing-segregation-of-duties-a-practical-experience-based-on-best-practices)).

**Applied to SecB, the collapse is treatable — and SecB's compensating
controls are unusually strong for a one-person deployment:**

| Compensating control | Already in force |
|---|---|
| Mechanical, non-discretionary gates | Authority, Test, Budget — all proven to fail on real PRs |
| An authority that cannot approve its own expansion | `G4` on every governance and enforcement path |
| A policy that cannot ratify itself | `check_dual_policy.py` — base and head must agree |
| Preparer and reviewer recorded separately | Evidence comments name executor and gate authority; `STAGE_GATE_PRD_BASELINED.md` ships with `decision` empty |
| Prohibited actions refused rather than weighed | `L0_ROOT_CONSTITUTION.md` `G5` |

**Recommendation.** Record the collapse as an **accepted risk with named
compensating controls and a review date** — the recognized treatment — rather
than leaving it as an implied equivalence discovered at stage 3. Concretely:
the operator may hold sponsor, product owner and gate authority for stages
1–8, provided each gate record names the collapse and cites the compensating
controls above.

**The one collapse that is not acceptable.** Stage 9's exit condition requires
that **QA and Security independently approve** the release candidate.
"Independent" is the substance of that gate, not its wording, and a
compensating control cannot manufacture independence from a single identity —
this is the same reason the ballot layer is `NOT_ACTIVE`. Before stage 9,
SecB needs either an external reviewer or a genuinely separate identity
(deferred capability D3). Stages 1–8 can proceed; stage 9 cannot, and that
should be recorded now rather than discovered when a release candidate is
waiting.

---

## What this changes for the stage-1 verdict

| Condition | Before | After this research |
|---|---|---|
| C-3 (three unmeasurable KPIs) | No method existed | All three have a named instrument with a minimum implementation costing 3 fields, 3 fields, and 3 fields respectively — no tooling |
| K-09 specifically | "Not computable" | Computable today: **≤21.4%** 95% upper bound on the downgrade rate, tightening to ≤10% at 30 observations |
| C-4 (single-person SoD) | Nominal SoD, unresolved | Recognized treatment identified: accepted risk + named compensating controls + review date, valid for stages 1–8 |
| Stage 9 | Assumed reachable | **Explicitly not reachable** without a second identity — surfaced now, not later |

`APPROVED_WITH_CONDITIONS` is now defensible: C-3 and C-4 have methods, and
their conditions can be written with owners and dates instead of hope.
**C-1, C-2 and C-5 remain untouched** — the product owner's name, the product
selection, and the verdict itself are the operator's, and no amount of
research substitutes for them.

## Sources

- [IEEE 1044-2009, Standard Classification for Software Anomalies](https://standards.ieee.org/ieee/1044/4607/)
- [Orthogonal Defect Classification](https://en.wikipedia.org/wiki/Orthogonal_Defect_Classification)
- [A Concise Guide to the Statistical Rule of Three](https://www.statology.org/a-concise-guide-to-the-statistical-rule-of-three/)
- [Confidence interval with zero events](http://www.pmean.com/01/zeroevents.html)
- [Wilson score interval](https://www.bohrium.com/en/sciencepedia/feynman/keyword/wilson_score_interval)
- [Don't Use the CLT in LLM Evals With Fewer Than a Few Hundred Datapoints](https://arxiv.org/pdf/2503.01747)
- [Reasoning's Razor: recall at critical operating points](https://arxiv.org/pdf/2510.21049)
- [F1 Score for AI Evaluation: Precision and Recall](https://galileo.ai/blog/f1-score-ai-evaluation-precision-recall)
- [Inside the LLM Call: GenAI Observability with OpenTelemetry](https://opentelemetry.io/blog/2026/genai-observability/)
- [OpenTelemetry GenAI Semantic Conventions Implementation Guide](https://hidekazu-konishi.com/entry/opentelemetry_genai_semantic_conventions_guide.html)
- [Why segregation of duties is a key internal control](https://www.sikich.com/insight/why-segregation-of-duties-is-a-key-internal-control-and-how-to-implement-it/)
- [Segregation of Duties for SOX Compliance](https://www.securends.com/blog/segregation-of-duties-for-sox-compliance/)
- [ISACA Journal — Implementing Segregation of Duties](https://www.isaca.org/resources/isaca-journal/issues/2016/volume-3/implementing-segregation-of-duties-a-practical-experience-based-on-best-practices)
