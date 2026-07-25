# Pen & Paper — standalone, harness-agnostic repo

**Audience:** an agent or developer working in a **fresh context** on the new
standalone Pen & Paper repository, with no access to the conversation that
produced this document.

**Source of truth for current behavior:** the Agent Zero plugin
`adam10890/a0_pen_paper`. This document describes what to extract, what to
leave behind, and what to build around it.

---

## 1. What Pen & Paper is

A **structured thinking workspace** for AI agents. Not a note-taking app and
not a memory store.

The governing distinction (from the plugin's own `rules.yaml`):

> Memory = the library. P&P = the notebook on the desk.
> P&P is a **workspace, not storage**. Distill information from memory into
> P&P; do not copy everything.

Concretely: an agent opens a **session**, writes into typed **sections** as it
works, and closes it. State lives in plain files on disk that a human can read,
`grep`, and commit to git. That transparency is the product, not an
implementation detail — it is why the system is files and not a database.

### Why a standalone repo

Today the logic is fused to Agent Zero: import paths, config loading, and path
resolution all assume an Agent Zero runtime. Other harnesses (Claude Code,
Cursor, MCP clients, plain CLI, CI) cannot use it. The goal is a **portable
core** plus **thin adapters**.

---

## 2. Non-negotiable design constraints

Carry these forward; they were paid for in bugs.

1. **Files on disk, human-readable, no database.** A session must remain
   greppable and diffable. If a design step requires a DB, it is the wrong step.
2. **Reads never mutate.** Listing or reading a session must not rewrite,
   backfill, or "repair" the file on disk. This is verified by tests in the
   plugin and must stay verified.
3. **Back-compat is absolute.** A workspace file written by an older version
   must load without migration. Every new field is optional with a derived or
   default value.
4. **Validate on write; tolerate on read.** The write path rejects malformed
   data. The read path *skips* malformed entries rather than raising — one
   corrupt entry must never make an otherwise valid session unlistable.
   (The plugin shipped a bug where validation ran only on write; do not repeat it.)
5. **Unknown input is an error, not a silent default.** An unknown filter key
   must raise. Silently ignoring a typo returns confidently wrong data.
6. **English only** in code, comments, docs, and prompts. Session *content* may
   be any language.

---

## 3. Current data model (extract this exactly)

### 3.1 Session workspace — `workspace.json`

One directory per session; the file lives at
`<runtime>/sessions/{active|archive}/<name>/workspace.json`.

```json
{
  "metadata": {
    "name": "string",
    "status": "active | closed",
    "state": "NORMAL | ARCHIVED",
    "template": "template_name | null",
    "template_version": "semver | null",
    "chat_id": "string | null",
    "created_at": "ISO8601"
  },
  "relations": [
    { "type": "REFERENCE | COMMENT", "target": "other_session_name" }
  ],

  "findings": [],
  "results": [],
  "insights": [],
  "notes": [],
  "decisions": [],
  "backtrack": [],
  "execution_log": []
}
```

**`VALID_SECTIONS`** = `findings, results, insights, notes, decisions,
backtrack, execution_log`. Sections are arrays of entries.

**`status` vs `state` are orthogonal and must stay that way:**

| Field | Values | Means |
|---|---|---|
| `metadata.status` | `active` / `closed` | work lifecycle — is the session finished? |
| `metadata.state` | `NORMAL` / `ARCHIVED` | storage/visibility — is it filed away? |

Closing a session sets `status: closed`; it does **not** archive it.

**Back-compat rule for `state`:** when the field is absent, derive it from the
directory (`sessions/active` → `NORMAL`, `sessions/archive` → `ARCHIVED`). The
explicit field wins when present. Never move files as a side effect of a read.

**Relations:** self-relations are rejected. Target existence is deliberately
**not** enforced — a relation may point at a session created later or since
deleted. Enforcing it would make creation order brittle.

### 3.2 Computed properties (derived, never stored)

Computed per session at list time from the concatenated section text, so a
client can triage **without opening every workspace**:

`has_link`, `has_task_list`, `has_incomplete_tasks`, `has_code`,
`has_execution_log`, `has_backtrack`, `title` (first Markdown H1, falling back
to the session name).

Compute once per session from already-parsed JSON. Keep regexes as
module-level constants.

### 3.3 Listing contract

```
list_sessions(
    *,
    include_archived: bool = False,
    page_size: int | None = None,      # max 1000, clamped
    page_token: str | None = None,     # opaque, signed against query shape
    order_by: str | None = None,       # "mtime|created|name" + " asc|desc"
    filter: dict | None = None,
) -> dict
```

- `filter` is a **structured dict, not an expression language.** Keys: `state`,
  `status`, `template`, `chat_id`, `name_contains`, the six boolean computed
  properties, `has_relations`, `relation_target`. All AND-ed. An unknown key
  raises.
- `page_token` is signed against `{order_by, filter, chat scope,
  include_archived}` so reusing it under a different query raises instead of
  returning a mismatched page.
- **Precedence:** `include_archived` decides which directories are *scanned*;
  `filter.state` only narrows within that scan and never widens it.
- Pipeline order: scan → sort → chat filter → structured filter → paginate.
  Filtering must happen before pagination or pages overlap.
- Passing none of these must reproduce the previous response shape exactly,
  including the **absence** of `next_page_token`.

### 3.4 Workflow templates

A registry (`template_registry.json`) maps template names to Markdown files
plus `version`, `description`, `phases`, `triggers`, and `base_workflows.hooks`
(`on_unknown`, `on_stuck`, `on_error`, `on_complete`). **Every hook target must
exist in `templates` with a matching `.md` file** — there is an integrity
validator for this; keep it.

### 3.5 Config schema (nested is canonical)

```json
{
  "runtime_dir": "usr/pen_and_paper",
  "features": {
    "retrieve_context_on_create": false,
    "vectorize_on_close": false,
    "context_loader_enabled": false,
    "context_loader_first_iteration_only": true
  },
  "session": { "max_active_sessions_in_context": 5 }
}
```

An older **flat** variant exists in the wild (`vectorize_by_default`,
`retrieve_context_by_default`, `max_active_sessions_in_context` at top level).
The plugin normalizes it at load time. Port that normalization; do not
reintroduce flat keys.

---

## 4. The coupling to break

These are the exact lines that make the current code non-portable:

| Coupling | Where | Fix |
|---|---|---|
| `from usr.plugins.a0_pen_paper.tools._config import ...` | `sessions_store.py:17`, `workflows_store.py:17`, `workflow_executor.py:16` | relative/package-internal imports |
| `from usr.plugins.a0_pen_paper.helpers import sessions_store` | `workflows_store.py:16` | same |
| `from helpers import files` → `files.get_abs_path()` | `sessions_store.py:96`, `workflows_store.py:45` | inject a path resolver |
| `from helpers.plugins import get_plugin_config` | `tools/_config.py:66` | inject a config provider |

The `usr.plugins...` absolute paths are the worst offender: they force every
consumer to fake a package tree. The plugin's own tests each carry an
`_install_standalone_package_alias()` shim to work around it — that shim is a
symptom, and it should not exist in the new repo.

**Target:** `core/` imports nothing from any harness. Two injection points:

```python
# core/runtime.py
class Runtime:
    """Everything the core needs from its host."""
    def resolve_path(self, relative: str) -> Path: ...
    def load_config(self) -> dict: ...

# Default implementation: plain filesystem + JSON/YAML file, zero deps.
```

Adapters supply a `Runtime`; the core never imports one.

---

## 5. Proposed repo layout

```
pen-paper/
  core/                     # zero harness imports, zero framework deps
    sessions.py             # workspace CRUD, sections, state, relations, properties
    listing.py              # filter / order_by / pagination
    workflows.py            # template registry + integrity validation
    executor.py             # step execution, execution_log
    config.py               # nested schema + legacy normalization
    runtime.py              # Runtime protocol + default filesystem impl
    schema/
      workspace.schema.json
      registry.schema.json
  adapters/
    agent_zero/             # Tool subclass, ApiHandler, extensions, webui
    mcp/                    # MCP server (see §6)
    cli/                    # `penpaper` command
    http/                   # standalone REST server
  skills/                   # see §7
  data/
    config/{rules,onboarding}.yaml
    templates/
    workflows/              # research.md, debugging.md, validation.md + seed registry
  tests/
    core/                   # harness-free, the bulk of the suite
    adapters/
  docs/
```

**Rule:** anything importing a harness lives under `adapters/`. If `core/`
needs a harness type, the design is wrong.

---

## 6. Harness adapters

| Adapter | Surface | Notes |
|---|---|---|
| **MCP** | `pen_paper.*` tools over MCP | **Highest priority.** MCP is the lingua franca for Claude Code, Cursor, and most modern clients. One adapter unlocks the majority of the "different harnesses" goal. |
| **CLI** | `penpaper session create/update/list/close` | Enables CI, shell agents, and manual use. Also the easiest end-to-end test surface. |
| **Agent Zero** | existing Tool + ApiHandler + Right Canvas | Port last; it must keep working. Treat the current plugin as the compatibility baseline. |
| **HTTP** | REST over `core` | For harnesses without MCP. |

Suggested MCP tool surface (mirrors the current tool actions):

```
pen_paper_create      (name, template?, variables?)
pen_paper_update      (name, section, content)
pen_paper_get         (name, section?)
pen_paper_list        (filter?, order_by?, page_size?, page_token?, include_archived?)
pen_paper_close       (name, vectorize?, ephemeral?)
pen_paper_relate      (name, target, type)
pen_paper_templates   (list | use)
```

---

## 7. `SKILL.md` — how every agent learns the system

This is the part that decides whether an arbitrary agent uses P&P *correctly*
or just pokes at it. The tools alone are not enough; behavior must be specified.

### 7.1 Why a skill and not just tool descriptions

Tool descriptions say *what a call does*. The skill says **when to reach for
the system, in what order, and what not to do**. The plugin's contract already
defines a mandatory sequence; it belongs in the skill:

1. Load the skill before starting work.
2. `list_templates` if the template name is unknown.
3. `use_template` with explicit variables.
4. Per phase: `update` the defined section **before** marking that phase
   complete in notes.
5. `close` with an explicit vectorize/ephemeral decision.

**Prohibitions worth stating explicitly:**
- Do not tick off items in notes without a matching `update` call.
- Do not leave an active session unclosed.
- Do not use P&P as long-term storage — distill, then close.

### 7.2 Single source, generated variants

Harnesses disagree on format. Author **one** canonical skill and generate the
rest, so behavior cannot drift:

```
skills/
  pen-and-paper/
    SKILL.md              # canonical: frontmatter + body
    references/
      philosophy.md       # progressive disclosure — loaded on demand
      session-management.md
      workflow-authoring.md
  _generated/
    claude-code/          # .claude/skills/ layout
    cursor/               # .cursor/rules/ layout
    agent-zero/           # AZ skills layout
    mcp-prompt.md         # served as an MCP prompt
```

A `make skills` step renders the variants. Add a CI check that fails if a
generated file is stale relative to the canonical source.

### 7.3 Canonical `SKILL.md` skeleton

```markdown
---
name: pen-and-paper
description: >
  Structured thinking workspace for multi-step work. Use when a task needs
  more than one step, spans multiple tool calls, or must survive a context
  reset. Not for one-shot answers.
triggers: [research, debugging, investigation, multi-step, planning]
---

# Pen & Paper

## When to use this
Multi-step work whose intermediate state matters. If the task is one
question with one answer, do NOT open a session.

## Mental model
Memory = the library. P&P = the notebook on the desk.
Distill into the notebook; do not copy the library into it.

## Sections — pick deliberately
| Section | Holds |
|---|---|
| findings | what you discovered (evidence) |
| results | outputs produced |
| insights | conclusions drawn from findings |
| decisions | choices made, with the reason |
| backtrack | dead ends — so they are not retried |
| notes | working scratch |
| execution_log | workflow step status (tooling writes this) |

## Mandatory sequence
1. `list` — is there an open session for this work already?
2. `create` (or `use_template`)
3. `update` the relevant section as you go — before claiming a step is done
4. `close` when finished, with an explicit vectorize decision

## Never
- Tick a checkbox without a matching `update`
- Leave a session open at the end of a task
- Paste large content verbatim — distill it

## More
- references/philosophy.md
- references/session-management.md
```

Keep the body short. Push detail into `references/` so it loads only when
needed — a skill that blows the context budget will be skipped.

### 7.4 Verifying agents actually follow it

Skills are prose; prose drifts. Add a small eval suite:

- Given a multi-step task, does the agent open a session at all?
- Does every "phase complete" claim have a preceding `update`?
- Does it close the session?
- Given a one-shot question, does it correctly *not* open a session?

`execution_log` plus session history make these checkable mechanically.

---

## 8. Suggested phasing

| Phase | Deliverable | Done when |
|---|---|---|
| 0 | Repo skeleton, license, CI | `pytest`/`unittest` runs green on an empty core |
| 1 | Port `core/sessions.py` + `listing.py` with **zero harness imports**; port the existing tests | full session suite passes with no `usr.plugins` shim anywhere |
| 2 | `core/config.py` incl. legacy flat-key normalization; JSON Schemas | a legacy workspace + legacy config both load |
| 3 | CLI adapter | create → update → list → close works end-to-end in a shell |
| 4 | MCP adapter | a Claude Code / Cursor session drives P&P over MCP |
| 5 | Canonical `SKILL.md` + generator + staleness CI check | `make skills` reproduces all variants byte-identically |
| 6 | `core/workflows.py` + `executor.py` | registry integrity validation passes; hooks resolve |
| 7 | Agent Zero adapter | the existing plugin suite passes against the extracted core |
| 8 | Skill-adherence evals (§7.4) | agents measurably follow the mandatory sequence |

Phase 1 is the real work. Phases 3–4 are what make the repo useful to anyone
other than Agent Zero.

---

## 9. Traps found the hard way

- **Mojibake.** `rules.yaml` and `onboarding.yaml` shipped double-encoded
  (UTF-8 read as cp1252) for months, corrupting Hebrew, arrows, box-drawing and
  emoji. When porting: read bytes, verify round-trip, and add a CI grep for
  `×|â†|â”|ðŸ|Â` over `data/`.
- **Blanket re-decoding is lossy.** A naive `encode("cp1252",
  errors="ignore").decode("utf-8")` silently drops characters undefined in
  cp1252 (Hebrew final-mem, some emoji) and corrupts legitimate em-dashes.
  Reverse only contiguous runs that decode to valid UTF-8.
- **Latent import bugs hide under `discover`.** A test module missing
  `import types` passed for weeks because an alphabetically earlier module
  registered a shared alias first. **Run every test module in isolation in CI**,
  not just the whole suite.
- **Same version, two schemas.** Two branches both shipped `1.2.0` with
  incompatible config shapes. Bump the version whenever a schema changes.
- **`archive` is a directory in one place and a field in another.** During the
  transition both exist. Decide early which is authoritative in the new repo
  (recommendation: the **field**, with the directory as a legacy fallback only).

---

## 10. Open questions for the owner

1. **Runtime layout.** Keep `usr/pen_and_paper/` for AZ compatibility, or adopt
   a neutral default (`.penpaper/`) with the AZ adapter overriding it?
2. **Package name** on PyPI (`pen-paper`? `penpaper`?) and Python floor (3.11+
   matches the current `dict[str, Any]` / `X | None` syntax).
3. **Vectorization** is currently an Agent Zero feature (`vectorize_on_close`).
   Core concern with a pluggable backend, or adapter-only?
4. **Storage authority** for archived state — field or directory (see §9).
5. **License** for the standalone repo.
6. Does the standalone repo **vendor** the AZ plugin as an adapter, or does the
   plugin depend on the published package?
