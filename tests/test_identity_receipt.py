"""The AIS sandbox computes a level from evidence, and refuses to invent one.

`SECB-WP-FWK-081` (issue #145).

`#144` refuses public disclosure below `AIS4`. That refusal is only useful if a level can be
computed from evidence, so this suite builds signed, OIDC-**shaped** fixtures and checks
each rung is earned. Three limits are asserted, not assumed:

* the sandbox ceiling is `AIS3` — no fixture reaches the `AIS4` that `#144` needs;
* `PRODUCTION_AIS_LEVEL` is `NOT_OBSERVED` on **every** run, successes included;
* nothing here creates an App, installation, secret, token or permission.

Fixtures are signed with a shared secret. That proves the fixture was not edited and
nothing about an issuer — real OIDC is asymmetric against a published JWKS — which is why
the registry must declare `not_oidc: true`.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check_identity_receipt.py"
SCHEMA = REPO_ROOT / "config" / "agent_identity_registry.schema.json"

OK = 0
FAIL = 2

KEY = "fixture-key-not-a-credential"
ROLES = ("AUTHORITY_RESOLVER", "DISCLOSURE_CLASSIFIER", "EFFECT_EXECUTOR")


def principal(role: str, index: int, **overrides) -> dict:
    data = {
        "app_id": f"App{index}",
        "installation_id": f"Inst{index}",
        "custody_domain": f"broker-{index}",
        "policy_domain": f"policy-{index}",
        "failure_domain": f"failure-{index}",
        "token_scope": {
            "repositories": ["bstBizEra/secb_pf"],
            "permissions": {"contents": "read"},
            "expires_in_seconds": 3600,
        },
        "oidc_claims": {
            "repository_id": "R_kgDOsecb",
            "run_id": f"100{index}",
            "workflow_ref": "bstBizEra/secb_pf/.github/workflows/ais.yml@refs/heads/main",
            "workflow_sha": "f1b2516688f94c7aad9a0b1b9c060abd023c86bf",
        },
        "revocation": {"http_status": 204, "reuse_after_revoke": "DENIED"},
    }
    for key, value in overrides.items():
        if key in ("token_scope", "oidc_claims", "revocation") and isinstance(value, dict):
            data[key].update(value)
        elif value is None:
            data.pop(key, None)
        else:
            data[key] = value
    return data


def registry(tmp_path, principals=None, sandbox=None, sign_with=KEY, **body_overrides) -> str:
    body = {
        "schema": "secb.agent-identity-registry/v1",
        "sandbox": sandbox if sandbox is not None else {
            "is_sandbox": True,
            "production_ais_level": "NOT_OBSERVED",
            "max_computable_level": "AIS3_CUSTODY_SEPARATED",
            "why_capped": (
                "AIS4 requires independent failure domains, which one simulated environment "
                "cannot exhibit."
            ),
        },
        "principals": principals if principals is not None else {
            role: principal(role, i) for i, role in enumerate(ROLES, start=1)
        },
    }
    body.update(body_overrides)
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    signature = hmac.new(sign_with.encode(), canonical, hashlib.sha256).hexdigest()
    document = dict(body)
    document["signature"] = {
        "algorithm": "HMAC_SHA256_FIXTURE",
        "not_oidc": True,
        "value": signature,
    }
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return str(path)


def run(path: str, key: str = KEY) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True, text=True, timeout=30, cwd=str(REPO_ROOT),
        env={"PATH": "/usr/bin:/bin", "REGISTRY": path, "FIXTURE_KEY": key},
    )


def observe(path: str) -> dict:
    result = run(path)
    assert result.returncode == OK, result.stderr
    return json.loads(result.stdout)


# --- the ceiling, asserted on every path --------------------------------------


def test_production_is_never_observed_even_on_success(tmp_path):
    observation = observe(registry(tmp_path))
    assert observation["PRODUCTION_AIS_LEVEL"] == "NOT_OBSERVED"
    assert observation["SANDBOX_AIS_LEVEL"] == "AIS3_CUSTODY_SEPARATED"
    assert observation["sandbox_ceiling"] == "AIS3_CUSTODY_SEPARATED"
    assert any("AIS4" in item for item in observation["not_proven"])


def test_a_registry_claiming_a_higher_ceiling_is_refused(tmp_path):
    """The whole point of the cap: a fixture must not advance #144's gate."""
    path = registry(tmp_path, sandbox={
        "is_sandbox": True,
        "production_ais_level": "NOT_OBSERVED",
        "max_computable_level": "AIS4_INDEPENDENT_DOMAINS",
        "why_capped": "x" * 41,
    })
    result = run(path)
    assert result.returncode == FAIL
    assert "exceeds the sandbox ceiling" in result.stderr
    assert "independent failure domains" in result.stderr


