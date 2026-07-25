# DOX contract - a0_pen_paper/docs

## Purpose

Capabilities, roadmap, component boundaries, workflow docs, and durable design
notes.

## Ownership

- Stable product documentation belongs here.
- Do not store runtime sessions, generated diagrams, or temporary package audit
  notes here unless explicitly promoted.

## Local Contracts

- `COMPONENT_BOUNDARIES.md` must stay aligned with plugin cooperation changes.
- Workflow docs should distinguish shipped behavior from deferred contract work.
- `dev-tracker.html` is the running development log and **must be updated in
  the same change that lands durable work** — features, fixes, schema changes,
  and decisions. It records what changed, why, and what was deliberately left
  undone. It is listed in `.gitignore` as an internal file: maintain it in the
  working copy, and do not publish it without the owner's explicit say-so.

## Work Guidance

- Keep future Workflows UI to Scribe Publish Contract work separate from base
  State-DOX storage unless explicitly requested.

## Verification

- Verify referenced files and docs index entries exist.
- Verify `dev-tracker.html` carries an entry for the change being made.

## Child DOX Index

No child AGENTS.md files yet.
