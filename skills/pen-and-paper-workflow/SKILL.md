---
name: pen-and-paper-workflow
description: >
  Deterministic workflow execution and template authoring for Pen & Paper. Use for
  multi-step planning, research, debugging, audit, state tracking, or editing the
  workflow templates that the agent and Canvas share.
version: 2.0.0
author: frantz
tags: [pen-paper, workflow, deterministic, sessions, templates, canvas]
trigger_patterns:
  - "plan"
  - "analyze"
  - "audit"
  - "debug"
  - "research"
  - "workflow template"
  - "edit workflow"
  - "template_registry"
  - "knowledge/workflows"
  - "create_template"
  - "edit_template"
  - "use_template"
  - "phases triggers"
  - "Canvas workflows"
  - "build workflow"
  - "co-design workflow"
  - "stop_no_change"
  - "iterative workflow"
priority: 2
---

# Pen & Paper Workflow Skill (HOW)

> **Routing.** Foundational rules and lifecycle → [`pen-and-paper`](../pen-and-paper/SKILL.md).
> Deterministic multi-step execution and template authoring → this skill.

## Purpose

Use Pen & Paper only as a **runtime workspace** for multi-step work. Do not treat
it as the policy engine — templates and registry live in the Workflow Dashboard.

## Activation Rules

Use when the task requires more than 3 steps, multiple tools, planning, debugging,
audit, research, state tracking, **or editing a workflow template** (the same skill
covers both running and authoring — the contract is the same).

Do **not** use for simple one-shot answers.

## Required Sequence (execution)

1. Identify task type: planning, research, debugging, audit, implementation, validation.
2. **`skills_tool:load`** the required domain skill (or this skill) **before** creating a Pen & Paper session.
3. `pen_paper` → `list_templates` if template name is unknown.
4. `pen_paper` → `use_template` or `create` with a deterministic session name.
5. Use **only** these sections: `findings`, `results`, `insights`, `notes`, `decisions`, `backtrack`, `execution_log`.
6. If a workflow template is required, load it before the first `update`.
7. If the template is missing, record the failure in `backtrack` and continue with `session` or a generic plan.
8. `pen_paper` → `update` after each major step; for step tracking use `execution_log` with JSON: `{"step_id":"...", "status":"running|done|failed"}`.
9. `pen_paper` → `read` before the final response.
10. `pen_paper` → `close` unless the task explicitly remains open.

## Failure Handling

- If a tool call fails, write the failure to `backtrack`.
- Do not invent section names.
- Do not invent missing templates.
- If config and runtime behavior disagree, follow actual tool behavior and note the contradiction in `backtrack`.
- Status values: `pending`, `running`, `done`, `failed`, `skipped` — never `COMPLETED`.

## Output Contract

Final response must include:

- What was done
- What evidence was collected
- What remains open
- Recommended next step

## Promotion Rule

Promote to a dedicated skill only after at least two successful runs and one
documented test matrix (`workflow_to_skill` template).

## Template Authoring

When the task is to create, edit, or manage workflow templates (the same files
edited in the Canvas UI), follow [`references/template-authoring.md`](references/template-authoring.md).
That page covers `create_template` / `edit_template` / `delete_template` /
`use_template`, the `template_registry.json` shape, the co-design protocol, the
iterative-improvement stop gate, and the optional wiki-template path.

## References

- [Template authoring (CRUD + Canvas + co-design)](references/template-authoring.md)
- [Starter workflow template](references/workflow-template.md)
- [Registry & file layout](references/workflow-registry.md)
- Foundational skill: [`pen-and-paper`](../pen-and-paper/SKILL.md)
- Machine-readable rules: [`data/config/rules.yaml`](../../data/config/rules.yaml) (`execution_contract`)
