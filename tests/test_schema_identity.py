"""Every JSON Schema in the tree declares a unique $id.

WHY. `$id` is the key an instance is matched to its schema by. A schema without one is
unenforceable *by construction* -- not merely unused. Seven schemas under
docs/06-agent-orchestration/skill-router/ had no $id, so no instance could ever be bound to them
and no validator could ever check one, while the files looked like working contracts.

    SCHEMA_EXISTS != SCHEMA_ADDRESSABLE != SCHEMA_ENFORCED

Found by running SECB-WP-FWK-104's repository validator (#180) against its own head: 11 findings,
7 of them NO_SCHEMA_ID and all 7 pre-existing. That validator is not on main, so this test is the
part of the property that can be asserted here, today, without waiting on that pull request.

WHAT THIS DOES NOT DO. It does not require a single $id *format*. Three incompatible forms are in
use:

    secb.<name>/vN            21 files   (the dominant form; adopted for the 7 fixed here)
    https://secb.example/…     6 files
    https://secb.local/…       1 file    (config/ballot.schema.json -- the constitutional one)

Unifying them is a controlled-vocabulary decision, not a test's call: $id is the matching key, so
changing one silently breaks whatever bound to the old value. Recorded and deferred -- see the
identifier-taxonomy registration issue. Asserting a single form here would either fail on 7
pre-existing files or quietly bless one convention by enforcement.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def schema_files() -> list[Path]:
    found = sorted(
        p for p in REPO_ROOT.rglob("*.schema.json")
        if ".git" not in p.parts and "node_modules" not in p.parts
    )
    assert found, "no *.schema.json found -- discovery is broken and this file checks nothing"
    return found


@pytest.mark.parametrize("path", schema_files(), ids=lambda p: p.name)
def test_every_schema_declares_an_id(path: Path):
    document = json.loads(path.read_text(encoding="utf-8"))
    assert "$id" in document, (
        f"{path.relative_to(REPO_ROOT)} declares no $id. An instance is matched to its schema by "
        "$id, so this schema cannot be bound to anything and no validator can check an instance "
        "against it. It is unenforceable by construction, which is worse than unused: the file "
        "reads as a working contract and enforces nothing.\n"
        "Add an $id. The dominant form in this repository is `secb.<name>/vN`."
    )
    assert isinstance(document["$id"], str) and document["$id"].strip(), (
        f"{path.relative_to(REPO_ROOT)} declares an empty or non-string $id"
    )


def test_no_two_schemas_claim_the_same_id():
    # A duplicated $id makes instance-to-schema matching ambiguous, and whichever the validator
    # happens to pick decides whether an instance is valid. That is a silent coin flip.
    by_id = defaultdict(list)
    for path in schema_files():
        document = json.loads(path.read_text(encoding="utf-8"))
        if "$id" in document:
            by_id[document["$id"]].append(path.relative_to(REPO_ROOT).as_posix())
    duplicates = {i: p for i, p in by_id.items() if len(p) > 1}
    assert not duplicates, (
        f"these $id values are claimed by more than one schema: {duplicates}. Matching an instance "
        "becomes order-dependent, so validity depends on which file the validator reached first."
    )


def test_every_schema_parses_and_declares_its_dialect():
    # A schema that does not say which dialect it is written in cannot be checked for keywords the
    # validator does not implement -- which is the other half of #180's findings.
    missing = []
    for path in schema_files():
        document = json.loads(path.read_text(encoding="utf-8"))
        if "$schema" not in document:
            missing.append(path.relative_to(REPO_ROOT).as_posix())
    assert not missing, f"these schemas declare no $schema dialect: {missing}"
