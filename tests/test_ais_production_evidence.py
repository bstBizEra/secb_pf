"""SECB-WP-FWK-089, issue #158 -- the AIS4 production evidence verifier.

Every refusal below is produced by INVOKING scripts/check_ais_production_evidence.py as a
subprocess against a mutated document. Importing the module and calling `evaluate` would
test the function; the shipped surface is a command, and a command can raise ImportError on
every invocation while its module's unit tests stay green.

The accept path is tested too, so no refusal is vacuous -- a verifier that refuses
everything passes a refusal-only suite perfectly.

The one thing this file may NOT do is reach AIS4 from a document alone. The out-of-band
`EXPECT_JWKS_DIGEST` test proves the AIS4 rung is reachable when an external fetch confirms
the key set, and the fixture test proves the shipped fixture does not reach it.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "scripts" / "check_ais_production_evidence.py"
SCHEMA_PATH = ROOT / "config" / "ais_production_evidence.schema.json"

GITHUB_ISSUER = "https://token.actions.githubusercontent.com"
MAIN_SHA = "f5aa26aef86250a7dfb68223f8f0b5d63f54ea52"
WORKFLOW_SHA = "5cba625d2ad6fc20b48cc4c5afb9ea18416c03d8"

# A 2048-bit RSA keypair generated once for these tests and hardcoded so runs are
# deterministic. It signs nothing outside this file and guards nothing. Hardcoding is the
# point: generating a keypair per run would make the suite slow and non-reproducible, and a
# pure-Python 2048-bit keygen is a lot of code to own for no test value.
_N_HEX = (
    "cf4883ab6da0b694091bbbfa1a5a3c67552e32bf1a99b071f305bc8d6155ab87"
    "b54c7e2cab9612a0f8716081924b00bf2d16d6239043526cfffc65647bb281a4"
    "6a74297a31869a3c10e2ab403fe36c38b8f84a7edc32538453ec4be5bb72ab8c"
    "e52dc2536b770a18d16f19c6591b61b8d0e37a9e3b6c47f89811847d3ad9bc31"
    "37e60b7ade2dbb9eed6c8649dd6bb3810e880568b903b8292fb87275ceb5f397"
    "df7f2854439b3b2f3078e9715e20fc910bb7ea756ab9f5ea431567b3055d59ed"
    "384a08aa06c1984e80ac2bce558aaf3ab0291a41123a97212bc9dbc0c032fdfb"
    "2e8e5636a7e43a758c5e6fb22eb51a81f14b2e27fcea7d161346f1e8422ea319"
)
_D_HEX = (
    "21fbb0fe93781446dbe16ca599d96e6ac087d4f108d2e69f1fe9325af978baa9"
    "029bba59e77db0ab2c602622c811bcdb1af0d205bd9a93f263db84e1fef7aa92"
    "82936dd367383aa41b5e9615f0038094221b2ed772915ba8e7bb674c1039c20f"
    "54e97621080ed99c6d05aa739edb42dfb27b80f85d24a8fe042c670cc2efbc8f"
    "07a2d5859d95c222a53163b26997d36ff35f957abf5e03ee7c6e12a51c9b7b58"
    "e5e6df501b8ece13aee4c5ff93615a6fbbc897ef07b12edb3cd0c25eb3f4c60d"
    "3b2836ff2956284e88347e1afe8ba706010695dcef996d9a687cb6fe53fb12a2"
    "7b7917a6fe4e68b5b42f50acd1056e4965568e7c9a4f852d53fd08230a604e7b"
)
N = int(_N_HEX, 16)
D = int(_D_HEX, 16)
E = 65537
KID = "secb-test-key-1"
SHA256_DIGESTINFO = binascii.unhexlify("3031300d060960864801650304020105000420")


def b64u(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def canonical(payload: object) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_digest(payload: object) -> str:
    return "sha256:" + hashlib.sha256(canonical(payload)).hexdigest()


def rsa_sign(message: bytes) -> bytes:
    """EMSA-PKCS1-v1_5 sign with the test key. Mirrors the verifier's expected block."""
    k = (N.bit_length() + 7) // 8
    tail = SHA256_DIGESTINFO + hashlib.sha256(message).digest()
    em = b"\x00\x01" + b"\xff" * (k - len(tail) - 3) + b"\x00" + tail
    return pow(int.from_bytes(em, "big"), D, N).to_bytes(k, "big")


