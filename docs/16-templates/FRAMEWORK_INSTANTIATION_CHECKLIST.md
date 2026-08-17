# Framework instantiation checklist

`SECB-WP-FWK-072`. Work through this after filling
[`FRAMEWORK_INSTANTIATION_PROFILE.yaml`](FRAMEWORK_INSTANTIATION_PROFILE.yaml). Canonical
framework status lives in
[`FRAMEWORK_PRODUCT_DEFINITION.md`](../00-governance/FRAMEWORK_PRODUCT_DEFINITION.md).

## Invariants — these are not preferences

- **No inherited template field silently becomes authority.** Every value an instance
  operates under is either filled in deliberately or blocks the instance.
- **Every unresolved placeholder makes the instance `NOT_READY`.** `TODO` is an unanswered
  authority question.
- **Framework defaults are recommendations** until the instance's authority ratifies them.
- **Prefixes and thresholds are data, not enforcement vocabulary.** `SECB-WP` moved into
  the envelope for this reason (`FWK-036`); the enforcement scripts read it at runtime.
- **Control strength is never reported above the mechanism and its verified behaviour.**
- **An instance cannot claim a populated capability from a schema or fixture alone.**

## Generated and baselined outputs

| Output | Done when |
|---|---|
| `AGENTS_contract` | The instance's operating contract exists and names its own authority, not SecB's |
| `delegation_envelope` | Scope, caps, tier, expiry filled; `ballot_layer` state stated honestly |
| `authority_classifier_profile` | `auto_paths`, `constitutional_paths` and governance paths reflect *this* project |
| `budget_policy` | A declared ceiling the CI can trip |
| `stage_gate_profile` | Which stages apply, and each one's exit evidence |
| `CI_or_equivalent_gate_bindings` | Gates wired and observed failing on a deliberate violation |
| `evidence_manifest` | What is recorded, where, and what is sealed |
| `condition_register` | Open conditions with owners — empty is a claim, not a default |
| `registry_manifests` | Agent, skill and tool registries — `EMPTY` is a valid, stated value |
| `instantiation_receipt` | Records the SecB `as_of_ref`, the profile digest, and who ratified it |

## Known instantiation cost, measured

`NFR-15` was measured twice on SecB itself. **0 of 3 enforcement scripts require an edit**;
13 files still do, of which 1 is the intended configuration change and 12 are prose or
identity strings. The mechanical surface is closed; **the prose surface grows with the
framework**. Budget for the prose, and prefer "the work-package prefix" over spelling a
literal one in any new governed document.

## Verify by invoking, not by reading

A gate that reads its configuration has a failure mode a hard-coded one does not: absent or
malformed configuration. Before declaring an instance ready, confirm each gate **fails
closed** on absent, empty, malformed and unreadable input. A configurable gate that fails
*open* when its configuration is missing is worse than the hard-coded gate it replaced.
