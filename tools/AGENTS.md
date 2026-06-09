# DOX contract - a0_pen_paper-repo/tools

## Purpose

Agent-facing tools for Pen & Paper sessions, wiki templates, and diagrams.

## Ownership

- Tool files own agent request parsing and response shape.
- Persistent behavior should route through helpers.

## Local Contracts

- Keep allowed section names aligned with session storage and UI.
- Tool prompt names must match exposed tool names.

## Work Guidance

- Update prompt guidance and tests when tool arguments or behavior changes.

## Verification

- Run `python -m py_compile` on touched tool files.
- Run focused session/workflow tests for storage-affecting behavior.

## Child DOX Index

No child AGENTS.md files yet.
