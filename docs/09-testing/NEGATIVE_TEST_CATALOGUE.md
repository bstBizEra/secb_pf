# Negative-Test Catalogue — which evasions the gates actually stop

Status: Measured 2026-08-11, as of `3b61307` · `SECB-WP-FWK-042` (issue #82)
Source scenarios: FPSA v1.0 §15 (15 cases) · BACP v1.1 §14 (18 cases)
Tests: `tests/test_negative_catalogue.py`, plus the existing suite it cites

`KN-001` says a gate counts only once **proven** to fail on a real pull request.
Three supplied specifications handed this project 33 concrete evasion scenarios
and nothing had mapped them against what the gates stop. This is that map.

## Measured coverage

```text
FPSA §15 scenarios          15
  COVERED                    4
  GAP — mechanism absent     7
  NOT_APPLICABLE             4   (no ballot layer, no runtime, no external effect)

BACP §14 scenarios          18
  COVERED                    2
  GAP                        3
  NOT_APPLICABLE            13   (durable execution, effects, identities — none exist)
```

**4 of 15** on FPSA. That is the number, and it is not flattering. Every
`COVERED` row names a test that exists and passes; a claim citing a test that
does not exist is the `#407` defect in test form, and
`test_every_covered_scenario_names_a_test_that_exists` fails the build if one
appears.

## FPSA §15

| # | Scenario | Status | Evidence or reason |
|--:|---|---|---|
| 01 | Rename a request to evade the duplicate detector | **GAP** | No duplicate detector exists. `FWK-038` measured the need at 2 for 2 on supplied specs and 0 for 36 on work items, and deferred the machinery with a trigger |
| 02 | Split a change into several tickets to evade a class | **GAP** | Verified: one 1,300-line change escalates, two ~550-line halves each auto-approve. `test_known_gap_splitting_a_change_evades_the_line_ceiling` locks the behaviour. The classifier sees one diff at a time and has no notion of a sibling ticket |
| 03 | Hide a permission grant in configuration | **GAP** | `config/` is an `auto_path` and only two files in it are named constitutional, so `config/permissions.json` auto-merges. **Found by doing it**: `FWK-041` landed `config/identifier_taxonomy.json` at `G0` under this rule. `test_known_gap_a_new_config_file_classifies_as_low_risk` |
| 04 | Add an integration without declaring it | **GAP** | No expansion manifest and no declared `write_set`. `FWK-039` deferred both with triggers |
| 05 | Add an exception with no expiry | **GAP** | No exception registry. The two live exceptions — the accepted single-identity risk and the envelope — both carry expiry by hand |
| 06 | Reduce an approval threshold or quorum | **COVERED** | Quorum lives in the envelope, which is constitutional. `test_lowering_a_quorum_or_ceiling_cannot_auto_approve`, and `g4_root_authority_surface_is_constitutional` |
| 07 | Change the classifier so your own change scores lower | **COVERED** | `test_editing_the_classifier_to_lower_its_own_risk_cannot_auto_approve`; also `divergence_escalates_even_when_head_would_pass` and `deleting_head_classifier_cannot_escape_comparison` |
| 08 | Change a protected path so your file stops being protected | **COVERED** | The path list is in the envelope. `test_the_two_named_config_files_are_still_constitutional`, plus the dual-policy rule — a widened envelope cannot approve its own widening |
| 09 | Proposer and auditor use one identity | **NOT_APPLICABLE** | `ballot_layer.state = NOT_ACTIVE`. `ballot.schema.json` requires `signer_identity` to differ from the proposer; nothing enforces it because no second identity exists. Recorded as accepted risk for stages 1–8 |
| 10 | Actual write-set wider than the approved one | **GAP** | No `write_set` is declared at intake, so there is nothing to compare against. `FWK-038`'s lean cut proposed the field |
| 11 | Cost or concurrency exceeds its cap mid-execution | **NOT_APPLICABLE** | No runtime caps and no cost telemetry. `K-10` has recorded nothing since `FWK-016` |
| 12 | Disable the audit logger, or edit evidence after a verdict | **COVERED, partially** | `g5_deleting_evidence_is_rejected` and `g5_removing_a_ci_enforcement_step_is_rejected` cover deletion; `test_editing_ci_so_a_gate_stops_running_cannot_auto_approve` covers the CI half. **Not covered:** editing evidence in place without deleting it |
| 13 | Keep a plugin or workflow past its trial expiry | **GAP** | No retirement contract. `FWK-039` measured one confirmed orphan — `src/secb_router/`, 669 SLOC, no runtime consumer — and no promote-or-retire decision |
| 14 | Add a policy that contradicts a canonical one | **GAP** | `SPECIFICATION_CONFLICT_PROTOCOL.md` is applied by reading. Four conflict records exist, all raised by hand |
| 15 | A rollback script that cannot restore the baseline | **NOT_APPLICABLE** | `K-07c` is `0/0` — no drill has ever run, which is why that row is recorded `undefined` rather than `100%` |

## BACP §14

Thirteen of the eighteen concern durable execution, external effects, workload
identities and learning pipelines. SecB has **zero** deployed surfaces, `E4`
evidence of **none**, and one identity — so a test would assert against
machinery that does not exist. They are listed as `NOT_APPLICABLE` with the
absent capability named, because an absent scenario and an unconsidered one
should not look alike.

| # | Scenario | Status | Evidence or reason |
|--:|---|---|---|
| 17 | Squash merge falsifies a tested-head ancestry check | **COVERED** | The property SecB depends on, proven in a hermetic repository: `test_squash_merge_breaks_ancestry_but_preserves_the_tree`, and `test_a_squash_that_changes_content_is_detectable_by_the_tree` proves the substitute can fail |
| 05 | Base branch changes after CI passes | **GAP, partially mitigated** | No `baseline_is_current` check. The dual-policy rule catches a *policy* change under the PR, not a content change under it. `mergeable_state` is checked by hand before every merge |
| 06 | A status check arrives from an unexpected source | **GAP, unfixable here** | Requires rulesets to pin the expected app. The API returns `403 Upgrade to GitHub Pro`; recorded in `AGENTS.md` and in `GOVERNANCE_DEFERRED_CAPABILITIES.md` §D1 |
| 10 | Sub-work items created to evade a budget | **GAP** | Same mechanism as FPSA 02, same lock |
| 18 | Several agents share a signer but are counted as a quorum | **NOT_APPLICABLE** | One identity; quorum is enforced nowhere in code, which is the compensating control |
| 01–04, 07–09, 11–16 | Crash after an external effect · replayed webhook · lease expiry mid-write · takeover without inspection · tampered policy bundle · borrowed auditor credential · injected tool response · kill signal mid-call · partial compensation · lagging cost telemetry · learning candidate edits its evaluator · claimed-complete with a failing postcondition · rollback to an incompatible schema | **NOT_APPLICABLE** | No durable workflow, no external effects, no leases, no signed bundles, no second identity, no learning pipeline. Each is a real scenario for a system that has those; none is one here |

## What a green run of this module means

> The recorded coverage still holds.

It does **not** mean no evasion is possible. Two of the tests here document a
hole by asserting current behaviour, so their **failure** means the hole was
closed and this catalogue is stale. The message on each says so.

That distinction is the correction `FWK-041` was put through — a suite proves
only *"no qualifying failure was observed within the boundary"*, and the boundary
here is the classifier's view of one diff at a time.

## The two gaps worth closing first, and why not here

**Ticket splitting (FPSA 02, BACP 10).** The fix needs cross-ticket state: the
classifier would have to know that a sibling work package touched adjacent
scope. That is `scripts/` — `G1` — and it is the first thing WICG's admission
control would buy if the machinery is ever earned.

**`config/` classification (FPSA 03).** The fix is a one-line envelope change:
classify `config/` as governance implementation rather than an `auto_path`, with
the two named files staying constitutional. It is a **`G4`** act on the authority
surface, and it would reclassify `FWK-041`'s own registry — which is exactly why
an executor proposes it and does not land it.

Neither is attempted here. `FWK-039`'s reasoning applies: a deferral with a
trigger is a decision, and this catalogue is the trigger's evidence.
