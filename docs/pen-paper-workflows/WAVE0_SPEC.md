# Wave 0 — Data Fix (Registry)

**Dependencies:** None (before Waves 1–3)  
**Goal:** Consistent registry; hooks point only to existing templates; template version field.

---

## Problem

[`template_registry.json`](../../usr/pen_and_paper/knowledge/workflows/template_registry.json) defines:

- `templates`: `session`, `workflow_to_skill` (files exist)
- `base_workflows.list` + `hooks`: `research`, `debugging`, `validation` (**no MD files**)

---

## Options (decision required)

| Option | Action | Pros | Cons |
|--------|--------|------|------|
| **A — Create templates** | Add `research.md`, `debugging.md`, `validation.md` + registry entries | Hooks work immediately | Maintain 3 templates |
| **B — Shrink hooks** | Remove/repoint hooks to `session` or empty | Minimal | Loses on_stuck policy |
| **C — Hybrid** | Create 3 minimal skeletons from `session.md` | Balanced | One-time work |

**Specification recommendation:** **C** — short skeletons + minimal phases/triggers.

---

## Detailed tasks

### W0-1: Add `version` to registry

```json
"session": {
  "version": "1.0.0",
  ...
}
```

- Update `workflows_store.py` / `create_template` / `edit_template` to persist `version` (optional, default `1.0.0`).
- `use_template` / `create` — set `template_version` in `workspace.metadata`.

### W0-2: Missing templates (if option C)

For each name in `base_workflows.list`:

1. Create `usr/pen_and_paper/knowledge/workflows/<name>.md` from a shortened `session.md`.
2. Add a `templates` entry with sensible phases/triggers.

**research:** phases `Gather`, `Synthesize`, `Report`  
**debugging:** phases `Reproduce`, `Isolate`, `Fix`, `Verify`  
**validation:** phases `Define criteria`, `Run checks`, `Sign-off`

### W0-3: Validation in `workflows_store`

- Add `validate_registry_integrity()`:
  - Every `templates[*].file` exists on disk
  - Every value in `base_workflows.hooks` exists in `templates`
- Call from `execute.py validate` and optionally from `workflows_save` (warn vs block).

### W0-4: Seed in `hooks.py` install

- Update default registry in plugin `data/` so fresh installs are not broken.

---

## Files to change

| File | Change |
|------|--------|
| `usr/pen_and_paper/knowledge/workflows/template_registry.json` | templates + version |
| `usr/pen_and_paper/knowledge/workflows/*.md` | 3 new files (if C) |
| `usr/plugins/a0_pen_paper/helpers/workflows_store.py` | integrity + version |
| `usr/plugins/a0_pen_paper/tools/pen_paper.py` | metadata.template_version |
| `usr/plugins/a0_pen_paper/hooks.py` | seed |

---

## Acceptance tests

- [ ] `python usr/plugins/a0_pen_paper/execute.py validate` passes
- [ ] No hook points to a name without MD
- [ ] `list_templates` lists all `base_workflows.list` entries
- [ ] `use_template` on `debugging` creates a session with phases in notes

---

## Out of scope for Wave 0

- `pen_paper` default changes (Wave 1)
- `execution_log` (Wave 2)
- Orchestrator (Wave 3)
