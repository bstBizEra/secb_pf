"""SECB-WP-FWK-089, issue #158 -- the AIS4 production evidence verifier (v2).

Every refusal is produced by INVOKING scripts/check_ais_production_evidence.py as a
subprocess against a mutated document. Importing `evaluate` would test the function; the
shipped surface is a command.

THE TEST THAT SHOULD HAVE EXISTED FIRST is `test_v1_counterexample_is_refused`. v1 of this
verifier checked RS256 correctly and still accepted one authentic token copied across every
role record, beside fabricated app/custody/policy strings and unsigned ballots, because the
signature covered the workflow context and nothing adjacent to it. Everything else here
exists to keep that class of hole closed:

    A VALID SIGNATURE OVER ONE PORTION OF A DOCUMENT MUST NOT LEND AUTHENTICITY TO
    ADJACENT UNSIGNED FIELDS.

The accept path is tested too, so no refusal is vacuous -- and the ceiling test asserts the
sound document reaches AIS3 and NOT AIS4, because AIS4 needs a live issuer fetch this tool
cannot perform.
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
KEYS_PATH = Path(__file__).parent / "fixtures" / "ais_test_keys.json"

GITHUB_ISSUER = "https://token.actions.githubusercontent.com"
JWKS_URI = f"{GITHUB_ISSUER}/.well-known/jwks"
MAIN_SHA = "f5aa26aef86250a7dfb68223f8f0b5d63f54ea52"
WORKFLOW_SHA = "7e478d714ef57f624de2ccddc5733697f06fb119"
JOB_WORKFLOW_REF = "bstBizEra/secb_pf/.github/workflows/ci.yml@refs/heads/main"
REPOSITORY_ID = "1029384756"
AUDIENCE = "bstBizEra"
SUBJECT_PREFIX = "repo:bstBizEra/secb_pf:"
NOW = "2026-08-17T10:30:00+00:00"

SHA256_DIGESTINFO = binascii.unhexlify("3031300d060960864801650304020105000420")

_MATERIAL = json.loads(KEYS_PATH.read_text(encoding="utf-8"))
E = _MATERIAL["e"]
PRIVATE = {k["kid"]: (int(k["n_hex"], 16), int(k["d_hex"], 16)) for k in _MATERIAL["keys"]}
ROLE_OF = {k["kid"]: (k["key_role"], k["owner"]) for k in _MATERIAL["keys"]}


def b64u(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def canonical(payload: object) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_digest(payload: object) -> str:
    return "sha256:" + hashlib.sha256(canonical(payload)).hexdigest()


def rsa_sign(kid: str, message: bytes, *, padding: int = 0xFF) -> bytes:
    """Sign with a test key. `padding` is a knob solely so a slack forgery can be built."""
    n, d = PRIVATE[kid]
    k = (n.bit_length() + 7) // 8
    tail = SHA256_DIGESTINFO + hashlib.sha256(message).digest()
    em = b"\x00\x01" + bytes([padding]) * (k - len(tail) - 3) + b"\x00" + tail
    return pow(int.from_bytes(em, "big"), d, n).to_bytes(k, "big")


def jwks_key(kid: str) -> dict:
    n, _ = PRIVATE[kid]
    key_role, owner = ROLE_OF[kid]
    return {
        "kid": kid,
        "kty": "RSA",
        "alg": "RS256",
        "key_role": key_role,
        "owner": owner,
        "n": b64u(n.to_bytes((n.bit_length() + 7) // 8, "big")),
        "e": b64u(E.to_bytes(3, "big")),
    }


JWKS_KEYS = [jwks_key(kid) for kid in PRIVATE]

SNAPSHOT = {
    "repository_id": REPOSITORY_ID,
    "main_sha": MAIN_SHA,
    "workflow_sha": WORKFLOW_SHA,
    "job_workflow_ref": JOB_WORKFLOW_REF,
}
SNAPSHOT_DIGEST = sha256_digest(SNAPSHOT)


def signed(kid: str, payload: dict, **overrides) -> dict:
    """Wrap a payload in a verified envelope. Overrides let a test break exactly one thing."""
    body = {"purpose": payload["purpose"], "snapshot_digest": SNAPSHOT_DIGEST, **payload}
    envelope = {"payload": body, "kid": kid, "signature": b64u(rsa_sign(kid, canonical(body)))}
    envelope.update(overrides)
    return envelope


def oidc_token(role: str, index: int, *, claims_override: dict | None = None,
               alg: str = "RS256", kid: str = "platform-oidc", sign_with: str | None = None,
               drop: str | None = None) -> str:
    claims = {
        "iss": GITHUB_ISSUER,
        "aud": AUDIENCE,
        "sub": f"{SUBJECT_PREFIX}role:{role}",
        "iat": "2026-08-17T10:00:00+00:00",
        "exp": "2026-08-17T10:45:00+00:00",
        "jti": f"jti-{index}",
        "repository_id": REPOSITORY_ID,
        "workflow_sha": WORKFLOW_SHA,
        "job_workflow_ref": JOB_WORKFLOW_REF,
    }
    claims.update(claims_override or {})
    if drop:
        claims.pop(drop, None)
    header = b64u(canonical({"alg": alg, "kid": kid, "typ": "JWT"}))
    payload = b64u(canonical(claims))
    signing_kid = sign_with or (kid if kid in PRIVATE else "platform-oidc")
    if alg != "RS256":
        return f"{header}.{payload}.{b64u(b'unsigned-bytes-of-plausible-shape')}"
    return f"{header}.{payload}.{b64u(rsa_sign(signing_kid, f'{header}.{payload}'.encode()))}"


ROLES = ["voter_a", "voter_b", "executor", "readback"]
# policy-admin-x administers policy-0 and policy-2; policy-admin-y administers policy-1 and
# policy-3. Both admin roots are OUTSIDE the set of principals' policy domains, so no
# principal's policy is governed from inside the set being validated.
POLICY_ADMIN = {0: "policy-admin-x", 1: "policy-admin-y", 2: "policy-admin-x", 3: "policy-admin-y"}


def principal(role: str, index: int) -> dict:
    principal_kid = f"principal-{role}"
    custody_root = f"custody-{index}"
    policy_domain = f"policy-{index}"
    return {
        "app_id": f"app-{index}",
        "installation_id": f"inst-{index}",
        "custody_domain": custody_root,
        "policy_domain": policy_domain,
        "token_scope": {
            "repositories": ["bstBizEra/secb_pf"],
            "permissions": {"contents": "read"},
        },
        "identity_attestation": signed(principal_kid, {
            "purpose": "PRINCIPAL_IDENTITY",
            "app_id": f"app-{index}",
            "installation_id": f"inst-{index}",
            "role": role,
        }),
        "custody_attestation": signed(custody_root, {
            "purpose": "CUSTODY_BINDING",
            "principal_kid": principal_kid,
            "custody_root": custody_root,
        }),
        "policy_attestation": signed(POLICY_ADMIN[index], {
            "purpose": "POLICY_BINDING",
            "policy_domain": policy_domain,
            "role": role,
            "administered_by": POLICY_ADMIN[index],
        }),
        "revocation_receipt": signed("platform-oidc", {
            "purpose": "REVOCATION_RECEIPT",
            "principal_kid": principal_kid,
            "reuse_result": "DENIED",
            "revoked_at": "2026-08-17T10:20:00+00:00",
            "reuse_attempted_at": "2026-08-17T10:21:00+00:00",
        }),
        "oidc": {"kid": "platform-oidc", "token": oidc_token(role, index)},
    }


def ballot(role: str, index: int, decision: str = "APPROVE") -> dict:
    return signed(f"principal-{role}", {
        "purpose": "BALLOT",
        "principal": role,
        "decision": decision,
        "nonce": f"nonce-{index}",
        "cast_at": "2026-08-17T10:05:00+00:00",
    })


def evidence() -> dict:
    """A document that is cryptographically sound and honestly caps at AIS3."""
    ballots = [ballot("voter_a", 0), ballot("voter_b", 1)]
    return {
        "schema": "secb.ais-production-evidence/v2",
        "snapshot": deepcopy(SNAPSHOT),
        "oidc_policy": {"audience": AUDIENCE, "subject_prefix": SUBJECT_PREFIX},
        "jwks": {
            "provenance": "LOCAL_FIXTURE",
            "issuer": GITHUB_ISSUER,
            "keys": deepcopy(JWKS_KEYS),
        },
        "principals": {role: principal(role, i) for i, role in enumerate(ROLES)},
        "ballots": ballots,
        "roles": {"executor": "executor", "readback_verifier": "readback"},
        "decision_receipt_digest": sha256_digest(ballots),
    }


def rebuild_receipt(document: dict) -> None:
    document["decision_receipt_digest"] = sha256_digest(document["ballots"])


def run(document: dict, tmp_path: Path, **env_extra: str) -> subprocess.CompletedProcess:
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    env = {
        **os.environ,
        "EVIDENCE": str(path),
        "EVALUATE_AT": NOW,
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


def accepts(document: dict, tmp_path: Path, **env_extra: str) -> dict:
    result = run(document, tmp_path, **env_extra)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


# ---------------------------------------------------------------- the v1 counterexample


def test_v1_counterexample_is_refused(tmp_path):
    """The document v1 accepted and reported AIS4 for. Every element is present.

    One authentic token copied across all four role records, fabricated distinct app,
    custody and policy strings, ballots that are plain unsigned records, and a JWKS digest
    the caller computed for itself. v2 must refuse it -- and the FIRST thing it refuses on
    is the reused token, because that is the fact the copied signature never covered.
    """
    document = evidence()
    one_token = document["principals"]["voter_a"]["oidc"]["token"]
    for role in ROLES:
        document["principals"][role]["oidc"]["token"] = one_token
    document["ballots"] = [
        {"principal": "voter_a", "snapshot_digest": SNAPSHOT_DIGEST, "decision": "APPROVE"},
        {"principal": "voter_b", "snapshot_digest": SNAPSHOT_DIGEST, "decision": "APPROVE"},
    ]
    rebuild_receipt(document)
    stderr = refuses(document, tmp_path, "was already presented by")
    assert "One token copied across role records is one principal" in stderr


def test_unsigned_ballots_alone_are_refused(tmp_path):
    """Isolate the ballot half of the counterexample: tokens fine, ballots unsigned."""
    document = evidence()
    document["ballots"] = [
        {"principal": "voter_a", "snapshot_digest": SNAPSHOT_DIGEST, "decision": "APPROVE"},
        {"principal": "voter_b", "snapshot_digest": SNAPSHOT_DIGEST, "decision": "APPROVE"},
    ]
    rebuild_receipt(document)
    refuses(document, tmp_path, "signed envelope has no payload object")


def test_fabricated_domain_strings_without_attestations_are_refused(tmp_path):
    """Distinct strings, no signature from the root they name."""
    document = evidence()
    document["principals"]["voter_b"]["custody_domain"] = "custody-invented"
    refuses(document, tmp_path, "expected 'custody-invented'")


# ------------------------------------------------------------------------- accept path


def test_sound_document_reaches_ais3_and_not_ais4(tmp_path):
    report = accepts(evidence(), tmp_path)
    assert report["OBSERVED_LEVEL"] == "AIS3_CUSTODY_SEPARATED"
    assert report["PRODUCTION_AIS_LEVEL"] == "NOT_OBSERVED"
    assert report["ais4_reachable_here"] is False
    assert report["confers_merge_authority"] is False
    for conjunct in (
        "SIGNED_WORKFLOW_CONTEXT", "PRINCIPAL_IDENTITY_ATTESTED", "CUSTODY_ATTESTED",
        "POLICY_ATTESTED", "BALLOTS_SIGNED", "EFFECT_ROLE_SEPARATION",
        "REVOCATION_RECEIPT_VERIFIED",
    ):
        assert report["conjuncts"][conjunct]["observed"] is True, conjunct
    assert report["unsatisfied"] == ["DISCOVERY_EXACTLY_BOUND", "ISSUER_TRUST_ANCHOR"]


def test_coverage_ledger_names_producer_and_authenticator_per_conjunct(tmp_path):
    """Cryptographic Coverage Accounting is emitted, not asserted."""
    report = accepts(evidence(), tmp_path)
    ledger = report["coverage_ledger"]
    for conjunct, entry in ledger.items():
        assert entry["asserted_fact"]
        assert entry["authoritative_producer"]
        assert "authenticator" in entry
    assert ledger["BALLOTS_SIGNED"]["authenticator"].startswith("PRINCIPAL-signed BALLOT")
    assert ledger["CUSTODY_ATTESTED"]["authenticator"].startswith("CUSTODY_ROOT-signed")
    # The two unauthenticated conjuncts are named, not hidden behind a rounded-up level.
    accounting = report["coverage_accounting"]
    assert accounting["complete"] is False
    assert set(accounting["unauthenticated"]) == {"DISCOVERY_EXACTLY_BOUND", "ISSUER_TRUST_ANCHOR"}


def test_issuer_trust_anchor_is_unsatisfiable_by_any_input(tmp_path):
    """No env lever, and no document field, can satisfy the anchor.

    v1 let `EXPECT_JWKS_DIGEST` stand in for a fetch, which proved only that two values
    agreed -- and one caller can compute both. The lever is gone; these assertions keep it
    gone.
    """
    document = evidence()
    document["jwks"]["provenance"] = "ISSUER_DISCOVERY"
    document["jwks"]["discovery"] = {
        "jwks_uri": JWKS_URI,
        "fetched_at": "2026-08-17T10:00:00+00:00",
        "response_digest": sha256_digest(JWKS_KEYS),
    }
    report = accepts(document, tmp_path)
    assert report["conjuncts"]["DISCOVERY_EXACTLY_BOUND"]["observed"] is True
    assert report["conjuncts"]["ISSUER_TRUST_ANCHOR"]["observed"] is False
    assert report["PRODUCTION_AIS_LEVEL"] == "NOT_OBSERVED"

    for lever in ("EXPECT_JWKS_DIGEST", "ISSUER_TRUST_ANCHOR", "TRANCHE_B_COMPLETE",
                  "FORCE_AIS4", "PRODUCTION_AIS_LEVEL"):
        forced = accepts(document, tmp_path, **{lever: sha256_digest(JWKS_KEYS)})
        assert forced["PRODUCTION_AIS_LEVEL"] == "NOT_OBSERVED", lever
        assert forced["conjuncts"]["ISSUER_TRUST_ANCHOR"]["observed"] is False, lever


# ------------------------------------------------------------------ signature coverage


def test_signature_verification_is_real(tmp_path):
    document = evidence()
    payload = document["principals"]["voter_a"]["identity_attestation"]["payload"]
    payload["app_id"] = "app-elsewhere"
    document["principals"]["voter_a"]["app_id"] = "app-elsewhere"
    refuses(document, tmp_path, "signature does not verify")


def test_padding_slack_forgery_is_refused(tmp_path):
    """A signature over a block with 0xab padding: correct DigestInfo, correct hash.

    Everything a verifier that SCANS for the digest accepts. Weaken the whole-block compare
    to `recovered.endswith(tail)` and this is the test that fails.
    """
    document = evidence()
    envelope = document["principals"]["voter_a"]["identity_attestation"]
    envelope["signature"] = b64u(
        rsa_sign("principal-voter_a", canonical(envelope["payload"]), padding=0xAB)
    )
    refuses(document, tmp_path, "signature does not verify")


def test_purpose_confusion_is_refused(tmp_path):
    """A validly signed BALLOT replayed where an identity attestation belongs."""
    document = evidence()
    document["principals"]["voter_a"]["identity_attestation"] = ballot("voter_a", 99)
    refuses(document, tmp_path, "must not be replayable as another")


def test_attestation_bound_to_another_snapshot_is_refused(tmp_path):
    document = evidence()
    stale = signed("principal-voter_a", {
        "purpose": "PRINCIPAL_IDENTITY", "app_id": "app-0", "installation_id": "inst-0",
        "role": "voter_a",
    })
    stale["payload"]["snapshot_digest"] = "sha256:" + "9" * 64
    stale["signature"] = b64u(rsa_sign("principal-voter_a", canonical(stale["payload"])))
    document["principals"]["voter_a"]["identity_attestation"] = stale
    refuses(document, tmp_path, "is bound to snapshot")


def test_wrong_key_role_for_a_purpose_is_refused(tmp_path):
    """A custody root may not sign an identity attestation."""
    document = evidence()
    envelope = signed("custody-0", {
        "purpose": "PRINCIPAL_IDENTITY", "app_id": "app-0", "installation_id": "inst-0",
        "role": "voter_a",
    })
    document["principals"]["voter_a"]["identity_attestation"] = envelope
    refuses(document, tmp_path, "must be signed by a PRINCIPAL")


def test_principal_may_not_attest_its_own_custody(tmp_path):
    document = evidence()
    document["principals"]["voter_a"]["custody_attestation"] = signed("principal-voter_a", {
        "purpose": "CUSTODY_BINDING", "principal_kid": "principal-voter_a",
        "custody_root": "custody-0",
    })
    refuses(document, tmp_path, "must be signed by a CUSTODY_ROOT")


def test_two_kids_over_one_modulus_are_refused(tmp_path):
    """The label-vs-substance error one layer down: two names, one key."""
    document = evidence()
    clone = deepcopy(jwks_key("principal-voter_a"))
    clone["kid"] = "principal-voter_a-alias"
    clone["owner"] = "voter_b"
    document["jwks"]["keys"].append(clone)
    refuses(document, tmp_path, "share the same modulus")


def test_two_principals_sharing_one_signing_key_are_refused(tmp_path):
    document = evidence()
    document["principals"]["voter_b"]["identity_attestation"] = signed("principal-voter_a", {
        "purpose": "PRINCIPAL_IDENTITY", "app_id": "app-1", "installation_id": "inst-1",
        "role": "voter_b",
    })
    refuses(document, tmp_path, "One signing key is one principal")


def test_key_without_an_owner_is_refused(tmp_path):
    document = evidence()
    document["jwks"]["keys"][0].pop("owner")
    refuses(document, tmp_path, "an unowned key separates nothing")


def test_unknown_key_role_is_refused(tmp_path):
    document = evidence()
    document["jwks"]["keys"][0]["key_role"] = "SUPERUSER"
    refuses(document, tmp_path, "is not one of")


# ------------------------------------------------------------------------ ballots

def test_ballot_signed_by_another_principals_key_is_refused(tmp_path):
    document = evidence()
    forged = signed("principal-voter_a", {
        "purpose": "BALLOT", "principal": "voter_b", "decision": "APPROVE",
        "nonce": "nonce-7", "cast_at": "2026-08-17T10:07:00+00:00",
    })
    document["ballots"][1] = forged
    rebuild_receipt(document)
    refuses(document, tmp_path, "another principal's ballot")


def test_replayed_nonce_is_refused(tmp_path):
    document = evidence()
    document["ballots"][1] = ballot("voter_b", 0)  # same nonce index as voter_a
    rebuild_receipt(document)
    refuses(document, tmp_path, "is replayed")


def test_one_principal_casting_two_ballots_is_refused(tmp_path):
    document = evidence()
    document["ballots"] = [ballot("voter_a", 0), ballot("voter_a", 1)]
    rebuild_receipt(document)
    refuses(document, tmp_path, "cast more than one ballot")


def test_decision_receipt_digest_must_bind_the_ballots(tmp_path):
    """v1 made this field schema-required and never read it: decorative."""
    document = evidence()
    document["decision_receipt_digest"] = "sha256:" + "3" * 64
    refuses(document, tmp_path, "does not digest the ballot set")


def test_adding_a_ballot_without_updating_the_receipt_is_refused(tmp_path):
    document = evidence()
    document["ballots"].append(ballot("readback", 5))
    refuses(document, tmp_path, "does not digest the ballot set")


def test_single_approval_is_a_shortfall_not_a_contradiction(tmp_path):
    document = evidence()
    document["ballots"] = [ballot("voter_a", 0), ballot("voter_b", 1, decision="ABSTAIN")]
    rebuild_receipt(document)
    report = accepts(document, tmp_path)
    assert "BALLOTS_SIGNED" in report["unsatisfied"]
    assert report["coverage_ledger"]["BALLOTS_SIGNED"]["authenticator"] == "UNAUTHENTICATED"


def test_ballot_from_an_unknown_principal_is_refused(tmp_path):
    document = evidence()
    ghost = signed("principal-readback", {
        "purpose": "BALLOT", "principal": "ghost", "decision": "APPROVE",
        "nonce": "nonce-8", "cast_at": "2026-08-17T10:08:00+00:00",
    })
    document["ballots"][1] = ghost
    rebuild_receipt(document)
    refuses(document, tmp_path, "is absent from the evidence")


# ------------------------------------------------------------------------- policy


def test_self_administered_policy_is_refused(tmp_path):
    document = evidence()
    document["principals"]["voter_a"]["policy_attestation"] = signed("policy-admin-x", {
        "purpose": "POLICY_BINDING", "policy_domain": "policy-0", "role": "voter_a",
        "administered_by": "policy-0",
    })
    refuses(document, tmp_path, "administered by its own domain")


def test_reciprocal_policy_administration_is_refused(tmp_path):
    """Unequal labels are not independence: A governs B and B governs A."""
    document = evidence()
    document["principals"]["voter_a"]["policy_attestation"] = signed("policy-admin-x", {
        "purpose": "POLICY_BINDING", "policy_domain": "policy-0", "role": "voter_a",
        "administered_by": "policy-1",
    })
    document["principals"]["voter_b"]["policy_attestation"] = signed("policy-admin-y", {
        "purpose": "POLICY_BINDING", "policy_domain": "policy-1", "role": "voter_b",
        "administered_by": "policy-0",
    })
    refuses(document, tmp_path, "administration is reciprocal")


def test_all_administration_internal_to_the_set_is_refused(tmp_path):
    document = evidence()
    chain = {0: "policy-1", 1: "policy-2", 2: "policy-3", 3: "policy-0"}
    for index, role in enumerate(ROLES):
        document["principals"][role]["policy_attestation"] = signed(
            POLICY_ADMIN[index], {
                "purpose": "POLICY_BINDING", "policy_domain": f"policy-{index}", "role": role,
                "administered_by": chain[index],
            })
    refuses(document, tmp_path, "no administration is external")


def test_shared_policy_domain_is_refused(tmp_path):
    document = evidence()
    document["principals"]["voter_b"]["policy_domain"] = "policy-0"
    document["principals"]["voter_b"]["policy_attestation"] = signed("policy-admin-y", {
        "purpose": "POLICY_BINDING", "policy_domain": "policy-0", "role": "voter_b",
        "administered_by": "policy-admin-y",
    })
    refuses(document, tmp_path, "share a policy domain")


# ------------------------------------------------------------------------- separation


def test_shared_app_installation_is_refused(tmp_path):
    document = evidence()
    document["principals"]["voter_b"] = principal("voter_b", 1)
    document["principals"]["voter_b"]["app_id"] = "app-0"
    document["principals"]["voter_b"]["identity_attestation"] = signed("principal-voter_b", {
        "purpose": "PRINCIPAL_IDENTITY", "app_id": "app-0", "installation_id": "inst-1",
        "role": "voter_b",
    })
    document["principals"]["voter_b"]["installation_id"] = "inst-0"
    document["principals"]["voter_b"]["identity_attestation"] = signed("principal-voter_b", {
        "purpose": "PRINCIPAL_IDENTITY", "app_id": "app-0", "installation_id": "inst-0",
        "role": "voter_b",
    })
    refuses(document, tmp_path, "share an App/installation")


def test_shared_custody_root_is_refused(tmp_path):
    document = evidence()
    document["principals"]["voter_b"]["custody_domain"] = "custody-0"
    document["principals"]["voter_b"]["custody_attestation"] = signed("custody-0", {
        "purpose": "CUSTODY_BINDING", "principal_kid": "principal-voter_b",
        "custody_root": "custody-0",
    })
    refuses(document, tmp_path, "share a credential custody domain")


def test_custody_attestation_for_the_wrong_key_is_refused(tmp_path):
    document = evidence()
    document["principals"]["voter_a"]["custody_attestation"] = signed("custody-0", {
        "purpose": "CUSTODY_BINDING", "principal_kid": "principal-voter_b",
        "custody_root": "custody-0",
    })
    refuses(document, tmp_path, "signed principal_kid")


def test_executor_may_not_vote(tmp_path):
    document = evidence()
    document["ballots"][1] = ballot("executor", 1)
    rebuild_receipt(document)
    refuses(document, tmp_path, "also cast a ballot")


def test_executor_may_not_verify_its_own_readback(tmp_path):
    document = evidence()
    document["roles"]["readback_verifier"] = "executor"
    refuses(document, tmp_path, "also the readback verifier")


# ------------------------------------------------------------------------ OIDC in full


def test_expired_token_is_refused(tmp_path):
    refuses(evidence(), tmp_path, "expired at", EVALUATE_AT="2026-08-17T11:30:00+00:00")


def test_not_yet_valid_token_is_refused(tmp_path):
    document = evidence()
    document["principals"]["voter_a"]["oidc"]["token"] = oidc_token(
        "voter_a", 0, claims_override={"nbf": "2026-08-17T12:00:00+00:00"})
    refuses(document, tmp_path, "not yet valid")


def test_wrong_audience_is_refused(tmp_path):
    document = evidence()
    document["principals"]["voter_a"]["oidc"]["token"] = oidc_token(
        "voter_a", 0, claims_override={"aud": "someone-else"})
    refuses(document, tmp_path, "valid token for someone else")


def test_subject_outside_the_repository_is_refused(tmp_path):
    document = evidence()
    document["principals"]["voter_a"]["oidc"]["token"] = oidc_token(
        "voter_a", 0, claims_override={"sub": "repo:attacker/repo:role:voter_a"})
    refuses(document, tmp_path, "is not under")


def test_over_hour_token_lifetime_is_refused(tmp_path):
    document = evidence()
    document["principals"]["voter_a"]["oidc"]["token"] = oidc_token(
        "voter_a", 0, claims_override={"exp": "2026-08-17T14:00:00+00:00"})
    refuses(document, tmp_path, "over the 3600s ceiling")


@pytest.mark.parametrize("claim", ["aud", "sub", "exp", "iat", "jti"])
def test_each_required_claim_is_enforced(tmp_path, claim):
    document = evidence()
    document["principals"]["voter_a"]["oidc"]["token"] = oidc_token("voter_a", 0, drop=claim)
    refuses(document, tmp_path, "missing required claims")


def test_wrong_issuer_is_refused(tmp_path):
    document = evidence()
    document["principals"]["voter_a"]["oidc"]["token"] = oidc_token(
        "voter_a", 0, claims_override={"iss": "https://token.actions.githubusercontent.com.evil"})
    refuses(document, tmp_path, "is not exactly")


@pytest.mark.parametrize("claim", ["repository_id", "workflow_sha", "job_workflow_ref"])
def test_context_claim_disagreeing_with_the_snapshot_is_refused(tmp_path, claim):
    document = evidence()
    document["principals"]["voter_a"]["oidc"]["token"] = oidc_token(
        "voter_a", 0, claims_override={claim: "bound-elsewhere"})
    refuses(document, tmp_path, "but the snapshot says")


def test_alg_none_is_refused(tmp_path):
    document = evidence()
    document["principals"]["voter_a"]["oidc"]["token"] = oidc_token("voter_a", 0, alg="none")
    refuses(document, tmp_path, "algorithm-confusion")


def test_oidc_signed_by_a_non_platform_key_is_refused(tmp_path):
    document = evidence()
    document["principals"]["voter_a"]["oidc"] = {
        "kid": "principal-voter_a",
        "token": oidc_token("voter_a", 0, kid="principal-voter_a"),
    }
    refuses(document, tmp_path, "must be signed by a PLATFORM")


def test_missing_evaluate_at_is_a_shortfall_not_a_pass(tmp_path):
    """Without a clock, expiry is unevaluable -- so the conjunct is not observed."""
    result = subprocess.run(
        [sys.executable, str(TOOL)], capture_output=True, text=True, check=False,
        env={
            **os.environ,
            "EVIDENCE": str(_write(tmp_path, evidence())),
            "EVALUATE_AT": "",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["OBSERVED_LEVEL"] == "AIS0_SELF_ASSERTED"
    assert "SIGNED_WORKFLOW_CONTEXT" in report["unsatisfied"]


def _write(tmp_path: Path, document: dict) -> Path:
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


# ------------------------------------------------------------------------- discovery


@pytest.mark.parametrize("uri", [
    "https://token.actions.githubusercontent.com.attacker.example/.well-known/jwks",
    "https://token.actions.githubusercontent.com@evil.example/.well-known/jwks",
    "http://token.actions.githubusercontent.com/.well-known/jwks",
    "https://token.actions.githubusercontent.com/.well-known/keys",
])
def test_lookalike_jwks_uris_are_refused(tmp_path, uri):
    """Each of these passed v1's `startswith` check. Host and path are compared exactly."""
    document = evidence()
    document["jwks"]["provenance"] = "ISSUER_DISCOVERY"
    document["jwks"]["discovery"] = {
        "jwks_uri": uri,
        "fetched_at": "2026-08-17T10:00:00+00:00",
        "response_digest": sha256_digest(JWKS_KEYS),
    }
    refuses(document, tmp_path, "jwks_uri")


