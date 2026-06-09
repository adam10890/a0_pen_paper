# DOX contract - a0_pen_paper/webui

## Purpose

Workflows Canvas and plugin UI surfaces for template editing, live sessions,
diagram generation, and publish flows.

## Ownership

- UI owns interaction state and display text.
- Helpers/API own persistence and business rules.

## Local Contracts

- Keep API route calls aligned with `api/`.
- Do not store runtime sessions or generated diagrams as static UI assets.

## Work Guidance

- Preserve stale-session handling and explicit user confirmation for destructive
  switches/deletes.

## Verification

- Inspect changed HTML/JS wiring and route names.

## Child DOX Index

No child AGENTS.md files yet.
