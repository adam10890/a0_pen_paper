# DOX contract - a0_pen_paper/prompts

## Purpose

Agent prompt guidance for Pen & Paper tools.

## Ownership

- Prompt filenames must match exposed tool names.
- Prompts describe agent usage; helpers/tools own behavior.

## Local Contracts

- Keep tool arguments and examples aligned with implemented actions.
- **This directory is the only guidance every model sees.** Files here are
  injected into the system prompt unconditionally. `skills/` load only when the
  model notices a trigger, and `data/templates/` load only when the model chooses
  to read them — neither is guaranteed. Therefore any rule that must hold
  *regardless of model capability* belongs here, stated imperatively.
- Cross-model determinism minimum for `agent.system.tool.pen_paper.md`: the full
  seven-name section vocabulary, the required call sequence, the step-status
  vocabulary (`pending|running|done|failed|skipped`, never `COMPLETED`), and the
  "never invent a section name" rule. Do not thin these out to save tokens.
- Keep prompts prescriptive and short. Explanation, rationale, and lifecycle
  detail belong in `skills/` and `data/templates/`, reached by pointer.

## Work Guidance

- Update prompts whenever tool names, actions, or result shape changes.
- When the section list or the execution contract changes, update all three
  in the same commit: this prompt, `skills/pen-and-paper-workflow/SKILL.md`, and
  `data/config/rules.yaml::execution_contract`.

## Verification

- Confirm prompt/tool name alignment.
- Confirm the section list here matches `VALID_SECTIONS` in
  `tools/pen_paper.py` exactly — a section the tool accepts but the prompt omits
  is invisible to any model that never loads the skill.

> Context: the deterministic sequence is elaborated in
> `skills/pen-and-paper-workflow/SKILL.md`; the machine-readable form is
> `data/config/rules.yaml::execution_contract`.

## Child DOX Index

No child AGENTS.md files yet.
