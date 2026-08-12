"""Subprocess tests for scripts/check_prohibited_calls.py (`NFR-18`, Gate 6).

Every prohibited category has a fixture that must be caught, because a scan that
cannot fail proves nothing (`K-05b`). The fixtures live in `tmp_path` and never
in the scanned tree -- writing a violation into the sealed package to test the
scanner would be the worst way to test a scanner.

The false-positive tests carry as much weight as the detection tests. The first
version of this scanner matched attribute names alone and reported
`visiting.remove(skill_id)` -- a `set[str]` operation in the router's
topological sort -- as a filesystem write. That is `DEF-ENGLOOP-MVP-001` in
miniature, a defect already recorded in this repository's sealed evidence, and
the scan meant to protect that package reproduced it. A false positive here
invites someone to edit a file whose certification voids on modification.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "check_prohibited_calls.py"
SEALED = (
    ROOT / "docs/06-agent-orchestration/skill-router"
    / "SECB-WP-ENGLOOP-MVP-001 — Sandbox Evidence"
)

CLEAN = 0
FINDINGS = 1
FAIL_CLOSED = 2


def scan(*paths: str | Path):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *(str(p) for p in paths)],
        capture_output=True, text=True, timeout=60,
    )


def fixture(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "candidate.py"
    path.write_text(body, encoding="utf-8")
    return path


# --- the property NFR-18 asserts ---------------------------------------------


def test_the_sealed_router_and_src_scan_clean():
    """What the two hand scans concluded, now recomputed on every run."""
    result = scan(SEALED, ROOT / "src")
    assert result.returncode == CLEAN, result.stdout + result.stderr
    assert "no external effect" in result.stdout


def test_the_scan_does_not_modify_the_sealed_package():
    """A scanner that writes to what it scans is worse than none."""
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in SEALED.iterdir() if p.is_file()}
    scan(SEALED)
    after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in SEALED.iterdir() if p.is_file()}
    assert before == after
    assert not (SEALED / ".pytest_cache").exists()


# --- each prohibited category must be caught ---------------------------------


def test_network_is_caught(tmp_path):
    for body in ("import socket\n", "from urllib import request\n",
                 "import x\nx.urlopen('http://y')\n"):
        result = scan(fixture(tmp_path, body))
        assert result.returncode == FINDINGS, body
        assert "network" in result.stderr, body


def test_subprocess_is_caught(tmp_path):
    for body in ("import subprocess\n", "import os\nos.system('ls')\n"):
        result = scan(fixture(tmp_path, body))
        assert result.returncode == FINDINGS, body
        assert "subprocess" in result.stderr, body


def test_filesystem_write_is_caught(tmp_path):
    for body in ("import shutil\n", "open('f','w')\n",
                 "from pathlib import Path\nPath('f').write_text('x')\n",
                 "import os\nos.remove('f')\n"):
        result = scan(fixture(tmp_path, body))
        assert result.returncode == FINDINGS, body


def test_dynamic_execution_is_caught(tmp_path):
    for body in ("eval('1')\n", "exec('pass')\n", "__import__('os')\n",
                 "import pickle\n"):
        result = scan(fixture(tmp_path, body))
        assert result.returncode == FINDINGS, body
        assert "dynamic execution" in result.stderr, body


# --- and the false positives must NOT be ------------------------------------


def test_a_set_remove_is_not_a_filesystem_write(tmp_path):
    """`DEF-ENGLOOP-MVP-001`, reproduced by the first version of this scanner.

    This is the regression that matters most. The router's topological sort
    calls `visiting.remove(skill_id)` on a `set[str]`, and the sealed package
    must keep scanning clean.
    """
    body = (
        "def order(ids: set[str]) -> list[str]:\n"
        "    visiting: set[str] = set()\n"
        "    visiting.add('a')\n"
        "    visiting.remove('a')\n"
        "    return sorted(ids)\n"
    )
    result = scan(fixture(tmp_path, body))
    assert result.returncode == CLEAN, (
        "a set operation must not be reported as a filesystem write:\n"
        + result.stderr
    )


def test_a_mention_in_a_docstring_or_comment_is_not_a_finding(tmp_path):
    """`ast` distinguishes a call from a mention; a regex would not."""
    body = (
        '"""This module never calls subprocess.run or eval, and does not open files."""\n'
        "# os.system would be prohibited here\n"
        "reopen = 1\n"
        "socket_like_name = 'not an import'\n"
    )
    result = scan(fixture(tmp_path, body))
    assert result.returncode == CLEAN, result.stderr


def test_a_json_loads_is_not_dynamic_execution(tmp_path):
    """`loads` is dangerous on pickle and ordinary on json."""
    body = "import json\njson.loads('{}')\n"
    result = scan(fixture(tmp_path, body))
    assert result.returncode == CLEAN, result.stderr


# --- fail closed -------------------------------------------------------------


def test_no_paths_fails_closed():
    result = scan()
    assert result.returncode == FAIL_CLOSED
    assert "not scanning clean" in result.stderr


def test_a_missing_path_fails_closed(tmp_path):
    result = scan(tmp_path / "absent")
    assert result.returncode == FAIL_CLOSED
    assert "does not exist" in result.stderr


def test_a_directory_with_no_python_fails_closed(tmp_path):
    (tmp_path / "notes.md").write_text("nothing here", encoding="utf-8")
    result = scan(tmp_path)
    assert result.returncode == FAIL_CLOSED
    assert "empty scan is not a clean scan" in result.stderr


def test_an_unparseable_file_fails_closed(tmp_path):
    fixture(tmp_path, "def broken(:\n")
    result = scan(tmp_path)
    assert result.returncode == FAIL_CLOSED
    assert "not a clean file" in result.stderr


def test_the_three_outcomes_have_three_exit_codes(tmp_path):
    clean = scan(fixture(tmp_path, "x = 1\n"))
    found = scan(fixture(tmp_path, "import socket\n"))
    broken = scan(tmp_path / "absent")
    assert {clean.returncode, found.returncode, broken.returncode} == {0, 1, 2}
