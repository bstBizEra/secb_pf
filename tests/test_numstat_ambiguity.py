"""Authority classification of numstat rows whose paths cannot be recovered.

Every fixture here is produced by RUNNING GIT, never hand-written. That is the
point of the file. `git diff --numstat` renders a rename inside the single path
field -- as "old => new" or "{old => new}/tail" -- and C-quotes paths carrying
non-ASCII bytes. A hand-typed fixture can only contain shapes its author already
knew existed, and the defect these tests pin was exactly a shape nobody had
written down: a rename row was classified by its SOURCE prefix, so moving a file
from an auto_path to a protected path auto-approved.

The suite that shipped with the defect had zero rename fixtures. It was green.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "classify_authority_delta.py"
ENVELOPE = ROOT / "config" / "delegation_envelope.json"
EXIT_OK, EXIT_ESCALATE, EXIT_REJECTED = 0, 2, 3


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True
    ).stdout


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "r"
    repo.mkdir()
    _git(repo, "init", "-q", ".")
    _git(repo, "config", "user.email", "t@example.invalid")
    _git(repo, "config", "user.name", "t")
    return repo


def _seed(repo: Path, rel: str, body: str = "seed\n") -> None:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body)


def _classify(numstat: str) -> int:
    """Return the classifier's exit code for a numstat blob."""
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=numstat,
        capture_output=True,
        text=True,
        env={**os.environ, "ENVELOPE": str(ENVELOPE)},
    ).returncode


# Each case moves a file from an auto_path to a surface the envelope protects.
# git chooses the rendering; we never choose it for it.
RELOCATIONS = [
    ("docs/note.md", ".github/workflows/injected.yml"),
    ("docs/note.md", "config/delegation_envelope.json"),
    ("docs/note.md", "scripts/classify_authority_delta.py"),
    ("docs/note.md", "AGENTS.md"),
    ("src/mod.py", ".github/workflows/injected.yml"),
    ("tests/t.py", "config/ballot.schema.json"),
    # same parent, so git emits the compact brace form instead
    ("docs/a/note.md", "docs/00-governance/L0_ROOT_CONSTITUTION.md"),
]


@pytest.mark.parametrize("src,dst", RELOCATIONS, ids=[f"{s}->{d}" for s, d in RELOCATIONS])
def test_a_rename_onto_a_protected_path_never_auto_approves(tmp_path, src, dst):
    repo = _repo(tmp_path)
    _seed(repo, src)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    base = _git(repo, "rev-parse", "HEAD").strip()
    (repo / dst).parent.mkdir(parents=True, exist_ok=True)
    _git(repo, "mv", src, dst)
    _git(repo, "commit", "-q", "-am", "relocate")
    head = _git(repo, "rev-parse", "HEAD").strip()

    numstat = _git(repo, "diff", "--numstat", f"{base}...{head}")
    assert numstat.strip(), "git produced no numstat row"
    assert _classify(numstat) != EXIT_OK, (
        f"relocation onto {dst} auto-approved; git rendered it as {numstat!r}"
    )


def test_git_really_does_hide_both_paths_in_one_field(tmp_path):
    """Pin the format assumption the fix rests on, from git itself.

    If a future git emits renames as separate tab fields, this fails and the
    parser's fail-closed rule should be revisited rather than silently bypassed.
    """
    repo = _repo(tmp_path)
    _seed(repo, "docs/note.md")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    base = _git(repo, "rev-parse", "HEAD").strip()
    Path(repo / "hooks").mkdir()
    _git(repo, "mv", "docs/note.md", "hooks/note.md")
    _git(repo, "commit", "-q", "-am", "move")
    row = _git(repo, "diff", "--numstat", f"{base}...HEAD").strip()

    assert row.count("\t") == 2, f"expected 3 tab-fields, got {row!r}"
    assert " => " in row.split("\t")[2], f"rename not rendered in the path field: {row!r}"


def test_deleting_an_empty_evidence_file_does_not_auto_approve(tmp_path):
    """A 0/0 row is byte-identical to a no-op; on a G5 surface it must escalate."""
    repo = _repo(tmp_path)
    _seed(repo, "docs/13-evidence/empty.md", "")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    base = _git(repo, "rev-parse", "HEAD").strip()
    _git(repo, "rm", "-q", "docs/13-evidence/empty.md")
    _git(repo, "commit", "-q", "-m", "remove")
    numstat = _git(repo, "diff", "--numstat", f"{base}...HEAD")

    assert numstat.split("\t")[:2] == ["0", "0"], f"expected a 0/0 row, got {numstat!r}"
    assert _classify(numstat) != EXIT_OK


def test_deleting_a_binary_evidence_artifact_does_not_auto_approve(tmp_path):
    """Binary rows carry '-' counts, so deletion is not inferable from them."""
    repo = _repo(tmp_path)
    p = repo / "docs" / "13-evidence" / "sealed.bin"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(bytes(range(256)) * 8)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    base = _git(repo, "rev-parse", "HEAD").strip()
    _git(repo, "rm", "-q", "docs/13-evidence/sealed.bin")
    _git(repo, "commit", "-q", "-m", "remove")
    numstat = _git(repo, "diff", "--numstat", f"{base}...HEAD")

    assert numstat.startswith("-\t-\t"), f"expected a binary row, got {numstat!r}"
    assert _classify(numstat) != EXIT_OK


def test_shrinking_evidence_while_adding_a_line_does_not_auto_approve(tmp_path):
    """The laundering shape: destroy content, add one line, stay under G5."""
    repo = _repo(tmp_path)
    _seed(repo, "docs/13-evidence/ledger.md", "".join(f"line {i}\n" for i in range(200)))
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    base = _git(repo, "rev-parse", "HEAD").strip()
    (repo / "docs" / "13-evidence" / "ledger.md").write_text("only this\n")
    _git(repo, "commit", "-q", "-am", "rewrite")
    numstat = _git(repo, "diff", "--numstat", f"{base}...HEAD")

    added, deleted, _ = numstat.split("\t", 2)
    assert int(deleted) > int(added), f"expected net shrinkage, got {numstat!r}"
    assert _classify(numstat) != EXIT_OK


def test_appending_to_evidence_still_auto_approves(tmp_path):
    """The control. Growth is not destruction, and must not draw a human."""
    repo = _repo(tmp_path)
    _seed(repo, "docs/13-evidence/ledger.md", "start\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    base = _git(repo, "rev-parse", "HEAD").strip()
    led = repo / "docs" / "13-evidence" / "ledger.md"
    led.write_text(led.read_text() + "".join(f"row {i}\n" for i in range(40)))
    _git(repo, "commit", "-q", "-am", "append")
    numstat = _git(repo, "diff", "--numstat", f"{base}...HEAD")

    assert _classify(numstat) == EXIT_OK, f"ordinary evidence growth escalated: {numstat!r}"