def test_discovery_without_a_record_is_refused(tmp_path):
    document = evidence()
    document["jwks"]["provenance"] = "ISSUER_DISCOVERY"
    refuses(document, tmp_path, "no discovery record")


def test_discovery_digest_not_matching_the_keys_is_refused(tmp_path):
    document = evidence()
    document["jwks"]["provenance"] = "ISSUER_DISCOVERY"
    document["jwks"]["discovery"] = {
        "jwks_uri": JWKS_URI,
        "fetched_at": "2026-08-17T10:00:00+00:00",
        "response_digest": sha256_digest({"other": "bytes"}),
    }
    refuses(document, tmp_path, "does not digest the key set")


# ------------------------------------------------------------------------ revocation


def test_reuse_accepted_after_revocation_is_refused(tmp_path):
    document = evidence()
    document["principals"]["voter_a"]["revocation_receipt"] = signed("platform-oidc", {
        "purpose": "REVOCATION_RECEIPT", "principal_kid": "principal-voter_a",
        "reuse_result": "ACCEPTED", "revoked_at": "2026-08-17T10:20:00+00:00",
        "reuse_attempted_at": "2026-08-17T10:21:00+00:00",
    })
    refuses(document, tmp_path, "does not deny reuse is a log entry")


def test_reuse_attempted_before_revocation_is_refused(tmp_path):
    document = evidence()
    document["principals"]["voter_a"]["revocation_receipt"] = signed("platform-oidc", {
        "purpose": "REVOCATION_RECEIPT", "principal_kid": "principal-voter_a",
        "reuse_result": "DENIED", "revoked_at": "2026-08-17T10:20:00+00:00",
        "reuse_attempted_at": "2026-08-17T10:19:00+00:00",
    })
    refuses(document, tmp_path, "at or before revocation")


