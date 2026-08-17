#!/usr/bin/env python3
"""Verify production AIS evidence against `secb.ais-production-evidence/v1` (FWK-089, #158).

WHAT THIS IS. Tranche A of #158: the verifier. It reads a document describing an identity
substrate and COMPUTES the highest level the evidence supports. It never reads a claimed
level, because a document that can assert its own level makes every check below decorative.

WHAT THIS IS NOT. It does not provision an App, a custody domain, a policy domain, or a
decision path, and running it green does not mean AIS4 was reached:

    VERIFIER_AVAILABLE != SUBSTRATE_AVAILABLE != INDEPENDENCE_OBSERVED

Tranche B -- separately administered Apps, distinct custody and policy domains, one real
ceremony -- is external by construction. Repository code cannot mark it complete, so this
tool has no flag, env var or input that does.

THE EIGHT CONJUNCTS. AIS4_INDEPENDENT_DOMAINS requires ALL of:

    OIDC_BOUND ^ DISTINCT_PLATFORM_PRINCIPALS ^ DISTINCT_CUSTODY_DOMAINS
    ^ DISTINCT_POLICY_DOMAINS ^ INDEPENDENT_DECISIONS ^ EFFECT_ROLE_SEPARATION
    ^ REVOCATION_BEHAVIOUR_OBSERVED ^ SIGNER_VERIFIED

Each is evidenced separately and reported separately. A missing conjunct yields
NOT_OBSERVED, never a rounded-up level.

TWO OUTCOMES, KEPT APART. Honest incompleteness and contradiction are different facts:

    exit 0 + PRODUCTION_AIS_LEVEL: NOT_OBSERVED  -- the evidence is well-formed and does
        not reach AIS4. A LOCAL_FIXTURE key set lands here: it is the truthful state of a
        repository that has no production substrate.
    exit 2 REFUSED                               -- the evidence contradicts itself, or
        claims something it does not show (shared App presented as separate principals, a
        fixture key set presented as issuer discovery, a signature that does not verify).

Collapsing the two would mean either that absence reads as failure, or -- far worse -- that
a contradiction reads as mere absence.

ON THE SIGNATURE CHECK. RS256 verification is `pow(sig, e, n)` plus a PKCS#1 v1.5 padding
comparison: public-key arithmetic over public inputs, no secret material, so it is
implementable under NFR-12 (stdlib only) without a dependency. Its limits are declared
rather than left to a reader: RS256 only, no certificate chain, no revocation of the key
itself, and no constant-time guarantee (irrelevant here -- everything it touches is
public). What it proves is that the token was signed by the holder of the private key for
`kid`. WHO that holder is comes from jwks.provenance, which is why a verifying signature
over a LOCAL_FIXTURE key set does not satisfy SIGNER_VERIFIED.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

OK = 0
FAIL = 2

SCHEMA = "secb.ais-production-evidence/v1"
GITHUB_ISSUER = "https://token.actions.githubusercontent.com"

LADDER = [
    "AIS0_SELF_ASSERTED",
    "AIS1_WORKFLOW_BOUND",
    "AIS2_PLATFORM_PRINCIPALS",
    "AIS3_CUSTODY_SEPARATED",
    "AIS4_INDEPENDENT_DOMAINS",
]

CONJUNCTS = (
    "OIDC_BOUND",
    "DISTINCT_PLATFORM_PRINCIPALS",
    "DISTINCT_CUSTODY_DOMAINS",
    "DISTINCT_POLICY_DOMAINS",
    "INDEPENDENT_DECISIONS",
    "EFFECT_ROLE_SEPARATION",
    "REVOCATION_BEHAVIOUR_OBSERVED",
    "SIGNER_VERIFIED",
)

# Claims that must be present AND must agree with the snapshot. `workflow_sha` and
# `job_workflow_ref` are what make a token specific to the code that ran, rather than to
# the repository in general.
BOUND_CLAIMS = {
    "repository_id": "repository_id",
    "workflow_sha": "workflow_sha",
    "job_workflow_ref": "job_workflow_ref",
}

MAX_TOKEN_LIFETIME_SECONDS = 3600
SHA256_DIGESTINFO = binascii.unhexlify("3031300d060960864801650304020105000420")


class Refused(ValueError):
    """The evidence contradicts itself or claims what it does not show."""


def b64url(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    try:
        return base64.urlsafe_b64decode(data + pad)
    except (binascii.Error, ValueError) as exc:
        raise Refused(f"value is not base64url ({exc})") from exc


def canonical(payload: object) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(payload: object) -> str:
    return "sha256:" + hashlib.sha256(canonical(payload)).hexdigest()


def parse_time(label: str, value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise Refused(f"{label}: {value!r} is not an ISO-8601 instant ({exc})") from exc


def verify_rs256(token: str, key: dict) -> dict:
    """Return the token's claims, or raise. The claims come from the SIGNED bytes only."""
    parts = token.split(".")
    if len(parts) != 3:
        raise Refused("oidc token is not a compact JWS (expected three dot-separated parts)")
    header_b64, payload_b64, signature_b64 = parts

    header = json.loads(b64url(header_b64))
    if header.get("alg") != "RS256":
        raise Refused(
            f"token alg is {header.get('alg')!r}; only RS256 is verified here, and `none` "
            "or an HMAC alg against an RSA key set is the classic algorithm-confusion "
            "downgrade"
        )
    if header.get("kid") != key["kid"]:
        raise Refused(f"token kid {header.get('kid')!r} does not match the key {key['kid']!r}")

    n = int.from_bytes(b64url(key["n"]), "big")
    e = int.from_bytes(b64url(key["e"]), "big")
    if n.bit_length() < 2048:
        raise Refused(f"modulus is {n.bit_length()} bits; under 2048 is not acceptable")
    if e < 3 or e % 2 == 0:
        raise Refused(f"public exponent {e} is not an odd integer >= 3")

    signature = b64url(signature_b64)
    k = (n.bit_length() + 7) // 8
    if len(signature) != k:
        raise Refused(f"signature is {len(signature)} bytes; the modulus is {k}")

    # EMSA-PKCS1-v1_5: 0x00 0x01 || 0xff... || 0x00 || DigestInfo || H(m)
    expected_hash = hashlib.sha256(f"{header_b64}.{payload_b64}".encode("ascii")).digest()
    tail = SHA256_DIGESTINFO + expected_hash
    padding_length = k - len(tail) - 3
    if padding_length < 8:
        raise Refused("modulus too small to hold a PKCS#1 v1.5 SHA-256 signature")
    expected_em = b"\x00\x01" + b"\xff" * padding_length + b"\x00" + tail

    recovered = pow(int.from_bytes(signature, "big"), e, n).to_bytes(k, "big")
    # Whole-block comparison. Scanning for the DigestInfo instead of rebuilding the exact
    # expected block is how Bleichenbacher-style forgeries get in: slack anywhere in the
    # padding is slack an attacker can put chosen bytes into.
    if recovered != expected_em:
        raise Refused("oidc signature does not verify against the declared key")

    return json.loads(b64url(payload_b64))


