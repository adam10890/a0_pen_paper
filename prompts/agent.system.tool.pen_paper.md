### pen_paper

Structured working-notes tool for complex tasks. Use it as a scratchpad for
multi-step reasoning, implementation plans, findings, decisions, results, and
backtrack items.

**First use in a session:** read `data/templates/_start_here.md`. It is the
operating manual (~80 lines) and points you to `_index.md` for everything
else. Do not skip it.

#### Arguments

- `action`: `create`, `update`, `read`, `close`, `list`, `help`,
  `list_templates`, `create_template`, `edit_template`, `delete_template`,
  `use_template`
- `name`: workspace name
- `section`: optional for `read`; if omitted, `read` returns the full workspace summary.
  For `update`, use one of `findings`, `results`, `insights`, `notes`, `decisions`, `backtrack`.
- `content`: text to add to a section
- `template`: optional template name for `create`
- `template_name`: template name for template actions
- `ephemeral`: delete source session on close when possible
- `retrieve_context`: retrieve similar previous sessions if available
- `vectorize`: vectorize the session on close if vector support exists

#### Basic usage

Create a workspace:

```json
{"tool_name":"pen_paper","tool_args":{"action":"create","name":"task_name"}}
```

Add a finding:

```json
{"tool_name":"pen_paper","tool_args":{"action":"update","name":"task_name","section":"findings","content":"discovered fact"}}
```

Record a decision:

```json
{"tool_name":"pen_paper","tool_args":{"action":"update","name":"task_name","section":"decisions","content":"decision and rationale"}}
```

Read a workspace:

```json
{"tool_name":"pen_paper","tool_args":{"action":"read","name":"task_name"}}
```

Close a workspace:

```json
{"tool_name":"pen_paper","tool_args":{"action":"close","name":"task_name","vectorize":true}}
```

List active workspaces:

```json
{"tool_name":"pen_paper","tool_args":{"action":"list"}}
```

#### Guidance

Use Pen & Paper for tasks with meaningful state across multiple steps. Avoid
using it for simple one-shot answers. Keep updates concise and only record
information that helps continue or audit the task.

For anything beyond the schema above (rules, lifecycle, splitting, archiving,
interaction with `llm_wiki`), consult `data/templates/_start_here.md` and
`data/templates/_index.md` — that's where the methodology lives.
