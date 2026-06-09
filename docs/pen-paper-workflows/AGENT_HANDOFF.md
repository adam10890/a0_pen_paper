# Agent Handoff — Pen & Paper + Workflow Dashboard

**Read this first.** Local master doc for humans and AI agents working on this system.  
**Last updated:** 2026-05-27  
**Status:** Waves 0–3 implemented locally; branch pushed to GitHub.

---

## 1. What this project is

We strengthened **Pen & Paper (P&P)** and the **Workflow Dashboard (WD)** so workflows behave more **predictably across different LLM models**.

| System | Role | Analogy |
|--------|------|---------|
| **Workflow Dashboard** | Templates, phases, triggers, config UI, Canvas editor | Policy + contract design |
| **Pen & Paper** | Live sessions (`workspace.json`), tool execution | Runtime / workspace |
| **SKILL.md** | Stable behavior after a workflow is proven | Production instructions for any agent |

**Design rule:** Prototype in P&P → stabilize → promote to SKILL → optional copy to Cursor (`.cursor/skills/`).

---

## 2. Where everything lives (local)

**Workspace root:** `c:\Users\frant\agent-zero\agent-zero-2\`  
(Cursor may open `agent-zero` parent — code is under `agent-zero-2`.)

| What | Path |
|------|------|
| Plugin code | `usr/plugins/a0_pen_paper/` |
| Runtime data (sessions, registry) | `usr/pen_and_paper/` |
| Template registry | `usr/pen_and_paper/knowledge/workflows/template_registry.json` |
| Template bodies | `usr/pen_and_paper/knowledge/workflows/*.md` |
| All documentation | `docs/pen-paper-workflows/` |
| Phase 1 artifacts (Agent Zero) | `usr/workdir/pen_paper_phase1_artifacts/` |
| Git clone for plugin only | `c:\Users\frant\agent-zero\a0_pen_paper-repo\` |

---

## 3. GitHub

| Item | Value |
|------|--------|
| Repository | https://github.com/adam10890/a0_pen_paper |
| Development branch | `develop/pen-paper-workflows` |
| Default branch | `main` |
| Open PR | https://github.com/adam10890/a0_pen_paper/pull/new/develop/pen-paper-workflows |

**Note:** The Cursor workspace folder is not a git repo. Plugin changes are committed on `a0_pen_paper` repo.

---

## 4. What was implemented (Waves 0–3)

### Wave 0 — Registry integrity
- Added templates: `research`, `debugging`, `validation` (+ `.md` files).
- Added `version` on registry entries.
- `validate_registry_integrity()` in `helpers/workflows_store.py`.

### Wave 1 — Config + documentation
- `pen_paper.py` reads `load_plugin_config()` / `feature_enabled()` (no hardcoded `True`).
- Unified `features.retrieve_context_on_create`, `features.vectorize_on_close`.
- Fixed SKILL API paths to `/plugins/a0_pen_paper/...`.

### Wave 2 — execution_log + canonical skill
- New section: `execution_log` in workspace.
- `rules.yaml` uses status `done` (not `COMPLETED`).
- New skill: `skills/pen-and-paper-workflow/SKILL.md`.

### Wave 3 — WorkflowExecutor
- `helpers/workflow_executor.py` — hooks, idempotency, registry checks.
- Pre-checks on `update` / `close` in `pen_paper.py`.
- Extension: `extensions/python/tool_execute_before/_50_pen_paper_workflow_guard.py`.

**Detail:** [`IMPLEMENTATION_STATUS.md`](IMPLEMENTATION_STATUS.md)

---

## 5. Architecture (short)

```
User / Agent
    │
    ├─► Workflow Dashboard (Canvas + config.html)
    │       └─► template_registry.json + *.md templates
    │
    ├─► skills_tool:load (pen-and-paper-workflow recommended)
    │
    └─► pen_paper tool
            └─► workspace.json (findings, results, execution_log, …)
```

**Contract between WD and P&P:** [`CONTRACT.md`](CONTRACT.md)

**Not implemented yet:** Full orchestrator auto-running hooks; Canvas etag; vectorizer; context_loader.

---

## 6. Skills — which to load when

| Skill | When to load |
|-------|----------------|
| `pen-and-paper-workflow` | Multi-step tasks; deterministic workflow execution |
| `pen-and-paper` | General P&P session methodology |
| `pen-paper-workflows` | Editing templates / Canvas / registry |

**Always:** `skills_tool:load` **before** opening a P&P session (BMAD-style), do not rely on triggers alone.

---

## 7. Key tool sequence (copy for agents)

```
1. skills_tool:load → pen-and-paper-workflow
2. pen_paper → list_templates (if needed)
3. pen_paper → use_template (template_name, name, variables)
4. pen_paper → update (section: findings|results|…|execution_log)
5. pen_paper → read (before final answer)
6. pen_paper → close (vectorize/ephemeral per policy)
```

**execution_log JSON example:**

```json
{"step_id": "phase_1_gather", "status": "done"}
```

Valid statuses: `pending`, `running`, `done`, `failed`, `skipped`.

---

## 8. Configuration (important)

| Source | Purpose |
|--------|---------|
| `usr/plugins/a0_pen_paper/config.json` | Plugin settings |
| `webui/config.html` | UI toggles for features |
| `tools/_config.py` | Code defaults + legacy key migration |

**Defaults (when tool args omit flags):**

- `retrieve_context_on_create`: **false**
- `vectorize_on_close`: **false**

Do not assume vectorize/retrieve are on — check config.

---

## 9. Verification — run before claiming "done"

1. **Automated:** `python usr/plugins/a0_pen_paper/scripts/verify_pen_paper_setup.py`
2. **Full checklist:** [`VERIFICATION_CHECKLIST.md`](VERIFICATION_CHECKLIST.md)
3. **Plugin validate:** `python usr/plugins/a0_pen_paper/execute.py validate`

---

## 10. Document map (read as needed)

| Document | Use when |
|----------|----------|
| **AGENT_HANDOFF.md** (this file) | Onboarding any agent |
| [VERIFICATION_CHECKLIST.md](VERIFICATION_CHECKLIST.md) | Testing / sign-off |
| [CONTRACT.md](CONTRACT.md) | Data contracts, promotion rules |
| [ENV_BASELINE.md](ENV_BASELINE.md) | Environment audit snapshot |
| [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) | What shipped vs deferred |
| [AGENT_ZERO_RESPONSES.md](AGENT_ZERO_RESPONSES.md) | Live UX findings from Agent Zero |
| [CURSOR_CLAUDE_PORTING.md](CURSOR_CLAUDE_PORTING.md) | Copy skills to Cursor/Claude |
| [WAVE0_SPEC.md](WAVE0_SPEC.md) … [WAVE3_SPEC.md](WAVE3_SPEC.md) | Implementation specs |
| [LIVE_SESSION_VIEW_SPEC.md](LIVE_SESSION_VIEW_SPEC.md) | Live agent session mirror in Workflows Canvas (Wave 4 — spec only) |
| [README.md](README.md) | Index of all docs |

---

## 11. Rules for agents editing this system

1. **English only** for new docs and prompts for other agents.
2. **Do not** break registry integrity — every hook target must have a template + `.md` file.
3. **Do not** reintroduce `COMPLETED` — use `done`.
4. **Minimize scope** — P&P plugin changes stay in `a0_pen_paper`; runtime user data in `usr/pen_and_paper/` is not always committed.
5. **Test** with `verify_pen_paper_setup.py` before push.
6. **Branch** for GitHub work: `develop/pen-paper-workflows` (or new feature branch off it).
7. **Two entities:** WD edits templates; P&P runs sessions — do not merge responsibilities in prose or code without updating CONTRACT.md.

---

## 12. Known gaps (do not assume they work)

| Gap | Workaround |
|-----|------------|
| `pen_paper_vectorizer` missing | vectorize fails silently; keep `vectorize_on_close: false` |
| `context_loader` not implemented | Ignore config flag |
| Canvas/agent race on same template | Avoid parallel edit; etag not built |
| Cross-model UAT | Run Tier E in VERIFICATION_CHECKLIST |
| SmartRouter disabled | Use WorkflowExecutor in P&P only |

---

## 13. How to stay updated

1. Read **IMPLEMENTATION_STATUS.md** after each work session.
2. Append results to **VERIFICATION_CHECKLIST.md** sign-off section.
3. If Agent Zero discovers new behavior, add to **AGENT_ZERO_RESPONSES.md** and update CONTRACT §7.
4. After code changes: commit to `a0_pen_paper` branch and note commit hash here:

| Date | Commit / note |
|------|----------------|
| 2026-05-27 | `42040e1` on `develop/pen-paper-workflows` — Waves 0–3 initial |
| 2026-05-28 | Verification Tier A/C PASS; Tier B B2 (yaml) fixed; Wave 4 Live Session implemented |

---

## 14. Quick commands reference

```powershell
# From agent-zero-2/
python usr/plugins/a0_pen_paper/scripts/verify_pen_paper_setup.py
python usr/plugins/a0_pen_paper/execute.py status
python usr/plugins/a0_pen_paper/execute.py validate
python -c "from usr.plugins.a0_pen_paper.helpers.workflows_store import validate_registry_integrity; print(validate_registry_integrity())"
```

Inside Agent Zero (Docker `/a0`):

```bash
python usr/plugins/a0_pen_paper/execute.py validate
```

---

## 15. Contact / ownership

- Plugin author (manifest): frantz  
- GitHub: adam10890/a0_pen_paper  
- Phase 1 investigation chat: P&P Analysis (`jpdsS7u1` in agent-zero-2 usr/chats)

When handing off to **Cursor** or **Claude Code**, also send: [CURSOR_CLAUDE_PORTING.md](CURSOR_CLAUDE_PORTING.md).