def test_self_signed_revocation_receipt_is_refused(tmp_path):
    """The subject may not sign its own revocation evidence."""
    document = evidence()
    document["principals"]["voter_a"]["revocation_receipt"] = signed("principal-voter_a", {
        "purpose": "REVOCATION_RECEIPT", "principal_kid": "principal-voter_a",
        "reuse_result": "DENIED", "revoked_at": "2026-08-17T10:20:00+00:00",
        "reuse_attempted_at": "2026-08-17T10:21:00+00:00",
    })
    refuses(document, tmp_path, "must be signed by a PLATFORM")


def test_absent_revocation_receipt_is_a_shortfall(tmp_path):
    document = evidence()
    del document["principals"]["voter_a"]["revocation_receipt"]
    report = accepts(document, tmp_path)
    assert "REVOCATION_RECEIPT_VERIFIED" in report["unsatisfied"]
    assert report["PRODUCTION_AIS_LEVEL"] == "NOT_OBSERVED"


# ---------------------------------------------------------------------- scope, structure


@pytest.mark.parametrize("repositories", [["*"], ["bstBizEra/*"]])
def test_wildcard_repository_scope_is_refused(tmp_path, repositories):
    document = evidence()
    document["principals"]["voter_a"]["token_scope"]["repositories"] = repositories
    refuses(document, tmp_path, "is a wildcard")


