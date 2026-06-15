### pen_paper_diagram

Generate editable `.drawio` diagrams from Pen & Paper artifacts.

Use this tool when the user asks to visualize a workflow, template, session,
process, architecture sketch, or step sequence as a diagram. The output is a
draw.io XML file, not an interactive whiteboard state.

#### Arguments

- `action`: `generate`, `list_options`, or `help`
- `source_type`: `template`, `session`, or `text`
- `source_id`: source name; aliases: `name`, `template_name`, `workspace`
- `content`: required only for `source_type=text`
- `diagram_type`: `flow`, `flow-vertical`, `layers`, `sequence`, or `timeline`
- `theme`: `tech-blue`, `morandi`, `mint`, `terracotta`, or `indigo`
- `output_name`: optional file stem

#### Usage

Generate from a workflow template:

```json
{"tool_name":"pen_paper_diagram","tool_args":{"source_type":"template","template_name":"debugging","diagram_type":"flow-vertical","theme":"tech-blue"}}
```

Generate from a live Pen & Paper session:

```json
{"tool_name":"pen_paper_diagram","tool_args":{"source_type":"session","name":"my_task","diagram_type":"layers","theme":"mint"}}
```

Generate from text:

```json
{"tool_name":"pen_paper_diagram","tool_args":{"source_type":"text","content":"Plan -> Build -> Verify","diagram_type":"flow"}}
```

#### Guidance

Prefer `template` when the user wants the reusable workflow policy visualized.
Prefer `session` when the user wants the current run/workspace visualized.
Prefer `text` for quick one-off diagrams.

Generated files are stored under the Pen & Paper runtime directory:

- template diagrams: `usr/pen_and_paper/diagrams/templates/<template>/`
- session diagrams: `usr/pen_and_paper/sessions/active/<session>/diagrams/`
- ad hoc diagrams: `usr/pen_and_paper/diagrams/ad_hoc/`

Do not describe the diagram as a whiteboard import unless another tool actually
imports it into the whiteboard.
