# Pen & Paper — Index

This is the catalog of every reference, template, and config page available in this plugin. Use it to pick the **minimum** set of pages you need for the current task. Do not read everything.

Each entry: `path — one-line summary — when to read`.

## Quick lookup — what are you doing?

| Situation | Read |
|---|---|
| Starting a brand-new session | `data/templates/session.md` (template) |
| Confused about rules / first time | `_start_here.md` (sibling) |
| Seeing an unfamiliar name for P&P (e.g. `P&P`, `pen_paper`, `עט ונייר`) | `_aliases.md` (sibling) |
| Need the full methodology | `skills/pen-and-paper/SKILL.md` |
| Session approaching 250 lines | `skills/pen-and-paper/references/session-management.md` (cleanup) |
| Need to split a session | `skills/pen-and-paper/references/session-management.md` (split) |
| Closing & vectorising a session | `skills/pen-and-paper/references/vectorizer.md` |
| Want to understand *why* P&P exists | `skills/pen-and-paper/references/philosophy.md` |
| Need long-term knowledge instead | Switch to `llm_wiki` — see bridge section below |

## Full catalog

### Operating layer (read often)

- `_start_here.md` — operating instructions, 7 core rules — **always read first**.
- `_index.md` — this page — when you do not know which other page to open.
- `_aliases.md` — all the names that refer to Pen & Paper (and the ones that do not) — when terminology looks ambiguous.

### Templates (copy when creating)

- `data/templates/session.md` — canonical session skeleton — when `pen_paper action=create` does not auto-template.

### Configuration (mostly admin-facing)

- `data/config/onboarding.yaml` — exhaustive onboarding manual (long) — only when `_start_here.md` does not answer your question.
- `data/config/rules.yaml` — system rules in machine-readable form — when writing tooling around P&P.

### Methodology references (read on demand)

- `skills/pen-and-paper/SKILL.md` — the skill description and high-level workflow — when re-orienting mid-task.
- `skills/pen-and-paper/references/philosophy.md` — why this system exists — first time you use the plugin or when something feels wrong.
- `skills/pen-and-paper/references/session-management.md` — lifecycle, cleanup, split, archive — when a session is getting unwieldy.
- `skills/pen-and-paper/references/vectorizer.md` — how `vectorize=true` works at close — when deciding what to vectorise.
- `skills/pen-and-paper/references/plugin-packaging.md` — internals — only when modifying the plugin itself.

### Documentation (admin / human-facing)

- `README.md` — install + basic usage — rarely needed during agent execution.
- `docs/CAPABILITIES_AND_ROADMAP.md` — feature inventory + future work — rarely needed during agent execution.

## Bridge to LLM Wiki

When you need long-term knowledge instead of working memory:

- `wiki_query` — search across all readable wikis for prior knowledge.
- `wiki_ingest` — promote a finding from this session into a wiki.
- See `wikis/onboarding/wiki/_start_here.md` in the SharedBrain vault for the wiki-side equivalent of this file.

## Reading budget

Aim for ≤3 reference pages per task. If you find yourself opening a 4th, the session itself is probably the wrong shape — re-read `_start_here.md` and reconsider.

## Hard ceiling — 500 lines per file

Every page in this plugin (and in `llm_wiki`) must stay ≤500 lines. Above 500, the agent's context budget pays a real cost. If a page grows past 500, split it and link with `[[wikilinks]]` (wiki) or sub-session files (P&P).
