# DOX contract - a0_pen_paper/tests

## Purpose

Tests for session state, workflow publish, and storage integration behavior.

## Ownership

- Tests should protect durable storage contracts and integration boundaries.

## Local Contracts

- Add focused tests for State-DOX template, publish, focus, or session storage
  changes.

## Work Guidance

- Prefer temporary runtime directories over live `usr/pen_and_paper/` state.

## Verification

- Run `python -m unittest tests.test_session_state tests.test_workflows_publish -v`.

## Child DOX Index

No child AGENTS.md files yet.
