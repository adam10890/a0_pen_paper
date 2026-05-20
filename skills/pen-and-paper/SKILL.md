---
name: pen-and-paper
description: Structured thinking workflow using virtual pen & paper sessions. Helps agent think step-by-step with persistent, searchable sessions. Use for complex reasoning, planning, or problem decomposition.
version: 1.1.0
author: Adam
tags: [thinking, methodology, workflow, planning, reasoning, sessions]
trigger_patterns: ["pen and paper", "pen paper", "think step by step", "structured thinking", "session", "עט ונייר", "חשיבה מובנית"]
priority: 2
---

# Pen & Paper (Pure Skill)

## First thing — always

When this skill activates, your **first action** is to read [`data/templates/_start_here.md`](../../data/templates/_start_here.md). It is the entry point to this entire system. Do not skip it; do not improvise.

From there, `_start_here.md` directs you to [`_index.md`](../../data/templates/_index.md) — a catalog of every reference page with a one-line summary of when to read it. Pick the **minimum** set relevant to your current task.

> Read `_start_here.md` → consult `_index.md` → load only the specific pages you actually need.

This skill exists so you do not have to keep every rule in context. The first two files are short on purpose.

## Pure Skill Architecture

This is a **Pure Skill** — a methodology and behavioral guide. The plugin provides the `pen_paper` tool, optional vector helper, prompts, templates, and references. This `SKILL.md` teaches the agent when and how to use the installed plugin; the templates teach the day-to-day mechanics.

## When to use Pen & Paper

- **Mandatory**: tasks with ≥3 tools, taking >90s, or involving multi-step planning.
- **Optional**: 2-tool operations.
- **Skip**: simple direct queries needing <2 tools.

Also use it when you need to make critical decisions, process complex logic, or structure a long-term plan.

## Relationship to LLM Wiki (long-term memory)

Pen & Paper is **working memory** — short-term, ephemeral, scoped to the current session (200-300 lines per page, archived after the session ends, deleted after 90 days).

The `llm_wiki` plugin is **long-term memory** — persistent knowledge that compounds across sessions (≤500 lines per page, retained indefinitely with git history).

Rules of thumb:

- Drafting / thinking through *this* task → Pen & Paper.
- Retrieving knowledge from prior work → `wiki_query` against `llm_wiki`.
- At session close, decide whether any P&P content is worth promoting to `llm_wiki` for future sessions.

Never duplicate the same fact in both.

## How it works (after you have read `_start_here.md`)

1. **Open a workspace**: `pen_paper` with `action: create`.
2. **Log findings**: record intermediate insights logically.
3. **Decisions**: explicitly document *why* you chose a path.
4. **Backtrack**: keep a list of things to return to.
5. **Close & vectorize**: complete the session with `action: close` (vectorize when useful).

## References

- [`_start_here.md`](../../data/templates/_start_here.md) — operating instructions (**read first**)
- [`_index.md`](../../data/templates/_index.md) — catalog of all pages
- [Philosophy & Core Principles](references/philosophy.md)
- [Session Management](references/session-management.md)
- [Vectorizer Details](references/vectorizer.md)
- [Plugin Packaging](references/plugin-packaging.md)
