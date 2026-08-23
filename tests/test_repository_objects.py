"""SECB-WP-FWK-104 -- deterministic repository object validation (P0 item 9).

The finding this tool exists to surface is DORMANCY. A schema nobody instantiates and nothing
validates is indistinguishable from an enforced one by reading the repository, and this framework
has already been bitten: END_TO_END_TRACEABILITY.schema.json sat unenforced, with an uncomputable
root field, until FWK-101 activated it -- found by hand, not by a check.

    SCHEMA_EXISTS != SCHEMA_ENFORCED
    SCHEMA_PRESENT != SCHEMA_USED

It also found three orphans of my own on its first run: #172's scope-register files declared schema
ids no schema defined, so they claimed conformance to nothing.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "scripts" / "check_repository_objects.py"

sys.path.insert(0, str(ROOT / "scripts"))
from check_repository_objects import ANNOTATIONS, ASSERTED, read_instance, run  # noqa: E402


def fixture_repo(tmp_path: Path, schemas: dict, instances: dict) -> Path:
    root = tmp_path / "repo"
    (root / "schemas").mkdir(parents=True)
    for name, body in schemas.items():
        (root / "schemas" / name).write_text(json.dumps(body), encoding="utf-8")
    for name, body in instances.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body if isinstance(body, str) else json.dumps(body), encoding="utf-8")
    return root


def simple_schema(identifier="secb.thing/v1") -> dict:
    return {"$schema": "http://json-schema.org/draft-07/schema#", "$id": identifier,
            "title": "Thing", "type": "object", "additionalProperties": False,
            "required": ["schema", "name"],
            "properties": {"schema": {"const": identifier},
                           "name": {"type": "string", "minLength": 1}}}


# ------------------------------------------------------------- the real repository


def test_the_real_repository_audit_runs_and_reports():
    """The audit must have VALIDATED something, not merely have run.

    This asserted `schemas_discovered >= 20`, `instances_discovered >= 5` and `failures == []`.
    All three survive a tree in which nothing conforms: an instance whose declared schema does not
    exist is an ORPHAN, and an orphan is not a failure. An independent review demonstrated it by
    renaming the `$id` in all 17 schemas -- `validated` fell to `[]`, every instance went orphan,
    and all 15 tests in this file still passed.

        AUDIT_RAN != AUDIT_VALIDATED_ANYTHING

    So the load-bearing assertion is on `validated`. The orphan count is pinned rather than
    required to be zero, because exactly one real orphan exists and is a finding this package
    reports rather than fixes: FRAMEWORK_INSTANTIATION_PROFILE.yaml declares
    `secb.framework-instantiation-profile/v1`, a schema that exists nowhere in the repository.
    Requiring `orphan_instances == []` would fail on the true state of the tree.
    """
    report = run(ROOT)
    assert report["schemas_discovered"] >= 20
    assert report["instances_discovered"] >= 5
    assert report["failures"] == [], report["failures"]

    assert report["validated"], (
        "the audit validated NOTHING. Every discovered instance is an orphan or unchecked, so a "
        "green result here says only that the walk completed -- which is true of a tree in which "
        "no schema matches any instance."
    )
    orphans = [o["instance"] for o in report["orphan_instances"]]
    assert orphans == ["docs/16-templates/FRAMEWORK_INSTANTIATION_PROFILE.yaml"], (
        f"the orphan set changed: {orphans}. One orphan is expected and recorded -- the "
        "instantiation profile declares a schema that does not exist. A new orphan means an "
        "instance lost its schema, which this audit exists to surface, not to tolerate."
    )


def test_the_report_is_deterministic_over_one_tree():
    """Same tree, same findings. The observation instant is reported BESIDE the body, never in it."""
    first, second = run(ROOT), run(ROOT)
    assert first == second
    assert "observed_at" not in first, (
        "a wall-clock value inside the body would make two runs over one tree differ"
    )


def test_every_reported_path_is_repository_relative():
    """Absolute paths would make two checkouts of one tree produce different reports."""
    report = run(ROOT)
    paths = (report["validated"] + [f["instance"] for f in report["failures"]]
             + [o["instance"] for o in report["orphan_instances"]]
             + [f["schema_file"] for f in report["schema_findings"]])
    assert paths, "nothing was reported, so nothing was checked"
    assert not [p for p in paths if p.startswith("/") or ":" in p[:3]]


def test_pre_existing_schema_findings_stay_attributed_to_their_surface():
    """Recorded rather than fixed: at `main@ace1e57`, seven skill-router schemas declared no $id.

    They are unenforceable by construction -- nothing can be matched to them -- but they predate this
    work package and belong to another surface. Reporting is the right action; editing them would be
    scope creep into content this package has no mandate over. **#192 gives all seven an $id**, which
    takes the count to zero.

    So the count is recorded here and deliberately NOT asserted. The previous form required
    `len(no_id) >= 5`, which made this test fail on the day the gap closed -- reporting the intended
    outcome as a defect. Cumulative-prefix simulation caught it: composed with #192, the count is 0.

        DEFICIENCY_PINNED != DEFICIENCY_PERMANENT

    What remains is the durable half: whichever NO_SCHEMA_ID findings the real tree still carries
    belong to the skill-router surface and not to this package's own schemas -- true at seven and
    true at zero. That the detector *works* is proven separately and unconditionally by
    `test_a_schema_without_an_id_is_a_finding_not_an_abort`, on a fixture, so this assertion going
    vacuous as #192 lands removes no coverage.
    """
    report = run(ROOT)
    no_id = [f for f in report["schema_findings"] if f["finding"] == "NO_SCHEMA_ID"]
    assert all("skill-router" in f["schema_file"] for f in no_id), (
        f"a NO_SCHEMA_ID finding now points outside the skill-router surface, so it is no longer a "
        f"pre-existing finding this package declined to fix: "
        f"{[f['schema_file'] for f in no_id if 'skill-router' not in f['schema_file']]}"
    )


# ------------------------------------------------------------- each finding class


def test_a_schema_without_an_id_is_a_finding_not_an_abort(tmp_path):
    """Aborting on one legacy file would make the tool unusable in the repository it audits."""
    root = fixture_repo(tmp_path, {"bad.schema.json": {"title": "no id"},
                                   "ok.schema.json": simple_schema()},
                        {"thing.json": {"schema": "secb.thing/v1", "name": "x"}})
    report = run(root)
    assert [f["finding"] for f in report["schema_findings"]] == ["NO_SCHEMA_ID"]
    assert report["validated"] == ["thing.json"], "the good instance is still validated"
    assert report["verdict"] == "OBJECT_VALIDATION_FAILED"


def test_a_duplicate_schema_id_is_reported(tmp_path):
    root = fixture_repo(tmp_path, {"a.schema.json": simple_schema(),
                                   "b.schema.json": simple_schema()}, {})
    findings = [f["finding"] for f in run(root)["schema_findings"]]
    assert "DUPLICATE_SCHEMA_ID" in findings


def test_an_orphan_instance_is_reported(tmp_path):
    """An instance declaring a schema nobody defines claims conformance to nothing."""
    root = fixture_repo(tmp_path, {"ok.schema.json": simple_schema()},
                        {"orphan.json": {"schema": "secb.absent/v1"}})
    report = run(root)
    assert report["orphan_instances"] == [{"instance": "orphan.json",
                                           "declared_schema": "secb.absent/v1"}]


def test_a_dormant_schema_is_reported(tmp_path):
    """The finding the tool exists for: present, unused, indistinguishable from enforced."""
    root = fixture_repo(tmp_path, {"ok.schema.json": simple_schema()}, {})
    report = run(root)
    assert report["dormant_schemas"] == ["secb.thing/v1"]
    assert report["dormant_ratio"] == "1/1"


def test_a_nonconforming_instance_is_a_failure(tmp_path):
    root = fixture_repo(tmp_path, {"ok.schema.json": simple_schema()},
                        {"bad.json": {"schema": "secb.thing/v1", "name": ""}})
    report = run(root)
    assert report["failures"][0]["instance"] == "bad.json"
    assert any("minLength" in e for e in report["failures"][0]["errors"])


def test_an_instance_of_an_uncheckable_schema_is_unchecked_not_valid(tmp_path):
    """Reporting it clean would claim a check that never ran."""
    schema = simple_schema()
    schema["properties"]["name"]["multipleOf"] = 2   # an assertion this validator cannot make
    root = fixture_repo(tmp_path, {"ok.schema.json": schema},
                        {"thing.json": {"schema": "secb.thing/v1", "name": "x"}})
    report = run(root)
    assert report["unchecked_instances"] == ["thing.json"]
    assert report["validated"] == []
    assert any(f["finding"] == "UNCHECKABLE_KEYWORDS" for f in report["schema_findings"])


def test_a_clean_repository_validates(tmp_path):
    root = fixture_repo(tmp_path, {"ok.schema.json": simple_schema()},
                        {"thing.json": {"schema": "secb.thing/v1", "name": "x"}})
    report = run(root)
    assert report["verdict"] == "REPOSITORY_OBJECTS_VALID"
    assert report["confers_merge_authority"] is False


# ------------------------------------------------------------- the keyword split


def test_annotations_are_recognised_without_being_asserted():
    """draft-07 treats `format` and `default` as ANNOTATIONS, not assertions.

    Classifying them as unsupported was wrong: a schema using them is fully checkable by a
    validator that ignores them, which is what the specification requires.

        RECOGNISED != ASSERTED
    """
    assert {"format", "default"} <= ANNOTATIONS
    assert not (ANNOTATIONS & ASSERTED)
    assert "minProperties" in ASSERTED


def test_min_properties_is_actually_enforced(tmp_path):
    """It was missing, which is how two of my own schemas were reported UNCHECKABLE."""
    schema = simple_schema()
    schema["properties"]["body"] = {"type": "object", "minProperties": 1}
    root = fixture_repo(tmp_path, {"ok.schema.json": schema},
                        {"thing.json": {"schema": "secb.thing/v1", "name": "x", "body": {}}})
    assert any("minProperties" in e for e in run(root)["failures"][0]["errors"])


# ------------------------------------------------------------- the YAML subset


def test_a_folded_scalar_inside_a_list_item_survives_the_reader(tmp_path):
    """The third recurrence of one gap, fixed at the cause.

    `stability-targets.yaml` (FWK-096) and `exclusions.yaml` (found by this very tool) both lost
    data to folded scalars in list items, and twice the DATA was rewritten instead of the reader.
    """
    path = tmp_path / "f.yaml"
    path.write_text(
        "schema: secb.thing/v1\nitems:\n  - id: A\n    reason: >-\n      first line\n"
        "      second line\n  - id: B\n    reason: short\n", encoding="utf-8")
    body = read_instance(path)
    assert body["items"][0]["reason"] == "first line second line"
    assert len(body["items"][0]) == 2, body["items"][0]
    assert body["items"][1]["reason"] == "short"


def test_the_cli_exits_non_zero_when_findings_exist():
    result = subprocess.run([sys.executable, str(TOOL)], capture_output=True, text=True,
                            env={**os.environ, "REPO_ROOT": str(ROOT),
                                 "PYTHONDONTWRITEBYTECODE": "1"}, check=False)
    report = json.loads(result.stdout)
    assert (result.returncode == 0) == (report["verdict"] == "REPOSITORY_OBJECTS_VALID")
    assert "observed_at" in report, "the instant is reported beside the body"
