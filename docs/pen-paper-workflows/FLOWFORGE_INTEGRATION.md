# FlowForge-Style Diagram Integration

**Version:** 0.1
**Status:** MVP implemented with Workflows Canvas generation controls
**Scope:** Pen & Paper diagram artifacts, not whiteboard persistence

## Purpose

Pen & Paper workflows and live sessions can now be rendered as editable
`.drawio` diagrams. This is inspired by FlowForge's deterministic draw.io XML
workflow, but implemented locally to avoid adding a runtime dependency on an
external Claude Code skill.

The integration is a renderer/exporter:

```text
Pen & Paper template/session/text
        -> pen_paper_diagram
        -> .drawio XML artifact
        -> draw.io / diagrams.net / VS Code draw.io extension
```

It does not replace `a0_whiteboard`, and it does not write whiteboard state.

## Tool

`pen_paper_diagram` supports:

| Source | Input | Output location |
|--------|-------|-----------------|
| `template` | `template_name` / `source_id` | `usr/pen_and_paper/diagrams/templates/<template>/` |
| `session` | active workspace `name` / `source_id` | `usr/pen_and_paper/sessions/active/<session>/diagrams/` |
| `text` | `content` | `usr/pen_and_paper/diagrams/ad_hoc/` |

Supported diagram types:

- `flow`
- `flow-vertical`
- `layers`
- `sequence`
- `timeline`

Supported themes:

- `tech-blue`
- `morandi`
- `mint`
- `terracotta`
- `indigo`

## Design Rules

- Keep generation deterministic: fixed coordinates, stable theme colors, and
  predictable node extraction.
- Treat draw.io files as artifacts. Source of truth remains the workflow
  template or `workspace.json`.
- Keep whiteboard integration as an explicit bridge. Pen & Paper exports the
  `.drawio`; `Send to Whiteboard` creates an annotation copy as whiteboard
  shapes.
- Store generated files under the Pen & Paper runtime directory, not in plugin
  source.

## Future UI Hook

The existing `pen_paper_workflows` Right Canvas surface includes a `Diagram`
control row:

- Templates mode: generate from selected template.
- Live mode: generate from selected session.
- Current MVP: show generated file path after creation.
- Current UI: preview sketch, copy path, download `.drawio`, open diagrams.net,
  and send an annotation copy to Whiteboard.

Do not add a second Canvas surface for this MVP.