def test_admin_permission_is_refused(tmp_path):
    document = evidence()
    document["principals"]["voter_a"]["token_scope"]["permissions"] = {"administration": "admin"}
    refuses(document, tmp_path, "is administrative")


def test_document_may_not_claim_its_own_level(tmp_path):
    for field in ("production_ais_level", "observed_level", "claimed_level"):
        document = evidence()
        document[field] = "AIS4_INDEPENDENT_DOMAINS"
        refuses(document, tmp_path, "the level is COMPUTED")


def test_wrong_schema_is_refused(tmp_path):
    document = evidence()
    document["schema"] = "secb.ais-production-evidence/v1"
    refuses(document, tmp_path, "expected 'secb.ais-production-evidence/v2'")


def test_stale_snapshot_is_refused(tmp_path):
    refuses(evidence(), tmp_path, "is not the expected", EXPECT_MAIN_SHA="0" * 40)


def test_snapshot_edit_invalidates_every_attestation(tmp_path):
    document = evidence()
    document["snapshot"]["main_sha"] = "a" * 40
    refuses(document, tmp_path, "is bound to snapshot")


def test_single_principal_separates_nothing(tmp_path):
    document = evidence()
    document["principals"] = {"voter_a": document["principals"]["voter_a"]}
    refuses(document, tmp_path, "separates nothing")


