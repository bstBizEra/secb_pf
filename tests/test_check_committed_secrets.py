"""Subprocess tests for scripts/check_committed_secrets.py (`NFR-17`, Gate 6).

`NFR-17` claimed zero committed credentials, verified by *"Repository scan"* --
by hand, the third such NFR after `NFR-04` and `NFR-18`.

The false-positive tests matter as much as the detection tests, and more than
usual. This repository is full of prose about tokens and secrets, its workflow
carries `GH_TOKEN: ${{ github.token }}`, and there are six SHA-256 digests in the
tracked tree -- 64 hex characters each, every one a legitimate evidence anchor. A
scan that flags those gets switched off, and a scan that is switched off protects
nothing. `FWK-048` learned the same lesson by reproducing a recorded defect.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "check_committed_secrets.py"

CLEAN = 0
FINDINGS = 1
FAIL_CLOSED = 2


def scan(*paths: str | Path):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *(str(p) for p in paths)],
        capture_output=True, text=True, timeout=120,
    )


def fixture(tmp_path: Path, body: str, name: str = "candidate.txt") -> Path:
    path = tmp_path / name
    path.write_text(body, encoding="utf-8")
    return path


# --- the property NFR-17 asserts ---------------------------------------------


def test_the_tracked_tree_is_clean():
    """What the hand scan concluded, now recomputed on every run."""
    result = scan(
        ROOT / "AGENTS.md", ROOT / "README.md", ROOT / "docs", ROOT / "config",
        ROOT / "scripts", ROOT / "src", ROOT / "tests", ROOT / ".github",
    )
    assert result.returncode == CLEAN, result.stdout + result.stderr


def test_the_scanner_does_not_flag_itself():
    """Its own patterns must not match its own source.

    A scanner that reports itself is a scanner nobody runs.
    """
    assert scan(SCRIPT).returncode == CLEAN


# --- known credential shapes must be caught ----------------------------------


# Credential shapes are BUILT at runtime, never written as literals. A secret
# scanner whose own tests contain the shapes it hunts flags its own test file --
# and the natural fix is an exclusion, which is how a scanner stops scanning.
# Assembling the strings keeps the scan honest about its own tree.
DASHES = "-" * 5
KEY_HEADER = DASHES + "BEGIN " + "RSA " + "PRIVATE" + " KEY" + DASHES
BARE_KEY_HEADER = DASHES + "BEGIN " + "PRIVATE" + " KEY" + DASHES


def test_a_private_key_block_is_caught(tmp_path):
    body = KEY_HEADER + "\nMIIEow…\n"
    result = scan(fixture(tmp_path, body))
    assert result.returncode == FINDINGS
    assert "private key block" in result.stderr


def test_provider_token_shapes_are_caught(tmp_path):
    cases = {
        "ghp_" + "a" * 36: "GitHub personal access token",
        "github_pat_" + "b" * 40: "GitHub fine-grained token",
        "AKIA" + "C" * 16: "AWS access key id",
        "xoxb-" + "1" * 24: "Slack token",
        "AIza" + "d" * 35: "Google API key",
        "sk-" + "e" * 48: "OpenAI-style secret key",
    }
    for value, label in cases.items():
        result = scan(fixture(tmp_path, "cred" + f"ential = {value}\n"))
        assert result.returncode == FINDINGS, value[:12]
        assert label in result.stderr, value[:12]


def test_a_secret_named_assignment_with_a_real_looking_value_is_caught(tmp_path):
    # Built, not written -- see the note above KEY_HEADER.
    value = "s7Kd92Lm" + "Qx4vBn18"
    for line in (
        "pass" + 'word = "' + value + '"',
        "api" + "_key: " + "8f3ba91c47de" + "205fbb6a",
        "client" + '_secret="' + value + '"',
    ):
        result = scan(fixture(tmp_path, line + "\n"))
        assert result.returncode == FINDINGS, line
        assert "secret-named assignment" in result.stderr, line


# --- and the false positives must NOT be -------------------------------------


def test_a_sha256_digest_is_not_a_secret(tmp_path):
    """Six of these are in the tracked tree and every one is an evidence anchor."""
    body = (
        "| `router.py` | "
        "`4d1dab78b30eff24b5b4a6202ef84d23c814fb9efed63da049d501eb53eecef2` |\n"
        "digest" + ' = "8db87b0fe89fa3954f6fb1759d427f9b27da45fa993372b48fb51ecf996ec1d0"\n'
    )
    assert scan(fixture(tmp_path, body, "record.md")).returncode == CLEAN


def test_a_template_reference_is_not_a_secret(tmp_path):
    """`GH_TOKEN: ${{ github.token }}` is a reference, and it is in `ci.yml`."""
    body = (
        "        env:\n"
        "          GH_" + "TOKEN: ${{ github.token }}\n"
        "          API_" + "KEY: ${API_KEY}\n"
        "          to" + 'ken = os.environ["TOKEN"]\n'
    )
    assert scan(fixture(tmp_path, body, "workflow.yml")).returncode == CLEAN


def test_prose_about_secrets_is_not_a_secret(tmp_path):
    """Name alone is not evidence, and this repository is full of such prose."""
    body = (
        "`NFR-17` requires that no credential or secret is committed, and the\n"
        "control is `.gitignore` secret patterns. A token must never be pasted\n"
        "into a tracked file, and any api_key belongs in a secret provider.\n"
    )
    assert scan(fixture(tmp_path, body, "notes.md")).returncode == CLEAN


def test_documented_placeholders_are_not_secrets(tmp_path):
    for line in (
        "pass" + 'word = "CHANGE_ME"',
        "api" + "_key: <your-key-here>",
        "to" + 'ken = "' + "x" * 16 + '"',
        "client" + "_secret: TBC-OPERATOR",
    ):
        result = scan(fixture(tmp_path, line + "\n"))
        assert result.returncode == CLEAN, line


def test_a_short_value_is_not_a_secret(tmp_path):
    """Below the length floor a value cannot carry a credential."""
    assert scan(fixture(tmp_path, "to" + 'ken = "abc"\n')).returncode == CLEAN


# --- fail closed -------------------------------------------------------------


def test_no_paths_fails_closed():
    result = scan()
    assert result.returncode == FAIL_CLOSED
    assert "not scanning clean" in result.stderr


def test_a_missing_path_fails_closed(tmp_path):
    result = scan(tmp_path / "absent")
    assert result.returncode == FAIL_CLOSED
    assert "does not exist" in result.stderr


def test_an_empty_directory_fails_closed(tmp_path):
    (tmp_path / "sub").mkdir()
    result = scan(tmp_path / "sub")
    assert result.returncode == FAIL_CLOSED
    assert "empty scan is not a clean scan" in result.stderr


def test_a_binary_file_is_skipped_not_scanned(tmp_path):
    """A credential inside a binary is out of scope, and stated as such.

    Skipping must not be silent about what was scanned -- the count in the
    clean message is the scanned count, not the file count.
    """
    (tmp_path / "blob.bin").write_bytes(b"\x00\x01ghp_" + b"a" * 40)
    (tmp_path / "ok.txt").write_text("nothing here\n", encoding="utf-8")
    result = scan(tmp_path)
    assert result.returncode == CLEAN
    assert "1 text file(s)" in result.stdout


def test_the_three_outcomes_have_three_exit_codes(tmp_path):
    clean = scan(fixture(tmp_path, "nothing\n", "a.txt"))
    found = scan(fixture(tmp_path, BARE_KEY_HEADER + "\n", "b.txt"))
    broken = scan(tmp_path / "absent")
    assert {clean.returncode, found.returncode, broken.returncode} == {0, 1, 2}


def test_every_placeholder_carries_a_reason():
    """An allowlist entry without a reason is how a scanner stops scanning."""
    import ast

    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "PLACEHOLDERS" for t in node.targets
        ):
            mapping = ast.literal_eval(node.value)
            assert mapping, "the placeholder allowlist must not be empty-by-accident"
            for key, reason in mapping.items():
                assert reason and reason.strip(), f"{key} has no reason"
            return
    raise AssertionError("PLACEHOLDERS not found")
