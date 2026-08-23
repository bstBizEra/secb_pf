#!/usr/bin/env python3
"""Deterministically validate every control-plane object in the repository (FWK-104, P0 item 9).

WHY A SCRIPT AND NOT ANOTHER TEST. The JSON-subset validator and the YAML-subset reader were living
in `tests/test_control_kernel.py`, which meant a tool could not reuse them and a downstream project
could not run them at all. Duplicating either was prohibited -- parallel implementation creates the
competing source of truth Rule 4 exists to prevent -- so they moved here and the tests import them.

WHAT IT REPORTS, and why the third line is the interesting one:

    validated          instances that conform to their declared schema
    failures           instances that do not
    orphan instances   an instance declaring a schema id no schema file defines
    DORMANT schemas    a schema file no instance uses

Dormancy is the finding this tool exists to surface. A schema nobody instantiates and nothing
validates is indistinguishable from an enforced one by reading the repository -- and this framework
has already been bitten by exactly that: END_TO_END_TRACEABILITY.schema.json sat unenforced with an
uncomputable root field until FWK-101 activated it, and it was found by hand rather than by a check.

    SCHEMA_EXISTS != SCHEMA_ENFORCED
    SCHEMA_PRESENT != SCHEMA_USED

DETERMINISM. Same tree, same report: instances are discovered by sorted path walk, findings are
sorted, and no wall-clock value enters the body. The observation instant is reported beside the
body, never inside it, so two runs over one tree produce identical findings.

STDLIB ONLY (NFR-12). The validator implements exactly the JSON Schema keywords the control-plane
schemas use and REFUSES a schema using any other, because a validator that skips what it does not
understand reports clean on the constraints it cannot check.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

OK = 0
FAIL = 2

SKIP_DIRS = (".git", "__pycache__", ".pytest_cache", "node_modules")


class Refused(ValueError):
    """The repository cannot be validated as it stands."""


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
        if "minProperties" in schema and len(instance) < schema["minProperties"]:
            errors.append(f"{path}: fewer than minProperties {schema['minProperties']}")
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


# Keywords this validator ASSERTS.
ASSERTED = {"type", "additionalProperties", "required", "properties", "const", "enum", "items",
            "minItems", "minLength", "pattern", "minimum", "minProperties"}
# Keywords it RECOGNISES without asserting. In draft-07 `format` and `default` are ANNOTATIONS, not
# assertions, so treating them as unsupported was wrong: a schema using them is fully checkable by a
# validator that ignores them, which is what the specification requires.
#
#     RECOGNISED != ASSERTED
ANNOTATIONS = {"$schema", "$id", "title", "description", "format", "default", "examples",
               "$comment", "deprecated", "readOnly", "writeOnly"}
SUPPORTED = ASSERTED | ANNOTATIONS


def keywords(schema, seen=None) -> set:
    """Every keyword a schema uses, so an unimplemented one downgrades instances to UNCHECKED.

    This scan is by keyword NAME, and a name is not a construct. `"type": "string"` and
    `"type": ["string", "null"]` are the same keyword and different features: the first is
    implemented below, the second is a union this validator cannot evaluate. Reporting only the
    name let a union pass the guard and then raise `TypeError: unhashable type: 'list'` inside
    `validate` -- a crash, on the first real instance, from the guard written to prevent exactly
    that.

        KEYWORD_SUPPORTED != CONSTRUCT_SUPPORTED

    Union types are therefore reported as the distinct token `type[]`, which is absent from
    SUPPORTED, so the existing UNCHECKABLE_KEYWORDS path handles them and no second mechanism is
    introduced.
    """
    seen = seen if seen is not None else set()
    if isinstance(schema, dict):
        for key, value in schema.items():
            seen.add("type[]" if key == "type" and isinstance(value, list) else key)
            if key in ("properties",) and isinstance(value, dict):
                for sub in value.values():
                    keywords(sub, seen)
            elif key in ("items", "additionalProperties") and isinstance(value, dict):
                keywords(value, seen)
    return seen


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
                    child_indent, child = lines[i]
                    k2, _, v2 = child.partition(":")
                    i += 1
                    if v2.strip() in (">-", "|", ">"):
                        # A folded scalar inside a list item. Handled here because the same gap
                        # has now bitten three times: stability-targets.yaml (FWK-096) and
                        # exclusions.yaml (found by FWK-104's own validator) both lost data to it,
                        # and twice the data was rewritten instead of the reader. Three
                        # occurrences is where the cause gets fixed rather than the instance.
                        folded = []
                        while i < len(lines) and lines[i][0] > child_indent:
                            folded.append(lines[i][1])
                            i += 1
                        entry[k2.strip()] = " ".join(folded)
                    else:
                        entry[k2.strip()] = _scalar(v2)
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




def read_instance(path: Path):
    """Return a dict for a JSON or subset-YAML file, or None when it is not an object."""
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        return json.loads(text)
    lines = []
    for raw in text.splitlines():
        stripped = raw.split(" #")[0].rstrip() if " #" in raw else raw.rstrip()
        if not stripped.strip() or stripped.lstrip().startswith("#"):
            continue
        lines.append((len(stripped) - len(stripped.lstrip()), stripped.strip()))
    if not lines:
        return None
    value, _ = _block(lines, 0, 0)
    return coerce_lists(value)


def discover_schemas(root: Path) -> tuple[dict[str, Path], list[dict]]:
    """Map declared $id to its file, and return schema-level FINDINGS separately.

    An unidentifiable or duplicated schema is a finding, not a reason to abort. Aborting the whole
    run on one legacy file would make the tool unusable in the repository it is meant to audit, and
    would pressure whoever runs it into editing content that may be out of their scope. The verdict
    still fails -- the finding is reported, not forgiven.
    """
    found: dict[str, Path] = {}
    findings: list[dict] = []
    for path in sorted(root.rglob("*.schema.json")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        try:
            schema = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            findings.append({"schema_file": rel(root, path), "finding": "UNPARSEABLE",
                             "detail": str(exc)})
            continue
        identifier = schema.get("$id")
        if not identifier:
            findings.append({
                "schema_file": rel(root, path), "finding": "NO_SCHEMA_ID",
                "detail": ("declares no $id, so no instance can be matched to it -- it is "
                           "unenforceable by construction, not merely unused")})
            continue
        if identifier in found:
            findings.append({
                "schema_file": rel(root, path), "finding": "DUPLICATE_SCHEMA_ID",
                "detail": (f"$id {identifier!r} is also declared by "
                           f"{rel(root, found[identifier])}; two schemas with one identity make "
                           "conformance ambiguous")})
            continue
        found[identifier] = path
    return found, findings


def discover_instances(root: Path) -> list[tuple[Path, dict]]:
    """Every object declaring a `schema` string, in sorted path order for determinism."""
    instances: list[tuple[Path, dict]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix not in (".json", ".yaml", ".yml"):
            continue
        if any(part in SKIP_DIRS for part in path.parts) or path.name.endswith(".schema.json"):
            continue
        try:
            body = read_instance(path)
        except (json.JSONDecodeError, UnicodeDecodeError, OSError, KeyError, IndexError):
            continue
        if isinstance(body, dict) and isinstance(body.get("schema"), str):
            instances.append((path, body))
    return instances


def rel(root: Path, path: Path) -> str:
    """Repo-relative, so two checkouts of one tree produce identical reports."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def run(root: Path) -> dict:
    schemas, schema_findings = discover_schemas(root)
    instances = discover_instances(root)

    # A schema using keywords this validator cannot check is recorded as UNCHECKABLE and its
    # instances are NOT reported validated. Reporting them clean would claim a check that never ran.
    uncheckable: set[str] = set()
    for identifier, path in sorted(schemas.items()):
        unsupported = keywords(json.loads(path.read_text(encoding="utf-8"))) - SUPPORTED
        if unsupported:
            uncheckable.add(identifier)
            schema_findings.append({
                "schema_file": rel(root, path), "finding": "UNCHECKABLE_KEYWORDS",
                "detail": (f"uses {sorted(unsupported)}, which this validator does not implement; "
                           "instances are reported UNCHECKED rather than valid")})

    validated: list[str] = []
    failures: list[dict] = []
    orphans: list[dict] = []
    used: set[str] = set()

    unchecked: list[str] = []
    for path, body in instances:
        declared = body["schema"]
        used.add(declared)
        schema_path = schemas.get(declared)
        if schema_path is None:
            orphans.append({"instance": rel(root, path), "declared_schema": declared})
            continue
        if declared in uncheckable:
            unchecked.append(rel(root, path))
            continue
        errors = validate(body, json.loads(schema_path.read_text(encoding="utf-8")))
        if errors:
            failures.append({"instance": rel(root, path), "schema": declared,
                             "errors": sorted(errors)})
        else:
            validated.append(rel(root, path))

    dormant = sorted(i for i in schemas if i not in used)
    return {
        "schema": "secb.repository-validation/v1",
        "verdict": ("REPOSITORY_OBJECTS_VALID"
                    if not failures and not orphans and not schema_findings
                    else "OBJECT_VALIDATION_FAILED"),
        "schemas_discovered": len(schemas),
        "instances_discovered": len(instances),
        "validated": sorted(validated),
        "failures": sorted(failures, key=lambda f: f["instance"]),
        "orphan_instances": sorted(orphans, key=lambda o: o["instance"]),
        "schema_findings": sorted(schema_findings, key=lambda f: f["schema_file"]),
        "unchecked_instances": sorted(unchecked),
        "dormant_schemas": dormant,
        "dormant_ratio": f"{len(dormant)}/{len(schemas)}",
        "not_proven": [
            "that a dormant schema is wrong; it is unused, which is a different finding",
            "that a validated instance is CORRECT; conformance is a shape, not a judgement",
            "that an instance outside .json/.yaml/.yml was considered",
            "that an UNCHECKED instance is valid; its schema uses keywords this tool cannot check",
        ],
        "confers_merge_authority": False,
    }


def main(argv: list[str]) -> int:
    root = Path(os.environ.get("REPO_ROOT", ".")).resolve()
    try:
        report = run(root)
    except Refused as exc:
        print(f"REFUSED (closed): {exc}", file=sys.stderr)
        return FAIL
    except OSError as exc:
        print(f"REFUSED (closed): repository unreadable ({exc})", file=sys.stderr)
        return FAIL
    except Exception as exc:  # noqa: BLE001 -- deliberate: an unexpected crash must fail CLOSED
        # Only Refused and OSError were caught, so any other exception escaped as an uncaught
        # traceback and the process exited 1 -- not the declared FAIL = 2, and with no report at
        # all. A validator that dies without a verdict must not be distinguishable, by exit code,
        # from one that ran and found nothing wrong.
        print(f"REFUSED (closed): the audit raised {type(exc).__name__}: {exc}. No verdict was "
              f"reached, so nothing here says the repository objects are valid", file=sys.stderr)
        return FAIL
    observed = datetime.now(timezone.utc).isoformat()
    print(json.dumps({**report, "observed_at": observed}, indent=2, sort_keys=True))
    return OK if report["verdict"] == "REPOSITORY_OBJECTS_VALID" else FAIL


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
