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
  For `update`, use exactly one of `findings`, `results`, `insights`, `notes`,
  `decisions`, `backtrack`, `execution_log`. These seven are the complete set.
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

#### Required sequence (multi-step work)

Follow this order every time. It is what makes the result the same regardless of
which model is running.

1. `create` (or `use_template`) with a deterministic workspace name.
2. `update` after each major step, into one of the seven sections above.
3. For step tracking, `update` `section: "execution_log"` with a JSON object:
   `{"step_id": "<stable id>", "status": "pending|running|done|failed|skipped"}`.
4. `read` before writing your final answer.
5. `close` unless the task deliberately stays open.

#### Hard rules

- Use only the seven section names listed above. **Never invent a section name.**
- Step status is one of `pending`, `running`, `done`, `failed`, `skipped`.
  **Never use `COMPLETED`** — `done` is the only success value.
- Reuse the same `step_id` for the same step; a step already `done` or `failed`
  is not re-run.
- If a tool call fails or a template is missing, record it in `backtrack` and
  continue. Do not invent templates.
- Terminal output alone does not complete a step — the `execution_log` update does.

#### Guidance

Use Pen & Paper for tasks with meaningful state across multiple steps. Avoid
using it for simple one-shot answers. Keep updates concise and only record
information that helps continue or audit the task.

For anything beyond the schema and rules above (lifecycle, splitting, archiving,
interaction with `llm_wiki`), consult `data/templates/_start_here.md` and
`data/templates/_index.md` — that's where the methodology lives.
