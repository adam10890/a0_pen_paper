# Aliases — Names for "Pen & Paper"

This page exists so you never waste tokens wondering "is this the same thing as...?" If you see any term in the table below, it refers to **this plugin**. Stop guessing and get on with the task.

**Canonical name:** *Pen & Paper* (capital P, capital P, ampersand).

## Aliases — all refer to Pen & Paper

| Alias | Where you'll see it | Notes |
|---|---|---|
| `Pen & Paper` | docs, prose, headings | Canonical full name |
| `P&P` | shorthand in docs and chat | Same thing |
| `pen and paper` / `pen-and-paper` | English prose, skill folder | Same |
| `pen_paper` | the tool name in JSON tool calls (`tool_name: "pen_paper"`) | The Python tool that backs the plugin |
| `skills/pen-and-paper/` | directory under `skills/` | The Anthropic-format skill that activates the plugin |
| `a0_pen_paper` | GitHub repo name | This plugin's repository |
| `עט ונייר` | Hebrew prose (Adam writes in Hebrew) | Same |
| `דף ועט` | Hebrew variant Adam uses casually | Same |
| `Pure Skill` | architecture docs | The *class* of plugin P&P belongs to — not P&P itself, but every reference applies to P&P |
| `scratchpad` / `notepad` / `notebook` | informal metaphors | The metaphor for what P&P *is* |
| `working memory` | functional description in docs | What P&P *does* relative to `llm_wiki` |
| `session` / `workspace` | runtime artifacts | A single P&P file (one task's notes), produced by `pen_paper action=create` |
| `structured thinking` / `think step by step` | skill trigger_patterns | Phrases that activate the skill |

## Related but DISTINCT — not aliases

These look similar but are **not** Pen & Paper. Do not conflate them.

| Term | What it actually is |
|---|---|
| `llm_wiki` / `LLM Wiki` / `SharedBrain` | The *other* plugin — long-term memory. P&P's complement, not its synonym. |
| `wiki_query` / `wiki_ingest` / `wiki_list` / `wiki_lint` / `wiki_register` / `wiki_commit` | Tools from `llm_wiki`, not from this plugin |
| `Karpathy wiki` / `wikillm` | Andrej Karpathy's wiki pattern that `llm_wiki` implements; not P&P |
| `Agent Zero` / `a0` | The host runtime. P&P is a plugin *for* Agent Zero, not Agent Zero itself. |
| `Obsidian vault` | The format `llm_wiki` uses for its storage; P&P's session files are plain markdown but live outside any vault |

## One-line rule

If you encounter a term in the **Aliases** table, do not re-derive its meaning — it refers to this plugin. If you encounter a term in the **Distinct** table, it refers to something else; check that doc, not this one.
