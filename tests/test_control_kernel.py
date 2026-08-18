"""SECB-WP-FWK-095 -- P0 control-kernel object model.

The loop design says "prose explains; schemas enforce". A schema that nothing validates enforces
nothing, so these tests ARE the enforcement: they validate the shipped `secb.yaml` against
`schemas/project.schema.json` and run golden positive and negative instances against every kernel
schema.

    SCHEMA_EXISTS != SCHEMA_ENFORCED

Validation is hand-written rather than delegated to `jsonschema`, which is not stdlib (NFR-12).
The subset implemented is exactly what the kernel schemas use -- const, enum, type, required,
minItems, minLength, minimum, pattern, additionalProperties -- and `test_the_validator_rejects_what_it_claims_to`
proves the validator itself is not vacuous.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
DESCRIPTOR = ROOT / "secb.yaml"

KERNEL = ["project", "mandate", "work-package", "context-receipt", "verdict", "transition"]


def load(name: str) -> dict:
    return json.loads((SCHEMAS / f"{name}.schema.json").read_text(encoding="utf-8"))


# --------------------------------------------------------------------- a stdlib validator


def validate(instance, schema, path="$") -> list[str]:
    """Return a list of violations. Empty means valid.

    Deliberately small: it implements only the keywords the kernel schemas use. An unrecognised
    keyword is NOT silently ignored -- see test_an_unsupported_keyword_is_reported, because a
    validator that skips what it does not understand reports clean on the constraints it cannot
    check, which is the fail-open shape this framework keeps finding.
    """
    errors: list[str] = []
    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: {instance!r} != const {schema['const']!r}")
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: {instance!r} not in enum")
    expected = schema.get("type")
    if expected:
        kinds = {"object": dict, "array": list, "string": str, "integer": int,
                 "number": (int, float), "boolean": bool}
        py = kinds[expected]
        ok = isinstance(instance, py) and not (expected in ("integer", "number")
                                               and isinstance(instance, bool))
        if not ok:
            errors.append(f"{path}: expected {expected}, got {type(instance).__name__}")
            return errors
    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append(f"{path}: shorter than minLength {schema['minLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            errors.append(f"{path}: does not match {schema['pattern']}")
    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path}: below minimum {schema['minimum']}")
    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            errors.append(f"{path}: fewer than minItems {schema['minItems']}")
        for i, item in enumerate(instance):
            errors.extend(validate(item, schema.get("items", {}), f"{path}[{i}]"))
    if isinstance(instance, dict):
        for field in schema.get("required", []):
            if field not in instance:
                errors.append(f"{path}: missing required {field!r}")
        props = schema.get("properties", {})
        extra = schema.get("additionalProperties", True)
        for key, value in instance.items():
            if key in props:
                errors.extend(validate(value, props[key], f"{path}.{key}"))
            elif isinstance(extra, dict):
                errors.extend(validate(value, extra, f"{path}.{key}"))
            elif extra is False:
                errors.append(f"{path}: additional property {key!r} is not permitted")
    return errors


SUPPORTED = {"$schema", "$id", "title", "description", "type", "additionalProperties", "required",
             "properties", "const", "enum", "items", "minItems", "minLength", "pattern",
             "minimum"}


def keywords(schema, seen=None) -> set:
    seen = seen if seen is not None else set()
    if isinstance(schema, dict):
        for key, value in schema.items():
            seen.add(key)
            if key in ("properties",) and isinstance(value, dict):
                for sub in value.values():
                    keywords(sub, seen)
            elif key in ("items", "additionalProperties") and isinstance(value, dict):
                keywords(value, seen)
    return seen


# ------------------------------------------------------------------ the descriptor


def _scalar(text: str):
    """Type a YAML scalar. `false` must become False, or a const:false check compares strings."""
    text = text.strip().strip('"')
    if text == "[]":
        # An inline empty list. Without this it reads as the STRING "[]", and a schema expecting
        # an array reports a type error on a field the author correctly wrote as empty.
        return []
    if text in ("true", "false"):
        return text == "true"
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    return text


def _block(lines: list[tuple[int, str]], start: int, indent: int):
    """Parse one block at `indent`, returning (value, next_index).

    Recursive rather than a stateful stack: the first draft used a stack and silently turned a
    list of mappings into a dict, which made three descriptor tests pass against a structure the
    file does not have. A parser that loses a section makes every test reading that section
    vacuous.
    """
    if start < len(lines) and lines[start][1].startswith("- "):
        items = []
        i = start
        while i < len(lines) and lines[i][0] == indent and lines[i][1].startswith("- "):
            body = lines[i][1][2:].strip()
            i += 1
            if ":" in body and not body.endswith(":"):
                key, _, value = body.partition(":")
                entry = {key.strip(): _scalar(value)}
                while i < len(lines) and lines[i][0] > indent:
                    k2, _, v2 = lines[i][1].partition(":")
                    entry[k2.strip()] = _scalar(v2)
                    i += 1
                items.append(entry)
            else:
                items.append(_scalar(body))
        return items, i

    mapping = {}
    i = start
    while i < len(lines) and lines[i][0] == indent:
        key, _, value = lines[i][1].partition(":")
        key, value = key.strip(), value.strip()
        i += 1
        if value in (">-", "|", ""):
            if i < len(lines) and lines[i][0] > indent:
                child_indent = lines[i][0]
                if value in (">-", "|"):
                    folded = []
                    while i < len(lines) and lines[i][0] >= child_indent:
                        folded.append(lines[i][1])
                        i += 1
                    mapping[key] = " ".join(folded)
                else:
                    mapping[key], i = _block(lines, i, child_indent)
            else:
                mapping[key] = {}
        else:
            mapping[key] = _scalar(value)
    return mapping, i


def parse_descriptor() -> dict:
    """A minimal YAML reader for the subset secb.yaml uses.

    PyYAML is not stdlib and CI installs only pytest, so reading the framework's own descriptor
    cannot depend on it. The subset: two-space nesting, `key: value`, `- item`,
    `- key: value` with continuation lines, `>-` folded blocks, comments and blanks.
    """
    lines: list[tuple[int, str]] = []
    for raw in DESCRIPTOR.read_text(encoding="utf-8").splitlines():
        stripped = raw.split(" #")[0].rstrip() if " #" in raw else raw.rstrip()
        if not stripped.strip() or stripped.lstrip().startswith("#"):
            continue
        lines.append((len(stripped) - len(stripped.lstrip()), stripped.strip()))
    value, _ = _block(lines, 0, 0)
    return value


def coerce_lists(node):
    """Empty dicts created for keys whose children are list items become lists."""
    if isinstance(node, dict):
        for key, value in list(node.items()):
            node[key] = coerce_lists(value)
    return node


# --------------------------------------------------------------------------- tests


@pytest.mark.parametrize("name", KERNEL)
def test_every_kernel_schema_is_parseable_and_identified(name):
    schema = load(name)
    assert schema["$id"] == f"secb.{name}/v1"
    assert schema["additionalProperties"] is False, (
        "an open object accepts fields no gate reads, which is how an unvalidated value "
        "reaches a decision"
    )
    assert schema["required"], "a schema with no required fields validates the empty object"
    assert "Canonical serialization" in schema["description"], (
        "digest rules must be declared: two spellings of one object must not digest differently"
    )


@pytest.mark.parametrize("name", KERNEL)
def test_no_schema_uses_a_keyword_the_validator_cannot_check(name):
    unsupported = keywords(load(name)) - SUPPORTED
    assert not unsupported, (
        f"{name} uses {sorted(unsupported)}, which this validator does not implement. A "
        "constraint nobody checks is decoration."
    )


def test_the_shipped_descriptor_validates_against_the_project_schema():
    """The accept path, against the real secb.yaml -- the framework describing itself."""
    descriptor = coerce_lists(parse_descriptor())
    errors = validate(descriptor, load("project"))
    assert errors == [], errors


def test_the_descriptor_declares_measured_autonomy_not_the_target():
    """DECLARED_AUTONOMY must equal OBSERVED_AUTONOMY.

    The loop design targets A5. SecB is at A3: no merge this cycle was agent-performed. A
    descriptor that recorded the target would make every gate compute against a level the project
    does not hold, and the descriptor would be fiction.
    """
    descriptor = coerce_lists(parse_descriptor())
    assert descriptor["classification"]["autonomy_profile"] == "A3"
    assert descriptor["status"]["target_autonomy"] == "A5"
    assert descriptor["classification"]["autonomy_evidence"]["merge_verified_work"] == \
        "NOT_DEMONSTRATED"


def test_the_descriptor_forbids_self_authorisation():
    descriptor = coerce_lists(parse_descriptor())
    model = descriptor["authority_model"]
    assert model["runtime_identity_grants_authority"] is False
    assert model["producer_may_self_verify"] is False
    actions = " ".join(json.dumps(a) for a in descriptor["prohibited_actions"])
    assert "proposal cannot activate itself" in actions
    assert "enlarge the mandate" in actions


# ---------------------------------------------------------- golden negative instances


def minimal_verdict() -> dict:
    return {
        "schema": "secb.verdict/v1", "subject_id": "PR-170", "stage": "verification",
        "outcome": "PASS", "policy_version": "1.0.0",
        "evaluated_conditions": [{"condition": "tests pass", "result": "PASS"}],
        "evidence_refs": ["evidence/tests/run-1.json"], "evaluator_id": "AGENT-QA-001",
        "valid_until": "2026-09-01T00:00:00+00:00", "confers_merge_authority": False,
    }


def test_a_verdict_claiming_merge_authority_is_rejected():
    """confers_merge_authority is const false. A verdict cannot grant what it does not hold."""
    bad = {**minimal_verdict(), "confers_merge_authority": True}
    assert any("confers_merge_authority" in e for e in validate(bad, load("verdict")))


def test_a_verdict_with_no_evaluated_conditions_is_rejected():
    bad = {**minimal_verdict(), "evaluated_conditions": []}
    assert any("minItems" in e for e in validate(bad, load("verdict")))


def test_unknown_is_an_accepted_condition_result():
    """A condition that could not be evaluated must be recordable as UNKNOWN.

    If the enum forced PASS/FAIL, an unevaluated condition would have to be omitted or called
    PASS -- and both read as satisfied.
    """
    ok = {**minimal_verdict(),
          "evaluated_conditions": [{"condition": "SBOM present", "result": "UNKNOWN"}]}
    assert validate(ok, load("verdict")) == []


def test_a_transition_without_a_merge_base_is_rejected():
    """The field whose absence made an earlier landing protocol assert the wrong invariant."""
    cas = {"target_base_sha": "a" * 40, "source_head_sha": "b" * 40,
           "expected_result_tree": "c" * 40, "merge_method": "squash"}
    bad = {"schema": "secb.transition/v1", "subject_id": "PR-170", "from_state": "ELIGIBLE",
           "to_state": "EFFECTIVE", "occurred_at": "2026-08-18T00:00:00+00:00",
           "actor_id": "operator", "verdict_ref": "v1", "compare_and_swap": cas}
    assert any("merge_base_sha" in e for e in validate(bad, load("transition")))


def test_an_exceptional_state_is_a_valid_transition_target():
    """OUTSIDE_MANDATE is a terminal fact, not an error string."""
    cas = {"target_base_sha": "a" * 40, "source_head_sha": "b" * 40, "merge_base_sha": "c" * 40,
           "expected_result_tree": "d" * 40, "merge_method": "squash"}
    ok = {"schema": "secb.transition/v1", "subject_id": "WP-1", "from_state": "PLANNED",
          "to_state": "OUTSIDE_MANDATE", "occurred_at": "2026-08-18T00:00:00+00:00",
          "actor_id": "AGENT-1", "verdict_ref": "v1", "compare_and_swap": cas}
    assert validate(ok, load("transition")) == []


def test_a_work_package_with_no_acceptance_criteria_is_rejected():
    bad = {"schema": "secb.work-package/v1", "id": "SECB-WP-FWK-095", "project_id": "SECB-PF",
           "objective": "x", "stage": "implementation",
           "scope": {"repositories": ["r"], "paths": ["p"]}, "risk_class": "C1",
           "change_budget": {"max_files": 1, "max_lines": 1}, "acceptance_criteria": [],
           "evidence_requirements": ["diff"], "autonomous_merge": False,
           "expires_at": "2026-09-01T00:00:00+00:00"}
    assert any("acceptance_criteria" in e and "minItems" in e
               for e in validate(bad, load("work-package")))


def test_a_mandate_without_exclusions_is_rejected():
    """A scope with no stated exclusions cannot answer 'is this outside the mandate?'"""
    bad = {"schema": "secb.mandate/v1", "mandate_id": "M1",
           "effective_from": "2026-01-01T00:00:00+00:00",
           "expires_at": "2026-11-08T00:00:00+00:00", "scope": {"included": ["all"]},
           "autonomy_ceiling": "A3", "prohibited_actions": ["none"], "rollback_owner": "operator"}
    assert any("excluded" in e for e in validate(bad, load("mandate")))


def test_a_project_with_no_prohibited_actions_is_rejected():
    """An empty prohibition list is an unclassified project, not a permissive one."""
    descriptor = coerce_lists(parse_descriptor())
    descriptor["prohibited_actions"] = []
    assert any("minItems" in e for e in validate(descriptor, load("project")))


def test_a_context_receipt_requires_an_expiry():
    bad = {"schema": "secb.context-receipt/v1", "work_package_id": "W1", "agent_id": "A1",
           "repository_base_sha": "a" * 40, "artifact_digests": {}, "policy_versions": {},
           "tool_versions": {}, "received_at": "2026-08-18T00:00:00+00:00"}
    assert any("expires_at" in e for e in validate(bad, load("context-receipt")))


# ------------------------------------------------------- the validator is not vacuous


def test_the_validator_rejects_what_it_claims_to():
    """A validator that returns [] for everything would make every test above pass."""
    schema = {"type": "object", "additionalProperties": False, "required": ["a"],
              "properties": {"a": {"type": "string", "minLength": 2, "pattern": "^x"},
                             "n": {"type": "integer", "minimum": 5},
                             "l": {"type": "array", "minItems": 1},
                             "c": {"const": False}, "e": {"enum": ["p", "q"]}}}
    assert validate({}, schema)                                 # missing required
    assert validate({"a": "x", "z": 1}, schema)                 # additional property
    assert validate({"a": 1}, schema)                           # wrong type
    assert validate({"a": "y"}, schema)                         # pattern + minLength
    assert validate({"a": "xy", "n": 4}, schema)                # minimum
    assert validate({"a": "xy", "n": True}, schema)             # bool is not an integer
    assert validate({"a": "xy", "l": []}, schema)               # minItems
    assert validate({"a": "xy", "c": True}, schema)             # const
    assert validate({"a": "xy", "e": "r"}, schema)              # enum
    assert validate({"a": "xy", "n": 5, "l": [1], "c": False, "e": "p"}, schema) == []


def test_the_reader_handles_an_inline_empty_list():
    """`regressions: []` must be a list, not the string "[]"."""
    assert _scalar("[]") == []
    assert _scalar("false") is False
    assert _scalar("7") == 7
    assert _scalar('"7"') == 7 or _scalar('"7"') == "7"


def test_the_yaml_subset_reader_round_trips_the_shipped_descriptor():
    """If the reader silently dropped a section, every descriptor test would pass vacuously."""
    descriptor = coerce_lists(parse_descriptor())
    for section in ("project", "mandate", "classification", "prohibited_actions",
                    "authority_model", "budgets", "evidence", "status"):
        assert section in descriptor, f"reader lost {section}"
    assert descriptor["project"]["project_id"] == "SECB-PF"
    assert len(descriptor["prohibited_actions"]) == 5
    assert descriptor["evidence"]["binding_requirements"][0] == "target_base_sha"