def test_missing_evidence_path_is_refused():
    result = subprocess.run(
        [sys.executable, str(TOOL)], capture_output=True, text=True, check=False,
        env={**os.environ, "EVIDENCE": "", "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert result.returncode == 2
    assert "EVIDENCE is required" in result.stderr


def test_unreadable_evidence_is_refused(tmp_path):
    result = subprocess.run(
        [sys.executable, str(TOOL)], capture_output=True, text=True, check=False,
        env={
            **os.environ, "EVIDENCE": str(tmp_path / "absent.json"),
            "PYTHONDONTWRITEBYTECODE": "1",
        },
    )
    assert result.returncode == 2
    assert "unreadable or unparseable" in result.stderr


def test_attestation_claiming_verification_without_a_verifier_is_refused(tmp_path):
    document = evidence()
    document["attestation"] = {"bundle_digest": "sha256:" + "2" * 64, "signer_verified": True}
    refuses(document, tmp_path, "no verified_by")


# ------------------------------------------------------------------------ the contract


def test_schema_declares_no_level_field_and_matches_v2():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema["$id"] == "secb.ais-production-evidence/v2"
    for banned in ("ais_level", "level", "production_ais_level", "claimed_level"):
        assert banned not in schema["properties"]


def test_fixture_satisfies_every_required_field_the_schema_declares():
    """Bind schema to verifier: nothing validates documents against it at runtime."""
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    document = evidence()
    for field in schema["required"]:
        assert field in document, f"schema requires {field!r}; the fixture omits it"
    principal_schema = schema["properties"]["principals"]["additionalProperties"]
    for role, body in document["principals"].items():
        for field in principal_schema["required"]:
            assert field in body, f"{role}: schema requires {field!r}"


def test_test_keys_are_distinct_and_not_pem():
    """The fixture keys must be genuinely distinct, and must not be PEM blobs."""
    raw = KEYS_PATH.read_text(encoding="utf-8")
    assert "BEGIN RSA PRIVATE KEY" not in raw and "BEGIN PRIVATE KEY" not in raw
    material = json.loads(raw)
    moduli = {k["n_hex"] for k in material["keys"]}
    assert len(moduli) == len(material["keys"]), "two test keys share a modulus"
    for key in material["keys"]:
        assert int(key["n_hex"], 16).bit_length() == 2048