def check_no_claimed_level(evidence: dict) -> None:
    """A level is computed here or it is nothing."""
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
            raise Refused(
                f"{role}: permission {permission}=admin. An administrative principal can "
                "edit the policy that validates it, which is the separation this level is "
                "supposed to establish"
            )
    issued = parse_time(f"{role}.issued_at", scope["issued_at"])
    expires = parse_time(f"{role}.expires_at", scope["expires_at"])
    lifetime = (expires - issued).total_seconds()
    if lifetime <= 0:
        raise Refused(f"{role}: token expires at or before it was issued")
    if lifetime > MAX_TOKEN_LIFETIME_SECONDS:
        raise Refused(
            f"{role}: token lifetime is {int(lifetime)}s, over the "
            f"{MAX_TOKEN_LIFETIME_SECONDS}s ceiling"
        )


def check_oidc(evidence: dict) -> None:
    """Every principal's token verifies and its signed claims agree with the snapshot."""
    snapshot = evidence["snapshot"]
    keys = {key["kid"]: key for key in evidence["jwks"]["keys"]}
    issuer = evidence["jwks"]["issuer"]

    for role, principal in sorted(evidence["principals"].items()):
        oidc = principal["oidc"]
        key = keys.get(oidc["kid"])
        if key is None:
            raise Refused(f"{role}: no key in the set matches kid {oidc['kid']!r}")
        claims = verify_rs256(oidc["token"], key)

        if claims.get("iss") != issuer:
            raise Refused(
                f"{role}: token iss {claims.get('iss')!r} is not the declared issuer "
                f"{issuer!r}"
            )
        for claim, field in BOUND_CLAIMS.items():
            if not claims.get(claim):
                raise Refused(f"{role}: signed token is missing the {claim} claim")
            if str(claims[claim]) != str(snapshot[field]):
                raise Refused(
                    f"{role}: token {claim} is {claims[claim]!r} but the snapshot says "
                    f"{snapshot[field]!r}. A token bound to other code proves an execution "
                    "context, not this one"
                )


