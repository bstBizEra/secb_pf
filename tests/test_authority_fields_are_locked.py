"""A schema that declares an authority-conferral field must pin it to false.

THE PROPERTY. Across this repository several objects carry a field whose whole purpose is to say
"this artifact grants nothing" -- `confers_merge_authority`, `may_delegate`, and their kin. A field
like that is only worth having if no valid instance can assert the opposite.

`config/shadow_merge_queue_receipt.schema.json` already does it correctly and has since before this
guard existed:

    "confers_merge_authority": {"const": false}       required: true

`const` AND `required`: a receipt cannot omit the field, and cannot set it true. That is the
difference between a property being *unrepresentable* and merely *conventional*.

WHY THIS GUARD IS REGRESSION-ONLY, AND WHAT IT DELIBERATELY DOES NOT DO.

An audit of the escalation surface found nine tools declaring non-conferral: two back it with schema
consts, seven emit it as an output value guarded by a test. Requiring all nine to carry a schema
would be the stronger control -- and it would turn seven open pull requests red until each wrote one,
which is a sequencing decision belonging to the operator rather than to a test.

    ADOPTION_LINT   forces the pattern onto emitters that lack it   → 7 PRs affected
    REGRESSION_LINT protects every instance that HAS it             → 0 PRs affected

This is the second. It cannot make anyone adopt the pattern; it makes the pattern impossible to
weaken once adopted, and it starts protecting each new instance the moment that instance appears --
including the eleven consts arriving with the control-kernel and authority-object work.

    PATTERN_AVAILABLE != PATTERN_ADOPTED    (the audit's finding, not this guard's job)
    PATTERN_ADOPTED   != PATTERN_PROTECTED  (this guard's job)
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# A field is authority-conferring if its NAME asserts a grant. Matched by name rather than by an
# allowlist so a newly-invented field is covered on the day it is written, not on the day someone
# remembers to register it.
CONFERRAL = re.compile(r"^(confers_\w*authority|may_delegate|grants_\w+|runtime_identity_grants_authority)$")


def schema_files() -> list[Path]:
    listing = subprocess.run(
        ["git", "ls-files", "-z"], cwd=REPO_ROOT, capture_output=True, check=True
    ).stdout.decode("utf-8", "replace")
    found = [REPO_ROOT / n for n in listing.split("\0")
             if n.endswith(".schema.json") and (REPO_ROOT / n).is_file()]
    assert found, "git ls-files found no *.schema.json -- this guard would check nothing"
    return found


def conferral_fields() -> list[tuple[str, str, dict, list]]:
    """(schema path, field name, its subschema, the object's required list)."""
    out = []
    for path in schema_files():
        document = json.loads(path.read_text(encoding="utf-8"))

        def walk(node):
            if not isinstance(node, dict):
                if isinstance(node, list):
                    for item in node:
                        walk(item)
                return
            props = node.get("properties")
            if isinstance(props, dict):
                for name, sub in props.items():
                    if CONFERRAL.match(name):
                        out.append((path.relative_to(REPO_ROOT).as_posix(), name, sub,
                                    node.get("required", [])))
            for value in node.values():
                walk(value)

        walk(document)
    return out


def test_the_scan_finds_the_known_instance():
    # Guards the guard. If the walk stops finding fields, every assertion below passes vacuously --
    # the failure mode that let a BOM guard and a vocabulary parser both report success on nothing.
    found = conferral_fields()
    assert found, (
        "no authority-conferral field found in any schema. The repository has carried "
        "confers_merge_authority in shadow_merge_queue_receipt.schema.json since before this guard; "
        "if the walk finds nothing, the walk is broken."
    )


@pytest.mark.parametrize("case", conferral_fields(),
                         ids=lambda c: f"{Path(c[0]).name}:{c[1]}")
def test_a_conferral_field_is_pinned_false(case):
    path, name, sub, _ = case
    assert sub.get("const") is False, (
        f"{path}: `{name}` is declared without `\"const\": false`, so a valid instance could assert "
        f"that this artifact DOES confer authority. Found: {json.dumps(sub)[:120]}\n\n"
        "A field that says 'grants nothing' is only worth having if nothing valid can say otherwise."
    )


@pytest.mark.parametrize("case", conferral_fields(),
                         ids=lambda c: f"{Path(c[0]).name}:{c[1]}")
def test_a_conferral_field_cannot_be_omitted(case):
    path, name, _, required = case
    assert name in required, (
        f"{path}: `{name}` is pinned to false but not required, so an instance may omit it. "
        "An absent disclaimer is not a disclaimer -- a consumer reading the object sees no statement "
        "either way, which is the empty-versus-absent confusion this repository has hit before."
    )
