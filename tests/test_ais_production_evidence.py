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
OBSERVED_CLAIMS_PATH = (Path(__file__).parent / "fixtures" /
                        "github_oidc_issued_claims_observation.json")

GITHUB_ISSUER = "https://token.actions.githubusercontent.com"
JWKS_URI = f"{GITHUB_ISSUER}/.well-known/jwks"
MAIN_SHA = "f5aa26aef86250a7dfb68223f8f0b5d63f54ea52"
WORKFLOW_SHA = "7e478d714ef57f624de2ccddc5733697f06fb119"
JOB_WORKFLOW_REF = "bstBizEra/secb_pf/.github/workflows/ci.yml@refs/heads/main"
AUDIENCE = "bstBizEra"
SUBJECT_REPOSITORY = "bstBizEra/secb_pf"
# The REAL issuer configuration for this repository, read back from
# GET /repos/bstBizEra/secb_pf/actions/oidc/customization/sub on 2026-08-18:
#   {"use_default": true, "use_immutable_subject": false,
#    "sub_claim_prefix": "repo:bstBizEra@230689381/secb_pf@1328913339"}
# and GET /repos/bstBizEra/secb_pf/environments -> {"total_count": 0}.
# Recorded here because the fixture's subjects must be shapes THIS issuer can mint.
REAL_SUB_CONFIG = {"use_default": True, "use_immutable_subject": False,
                   "sub_claim_prefix": "repo:bstBizEra@230689381/secb_pf@1328913339"}
REPOSITORY_ID = "1328913339"
REPOSITORY_OWNER_ID = "230689381"
ENVIRONMENTS = {role: f"secb-{role.replace('_', '-')}" for role in
                ("voter_a", "voter_b", "executor", "readback")}
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
        "sub": f"repo:{SUBJECT_REPOSITORY}:environment:{ENVIRONMENTS[role]}",
        "environment": ENVIRONMENTS[role],
        "ref": "refs/heads/main",
        "repository": SUBJECT_REPOSITORY,
        "repository_owner_id": REPOSITORY_OWNER_ID,
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
        "oidc": {"kid": "platform-oidc", "token": oidc_token(role, index),
                 "environment": ENVIRONMENTS[role]},
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
        "oidc_policy": {
            "audience": AUDIENCE,
            "subject_repository": SUBJECT_REPOSITORY,
            # Bound to the issuer's own configuration, not to a shape this repository invented.
            "subject_configuration": {**REAL_SUB_CONFIG, "context": "environment"},
            "environments_observed": {
                "environments": sorted(ENVIRONMENTS.values()),
                "readback": "GET /repos/bstBizEra/secb_pf/environments",
                "fetched_at": "2026-08-18T01:00:00+00:00",
            },
        },
        "jwks": {
            "provenance": "LOCAL_FIXTURE",
            "issuer": GITHUB_ISSUER,
            "keys": deepcopy(JWKS_KEYS),
        },
        "principals": {role: principal(role, i) for i, role in enumerate(ROLES)},
        "ballots": ballots,
        "role_assignment": signed("policy-admin-x", {
            "purpose": "ROLE_ASSIGNMENT",
            "executor": "executor",
            "readback_verifier": "readback",
        }),
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
    stderr = refuses(document, tmp_path, "not bound to the")
    # It does not reach the jti replay guard: the copied token was minted for voter_a's
    # environment, so presenting it as another principal fails the principal binding first.
    # Revision 4 refuses this one edge earlier than revision 2 did -- the token is rejected for
    # not belonging to the principal, not merely for having been seen twice.
    assert "self-consistent, not bound" in stderr


def test_same_jti_across_two_principals_is_refused(tmp_path):
    """Replay detection, now that the sub binding catches the naive copy first.

    Two tokens with correct per-role `sub` values but ONE jti: the same minted token
    presented twice, which is one principal however many roles the document names.
    """
    document = evidence()
    document["principals"]["voter_b"]["oidc"]["token"] = oidc_token(
        "voter_b", 1, claims_override={"jti": "jti-0"})
    stderr = refuses(document, tmp_path, "was already presented by")
    assert "is one principal" in stderr


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
    """A domain whose administrator is itself, with the signature to match."""
    document = evidence()
    document["principals"]["voter_a"]["policy_domain"] = "policy-admin-x"
    document["principals"]["voter_a"]["policy_attestation"] = signed("policy-admin-x", {
        "purpose": "POLICY_BINDING", "policy_domain": "policy-admin-x", "role": "voter_a",
        "administered_by": "policy-admin-x",
    })
    refuses(document, tmp_path, "administered by its own domain")


