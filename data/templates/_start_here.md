# Start Here — Pen & Paper Operating Instructions

You are reading this because the Pen & Paper skill just activated. This is the **first** page you read every time you use this plugin. It is short on purpose (under ~80 lines) so it costs almost nothing to keep in context.

## What Pen & Paper is

A structured working-memory workspace. Think of it as the notepad on a desk where you scribble *while* you work on a task. It is **not** a place to store knowledge for later — that belongs in `llm_wiki`.

## The 7 core rules

1. **Workspace, not archive.** P&P is for the current task. Do not write things here you will need next week.
2. **Extract, do not copy.** Pull only the facts you need from memory or tools. Do not paste whole documents.
3. **Work from P&P during execution.** Once a session is open, your scratchpad-of-truth is the session file, not your context window.
4. **Critical info at top & bottom.** "Lost in the Middle" is real. Put what matters most at the head and tail of each section.
5. **Aim for 200-300 lines per page.** Concise is faster to re-read.
6. **Cleanup at 250 lines.** Trim resolved sub-threads.
7. **Mandatory split at 300 lines.** Break into linked sub-sessions. Hard ceiling for the whole system: **500 lines per file** — never exceed it.

## Workflow

```
pen_paper(action="create", name="2026-05-20_task_name")
  -> update findings / decisions / insights as you work
  -> close at end (vectorize=true if worth recalling)
```

Naming: `YYYY-MM-DD_task_name.md`. System files prefixed with `_`.

## What to do next — read the index

You almost never need every reference page. **Open `_index.md`** (sibling of this file). It lists every available template, config, and reference page with a one-line description of when to reach for it. Pick the minimum set, then come back here if you forget the rules.

> Default reading order:
>
> 1. This file (`_start_here.md`) — done.
> 2. `_index.md` — to pick the next page.
> 3. The 1-2 specific pages your task actually needs.

## Bridge to LLM Wiki (long-term memory)

Before you start drafting in P&P, ask:

- **"Has anyone solved this before?"** → `wiki_query` against `llm_wiki`. If yes, build on it instead of starting from scratch.
- **"Will this be useful next time?"** → at the *end* of your session, promote the synthesised conclusion (not the scratch work) to `llm_wiki` via `wiki_ingest`.

Hard rule: never duplicate the same fact in both systems. P&P is for *this* session. Wiki is for *future* sessions.

## When in doubt

- Lost? Re-read this page.
- Need a specific procedure? Open `_index.md` and pick.
- Need methodology depth? `skills/pen-and-paper/SKILL.md` and `skills/pen-and-paper/references/`.
- Need to record something durable? Stop, switch to `llm_wiki`.
