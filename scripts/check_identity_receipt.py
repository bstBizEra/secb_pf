#!/usr/bin/env python3
"""Compute an AIS level from identity evidence, offline. Fail-closed.

`SECB-WP-FWK-081` (issue #145).

    ROLE_LABEL ≠ PLATFORM_PRINCIPAL ≠ CREDENTIAL_CUSTODY_DOMAIN ≠ DECISION_INDEPENDENCE

`#144` refuses public disclosure while the substrate is below `AIS4`. That refusal is only
useful if the level can be **computed from evidence** rather than declared, which is what
this does — for a **sandbox**, with three hard limits stated up front:

* **It creates nothing.** No GitHub App, installation, secret, token or permission.
* **It cannot observe production.** `PRODUCTION_AIS_LEVEL: NOT_OBSERVED` is printed on
  every run, including successful ones. A fixture demonstrates the *shape* of evidence.
* **It cannot compute `AIS4`.** Independent failure domains are not exhibited by one
  simulated environment, so the ceiling is `AIS3` and a registry asking for more is refused.
  Otherwise a fixture would advance the gate that exists to wait for real identities.

What each rung requires, and the research constraint behind it:

`AIS1_WORKFLOW_BOUND`
    OIDC claims present, and `workflow_ref` **bound to `workflow_sha`** — a ref names a
    path, a sha pins its content. Under a reusable workflow the executing definition is not
    the entry workflow, so `job_workflow_ref` obliges `job_workflow_sha`. OIDC proves a
    *workflow execution context*, never that an independent agent exists.

`AIS2_PLATFORM_PRINCIPALS`
    Distinct `(app_id, installation_id)` per role. `actor_id` is **prohibited** as a
    principal: it is the account that started the workflow, not the agent holding the role.

`AIS3_CUSTODY_SEPARATED`
    Distinct custody **and** policy domains, plus token scope that is actually least
    privilege — an hour ceiling means nothing if the token covers every repository with
    broad permissions. Revocation counts only when reuse was **denied**; an HTTP `204`
    says a call was accepted, not that the token stopped working.

Contract:

    REGISTRY   registry path (default config/agent_identity_registry.schema.json's subject)
    FIXTURE_KEY  shared secret for the fixture HMAC

Exit codes:

    0  a level was computed and printed
    2  refused — malformed registry, prohibited evidence, or a level claim it cannot support
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
from pathlib import Path

OK = 0
FAIL = 2

LADDER = [
    "AIS0_SELF_ASSERTED",
    "AIS1_WORKFLOW_BOUND",
    "AIS2_PLATFORM_PRINCIPALS",
    "AIS3_CUSTODY_SEPARATED",
    "AIS4_INDEPENDENT_DOMAINS",
]

SANDBOX_CEILING = "AIS3_CUSTODY_SEPARATED"

REQUIRED_CLAIMS = ("repository_id", "run_id", "workflow_ref", "workflow_sha")


class Refused(ValueError):
    """The evidence does not support the level being computed."""


def canonical(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign(payload: dict, key: str) -> str:
    return hmac.new(key.encode("utf-8"), canonical(payload), hashlib.sha256).hexdigest()


def verify_signature(registry: dict, key: str) -> None:
    """Prove the fixture was not edited. This is not issuer verification.

    Real OIDC is asymmetric and checked against a published JWKS. A shared secret cannot
    distinguish an issuer from anyone else holding the secret, which is why the registry
    must declare `not_oidc: true` and why this cannot lift the level past the ceiling.
    """
    signature = registry.get("signature", {})
    if signature.get("algorithm") != "HMAC_SHA256_FIXTURE" or not signature.get("not_oidc"):
        raise Refused(
            "registry must declare algorithm HMAC_SHA256_FIXTURE and not_oidc true; a "
            "fixture signature must not be presented as OIDC verification"
        )
    provided = signature.get("value", "")
    body = {k: v for k, v in registry.items() if k != "signature"}
    if not provided or not hmac.compare_digest(provided, sign(body, key)):
        raise Refused("fixture signature is absent or does not match the registry body")


def check_workflow_binding(role: str, claims: dict) -> None:
    missing = [c for c in REQUIRED_CLAIMS if not claims.get(c)]
    if missing:
        raise Refused(
            f"{role}: OIDC claims missing {missing}. workflow_ref names a path and "
            "workflow_sha pins its content; a ref alone binds a moveable target"
        )
    if claims.get("job_workflow_ref") and not claims.get("job_workflow_sha"):
        raise Refused(
            f"{role}: job_workflow_ref is present without job_workflow_sha. Under a "
            "reusable workflow the executing definition is not the entry workflow"
        )
    if claims.get("actor_id"):
        raise Refused(
            f"{role}: actor_id is present and is prohibited as principal evidence. It is "
            "the account that started the workflow, not the agent holding the role"
        )


def check_least_privilege(role: str, scope: dict) -> None:
    if scope.get("expires_in_seconds", 10 ** 9) > 3600:
        raise Refused(f"{role}: token lifetime exceeds one hour")
    repositories = scope.get("repositories") or []
    permissions = scope.get("permissions") or {}
    if not repositories or not permissions:
        raise Refused(
            f"{role}: token scope must name repositories and permissions at issuance. A "
            "one-hour ceiling is not least privilege if the token covers everything for "
            "that hour"
        )
    if "*" in repositories:
        raise Refused(f"{role}: token scoped to all repositories is not least privilege")


def check_revocation(role: str, revocation: dict | None) -> None:
    if revocation is None:
        return
    reuse = revocation.get("reuse_after_revoke")
    if reuse != "DENIED":
        raise Refused(
            f"{role}: revocation records reuse_after_revoke={reuse!r}. Only DENIED is "
            "evidence -- an HTTP 204 says a call was accepted, not that the token stopped "
            "working. Revocation is a behavioural claim"
        )


def compute_level(registry: dict) -> str:
    sandbox = registry.get("sandbox", {})
    if sandbox.get("is_sandbox") is not True:
        raise Refused("registry does not declare is_sandbox: true; this tool reads sandboxes")
    if sandbox.get("production_ais_level") != "NOT_OBSERVED":
        raise Refused(
            f"production_ais_level is {sandbox.get('production_ais_level')!r}; a sandbox "
            "cannot observe production, and a fixture must never advance it"
        )
    ceiling = sandbox.get("max_computable_level", SANDBOX_CEILING)
    if ceiling != SANDBOX_CEILING:
        raise Refused(
            f"max_computable_level {ceiling!r} exceeds the sandbox ceiling "
            f"{SANDBOX_CEILING}. AIS4 needs independent failure domains, which one "
            "simulated environment does not exhibit"
        )

    principals = registry.get("principals") or {}
    if len(principals) < 2:
        raise Refused("a substrate with fewer than two principals separates nothing")

    for role, principal in principals.items():
        check_workflow_binding(role, principal.get("oidc_claims") or {})
    level = "AIS1_WORKFLOW_BOUND"

    identities = {}
    for role, principal in principals.items():
        key = (principal.get("app_id"), principal.get("installation_id"))
        if not all(key):
            raise Refused(f"{role}: app_id and installation_id are both required")
        identities.setdefault(key, []).append(role)
    shared = {str(k): v for k, v in identities.items() if len(v) > 1}
    if shared:
        return level  # distinct claims, one principal: stops at AIS1
    level = "AIS2_PLATFORM_PRINCIPALS"

    custody = {p.get("custody_domain") for p in principals.values()}
    policy = {p.get("policy_domain") for p in principals.values()}
    if len(custody) < len(principals) or len(policy) < len(principals):
        return level  # separate principals, shared broker or policy: stops at AIS2

    for role, principal in principals.items():
        check_least_privilege(role, principal.get("token_scope") or {})
        check_revocation(role, principal.get("revocation"))
    return "AIS3_CUSTODY_SEPARATED"


def main(argv: list[str]) -> int:
    env = dict(os.environ)
    path = env.get("REGISTRY", "").strip()
    if not path:
        print("REFUSED (closed): REGISTRY is required", file=sys.stderr)
        return FAIL
    try:
        registry = json.loads(Path(path).read_text(encoding="utf-8"))
        verify_signature(registry, env.get("FIXTURE_KEY", ""))
        level = compute_level(registry)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"REFUSED (closed): registry unreadable or unparseable ({exc})", file=sys.stderr)
        return FAIL
    except Refused as exc:
        print(f"REFUSED (closed): {exc}", file=sys.stderr)
        return FAIL
    except (KeyError, TypeError, AttributeError) as exc:
        print(f"REFUSED (closed): malformed registry ({exc})", file=sys.stderr)
        return FAIL

    print(json.dumps({
        "schema": "secb.identity-substrate-observation/v1",
        "SANDBOX_AIS_LEVEL": level,
        "PRODUCTION_AIS_LEVEL": "NOT_OBSERVED",
        "sandbox_ceiling": SANDBOX_CEILING,
        "not_proven": [
            "that any production principal exists",
            "that OIDC proves an independent agent -- it proves a workflow execution context",
            "that this HMAC verifies an issuer; real OIDC is asymmetric against a JWKS",
            f"any level above {SANDBOX_CEILING}, including the AIS4 that #144 requires",
        ],
    }, indent=2, sort_keys=True))
    return OK


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
