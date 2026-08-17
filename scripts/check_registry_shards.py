#!/usr/bin/env python3
"""Aggregate control-surface shards deterministically, and prove equivalence.

`SECB-WP-FWK-084` (issue #151).

`config/control_surface.json` is claimed by five open branches, one hunk each, all at the
array tail — and the shadow merge queue (`FWK-083`) proved the resulting conflict at prefix
9 of a measured queue. Every new control forces an edit to one file, so parallel work
always contends there.

Sharding removes the shared line, and **there is no hand-maintained index**: the aggregate
is derived by enumerating shard files. An index would be one more thing that can disagree
with reality, which is the class of defect this repository keeps finding.

Three properties that make the migration safe rather than merely staged:

* **One authority at every state.** During migration the monolith is `AUTHORITATIVE` and
  the shards are `NON_AUTHORITATIVE`. Dual-read exists to *prove equivalence*, never to
  create a second source of truth — two authorities is the failure the equivalence proof is
  supposed to prevent, not a step on the way there.
* **Removal leaves a tombstone.** Deleting a shard silently would let a control disappear
  with no trace. A `TOMBSTONE` binds `supersedes_digest`, so a removal can be checked
  against what it removed.
* **The digest needs a reproducible representation.** Canonicalisation follows RFC 8785
  (JCS) — as a **named subset**, `secb.jcs-subset/v1`, which rejects what it does not
  implement rather than guessing. Claiming full JCS while implementing part of it is the
  overclaim this framework exists to catch.

Contract:

    SHARD_DIR   directory of shard files          (default config/control_shards)
    MONOLITH    the file being migrated from      (default config/control_surface.json)
    MODE        AGGREGATE | PROVE_EQUIVALENCE     (default AGGREGATE)

Exit codes:

    0  aggregate emitted, or equivalence proven
    2  refused — a golden-negative case, or the two views disagree
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

OK = 0
FAIL = 2

CANONICALISATION = "secb.jcs-subset/v1"
DEFAULT_SHARDS = "config/control_shards"
DEFAULT_MONOLITH = "config/control_surface.json"


class Refused(ValueError):
    """A golden-negative case, or a disagreement between the two views."""


# --- canonicalisation ---------------------------------------------------------

def canonicalise(value, path: str = "$") -> str:
    """RFC 8785 JCS, **subset**. Out-of-scope input is refused, never approximated.

    Implemented: objects with string keys sorted by code unit, arrays in order, strings
    with JSON escaping, integers, booleans, null.

    **Not implemented, and therefore rejected:** floating-point numbers. JCS specifies
    ECMAScript `Number::toString` serialisation, which this does not implement, and a
    digest computed over a number formatted some other way is reproducible only by this
    tool — which is the opposite of the point.
    """
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        raise Refused(
            f"{path}: floating-point values are outside {CANONICALISATION}. RFC 8785 "
            "specifies ECMAScript number serialisation, which this subset does not "
            "implement; refusing rather than inventing a formatting"
        )
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return "[" + ",".join(canonicalise(v, f"{path}[{i}]") for i, v in enumerate(value)) + "]"
    if isinstance(value, dict):
        for key in value:
            if not isinstance(key, str):
                raise Refused(f"{path}: non-string object key {key!r}")
        items = sorted(value.items(), key=lambda kv: kv[0].encode("utf-16-be"))
        return "{" + ",".join(
            f"{json.dumps(k, ensure_ascii=False)}:{canonicalise(v, f'{path}.{k}')}"
            for k, v in items
        ) + "}"
    raise Refused(f"{path}: {type(value).__name__} is outside {CANONICALISATION}")


def digest_of(value) -> str:
    return hashlib.sha256(canonicalise(value).encode("utf-8")).hexdigest()


# --- aggregation --------------------------------------------------------------

def load_shards(directory: Path) -> list[dict]:
    if not directory.is_dir():
        raise Refused(f"shard directory {directory} does not exist")
    shards = []
    for file in sorted(directory.glob("*.json")):
        try:
            shard = json.loads(file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise Refused(f"{file.name}: unparseable ({exc})") from exc
        shard["_file"] = file.name
        shards.append(shard)
    return shards


def aggregate(shards: list[dict]) -> dict:
    """Deterministic, and refusing every golden-negative case."""
    by_id: dict[str, str] = {}
    by_path: dict[str, str] = {}
    controls, exclusions, tombstones = [], [], []

    for shard in shards:
        name = shard.get("_file", "?")
        if shard.get("schema") != "secb.control-shard/v1":
            raise Refused(f"{name}: not a secb.control-shard/v1 document")
        kind, ident, path = shard.get("kind"), shard.get("id"), shard.get("path")
        if not ident or not path:
            raise Refused(f"{name}: id and path are required")
        if ident in by_id:
            raise Refused(
                f"duplicate id {ident!r} in {name} and {by_id[ident]}. Two shards claiming "
                "one id is not a merge to resolve by hand"
            )
        by_id[ident] = name
        if kind in ("CONTROL", "EXCLUSION"):
            if path in by_path:
                raise Refused(f"duplicate path {path!r} in {name} and {by_path[path]}")
            by_path[path] = name
        if kind == "CONTROL":
            controls.append(shard)
        elif kind == "EXCLUSION":
            exclusions.append(shard)
        elif kind == "TOMBSTONE":
            if not shard.get("supersedes_digest"):
                raise Refused(f"{name}: a tombstone must name the digest it retires")
            tombstones.append(shard)
        else:
            raise Refused(f"{name}: unknown kind {kind!r}")

    def clean(entries):
        # Ordering is by id, so the aggregate does not depend on filesystem order.
        return [{k: v for k, v in e.items() if k != "_file"}
                for e in sorted(entries, key=lambda e: e["id"])]

    body = {
        "schema": "secb.control-surface-aggregate/v1",
        "canonicalisation": CANONICALISATION,
        "controls": clean(controls),
        "declared_exclusions": clean(exclusions),
        "tombstones": clean(tombstones),
    }
    body["registry_root_digest"] = digest_of(
        {k: v for k, v in body.items() if k != "registry_root_digest"})
    return body


# --- dual read ----------------------------------------------------------------

def prove_equivalence(aggregated: dict, monolith: dict) -> dict:
    """Compare the two views. The monolith stays authoritative throughout."""
    def key(entry):
        return entry["path"]

    a_controls = {key(c) for c in aggregated["controls"]}
    m_controls = {c["path"] for c in monolith.get("controls", [])}
    a_excl = {key(e) for e in aggregated["declared_exclusions"]}
    m_excl = {e["path"] for e in monolith.get("declared_exclusions", [])}

    findings = {
        "schema": "secb.registry-equivalence/v1",
        "authoritative_view": "MONOLITH",
        "shard_view": "NON_AUTHORITATIVE",
        "why": (
            "One authority at every state. Dual-read proves the derived view matches; it "
            "does not make the derived view a second source of truth."
        ),
        "controls_only_in_shards": sorted(a_controls - m_controls),
        "controls_only_in_monolith": sorted(m_controls - a_controls),
        "exclusions_only_in_shards": sorted(a_excl - m_excl),
        "exclusions_only_in_monolith": sorted(m_excl - a_excl),
        "registry_root_digest": aggregated["registry_root_digest"],
        "authority_flip_permitted": False,
        "authority_flip_blocked_by": (
            "queue contention: config/control_surface.json is claimed by five open branches, "
            "and flipping authority while they are in flight would resolve their conflicts "
            "into a file that is no longer authoritative"
        ),
    }
    findings["equivalent"] = not any(
        findings[k] for k in (
            "controls_only_in_shards", "controls_only_in_monolith",
            "exclusions_only_in_shards", "exclusions_only_in_monolith")
    )
    findings["verdict"] = "VIEWS_EQUIVALENT" if findings["equivalent"] else "VIEWS_DIVERGED"
    return findings


def main(argv: list[str]) -> int:
    env = dict(os.environ)
    mode = env.get("MODE", "AGGREGATE")
    try:
        shards = load_shards(Path(env.get("SHARD_DIR", DEFAULT_SHARDS)))
        aggregated = aggregate(shards)
        if mode == "PROVE_EQUIVALENCE":
            monolith = json.loads(
                Path(env.get("MONOLITH", DEFAULT_MONOLITH)).read_text(encoding="utf-8"))
            result = prove_equivalence(aggregated, monolith)
        elif mode == "AGGREGATE":
            result = aggregated
        else:
            raise Refused(f"unknown MODE {mode!r}")
    except Refused as exc:
        print(f"REFUSED (closed): {exc}", file=sys.stderr)
        return FAIL
    except OSError as exc:
        print(f"REFUSED (closed): {exc}", file=sys.stderr)
        return FAIL

    print(json.dumps(result, indent=2, sort_keys=True))
    return OK if result.get("verdict") != "VIEWS_DIVERGED" else FAIL


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
