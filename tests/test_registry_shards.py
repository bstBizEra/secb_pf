"""Sharded control surface — `SECB-WP-FWK-084` (#151).

`config/control_surface.json` is claimed by five open branches at one hunk each, and the
shadow merge queue proved the resulting conflict at prefix 9 of a measured queue. Sharding
removes the shared line. These tests hold the migration to three properties:

* one authority at every state — dual-read proves equivalence, it does not create a second
  source of truth;
* removal leaves a tombstone, so a control cannot disappear silently;
* the digest has a reproducible representation, declared as a **subset** of RFC 8785 that
  refuses what it does not implement.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check_registry_shards.py"
MONOLITH = REPO_ROOT / "config" / "control_surface.json"

OK = 0
FAIL = 2


def shard(tmp_path, name: str, **fields) -> Path:
    body = {"schema": "secb.control-shard/v1"}
    body.update(fields)
    path = tmp_path / f"{name}.json"
    path.write_text(json.dumps(body), encoding="utf-8")
    return path


def control(tmp_path, name, ident=None, path_=None, **extra):
    fields = {"kind": "CONTROL", "id": ident or name,
              "path": path_ or f"scripts/{name}.py", "sha256": "a" * 64, "bytes": 10,
              "portability_class": "configure",
              "staleness_consequence": "None derivable."}
    fields.update(extra)
    return shard(tmp_path, name, **fields)


def run(shard_dir, mode="AGGREGATE", monolith=None) -> subprocess.CompletedProcess:
    env = {"PATH": "/usr/bin:/bin", "SHARD_DIR": str(shard_dir), "MODE": mode,
           "MONOLITH": str(monolith or MONOLITH)}
    return subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True,
                          cwd=str(REPO_ROOT), env=env, timeout=60)


def aggregate(shard_dir, **kw) -> dict:
    result = run(shard_dir, **kw)
    assert result.returncode == OK, result.stderr
    return json.loads(result.stdout)


# --- determinism --------------------------------------------------------------


def test_the_aggregate_is_ordered_by_id_not_by_filesystem(tmp_path):
    """Ordering drift would change the digest without changing the content."""
    control(tmp_path, "zebra")
    control(tmp_path, "alpha")
    document = aggregate(tmp_path)
    assert [c["id"] for c in document["controls"]] == ["alpha", "zebra"]


def test_the_root_digest_is_stable_across_runs_and_file_order(tmp_path):
    control(tmp_path, "alpha")
    control(tmp_path, "zebra")
    first = aggregate(tmp_path)["registry_root_digest"]
    (tmp_path / "alpha.json").rename(tmp_path / "zzz_alpha.json")
    assert aggregate(tmp_path)["registry_root_digest"] == first


def test_a_content_change_moves_the_root_digest(tmp_path):
    control(tmp_path, "alpha")
    before = aggregate(tmp_path)["registry_root_digest"]
    control(tmp_path, "alpha", sha256="b" * 64)
    assert aggregate(tmp_path)["registry_root_digest"] != before


def test_there_is_no_hand_maintained_index(tmp_path):
    """The aggregate is derived by enumeration; an index could disagree with reality."""
    control(tmp_path, "alpha")
    document = aggregate(tmp_path)
    assert len(document["controls"]) == 1
    control(tmp_path, "beta")
    assert len(aggregate(tmp_path)["controls"]) == 2, (
        "adding a shard file must be sufficient; nothing else is edited"
    )


# --- golden negatives ---------------------------------------------------------


def test_duplicate_ids_are_refused(tmp_path):
    control(tmp_path, "one", ident="same", path_="scripts/a.py")
    control(tmp_path, "two", ident="same", path_="scripts/b.py")
    result = run(tmp_path)
    assert result.returncode == FAIL
    assert "duplicate id" in result.stderr
    assert "not a merge to resolve by hand" in result.stderr


def test_duplicate_paths_are_refused(tmp_path):
    control(tmp_path, "one", ident="one", path_="scripts/same.py")
    control(tmp_path, "two", ident="two", path_="scripts/same.py")
    result = run(tmp_path)
    assert result.returncode == FAIL
    assert "duplicate path" in result.stderr


def test_a_tombstone_without_a_superseded_digest_is_refused(tmp_path):
    """Silent closure: a removal that names nothing cannot be checked against anything."""
    shard(tmp_path, "gone", kind="TOMBSTONE", id="gone", path="scripts/gone.py")
    result = run(tmp_path)
    assert result.returncode == FAIL
    assert "must name the digest it retires" in result.stderr


def test_a_tombstone_with_its_digest_is_recorded(tmp_path):
    shard(tmp_path, "gone", kind="TOMBSTONE", id="gone", path="scripts/gone.py",
          supersedes_digest="c" * 64, retired_reason="folded into another control",
          retired_by_work_package="SECB-WP-FWK-084")
    document = aggregate(tmp_path)
    assert document["tombstones"][0]["supersedes_digest"] == "c" * 64


def test_an_unknown_kind_is_refused(tmp_path):
    shard(tmp_path, "odd", kind="SOMETHING", id="odd", path="scripts/odd.py")
    result = run(tmp_path)
    assert result.returncode == FAIL
    assert "unknown kind" in result.stderr


def test_a_foreign_schema_is_refused(tmp_path):
    path = tmp_path / "foreign.json"
    path.write_text(json.dumps({"schema": "something.else/v1", "kind": "CONTROL",
                                "id": "x", "path": "scripts/x.py"}), encoding="utf-8")
    result = run(tmp_path)
    assert result.returncode == FAIL
    assert "not a secb.control-shard/v1" in result.stderr


def test_an_absent_shard_directory_is_refused(tmp_path):
    result = run(tmp_path / "nope")
    assert result.returncode == FAIL
    assert "does not exist" in result.stderr


# --- canonicalisation is a named subset ---------------------------------------


def test_a_float_is_refused_rather_than_guessed(tmp_path):
    """RFC 8785 specifies ECMAScript number serialisation; this subset does not implement it.

    Formatting a float some other way yields a digest reproducible only by this tool, which
    is the opposite of the point. Naming the subset and refusing is the honest option the
    issue requires.
    """
    control(tmp_path, "alpha", weight=1.5)
    result = run(tmp_path)
    assert result.returncode == FAIL
    assert "floating-point" in result.stderr
    assert "secb.jcs-subset/v1" in result.stderr


def test_the_aggregate_names_its_canonicalisation_subset(tmp_path):
    control(tmp_path, "alpha")
    assert aggregate(tmp_path)["canonicalisation"] == "secb.jcs-subset/v1", (
        "claiming full JCS while implementing part of it is the overclaim this framework "
        "exists to catch"
    )


# --- dual read, single authority ----------------------------------------------


def test_equivalence_keeps_the_monolith_authoritative(tmp_path):
    control(tmp_path, "alpha")
    findings = json.loads(run(tmp_path, mode="PROVE_EQUIVALENCE").stdout)
    assert findings["authoritative_view"] == "MONOLITH"
    assert findings["shard_view"] == "NON_AUTHORITATIVE"
    assert findings["authority_flip_permitted"] is False
    assert "queue contention" in findings["authority_flip_blocked_by"]


def test_divergence_between_the_views_is_reported_not_reconciled(tmp_path):
    control(tmp_path, "alpha", path_="scripts/not_in_monolith.py")
    result = run(tmp_path, mode="PROVE_EQUIVALENCE")
    assert result.returncode == FAIL
    findings = json.loads(result.stdout)
    assert findings["verdict"] == "VIEWS_DIVERGED"
    assert "scripts/not_in_monolith.py" in findings["controls_only_in_shards"]
    assert findings["controls_only_in_monolith"], (
        "the monolith's entries must be reported as missing from the shard view too; a "
        "one-directional comparison would call an empty shard set equivalent"
    )


def test_a_faithful_shard_set_proves_equivalent_to_the_monolith(tmp_path):
    """The accept path, generated from the authoritative view."""
    monolith = json.loads(MONOLITH.read_text(encoding="utf-8"))
    for index, entry in enumerate(monolith["controls"]):
        shard(tmp_path, f"c{index}", kind="CONTROL", id=f"c{index}", path=entry["path"],
              sha256=entry["sha256"], portability_class=entry["portability_class"],
              staleness_consequence=entry["staleness_consequence"])
    for index, entry in enumerate(monolith["declared_exclusions"]):
        shard(tmp_path, f"e{index}", kind="EXCLUSION", id=f"e{index}", path=entry["path"],
              reason=entry["reason"], trigger_to_cover=entry["trigger_to_cover"],
              why_declared=entry["why_declared"])
    result = run(tmp_path, mode="PROVE_EQUIVALENCE")
    assert result.returncode == OK, result.stdout
    findings = json.loads(result.stdout)
    assert findings["verdict"] == "VIEWS_EQUIVALENT"
    assert findings["equivalent"] is True
