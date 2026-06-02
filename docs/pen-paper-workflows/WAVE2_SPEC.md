# Wave 2 — execution_log, Schema, Promotion

**Dependencies:** Wave 0 (registry), Wave 1 (config)  
**Goal:** Step tracking in workspace; template validation; SKILL path with eval.

---

## W2-1: `execution_log` in P&P

### Change `pen_paper.py`

```python
VALID_SECTIONS = [
    "findings", "results", "insights", "notes",
    "decisions", "backtrack", "execution_log",
]
```

### New actions (optional)

- `action: log_step` — `step_id`, `status`, `note`
- Or: `update` with `section: execution_log` and structured JSON

### Rules (implement `execution_contract`)

- Step is `done` only after required section `update`s
- Do not re-run `step_id` with status `done` / `failed`
- Statuses: `pending`, `running`, `done`, `failed`, `skipped` (not `COMPLETED`)

### Update `rules.yaml`

- Replace `COMPLETED` → `done`
- `enforcement`: `pen_paper.py` + (future) pre-tool extension

---

## W2-2: JSON Schema for templates

### Target file

`usr/plugins/a0_pen_paper/schemas/template_registry.schema.json`

- `templates.*`: required `file`, `description`, `phases` (array), `triggers` (array)
- `version`: semver pattern
- `base_workflows.hooks`: values ⊆ keys of `templates`

### Integration

- `workflows_save`, `workflows_create`, `create_template`, `edit_template` — validate before write
- Clear errors for agent + UI toast

---

## W2-3: Phase completion

- WD: optional `phase_schema` per template (required_sections per phase)
- P&P: on `use_template`, inject checklist + `step_id` per phase
- SKILL: "before phase [x] — log_step running → updates → log_step done"

---

## W2-4: Promotion via `a0_skill_creator`

### Flow

1. Complete `workflow_to_skill` in P&P
2. Run skill-creator with:
   - Source: template MD + session summary
   - Target: `usr/plugins/a0_pen_paper/skills/<new-skill>/` or `usr/workdir/skills/`
3. Eval: trigger phrases (multilingual as needed)
4. `stop_no_change` on WD template

### Deliverables

- `SKILL.md` with explicit tool sequence
- `references/` with example payloads
- Optional `promoted_skills` entry in registry

---

## W2-5: Tests

| Type | Description |
|------|-------------|
| Unit | `validate_registry_integrity`, schema validator |
| Integration | create → update execution_log → close |
| Manual | workflow_to_skill → skill_creator → skills_tool:search |

---

## Out of scope for Wave 2

- Automatic hook execution (Wave 3)
- Full SmartRouter

---

## Acceptance tests

- [ ] `execution_log` persisted in workspace.json
- [ ] Re-running a `done` step is rejected or logged
- [ ] Invalid registry blocked on save
- [ ] New skill passes basic skill_creator eval
