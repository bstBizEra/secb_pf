#!/usr/bin/env python3
"""Prohibited-call scan for `NFR-18` (`SECB-WP-FWK-048`, Gate 6).

`NFR-18` states that the sandbox router performs no external effect — zero
network, subprocess, filesystem-write or dynamic-execution paths — and named its
verification as *"verified twice by static scan, at certification and
independent review."* By hand, twice, and never since. That is the defect
`NFR-04` had before `FWK-045`: a property asserted about a **certified**
artifact with nothing recomputing it.

Uses `ast`, not a regex. A regex for ``open(`` matches a docstring, a comment
and a variable named ``reopen``; `ast` distinguishes a call from a mention. That
matters here because the scan runs over a package whose certification **voids on
modification** — a false positive invites someone to edit a sealed file to
satisfy a scanner, which is the worst available outcome. `NFR-12` permits it:
`ast` is stdlib.

    argv[1..]  paths to scan (files or directories)

Exit codes:

    0  clean — no prohibited call found
    1  findings — at least one prohibited call, listed with file and line
    2  fail closed — nothing to scan, a missing path, or a file that will not
       parse. An unparseable file is not a clean file.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

EXIT_CLEAN = 0
EXIT_FINDINGS = 1
EXIT_FAIL_CLOSED = 2

# Module-level names whose use at all is an external effect.
PROHIBITED_MODULES = {
    "socket": "network",
    "http": "network",
    "urllib": "network",
    "requests": "network",
    "httpx": "network",
    "ftplib": "network",
    "smtplib": "network",
    "telnetlib": "network",
    "asyncio": "network or concurrency",
    "subprocess": "subprocess",
    "multiprocessing": "subprocess",
    "shutil": "filesystem write",
    "tempfile": "filesystem write",
    "ctypes": "dynamic execution",
    "importlib": "dynamic execution",
    "pickle": "dynamic execution",
    "marshal": "dynamic execution",
}

# Bare callables that carry an effect regardless of the module they came from.
PROHIBITED_CALLS = {
    "open": "filesystem access",
    "eval": "dynamic execution",
    "exec": "dynamic execution",
    "compile": "dynamic execution",
    "__import__": "dynamic execution",
    "input": "external input",
}

# Attribute calls come in two kinds, and conflating them reproduces a defect
# this repository has already recorded.
#
# The first version of this file matched attribute names alone, so
# `visiting.remove(skill_id)` -- a `set[str]` operation in the router's
# topological sort -- was reported as a filesystem write. That is
# `DEF-ENGLOOP-MVP-001` in miniature: the MVP's own `set.remove()` scanner made
# the same mistake, it is recorded in the sealed evidence, and the scan meant to
# protect that package reproduced it. A false positive here is not a harmless
# nuisance -- it invites someone to edit a file whose certification voids on
# modification, in order to satisfy a scanner.

# Unambiguous: these attribute names carry an effect whatever the receiver is.
PROHIBITED_ATTRS_ANY_RECEIVER = {
    "system": "subprocess",
    "popen": "subprocess",
    "rmtree": "filesystem write",
    "makedirs": "filesystem write",
    "write_text": "filesystem write",
    "write_bytes": "filesystem write",
    "urlopen": "network",
}

# Ambiguous: dangerous on a module, ordinary on a container. `remove` on a set,
# `connect` on a signal, `loads` on json. Flagged only when the receiver is a
# name bound by importing a risky module.
PROHIBITED_ATTRS_RISKY_RECEIVER = {
    "remove": "filesystem write",
    "unlink": "filesystem write",
    "rmdir": "filesystem write",
    "mkdir": "filesystem write",
    "rename": "filesystem write",
    "spawn": "subprocess",
    "fork": "subprocess",
    "connect": "network",
    "sendall": "network",
    "loads": "dynamic execution",
}

# Modules whose bound name makes an ambiguous attribute dangerous. `os` and
# `sys` are not prohibited outright -- the router imports neither, but a future
# module legitimately might -- so they are receivers rather than imports.
RISKY_RECEIVERS = {
    "os", "path", "shutil", "subprocess", "socket", "pathlib", "Path",
    "sys", "pickle", "marshal", "ctypes", "importlib",
}


class Scanner(ast.NodeVisitor):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.findings: list[tuple[int, str, str]] = []
        # Names bound by an import, so an ambiguous attribute call can be told
        # apart from a container method with the same name.
        self.bound_risky: set[str] = set()

    def _record(self, node: ast.AST, name: str, category: str) -> None:
        self.findings.append((getattr(node, "lineno", 0), name, category))

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            root = alias.name.split(".")[0]
            if root in PROHIBITED_MODULES:
                self._record(node, f"import {alias.name}", PROHIBITED_MODULES[root])
            bound = alias.asname or alias.name.split(".")[0]
            if root in RISKY_RECEIVERS or bound in RISKY_RECEIVERS:
                self.bound_risky.add(bound)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        root = (node.module or "").split(".")[0]
        if root in PROHIBITED_MODULES:
            self._record(node, f"from {node.module} import …", PROHIBITED_MODULES[root])
        for alias in node.names:
            bound = alias.asname or alias.name
            if root in RISKY_RECEIVERS or bound in RISKY_RECEIVERS:
                self.bound_risky.add(bound)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if isinstance(func, ast.Name) and func.id in PROHIBITED_CALLS:
            self._record(node, f"{func.id}()", PROHIBITED_CALLS[func.id])
        elif isinstance(func, ast.Attribute):
            attr = func.attr
            if attr in PROHIBITED_ATTRS_ANY_RECEIVER:
                self._record(
                    node, f".{attr}()", PROHIBITED_ATTRS_ANY_RECEIVER[attr]
                )
            elif attr in PROHIBITED_ATTRS_RISKY_RECEIVER:
                receiver = func.value
                name = (
                    receiver.id if isinstance(receiver, ast.Name)
                    else receiver.attr if isinstance(receiver, ast.Attribute)
                    else None
                )
                if name in self.bound_risky or name in RISKY_RECEIVERS:
                    self._record(
                        node,
                        f"{name}.{attr}()",
                        PROHIBITED_ATTRS_RISKY_RECEIVER[attr],
                    )
        self.generic_visit(node)


def python_files(targets: list[str]) -> list[Path]:
    files: list[Path] = []
    for target in targets:
        path = Path(target)
        if not path.exists():
            raise ValueError(f"path does not exist: {target}")
        if path.is_file():
            files.append(path)
        else:
            files.extend(sorted(p for p in path.rglob("*.py")))
    return files


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(
            "PROHIBITED CALL SCAN FAIL (closed): no paths given; scanning "
            "nothing is not scanning clean",
            file=sys.stderr,
        )
        return EXIT_FAIL_CLOSED

    try:
        files = python_files(argv[1:])
    except ValueError as exc:
        print(f"PROHIBITED CALL SCAN FAIL (closed): {exc}", file=sys.stderr)
        return EXIT_FAIL_CLOSED

    if not files:
        print(
            "PROHIBITED CALL SCAN FAIL (closed): the given paths contain no "
            "Python files; an empty scan is not a clean scan",
            file=sys.stderr,
        )
        return EXIT_FAIL_CLOSED

    findings: list[str] = []
    for path in files:
        source = path.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as exc:
            print(
                f"PROHIBITED CALL SCAN FAIL (closed): {path} will not parse "
                f"({exc}); an unparseable file is not a clean file",
                file=sys.stderr,
            )
            return EXIT_FAIL_CLOSED
        scanner = Scanner(path)
        scanner.visit(tree)
        for line, name, category in scanner.findings:
            findings.append(f"{path}:{line}: {name} — {category}")

    if findings:
        print(
            f"PROHIBITED CALL SCAN: {len(findings)} finding(s) across "
            f"{len(files)} file(s):\n  " + "\n  ".join(findings),
            file=sys.stderr,
        )
        return EXIT_FINDINGS

    print(f"PROHIBITED CALL SCAN CLEAN: {len(files)} file(s), no external effect")
    return EXIT_CLEAN


if __name__ == "__main__":
    sys.exit(main(sys.argv))
