# Analysis and Research — BST-EL-METRIC-001, before adoption

Status: Analysis complete, adoption **recommended with three amendments**
Work Package: `SECB-WP-FWK-022` (issue #42)
Subject: the operator-supplied Docs–Code–Surface Measurement Standard v0.1
Method: verify each external claim · apply the model to SecB and compute · then
recommend

## Why analysis came before adoption

The executor previously offered a 7:1 docs-to-code ratio as evidence that
governance had become the product. The standard's first conclusion is that this
instrument is wrong. Adopting a standard whose purpose is to stop bad
measurement, *without measuring anything first*, would repeat the error in a new
costume. So the model was applied before being installed.

## Part 1 — Verification of the standard's external claims

| Claim | Verified? | What the source says |
|---|---|---|
| DORA associates documentation quality with organizational performance, measured through reliability, findability, clarity and currency rather than volume | **Confirmed** | DORA links documentation quality to the organization's ability to meet performance and profitability goals, assessed via eight attributes including clarity, findability and reliability. It reports that documentation quality *"drives the implementation of every single technical practice studied"* and that the lift from technical capabilities is **amplified** for teams with above-average documentation quality ([DORA](https://dora.dev/capabilities/documentation-quality/)) |
| GitHub Linguist must not be used as a docs-to-code ratio because it excludes prose | **Confirmed, and more strongly than stated** | Linguist excludes *"binary data, vendored code, generated code, documentation, or … `data` (e.g. SQL) or `prose` (e.g. Markdown) languages"* — filtered before detection runs. Using Linguist percentages as a docs ratio would divide by a denominator from which documentation has already been removed ([how-linguist-works](https://github.com/github-linguist/linguist/blob/main/docs/how-linguist-works.md)) |
| `cloc` gives repeatable physical source/comment/blank counts and can diff two revisions | Accepted, not independently exercised | SecB's baseline below used `git ls-files` plus a non-blank/non-comment filter instead, because `cloc` is not installed and adding a dependency to take one baseline is not warranted. The standard's boundary definitions are what matter; the tool is substitutable |
| OpenAPI / GraphQL introspection / AsyncAPI / Storybook are suitable machine-readable surface sources | Accepted as design guidance | **Not applicable to SecB**, which has none of these. Relevant to future products, which is the point of a standard |
| OWASP recommends maintaining API inventories because missing inventories create operational and security risk | Accepted | Cited as API9:2023 Improper Inventory Management. Consistent with the standard's `SDI` drift metric |

**No claim was found to be wrong.** One is understated: the Linguist warning is
more important than the standard makes it, because Linguist output is the number
most people already have and would reach for first.

## Part 2 — Independent finding the standard does not mention

Goodhart's Law applies to `DSC` exactly as it applies to `DCR`. *"When a measure
becomes a target, it ceases to be a good measure"* — and the documented
containment strategy is to **pair every efficiency metric with a quality or
outcome metric, so single-metric gaming becomes visible because the cost shows
up elsewhere** ([Goodhart's Law and metric gaming](https://wiki.wfmlabs.org/wiki/Goodhart%27s_Law_and_Metric_Gaming),
[Goodhart's Law in software](https://codepulsehq.com/guides/goodharts-law-engineering-metrics)).

The standard's §8 recommends `DSC` as *"the primary executive KPI"*. `DSC` is a
ratio whose **denominator is chosen by the party being measured.** Its cheapest
improvement is not writing documentation — it is declaring less surface, or
classifying a behaviour as internal so it never enters the manifest. `SDI` is the
intended guard, but `SDI` compares declared against *observed* surface, and
observation depends on extractors that only exist for the surface kinds a project
happens to use.

SecB is the proof. See below: its `DSC` is high while its condition is bad.

## Part 3 — The model applied to SecB, computed

Commands and boundaries are recorded so the numbers are reproducible.

**Documentation universe** — prose words, fenced code blocks and inline code
stripped, table pipes and markup removed:

```
active_prose_words   42,408
code_block_words      1,371   (measured separately as examples, not prose)
```

**Code universe** — non-blank, non-comment authored lines:

```
production_sloc         669   (scripts/ + src/)
test_sloc               487   (reported separately, per the standard)
```

**Surface inventory**, applied honestly against the taxonomy. The router in
`src/secb_router/` is **excluded**: it has no consumer outside its own tests, and
the standard says internal functions are not surface unless they form a supported
contract.

| surface_id | kind | B | E | C | S | PSU |
|---|---|--:|--:|--:|--:|--:|
| `CLI-CHECK-WP-REF` | cli_command | 1.0 | 1.0 | 1.5 | 1.1 | 1.65 |
| `CLI-CHECK-BUDGET` | cli_command | 1.0 | 1.0 | 1.5 | 1.1 | 1.65 |
| `CLI-CLASSIFY-DELTA` | cli_command | 1.0 | 1.0 | 2.0 | 1.1 | 2.20 |
| `CLI-CHECK-DUAL-POLICY` | cli_command | 1.0 | 1.0 | 2.0 | 1.1 | 2.20 |
| `ADMIN-ENVELOPE-EDIT` | admin_action | 1.0 | 1.0 | 2.0 | 1.1 | 2.20 |
| `REPORT-GOV-VERDICT` | report | 1.5 | 1.0 | 1.5 | 1.1 | 2.48 |

**Seven of the ten taxonomy kinds are empty**: no UI journey, no UI state, no
REST operation, no GraphQL operation, no event operation, no webhook, no
scheduled job.

| Metric | Value |
|---|---|
| `WPS` weighted product surface | **12.38** from 6 declared items |
| `DCR-S` | **6,339** prose words per 100 production SLOC |
| `PSD` surface density | 18.5 PSU per kSLOC |
| Prose words per PSU | **3,427** |
| `DSC` documentation surface coverage | **≈0.67** — see below |
| `TCR` traceability closure | 6 of 6 surfaces trace to a requirement, an implementation and (4 of 6) a test |

`DSC` was computed, not assumed. Every surface has an ID, owner, behavioural
description, requirement reference, implementation reference and change history.
But the standard's **conditional obligation for an operational dependency**
requires a runbook, monitoring, alert and recovery procedure, and **four of six
surfaces have none of those** — `NEW_PROJECT_BOOTSTRAP.md` documents
instantiation, not gate operation or recovery. Counting that obligation, coverage
lands near two thirds rather than the ~100% a naive reading would report.

## Part 4 — What the numbers say that the ratio did not

The 7:1 figure said "too much documentation". That framing was wrong, and the
correction is not that everything is fine.

**3,427 prose words per unit of product surface** is the real number. There is
not too much documentation; **there is almost no product.** Seven of ten surface
kinds are empty, and the six items that exist are the machinery that governs the
repository — not behaviour any user depends on.

Two consequences follow that the ratio could not reach:

1. **A high `DSC` here would be an artefact of a tiny denominator.** If the
   operational-dependency obligation were waived, SecB's coverage would read
   ~100% while its condition remained "documents nearly everything about nearly
   nothing". `DSC` as *primary* executive KPI is therefore unsafe at low `WPS`.
2. **The genuine gap is operational, not descriptive.** The four gates run in
   production CI, are depended on by every merge, and have **no runbook, no
   monitoring, no alerting and no recovery procedure.** That is a real
   documentation deficiency the ratio was blind to and this model found on first
   application.

## Part 5 — Recommendation

**Adopt, with three amendments.** The model is sound, its citations hold, and its
first application produced two findings the previous instrument could not.

| # | Amendment | Reason |
|--:|---|---|
| **A1** | `DSC` is not the primary KPI on its own. Report it **always paired with `WPS`**, and treat `DSC` as uninterpretable below a stated `WPS` floor | Goodhart: the denominator is chosen by the measured party, and SecB demonstrates a high `DSC` coexisting with a bad condition |
| **A2** | Add a **fourth verdict vocabulary** entry to the reconciliation table in `SPECIFICATION_CONFLICT_PROTOCOL.md`. This standard's `HUMAN_REQUIRED` is a *policy-exception* verdict on a docs check — not the merge verdict (retired), not the stage-gate verdict, not the conflict verdict | Four vocabularies now share tokens; SecB has already fixed this collision class twice |
| **A3** | Adopt at **roadmap stage 1 (Observe) only**. No gate, no threshold, no blocking | The standard's own roadmap says observe first; SecB has 6 surface items, which does not justify an extractor, and the weights are explicitly uncalibrated pending a six-to-eight-week baseline |

**Do not adopt** the CI extraction pipeline, the gates table, or the weight
calibration yet. Each requires either surface SecB does not have or a baseline
period that has not elapsed.

## Part 6 — What adoption would oblige next

Recorded so adoption is not mistaken for completion:

- The operational-dependency gap on four gates becomes a named documentation
  obligation — a runbook covering gate operation, failure and recovery.
- `WPS` becomes the honest headline number for "is SecB a product yet", replacing
  the ratio. Today it is **12.38**.
- The surface manifest needs a schema before a second project uses it, or every
  project will invent its own field names — the same lesson recorded for the
  OpenTelemetry cost attributes.
