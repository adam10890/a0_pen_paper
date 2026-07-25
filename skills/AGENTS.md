# DOX contract - a0_pen_paper/skills

## Purpose

Agent-facing Pen & Paper workflow guidance and references.

## Ownership

- Skill frontmatter and references define agent usage contracts.
- Skills should align with tools, templates, and README behavior.

## Local Contracts

- Do not document unavailable tool actions as current behavior.
- Keep workflow template guidance aligned with runtime template schema.
- **Two skills, disjoint roles — keep it that way.** `pen-and-paper` (priority 1)
  is WHAT/WHY: philosophy, when to use, lifecycle. `pen-and-paper-workflow`
  (priority 2) is HOW: deterministic execution plus template authoring. Do not
  add a third skill that overlaps either, and do not reintroduce identity
  triggers ("pen and paper", "structured thinking") into the HOW skill — the
  overlap is what made activation non-deterministic before.
- Skills are the home for methodology moved out of tool code. Content belongs
  here or in `data/templates/`, never re-embedded in `tools/`.
- Skills are **not** guaranteed to load — they depend on trigger matching. Any
  rule that must hold on every model belongs in `prompts/` instead; the skill
  then elaborates it. Never make a skill the *only* home for a correctness rule.

## Work Guidance

- Update skill references when template registry or workflow publish behavior
  changes.
- If you change the section vocabulary or execution contract, update
  `prompts/agent.system.tool.pen_paper.md` and
  `data/config/rules.yaml::execution_contract` in the same commit.

## Verification

- Inspect skill frontmatter and referenced files after edits.
- Confirm every `references/*.md` linked from a SKILL.md or from
  `data/templates/_index.md` actually exists (dangling links strand small models).
- `scripts/verify_pen_paper_setup.py` asserts the exact set of skill directories;
  adding or removing one requires updating that check.

> Context: the always-injected counterpart to these skills is `prompts/` — see
> `prompts/AGENTS.md`. Tool-side invariants — see `tools/AGENTS.md`.

## Child DOX Index

No child AGENTS.md files yet.
