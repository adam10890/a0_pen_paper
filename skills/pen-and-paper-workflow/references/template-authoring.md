# Template Authoring (reference for `pen-and-paper-workflow`)

Use this page when the task is to **create, edit, or manage Pen & Paper workflow
templates** (Markdown body + entries in `template_registry.json`). The same files
are edited by the agent (`create_template` / `edit_template`) and by the human in
the Canvas UI.

## Locations

| Item | Path |
|------|------|
| Registry | `usr/pen_and_paper/knowledge/workflows/template_registry.json` |
| Template body | `usr/pen_and_paper/knowledge/workflows/<name>.md` |
| Seed template | `usr/plugins/a0_pen_paper/data/templates/session.md` |
| Recommended starter | [workflow-template.md](workflow-template.md) |

Template names: `^[a-z0-9_]+$` (e.g. `research`, `debug_session`).

## `pen_paper` Tool Actions

| action | When |
|--------|------|
| `list_templates` | Before editing — list templates + phases/triggers |
| `create_template` | New template: `template_name`, `description`, `phases`, `triggers`, `content` (`template_content` alias is accepted) |
| `edit_template` | Update: `updates` with `content`, `description`, `phases`, `triggers` |
| `delete_template` | Delete (file archived under `_archived/templates/`); **do not** delete `session` |
| `use_template` | Live workspace: `template_name`, `name`, optional `variables` |

### Create a New Template

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

## Recommended Authoring Flow

1. `list_templates` — see what exists
2. If missing — `create_template` using [workflow-template.md](workflow-template.md)
3. If existing — `edit_template` (do not write disk directly unless the user explicitly asked)
4. `use_template` to open a working session for the user
5. Continue with the main `pen-and-paper-workflow` execution sequence

## Co-Design with the User

When the user asks to "build a workflow", do not write a full template immediately. Run a short co-design:

1. Ask about **goal**, **triggers**, **work phases**, **done criteria**, and **what must not change**
2. Propose a skeleton from [workflow-template.md](workflow-template.md)
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
- The user says "do not change", "good enough", "leave it as is"
- Two consecutive iterations show no clear improvement
- Risk of breaking the existing workflow outweighs the benefit

On stop, return a short summary: what was tested, why no change was saved, and what would trigger a new iteration later.

## Wiki Templates (Optional)

Templates from vault (not local registry files):

1. Ensure `llm_wiki_integration.enabled`
2. `pen_paper_wiki_template` → `load_template`
3. Create a normal Pen & Paper workspace with `action=create` and paste the returned `session_payload` or selected notes into `content`

For vault editing — `llm-wiki` skill; for local templates — this reference.

## See Also

- [Starter workflow template](workflow-template.md)
- [Registry & file layout](workflow-registry.md)
- Foundational skill: [`pen-and-paper`](../../pen-and-paper/SKILL.md)
