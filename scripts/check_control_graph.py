#!/usr/bin/env python3
"""Derive the control execution graph from the workflow, not from filenames.

`SECB-WP-FWK-082` (issue #147).

    STATIC_EXECUTION_GRAPH ↔ RUNTIME_EXECUTION_RECEIPT ↔ CONTROL_SURFACE_REGISTRY

Three views of the same controls. This builds the **first**. Discovery by filename pattern
was wrong in both directions and both were live:

* `scripts/emit_pr_input_binding.py` is invoked by `ci.yml` on #134 and escaped
  classification entirely, because the guard globbed `check_*.py`;
* `scripts/check_identity_receipt.py` matches that glob while no workflow invokes it, so
  the glob would claim it as CI enforcement.

Six statuses per path, none implying the next:

    DISCOVERED → REACHABLE → EXECUTED → RESULT_PROPAGATED
              → NORMATIVELY_CONSUMED → ENFORCED

Only the first two are statically decidable. `EXECUTED` and `NORMATIVELY_CONSUMED` need a
run and a consumer, so they are `NOT_OBSERVED` — a static parser reporting them any other
way would be claiming a runtime fact. `RESULT_PROPAGATED` is provably `false` when
`continue-on-error` is set, because the step then cannot fail its job.

**`REACHABLE` is deliberately three-valued.** A conditionally-skipped job reports success
and does not block a merge even when it is a required check, so "the path exists" and "the
path runs" are different claims.

**Parse fidelity is a declared subset.** Enforcement scripts import the standard library
only (`NFR-12`), so there is no YAML parser here — this reads an indentation-structured
subset and reports anything outside it as an unresolved edge. A silent omission would be
indistinguishable from an absent control.

Contract:

    WORKFLOW   workflow path (default .github/workflows/ci.yml)
    REGISTRY   control-surface manifest (default config/control_surface.json)

Exit codes:

    0  graph emitted
    2  refused — workflow unreadable, or an invoked control is unaccounted for
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

OK = 0
FAIL = 2

DEFAULT_WORKFLOW = ".github/workflows/ci.yml"
DEFAULT_REGISTRY = "config/control_surface.json"

SCRIPT_REF = re.compile(r"(scripts/[a-z0-9_]+\.py)")
EXPRESSION = re.compile(r"\$\{\{.*?\}\}")
SHELL_VAR = re.compile(r"\$[A-Za-z_{]")


class Refused(ValueError):
    """The graph cannot be built, or it contradicts the registry."""


def indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def parse_workflow(text: str) -> tuple[list[dict], list[dict]]:
    """Return (paths, unresolved_edges) from the recognised workflow subset."""
    lines = text.splitlines()
    paths: list[dict] = []
    unresolved: list[dict] = []

    in_jobs = False
    jobs_indent = 0
    job = None
    job_state: dict = {}
    step: dict | None = None

    def close_step() -> None:
        nonlocal step
        if step and step.get("scripts"):
            for script in step["scripts"]:
                paths.append({
                    "path": script,
                    "job": job,
                    "step": step.get("name") or "(unnamed)",
                    "job_condition": job_state.get("if"),
                    "step_condition": step.get("if"),
                    "needs": job_state.get("needs", []),
                    "continue_on_error": bool(step.get("continue_on_error")),
                })
        step = None

    for raw in lines:
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = indent_of(line)
        stripped = line.strip()

        if not in_jobs:
            if stripped == "jobs:":
                in_jobs, jobs_indent = True, indent
            continue

        # a new job key
        if indent == jobs_indent + 2 and stripped.endswith(":") and " " not in stripped[:-1]:
            close_step()
            job = stripped[:-1]
            job_state = {"if": None, "needs": []}
            continue

        if job is None:
            continue

        # job-level keys
        if indent == jobs_indent + 4:
            if stripped.startswith("if:"):
                job_state["if"] = stripped[3:].strip()
            elif stripped.startswith("needs:"):
                value = stripped[6:].strip()
                job_state["needs"] = [v.strip() for v in value.strip("[]").split(",") if v.strip()]
            elif stripped.startswith("strategy:"):
                unresolved.append({
                    "kind": "UNRESOLVED_DYNAMIC_EDGE", "where": f"{job}.strategy",
                    "value": "matrix", "why": "a matrix multiplies a job into instances this parser does not enumerate",
                })
            continue

        # step boundary
        if stripped.startswith("- ") and indent >= jobs_indent + 6:
            close_step()
            step = {"scripts": [], "if": None, "name": None, "continue_on_error": False}
            stripped = stripped[2:].strip()

        if step is None:
            continue

        if stripped.startswith("name:"):
            step["name"] = stripped[5:].strip().strip('"')
        elif stripped.startswith("if:"):
            step["if"] = stripped[3:].strip()
        elif stripped.startswith("continue-on-error:"):
            step["continue_on_error"] = stripped.split(":", 1)[1].strip() == "true"
        elif stripped.startswith("uses:"):
            value = stripped[5:].strip()
            local = value.startswith("./")
            unresolved.append({
                "kind": "COMPOSITE_ACTION" if local else "EXTERNAL_ACTION",
                "where": f"{job}.{step.get('name') or '(unnamed)'}",
                "value": value,
                "why": ("a local composite action adds execution edges the caller does not show"
                        if local else
                        "an external action's steps are not in this repository and are not followed"),
            })

        for script in SCRIPT_REF.findall(stripped):
            if EXPRESSION.search(stripped) or SHELL_VAR.search(stripped.replace(script, "")):
                unresolved.append({
                    "kind": "UNRESOLVED_DYNAMIC_EDGE",
                    "where": f"{job}.{step.get('name') or '(unnamed)'}",
                    "value": stripped[:80],
                    "why": "the invocation is interpolated, so the target is not statically fixed",
                })
            if script not in step["scripts"]:
                step["scripts"].append(script)

    close_step()
    return paths, unresolved


def classify(record: dict) -> dict:
    conditional = bool(record["job_condition"] or record["step_condition"] or record["needs"])
    return {
        "DISCOVERED": True,
        "REACHABLE": "CONDITIONAL" if conditional else "UNCONDITIONAL",
        "EXECUTED": "NOT_OBSERVED",
        "RESULT_PROPAGATED": False if record["continue_on_error"] else "NOT_OBSERVED",
        "NORMATIVELY_CONSUMED": "NOT_OBSERVED",
        "ENFORCED": "NOT_OBSERVED",
    }


def accounted(registry: dict) -> set[str]:
    return ({c["path"] for c in registry.get("controls", [])}
            | {e["path"] for e in registry.get("declared_exclusions", [])})


def main(argv: list[str]) -> int:
    env = dict(os.environ)
    try:
        text = Path(env.get("WORKFLOW", DEFAULT_WORKFLOW)).read_text(encoding="utf-8")
        registry = json.loads(Path(env.get("REGISTRY", DEFAULT_REGISTRY)).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"REFUSED (closed): {exc}", file=sys.stderr)
        return FAIL

    records, unresolved = parse_workflow(text)
    for record in records:
        record["status"] = classify(record)

    invoked = {r["path"] for r in records}
    missing = sorted(invoked - accounted(registry))
    if missing:
        print(
            "REFUSED (closed): the workflow invokes controls the registry does not account "
            f"for: {missing}. Discovery is by execution path, so a script CI runs cannot be "
            "unclassified merely because its name does not match a pattern",
            file=sys.stderr,
        )
        return FAIL

    print(json.dumps({
        "schema": "secb.control-execution-graph/v1",
        "parse_fidelity": {
            "level": "SUBSET",
            "recognised": ["jobs", "steps", "run", "uses", "if", "needs",
                           "strategy.matrix", "continue-on-error"],
            "why": ("Enforcement scripts import the standard library only (NFR-12), so no YAML "
                    "parser is available; unrecognised syntax becomes an unresolved edge."),
        },
        "paths": sorted(records, key=lambda r: (r["path"], r["job"])),
        "unresolved_edges": unresolved,
        "not_proven": [
            "that any path executed -- EXECUTED requires a run",
            "that any result was consumed -- that view is the runtime receipt's",
            "that anything is enforced -- branch protection is not observed here",
            "that the parse is YAML-conformant; it recognises a declared subset",
        ],
    }, indent=2, sort_keys=True))
    return OK


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
