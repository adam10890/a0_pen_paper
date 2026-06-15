# Workflow Template — Starter (copy for `create_template`)

Replace bracketed placeholders. Keep phase headings consistent so `use_template` maps cleanly to workspace sections.

---

# [WORKFLOW_TITLE]

> **Purpose:** [One sentence — what this workflow is for]

**Phases:** [Phase 1] → [Phase 2] → [Phase 3]

---

## Phase 1: [PHASE_NAME]

### Objective

- [What must be true before leaving this phase]

### Notes

- 

### Checklist

- [ ] 

---

## Phase 2: [PHASE_NAME]

### Objective

- 

### Notes

- 

---

## Phase 3: [PHASE_NAME]

### Objective

- 

### Notes

- 

---

## Completion

**Done when:**

- [ ] [Criterion 1]
- [ ] [Criterion 2]

**Handoff to Pen & Paper sections:**

| Phase content | Maps to workspace `section` |
|---------------|----------------------------|
| Facts discovered | `findings` |
| Choices made | `decisions` |
| Items to revisit | `backtrack` |
| Finished outputs | `results` |
| Patterns learned | `insights` |

---

## Registry metadata (for `create_template`)

| Field | Example |
|-------|---------|
| `template_name` | `my_workflow` |
| `description` | Short English description |
| `description_he` | תיאור קצר בעברית |
| `phases` | `["Plan", "Execute", "Review"]` |
| `triggers` | `["planning", "תכנון", "my_workflow"]` |

Variables in body: `{{PROJECT}}`, `{{OWNER}}` — substituted in `use_template`.
