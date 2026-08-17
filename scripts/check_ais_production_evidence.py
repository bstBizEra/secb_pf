#!/usr/bin/env python3
"""Verify production AIS evidence against `secb.ais-production-evidence/v2` (FWK-089, #158).

WHY v2 EXISTS. v1 verified RS256 correctly -- whole-block EMSA-PKCS1-v1_5 per RFC 8017, with
padding slack rejected -- and was still unsound, because the signature covered the OIDC
workflow context and NOTHING ELSE. Every separation it reported was a comparison of
repository-authored STRINGS sitting next to that signature:

    one authentic workflow token, copied across every role record
    + fabricated distinct app / custody / policy strings
    + unsigned APPROVE ballots
    + a JWKS digest the caller computed and then supplied to itself
    -> v1 reported AIS4

That is internally consistent evidence, not independently established separation. The rule
that shapes this file:

    A VALID SIGNATURE OVER ONE PORTION OF A DOCUMENT MUST NOT LEND AUTHENTICITY TO
    ADJACENT UNSIGNED FIELDS.

CRYPTOGRAPHIC COVERAGE ACCOUNTING. Every conjunct names the fact asserted, the producer
authorised to assert it, and the signature binding that producer to this subject, this
snapshot and this purpose. Promotion requires

    ASSERTED_CONJUNCTS == AUTHENTICATED_CONJUNCTS == IDENTITY_BOUND_CONJUNCTS
                       == CURRENT_SNAPSHOT_CONJUNCTS

and the ledger is emitted so coverage can be audited rather than inferred. An asserted fact
with no authenticator is reported `UNAUTHENTICATED` and never counted.

WHAT NO DOCUMENT CAN DO HERE. AIS4 also requires ISSUER_TRUST_ANCHOR: proof that the key set
really is the issuer's. That is a live fetch from the issuer, which this tool does not
perform, and it cannot be delegated to a digest the caller supplies -- v1's
`EXPECT_JWKS_DIGEST` proved only that two values agreed, and one caller can compute both. So

    AIS4_NOT_REACHABLE_OFFLINE

is a structural property of this tool. The ceiling here is AIS3, and the top rung is
reachable only through Tranche B: separately administered Apps, distinct custody roots, one
real ceremony. External by construction; nothing here can mark it complete.

PURPOSE BINDING. Every signed payload carries a `purpose` and is accepted only for that
purpose. Without it a signed ballot could be replayed as an identity attestation -- same key,
same snapshot, different meaning.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

UTC = timezone.utc

OK = 0
FAIL = 2

SCHEMA = "secb.ais-production-evidence/v2"
GITHUB_ISSUER = "https://token.actions.githubusercontent.com"
GITHUB_ISSUER_HOST = "token.actions.githubusercontent.com"
GITHUB_JWKS_PATH = "/.well-known/jwks"

LADDER = [
    "AIS0_SELF_ASSERTED",
    "AIS1_WORKFLOW_BOUND",
    "AIS2_PLATFORM_PRINCIPALS",
    "AIS3_CUSTODY_SEPARATED",
    "AIS4_INDEPENDENT_DOMAINS",
]
OFFLINE_CEILING = "AIS3_CUSTODY_SEPARATED"

CONJUNCTS = (
    "SIGNED_WORKFLOW_CONTEXT",
    "PRINCIPAL_IDENTITY_ATTESTED",
    "CUSTODY_ATTESTED",
    "POLICY_ATTESTED",
    "BALLOTS_SIGNED",
    "EFFECT_ROLE_SEPARATION",
    "REVOCATION_RECEIPT_VERIFIED",
    "DISCOVERY_EXACTLY_BOUND",
    "ISSUER_TRUST_ANCHOR",
)

# purpose -> the key_role permitted to sign it. Fixing the producer of each fact is the
# point: otherwise whoever holds any key in the set can assert anything in the document.
PURPOSE_SIGNERS = {
    "PRINCIPAL_IDENTITY": "PRINCIPAL",
    "CUSTODY_BINDING": "CUSTODY_ROOT",
    "POLICY_BINDING": "POLICY_ADMIN_ROOT",
    "BALLOT": "PRINCIPAL",
    "REVOCATION_RECEIPT": "PLATFORM",
    "ROLE_ASSIGNMENT": "POLICY_ADMIN_ROOT",
    "OIDC": "PLATFORM",
}
KEY_ROLES = ("PRINCIPAL", "CUSTODY_ROOT", "POLICY_ADMIN_ROOT", "PLATFORM")

REQUIRED_OIDC_CLAIMS = ("iss", "aud", "sub", "exp", "iat", "jti")
BOUND_CLAIMS = ("repository_id", "workflow_sha", "job_workflow_ref")

MAX_TOKEN_LIFETIME_SECONDS = 3600
SHA256_DIGESTINFO = binascii.unhexlify("3031300d060960864801650304020105000420")


class Refused(ValueError):
    """The evidence contradicts itself, or claims what it does not authenticate."""


def b64url(data: str) -> bytes:
    try:
        return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))
    except (binascii.Error, ValueError) as exc:
        raise Refused(f"value is not base64url ({exc})") from exc


def canonical(payload: object) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(payload: object) -> str:
    return "sha256:" + hashlib.sha256(canonical(payload)).hexdigest()


def parse_time(label: str, value: object) -> datetime:
    if isinstance(value, bool):
        raise Refused(f"{label}: {value!r} is not an instant")
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=UTC)
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise Refused(f"{label}: {value!r} is not an ISO-8601 instant ({exc})") from exc
    if parsed.tzinfo is None:
        raise Refused(f"{label}: {value!r} has no timezone; an instant without one is ambiguous")
    return parsed


# --------------------------------------------------------------------------- primitives


def verify_rs256(signing_input: bytes, signature: bytes, key: dict) -> None:
    """RFC 8017 EMSA-PKCS1-v1_5 verification. Raises unless the block matches exactly."""
    n = int.from_bytes(b64url(key["n"]), "big")
    e = int.from_bytes(b64url(key["e"]), "big")
    if n.bit_length() < 2048:
        raise Refused(f"key {key['kid']}: modulus is {n.bit_length()} bits; under 2048 is refused")
    if e < 3 or e % 2 == 0:
        raise Refused(f"key {key['kid']}: public exponent {e} is not an odd integer >= 3")

    k = (n.bit_length() + 7) // 8
    if len(signature) != k:
        raise Refused(f"key {key['kid']}: signature is {len(signature)} bytes; modulus is {k}")

    tail = SHA256_DIGESTINFO + hashlib.sha256(signing_input).digest()
    padding_length = k - len(tail) - 3
    if padding_length < 8:
        raise Refused(f"key {key['kid']}: modulus too small for a PKCS#1 v1.5 SHA-256 signature")
    expected = b"\x00\x01" + b"\xff" * padding_length + b"\x00" + tail

    recovered = pow(int.from_bytes(signature, "big"), e, n).to_bytes(k, "big")
    # Whole-block comparison. A suffix scan leaves slack in the padding, and slack in the
    # padding is where Bleichenbacher-style forgeries live.
    if recovered != expected:
        raise Refused(f"key {key['kid']}: signature does not verify")


def key_for(keys: dict, kid: str, purpose: str) -> dict:
    key = keys.get(kid)
    if key is None:
        raise Refused(f"no key in the set matches kid {kid!r}")
    required = PURPOSE_SIGNERS[purpose]
    if key["key_role"] != required:
        raise Refused(
            f"key {kid!r} has key_role {key['key_role']!r} but purpose {purpose} must be "
            f"signed by a {required}"
        )
    return key


def verify_signed(
    label: str,
    envelope: dict,
    *,
    purpose: str,
    snapshot_digest: str,
    keys: dict,
    expect_owner: str | None = None,
    expect_fields: dict | None = None,
) -> dict:
    """Verify one signed envelope and return its payload.

    Order matters: the signature verifies; the signer holds the role authorised for this
    purpose; the payload declares this purpose; the payload is bound to THIS snapshot; the
    signed subject fields are the ones the caller expected. Every fact returned is covered by
    the signature, which is why nothing here reads a field from outside the envelope.
    """
    payload = envelope.get("payload")
    if not isinstance(payload, dict):
        raise Refused(f"{label}: signed envelope has no payload object")
    key = key_for(keys, envelope.get("kid", ""), purpose)
    verify_rs256(canonical(payload), b64url(envelope.get("signature", "")), key)

    if payload.get("purpose") != purpose:
        raise Refused(
            f"{label}: payload purpose is {payload.get('purpose')!r}, expected {purpose!r}. A "
            "signature made for one purpose must not be replayable as another"
        )
    if payload.get("snapshot_digest") != snapshot_digest:
        raise Refused(
            f"{label}: payload is bound to snapshot {payload.get('snapshot_digest')!r}, not "
            f"{snapshot_digest!r}. Evidence for another snapshot is another decision"
        )
    if expect_owner is not None and key["owner"] != expect_owner:
        raise Refused(
            f"{label}: signed by a key owned by {key['owner']!r}, expected {expect_owner!r}"
        )
    for field, expected in (expect_fields or {}).items():
        if payload.get(field) != expected:
            raise Refused(
                f"{label}: signed {field} is {payload.get(field)!r} but the document says "
                f"{expected!r}. The signed value is authoritative; the unsigned one is a claim"
            )
    return payload


def load_keys(evidence: dict) -> dict:
    """Index the key set by kid, refusing any set where two names share one key.

    Checking `kid` uniqueness alone would repeat the very error v2 exists to fix, one layer
    down: two kids over one modulus is ONE key holder wearing two names, and every
    separation computed from it would be a comparison of labels again.
    """
    keys: dict[str, dict] = {}
    by_material: dict[tuple[str, str], str] = {}
    for key in evidence["jwks"]["keys"]:
        kid = key["kid"]
        if kid in keys:
            raise Refused(f"duplicate kid {kid!r} in the key set")
        if key.get("key_role") not in KEY_ROLES:
            raise Refused(
                f"key {kid!r}: key_role {key.get('key_role')!r} is not one of {KEY_ROLES}"
            )
        if not key.get("owner"):
            raise Refused(f"key {kid!r}: owner is required -- an unowned key separates nothing")
        material = (key["n"], key["e"])
        if material in by_material:
            raise Refused(
                f"keys {by_material[material]!r} and {kid!r} share the same modulus. Two kids "
                "over one key is one holder with two names, not two principals"
            )
        by_material[material] = kid
        keys[kid] = key
    return keys


# ------------------------------------------------------------------------ OIDC, in full


def validate_oidc(role: str, principal: dict, evidence: dict, keys: dict, now: datetime,
                  seen_jti: dict) -> dict:
    """Signature, exact issuer, audience, subject, expiry, lifetime and replay.

    v1 read the signature, the issuer and three context claims. `aud`, `sub`, `exp`, `iat`
    and `jti` were unread, so an authentic token minted for another audience, expired by any
    margin, could be copied into every role record in the document.
    """
    oidc = principal["oidc"]
    parts = oidc["token"].split(".")
    if len(parts) != 3:
        raise Refused(f"{role}: oidc token is not a compact JWS")
    header_b64, payload_b64, signature_b64 = parts

    header = json.loads(b64url(header_b64))
    if header.get("alg") != "RS256":
        raise Refused(
            f"{role}: token alg is {header.get('alg')!r}; only RS256 is verified, and `none` "
            "or an HMAC alg against an RSA key set is the classic algorithm-confusion downgrade"
        )
    if header.get("kid") != oidc["kid"]:
        raise Refused(
            f"{role}: token kid {header.get('kid')!r} disagrees with the declared {oidc['kid']!r}"
        )
    key = key_for(keys, oidc["kid"], "OIDC")
    verify_rs256(f"{header_b64}.{payload_b64}".encode("ascii"), b64url(signature_b64), key)
    claims = json.loads(b64url(payload_b64))

    missing = [c for c in REQUIRED_OIDC_CLAIMS if c not in claims]
    if missing:
        raise Refused(f"{role}: signed token is missing required claims {missing}")
    if claims["iss"] != GITHUB_ISSUER:
        raise Refused(f"{role}: token iss {claims['iss']!r} is not exactly {GITHUB_ISSUER!r}")

    policy = evidence["oidc_policy"]
    audience = claims["aud"] if isinstance(claims["aud"], list) else [claims["aud"]]
    if policy["audience"] not in audience:
        raise Refused(
            f"{role}: token aud {claims['aud']!r} does not include the required "
            f"{policy['audience']!r}. A token minted for another audience is a valid token "
            "for someone else"
        )
    # Structured, segment-exact. A raw prefix test accepts any longer repository whose
    # name merely STARTS with the expected one ("secb_pf" under a prefix of "secb"), and it
    # never binds the token to the ROLE presenting it -- so one principal's token satisfies
    # every role record that carries the same prefix. Both are closed by comparing segments.
    segments = str(claims["sub"]).split(":")
    expected = ["repo", policy["subject_repository"], "role", role]
    if segments != expected:
        raise Refused(
            f"{role}: token sub {claims['sub']!r} does not match exactly "
            f"{':'.join(expected)!r}. A prefix match binds neither the repository nor the "
            "role, so one token would satisfy every role record sharing that prefix"
        )

    issued = parse_time(f"{role}.iat", claims["iat"])
    expires = parse_time(f"{role}.exp", claims["exp"])
    if issued > now:
        raise Refused(
            f"{role}: token iat {issued.isoformat()} is after the evaluation instant "
            f"{now.isoformat()}. A token issued in the future is either a clock forgery or "
            "evidence about a run that has not happened"
        )
    if "nbf" in claims and parse_time(f"{role}.nbf", claims["nbf"]) > now:
        raise Refused(f"{role}: token is not yet valid at {now.isoformat()}")
    if expires <= issued:
        raise Refused(f"{role}: token exp is at or before iat")
    if (expires - issued).total_seconds() > MAX_TOKEN_LIFETIME_SECONDS:
        raise Refused(
            f"{role}: token lifetime is {int((expires - issued).total_seconds())}s, over the "
            f"{MAX_TOKEN_LIFETIME_SECONDS}s ceiling"
        )
    if now >= expires:
        raise Refused(
            f"{role}: token expired at {expires.isoformat()}, evaluated at {now.isoformat()}"
        )

    if claims["jti"] in seen_jti:
        raise Refused(
            f"{role}: jti {claims['jti']!r} was already presented by {seen_jti[claims['jti']]!r}. "
            "One token copied across role records is one principal, however many roles the "
            "document names"
        )
    seen_jti[claims["jti"]] = role

    for claim in BOUND_CLAIMS:
        if not claims.get(claim):
            raise Refused(f"{role}: signed token is missing the {claim} claim")
        if str(claims[claim]) != str(evidence["snapshot"][claim]):
            raise Refused(
                f"{role}: token {claim} is {claims[claim]!r} but the snapshot says "
                f"{evidence['snapshot'][claim]!r}"
            )
    return claims


# -------------------------------------------------------------------------- the checks


def check_no_claimed_level(evidence: dict) -> None:
    banned = ("ais_level", "level", "production_ais_level", "claimed_level", "observed_level")
    present = [k for k in banned if k in evidence]
    if present:
        raise Refused(
            f"evidence declares {present}; the level is COMPUTED from the conjuncts and a "
            "document that asserts its own level makes every check decorative"
        )


def check_scope(role: str, scope: dict) -> None:
    for repository in scope["repositories"]:
        if "*" in repository:
            raise Refused(f"{role}: repository scope {repository!r} is a wildcard")
    for permission, access in scope["permissions"].items():
        if "*" in permission or "*" in access:
            raise Refused(f"{role}: permission {permission}={access!r} is a wildcard")
        if access == "admin":
            raise Refused(f"{role}: permission {permission}=admin is administrative")


def check_discovery(evidence: dict) -> tuple[bool, str]:
    """Exact issuer and jwks_uri binding. `startswith` is not host validation.

    v1 accepted any URL beginning with the issuer string, which includes
    `https://token.actions.githubusercontent.com.attacker.example/jwks` (suffix-extension
    host) and `https://token.actions.githubusercontent.com@evil.example/jwks` (userinfo
    trick). Both are refused here by parsing the URL and comparing the host exactly.
    """
    jwks = evidence["jwks"]
    if jwks["provenance"] != "ISSUER_DISCOVERY":
        return False, (
            f"jwks.provenance is {jwks['provenance']}: the keys are repository-supplied, so "
            "the signatures prove internal consistency and not an issuer"
        )
    discovery = jwks.get("discovery")
    if not discovery:
        raise Refused("provenance is ISSUER_DISCOVERY with no discovery record")
    if jwks["issuer"] != GITHUB_ISSUER:
        return False, f"issuer {jwks['issuer']!r} is not exactly {GITHUB_ISSUER!r}"

    parsed = urlparse(discovery["jwks_uri"])
    if parsed.scheme != "https":
        raise Refused(f"jwks_uri scheme {parsed.scheme!r} is not https")
    if parsed.username or parsed.password or "@" in (parsed.netloc or ""):
        raise Refused(
            f"jwks_uri {discovery['jwks_uri']!r} carries userinfo; the real host is what "
            "follows the '@', which is how a prefix check gets fooled"
        )
    if parsed.hostname != GITHUB_ISSUER_HOST:
        raise Refused(f"jwks_uri host {parsed.hostname!r} is not exactly {GITHUB_ISSUER_HOST!r}")
    if parsed.path != GITHUB_JWKS_PATH:
        raise Refused(f"jwks_uri path {parsed.path!r} is not {GITHUB_JWKS_PATH!r}")
    if discovery["response_digest"] != digest(jwks["keys"]):
        raise Refused(
            f"discovery response_digest {discovery['response_digest']} does not digest the "
            f"key set it accompanies ({digest(jwks['keys'])})"
        )
    return True, f"issuer and jwks_uri bound exactly; keys digest {discovery['response_digest']}"


def evaluate(evidence: dict, expected_main_sha: str, evaluate_at: str) -> tuple[dict, dict]:
    """Return (conjunct results, coverage ledger). Contradictions raise."""
    if evidence.get("schema") != SCHEMA:
        raise Refused(f"schema is {evidence.get('schema')!r}, expected {SCHEMA!r}")
    check_no_claimed_level(evidence)
    if expected_main_sha and evidence["snapshot"]["main_sha"] != expected_main_sha:
        raise Refused(
            f"snapshot main_sha {evidence['snapshot']['main_sha']} is not the expected "
            f"{expected_main_sha}"
        )
    now = parse_time("EVALUATE_AT", evaluate_at) if evaluate_at else None

    principals = evidence["principals"]
    if len(principals) < 2:
        raise Refused("a substrate with fewer than two principals separates nothing")
    keys = load_keys(evidence)
    snapshot_digest = digest(evidence["snapshot"])

    results: dict[str, tuple[bool, str]] = {}
    ledger: dict[str, dict] = {}

    def record(conjunct: str, fact: str, producer: str, authenticator: str | None) -> None:
        ledger[conjunct] = {
            "asserted_fact": fact,
            "authoritative_producer": producer,
            "authenticator": authenticator or "UNAUTHENTICATED",
            "bound_to_snapshot": authenticator is not None,
        }

    # 1. SIGNED_WORKFLOW_CONTEXT.
    if now is None:
        results["SIGNED_WORKFLOW_CONTEXT"] = (
            False, "EVALUATE_AT was not supplied, so token expiry cannot be evaluated")
        record("SIGNED_WORKFLOW_CONTEXT", "workflow execution context", "the issuer", None)
    else:
        seen_jti: dict[str, str] = {}
        for role in sorted(principals):
            validate_oidc(role, principals[role], evidence, keys, now, seen_jti)
        results["SIGNED_WORKFLOW_CONTEXT"] = (
            True, f"{len(principals)} tokens fully validated, {len(seen_jti)} distinct jti")
        record("SIGNED_WORKFLOW_CONTEXT", "workflow execution context",
               f"the issuer {GITHUB_ISSUER}", "PLATFORM-signed OIDC JWS, one distinct jti per role")

    # 2. PRINCIPAL_IDENTITY_ATTESTED -- app/installation/role signed by the principal itself.
    principal_keys: dict[str, str] = {}
    for role, principal in sorted(principals.items()):
        verify_signed(
            f"{role}.identity_attestation", principal["identity_attestation"],
            purpose="PRINCIPAL_IDENTITY", snapshot_digest=snapshot_digest, keys=keys,
            expect_fields={
                "app_id": principal["app_id"],
                "installation_id": principal["installation_id"],
                "role": role,
            },
        )
        kid = principal["identity_attestation"]["kid"]
        if kid in principal_keys:
            raise Refused(
                f"{role} and {principal_keys[kid]} signed their identity attestations with the "
                f"same key {kid!r}. One signing key is one principal, whatever the labels say"
            )
        principal_keys[kid] = role
        check_scope(role, principal["token_scope"])

    seen_apps: dict[tuple, list[str]] = {}
    for role, principal in principals.items():
        seen_apps.setdefault(
            (principal["app_id"], principal["installation_id"]), []).append(role)
    shared = {str(k): sorted(v) for k, v in seen_apps.items() if len(v) > 1}
    if shared:
        raise Refused(f"roles share an App/installation: {shared}")
    results["PRINCIPAL_IDENTITY_ATTESTED"] = (
        True, f"{len(principals)} identity attestations, each signed by a distinct key")
    record("PRINCIPAL_IDENTITY_ATTESTED", "app_id, installation_id, role",
           "the principal itself", "PRINCIPAL-signed PRINCIPAL_IDENTITY attestation")

    # 3. CUSTODY_ATTESTED -- the custody ROOT attests that it holds this principal's key.
    custody_roots: dict[str, list[str]] = {}
    for role, principal in sorted(principals.items()):
        verify_signed(
            f"{role}.custody_attestation", principal["custody_attestation"],
            purpose="CUSTODY_BINDING", snapshot_digest=snapshot_digest, keys=keys,
            expect_owner=principal["custody_domain"],
            expect_fields={
                "principal_kid": principal["identity_attestation"]["kid"],
                "custody_root": principal["custody_domain"],
            },
        )
        custody_roots.setdefault(principal["custody_domain"], []).append(role)
    shared_custody = {k: sorted(v) for k, v in custody_roots.items() if len(v) > 1}
    if shared_custody:
        raise Refused(
            f"roles share a credential custody domain: {shared_custody}. One root that can "
            "read every private key is one principal wearing several hats"
        )
    results["CUSTODY_ATTESTED"] = (
        True, f"{len(custody_roots)} custody roots, each attesting exactly one principal key")
    record("CUSTODY_ATTESTED", "which root holds the principal's private key",
           "the custody root", "CUSTODY_ROOT-signed CUSTODY_BINDING attestation")

    # 4. POLICY_ATTESTED -- an independent admin root signs it, non-reciprocally.
    policy_domains: dict[str, list[str]] = {}
    administered_by: dict[str, str] = {}
    for role, principal in sorted(principals.items()):
        payload = verify_signed(
            f"{role}.policy_attestation", principal["policy_attestation"],
            purpose="POLICY_BINDING", snapshot_digest=snapshot_digest, keys=keys,
            expect_fields={"policy_domain": principal["policy_domain"], "role": role},
        )
        admin = payload["administered_by"]
        signer_owner = keys[principal["policy_attestation"]["kid"]]["owner"]
        if signer_owner != admin:
            raise Refused(
                f"{role}: policy attestation names administrator {admin!r} but is signed by a "
                f"key owned by {signer_owner!r}. A signature from one admin root asserting "
                "that ANOTHER root governs this principal is hearsay: the signer must be the "
                "producer of the fact it asserts"
            )
        if admin == principal["policy_domain"]:
            raise Refused(f"{role}: policy is administered by its own domain {admin!r}")
        administered_by[principal["policy_domain"]] = admin
        policy_domains.setdefault(principal["policy_domain"], []).append(role)
    shared_policy = {k: sorted(v) for k, v in policy_domains.items() if len(v) > 1}
    if shared_policy:
        raise Refused(f"roles share a policy domain: {shared_policy}")
    for domain, admin in administered_by.items():
        if administered_by.get(admin) == domain:
            raise Refused(
                f"policy administration is reciprocal: {domain!r} administers {admin!r} and "
                "back again. Mutual administration is one administrator with two names, which "
                "is why unequal labels are not independence"
            )
    external = sorted({a for a in administered_by.values() if a not in policy_domains})
    if not external:
        raise Refused(
            "every policy administrator is itself one of the principals' policy domains, so no "
            "administration is external to the set being validated"
        )
    results["POLICY_ATTESTED"] = (
        True,
        f"{len(policy_domains)} policy domains, non-reciprocal, external admin root(s) {external}",
    )
    record("POLICY_ATTESTED", "which admin root governs the principal's policy",
           "the policy admin root", "POLICY_ADMIN_ROOT-signed POLICY_BINDING attestation")

    # 5. BALLOTS_SIGNED -- each ballot signed by its own principal's key, nonce-bound.
    ballots = evidence["ballots"]
    voters: list[str] = []
    nonces: set[str] = set()
    for index, ballot in enumerate(ballots):
        payload = verify_signed(
            f"ballot[{index}]", ballot, purpose="BALLOT",
            snapshot_digest=snapshot_digest, keys=keys,
        )
        voter = payload["principal"]
        if voter not in principals:
            raise Refused(f"ballot[{index}]: principal {voter!r} is absent from the evidence")
        expected_kid = principals[voter]["identity_attestation"]["kid"]
        if ballot["kid"] != expected_kid:
            raise Refused(
                f"ballot[{index}]: signed by {ballot['kid']!r} but {voter!r}'s identity key is "
                f"{expected_kid!r}. A ballot signed by another key is another principal's ballot"
            )
        if voter in voters:
            raise Refused(f"ballot[{index}]: {voter!r} cast more than one ballot")
        if payload["nonce"] in nonces:
            raise Refused(f"ballot[{index}]: nonce {payload['nonce']!r} is replayed")
        nonces.add(payload["nonce"])
        voters.append(voter)

    if evidence["decision_receipt_digest"] != digest(ballots):
        raise Refused(
            f"decision_receipt_digest {evidence['decision_receipt_digest']} does not digest the "
            f"ballot set ({digest(ballots)}). A receipt nothing consumes is decorative, and one "
            "that disagrees with the ballots is worse"
        )
    approvals = [b for b in ballots if b["payload"]["decision"] == "APPROVE"]
    if len(approvals) < 2:
        results["BALLOTS_SIGNED"] = (
            False,
            f"{len(approvals)} signed approving ballot(s); two distinct principals are the minimum",
        )
        record("BALLOTS_SIGNED", "the decision", "each voting principal", None)
    else:
        results["BALLOTS_SIGNED"] = (
            True,
            f"{len(approvals)} signed approvals from distinct principals, receipt digest bound",
        )
        record("BALLOTS_SIGNED", "the decision", "each voting principal",
               "PRINCIPAL-signed BALLOT with nonce, digested by decision_receipt_digest")

    # 6. EFFECT_ROLE_SEPARATION -- the ASSIGNMENT itself must be signed.
    # v2 read executor/readback from an unsigned `roles` object. The separation was then only
    # as trustworthy as whoever wrote the file: naming a compliant executor costs nothing when
    # nobody signs the naming. The assignment is now a signed envelope from a POLICY_ADMIN_ROOT
    # that is EXTERNAL to the principals' own policy domains -- authority over the derived
    # decision, not merely a record of it.
    assignment = evidence.get("role_assignment")
    if not assignment:
        results["EFFECT_ROLE_SEPARATION"] = (
            False, "role_assignment is absent; who executes and who verifies is unattested")
        record("EFFECT_ROLE_SEPARATION", "who executes and who verifies",
               "an external policy admin root", None)
        voters_note = None
    else:
        payload = verify_signed(
            "role_assignment", assignment, purpose="ROLE_ASSIGNMENT",
            snapshot_digest=snapshot_digest, keys=keys,
        )
        signer_owner = keys[assignment["kid"]]["owner"]
        if signer_owner in policy_domains:
            raise Refused(
                f"role_assignment is signed by {signer_owner!r}, which is one of the "
                "principals' own policy domains. An assignment signed from inside the set it "
                "governs is self-assignment with an extra step"
            )
        if signer_owner not in external:
            raise Refused(
                f"role_assignment is signed by {signer_owner!r}, which administers none of "
                f"these principals' policies (external roots: {external}). A signer with no "
                "authority over the subjects has no authority over their role assignment"
            )
        executor, readback = payload["executor"], payload["readback_verifier"]
        absent = sorted({executor, readback} - set(principals))
        if absent:
            raise Refused(f"role_assignment names principals absent from the evidence: {absent}")
        if executor in voters:
            raise Refused(
                f"the executor {executor!r} also cast a ballot. An executor that votes on its "
                "own effect provides no separation"
            )
        if executor == readback:
            raise Refused(
                f"the executor {executor!r} is also the readback verifier. Verifying your own "
                "landing is the failure Typed Multi-Path Readback exists to prevent"
            )
        results["EFFECT_ROLE_SEPARATION"] = (
            True,
            f"executor {executor}, readback {readback}, assigned by external root {signer_owner}",
        )
        record("EFFECT_ROLE_SEPARATION", "who executes and who verifies",
               f"external policy admin root {signer_owner}",
               "POLICY_ADMIN_ROOT-signed ROLE_ASSIGNMENT, snapshot-bound")

    # 7. REVOCATION_RECEIPT_VERIFIED -- the PLATFORM signs the denial, not the document.
    not_denied: list[str] = []
    for role, principal in sorted(principals.items()):
        receipt = principal.get("revocation_receipt")
        if not receipt:
            not_denied.append(role)
            continue
        payload = verify_signed(
            f"{role}.revocation_receipt", receipt, purpose="REVOCATION_RECEIPT",
            snapshot_digest=snapshot_digest, keys=keys,
            expect_fields={"principal_kid": principal["identity_attestation"]["kid"]},
        )
        if payload["reuse_result"] == "ACCEPTED":
            raise Refused(
                f"{role}: reuse after revocation was ACCEPTED. Revocation that does not deny "
                "reuse is a log entry"
            )
        if payload["reuse_result"] != "DENIED":
            not_denied.append(role)
            continue
        revoked = parse_time(f"{role}.revoked_at", payload["revoked_at"])
        attempted = parse_time(f"{role}.reuse_attempted_at", payload["reuse_attempted_at"])
        if attempted <= revoked:
            raise Refused(
                f"{role}: reuse was attempted at or before revocation, so DENIED shows nothing "
                "about revocation"
            )
    if not_denied:
        results["REVOCATION_RECEIPT_VERIFIED"] = (
            False, f"no verified reuse-after-revocation receipt for: {not_denied}")
        record("REVOCATION_RECEIPT_VERIFIED", "reuse after revocation was denied",
               "the platform", None)
    else:
        results["REVOCATION_RECEIPT_VERIFIED"] = (
            True, "every principal has a PLATFORM-signed receipt showing reuse DENIED")
        record("REVOCATION_RECEIPT_VERIFIED", "reuse after revocation was denied",
               "the platform", "PLATFORM-signed REVOCATION_RECEIPT")

    # 8. DISCOVERY_EXACTLY_BOUND.
    bound, note = check_discovery(evidence)
    results["DISCOVERY_EXACTLY_BOUND"] = (bound, note)
    record("DISCOVERY_EXACTLY_BOUND", "the key set is the issuer's published set", "the issuer",
           "exact issuer + jwks_uri host/path + response digest" if bound else None)

    # 9. ISSUER_TRUST_ANCHOR -- unsatisfiable here, by construction rather than by omission.
    results["ISSUER_TRUST_ANCHOR"] = (
        False,
        "a live fetch from the issuer is required and this tool performs none. It cannot be "
        "delegated to a caller-supplied digest: one caller can compute and present both sides, "
        "so agreement proves arithmetic, not provenance",
    )
    record("ISSUER_TRUST_ANCHOR", "the key set really is the issuer's",
           "an independent fetcher outside this repository", None)

    attestation = evidence.get("attestation")
    if attestation and attestation["signer_verified"] and not attestation.get("verified_by"):
        raise Refused(
            "attestation declares signer_verified with no verified_by. Generation has no "
            "security value until signature, timestamp and signer are independently checked"
        )

    return results, ledger


def observed_level(results: dict) -> str:
    if not results["SIGNED_WORKFLOW_CONTEXT"][0]:
        return LADDER[0]
    level = "AIS1_WORKFLOW_BOUND"
    if not results["PRINCIPAL_IDENTITY_ATTESTED"][0]:
        return level
    level = "AIS2_PLATFORM_PRINCIPALS"
    if not results["CUSTODY_ATTESTED"][0]:
        return level
    level = "AIS3_CUSTODY_SEPARATED"
    if all(results[name][0] for name in CONJUNCTS):
        return "AIS4_INDEPENDENT_DOMAINS"
    return level


def main(argv: list[str]) -> int:
    env = dict(os.environ)
    path = env.get("EVIDENCE", "").strip()
    if not path:
        print("REFUSED (closed): EVIDENCE is required", file=sys.stderr)
        return FAIL
    try:
        evidence = json.loads(Path(path).read_text(encoding="utf-8"))
        results, ledger = evaluate(
            evidence,
            env.get("EXPECT_MAIN_SHA", "").strip(),
            env.get("EVALUATE_AT", "").strip(),
        )
    except (OSError, json.JSONDecodeError) as exc:
        print(f"REFUSED (closed): evidence unreadable or unparseable ({exc})", file=sys.stderr)
        return FAIL
    except Refused as exc:
        print(f"REFUSED (closed): {exc}", file=sys.stderr)
        return FAIL
    except (KeyError, TypeError, AttributeError, IndexError) as exc:
        print(f"REFUSED (closed): malformed evidence ({exc!r})", file=sys.stderr)
        return FAIL

    level = observed_level(results)
    authenticated = [c for c in CONJUNCTS if ledger[c]["authenticator"] != "UNAUTHENTICATED"]
    print(json.dumps({
        "schema": "secb.ais-production-observation/v2",
        "OBSERVED_LEVEL": level,
        "PRODUCTION_AIS_LEVEL": level if level == LADDER[4] else "NOT_OBSERVED",
        "offline_ceiling": OFFLINE_CEILING,
        "ais4_reachable_here": False,
        "conjuncts": {c: {"observed": results[c][0], "note": results[c][1]} for c in CONJUNCTS},
        "unsatisfied": [c for c in CONJUNCTS if not results[c][0]],
        "coverage_ledger": ledger,
        "coverage_accounting": {
            "asserted": len(CONJUNCTS),
            "authenticated": len(authenticated),
            "unauthenticated": [c for c in CONJUNCTS if c not in authenticated],
            "complete": len(authenticated) == len(CONJUNCTS),
        },
        "tranche_b": "EXTERNAL_AUTHORITY_REQUIRED -- no input to this tool can mark it complete",
        "not_proven": [
            "that the key set is the issuer's; that needs a live fetch this tool cannot do",
            "that a signature over one field authenticates any adjacent unsigned field",
            "that distinct identifier STRINGS are distinct security domains -- only distinct "
            "signing keys with attestations from distinct roots evidence that",
            "that RS256 verification here covers certificate chains or key revocation",
        ],
        "confers_merge_authority": False,
    }, indent=2, sort_keys=True))
    return OK


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
