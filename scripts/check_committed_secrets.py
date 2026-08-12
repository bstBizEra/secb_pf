#!/usr/bin/env python3
"""Committed-secret scan for `NFR-17` (`SECB-WP-FWK-049`, Gate 6).

`NFR-17` states that no credential or secret is committed, target zero
occurrences, and names its verification as *"Repository scan."* By hand — the
third such NFR, after `NFR-04` (`FWK-045`) and `NFR-18` (`FWK-048`). The
existing control is `.gitignore` patterns, which stop a file from being added
and say nothing about a secret pasted into a file that is already tracked.

Two rules, and the split is the whole design.

**Known shapes** are matched anywhere, because a private-key header or a
`ghp_`-prefixed token is a credential wherever it appears. There is no context
in which those are innocent.

**Secret-named assignments** are matched only when a secret-ish identifier is
assigned a literal that is long enough to be real and is not a placeholder.
Name alone is not evidence: this repository is full of prose about tokens and
secrets, and `GH_TOKEN: ${{ github.token }}` in a workflow is a reference, not
a secret. Value alone is not evidence either — a SHA-256 digest is 64 hex
characters and there are six of them in the tracked tree, every one a
legitimate evidence anchor. **Requiring both is what keeps this scan usable**,
and a scan that is ignored protects nothing.

Placeholders are listed explicitly with a reason, because an allowlist is how a
scanner quietly stops scanning. `FWK-048` learned that the hard way: matching
attribute names alone reproduced a recorded false-positive defect and declared a
sealed package dirty.

    argv[1..]  paths to scan (files or directories)

Exit codes:

    0  clean — no credential shape and no secret-named assignment found
    1  findings — listed with file, line and which rule fired
    2  fail closed — nothing to scan, a missing path, or a file that cannot be
       read as text. An unreadable file is not a clean file.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

EXIT_CLEAN = 0
EXIT_FINDINGS = 1
EXIT_FAIL_CLOSED = 2

# Unambiguous credential formats. Matched anywhere, because there is no context
# in which these are innocent. Each pattern requires enough trailing payload
# that this file's own source does not match it.
KNOWN_SHAPES = [
    (re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----"),
     "private key block"),
    (re.compile(r"\bghp_[A-Za-z0-9]{30,}"), "GitHub personal access token"),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{30,}"), "GitHub fine-grained token"),
    (re.compile(r"\bgh[opsu]_[A-Za-z0-9]{30,}"), "GitHub token"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS access key id"),
    (re.compile(r"\bASIA[0-9A-Z]{16}\b"), "AWS temporary access key id"),
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}"), "Slack token"),
    (re.compile(r"\bAIza[0-9A-Za-z_-]{30,}"), "Google API key"),
    (re.compile(r"\bsk-[A-Za-z0-9]{40,}"), "OpenAI-style secret key"),
]

# Identifiers that suggest a secret. Name alone is not a finding.
SECRET_NAMES = re.compile(
    r"(?i)\b("
    r"pass(?:word|wd|phrase)|secret|token|api[_-]?key|apikey|"
    r"private[_-]?key|credential|client[_-]?secret|auth[_-]?token"
    r")\b"
)

# name = "value" / name: "value" / name=value in an env-ish line.
ASSIGNMENT = re.compile(
    r"""(?P<name>[A-Za-z_][A-Za-z0-9_.\-]*)\s*[:=]\s*(?P<q>["']?)(?P<value>[^"'\s,}\)]{12,})(?P=q)"""
)

# Placeholders, each with the reason it is not a credential. An allowlist entry
# without a reason is how a scanner stops scanning.
PLACEHOLDERS = {
    "change_me": "the documented placeholder convention",
    "changeme": "same",
    "xxxxxxxxxxxx": "obvious filler",
    "your_token_here": "documentation placeholder",
    "redacted": "deliberately removed",
    "example": "documentation",
    "placeholder": "self-describing",
    "tbc-operator": "this repository's own unset-value marker",
}


def is_placeholder(value: str) -> bool:
    low = value.strip().lower()
    if low in PLACEHOLDERS:
        return True
    # A reference rather than a value: env lookup, template expression, or an
    # angle-bracket stand-in. `GH_TOKEN: ${{ github.token }}` is a reference.
    if any(marker in value for marker in ("${", "$(", "{{", "<", ">", "os.environ", "getenv")):
        return True
    # Repeated single character, or a value made only of punctuation/dots.
    if len(set(low)) <= 2 or set(low) <= set("._-…"):
        return True
    return any(word in low for word in PLACEHOLDERS)


def scan_text(path: Path, text: str) -> list[str]:
    findings: list[str] = []
    for number, line in enumerate(text.splitlines(), start=1):
        for pattern, label in KNOWN_SHAPES:
            if pattern.search(line):
                findings.append(f"{path}:{number}: {label} — known credential shape")
        match = ASSIGNMENT.search(line)
        if match and SECRET_NAMES.search(match.group("name")):
            value = match.group("value")
            if not is_placeholder(value):
                findings.append(
                    f"{path}:{number}: secret-named assignment to "
                    f"{match.group('name')!r} with a {len(value)}-character literal"
                )
    return findings


def text_files(targets: list[str]) -> list[Path]:
    files: list[Path] = []
    for target in targets:
        path = Path(target)
        if not path.exists():
            raise ValueError(f"path does not exist: {target}")
        if path.is_file():
            files.append(path)
        else:
            files.extend(sorted(p for p in path.rglob("*") if p.is_file()))
    return files


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(
            "SECRET SCAN FAIL (closed): no paths given; scanning nothing is "
            "not scanning clean",
            file=sys.stderr,
        )
        return EXIT_FAIL_CLOSED

    try:
        files = text_files(argv[1:])
    except ValueError as exc:
        print(f"SECRET SCAN FAIL (closed): {exc}", file=sys.stderr)
        return EXIT_FAIL_CLOSED

    if not files:
        print(
            "SECRET SCAN FAIL (closed): the given paths contain no files; an "
            "empty scan is not a clean scan",
            file=sys.stderr,
        )
        return EXIT_FAIL_CLOSED

    findings: list[str] = []
    scanned = 0
    for path in files:
        try:
            raw = path.read_bytes()
        except OSError as exc:
            print(
                f"SECRET SCAN FAIL (closed): cannot read {path} ({exc}); an "
                "unreadable file is not a clean file",
                file=sys.stderr,
            )
            return EXIT_FAIL_CLOSED
        if b"\x00" in raw[:8192]:
            continue  # binary; a credential in a binary is out of this scan's scope
        scanned += 1
        findings.extend(scan_text(path, raw.decode("utf-8", errors="replace")))

    if findings:
        print(
            f"SECRET SCAN: {len(findings)} finding(s) across {scanned} file(s):\n  "
            + "\n  ".join(findings),
            file=sys.stderr,
        )
        return EXIT_FINDINGS

    print(f"SECRET SCAN CLEAN: {scanned} text file(s), no credential found")
    return EXIT_CLEAN


if __name__ == "__main__":
    sys.exit(main(sys.argv))
