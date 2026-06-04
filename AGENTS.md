# AGENTS.md — a0_pen_paper

**Version:** 1.1.2 | **Target:** Agent Zero v1.15–v1.17

## What this plugin does

Structured thinking workspace for agents. Creates named task sessions, records findings/decisions/insights/notes/backtrack items into sections, and archives sessions when done. Optional vector recall and LLM Wiki template integration.

## Key files

| Path | Role |
|---|---|
| `plugin.yaml` | Manifest — `per_project_config: true`, `per_agent_config: true` |
| `tools/pen_paper.py` | Main tool (~47KB) — all session actions |
| `tools/_config.py` | Config loading helpers |
| `tools/_wiki_helpers.py` | LLM Wiki bridge (template export) |
| `tools/pen_paper_wiki_template.py` | Wiki template generation |
| `hooks.py` | `install(**kwargs)` — creates runtime directory tree on first activation |
| `extensions/` | Prompt context loader — injects session summary into system prompt |
| `data/config/` | Default `onboarding.yaml`, `rules.yaml` |
| `data/templates/session.md` | Default session template |

## Runtime storage (outside plugin dir)

```
usr/pen_and_paper/
├── sessions/
│   ├── active/          # open sessions
│   └── archive/         # closed sessions
├── config/              # onboarding.yaml, rules.yaml
├── templates/           # custom session templates
├── knowledge/workflows/ # template_registry.json
└── vectors/             # vector cache (optional)
```

Never write session data inside the plugin directory.

## Tool: `pen_paper`

| Action | Key args | Notes |
|---|---|---|
| `create` | `name`, `template` (opt) | Opens a new session |
| `update` | `name`, `section`, `content` | Appends to a section |
| `read` | `name`, `section` (opt) | Returns session content |
| `close` | `name`, `vectorize` (opt) | Archives the session |
| `list` | — | Active sessions |
| `delete` | `name` | Removes from archive |

## Section types

`findings` · `decisions` · `insights` · `results` · `notes` · `backtrack`

## LLM Wiki bridge

`tools/_wiki_helpers.py` — when `llm_wiki` is installed, `close` with `vectorize: true` exports the session as a wiki template for long-term knowledge retention.

## Prompt context loader

`extensions/` injects the active session summary into the agent's system prompt on each turn — the agent always knows its current workspace state without having to call `read`.

## How to add a new section type

Add the section name to the allowed sections validation block in `tools/pen_paper.py`.

## Constraints

- Sessions live in `usr/pen_and_paper/sessions/` — never inside the plugin dir.
- `hooks.py::install(**kwargs)` creates the runtime tree — idempotent.
- Vector cache is optional — graceful fallback if `sentence-transformers` is not installed.
- Page size: warning at 250 lines, split at 300 lines.