def test_a_registry_claiming_production_observation_is_refused(tmp_path):
    path = registry(tmp_path, sandbox={
        "is_sandbox": True,
        "production_ais_level": "AIS4_INDEPENDENT_DOMAINS",
        "max_computable_level": "AIS3_CUSTODY_SEPARATED",
        "why_capped": "x" * 41,
    })
    result = run(path)
    assert result.returncode == FAIL
    assert "cannot observe production" in result.stderr


# --- AIS1: workflow binding ---------------------------------------------------


def test_a_ref_without_a_sha_does_not_reach_ais1(tmp_path):
    """A ref names a path; a sha pins its content."""
    principals = {r: principal(r, i) for i, r in enumerate(ROLES, start=1)}
    principals["AUTHORITY_RESOLVER"]["oidc_claims"].pop("workflow_sha")
    result = run(registry(tmp_path, principals=principals))
    assert result.returncode == FAIL
    assert "workflow_sha" in result.stderr
    assert "moveable target" in result.stderr


def test_a_reusable_workflow_must_bind_the_job_definition(tmp_path):
    """Under a reusable workflow the executing definition is not the entry workflow."""
    principals = {r: principal(r, i) for i, r in enumerate(ROLES, start=1)}
    principals["EFFECT_EXECUTOR"]["oidc_claims"]["job_workflow_ref"] = "org/reusable/.github/workflows/x.yml@main"
    result = run(registry(tmp_path, principals=principals))
    assert result.returncode == FAIL
    assert "job_workflow_sha" in result.stderr


def test_actor_id_is_prohibited_as_principal_evidence(tmp_path):
    """It is the account that started the workflow, not the agent holding the role."""
    principals = {r: principal(r, i) for i, r in enumerate(ROLES, start=1)}
    principals["DISCLOSURE_CLASSIFIER"]["oidc_claims"]["actor_id"] = "BizEraERP"
    result = run(registry(tmp_path, principals=principals))
    assert result.returncode == FAIL
    assert "prohibited as principal evidence" in result.stderr


# --- AIS2: platform principals ------------------------------------------------


def test_shared_app_identity_stops_at_ais1(tmp_path):
    """Distinct OIDC claims with one App is one principal wearing several role labels."""
    principals = {r: principal(r, 1) for r in ROLES}
    for i, role in enumerate(ROLES, start=1):
        principals[role]["oidc_claims"]["run_id"] = f"200{i}"
        principals[role]["custody_domain"] = f"broker-{i}"
        principals[role]["policy_domain"] = f"policy-{i}"
    assert observe(registry(tmp_path, principals=principals))["SANDBOX_AIS_LEVEL"] == (
        "AIS1_WORKFLOW_BOUND"
    )


# --- AIS3: custody and policy separation --------------------------------------