def check_snapshot_freshness(evidence: dict, expected_main_sha: str) -> None:
    if expected_main_sha and evidence["snapshot"]["main_sha"] != expected_main_sha:
        raise Refused(
            f"snapshot main_sha {evidence['snapshot']['main_sha']} is not the expected "
            f"{expected_main_sha}. Evidence for a superseded tree is historical, and "
            "SUPERSEDED_FOR_CURRENT_ELIGIBILITY != VALID_FOR_THIS_DECISION"
        )


def evaluate(evidence: dict, expected_main_sha: str, expected_jwks_digest: str = "") -> dict:
    """Return {conjunct: (observed, note)}. Contradictions raise instead."""
    if evidence.get("schema") != SCHEMA:
        raise Refused(f"schema is {evidence.get('schema')!r}, expected {SCHEMA!r}")
    check_no_claimed_level(evidence)
    check_snapshot_freshness(evidence, expected_main_sha)

    principals = evidence["principals"]
    if len(principals) < 2:
        raise Refused("a substrate with fewer than two principals separates nothing")

    results: dict[str, tuple[bool, str]] = {}

    # 1. OIDC_BOUND -- every token verifies and binds this snapshot.
    check_oidc(evidence)
    results["OIDC_BOUND"] = (True, "every principal's signed token binds this snapshot")

    # 2. DISTINCT_PLATFORM_PRINCIPALS.
    seen: dict[tuple[str, str], list[str]] = {}
    for role, principal in principals.items():
        seen.setdefault((principal["app_id"], principal["installation_id"]), []).append(role)
    shared = {str(k): sorted(v) for k, v in seen.items() if len(v) > 1}
    if shared:
        raise Refused(
            f"roles share an App/installation: {shared}. Distinct role NAMES over one "
            "platform principal is a label, not a separation"
        )
    results["DISTINCT_PLATFORM_PRINCIPALS"] = (True, f"{len(principals)} distinct App installations")

    # 3. DISTINCT_CUSTODY_DOMAINS.
    custody: dict[str, list[str]] = {}
    for role, principal in principals.items():
        custody.setdefault(principal["custody_domain"], []).append(role)
        check_scope(role, principal["token_scope"])
    shared_custody = {k: sorted(v) for k, v in custody.items() if len(v) > 1}
    if shared_custody:
        raise Refused(
            f"roles share a credential custody domain: {shared_custody}. One runtime that "
            "can read every private key is one principal wearing several hats"
        )
    results["DISTINCT_CUSTODY_DOMAINS"] = (True, f"{len(custody)} distinct custody domains")

    # 4. DISTINCT_POLICY_DOMAINS -- and nobody administers the policy that validates them.
    policy: dict[str, list[str]] = {}
    for role, principal in principals.items():
        policy.setdefault(principal["policy_domain"], []).append(role)
        if principal["policy_administered_by"] == principal["policy_domain"]:
            raise Refused(
                f"{role}: policy_administered_by equals its own policy_domain "
                f"({principal['policy_domain']!r}). A principal that can edit the policy "
                "validating its decisions is its own auditor"
            )
    shared_policy = {k: sorted(v) for k, v in policy.items() if len(v) > 1}
    if shared_policy:
        raise Refused(f"roles share a policy domain: {shared_policy}")
    results["DISTINCT_POLICY_DOMAINS"] = (True, f"{len(policy)} distinct, externally administered policy domains")

    # 5. INDEPENDENT_DECISIONS -- distinct principals, one snapshot, computed digest.
    expected_digest = digest(evidence["snapshot"])
    ballots = evidence["ballots"]
    voters = [ballot["principal"] for ballot in ballots]
    unknown = sorted(set(voters) - set(principals))
    if unknown:
        raise Refused(f"ballots cast by principals absent from the evidence: {unknown}")
    if len(set(voters)) != len(voters):
        raise Refused(f"a principal cast more than one ballot: {sorted(voters)}")
    for ballot in ballots:
        if ballot["snapshot_digest"] != expected_digest:
            raise Refused(
                f"ballot by {ballot['principal']} is bound to {ballot['snapshot_digest']} "
                f"but the snapshot digests to {expected_digest}. Independent decisions "
                "about different snapshots are a coincidence, not a quorum"
            )
    approvals = [b for b in ballots if b["decision"] == "APPROVE"]
    if len(approvals) < 2:
        results["INDEPENDENT_DECISIONS"] = (
            False,
            f"{len(approvals)} approving ballot(s) from distinct principals; two are the minimum",
        )
    else:
        results["INDEPENDENT_DECISIONS"] = (
            True, f"{len(approvals)} distinct principals approved the same snapshot digest")

    # 6. EFFECT_ROLE_SEPARATION.
    roles = evidence.get("roles") or {}
    executor = roles.get("executor")
    readback = roles.get("readback_verifier")
    if not executor or not readback:
        results["EFFECT_ROLE_SEPARATION"] = (
            False, "roles.executor and roles.readback_verifier are not both declared")
    else:
        missing = sorted({executor, readback} - set(principals))
        if missing:
            raise Refused(f"roles name principals absent from the evidence: {missing}")
        if executor in voters:
            raise Refused(
                f"the executor {executor!r} also cast a ballot. An executor that votes on "
                "its own effect provides no separation"
            )
        if executor == readback:
            raise Refused(
                f"the executor {executor!r} is also the readback verifier. Verifying your "
                "own landing is the failure Typed Multi-Path Readback exists to prevent"
            )
        results["EFFECT_ROLE_SEPARATION"] = (
            True, f"executor {executor}, readback {readback}, neither a voter nor each other")

    # 7. REVOCATION_BEHAVIOUR_OBSERVED.
    not_denied = []
    for role, principal in sorted(principals.items()):
        revocation = principal["revocation"]
        if revocation["reuse_result"] == "ACCEPTED":
            raise Refused(
                f"{role}: reuse after revocation was ACCEPTED. Revocation that does not "
                "deny reuse is a log entry"
            )
        if revocation["reuse_result"] != "DENIED":
            not_denied.append(role)
            continue
        revoked = parse_time(f"{role}.revoked_at", revocation["revoked_at"])
        attempted = parse_time(f"{role}.reuse_attempted_at", revocation["reuse_attempted_at"])
        if attempted <= revoked:
            raise Refused(
                f"{role}: reuse was attempted at or before revocation, so DENIED shows "
                "nothing about revocation"
            )
    if not_denied:
        results["REVOCATION_BEHAVIOUR_OBSERVED"] = (
            False, f"reuse-after-revocation not attempted for: {not_denied}")
    else:
        results["REVOCATION_BEHAVIOUR_OBSERVED"] = (
            True, "every principal's reuse after revocation was observed DENIED")

    # 8. SIGNER_VERIFIED -- signatures verified above; this is about key PROVENANCE.
    jwks = evidence["jwks"]
    if jwks["provenance"] == "ISSUER_DISCOVERY":
        discovery = jwks.get("discovery")
        if not discovery:
            raise Refused(
                "jwks.provenance is ISSUER_DISCOVERY with no discovery record. An "
                "undocumented fetch is indistinguishable from a key the repository chose"
            )
        if jwks["issuer"] != GITHUB_ISSUER:
            results["SIGNER_VERIFIED"] = (
                False, f"issuer {jwks['issuer']!r} is not {GITHUB_ISSUER!r}")
        elif not discovery["url"].startswith(GITHUB_ISSUER):
            raise Refused(
                f"discovery url {discovery['url']!r} is not under the declared issuer "
                f"{GITHUB_ISSUER!r}"
            )
        elif discovery["response_digest"] != digest(jwks["keys"]):
            raise Refused(
                f"discovery response_digest {discovery['response_digest']} does not digest "
                f"the key set it accompanies ({digest(jwks['keys'])}). A record describing "
                "other bytes than the keys in hand describes a different fetch"
            )
        elif not expected_jwks_digest:
            # The hole this closes: every field of a discovery record is writable by
            # whoever writes the document, so a fixture could fabricate a fetch it never
            # made and walk itself to AIS4. The fetch must therefore be confirmed
            # OUT OF BAND -- by the job that actually performed it -- exactly as the shadow
            # queue confirms a receipt against a digest passed through `needs` rather than
            # through the artifact. DOCUMENT_SAYS_FETCHED != FETCH_INDEPENDENTLY_CONFIRMED.
            results["SIGNER_VERIFIED"] = (
                False,
                "discovery record is self-reported and EXPECT_JWKS_DIGEST was not supplied "
                "out of band; a document cannot confirm its own fetch",
            )
        elif expected_jwks_digest != discovery["response_digest"]:
            raise Refused(
                f"out-of-band jwks digest {expected_jwks_digest} does not match the "
                f"document's {discovery['response_digest']}"
            )
        else:
            results["SIGNER_VERIFIED"] = (
                True,
                f"keys fetched from {discovery['url']} at {discovery['fetched_at']}, "
                f"response {discovery['response_digest']} confirmed out of band",
            )
    else:
        results["SIGNER_VERIFIED"] = (
            False,
            "jwks.provenance is LOCAL_FIXTURE: the signatures verify against a key set the "
            "repository supplied, which proves internal consistency and not an issuer. "
            "SIGNATURE_VERIFIES != ISSUER_ESTABLISHED",
        )

    attestation = evidence.get("attestation")
    if attestation and attestation["signer_verified"] and not attestation.get("verified_by"):
        raise Refused(
            "attestation declares signer_verified with no verified_by. Generation has no "
            "security value until signature, timestamp and signer are independently checked"
        )

    return results


