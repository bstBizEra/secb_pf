"""SECB-WP-FWK-101 -- activating the End-to-End Traceability Envelope (P0 item 5).

The schema at docs/13-evidence/END_TO_END_TRACEABILITY.schema.json predates this work package. Two
things were true of it: nothing validated it, and `root_sha256` had no defined computation, so no
one could produce a conforming value or detect a mutated one.

    SCHEMA_EXISTS != SCHEMA_ENFORCED
    SEALED_FIELD != COMPUTABLE_FIELD

Extending the dormant schema rather than writing a rival is the deduplication rule applied: a
second evidence schema would have left the first inert and created two sources of truth.
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "scripts" / "check_traceability_envelope.py"
REAL = ROOT / "evidence" / "traceability" / "SECB-WP-FWK-091.json"
SCHEMA = ROOT / "docs" / "13-evidence" / "END_TO_END_TRACEABILITY.schema.json"

sys.path.insert(0, str(ROOT / "scripts"))
from check_traceability_envelope import compute_root  # noqa: E402


def envelope() -> dict:
    return json.loads(REAL.read_text(encoding="utf-8"))


def reseal(body: dict) -> dict:
    body["root_sha256"] = compute_root(body["nodes"], body["edges"])
    return body


def run(body: dict, tmp_path: Path) -> subprocess.CompletedProcess:
    path = tmp_path / "envelope.json"
    path.write_text(json.dumps(body), encoding="utf-8")
    return subprocess.run([sys.executable, str(TOOL)], capture_output=True, text=True,
                          env={**os.environ, "ENVELOPE_FILE": str(path), "REPO_ROOT": str(ROOT),
                               "PYTHONDONTWRITEBYTECODE": "1"}, check=False)


def refuses(body: dict, tmp_path: Path, fragment: str) -> str:
    result = run(body, tmp_path)
    assert result.returncode == 2, result.stdout
    assert fragment in result.stderr, result.stderr
    return result.stderr


# ------------------------------------------------------------------- the real envelope


def test_the_shipped_envelope_is_sealed_and_coherent(tmp_path):
    result = run(envelope(), tmp_path)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["verdict"] == "ENVELOPE_SEALED_AND_COHERENT"
    assert report["work_package_id"] == "SECB-WP-FWK-091"
    assert report["nodes"] == 9 and report["edges"] == 9


def test_the_shipped_envelope_traces_a_real_landing(tmp_path):
    """Ticket through observation, for the one work package that ran the whole loop this cycle."""
    body = envelope()
    kinds = {n["type"] for n in body["nodes"]}
    for required in ("TICKET", "BRANCH", "PR", "CHECK", "REVIEW", "COMMIT", "OBSERVATION"):
        assert required in kinds, required
    rels = {e["relationship"] for e in body["edges"]}
    assert {"IMPLEMENTS", "VERIFIES", "APPROVES", "BUILT_FROM", "AUTHORIZES"} <= rels


def test_it_conforms_to_the_pre_existing_schema_not_a_new_one():
    """The envelope must satisfy the schema that was already in the repository."""
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    body = envelope()
    for field in schema["required"]:
        assert field in body, field
    node_types = set(schema["properties"]["nodes"]["items"]["properties"]["type"]["enum"])
    assert {n["type"] for n in body["nodes"]} <= node_types


# ------------------------------------------------------- the seal actually seals


def test_mutating_any_node_breaks_the_seal(tmp_path):
    """The property that makes `sealed` mean something."""
    body = envelope()
    body["nodes"][0]["producer"] = "someone-else"
    stderr = refuses(body, tmp_path, "root_sha256 recomputes to")
    assert "has been mutated" in stderr


def test_adding_an_edge_breaks_the_seal(tmp_path):
    body = envelope()
    body["edges"].append({"from": "OBS-LANDING", "to": "TICKET-162",
                          "relationship": "DERIVED_FROM"})
    refuses(body, tmp_path, "root_sha256 recomputes to")


def test_the_root_describes_the_graph_not_the_file_order(tmp_path):
    """Reordering nodes and edges must NOT change the root.

    Without sorting, two writers recording identical evidence would produce different roots, and
    the root could not distinguish a mutation from a re-serialisation.
    """
    body = envelope()
    shuffled = copy.deepcopy(body)
    shuffled["nodes"] = list(reversed(shuffled["nodes"]))
    shuffled["edges"] = list(reversed(shuffled["edges"]))
    assert compute_root(shuffled["nodes"], shuffled["edges"]) == body["root_sha256"]
    assert run(shuffled, tmp_path).returncode == 0


# ------------------------------------------------------------- graph integrity


def test_a_dangling_edge_is_refused(tmp_path):
    body = envelope()
    body["edges"].append({"from": "PR-163", "to": "GHOST", "relationship": "VERIFIES"})
    stderr = refuses(reseal(body), tmp_path, "which is not a node")
    assert "does not contain" in stderr


def test_a_cycle_is_refused(tmp_path):
    """Evidence cannot derive from itself."""
    body = envelope()
    body["edges"].append({"from": "TICKET-162", "to": "OBS-LANDING",
                          "relationship": "DERIVED_FROM"})
    refuses(reseal(body), tmp_path, "contains a cycle")


def test_an_orphan_node_is_refused(tmp_path):
    """A node in no edge is an artifact the envelope mentions but does not trace."""
    body = envelope()
    body["nodes"].append({"id": "LONELY", "type": "ARTIFACT", "sha256": "b" * 64,
                          "producer": "x", "timestamp": "2026-08-18T00:00:00Z"})
    refuses(reseal(body), tmp_path, "participate in no edge")


def test_a_duplicate_node_id_is_refused(tmp_path):
    body = envelope()
    body["nodes"].append(dict(body["nodes"][0]))
    refuses(reseal(body), tmp_path, "duplicate node id")


# ------------------------------------------------------------- schema conformance


def test_an_unknown_node_type_is_refused(tmp_path):
    body = envelope()
    body["nodes"][0]["type"] = "VIBES"
    refuses(reseal(body), tmp_path, "is not a declared type")


def test_an_unknown_relationship_is_refused(tmp_path):
    body = envelope()
    body["edges"][0]["relationship"] = "SORT_OF_RELATES_TO"
    refuses(reseal(body), tmp_path, "unknown relationship")


def test_a_malformed_node_digest_is_refused(tmp_path):
    body = envelope()
    body["nodes"][0]["sha256"] = "NOTHEX"
    refuses(reseal(body), tmp_path, "not 64 lowercase hex")


def test_a_bad_work_package_id_is_refused(tmp_path):
    body = envelope()
    body["work_package_id"] = "wp-1"
    refuses(reseal(body), tmp_path, "does not match")


@pytest.mark.parametrize("field", ["episode_id", "root_sha256", "sealed_at", "sealed_by", "nodes"])
def test_every_required_field_is_enforced(tmp_path, field):
    body = envelope()
    del body[field]
    refuses(body, tmp_path, "missing required field")


def test_an_envelope_with_no_edges_records_artifacts_not_traceability(tmp_path):
    body = envelope()
    body["edges"] = []
    refuses(body, tmp_path, "records artifacts, not traceability")


# ----------------------------------------------------------- declared limits


def test_the_report_states_what_a_node_digest_does_not_prove(tmp_path):
    """IDENTITY_DIGEST != CONTENT_DIGEST, stated rather than implied."""
    report = json.loads(run(envelope(), tmp_path).stdout)
    joined = " ".join(report["not_proven"])
    assert "IDENTITY_DIGEST != CONTENT_DIGEST" in joined
    assert "COMPLETE" in joined
    assert "signature" in joined
    assert report["confers_merge_authority"] is False


def test_a_missing_envelope_path_is_refused():
    result = subprocess.run([sys.executable, str(TOOL)], capture_output=True, text=True,
                            env={**os.environ, "ENVELOPE_FILE": "",
                                 "PYTHONDONTWRITEBYTECODE": "1"}, check=False)
    assert result.returncode == 2 and "ENVELOPE_FILE is required" in result.stderr
