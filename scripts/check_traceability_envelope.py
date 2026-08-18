"""Enforce the End-to-End Traceability Envelope (FWK-101, P0 item 5 -- the Evidence Object).

WHY THIS RATHER THAN A NEW SCHEMA. `docs/13-evidence/END_TO_END_TRACEABILITY.schema.json` already
defines the evidence graph the loop design asks for: nineteen node types, nine relationships, a
sealed root. Two things were true of it before this file existed:

    nothing validated it            SCHEMA_EXISTS != SCHEMA_ENFORCED
    root_sha256 was undefined       SEALED_FIELD != COMPUTABLE_FIELD

The second is the sharper one. A sealed envelope whose root nobody can recompute is a label, not a
seal -- there was no rule by which anyone could produce a conforming value or detect a mutated one.
Writing a competing schema would have left the original dormant and created a second source of
truth, which the framework's own deduplication rule prohibits. This activates what exists.

THE CANONICALISATION, DEFINED HERE BECAUSE IT WAS NOWHERE

    root_sha256 = sha256(canonical_json({
        "nodes": [{id, producer, sha256, timestamp, type}, ...] sorted by id,
        "edges": [{from, relationship, to}, ...]              sorted by (from, to, relationship),
    }))

    canonical_json = UTF-8, keys sorted, separators (',', ':'), no trailing newline

Sorting is what makes the root a property of the GRAPH rather than of the file's line order: two
writers recording the same evidence must produce the same root, or the root cannot detect mutation.

WHAT A NODE DIGEST DOES AND DOES NOT PROVE. The schema fixes a node to five fields, so a node
cannot declare whether its `sha256` is over retrievable content or over an identifier. For a commit
or a workflow run, the digest is necessarily over the IDENTIFIER -- the object is not stored in the
envelope. That proves the identifier was recorded, not that the artifact still exists or is
unchanged.

    IDENTITY_DIGEST != CONTENT_DIGEST

The validator therefore verifies graph integrity and seal integrity; artifact resolvability is the
reconciler's UNVERIFIABLE_RELEASE class, not this one.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path

OK = 0
FAIL = 2

SCHEMA_PATH = "docs/13-evidence/END_TO_END_TRACEABILITY.schema.json"
NODE_FIELDS = ("id", "producer", "sha256", "timestamp", "type")
EDGE_FIELDS = ("from", "relationship", "to")
SHA256 = re.compile(r"^[a-f0-9]{64}$")


class Refused(ValueError):
    """The envelope is not a coherent, sealed evidence graph."""


def canonical(payload: object) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def compute_root(nodes: list[dict], edges: list[dict]) -> str:
    """The rule this file defines. Sorted, so the root describes the graph and not the file."""
    body = {
        "nodes": sorted(({k: n[k] for k in NODE_FIELDS} for n in nodes),
                        key=lambda n: n["id"]),
        "edges": sorted(({k: e[k] for k in EDGE_FIELDS} for e in edges),
                        key=lambda e: (e["from"], e["to"], e["relationship"])),
    }
    return hashlib.sha256(canonical(body)).hexdigest()


def load_schema(root: Path) -> dict:
    try:
        return json.loads((root / SCHEMA_PATH).read_text(encoding="utf-8"))
    except OSError as exc:
        raise Refused(f"the traceability schema is unreadable at {SCHEMA_PATH} ({exc})") from exc


def check_against_schema(envelope: dict, schema: dict) -> None:
    """The subset the envelope schema uses: required, const, enum, pattern, minItems, type."""
    for field in schema["required"]:
        if field not in envelope:
            raise Refused(f"envelope is missing required field {field!r}")
    if envelope["schema_version"] != schema["properties"]["schema_version"]["const"]:
        raise Refused(f"schema_version {envelope['schema_version']!r} is not the declared const")
    wp_pattern = schema["properties"]["work_package_id"]["pattern"]
    if not re.match(wp_pattern, envelope["work_package_id"]):
        raise Refused(f"work_package_id {envelope['work_package_id']!r} does not match {wp_pattern}")

    node_types = set(schema["properties"]["nodes"]["items"]["properties"]["type"]["enum"])
    edge_rels = set(schema["properties"]["edges"]["items"]["properties"]["relationship"]["enum"])
    if not envelope["nodes"]:
        raise Refused("an envelope with no nodes traces nothing")
    if not envelope["edges"]:
        raise Refused("an envelope with no edges records artifacts, not traceability")

    for node in envelope["nodes"]:
        missing = [f for f in NODE_FIELDS if f not in node]
        if missing:
            raise Refused(f"node {node.get('id', '?')!r} is missing {missing}")
        if node["type"] not in node_types:
            raise Refused(f"node {node['id']!r}: type {node['type']!r} is not a declared type")
        if not SHA256.match(node["sha256"]):
            raise Refused(f"node {node['id']!r}: sha256 is not 64 lowercase hex")
    for edge in envelope["edges"]:
        missing = [f for f in EDGE_FIELDS if f not in edge]
        if missing:
            raise Refused(f"an edge is missing {missing}")
        if edge["relationship"] not in edge_rels:
            raise Refused(f"edge {edge['from']}->{edge['to']}: unknown relationship")


def check_graph(envelope: dict) -> dict:
    ids: dict[str, dict] = {}
    for node in envelope["nodes"]:
        if node["id"] in ids:
            raise Refused(f"duplicate node id {node['id']!r}; a graph cannot have two of one node")
        ids[node["id"]] = node

    adjacency: dict[str, list[str]] = {i: [] for i in ids}
    for edge in envelope["edges"]:
        for end in ("from", "to"):
            if edge[end] not in ids:
                raise Refused(
                    f"edge references {edge[end]!r}, which is not a node. A dangling edge is a "
                    "traceability claim to something the envelope does not contain"
                )
        adjacency[edge["from"]].append(edge["to"])

    # Acyclicity. SUPERSEDES and DERIVED_FROM can close a loop, and a cycle means the evidence
    # graph asserts that something derives from itself.
    WHITE, GREY, BLACK = 0, 1, 2
    colour = {i: WHITE for i in ids}

    def visit(start: str) -> None:
        stack = [(start, iter(adjacency[start]))]
        colour[start] = GREY
        while stack:
            node, children = stack[-1]
            advanced = False
            for child in children:
                if colour[child] == GREY:
                    raise Refused(
                        f"the graph contains a cycle through {child!r}; evidence cannot derive "
                        "from itself"
                    )
                if colour[child] == WHITE:
                    colour[child] = GREY
                    stack.append((child, iter(adjacency[child])))
                    advanced = True
                    break
            if not advanced:
                colour[node] = BLACK
                stack.pop()

    for identifier in ids:
        if colour[identifier] == WHITE:
            visit(identifier)

    connected = {e["from"] for e in envelope["edges"]} | {e["to"] for e in envelope["edges"]}
    orphans = sorted(set(ids) - connected)
    if orphans:
        raise Refused(
            f"nodes {orphans} participate in no edge. An unconnected node is an artifact the "
            "envelope mentions but does not trace"
        )
    return ids


def validate(root: Path, envelope: dict) -> dict:
    schema = load_schema(root)
    check_against_schema(envelope, schema)
    ids = check_graph(envelope)

    recomputed = compute_root(envelope["nodes"], envelope["edges"])
    if recomputed != envelope["root_sha256"]:
        raise Refused(
            f"root_sha256 recomputes to {recomputed[:16]}… but the envelope records "
            f"{envelope['root_sha256'][:16]}…. A sealed envelope whose root does not recompute has "
            "been mutated, or was sealed under a different rule than the one this validator "
            "defines -- either way it is not verifiable as sealed"
        )

    kinds: dict[str, int] = {}
    for node in envelope["nodes"]:
        kinds[node["type"]] = kinds.get(node["type"], 0) + 1
    return {
        "schema": "secb.traceability-observation/v1",
        "verdict": "ENVELOPE_SEALED_AND_COHERENT",
        "work_package_id": envelope["work_package_id"],
        "episode_id": envelope["episode_id"],
        "nodes": len(ids),
        "edges": len(envelope["edges"]),
        "node_types": kinds,
        "root_sha256": envelope["root_sha256"],
        "sealed_at": envelope["sealed_at"],
        "sealed_by": envelope["sealed_by"],
        "not_proven": [
            "that any node's artifact still exists or is unchanged; a node digest over an "
            "identifier proves the identifier (IDENTITY_DIGEST != CONTENT_DIGEST)",
            "that the graph is COMPLETE; it proves the recorded graph is coherent and sealed",
            "that sealed_by is who they claim to be; this validator checks no signature",
        ],
        "confers_merge_authority": False,
    }


def main(argv: list[str]) -> int:
    path = os.environ.get("ENVELOPE_FILE", "").strip()
    if not path:
        print("REFUSED (closed): ENVELOPE_FILE is required", file=sys.stderr)
        return FAIL
    root = Path(os.environ.get("REPO_ROOT", ".")).resolve()
    try:
        report = validate(root, json.loads(Path(path).read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"REFUSED (closed): envelope unreadable ({exc})", file=sys.stderr)
        return FAIL
    except Refused as exc:
        print(f"REFUSED (closed): {exc}", file=sys.stderr)
        return FAIL
    except (KeyError, TypeError, AttributeError) as exc:
        print(f"REFUSED (closed): malformed envelope ({exc!r})", file=sys.stderr)
        return FAIL
    print(json.dumps(report, indent=2, sort_keys=True))
    return OK


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
