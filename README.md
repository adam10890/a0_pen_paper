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

## Included

- Agent tool: `pen_paper`
- Agent tool: `pen_paper_diagram` for editable `.drawio` workflow diagrams
- Optional vector helper with graceful fallback
- Prompt guidance for the tool
- Skill documentation under `skills/pen-and-paper`
- Minimal onboarding/config/template files
- Prompt context loader extension
- Visual development tracker

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

## Optional Scribe Agent

This package includes `optional_agents/scribe_DISABLED/` as **disabled** documentation
and a future activation template. It is not auto-loaded.

To enable Scribe later, copy the folder to `/a0/usr/agents/scribe/` and rename
`agent.yaml.example` to `agent.yaml`. See `docs/OPTIONAL_COMPONENTS.md` and
`optional_agents/scribe_DISABLED/README.md` for details.
