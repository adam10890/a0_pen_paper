# Agent Zero Questions and Artifacts (copy-paste)

Paste the block below into the Agent Zero chat. Goal: close gaps that code review alone cannot answer (phase 1 specification).

---

## Prompt to paste

```
We are in phase 1 specification for Pen & Paper + Workflow Dashboard (no plugin code changes yet).
Code review found:
- base_workflows.hooks point to research/debugging/validation but there are no MD files
- pen_paper.py: retrieve_context/vectorize default to True; config.html/config.json are not wired to the tool
- execution_contract in rules.yaml is not enforced; SmartRouter is disabled
- COMPLETED in rules vs DONE in WorkflowStepStatus

Please answer briefly and focused on each section, then produce the artifacts at the end.

### Usage experience
1. When do you open a pen_paper session vs only skills_tool:load?
2. pen_paper failures — frequency, recovery, state drift?
3. Canvas Workflows vs create_template — what is missing for "policy"? Parallel editing (user in Canvas while you write to registry)?
4. pen_paper_wiki_template + /data/SharedBrain — does it work in your environment?
5. Did you try base_workflows hooks (on_stuck→debugging)? What happened without debugging.md?

### Determinism
6. Same template + variables on two models — what changed (diff)?
7. skills_tool:load before workflow (BMAD pattern) or trigger only?
8. Minimum SKILL content for cross-model predictability?

### Router / config / contract
9. Was SmartRouter ever active? Step duplication after it was disabled?
10. execution_contract — ignore / interpret / execution_log?
11. COMPLETED vs DONE — which status do you use?
12. Do config.html settings affect your behavior?

### Promotion
13. workflow_to_skill end-to-end — what stays in P&P?
14. Did you use a0_skill_creator?
15. Propose one canonical SKILL.md ready to copy to Cursor
16. plugin_debugger — latest audit findings on a0_pen_paper

### Artifacts (required)
- workspace.json from a successful vs failed session
- Tool call log for one template run
- template_registry.json + which templates are production
- config.json + what appears in the config UI
- "works / broken" table from plugin_debugger on a0_pen_paper
```

---

## How to use responses

1. Save answers in `docs/pen-paper-workflows/AGENT_ZERO_RESPONSES.md` (manual, after the chat).
2. Update [`CONTRACT.md`](CONTRACT.md) — section "Open questions" — close items per answers.
3. Proceed to Wave 0+ only after closing items 5, 12, 13 (hooks, config effect, promotion).
