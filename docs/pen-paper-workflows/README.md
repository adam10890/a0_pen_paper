# Pen & Paper + Workflows — Phase 1 Specification

Specification documents (no plugin code changes in this phase). Created per architecture plan 2026-05-27.

**Language policy:** All docs and agent prompts in this folder are **English only**.

## Document map

| Document | Contents |
|----------|----------|
| [ENV_BASELINE.md](ENV_BASELINE.md) | Environment verification, config, broken registry |
| [AGENT_ZERO_QUESTIONS.md](AGENT_ZERO_QUESTIONS.md) | Copy-paste prompt for Agent Zero |
| [AGENT_ZERO_RESPONSES.md](AGENT_ZERO_RESPONSES.md) | Placeholder for Agent Zero answers |
| [CONTRACT.md](CONTRACT.md) | WD ↔ P&P ↔ SKILL contract |
| [CURSOR_CLAUDE_PORTING.md](CURSOR_CLAUDE_PORTING.md) | Porting to Cursor / Claude Code |
| [WAVE0_SPEC.md](WAVE0_SPEC.md) | Registry fix + version |
| [WAVE1_SPEC.md](WAVE1_SPEC.md) | Config + documentation |
| [WAVE2_SPEC.md](WAVE2_SPEC.md) | execution_log + schema + promotion |
| [WAVE3_SPEC.md](WAVE3_SPEC.md) | Orchestrator — option A (P&P executor) |

## Recommended execution order

1. Fill in `AGENT_ZERO_RESPONSES.md`
2. Wave 0 → 1 → 2 → 3
3. Cross-model UAT (see PORTING)

## Relevant code

- `usr/plugins/a0_pen_paper/`
- `usr/pen_and_paper/`
