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
- When adding plugin cooperation, document whether the component is `local` or
  `bridge` in the nearest durable docs file.
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
- `api/AGENTS.md` — web/API wrappers for sessions, workflows, and diagrams.
- `webui/AGENTS.md` — Workflows Canvas and plugin UI surfaces.
- `skills/AGENTS.md` — agent-facing Pen & Paper skills and references.
- `docs/AGENTS.md` — capabilities, roadmap, component boundaries, and workflow
  docs.
- `data/AGENTS.md` — shipped templates, workflow registries, and State-DOX
  template fixtures.
- `prompts/AGENTS.md` — tool prompt guidance.
- `extensions/AGENTS.md` — Agent Zero hooks and Right Canvas registration.
- `scripts/AGENTS.md` — setup and verification scripts.
