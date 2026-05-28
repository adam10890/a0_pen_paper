# Pen & Paper Wiki Template Tool

The `pen_paper_wiki_template` tool discovers wiki pages tagged as Pen & Paper workflow templates from the LLM Wiki SharedBrain vault.

## When to Call This Tool

Call `list_templates` only when starting a new Pen & Paper session and a wiki workflow template may help, or when the user explicitly mentions structured research, debugging, planning, or similar workflow templates.

Do not use this tool for general wiki search; use the wiki tools/librarian for normal knowledge lookup.

## Actions

### `action=list_templates`

Scans readable SharedBrain wikis for pages tagged with `type: pen_paper_template` in YAML frontmatter. Returns namespace, wiki, phase count, context budget, and short description.

### `action=load_template`

Required: `namespace=wiki:<wiki_name>:<template_name>`

Returns metadata, phases, triggers, a short preview, and a JSON `session_payload`.

## After Loading a Template

The current `pen_paper` tool does not have `create_session` or `create_from_payload`. To use a wiki template today, create a workspace with normal `create` and paste the payload or selected template notes into `content`:

```json
{"tool_name":"pen_paper","tool_args":{"action":"create","name":"my_task","content":"<session_payload or template notes>"}}
```

Then continue with normal `update`, `read`, and `close` actions.

## Template Format in Wiki

A wiki page becomes a Pen & Paper template when its YAML frontmatter includes:

```yaml
---
type: pen_paper_template
template_name: research_session
title: "Structured Research Session"
description: "Deep-dive research workflow with source tracking"
phases:
  - name: Plan
    description: "Define research question and scope"
  - name: Gather
    description: "Collect and ingest sources"
triggers: [research, deep-dive, investigate]
context_budget: medium
---
```

## Error Handling

The tool should degrade gracefully if integration is disabled, the vault is missing, no tagged templates exist, or a page has malformed frontmatter.