def observed_level(results: dict[str, tuple[bool, str]]) -> str:
    """Highest rung whose evidence is present. Never rounds up."""
    if not results["OIDC_BOUND"][0]:
        return LADDER[0]
    level = "AIS1_WORKFLOW_BOUND"
    if not results["DISTINCT_PLATFORM_PRINCIPALS"][0]:
        return level
    level = "AIS2_PLATFORM_PRINCIPALS"
    if not results["DISTINCT_CUSTODY_DOMAINS"][0]:
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
        results = evaluate(
            evidence,
            env.get("EXPECT_MAIN_SHA", "").strip(),
            env.get("EXPECT_JWKS_DIGEST", "").strip(),
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
    reached = level == "AIS4_INDEPENDENT_DOMAINS"
    print(json.dumps({
        "schema": "secb.ais-production-observation/v1",
        "OBSERVED_LEVEL": level,
        "PRODUCTION_AIS_LEVEL": level if reached else "NOT_OBSERVED",
        "conjuncts": {name: {
            "observed": results[name][0],
            "note": results[name][1],
        } for name in CONJUNCTS},
        "unsatisfied": [name for name in CONJUNCTS if not results[name][0]],
        "tranche_b": "EXTERNAL_AUTHORITY_REQUIRED -- no input to this tool can mark it complete",
        "not_proven": [
            "that a verifier reaching AIS4 on some document means this repository has one",
            "that a verifying signature establishes an issuer; that is jwks.provenance",
            "that a discovery record proves a fetch happened; only the out-of-band "
            "EXPECT_JWKS_DIGEST, supplied by the job that fetched, can confirm that",
            "that RS256 verification here covers certificate chains or key revocation",
            "that conformance to the schema is sufficient; the conjuncts are evidenced",
        ],
        "confers_merge_authority": False,
    }, indent=2, sort_keys=True))
    return OK


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
