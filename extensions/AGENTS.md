# DOX contract - a0_pen_paper-repo/extensions

## Purpose

Agent Zero hooks for prompt injection, workflow guards, focus tracking, and
Right Canvas registration.

## Ownership

- Extensions integrate plugin behavior with Agent Zero lifecycle and UI hooks.
- Helpers own persistence/business logic.

## Local Contracts

- Focus tracking must read `agent.loop_data.current_tool.args` when `tool_args`
  is absent.
- Hooks should fail softly and not break the ego loop.

## Work Guidance

- Keep hook logic narrow and route durable behavior through helpers.

## Verification

- Run `python -m py_compile` on touched Python extension files.
- Run session state tests for focus-tracking behavior changes.

## Child DOX Index

No child AGENTS.md files yet.
