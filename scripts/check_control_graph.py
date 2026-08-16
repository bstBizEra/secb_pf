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

Discovery is the **union over all tracked workflows**, not `ci.yml` alone:

    CONTROL DISCOVERY = UNION(EXECUTION EDGES OF ALL TRACKED WORKFLOWS)

`FWK-083` added a second workflow one pull request after this one, which would have been
invisible to a `ci.yml`-only parser. Every edge records its `workflow_path`, the same
script reached from two workflows is two edges and one membership obligation, and a
workflow that cannot be read is reported rather than skipped.

Four independent axes per path, because collapsing them is how a control comes to look
enforced when it is merely present:

    CONTROL_SURFACE_MEMBERSHIP ≠ CI_REACHABILITY ≠ RESULT_CONSUMPTION ≠ CI_ENFORCEMENT

`CI_REACHABILITY` never says *unconditional*. A step with no `if` still carries GitHub's
default `success()` condition, so a previous step's failure skips it — the absence of an
explicit condition is an observation about the file, not a guarantee about execution. The
values are `NO_EXPLICIT_CONDITION_OBSERVED`, `EXPLICIT_CONDITION_PRESENT`,
`STATICALLY_UNREACHABLE` and `REACHABILITY_NOT_PROVEN`.

`RESULT_CONSUMPTION` is split, because `continue-on-error` proves less than it appears to:
it establishes `DIRECT_JOB_FAILURE_PROPAGATION: false`, and a later step can still read
`steps.<id>.outcome`, so `DOWNSTREAM_RESULT_CONSUMPTION` stays `NOT_OBSERVED`.

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
ANCHOR_OR_ALIAS = re.compile(r"(^|\s)[&*][A-Za-z0-9_-]+|^\s*<<:")

# Keys this parser understands. Anything else inside a job or step is reported as
# UNRECOGNISED_SYNTAX rather than skipped -- silently ignoring a key means the parser
# cannot honestly say unknown syntax becomes an unresolved edge (C-CEG-02).
JOB_KEYS = {
    "name", "runs-on", "if", "needs", "steps", "strategy", "permissions", "env",
    "timeout-minutes", "outputs", "container", "services", "defaults", "concurrency",
    "continue-on-error", "uses", "with", "secrets", "environment",
}
STEP_KEYS = {
    "name", "if", "uses", "run", "with", "env", "id", "shell", "working-directory",
    "timeout-minutes", "continue-on-error",
}
EXPRESSION = re.compile(r"\$\{\{.*?\}\}")
SHELL_VAR = re.compile(r"\$[A-Za-z_{]")


class Refused(ValueError):
    """The graph cannot be built, or it contradicts the registry."""


def indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def parse_workflow(text: str) -> tuple[list[dict], list[dict]]:
    """Return (paths, unresolved_edges) over the recognised subset.

    Every line inside a job that this parser does not recognise becomes an
    `UNRECOGNISED_SYNTAX` edge and marks its job or step `parse_incomplete`, which forces
    reachability to `REACHABILITY_NOT_PROVEN`. Reporting only the unsupported syntax it
    happens to know about — while skipping the rest — is what made the earlier claim that
    "unknown syntax becomes an unresolved edge" untrue (`C-CEG-02`).

    YAML anchors and aliases are a real blind spot, not a hypothetical one: an alias can
    import an entire job, so an indentation parser can miss a whole execution path. They
    are detected and reported rather than silently mis-parsed.
    """
    paths: list[dict] = []
    unresolved: list[dict] = []

    in_jobs = False
    jobs_indent = 0
    job = None
    job_state: dict = {}
    step: dict | None = None
    step_key_indent: int | None = None
    block_indent: int | None = None

    def note(kind: str, where: str, value: str, why: str) -> None:
        unresolved.append({"kind": kind, "where": where, "value": value[:100], "why": why})

    def incomplete() -> None:
        if step is not None:
            step["parse_incomplete"] = True
        elif job_state:
            job_state["parse_incomplete"] = True

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
                    "parse_incomplete": bool(step.get("parse_incomplete")
                                             or job_state.get("parse_incomplete")),
                })
        step = None

    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = indent_of(line)
        stripped = line.strip()

        # inside a block scalar (run: |) the content is shell, not workflow syntax
        if block_indent is not None:
            if indent > block_indent:
                for script in SCRIPT_REF.findall(stripped):
                    if step is not None and script not in step["scripts"]:
                        step["scripts"].append(script)
                    if EXPRESSION.search(stripped) or SHELL_VAR.search(stripped.replace(script, "")):
                        note("UNRESOLVED_DYNAMIC_EDGE", f"{job}", stripped,
                             "the invocation is interpolated, so the target is not statically fixed")
                continue
            block_indent = None

        if ANCHOR_OR_ALIAS.search(line):
            note("YAML_ANCHOR_OR_ALIAS", f"{job or '(top level)'}", stripped,
                 "an anchor or alias can import an entire job; an indentation parser may "
                 "miss the execution path it introduces")
            incomplete()

        if not in_jobs:
            if stripped == "jobs:":
                in_jobs, jobs_indent = True, indent
            continue

        if indent == jobs_indent + 2 and stripped.endswith(":") and " " not in stripped[:-1]:
            close_step()
            job = stripped[:-1]
            job_state = {"if": None, "needs": [], "parse_incomplete": False}
            continue

        if job is None:
            continue

        key = stripped.split(":", 1)[0].lstrip("- ").strip() if ":" in stripped else None
        value = stripped.split(":", 1)[1].strip() if ":" in stripped else ""
        if value in ("|", ">", "|-", ">-", "|+", ">+"):
            block_indent = indent

        # job-level keys
        if indent == jobs_indent + 4 and step is None:
            if key not in JOB_KEYS:
                note("UNRECOGNISED_SYNTAX", f"{job}.{key}", stripped,
                     "the parser does not model this job key, so anything it implies about "
                     "execution is unknown")
                job_state["parse_incomplete"] = True
            elif key == "if":
                job_state["if"] = value
            elif key == "needs":
                job_state["needs"] = [v.strip() for v in value.strip("[]").split(",") if v.strip()]
            elif key == "strategy":
                note("UNRESOLVED_DYNAMIC_EDGE", f"{job}.strategy", "matrix",
                     "a matrix multiplies a job into instances this parser does not enumerate")
                job_state["parse_incomplete"] = True
            continue

        if stripped.startswith("- ") and indent >= jobs_indent + 6:
            close_step()
            step = {"scripts": [], "if": None, "name": None,
                    "continue_on_error": False, "parse_incomplete": False}
            # A step's own keys sit two columns right of the dash. Anything deeper is a
            # child of one of them -- `with:` and `env:` mappings especially -- and is not
            # a step key. Without this the parser flagged `python-version` and every env
            # var as unrecognised, forcing REACHABILITY_NOT_PROVEN on every path. A guard
            # that always says "not proven" is one nobody reads.
            step_key_indent = indent + 2
            stripped = stripped[2:].strip()
            key = stripped.split(":", 1)[0].strip() if ":" in stripped else None
            value = stripped.split(":", 1)[1].strip() if ":" in stripped else ""
            if value in ("|", ">", "|-", ">-"):
                block_indent = indent

        if step is None:
            continue

        # a child of a step key, not a step key
        if step_key_indent is not None and indent > step_key_indent:
            for script in SCRIPT_REF.findall(stripped):
                if script not in step["scripts"]:
                    step["scripts"].append(script)
            continue

        if key and key not in STEP_KEYS and block_indent is None:
            note("UNRECOGNISED_SYNTAX", f"{job}.step.{key}", stripped,
                 "the parser does not model this step key")
            step["parse_incomplete"] = True
        elif key == "name":
            step["name"] = value.strip('"')
        elif key == "if":
            step["if"] = value
        elif key == "continue-on-error":
            step["continue_on_error"] = value == "true"
        elif key == "uses":
            local = value.startswith("./")
            note("COMPOSITE_ACTION" if local else "EXTERNAL_ACTION",
                 f"{job}.{step.get('name') or '(unnamed)'}", value,
                 "a local composite action adds execution edges the caller does not show"
                 if local else
                 "an external action's steps are not in this repository and are not followed")

        for script in SCRIPT_REF.findall(stripped):
            if EXPRESSION.search(stripped) or SHELL_VAR.search(stripped.replace(script, "")):
                note("UNRESOLVED_DYNAMIC_EDGE", f"{job}.{step.get('name') or '(unnamed)'}",
                     stripped, "the invocation is interpolated, so the target is not statically fixed")
            if script not in step["scripts"]:
                step["scripts"].append(script)

    close_step()
    return paths, unresolved


def parse_all(directory: Path) -> tuple[list[dict], list[dict]]:
    """Every tracked workflow, deterministically ordered.

        CONTROL DISCOVERY = UNION(EXECUTION EDGES OF ALL TRACKED WORKFLOWS)
                          ≠ EXECUTION EDGES OF ci.yml ONLY

    The first version read `ci.yml` alone, so a control invoked only by a second workflow
    was invisible — and `FWK-083` added exactly such a workflow one pull request later,
    which is the golden-negative case below rather than a hypothetical.

    An unreadable workflow is **reported**, never skipped: a silent omission is
    indistinguishable from an absent control, and the file that cannot be parsed is the
    one most likely to be hiding something.
    """
    records: list[dict] = []
    unresolved: list[dict] = []
    files = sorted(list(directory.glob("*.yml")) + list(directory.glob("*.yaml")))
    if not files:
        unresolved.append({
            "kind": "UNRECOGNISED_SYNTAX", "where": str(directory), "value": "(no workflows)",
            "why": "no workflow files found; discovery over an empty set proves nothing",
        })
    for file in files:
        relative = f".github/workflows/{file.name}"
        try:
            text = file.read_text(encoding="utf-8")
        except OSError as exc:
            unresolved.append({
                "kind": "UNRECOGNISED_SYNTAX", "where": relative, "value": str(exc)[:100],
                "why": "the workflow could not be read, so its execution edges are unknown; "
                       "omitting it silently would look identical to it having none",
            })
            continue
        file_records, file_unresolved = parse_workflow(text)
        for record in file_records:
            record["workflow_path"] = relative
        for edge in file_unresolved:
            edge["workflow_path"] = relative
        records.extend(file_records)
        unresolved.extend(file_unresolved)
    return records, unresolved


