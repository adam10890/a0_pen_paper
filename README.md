# Pen & Paper Plugin

Pen & Paper is a structured thinking workspace plugin for Agent Zero.

It provides a `pen_paper` tool for creating task workspaces, recording
findings, decisions, insights, results, notes, and backtrack items, then
closing sessions into an archive.

## Install

Extract this folder into:

```text
/a0/usr/plugins/a0_pen_paper/
```

Restart Agent Zero or refresh plugin caches after installation.

## Runtime data

The plugin stores runtime sessions outside the plugin directory:

```text
/a0/usr/pen_and_paper/
```

This keeps plugin removal and upgrades safer.

## State-DOX working state

Pen & Paper also stores a compact machine-readable state layer for background
writers such as `a0_scribe`. Reusable workflow templates live in
`data/workflow_state_templates/`; each active session gets mutable live copies
under `state/workflows/`, plus `state/session_state.yaml` and `state/events.jsonl`.
The YAML files are the current working state, while `workspace.json` remains the
human-readable ledger.

State-DOX runtime layout:

```text
sessions/active/<workspace>/
├── workspace.json
└── state/
    ├── events.jsonl
    ├── session_state.yaml
    └── workflows/
        ├── planning.yaml
        ├── implementation.yaml
        ├── debugging.yaml
        ├── verification.yaml
        └── research.yaml
```

`events.jsonl` is append-only audit evidence. `session_state.yaml` and
`state/workflows/*.yaml` are mutable live state. Each workflow template declares
the matching `a0_scribe` workflow skill so the background scribe can load the
right capability guidance.

Workflows published from the UI can define custom `activation_tags`. Scribe
will apply those tags only when a later observation emits explicit evidence
such as `SCRIBE_TAGS: tag_name` / `STATE_DOX_TAGS: tag_name`, or when the exact
tag appears in non-read-only activity. Reading a source file that merely
contains the tag string is not enough to activate the workflow.

The preferred State-DOX template schema is nested (`workflow.activation_tags`
and `scribe.skill`), but the reader also accepts flat runtime YAML with `name`,
`activation_tags`, and `skill` for agent-authored workflow files.

Pen & Paper also maintains a chat focus pointer used by `a0_scribe`. The focus
extension reads the current tool metadata from `agent.loop_data.current_tool.args`
when Agent Zero does not pass `tool_args` into `tool_execute_after`.

## Included

- Agent tool: `pen_paper`
- Agent tool: `pen_paper_diagram` for editable `.drawio` workflow diagrams
- Optional vector helper with graceful fallback
- Prompt guidance for the tool
- Skill documentation under `skills/pen-and-paper`
- Minimal onboarding/config/template files
- Visual development tracker
- State-DOX workflow templates for machine-readable per-session working state

## Excluded intentionally

- Legacy session API endpoint
- GSD workflows
- Archived sessions
- Vector DB cache files
- Legacy workflow archives

## Basic usage

```json
{"tool_name":"pen_paper","tool_args":{"action":"create","name":"my_task"}}
```

```json
{"tool_name":"pen_paper","tool_args":{"action":"update","name":"my_task","section":"findings","content":"Important finding"}}
```

```json
{"tool_name":"pen_paper","tool_args":{"action":"close","name":"my_task","vectorize":true}}
```

Generate an editable draw.io diagram from a workflow template:

```json
{"tool_name":"pen_paper_diagram","tool_args":{"source_type":"template","template_name":"debugging","diagram_type":"flow-vertical"}}
```

The Workflows Canvas can preview the generated sketch, download the `.drawio`
file, open diagrams.net, or send an annotation copy to `a0_whiteboard`.

## Scribe integration

The active Scribe integration is the separate `a0_scribe` plugin. It observes
tool activity, writes compact State-DOX events into the focused Pen & Paper
workspace, updates workflow YAML, and may inject compact working state back into
the ego.

An earlier in-tree scribe agent profile was removed from this package; it is not
the current integration path.

Use `a0_scribe` for current Scribe work. See
`../a0_scribe/README.md` for the observer, state semantics, and test prompts.
