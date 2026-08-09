# Skill Router Failure-Injection Tests FIT-101–120

Status: Specification coverage complete; runtime certification pending.

| FIT | Required behavior |
|---|---|
| 101 | Named qualified skill prioritized without bypassing authority |
| 102 | Unavailable/revoked named skill fails safely |
| 103 | Frozen inputs reproduce the same route |
| 104 | Redundant skill excluded |
| 105 | Missing mandatory capability blocks execution |
| 106 | Prerequisite DAG and typed handoffs resolve correctly |
| 107 | Cyclic/incompatible prerequisites fail closed |
| 108 | Changed instruction digest invalidates route |
| 109 | Risk-ceiling violation blocks invocation |
| 110 | Selection cannot authorize an effect |
| 111 | High-impact effects require separate authorization |
| 112 | Untrusted output cannot become privileged instruction |
| 113 | Missing mandatory instruction resource blocks action |
| 114 | Handoff schema/provenance mismatch blocks consumer |
| 115 | Validation failure triggers bounded repair without weaker acceptance |
| 116 | Unknown external outcome reconciled before retry/fallback |
| 117 | Fallback preserves all control floors |
| 118 | Budget exhaustion holds new work but permits authorized containment |
| 119 | Evidence reconstructs route and outcome |
| 120 | Outcome learning cannot self-admit skills or alter governance |

Each execution record must include test version, frozen fixtures, runtime/build identity, policy and registry hashes, commands, outputs, timestamps, evidence digests, independent reviewer, result and linked defect/closure. Continuous identifiers FIT-001–120 must be unique with no gaps.
