"""Subprocess tests for scripts/check_work_package_ref.py (Authority Gate).

Every test invokes the script as a real subprocess -- the same surface CI
uses -- rather than importing it. A gate that passes unit tests through
import but breaks when invoked is a fail-open defect; testing the invoked
command is what catches it.

Since `SECB-WP-FWK-036` the prefix is configuration, so the tests cover two
things that did not exist before: that a *different* prefix works end to end
(the whole point of the change), and that every way of failing to read the
configuration exits 2 rather than 0. A configurable gate that fails open when
its configuration is absent is worse than the hard-coded one it replaced.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check_work_package_ref.py"

PASS = 0
FAIL_CLOSED = 2

# The tests that exercise *this* project's configuration read the prefix from
# the same envelope the gate reads, so they travel to an instantiated project
# without edits. The tests that prove configurability still pin a literal
# ("ACME-TICKET"), which is where the concrete coverage lives -- a suite that
# derived every value from the configuration would pass no matter what the
# configuration said.
_ENVELOPE = json.loads(
    (REPO_ROOT / "config" / "delegation_envelope.json").read_text(encoding="utf-8")
)
PREFIX = (_ENVELOPE.get("project") or {}).get("work_package_prefix")
assert PREFIX, (
    "config/delegation_envelope.json has no project.work_package_prefix; "
    "the Authority Gate reads it from there (NFR-15, SECB-WP-FWK-036)"
)
WP_ID = f"{PREFIX}-FWK-002"


def run_gate(
    args: list[str] | None = None,
    env_text: str | None = None,
    envelope: str | None = None,
):
    env = {k: v for k, v in os.environ.items() if k not in ("WP_TEXT", "ENVELOPE")}
    if env_text is not None:
        env["WP_TEXT"] = env_text
    if envelope is not None:
        env["ENVELOPE"] = envelope
    return subprocess.run(
        [sys.executable, str(SCRIPT), *(args or [])],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )


def write_envelope(tmp_path: Path, project) -> str:
    """Write a minimal envelope carrying *project* verbatim, return its path."""
    payload = {"envelope_id": "ENV-TEST", "schema_version": 1}
    if project is not None:
        payload["project"] = project
    path = tmp_path / "envelope.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


# --- behaviour against this repository's own configured prefix ---------------


def test_pass_when_title_cites_work_package():
    result = run_gate(env_text=f"feat: add intake form ({WP_ID})")
    assert result.returncode == PASS
    assert WP_ID in result.stdout


def test_pass_reference_may_appear_anywhere_in_body():
    result = run_gate(env_text=f"Some title\n\nImplements {PREFIX}-ENGLOOP-004.")
    assert result.returncode == PASS


def test_fail_when_no_reference_present():
    result = run_gate(env_text="feat: quick improvement, no ticket")
    assert result.returncode == FAIL_CLOSED
    assert "No Ticket, No Work" in result.stderr


def test_failure_message_names_the_configured_prefix():
    # The operator of a new project needs to be told which scheme the gate is
    # enforcing; a message naming a prefix the project does not use sends them
    # looking in the wrong place.
    result = run_gate(env_text="no ticket here")
    assert result.returncode == FAIL_CLOSED
    assert f"{PREFIX}-*" in result.stderr


def test_fail_closed_on_empty_input():
    result = run_gate(env_text="")
    assert result.returncode == FAIL_CLOSED
    assert "fail" in result.stderr.lower() or "FAIL" in result.stderr


def test_fail_closed_when_nothing_provided_at_all():
    result = run_gate()
    assert result.returncode == FAIL_CLOSED


def test_fail_on_lookalike_prefix_without_id():
    # "SECB-WP-" alone is not a work package; the ID segment is required.
    result = run_gate(env_text=f"mentions {PREFIX}- but never a real ID")
    assert result.returncode == FAIL_CLOSED


def test_fail_on_lowercase_reference():
    # IDs are uppercase by convention; lowercase text must not pass the gate.
    result = run_gate(env_text=f"{WP_ID.lower()} lowercase does not count")
    assert result.returncode == FAIL_CLOSED


def test_env_var_takes_precedence_over_argv():
    # CI feeds text via WP_TEXT so PR titles are never shell-interpolated;
    # argv must not override the trusted channel once it is set.
    result = run_gate(args=[f"{PREFIX}-FAKE-999"], env_text="no reference here")
    assert result.returncode == FAIL_CLOSED


def test_argv_fallback_still_works_without_env():
    result = run_gate(args=["chore:", "cleanup", "under", WP_ID])
    assert result.returncode == PASS


# --- the prefix is configuration (SECB-WP-FWK-036, NFR-15) ------------------


def test_custom_prefix_from_envelope_passes(tmp_path):
    # This is the measured defect: instantiating the framework used to require
    # editing this script's regex. It must now require editing the envelope.
    envelope = write_envelope(tmp_path, {"work_package_prefix": "ACME-TICKET"})
    result = run_gate(env_text="feat: bootstrap (ACME-TICKET-001)", envelope=envelope)
    assert result.returncode == PASS
    assert "ACME-TICKET-001" in result.stdout


def test_foreign_prefix_rejected_under_custom_configuration(tmp_path):
    # A project configured for ACME must not accept SecB's own IDs -- otherwise
    # the gate is decoration, passing on any plausible-looking string.
    envelope = write_envelope(tmp_path, {"work_package_prefix": "ACME-TICKET"})
    result = run_gate(env_text=f"feat: sneak in {WP_ID}", envelope=envelope)
    assert result.returncode == FAIL_CLOSED
    assert "ACME-TICKET-*" in result.stderr


def test_fail_closed_when_envelope_missing(tmp_path):
    result = run_gate(
        env_text=f"feat: work ({WP_ID})",
        envelope=str(tmp_path / "does-not-exist.json"),
    )
    assert result.returncode == FAIL_CLOSED
    assert "unreadable" in result.stderr


def test_fail_closed_when_envelope_is_malformed_json(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("{ not json", encoding="utf-8")
    result = run_gate(env_text=f"feat: work ({WP_ID})", envelope=str(path))
    assert result.returncode == FAIL_CLOSED
    assert "not valid JSON" in result.stderr


def test_fail_closed_when_project_block_absent(tmp_path):
    envelope = write_envelope(tmp_path, None)
    result = run_gate(env_text=f"feat: work ({WP_ID})", envelope=envelope)
    assert result.returncode == FAIL_CLOSED
    assert "work_package_prefix" in result.stderr


def test_fail_closed_when_prefix_is_empty(tmp_path):
    envelope = write_envelope(tmp_path, {"work_package_prefix": ""})
    result = run_gate(env_text=f"feat: work ({WP_ID})", envelope=envelope)
    assert result.returncode == FAIL_CLOSED


def test_fail_closed_on_prefix_containing_regex_metacharacters(tmp_path):
    # ".*" as a prefix would match every PR title. The gate must refuse it
    # rather than compile it -- this is the fail-open path the guard exists for.
    envelope = write_envelope(tmp_path, {"work_package_prefix": ".*"})
    result = run_gate(env_text="feat: no ticket at all", envelope=envelope)
    assert result.returncode == FAIL_CLOSED
    assert "plausible" in result.stderr


def test_fail_closed_on_non_string_prefix(tmp_path):
    envelope = write_envelope(tmp_path, {"work_package_prefix": 42})
    result = run_gate(env_text=f"feat: work ({WP_ID})", envelope=envelope)
    assert result.returncode == FAIL_CLOSED


def test_configuration_is_checked_before_input(tmp_path):
    # Order matters for diagnosis: a project whose envelope is broken AND whose
    # PR cites no ticket should be told about the envelope, because that is the
    # failure the operator must fix first.
    result = run_gate(env_text="", envelope=str(tmp_path / "missing.json"))
    assert result.returncode == FAIL_CLOSED
    assert "unreadable" in result.stderr
