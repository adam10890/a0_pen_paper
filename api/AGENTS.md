# DOX contract - a0_pen_paper/api

## Purpose

HTTP/API wrappers for sessions, workflow templates, publish operations, and
diagram/whiteboard bridges.

## Ownership

- API files should stay thin wrappers over helper logic.
- They own request validation and response envelopes.

## Local Contracts

- Keep route names aligned with Workflows Canvas callers.
- Publish APIs write runtime templates only; shipped template files remain
  source-controlled fixtures.

## Work Guidance

- Return explicit stale/conflict errors instead of silently overwriting session
  or template data.

## Verification

- Run `python -m py_compile` on touched API files.
- Run workflow publish/session tests when publish or session endpoints change.

## Child DOX Index

No child AGENTS.md files yet.
