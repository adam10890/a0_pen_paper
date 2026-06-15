# Porting Map: Agent Zero → Cursor / Claude Code

**Goal:** Predictable behavior across models and environments. Agent Zero SKILL files are **not** loaded automatically in Cursor.

---

## 1. Paths

| Environment | Repo root | P&P plugin | Runtime |
|-------------|-----------|------------|---------|
| Agent Zero | `agent-zero-2/` | `usr/plugins/a0_pen_paper/` | `usr/pen_and_paper/` |
| Cursor (local) | `.cursor/skills/<skill-name>/SKILL.md` | — | — |
| Claude Code | `.claude/skills/` or project | — | — |

---

## 2. What to copy / what not to copy

| Source | Copy to Cursor? | Notes |
|--------|-----------------|-------|
| `skills/pen-and-paper/SKILL.md` | Yes (abbreviated) | Remove `pen_paper` dependency if the tool is unavailable |
| `skills/pen-and-paper-workflow/SKILL.md` + `references/template-authoring.md` | Yes — covers both execution and template editing | Fix API paths to `/plugins/...` only if A0 server exists |
| `knowledge/workflows/*.md` | Yes as helper files | Or embed in SKILL |
| `template_registry.json` | Yes (read-only ref) | Cursor does not run Canvas |
| `rules.yaml` execution_contract | Yes as SKILL rules | After Wave 2 — use status `done` |
| `pen_paper.py` | No | Replace with markdown files / TodoWrite in Cursor |

---

## 3. Recommended Cursor SKILL template

```markdown
---
name: my-stable-workflow
description: >
  One-line trigger description. Use when user asks for X, Y, Z.
---

# My Stable Workflow

## Triggers
- phrase one
- phrase two

## Preconditions
- [ ] List templates / read registry if in A0
- [ ] Load this skill (Cursor: automatic when matched)

## Steps (fixed order)
1. ...
2. ...

## Tool mapping (Agent Zero only)
| Step | tool_name | tool_args |
|------|-----------|-----------|
| Open session | pen_paper | action=use_template, ... |

## Cursor equivalent
| Step | Action |
|------|--------|
| Open session | Create/update `docs/workflow-session.md` from template |

## Output contract
Required sections / JSON shape at end.

## Forbidden
- Do not skip step N
- Do not mark phase complete without updating section X
```

---

## 4. Tool mapping

| Agent Zero | Cursor (no pen_paper) |
|------------|-------------------------|
| `pen_paper` create/update/close | Project markdown file + git |
| `use_template` + `{{VAR}}` | Copy template + search-replace |
| `list_templates` | Read `template_registry.json` |
| `workflows_save` (Canvas) | Manual MD + JSON edit |
| `skills_tool:load` | Cursor skill auto-load |
| `pen_paper_wiki_template` | Manual vault read / MCP if available |

---

## 5. Recommended promotion path

1. Stabilize in A0: P&P + WD (`stop_no_change`)
2. `workflow_to_skill` or `a0_skill_creator`
3. Export: copy `SKILL.md` + `references/` to `.cursor/skills/<name>/`
4. Add "Cursor equivalent" section
5. UAT: same prompt on small and large models in Cursor

---

## 6. Predictability UAT

| Test | Agent Zero | Cursor |
|------|------------|--------|
| Same trigger | Same template | Same SKILL |
| Same inputs | Same `variables` | Same placeholders |
| Output | workspace sections | Same file structure |
| Step order | Tool log | SKILL checklist |

Optional results doc: `docs/pen-paper-workflows/UAT_CROSS_MODEL.md`.

---

## 7. Source files to read in Cursor

```
agent-zero-2/usr/plugins/a0_pen_paper/tools/pen_paper.py
agent-zero-2/usr/plugins/a0_pen_paper/helpers/workflows_store.py
agent-zero-2/usr/pen_and_paper/knowledge/workflows/template_registry.json
agent-zero-2/docs/pen-paper-workflows/CONTRACT.md
```
