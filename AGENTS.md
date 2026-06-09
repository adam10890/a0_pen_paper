# DOX contract — a0_pen_paper-repo

## Purpose

Standalone source package for the Agent Zero Pen & Paper plugin. The plugin
provides structured working-memory sessions, workflow templates, optional wiki
template integration, and archive-oriented task notes.

## Ownership

- This folder is plugin source, not live runtime state.
- Runtime sessions belong outside the plugin directory, under the configured
  Agent Zero `usr/pen_and_paper/` location.
- Package archives in `plugin_dev_zip_files/` are distribution artifacts; this
  repo is the preferred source when both exist.

## Local Contracts

- Keep the plugin installable under `/a0/usr/plugins/a0_pen_paper/`.
- Keep tool behavior, prompt guidance, skills, and docs aligned when changing
  workflows.
- Avoid storing session archives, vector caches, or generated runtime state in
  the plugin source.
- Preserve graceful fallback when optional vector or `llm_wiki` integration is
  unavailable.
- Keep generated diagram artifacts under runtime storage
  `usr/pen_and_paper/diagrams/` or a session's `diagrams/` folder, never in
  plugin source.

## Work Guidance

- Main tool code lives in `tools/`.
- Workflow/session persistence helpers live in `helpers/`.
- Diagram XML generation helpers live in `helpers/`; Agent-facing diagram
  actions live in `tools/`.
- Pen & Paper State-DOX templates live under
  `data/workflow_state_templates/` (shipped built-ins); live per-session copies
  belong under the active workspace's runtime `state/` folder.
- UI-published State-DOX templates are runtime data and live under
  `usr/pen_and_paper/knowledge/workflows/state_dox/` (never in plugin source).
  `workflows_store.publish_state_dox()` writes them; `sessions_store`
  (`workflow_template_dirs` / `list_state_dox_templates` / `ensure_state_files`)
  merges shipped + runtime with shipped winning on id clash. Reserved built-in
  ids cannot be published. Scribe reads via `list_state_dox_templates()`.
  Custom `activation_tags` are valid, but Scribe only applies them when an
  observation emits explicit evidence (`SCRIBE_TAGS:` / `STATE_DOX_TAGS:`) or an
  exact keyword in non-read-only activity.
- `list_state_dox_templates()` accepts both canonical nested YAML
  (`workflow.activation_tags`, `scribe.skill`) and flat runtime YAML
  (`name`, `activation_tags`, `skill`) so agent-authored template files do not
  silently lose custom triggers.
- Each State-DOX workflow template must declare `scribe.skill` pointing to the
  matching `a0_scribe/skills/scribe-workflow-*` capability.
- `tool_execute_after` focus tracking must read tool metadata from
  `agent.loop_data.current_tool.args` when `tool_args` is absent; Agent Zero
  core does not reliably pass `tool_args` into after-tool extensions.
- When adding plugin cooperation, mark whether the component is `local` or
  `bridge` in `docs/COMPONENT_BOUNDARIES.md`.
- User-facing workflow docs live in `docs/pen-paper-workflows/`.
- Agent-facing skills live in `skills/`.
- Web/API surfaces should remain thin wrappers over helper logic.

## Verification

- Run `python -m py_compile` on touched Python files.
- Run `python -m unittest tests.test_session_state -v` when changing session
  state helpers or workflow state templates.
- Run `scripts/verify_pen_paper_setup.py` when layout or install assumptions
  change.
- Check `README.md` and `docs/CAPABILITIES_AND_ROADMAP.md` when changing
  durable behavior.

## Child DOX Index

- `helpers/AGENTS.md` — sessions, workflows, State-DOX storage, diagrams, and
  execution helpers.
- `tools/AGENTS.md` — agent-facing Pen & Paper tools.
- `api/AGENTS.md` — web/API wrappers for sessions, workflows, publish, and
  diagrams.
- `webui/AGENTS.md` — Workflows Canvas and plugin UI surfaces.
- `skills/AGENTS.md` — agent-facing Pen & Paper skills and references.
- `docs/AGENTS.md` — capabilities, roadmap, component boundaries, and workflow
  docs.
- `data/AGENTS.md` — shipped templates, workflow registries, and State-DOX
  template fixtures.
- `prompts/AGENTS.md` — tool prompt guidance.
- `extensions/AGENTS.md` — Agent Zero hooks and Right Canvas registration.
- `tests/AGENTS.md` — session state and workflow publish tests.
- `scripts/AGENTS.md` — setup and verification scripts.
