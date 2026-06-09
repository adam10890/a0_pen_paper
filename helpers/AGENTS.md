# DOX contract - a0_pen_paper-repo/helpers

## Purpose

Session persistence, workflow registry/state helpers, diagram generation, and
workflow execution support.

## Ownership

- Session helpers own live session files, focus, State-DOX runtime files, event
  append, and template copy/merge behavior.
- Workflow helpers own workflow template registry and runtime-published
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

- Run session/workflow tests for State-DOX or storage changes.
- Run `python -m py_compile` on touched helper files.

## Child DOX Index

No child AGENTS.md files yet.
