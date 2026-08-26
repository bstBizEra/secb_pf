# SecB PF / BADF — Claude repository adapter

Claude Code loads this file automatically. The normative operating contract is **`AGENTS.md`**; this file MUST NOT duplicate it.

@AGENTS.md

## Mandatory read set before material work

1. `AGENTS.md`
2. `docs/00-governance/FRAMEWORK_PRODUCT_DEFINITION.md`
3. applicable documents under `docs/00-governance/`
4. `docs/06-agent-orchestration/ENGINEER_LOOP.md` and `LEARN_LOOP.md`
5. applicable ADRs under `docs/12-decisions/`
6. applicable evidence/runbook contracts under `docs/13-evidence/` and `docs/15-runbooks/`

## Adapter rules

- Do not treat this file as an authority source.
- Do not infer permission from a successful tool call.
- Run the repository's authority classification before material mutations.
- Preserve exact source/head/tree identity when producing evidence.
- A council result is review evidence, not approval, unless an effective mandate explicitly says otherwise.
- If `AGENTS.md` conflicts with this adapter, `AGENTS.md` wins and the conflict is a stop condition.