@pytest.mark.parametrize("field", ["custody_domain", "policy_domain"])
def test_a_shared_domain_stops_at_ais2(tmp_path, field):
    """Separate principals sharing a broker or a policy is one domain with several names."""
    principals = {r: principal(r, i, **{field: "shared"}) for i, r in enumerate(ROLES, start=1)}
    assert observe(registry(tmp_path, principals=principals))["SANDBOX_AIS_LEVEL"] == (
        "AIS2_PLATFORM_PRINCIPALS"
    )


@pytest.mark.parametrize("scope,fragment", [
    ({"repositories": ["*"]}, "all repositories"),
    ({"permissions": {}}, "repositories and permissions"),
    ({"expires_in_seconds": 7200}, "exceeds one hour"),
])
def test_an_hour_ceiling_alone_is_not_least_privilege(tmp_path, scope, fragment):
    principals = {r: principal(r, i) for i, r in enumerate(ROLES, start=1)}
    principals["EFFECT_EXECUTOR"]["token_scope"].update(scope)
    result = run(registry(tmp_path, principals=principals))
    assert result.returncode == FAIL
    assert fragment in result.stderr


@pytest.mark.parametrize("reuse", ["ACCEPTED", "NOT_TESTED"])
def test_revocation_is_a_behavioural_claim(tmp_path, reuse):
    """A 204 says a call was accepted, not that the token stopped working."""
    principals = {r: principal(r, i) for i, r in enumerate(ROLES, start=1)}
    principals["EFFECT_EXECUTOR"]["revocation"]["reuse_after_revoke"] = reuse
    result = run(registry(tmp_path, principals=principals))
    assert result.returncode == FAIL
    assert "Only DENIED is evidence" in result.stderr


# --- fail-closed --------------------------------------------------------------


def test_a_forged_signature_is_refused(tmp_path):
    result = run(registry(tmp_path, sign_with="the-wrong-key"))
    assert result.returncode == FAIL
    assert "signature is absent or does not match" in result.stderr


def test_a_signature_presented_as_oidc_is_refused(tmp_path):
    path = Path(registry(tmp_path))
    document = json.loads(path.read_text(encoding="utf-8"))
    document["signature"]["not_oidc"] = False
    path.write_text(json.dumps(document), encoding="utf-8")
    result = run(str(path))
    assert result.returncode == FAIL
    assert "must not be presented as OIDC verification" in result.stderr


def test_a_single_principal_separates_nothing(tmp_path):
    principals = {"AUTHORITY_RESOLVER": principal("AUTHORITY_RESOLVER", 1)}
    result = run(registry(tmp_path, principals=principals))
    assert result.returncode == FAIL
    assert "separates nothing" in result.stderr


def test_an_absent_registry_fails_closed(tmp_path):
    result = run(str(tmp_path / "absent.json"))
    assert result.returncode == FAIL
    assert "unreadable or unparseable" in result.stderr


def test_no_registry_path_fails_closed():
    result = subprocess.run(
        [sys.executable, str(SCRIPT)], capture_output=True, text=True, timeout=30,
        cwd=str(REPO_ROOT), env={"PATH": "/usr/bin:/bin"},
    )
    assert result.returncode == FAIL
    assert "REGISTRY is required" in result.stderr


# --- the schema states its own limits -----------------------------------------


def test_the_schema_pins_production_and_the_ceiling():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    sandbox = schema["properties"]["sandbox"]["properties"]
    assert sandbox["production_ais_level"]["const"] == "NOT_OBSERVED"
    assert sandbox["max_computable_level"]["const"] == "AIS3_CUSTODY_SEPARATED"
    assert schema["properties"]["signature"]["properties"]["not_oidc"]["const"] is True


def test_the_schema_keeps_the_four_terms_apart():
    """One field would let any of them stand in for the others."""
    fields = json.loads(SCHEMA.read_text(encoding="utf-8"))["properties"]["principals"][
        "additionalProperties"]["required"]
    for term in ("app_id", "installation_id", "custody_domain", "policy_domain", "failure_domain"):
        assert term in fields, f"the registry must record {term} separately"