def test_reciprocal_policy_administration_is_refused(tmp_path):
    """Unequal labels are not independence: x governs y and y governs x."""
    document = evidence()
    document["principals"]["voter_a"]["policy_domain"] = "policy-admin-x"
    document["principals"]["voter_a"]["policy_attestation"] = signed("policy-admin-y", {
        "purpose": "POLICY_BINDING", "policy_domain": "policy-admin-x", "role": "voter_a",
        "administered_by": "policy-admin-y",
    })
    document["principals"]["voter_b"]["policy_domain"] = "policy-admin-y"
    document["principals"]["voter_b"]["policy_attestation"] = signed("policy-admin-x", {
        "purpose": "POLICY_BINDING", "policy_domain": "policy-admin-y", "role": "voter_b",
        "administered_by": "policy-admin-x",
    })
    refuses(document, tmp_path, "administration is reciprocal")


def test_all_administration_internal_to_the_set_is_refused(tmp_path):
    """A 3-cycle: x governed by y, y by z, z by x. No reciprocity, still no outside.

    Every signature is valid and every signer IS the administrator it names, so gap 1 and the
    reciprocity check both pass -- and the set still audits only itself.
    """
    document = evidence()
    cycle = {"policy-admin-x": "policy-admin-y",
             "policy-admin-y": "policy-admin-z",
             "policy-admin-z": "policy-admin-x"}
    document["principals"] = {r: document["principals"][r] for r in ("voter_a", "voter_b", "executor")}
    for role, domain in zip(("voter_a", "voter_b", "executor"), cycle):
        document["principals"][role]["policy_domain"] = domain
        document["principals"][role]["policy_attestation"] = signed(cycle[domain], {
            "purpose": "POLICY_BINDING", "policy_domain": domain, "role": role,
            "administered_by": cycle[domain],
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
    document["role_assignment"] = signed("policy-admin-x", {
        "purpose": "ROLE_ASSIGNMENT", "executor": "executor", "readback_verifier": "executor",
    })
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
        "voter_a", 0, claims_override={"sub": "repo:attacker/repo:environment:secb-voter-a"})
    refuses(document, tmp_path, "is not the subject the declared issuer")


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
    assert "roles" not in document, "the unsigned roles object must not come back"
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


# ============================================================================
# Cryptographic Coverage Closure -- one counterexample per unresolved binding
# from the revision-2 review. Each builds a document that revision 2 ACCEPTED
# and asserts it is now refused. A closed edge with no counterexample is a
# claim about the code, not a property of it.
# ============================================================================


def test_closure_1_policy_signer_must_be_the_administrator_it_names(tmp_path):
    """Gap 1: signer identity was never matched to the signed `administered_by`.

    policy-admin-y signs an attestation asserting that policy-admin-x administers voter_a.
    Both are legitimate POLICY_ADMIN_ROOT keys and the signature verifies, so revision 2
    accepted it -- an admin root vouching for another root's authority, which is hearsay.
    """
    document = evidence()
    document["principals"]["voter_a"]["policy_attestation"] = signed("policy-admin-y", {
        "purpose": "POLICY_BINDING", "policy_domain": "policy-0", "role": "voter_a",
        "administered_by": "policy-admin-x",
    })
    stderr = refuses(document, tmp_path, "is signed by a key owned by")
    assert "hearsay" in stderr


def test_closure_2a_role_assignment_must_be_signed(tmp_path):
    """Gap 2: executor/readback came from an unsigned object.

    Absence is a shortfall rather than a contradiction -- but it must stop the conjunct,
    which is what revision 2 failed to do while reporting the separation as observed.
    """
    document = evidence()
    del document["role_assignment"]
    report = accepts(document, tmp_path)
    assert report["conjuncts"]["EFFECT_ROLE_SEPARATION"]["observed"] is False
    assert report["coverage_ledger"]["EFFECT_ROLE_SEPARATION"]["authenticator"] == "UNAUTHENTICATED"
    assert report["PRODUCTION_AIS_LEVEL"] == "NOT_OBSERVED"


def test_closure_2b_role_assignment_signed_from_inside_the_set_is_refused(tmp_path):
    """Gap 2, the sharper half: a signature is not authority.

    A POLICY_ADMIN_ROOT key is used, so purpose and role checks pass -- but its owner is one
    of the principals' own policy domains, making the assignment self-assignment with an
    extra step.
    """
    document = evidence()
    for key in document["jwks"]["keys"]:
        if key["kid"] == "policy-admin-z":
            key["owner"] = "policy-0"          # a real, distinct key placed inside the set
    document["role_assignment"] = signed("policy-admin-z", {
        "purpose": "ROLE_ASSIGNMENT", "executor": "executor", "readback_verifier": "readback",
    })
    refuses(document, tmp_path, "self-assignment with an extra step")


def test_closure_2c_role_assignment_signer_needs_authority_over_the_subjects(tmp_path):
    """Gap 2, third edge: an external root that administers none of these principals."""
    document = evidence()
    document["role_assignment"] = signed("policy-admin-w", {
        "purpose": "ROLE_ASSIGNMENT", "executor": "executor", "readback_verifier": "readback",
    })
    refuses(document, tmp_path, "no authority over their role assignment")


def test_closure_3a_sub_prefix_extension_is_refused(tmp_path):
    """Gap 3: `startswith` on `sub` accepted a longer repository name.

    A token for `bstBizEra/secb_pf_shadow` passes any prefix test written against
    `repo:bstBizEra/secb_pf` -- a different repository entirely.
    """
    document = evidence()
    document["oidc_policy"]["subject_repository"] = "bstBizEra/secb_pf"
    document["principals"]["voter_a"]["oidc"]["token"] = oidc_token(
        "voter_a", 0,
        claims_override={"sub": "repo:bstBizEra/secb_pf_shadow:environment:secb-voter-a"})
    refuses(document, tmp_path, "is not the subject the declared issuer")


def test_closure_3b_token_for_another_principal_is_refused(tmp_path):
    """A prefix bound no principal; the rebuilt subject does.

    An authentic token whose `sub` names the executor's environment, presented in voter_a's
    record. Same repository, same audience, valid signature, unique jti -- and it is refused
    because the subject rebuilt from voter_a's own claims is not the one presented.
    """
    document = evidence()
    document["principals"]["voter_a"]["oidc"]["token"] = oidc_token(
        "voter_a", 0,
        claims_override={"sub": f"repo:{SUBJECT_REPOSITORY}:environment:{ENVIRONMENTS['executor']}"})
    refuses(document, tmp_path, "is not the subject the declared issuer")


def test_closure_4_future_issued_token_is_refused(tmp_path):
    """Gap 4: `iat` in the future passed, because only `exp` was compared to the clock.

    A token issued an hour after the evaluation instant, still unexpired, is either a clock
    forgery or evidence about a run that has not happened.
    """
    document = evidence()
    document["principals"]["voter_a"]["oidc"]["token"] = oidc_token(
        "voter_a", 0, claims_override={
            "iat": "2026-08-17T11:30:00+00:00", "exp": "2026-08-17T12:00:00+00:00"})
    stderr = refuses(document, tmp_path, "is after the evaluation instant")
    assert "has not happened" in stderr


def test_closure_coverage_ledger_has_no_unauthenticated_derived_conjunct(tmp_path):
    """Every conjunct except the two structurally external ones is authenticated.

    This is the ledger assertion the four gaps would each have broken: EFFECT_ROLE_SEPARATION
    was reported observed while resting on unsigned text, which is exactly a COVERAGE_GAP
    that a nearby-signature ledger cannot see.
    """
    report = accepts(evidence(), tmp_path)
    unauthenticated = set(report["coverage_accounting"]["unauthenticated"])
    assert unauthenticated == {"DISCOVERY_EXACTLY_BOUND", "ISSUER_TRUST_ANCHOR"}
    assert report["coverage_ledger"]["EFFECT_ROLE_SEPARATION"]["authenticator"].startswith(
        "POLICY_ADMIN_ROOT-signed ROLE_ASSIGNMENT")


# ============================================================================
# Revision 4. Revision 3 required `repo:<repo>:role:<role>` -- and `role` is not
# a claim key GitHub supports, so NO issuer configuration could mint it. The
# fixture signed the invented shape with repository-held test keys, which proved
# verifier/fixture agreement and nothing about the issuer.
#
#     FIXTURE_ACCEPTS != ISSUER_CAN_MINT
#
# The subject is now rebuilt from the token's own claims per a READBACK of the
# issuer's subject-claim customization, so expectation and configuration are one
# authority instead of two.
# ============================================================================


def test_positive_fixture_is_bound_to_an_observed_github_token_shape():
    """Bind the synthetic subject tests to claims GitHub actually issued.

    The compact credential is deliberately absent. The exact allowlisted record and its
    digest came from Actions run 32059511164; stable assertions below distinguish a
    real issuer observation from documentation-shaped data authored by this repository.
    """
    fixture = json.loads(OBSERVED_CLAIMS_PATH.read_text(encoding="utf-8"))
    record = fixture["record"]
    claims = record["claims"]
    provenance = fixture["provenance"]

    assert provenance["compact_jwt_retained"] is False
    assert sha256_digest(record) == provenance["claims_record_digest"]
    assert provenance["workflow_run_url"].endswith("/actions/runs/32059511164")
    assert record["source"]["run_id"] == claims["run_id"] == "32059511164"
    assert record["source"]["sha"] == claims["sha"]
    assert claims["iss"] == GITHUB_ISSUER
    assert claims["aud"] == "secb-pf:oidc-observation"
    assert claims["repository"] == SUBJECT_REPOSITORY
    assert claims["repository_id"] == REPOSITORY_ID
    assert claims["repository_owner_id"] == REPOSITORY_OWNER_ID
    assert claims["sub"] == f"{REAL_SUB_CONFIG['sub_claim_prefix']}:pull_request"
    assert claims["event_name"] == "pull_request"
    assert claims["ref"] == "refs/pull/159/merge"
    assert claims["job_workflow_ref"] == claims["workflow_ref"]
    assert claims["job_workflow_ref"].endswith(
        ".github/workflows/oidc-issued-claims.yml@refs/pull/159/merge")
    assert claims["workflow_sha"] == claims["job_workflow_sha"] == claims["sha"]
    assert int(claims["nbf"]) <= int(claims["iat"]) < int(claims["exp"])
    assert int(claims["exp"]) - int(claims["iat"]) == 300


def test_revision_3_role_subject_is_now_refused(tmp_path):
    """The exact contract revision 3 enforced must now fail: it was unsatisfiable."""
    document = evidence()
    document["principals"]["voter_a"]["oidc"]["token"] = oidc_token(
        "voter_a", 0, claims_override={"sub": f"repo:{SUBJECT_REPOSITORY}:role:voter_a"})
    refuses(document, tmp_path, "is not the subject the declared issuer")


def test_a_template_naming_an_unsupported_claim_key_is_refused(tmp_path):
    """`role` in include_claim_keys is refused as NOT PRODUCIBLE, not merely mismatched.

    This is the finding in its most direct form: the issuer supports repo, context,
    repository_owner, repository_visibility, job_workflow_ref, repository_id,
    repository_owner_id, environment and repo_property_*. A template outside that set cannot
    be minted by any configuration.
    """
    document = evidence()
    document["oidc_policy"]["subject_configuration"] = {
        "use_default": False, "use_immutable_subject": False,
        "include_claim_keys": ["repo", "role"],
    }
    stderr = refuses(document, tmp_path, "SUBJECT_TEMPLATE_NOT_PRODUCIBLE")
    assert "not claim keys the issuer supports" in stderr


def test_a_custom_template_is_rebuilt_from_the_signed_claims(tmp_path):
    """A supported custom template is accepted when the token's claims produce that subject."""
    document = evidence()
    document["oidc_policy"]["subject_configuration"] = {
        "use_default": False, "use_immutable_subject": False,
        "include_claim_keys": ["repo", "environment"],
    }
    for role in ROLES:
        document["principals"][role]["oidc"]["token"] = oidc_token(
            role, ROLES.index(role),
            claims_override={"sub": f"{SUBJECT_REPOSITORY}:{ENVIRONMENTS[role]}"})
    report = accepts(document, tmp_path)
    assert report["conjuncts"]["SIGNED_WORKFLOW_CONTEXT"]["observed"] is True


def test_a_template_key_absent_from_the_signed_token_is_refused(tmp_path):
    document = evidence()
    document["oidc_policy"]["subject_configuration"] = {
        "use_default": False, "use_immutable_subject": False,
        "include_claim_keys": ["repo", "job_workflow_ref"],
    }
    for role in ROLES:
        document["principals"][role]["oidc"]["token"] = oidc_token(
            role, ROLES.index(role), drop="job_workflow_ref",
            claims_override={"sub": f"{SUBJECT_REPOSITORY}:x"})
    refuses(document, tmp_path, "carries no")


@pytest.mark.parametrize("context,sub_tail", [
    ("pull_request", "pull_request"),
    ("ref", "ref:refs/heads/main"),
])
def test_documented_default_contexts_are_accepted(tmp_path, context, sub_tail):
    """The other two documented default contexts must verify -- shape fidelity, both ways."""
    document = evidence()
    document["oidc_policy"]["subject_configuration"] = {**REAL_SUB_CONFIG, "context": context}
    for role in ROLES:
        document["principals"][role]["oidc"]["token"] = oidc_token(
            role, ROLES.index(role),
            claims_override={"sub": f"repo:{SUBJECT_REPOSITORY}:{sub_tail}"})
    report = accepts(document, tmp_path)
    assert report["conjuncts"]["SIGNED_WORKFLOW_CONTEXT"]["observed"] is True


def test_a_shared_subject_does_not_distinguish_principals(tmp_path):
    """THIS repository's real state: default template, no environments.

    Under `pull_request` (or `ref`) context every principal's subject is identical, so the
    subject identifies the repository and not the principal. Producible, and not
    distinguishing -- reported as a shortfall rather than accepted.

        SUBJECT_PRODUCIBLE != SUBJECT_DISTINGUISHING
    """
    document = evidence()
    document["oidc_policy"]["subject_configuration"] = {
        **REAL_SUB_CONFIG, "context": "pull_request"}
    for role in ROLES:
        document["principals"][role]["oidc"]["token"] = oidc_token(
            role, ROLES.index(role),
            claims_override={"sub": f"repo:{SUBJECT_REPOSITORY}:pull_request"})
    report = accepts(document, tmp_path)
    assert report["conjuncts"]["SUBJECT_PRODUCIBLE_AND_DISTINGUISHING"]["observed"] is False
    assert "shared by more than one principal" in \
        report["conjuncts"]["SUBJECT_PRODUCIBLE_AND_DISTINGUISHING"]["note"]
    assert report["PRODUCTION_AIS_LEVEL"] == "NOT_OBSERVED"


def test_an_environment_absent_from_the_readback_is_refused(tmp_path):
    """A subject naming an environment that does not exist cannot be minted.

    The live readback for this repository is `{"total_count": 0}` -- zero environments -- so
    every environment-context subject the fixture uses is currently unmintable HERE. That is
    why the readback is required rather than assumed.
    """
    document = evidence()
    document["oidc_policy"]["environments_observed"]["environments"] = ["secb-voter-a"]
    refuses(document, tmp_path, "absent from the readback of what exists")


def test_no_environments_readback_leaves_the_conjunct_unobserved(tmp_path):
    document = evidence()
    del document["oidc_policy"]["environments_observed"]
    report = accepts(document, tmp_path)
    assert report["conjuncts"]["SUBJECT_PRODUCIBLE_AND_DISTINGUISHING"]["observed"] is False
    assert "no environments_observed" in \
        report["conjuncts"]["SUBJECT_PRODUCIBLE_AND_DISTINGUISHING"]["note"]


def test_immutable_subject_prefix_must_match_the_tokens_own_ids(tmp_path):
    """The immutable format binds owner and repository IDs, and both come from the token."""
    document = evidence()
    document["oidc_policy"]["subject_configuration"] = {
        "use_default": True, "use_immutable_subject": True,
        "sub_claim_prefix": "repo:bstBizEra@999/secb_pf@1328913339", "context": "environment",
    }
    refuses(document, tmp_path, "disagrees with the prefix the")


def test_immutable_subject_is_accepted_when_the_ids_agree(tmp_path):
    """The real readback's prefix, with subjects rebuilt in the immutable shape."""
    document = evidence()
    prefix = REAL_SUB_CONFIG["sub_claim_prefix"]
    document["oidc_policy"]["subject_configuration"] = {
        "use_default": True, "use_immutable_subject": True,
        "sub_claim_prefix": prefix, "context": "environment",
    }
    for role in ROLES:
        document["principals"][role]["oidc"]["token"] = oidc_token(
            role, ROLES.index(role),
            claims_override={"sub": f"{prefix}:environment:{ENVIRONMENTS[role]}"})
    report = accepts(document, tmp_path)
    assert report["conjuncts"]["SUBJECT_PRODUCIBLE_AND_DISTINGUISHING"]["observed"] is True


def test_a_token_minted_for_another_environment_is_refused(tmp_path):
    """The gap the v1 counterexample exposed in revision 4's own first draft.

    voter_a presents a token minted for the executor's environment. It rebuilds to its OWN
    subject under the issuer configuration, so the consistency check passes -- and it must
    still be refused, because self-consistency says nothing about which principal holds it.
    """
    document = evidence()
    document["principals"]["voter_a"]["oidc"]["token"] = oidc_token(
        "voter_a", 0, claims_override={
            "environment": ENVIRONMENTS["executor"],
            "sub": f"repo:{SUBJECT_REPOSITORY}:environment:{ENVIRONMENTS['executor']}",
        })
    stderr = refuses(document, tmp_path, "but this principal declares")
    assert "self-consistent, not bound" in stderr


def test_an_environment_context_principal_must_declare_its_own_environment(tmp_path):
    document = evidence()
    del document["principals"]["voter_a"]["oidc"]["environment"]
    refuses(document, tmp_path, "declare which environment is ITS own")
