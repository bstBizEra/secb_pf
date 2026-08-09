# Evidence Package Schema

Status: Implementation Ready
Version: 1.0.0
Schema ID: `secb.evidence.engineering-episode/1.0`
Work Package: `SECB-WP-ENGLOOP-001`

## Required Envelope

```json
{
  "schema_id": "secb.evidence.engineering-episode/1.0",
  "episode_id": "EP-...",
  "work_package_id": "SECB-WP-...",
  "objective": "...",
  "risk_tier": "R0|R1|R2|R3|R4",
  "state_transition": {"from": "...", "to": "..."},
  "actors": [{"actor_id": "...", "role": "...", "identity_type": "human|agent|service"}],
  "authority": {"source_ref": "...", "scope_hash": "sha256:...", "expires_at": "..."},
  "context": {"repository_sha": "...", "policy_version": "...", "skill_versions": [], "tool_versions": []},
  "requirements": [{"requirement_id": "...", "acceptance_criteria": [], "evidence_refs": []}],
  "execution": {"plan_ref": "...", "budget": {}, "leases": [], "checkpoints": [], "side_effects": []},
  "verification": {"tests": [], "scans": [], "reviews": [], "gate_decisions": []},
  "outcome": {"status": "...", "change_refs": [], "residual_risks": [], "rollback_ref": "..."},
  "learning_handoff": {"observations": [], "hypotheses": [], "anti_patterns": []},
  "artifacts": [{"artifact_id": "...", "uri": "...", "sha256": "...", "created_at": "...", "producer": "..."}],
  "manifest_sha256": "sha256:...",
  "sealed_at": "..."
}
```

## Integrity Rules

- Canonical serialization is UTF-8 with stable field ordering before hashing.
- Every material artifact has SHA-256, producer identity, timestamp, source command or decision, and data-class label.
- Logs and outputs are redacted before persistence; secret values, access tokens, and unnecessary personal data are prohibited.
- Evidence is append-only after sealing. Corrections create a new version that references and supersedes the prior manifest.
- Gate decisions include policy version, evaluator, input hashes, outcome, conditions, expiry, and exception reference where applicable.
- External evidence is copied or referenced through an approved immutable/checksum-verifiable store; mutable links alone are insufficient.

## Traceability

Each acceptance criterion links to one or more test, review, or decision artifacts. Each change links to its requirement and applicable ADR. Each release links to merge SHA, build provenance, deployment ID, verification, and rollback plan.

## Validation

The Evidence Gate fails if any required field is missing, a hash mismatch exists, authority or approval is expired, the artifact producer is unattributable, a blocking test/scan is absent, traceability is broken, redaction fails, or the manifest cannot be reproduced.

