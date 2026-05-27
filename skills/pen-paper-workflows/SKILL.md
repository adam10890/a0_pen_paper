---
name: pen-paper-workflows
description: >
  Create, edit, and manage Pen & Paper workflow templates (markdown + registry metadata)
  for the a0_pen_paper plugin. Use when the user asks to edit workflows, templates, phases,
  triggers, template_registry, knowledge/workflows, Canvas workflow editor, create_template,
  edit_template, use_template, co-design a workflow with the user, iterative workflow
  improvement, or stop_no_change when the workflow must not be modified.
version: 1.3.0
author: frantz
tags: [pen-paper, workflows, templates, markdown, registry, canvas]
trigger_patterns:
  - workflow template
  - edit workflow
  - pen paper template
  - template_registry
  - knowledge/workflows
  - create_template
  - edit_template
  - use_template
  - phases triggers
  - Canvas workflows
  - build workflow
  - co-design workflow
  - stop_no_change
  - iterative workflow
priority: 2
---

# Pen & Paper — Workflow Editing

Workflow templates are Markdown files plus entries in `template_registry.json`. They power `pen_paper` (`use_template`, `create` with `template`) — the **same files** are edited in the UI (Canvas) and by the agent.

## Locations

| Item | Path |
|------|------|
| Registry | `usr/pen_and_paper/knowledge/workflows/template_registry.json` |
| Template body | `usr/pen_and_paper/knowledge/workflows/<name>.md` |
| Seed template | `usr/plugins/a0_pen_paper/data/templates/session.md` |
| Recommended starter | [workflow-template.md](references/workflow-template.md) |

Template names: `^[a-z0-9_]+$` (e.g. `research`, `debug_session`).

## `pen_paper` Tool Actions

| action | When |
|--------|------|
| `list_templates` | Before editing — list templates + phases/triggers |
| `create_template` | New template: `template_name`, `description`, `phases`, `triggers`, `content` (`template_content` alias is accepted) |
| `edit_template` | Update: `updates` with `content`, `description`, `phases`, `triggers` |
| `delete_template` | Delete (file archived under `_archived/templates/`); **do not** delete `session` |
| `use_template` | Live workspace: `template_name`, `name`, optional `variables` |

### Create a New Template (Agent)

```json
{
  "tool_name": "pen_paper",
  "tool_args": {
    "action": "create_template",
    "template_name": "incident_response",
    "description": "Structured incident triage",
    "phases": ["Triage", "Mitigate", "Postmortem"],
    "triggers": ["incident", "outage", "SEV"],
    "content": "# Incident Response\n\n## Phase 1: Triage\n\n### Notes:\n- \n"
  }
}
```

### Edit Content + Metadata

```json
{
  "tool_name": "pen_paper",
  "tool_args": {
    "action": "edit_template",
    "template_name": "incident_response",
    "updates": {
      "description": "Updated triage flow",
      "phases": ["Triage", "Mitigate", "Communicate", "Postmortem"],
      "content": "# Incident Response\n\n..."
    }
  }
}
```

### Use Template for a Session

```json
{
  "tool_name": "pen_paper",
  "tool_args": {
    "action": "use_template",
    "template_name": "incident_response",
    "name": "prod_outage_may21",
    "variables": {"SERVICE": "api-gateway"}
  }
}
```

Markdown body variables: `{{SERVICE}}` are substituted in `use_template`.

## `template_registry.json` Shape

```json
{
  "templates": {
    "session": {
      "file": "session.md",
      "description": "General structured working session",
      "phases": ["Plan", "Work", "Review"],
      "triggers": ["session", "planning", "task"]
    }
  },
  "base_workflows": {
    "list": ["research", "debugging", "validation"],
    "hooks": { "on_unknown": "research", "on_stuck": "debugging" }
  }
}
```

- `base_workflows` — suggested sub-flows (separate files not required in MVP)
- `triggers` — keywords for template suggestion (see `_suggest_template` in the tool)

## Human Editing (Canvas + Settings)

1. **Plugin Configure** → **Open Workflows in Canvas** (or Workflows icon on the right Canvas rail)
2. Edit Markdown + phases/triggers → **Save**
3. The agent sees file changes immediately; the panel auto-reloads when the agent saved and you have no unsaved local draft

WebUI API (not required for the agent):  
`/plugins/a0_pen_paper/workflows_list|workflows_get|workflows_save|workflows_create|workflows_delete`

## Recommended Agent Flow

1. `list_templates` — see what exists
2. If missing — `create_template` using [workflow-template.md](references/workflow-template.md)
3. If existing — `edit_template` (do not write disk directly unless the user explicitly asked)
4. `use_template` to open a working session for the user
5. Continue with **`pen-and-paper`** skill for session management (findings, close, …)

## Co-Design with the User

When the user asks to “build a workflow”, do not write a full template immediately. Run a short co-design:

1. Ask about **goal**, **triggers**, **work phases**, **done criteria**, and **what must not change**
2. Propose a skeleton from [workflow-template.md](references/workflow-template.md)
3. Request approval before `create_template` or Canvas/API save
4. After approval, create the template and open a trial session with `use_template`
5. Record in `decisions` why the structure was chosen

If the user wants real-time editing, use Canvas Workflows: the user edits; the agent proposes/updates via the same files.

## Iterative Improvement and Stop Gate

For improving an existing workflow, use a small controlled change loop:

1. **Baseline:** Read the current template and define the problem
2. **Hypothesis:** Propose **one** change only (phase, trigger, checklist, or wording)
3. **Dry run:** Validate against a short scenario or a real session
4. **Decision gate:** Ask/set one of three outcomes:
   - `apply` — save the change
   - `revise` — try another change
   - `stop_no_change` — stop and leave the workflow unchanged
5. On `stop_no_change`, do not call `edit_template`; record in `decisions` why no change was made

Also stop without asking again if:

- The proposed change does not improve the done criteria
- The user says “do not change”, “good enough”, “leave it as is”
- Two consecutive iterations show no clear improvement
- Risk of breaking the existing workflow outweighs the benefit

On stop, return a short summary: what was tested, why no change was saved, and what would trigger a new iteration later.

## Wiki Templates (Optional)

Templates from vault (not local registry files):

1. Ensure `llm_wiki_integration.enabled`
2. `pen_paper_wiki_template` → `load_template`
3. Create a normal Pen & Paper workspace with `action=create` and paste the returned `session_payload` or selected notes into `content`

For vault editing — `llm-wiki` skill; for local templates — this skill.

## References

- [Starter workflow template](references/workflow-template.md)
- [Registry & file layout](references/workflow-registry.md)
- [Pen & Paper sessions](../pen-and-paper/SKILL.md)
