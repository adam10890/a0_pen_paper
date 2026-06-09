# DOX contract - a0_pen_paper/helpers

## Purpose

Session persistence, workflow registry/state helpers, diagram generation, and
workflow execution support.

## Ownership

- `sessions_store.py` owns live session files, focus, State-DOX runtime files,
  event append, and template copy/merge behavior.
- `workflows_store.py` owns workflow template registry and UI-published
  State-DOX template persistence.
- Diagram helpers own deterministic draw.io/whiteboard shape generation.

## Local Contracts

- Runtime sessions and UI-published State-DOX templates live under configured
  `usr/pen_and_paper/`, never plugin source.
- Shipped State-DOX templates live under `data/workflow_state_templates/`.
- Scribe reads State-DOX templates via helper APIs; do not bypass storage
  helpers.

## Work Guidance

- Keep API and tool files thin over helper behavior.
- Preserve shipped-template precedence and reserved built-in workflow ids.

## Verification

- Run `python -m unittest tests.test_session_state tests.test_workflows_publish -v`
  when changing State-DOX/session workflow behavior.
- Run `python -m py_compile` on touched helper files.

## Child DOX Index

No child AGENTS.md files yet.
