"""The product definition's counts must be recomputable from the ref it cites.

`SECB-WP-FWK-072` (issue #131).

    PROPOSED_HEAD evidence  ≠  EFFECTIVE_MAIN capability

A count with no `as_of_ref` is not a measurement, and a count taken from an open pull
request is not a property of the framework — the 209 tests reported while reviewing PR
#123 belong to that head, not to `main`. Every number in the definition's measured block
is therefore recomputed here **from the ref the document itself names**, so moving the ref
without re-measuring fails, and re-measuring without moving the ref fails too.

**Where this module can and cannot run.** Recomputation needs the cited commit in the
local object store. CI checks out shallow, so those tests `skip` there with an
`OBSERVATION_INCOMPLETE` reason rather than passing — a guard that cannot observe has not
verified anything. They run on any full clone. Giving the test job full history means
editing `ci.yml`, which PR #134 already claims, so it is deferred rather than contended.

`README.md` said *"Skeleton / Draft"* for a framework with 51 commits and seven working
gates. That is an underclaim, the mirror of `NFR-17`, and the same fault: the record and
the tree disagreed.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFINITION = REPO_ROOT / "docs" / "00-governance" / "FRAMEWORK_PRODUCT_DEFINITION.md"
PROFILE = REPO_ROOT / "docs" / "16-templates" / "FRAMEWORK_INSTANTIATION_PROFILE.yaml"
CHECKLIST = REPO_ROOT / "docs" / "16-templates" / "FRAMEWORK_INSTANTIATION_CHECKLIST.md"
README = REPO_ROOT / "README.md"

PROJECTION_FIELDS = ("as_of_ref", "projection", "binding", "observation_boundary")


def ref_available(ref: str) -> bool:
    """Is the cited commit in this checkout's object store?

    `actions/checkout@v4` defaults to `fetch-depth: 1`, so the test job holds only the
    PR head — a historical ref is simply absent, and `git cat-file` exits 128. Measured:
    this module's first version failed CI for exactly that reason while passing locally.
    """
    return subprocess.run(
        ["git", "-C", str(REPO_ROOT), "cat-file", "-e", f"{ref}^{{commit}}"],
        capture_output=True,
    ).returncode == 0


def require_ref(ref: str) -> None:
    """Skip with a reason that cannot be read as verification.

    A shallow checkout makes recomputation impossible, not passing. The distinction is
    `OBSERVATION_INCOMPLETE` versus a clean result — the same rule #126 sets for the
    network half of its gate, applied to this module's own limits. Making CI fetch full
    history would edit `ci.yml`, which PR #134 already claims; deferred rather than
    contended.
    """
    if not ref_available(ref):
        pytest.skip(
            f"OBSERVATION_INCOMPLETE: cited ref {ref[:7]} is absent from this checkout "
            "(shallow clone). Recomputation is a full-clone guard and did NOT run — this "
            "is not evidence the counts are correct"
        )


def git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def measured_block() -> dict[str, str]:
    """The `EFFECTIVE_MAIN` block — the one that carries binding counts."""
    text = DEFINITION.read_text(encoding="utf-8")
    for block in re.findall(r"```yaml\n(.*?)```", text, re.S):
        if "projection: EFFECTIVE_MAIN" in block:
            values = {}
            for line in block.splitlines():
                if ":" in line and not line.startswith((" ", "\t", "#")):
                    key, _, value = line.partition(":")
                    values[key.strip()] = value.strip().strip('"')
            return values
    raise AssertionError("no EFFECTIVE_MAIN measured block found in the definition")


def test_the_measured_block_declares_every_projection_field():
    block = measured_block()
    for field in PROJECTION_FIELDS:
        assert field in block, f"the measured block omits {field!r}"
    assert re.fullmatch(r"[0-9a-f]{40}", block["as_of_ref"]), (
        "as_of_ref must be a full commit SHA — an abbreviated ref is ambiguous over time"
    )


def test_the_cited_ref_exists_and_is_an_ancestor_of_main():
    """A ref nobody can resolve makes every count below it unverifiable."""
    ref = measured_block()["as_of_ref"]
    require_ref(ref)
    if not ref_available("origin/main"):
        pytest.skip("OBSERVATION_INCOMPLETE: origin/main is absent from this checkout")
    assert git("cat-file", "-t", ref) == "commit"
    merge_base = git("merge-base", ref, "origin/main")
    assert merge_base == ref, (
        f"{ref[:7]} is not an ancestor of origin/main; the definition cites a ref that is "
        "not on the effective base"
    )


@pytest.mark.parametrize(
    "field,command",
    [
        ("commits", ("rev-list", "--count")),
        ("enforcement_scripts", ("ls-tree", "-r", "--name-only")),
        ("test_modules", ("ls-tree", "-r", "--name-only")),
        ("numbered_documentation_domains", ("ls-tree", "-d", "--name-only")),
    ],
)
def test_each_count_is_recomputable_from_the_cited_ref(field, command):
    """The coupling: move the ref without re-measuring, and this fails."""
    block = measured_block()
    ref = block["as_of_ref"]
    require_ref(ref)
    declared = int(block[field])

    if field == "commits":
        actual = int(git("rev-list", "--count", ref))
    elif field == "enforcement_scripts":
        actual = len([f for f in git("ls-tree", "-r", "--name-only", ref, "scripts/").splitlines()
                      if f.endswith(".py")])
    elif field == "test_modules":
        actual = len([f for f in git("ls-tree", "-r", "--name-only", ref, "tests/").splitlines()
                      if f.endswith(".py")])
    else:
        actual = len([d for d in git("ls-tree", "-d", "--name-only", ref, "docs/").splitlines()
                      if re.match(r"docs/\d{2}-", d)])

    assert declared == actual, (
        f"{field} is declared {declared} but recomputes to {actual} at {ref[:7]}. Either "
        "the count is stale or the ref moved without re-measurement"
    )


def test_the_skill_population_is_reported_as_empty_while_it_is_empty():
    """The claim the three-axis split exists to keep honest.

    A tested router with no registry is mechanism-ready and population-empty. If a
    registry instance ever lands, this must be re-measured rather than left reading zero.
    """
    block = measured_block()
    instances = list(REPO_ROOT.glob("config/*skill*registry*.json"))
    instances += [p for p in REPO_ROOT.glob("docs/skills/catalog/*") if p.suffix in {".json", ".yaml"}]
    assert int(block["skill_registry_instances"]) == len(instances), (
        f"declared {block['skill_registry_instances']} skill registry instances; found "
        f"{[str(p) for p in instances]}"
    )


def test_the_three_readiness_axes_are_stated_separately():
    text = DEFINITION.read_text(encoding="utf-8")
    for axis in (
        "FRAMEWORK_CONTROL_READINESS",
        "INSTANCE_POPULATION_READINESS",
        "RUNTIME_EXECUTION_READINESS",
    ):
        assert axis in text, f"{axis} is not stated"
    assert "≠" in text, "the axes must be stated as distinct, not merely listed"


def test_readme_defers_to_the_canonical_status_reference():
    """Two copies of a status drift; that is how 'Skeleton / Draft' survived."""
    text = README.read_text(encoding="utf-8")
    assert "Skeleton / Draft" not in text
    assert "Skeleton establishment only" not in text
    assert "FRAMEWORK_PRODUCT_DEFINITION.md" in text, (
        "the README must point at the canonical status reference rather than restate it"
    )


def test_the_definition_declares_itself_canonical():
    assert "canonical_status_reference: true" in DEFINITION.read_text(encoding="utf-8")


def test_every_profile_placeholder_blocks_the_instance():
    """`TODO` is an unanswered authority question, not a default.

    Asserted because the failure mode of a template is silent inheritance: a field nobody
    filled in becomes the value the instance operates under.
    """
    text = PROFILE.read_text(encoding="utf-8")
    assert "TODO" in text, "the profile must ship with explicit placeholders"
    assert "every unresolved placeholder makes the instance NOT_READY" in text
    for required in ("project_identity", "authority_owner", "work_package_prefix",
                     "delegation_ceiling", "expiry_policy"):
        assert f"{required}:" in text, f"the profile omits {required}"


def test_the_registries_ship_empty_and_say_so():
    """A schema is not a population — the distinction this work package is built on."""
    text = PROFILE.read_text(encoding="utf-8")
    for registry in ("agent_registry", "skill_registry", "tool_registry"):
        section = text.split(f"{registry}:")[1].split("\n\n")[0]
        assert "state: EMPTY" in section, f"{registry} must ship declared EMPTY"


def test_the_checklist_carries_the_invariants_that_prevent_silent_inheritance():
    text = CHECKLIST.read_text(encoding="utf-8")
    for invariant in (
        "No inherited template field silently becomes authority",
        "Control strength is never reported above the mechanism",
        "cannot claim a populated capability from a schema or fixture alone",
    ):
        assert invariant in text, f"the checklist omits: {invariant}"


def test_the_known_duplication_is_recorded_rather_than_forgotten():
    """`NFR_CATALOGUE.md`'s stale header is deferred, and the deferral is visible."""
    text = DEFINITION.read_text(encoding="utf-8")
    assert "NFR_CATALOGUE.md" in text and "Stage 2 in progress" in text, (
        "the known status duplication must be recorded, since it is not fixed here"
    )
