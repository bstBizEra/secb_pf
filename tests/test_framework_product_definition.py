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

import ast
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


# --- required versus advisory -------------------------------------------------
#
# A REQUIRED assertion must never turn a missing prerequisite into a green job. The five
# ref-dependent checks cannot run under CI's HEAD_ONLY checkout, so they are ADVISORY:
# named `test_advisory_*`, permitted to skip, and never citable as verification.
# Everything else is REQUIRED and must execute on every run (`SECB-WP-FWK-078`).
ADVISORY_PREFIX = "test_advisory_"


def test_no_required_assertion_can_skip_its_way_to_green():
    """The review condition, applied to this module itself.

    `zero failures ≠ zero required observations omitted`. A required test that calls
    `pytest.skip` on a missing prerequisite converts an unmet precondition into a passing
    job — the fail-open shape this repository forbids everywhere else.

    Detection is `ast`-based, over **call nodes**, not substrings. The first version
    matched text and flagged itself, because a guard searching for a skip call
    necessarily contains that text — the same false positive a name-only matcher produced
    in `check_prohibited_calls.py` when it read `set.remove()` as a filesystem write
    (`SECB-WP-FWK-048`). A matcher must look at what the code *calls*.
    """
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    escapes = {"require_ref", "skip"}
    offenders = []
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef) or not node.name.startswith("test_"):
            continue
        if node.name.startswith(ADVISORY_PREFIX):
            continue
        for inner in ast.walk(node):
            if isinstance(inner, ast.Call):
                func = inner.func
                name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
                if name in escapes:
                    offenders.append(node.name)
                    break
    assert not offenders, (
        f"required assertions {offenders} can skip. Rename them test_advisory_* and stop "
        "citing them as verification, or give them prerequisites that always hold"
    )


def test_the_definition_does_not_claim_verification_it_did_not_receive():
    """`NOT_VERIFIED_BY_CI` belongs on the claim, not only in a skip reason.

    A skip reason lives in a job log nobody opens once the checkmark is green. The
    claim's own surface must carry its verification status, or the green Test job becomes
    the evidence by default.
    """
    block = measured_block()
    assert block.get("verification_status") == "NOT_VERIFIED_BY_CI", (
        "these counts are recomputed only on a full clone; the document must say so where "
        "the counts are"
    )
    assert block.get("required_checkout_profile") == "ANCESTRY_PATH", (
        "rev-list --count and the ancestor proof need ancestry, not merely the objects"
    )
    assert "must not be cited as evidence" in DEFINITION.read_text(encoding="utf-8"), (
        "the document must forbid citing the green Test job for these counts"
    )


def test_the_measured_block_declares_every_projection_field():
    block = measured_block()
    for field in PROJECTION_FIELDS:
        assert field in block, f"the measured block omits {field!r}"
    assert re.fullmatch(r"[0-9a-f]{40}", block["as_of_ref"]), (
        "as_of_ref must be a full commit SHA — an abbreviated ref is ambiguous over time"
    )


def test_advisory_the_cited_ref_exists_and_is_an_ancestor_of_main():
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
def test_advisory_each_count_is_recomputable_from_the_cited_ref(field, command):
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


def test_every_commit_this_document_cites_is_a_full_digest():
    """§ Projection discipline mandates `<full commit or immutable artifact digest>`. Enforce it.

    The stage-2 ratifier was cited as `c94e4da` — seven characters, in the document that requires
    full digests four lines further down. An abbreviation is neither full nor immutable: it is
    ambiguous by construction and grows more so as the repository does.

        DECLARED != ENFORCED   — on the document's own anchor rule

    Both commits cited here are 40 characters and both resolve. This keeps it that way.
    """
    text = DEFINITION.read_text(encoding="utf-8")
    tokens = set(re.findall(r"\b[0-9a-f]{7,40}\b", text))
    assert tokens, "no commit-shaped token found — the anchor convention changed, or this checks nothing"
    short = sorted(t for t in tokens if len(t) != 40)
    assert not short, (
        f"abbreviated commit reference(s) {short} in a document whose own § Projection discipline "
        f"requires `<full commit or immutable artifact digest>`."
    )
    for token in sorted(tokens):
        resolved = subprocess.run(["git", "rev-parse", "--verify", "-q", f"{token}^{{commit}}"],
                                  cwd=REPO_ROOT, capture_output=True, text=True)
        assert resolved.returncode == 0, f"{token} is cited as a commit but does not resolve"
