# Workflow Registry & Files

## Layout

```text
usr/pen_and_paper/knowledge/workflows/
├── template_registry.json
├── session.md              # built-in default
├── my_custom.md
└── ...

usr/pen_and_paper/_archived/templates/
└── deleted_template.md     # after delete_template
```

## `template_registry.json` schema

### `templates.<name>`

| Key | Type | Required |
|-----|------|----------|
| `file` | string | yes — usually `<name>.md` |
| `description` | string | recommended |
| `description_he` | string | optional |
| `phases` | string[] | recommended — drives UI + suggestions |
| `triggers` | string[] | recommended — substring match on task name |

### `base_workflows`

Optional sub-flow hints (not separate files required):

```json
"base_workflows": {
  "list": ["research", "debugging", "validation"],
  "hooks": {
    "on_unknown": "research",
    "on_stuck": "debugging",
    "on_error": "debugging",
    "on_complete": "validation"
  }
}
```

## Agent vs human edits

| Channel | Mechanism |
|---------|-----------|
| Agent | `pen_paper` `create_template` / `edit_template` / `delete_template` |
| Human | Canvas **Workflows** panel or direct file edit (prefer Save via UI for registry sync) |
| API | `POST /plugins/a0_pen_paper/workflows_*` |

Always keep **registry entry** and **`.md` file** in sync. The tool and API do both on save.

## Built-in protection

- `session` — default template; do not `delete_template`
- Names must match `^[a-z0-9_]+$`

## Seed / repair

If registry or `session.md` missing:

```bash
python usr/plugins/a0_pen_paper/execute.py install
# or
python usr/plugins/a0_pen_paper/execute.py repair
```
