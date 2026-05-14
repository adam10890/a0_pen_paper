# Pen & Paper Wiki Template Tool

The `pen_paper_wiki_template` tool discovers and loads wiki pages tagged as Pen & Paper workflow templates from the LLM Wiki SharedBrain vault.

## When to Call This Tool

**Call `list_templates` ONLY when:**

- Starting a new Pen & Paper session
- The user explicitly mentions a topic that may have a wiki workflow (e.g., "research", "debugging", "planning")

**Do NOT call this tool:**

- To browse general wiki content — use `wiki_query` for that
- To read arbitrary wiki pages — this tool only surfaces templates
- More than once per agent iteration

## Actions

### `action=list_templates`

Scans all readable wikis for pages tagged with `type: pen_paper_template` in YAML frontmatter.

Returns a compact table with template metadata:
- Namespace: `wiki:<wiki_name>:<template_name>`
- Wiki name
- Phase count
- Context budget (low/medium/high)
- Description (truncated)

Context cost: ~200-500 tokens (cached results are even cheaper)

### `action=load_template`

Loads a specific template's metadata and structure.

Required argument: `namespace=<wiki:name>` (e.g., `namespace=wiki:commons:research_session`)

Returns:
- Template metadata (title, description, phases, triggers)
- First 500 chars of page body as preview
- A `session_payload` JSON blob ready to pass to `pen_paper.create_session`

Context cost: ~300-800 tokens

## Context Window Safeguards

This tool enforces strict limits to prevent context overflow:

- **Max 20 templates per list** — table format is already compact
- **Max 500 chars preview** by default
- **Max 3000 chars** on full content load
- **5-minute discovery cache** — avoids repeated file scans
- **Namespace separation** — wiki templates are distinct from built-in Pen & Paper templates

## After Loading a Template

To create a Pen & Paper session with the loaded template, call the `pen_paper` tool:

```
pen_paper action=create_session title=<your session title> template_payload=<session_payload_from_load_template>
```

The `session_payload` blob includes:
- Template source (wiki namespace)
- Phase-based section structure
- Metadata (context budget, triggers, description)

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
  - name: Analyze
    description: "Cross-reference and synthesize"
  - name: Conclude
    description: "Summarize findings and gaps"
triggers: [research, deep-dive, investigate]
context_budget: medium
---
```

## Error Handling

The tool degrades gracefully if:

- `llm_wiki` plugin is not installed → returns clean error message
- No SharedBrain vault configured → returns "no vault configured"
- No tagged templates found → returns "no templates found"
- Malformed frontmatter → page is skipped with warning logged