def invoked_scripts_in(directory: Path) -> set[str]:
    """The canonical discovery entry point, over all workflows.

    `tests/test_control_surface.py` imports this rather than re-deriving the set with its
    own regex. Two implementations of "which controls does CI invoke" would disagree
    eventually, and the guard would be enforcing the weaker one (`C-CEG-01`).

    The same script invoked by two workflows yields two graph **edges** and **one**
    membership obligation — it is one control, discovered twice.
    """
    records, _ = parse_all(directory)
    return {record["path"] for record in records}


def invoked_scripts(text: str) -> set[str]:
    """Single-workflow discovery, retained for callers holding one file's text."""
    records, _ = parse_workflow(text)
    return {record["path"] for record in records}


def reachability(record: dict) -> str:
    """Four values, and `UNCONDITIONAL` is not among them (`C-CEG-04`).

    A step with no `if` is **not** unconditional: GitHub applies a default `success()`
    condition, so a previous step's failure skips it. The absence of an explicit condition
    is an observation about the file, not a guarantee about execution.
    """
    if record.get("parse_incomplete"):
        return "REACHABILITY_NOT_PROVEN"
    for condition in (record["job_condition"], record["step_condition"]):
        if condition and condition.strip() in ("false", "${{ false }}"):
            return "STATICALLY_UNREACHABLE"
    if record["job_condition"] or record["step_condition"] or record["needs"]:
        return "EXPLICIT_CONDITION_PRESENT"
    return "NO_EXPLICIT_CONDITION_OBSERVED"


def classify(record: dict, membership: str) -> dict:
    """Four independent axes (`C-CEG-05`).

        CONTROL_SURFACE_MEMBERSHIP ≠ CI_REACHABILITY ≠ RESULT_CONSUMPTION ≠ CI_ENFORCEMENT

    Being in the registry says nothing about running; running says nothing about anyone
    reading the result; and none of it says a merge is blocked.
    """
    return {
        "CONTROL_SURFACE_MEMBERSHIP": membership,
        "CI_REACHABILITY": reachability(record),
        "EXECUTION_OBSERVED": "NOT_OBSERVED",
        "RESULT_CONSUMPTION": {
            # `continue-on-error` proves only that a failure does not fail the job
            # DIRECTLY. A later step can still read `steps.<id>.outcome`, so consumption
            # is a separate, unobserved question (`C-CEG-03`).
            "DIRECT_JOB_FAILURE_PROPAGATION": False if record["continue_on_error"] else "NOT_OBSERVED",
            "DOWNSTREAM_RESULT_CONSUMPTION": "NOT_OBSERVED",
        },
        "CI_ENFORCEMENT": "NOT_OBSERVED",
    }


def accounted(registry: dict) -> set[str]:
    return ({c["path"] for c in registry.get("controls", [])}
            | {e["path"] for e in registry.get("declared_exclusions", [])})


def main(argv: list[str]) -> int:
    env = dict(os.environ)
    try:
        registry = json.loads(Path(env.get("REGISTRY", DEFAULT_REGISTRY)).read_text(encoding="utf-8"))
        if env.get("WORKFLOW"):
            # One named workflow, for fixtures and narrow checks.
            text = Path(env["WORKFLOW"]).read_text(encoding="utf-8")
            records, unresolved = parse_workflow(text)
            for record in records:
                record["workflow_path"] = env["WORKFLOW"]
        else:
            records, unresolved = parse_all(
                Path(env.get("WORKFLOW_DIR", ".github/workflows")))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"REFUSED (closed): {exc}", file=sys.stderr)
        return FAIL
    tracked = {c["path"] for c in registry.get("controls", [])}
    excluded = {e["path"] for e in registry.get("declared_exclusions", [])}
    for record in records:
        membership = ("TRACKED" if record["path"] in tracked
                      else "EXCLUDED" if record["path"] in excluded else "UNACCOUNTED")
        record["axes"] = classify(record, membership)

    # One membership obligation per control, however many edges reach it.
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
        "paths": sorted(records, key=lambda r: (r["path"], r.get("workflow_path", ""), r["job"])),
        "workflows_parsed": sorted({r.get("workflow_path", "?") for r in records}),
        "unresolved_edges": unresolved,
        "not_proven": [
            "that any path executed -- execution requires a run",
            "that a downstream step did not read a continue-on-error outcome",
            "that a path without an explicit condition is unconditional; the default "
            "success() condition still applies",
            "that anything is enforced -- branch protection is not observed here",
            "that the parse is YAML-conformant; unrecognised keys and YAML aliases are "
            "reported as unresolved edges and force REACHABILITY_NOT_PROVEN",
            "that discovery implies enforcement; membership, reachability, consumption and "
            "enforcement remain four separate axes",
        ],
    }, indent=2, sort_keys=True))
    return OK


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