def jwt(claims: dict, *, alg: str = "RS256", kid: str = KID, sign: bool = True) -> str:
    header = b64u(canonical({"alg": alg, "kid": kid, "typ": "JWT"}))
    payload = b64u(canonical(claims))
    if not sign:
        return f"{header}.{payload}.{b64u(b'not-a-signature-just-bytes-of-the-right-shape')}"
    return f"{header}.{payload}.{b64u(rsa_sign(f'{header}.{payload}'.encode('ascii')))}"


JWKS_KEYS = [{
    "kid": KID,
    "kty": "RSA",
    "alg": "RS256",
    "n": b64u(N.to_bytes((N.bit_length() + 7) // 8, "big")),
    "e": b64u(E.to_bytes(3, "big")),
}]


def principal(role: str, index: int, *, app: str | None = None) -> dict:
    return {
        "app_id": app or f"app-{index}",
        "installation_id": f"inst-{index}",
        "custody_domain": f"custody-{index}",
        "policy_domain": f"policy-{index}",
        # Administered by a DIFFERENT domain: policy-0 administers policy-1 and vice versa.
        "policy_administered_by": f"policy-{(index + 1) % 4}",
        "token_scope": {
            "repositories": ["bstBizEra/secb_pf"],
            "permissions": {"contents": "read"},
            "issued_at": "2026-08-17T10:00:00+00:00",
            "expires_at": "2026-08-17T10:45:00+00:00",
        },
        "revocation": {
            "challenge_id": f"chal-{index}",
            "revoked_at": "2026-08-17T10:20:00+00:00",
            "reuse_attempted_at": "2026-08-17T10:21:00+00:00",
            "reuse_result": "DENIED",
        },
        "oidc": {
            "kid": KID,
            "token": jwt({
                "iss": GITHUB_ISSUER,
                "aud": "bstBizEra",
                "sub": f"repo:bstBizEra/secb_pf:role:{role}",
                "repository_id": "1029384756",
                "run_id": f"3203{index}",
                "workflow_ref": "bstBizEra/secb_pf/.github/workflows/ci.yml@refs/heads/main",
                "workflow_sha": WORKFLOW_SHA,
                "job_workflow_ref": "bstBizEra/secb_pf/.github/workflows/ci.yml@refs/heads/main",
            }),
        },
    }


SNAPSHOT = {
    "repository_id": "1029384756",
    "main_sha": MAIN_SHA,
    "workflow_sha": WORKFLOW_SHA,
    "job_workflow_ref": "bstBizEra/secb_pf/.github/workflows/ci.yml@refs/heads/main",
}


def evidence() -> dict:
    """A document that is internally sound and honestly caps at AIS3.

    Four principals: two voters, one executor, one readback verifier. LOCAL_FIXTURE keys,
    because that is the truth about a key set a test wrote.
    """
    roles = ["voter_a", "voter_b", "executor", "readback"]
    return {
        "schema": "secb.ais-production-evidence/v1",
        "snapshot": deepcopy(SNAPSHOT),
        "jwks": {
            "provenance": "LOCAL_FIXTURE",
            "issuer": GITHUB_ISSUER,
            "keys": deepcopy(JWKS_KEYS),
        },
        "principals": {role: principal(role, i) for i, role in enumerate(roles)},
        "ballots": [
            {
                "principal": "voter_a",
                "snapshot_digest": sha256_digest(SNAPSHOT),
                "decision": "APPROVE",
                "cast_at": "2026-08-17T10:05:00+00:00",
            },
            {
                "principal": "voter_b",
                "snapshot_digest": sha256_digest(SNAPSHOT),
                "decision": "APPROVE",
                "cast_at": "2026-08-17T10:06:00+00:00",
            },
        ],
        "roles": {"executor": "executor", "readback_verifier": "readback"},
        "decision_receipt_digest": sha256_digest({"decision": "APPROVE"}),
    }


def run(document: dict, tmp_path: Path, **env_extra: str) -> subprocess.CompletedProcess:
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    env = {
        **os.environ,
        "EVIDENCE": str(path),
        "PYTHONDONTWRITEBYTECODE": "1",
        **env_extra,
    }
    return subprocess.run(
        [sys.executable, str(TOOL)], capture_output=True, text=True, env=env, check=False
    )


def refuses(document: dict, tmp_path: Path, fragment: str, **env_extra: str) -> str:
    result = run(document, tmp_path, **env_extra)
    assert result.returncode == 2, f"expected refusal, got {result.returncode}: {result.stdout}"
    assert "REFUSED (closed)" in result.stderr
    assert fragment in result.stderr, f"{fragment!r} not in {result.stderr!r}"
    return result.stderr


# --------------------------------------------------------------------------- accept path


def test_sound_fixture_is_accepted_and_caps_below_ais4(tmp_path):
    """The fixture is well-formed, so it is NOT refused -- and it does not reach AIS4."""
    result = run(evidence(), tmp_path)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["OBSERVED_LEVEL"] == "AIS3_CUSTODY_SEPARATED"
    assert report["PRODUCTION_AIS_LEVEL"] == "NOT_OBSERVED"
    assert report["unsatisfied"] == ["SIGNER_VERIFIED"]
    assert report["confers_merge_authority"] is False
    assert report["conjuncts"]["OIDC_BOUND"]["observed"] is True


def test_signature_verification_is_real_not_structural(tmp_path):
    """Flip one byte of a signed token's payload: the signature must stop verifying.

    Without this, every other test could pass against a verifier that only counts dots.
    """
    document = evidence()
    token = document["principals"]["voter_a"]["oidc"]["token"]
    header, payload, signature = token.split(".")
    tampered = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    tampered["sub"] = "repo:bstBizEra/secb_pf:role:someone_else"
    document["principals"]["voter_a"]["oidc"]["token"] = (
        f"{header}.{b64u(canonical(tampered))}.{signature}"
    )
    refuses(document, tmp_path, "signature does not verify")


def test_padding_slack_forgery_is_refused(tmp_path):
    """The signed block must match EXACTLY, not merely end with the right DigestInfo.

    This document's signature is produced with the private key over a block whose padding
    is 0xab instead of 0xff, so the recovered block carries a correct SHA-256 DigestInfo and
    a correct hash in the correct position -- everything a verifier that SCANS for the
    digest would accept. Slack anywhere in the padding is where Bleichenbacher-style
    forgeries live, which is why the verifier rebuilds the expected block and compares the
    whole thing. Weaken that comparison to a suffix check and this test is the one that
    fails.
    """
    document = evidence()
    header, payload, _ = document["principals"]["voter_a"]["oidc"]["token"].split(".")
    message = f"{header}.{payload}".encode("ascii")
    k = (N.bit_length() + 7) // 8
    tail = SHA256_DIGESTINFO + hashlib.sha256(message).digest()
    slack = b"\x00\x01" + b"\xab" * (k - len(tail) - 3) + b"\x00" + tail
    forged = pow(int.from_bytes(slack, "big"), D, N).to_bytes(k, "big")
    document["principals"]["voter_a"]["oidc"]["token"] = f"{header}.{payload}.{b64u(forged)}"
    refuses(document, tmp_path, "does not verify against the declared key")


def test_ais4_is_reachable_only_with_out_of_band_confirmation(tmp_path):
    """The top rung must be reachable, or the ladder is decorative -- but only externally.

    Same document twice. Without EXPECT_JWKS_DIGEST it caps at AIS3; with the digest
    supplied out of band -- standing in for the job that actually fetched the key set -- it
    reaches AIS4. That is the Tranche A/Tranche B boundary expressed as a test.
    """
    document = evidence()
    document["jwks"]["provenance"] = "ISSUER_DISCOVERY"
    document["jwks"]["discovery"] = {
        "url": f"{GITHUB_ISSUER}/.well-known/jwks",
        "fetched_at": "2026-08-17T10:00:00+00:00",
        "response_digest": sha256_digest(JWKS_KEYS),
    }

    without = json.loads(run(document, tmp_path).stdout)
    assert without["PRODUCTION_AIS_LEVEL"] == "NOT_OBSERVED"
    assert without["unsatisfied"] == ["SIGNER_VERIFIED"]
    assert "cannot confirm its own fetch" in without["conjuncts"]["SIGNER_VERIFIED"]["note"]

    with_oob = json.loads(
        run(document, tmp_path, EXPECT_JWKS_DIGEST=sha256_digest(JWKS_KEYS)).stdout
    )
    assert with_oob["OBSERVED_LEVEL"] == "AIS4_INDEPENDENT_DOMAINS"
    assert with_oob["PRODUCTION_AIS_LEVEL"] == "AIS4_INDEPENDENT_DOMAINS"
    assert with_oob["unsatisfied"] == []
    assert with_oob["confers_merge_authority"] is False


# ------------------------------------------------------- laundering and claimed levels


def test_document_may_not_claim_its_own_level(tmp_path):
    for field in ("production_ais_level", "observed_level", "claimed_level"):
        document = evidence()
        document[field] = "AIS4_INDEPENDENT_DOMAINS"
        refuses(document, tmp_path, "the level is COMPUTED")


def test_fixture_keys_may_not_be_presented_as_issuer_discovery(tmp_path):
    document = evidence()
    document["jwks"]["provenance"] = "ISSUER_DISCOVERY"
    refuses(document, tmp_path, "no discovery record")


def test_discovery_record_must_digest_the_keys_it_accompanies(tmp_path):
    document = evidence()
    document["jwks"]["provenance"] = "ISSUER_DISCOVERY"
    document["jwks"]["discovery"] = {
        "url": f"{GITHUB_ISSUER}/.well-known/jwks",
        "fetched_at": "2026-08-17T10:00:00+00:00",
        "response_digest": sha256_digest({"some": "other bytes"}),
    }
    refuses(document, tmp_path, "does not digest the key set")


def test_out_of_band_digest_disagreement_is_refused_not_downgraded(tmp_path):
    """A wrong out-of-band digest is a contradiction, not mere absence."""
    document = evidence()
    document["jwks"]["provenance"] = "ISSUER_DISCOVERY"
    document["jwks"]["discovery"] = {
        "url": f"{GITHUB_ISSUER}/.well-known/jwks",
        "fetched_at": "2026-08-17T10:00:00+00:00",
        "response_digest": sha256_digest(JWKS_KEYS),
    }
    refuses(
        document, tmp_path, "does not match the document",
        EXPECT_JWKS_DIGEST="sha256:" + "0" * 64,
    )


def test_discovery_url_outside_the_issuer_is_refused(tmp_path):
    document = evidence()
    document["jwks"]["provenance"] = "ISSUER_DISCOVERY"
    document["jwks"]["discovery"] = {
        "url": "https://attacker.example/.well-known/jwks",
        "fetched_at": "2026-08-17T10:00:00+00:00",
        "response_digest": sha256_digest(JWKS_KEYS),
    }
    refuses(document, tmp_path, "not under the declared issuer")


# ------------------------------------------------------------------ separation dimensions


def test_shared_app_installation_is_refused(tmp_path):
    document = evidence()
    document["principals"]["voter_b"]["app_id"] = document["principals"]["voter_a"]["app_id"]
    document["principals"]["voter_b"]["installation_id"] = (
        document["principals"]["voter_a"]["installation_id"]
    )
    refuses(document, tmp_path, "share an App/installation")


def test_shared_custody_domain_is_refused(tmp_path):
    document = evidence()
    document["principals"]["voter_b"]["custody_domain"] = "custody-0"
    refuses(document, tmp_path, "share a credential custody domain")


def test_shared_policy_domain_is_refused(tmp_path):
    document = evidence()
    document["principals"]["voter_b"]["policy_domain"] = "policy-0"
    document["principals"]["voter_b"]["policy_administered_by"] = "policy-2"
    refuses(document, tmp_path, "share a policy domain")


def test_self_administered_policy_is_refused(tmp_path):
    document = evidence()
    document["principals"]["voter_a"]["policy_administered_by"] = "policy-0"
    refuses(document, tmp_path, "its own auditor")


def test_executor_may_not_vote(tmp_path):
    document = evidence()
    document["ballots"][1] = {
        "principal": "executor",
        "snapshot_digest": sha256_digest(SNAPSHOT),
        "decision": "APPROVE",
        "cast_at": "2026-08-17T10:06:00+00:00",
    }
    refuses(document, tmp_path, "also cast a ballot")


def test_executor_may_not_verify_its_own_readback(tmp_path):
    document = evidence()
    document["roles"]["readback_verifier"] = "executor"
    refuses(document, tmp_path, "also the readback verifier")


# ------------------------------------------------------------------ scope and lifetime


@pytest.mark.parametrize("repositories", [["*"], ["bstBizEra/*"]])
def test_wildcard_repository_scope_is_refused(tmp_path, repositories):
    document = evidence()
    document["principals"]["voter_a"]["token_scope"]["repositories"] = repositories
    refuses(document, tmp_path, "is a wildcard")


def test_admin_permission_is_refused(tmp_path):
    document = evidence()
    document["principals"]["voter_a"]["token_scope"]["permissions"] = {"administration": "admin"}
    refuses(document, tmp_path, "administrative principal")


def test_excessive_token_lifetime_is_refused(tmp_path):
    document = evidence()
    document["principals"]["voter_a"]["token_scope"]["expires_at"] = "2026-08-17T14:00:00+00:00"
    refuses(document, tmp_path, "over the 3600s ceiling")


def test_expiry_before_issue_is_refused(tmp_path):
    document = evidence()
    document["principals"]["voter_a"]["token_scope"]["expires_at"] = "2026-08-17T09:00:00+00:00"
    refuses(document, tmp_path, "expires at or before it was issued")


# --------------------------------------------------------------- snapshot and decisions


def test_stale_snapshot_is_refused_against_an_expected_sha(tmp_path):
    refuses(
        evidence(), tmp_path, "is not the expected",
        EXPECT_MAIN_SHA="0" * 40,
    )


def test_ballot_bound_to_a_different_snapshot_is_refused(tmp_path):
    document = evidence()
    document["ballots"][1]["snapshot_digest"] = "sha256:" + "1" * 64
    refuses(document, tmp_path, "not a quorum")


def test_snapshot_edit_invalidates_every_ballot_digest(tmp_path):
    """Editing the snapshot must break the binding, not silently re-anchor it."""
    document = evidence()
    document["snapshot"]["main_sha"] = "a" * 40
    refuses(document, tmp_path, "the snapshot digests to")


def test_one_principal_may_not_cast_two_ballots(tmp_path):
    document = evidence()
    document["ballots"][1]["principal"] = "voter_a"
    refuses(document, tmp_path, "cast more than one ballot")


def test_ballot_from_an_unknown_principal_is_refused(tmp_path):
    document = evidence()
    document["ballots"][1]["principal"] = "ghost"
    refuses(document, tmp_path, "absent from the evidence")


def test_single_approval_does_not_satisfy_independent_decisions(tmp_path):
    """Not a contradiction -- an honest shortfall. It reports, it does not refuse."""
    document = evidence()
    document["ballots"][1]["decision"] = "ABSTAIN"
    result = run(document, tmp_path)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["PRODUCTION_AIS_LEVEL"] == "NOT_OBSERVED"
    assert "INDEPENDENT_DECISIONS" in report["unsatisfied"]


# ------------------------------------------------------------------------- revocation


def test_reuse_accepted_after_revocation_is_refused(tmp_path):
    document = evidence()
    document["principals"]["voter_a"]["revocation"]["reuse_result"] = "ACCEPTED"
    refuses(document, tmp_path, "does not deny reuse is a log entry")


def test_reuse_attempted_before_revocation_is_refused(tmp_path):
    document = evidence()
    document["principals"]["voter_a"]["revocation"]["reuse_attempted_at"] = (
        "2026-08-17T10:19:00+00:00"
    )
    refuses(document, tmp_path, "at or before revocation")


def test_revocation_not_attempted_is_a_shortfall_not_a_contradiction(tmp_path):
    document = evidence()
    document["principals"]["voter_a"]["revocation"]["reuse_result"] = "NOT_ATTEMPTED"
    result = run(document, tmp_path)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert "REVOCATION_BEHAVIOUR_OBSERVED" in report["unsatisfied"]
    assert report["PRODUCTION_AIS_LEVEL"] == "NOT_OBSERVED"


# ------------------------------------------------------------------------ token binding


def test_alg_none_is_refused(tmp_path):
    document = evidence()
    document["principals"]["voter_a"]["oidc"]["token"] = jwt(
        {"iss": GITHUB_ISSUER}, alg="none", sign=False
    )
    refuses(document, tmp_path, "algorithm-confusion")


def test_hs256_against_the_rsa_key_set_is_refused(tmp_path):
    document = evidence()
    document["principals"]["voter_a"]["oidc"]["token"] = jwt(
        {"iss": GITHUB_ISSUER}, alg="HS256", sign=False
    )
    refuses(document, tmp_path, "only RS256 is verified")


def test_unknown_kid_is_refused(tmp_path):
    document = evidence()
    document["principals"]["voter_a"]["oidc"]["kid"] = "no-such-key"
    refuses(document, tmp_path, "no key in the set matches kid")


def test_token_kid_disagreeing_with_the_declared_key_is_refused(tmp_path):
    document = evidence()
    document["principals"]["voter_a"]["oidc"]["token"] = jwt({"iss": GITHUB_ISSUER}, kid="other")
    refuses(document, tmp_path, "does not match the key")


def test_wrong_issuer_in_the_signed_token_is_refused(tmp_path):
    document = evidence()
    claims = {
        "iss": "https://attacker.example",
        "repository_id": "1029384756",
        "workflow_sha": WORKFLOW_SHA,
        "job_workflow_ref": SNAPSHOT["job_workflow_ref"],
    }
    document["principals"]["voter_a"]["oidc"]["token"] = jwt(claims)
    refuses(document, tmp_path, "is not the declared issuer")


@pytest.mark.parametrize("claim", ["repository_id", "workflow_sha", "job_workflow_ref"])
def test_token_claim_disagreeing_with_the_snapshot_is_refused(tmp_path, claim):
    document = evidence()
    claims = {
        "iss": GITHUB_ISSUER,
        "repository_id": "1029384756",
        "workflow_sha": WORKFLOW_SHA,
        "job_workflow_ref": SNAPSHOT["job_workflow_ref"],
    }
    claims[claim] = "bound-to-something-else"
    document["principals"]["voter_a"]["oidc"]["token"] = jwt(claims)
    refuses(document, tmp_path, "not this one")


@pytest.mark.parametrize("claim", ["repository_id", "workflow_sha", "job_workflow_ref"])
def test_missing_bound_claim_is_refused(tmp_path, claim):
    document = evidence()
    claims = {
        "iss": GITHUB_ISSUER,
        "repository_id": "1029384756",
        "workflow_sha": WORKFLOW_SHA,
        "job_workflow_ref": SNAPSHOT["job_workflow_ref"],
    }
    del claims[claim]
    document["principals"]["voter_a"]["oidc"]["token"] = jwt(claims)
    refuses(document, tmp_path, f"missing the {claim} claim")


def test_weak_modulus_is_refused(tmp_path):
    """A 1024-bit key with a correct signature over it still fails: strength is checked."""
    document = evidence()
    small_n = (1 << 1023) | 1
    document["jwks"]["keys"][0]["n"] = b64u(small_n.to_bytes(128, "big"))
    refuses(document, tmp_path, "under 2048 is not acceptable")


def test_even_public_exponent_is_refused(tmp_path):
    document = evidence()
    document["jwks"]["keys"][0]["e"] = b64u((4).to_bytes(1, "big"))
    refuses(document, tmp_path, "not an odd integer")


def test_signature_of_the_wrong_length_is_refused(tmp_path):
    document = evidence()
    header, payload, _ = document["principals"]["voter_a"]["oidc"]["token"].split(".")
    document["principals"]["voter_a"]["oidc"]["token"] = f"{header}.{payload}.{b64u(b'short')}"
    refuses(document, tmp_path, "the modulus is")


def test_malformed_token_shape_is_refused(tmp_path):
    document = evidence()
    document["principals"]["voter_a"]["oidc"]["token"] = "not.a.jws.at.all"
    refuses(document, tmp_path, "compact JWS")


# ------------------------------------------------------------------- structural refusals


def test_wrong_schema_is_refused(tmp_path):
    document = evidence()
    document["schema"] = "secb.agent-identity-registry/v1"
    refuses(document, tmp_path, "expected 'secb.ais-production-evidence/v1'")


def test_single_principal_separates_nothing(tmp_path):
    document = evidence()
    document["principals"] = {"only": document["principals"]["voter_a"]}
    document["ballots"] = document["ballots"][:1]
    refuses(document, tmp_path, "separates nothing")


def test_missing_evidence_path_is_refused(tmp_path):
    result = subprocess.run(
        [sys.executable, str(TOOL)],
        capture_output=True, text=True, check=False,
        env={**os.environ, "EVIDENCE": "", "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert result.returncode == 2
    assert "EVIDENCE is required" in result.stderr


def test_unreadable_evidence_is_refused(tmp_path):
    result = subprocess.run(
        [sys.executable, str(TOOL)],
        capture_output=True, text=True, check=False,
        env={
            **os.environ,
            "EVIDENCE": str(tmp_path / "absent.json"),
            "PYTHONDONTWRITEBYTECODE": "1",
        },
    )
    assert result.returncode == 2
    assert "unreadable or unparseable" in result.stderr


def test_attestation_claiming_verification_without_a_verifier_is_refused(tmp_path):
    document = evidence()
    document["attestation"] = {
        "bundle_digest": "sha256:" + "2" * 64,
        "signer_verified": True,
    }
    refuses(document, tmp_path, "no verified_by")


def test_roles_naming_an_absent_principal_are_refused(tmp_path):
    document = evidence()
    document["roles"]["executor"] = "phantom"
    refuses(document, tmp_path, "principals absent from the evidence")


def test_missing_roles_block_is_a_shortfall_not_a_contradiction(tmp_path):
    document = evidence()
    del document["roles"]
    result = run(document, tmp_path)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert "EFFECT_ROLE_SEPARATION" in report["unsatisfied"]


# ------------------------------------------------------------------------- the contract


def test_schema_file_declares_no_level_field():
    """The schema must not offer a field a document could assert its level with."""
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    properties = schema["properties"]
    for banned in ("ais_level", "level", "production_ais_level", "claimed_level"):
        assert banned not in properties
    assert schema["$id"] == "secb.ais-production-evidence/v1"


def test_fixture_satisfies_every_required_field_the_schema_declares():
    """Bind the schema to the verifier so they cannot drift apart silently.

    Nothing validates documents against this schema at runtime -- NFR-12 keeps the gates
    stdlib-only, and `jsonschema` is not stdlib. So the schema is a contract the verifier
    enforces by hand, and the failure mode is drift: a required field nobody checks, or a
    check for a field the schema never declared. This test walks the schema's `required`
    lists against the accepted fixture, which is the cheap half of that gap.
    SCHEMA_DECLARES != VERIFIER_ENFORCES, and this test is the only thing that notices.
    """
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    document = evidence()
    for field in schema["required"]:
        assert field in document, f"schema requires {field!r}; the fixture omits it"

    principal_schema = schema["properties"]["principals"]["additionalProperties"]
    for role, body in document["principals"].items():
        for field in principal_schema["required"]:
            assert field in body, f"{role}: schema requires {field!r}"
        for field in principal_schema["properties"]["token_scope"]["required"]:
            assert field in body["token_scope"], f"{role}.token_scope requires {field!r}"
        for field in principal_schema["properties"]["revocation"]["required"]:
            assert field in body["revocation"], f"{role}.revocation requires {field!r}"

    for ballot in document["ballots"]:
        for field in schema["properties"]["ballots"]["items"]["required"]:
            assert field in ballot, f"ballot requires {field!r}"


def test_tool_states_tranche_b_is_external(tmp_path):
    report = json.loads(run(evidence(), tmp_path).stdout)
    assert "EXTERNAL_AUTHORITY_REQUIRED" in report["tranche_b"]


def test_no_input_can_mark_tranche_b_complete(tmp_path):
    """Try the obvious levers. Each must leave PRODUCTION_AIS_LEVEL unmoved."""
    for lever in ("TRANCHE_B", "TRANCHE_B_COMPLETE", "PRODUCTION_AIS_LEVEL", "FORCE_AIS4"):
        report = json.loads(run(evidence(), tmp_path, **{lever: "AIS4_INDEPENDENT_DOMAINS"}).stdout)
        assert report["PRODUCTION_AIS_LEVEL"] == "NOT_OBSERVED", lever
