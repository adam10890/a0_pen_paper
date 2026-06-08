# Pen & Paper + Workflows — Phase 1 Specification

Specification documents (no plugin code changes in this phase). Created per architecture plan 2026-05-27.

**Language policy:** All docs and agent prompts in this folder are **English only**.

## Start here

| Document | Contents |
|----------|----------|
| **[AGENT_HANDOFF.md](AGENT_HANDOFF.md)** | **Master doc for agents — read first** |
| **[VERIFICATION_CHECKLIST.md](VERIFICATION_CHECKLIST.md)** | **Full test plan (Tiers A–F)** |

**Quick verify:**

```powershell
python usr/plugins/a0_pen_paper/scripts/verify_pen_paper_setup.py
```

## Document map

| Document | Contents |
|----------|----------|
| [ENV_BASELINE.md](ENV_BASELINE.md) | Environment verification, config, broken registry |
| [AGENT_ZERO_QUESTIONS.md](AGENT_ZERO_QUESTIONS.md) | Copy-paste prompt for Agent Zero |
| [AGENT_ZERO_RESPONSES.md](AGENT_ZERO_RESPONSES.md) | Agent Zero UX findings |
| [CONTRACT.md](CONTRACT.md) | WD ↔ P&P ↔ SKILL contract |
| [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) | What shipped vs deferred |
| [CURSOR_CLAUDE_PORTING.md](CURSOR_CLAUDE_PORTING.md) | Porting to Cursor / Claude Code |
| [WAVE0_SPEC.md](WAVE0_SPEC.md) | Registry fix + version |
| [WAVE1_SPEC.md](WAVE1_SPEC.md) | Config + documentation |
| [WAVE2_SPEC.md](WAVE2_SPEC.md) | execution_log + schema + promotion |
| [WAVE3_SPEC.md](WAVE3_SPEC.md) | Orchestrator — option A (P&P executor) |
| [LIVE_SESSION_VIEW_SPEC.md](LIVE_SESSION_VIEW_SPEC.md) | **Live view** — see/copy/edit agent session from Workflows Canvas (Wave 4) |
| [FLOWFORGE_INTEGRATION.md](FLOWFORGE_INTEGRATION.md) | FlowForge-style `.drawio` diagram exporter for templates and sessions |

## Recommended execution order

1. Fill in `AGENT_ZERO_RESPONSES.md`
2. Wave 0 → 1 → 2 → 3
3. Cross-model UAT (see PORTING)

## Relevant code

- `usr/plugins/a0_pen_paper/`
- `usr/pen_and_paper/`
