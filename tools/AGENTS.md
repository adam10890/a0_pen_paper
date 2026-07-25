# DOX contract - a0_pen_paper/tools

## Purpose

Agent-facing tools for Pen & Paper sessions, wiki templates, and diagrams.

## Ownership

- Tool files own agent request parsing and response shape.
- Persistent behavior should route through helpers.

## Local Contracts

- Keep allowed section names aligned with session storage and UI.
- Tool prompt names must match exposed tool names.
- **Knowledge/hands separation (do not regress).** Tool code is "hands": argument
  parsing, orchestration, response shape. Methodology is "knowledge" and lives in
  `skills/` + `data/templates/` + `data/config/rules.yaml`. Do **not** re-embed
  onboarding text, core rules, formatting conventions, or per-section prose into
  tool code — return a short pointer to `data/templates/_start_here.md` instead.
  `_get_quick_start_message()` is deliberately ~5 lines; keep it that way.
- Data the tool needs at runtime (section hints, summary headings) is loaded from
  `data/config/rules.yaml` (`_load_rules` / `_section_hints`), not hardcoded.
- Disk I/O routes through `helpers/sessions_store.py` (sessions) and
  `helpers/workflows_store.py` (templates). Do not add new inline
  `files.write_file` calls for session or template state.
- Policy checks (`WorkflowExecutor.pre_update`, execution-log validation,
  idempotency) stay in the tool; the stores remain dumb writers.
- `VALID_SECTIONS` stays a literal list in `tools/pen_paper.py` —
  `scripts/verify_pen_paper_setup.py` greps the file text for `execution_log`.
  Do not replace it with an import.

## Work Guidance

- Update prompt guidance and tests when tool arguments or behavior changes.
- The deterministic sequence and section vocabulary must stay in sync across three
  places: `prompts/agent.system.tool.pen_paper.md` (always injected — the only one
  every model sees), `skills/pen-and-paper-workflow/SKILL.md`, and
  `data/config/rules.yaml::execution_contract`. Change one, check the other two.

> Context: methodology lives in `skills/` — see `skills/AGENTS.md`. Runtime
> prompt-injection contract — see `prompts/AGENTS.md`.

## Verification

- Run `python -m py_compile` on touched tool files.
- Run focused session/workflow tests for storage-affecting behavior.

## Child DOX Index

No child AGENTS.md files yet.
