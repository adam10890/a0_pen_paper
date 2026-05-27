---
name: pen-and-paper-workflow
description: >
  Deterministic workflow execution using Pen & Paper as runtime state and Workflow
  Dashboard as policy controller. Use for multi-step planning, research, debugging,
  audit, or state tracking.
version: 1.0.0
author: frantz
tags: [pen-paper, workflow, deterministic, sessions]
trigger_patterns:
  - "plan"
  - "analyze"
  - "audit"
  - "debug"
  - "research"
  - "structured thinking"
  - "pen and paper"
priority: 2
---

# Pen & Paper Workflow Skill

## Purpose

Use Pen & Paper only as a **runtime workspace** for multi-step work. Do not treat it as the policy engine — templates and registry live in the Workflow Dashboard.

## Activation Rules

Use when the task requires more than 3 steps, multiple tools, planning, debugging, audit, research, or state tracking.

Do **not** use for simple one-shot answers.

## Required Sequence

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

Promote to a dedicated skill only after at least two successful runs and one documented test matrix (`workflow_to_skill` template).
