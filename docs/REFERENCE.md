# a0_pen_paper — Reference

**Version:** 1.1.2 | Agent Zero v1.15–v1.17

## Overview

Structured thinking workspace. The agent creates named sessions, logs findings and decisions as work progresses, and archives them when done. Sessions persist across conversation turns.

## Installation

```bash
docker cp ./a0_pen_paper <container>:/a0/usr/plugins/a0_pen_paper
```

The `hooks.py` install hook creates `usr/pen_and_paper/` with the required directory tree on first activation.

## Tool API

Tool name: `pen_paper`

### create
```json
{"tool_name":"pen_paper","tool_args":{"action":"create","name":"my_task"}}
```
Optional: `"template": "session"` to use a named template.

### update — append to a section
```json
{
  "tool_name": "pen_paper",
  "tool_args": {
    "action": "update",
    "name": "my_task",
    "section": "findings",
    "content": "The API returns 429 when rate-limited."
  }
}
```

**Sections:** `findings` · `decisions` · `insights` · `results` · `notes` · `backtrack`

### read
```json
{"tool_name":"pen_paper","tool_args":{"action":"read","name":"my_task"}}
```
Optional: `"section": "findings"` to read a single section.

### close
```json
{"tool_name":"pen_paper","tool_args":{"action":"close","name":"my_task"}}
```
Optional: `"vectorize": true` to index into vector store and export wiki template.

### list
```json
{"tool_name":"pen_paper","tool_args":{"action":"list"}}
```

### delete
```json
{"tool_name":"pen_paper","tool_args":{"action":"delete","name":"my_archived_task"}}
```

## Storage

| Path | Contents |
|---|---|
| `usr/pen_and_paper/sessions/active/` | Open sessions |
| `usr/pen_and_paper/sessions/archive/` | Closed sessions |
| `usr/pen_and_paper/config/` | `onboarding.yaml`, `rules.yaml` |
| `usr/pen_and_paper/vectors/` | Vector cache (optional) |

## LLM Wiki integration

When `llm_wiki` is installed, closing a session with `vectorize: true` exports it as a wiki template — the session's knowledge becomes part of the long-term SharedBrain.

## Configuration

Section: `agent`. Supports per-project and per-agent overrides.

| Key | Default | Description |
|---|---|---|
| `vector.enabled` | `true` | Enable vector recall |
| `max_session_lines` | 250 | Warning threshold (split at 300) |

## Prompt context

The `extensions/` context loader automatically injects the active session summary into the agent's system prompt — no need to call `read` to orient the agent.
