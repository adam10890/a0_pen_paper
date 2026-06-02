# Pen & Paper + Workflows — Verification Checklist

**Purpose:** Confirm Waves 0–4 work correctly before merge or production use.  
**Last updated:** 2026-05-28  
**Branch:** `develop/pen-paper-workflows` on [adam10890/a0_pen_paper](https://github.com/adam10890/a0_pen_paper)

---

## How to use this document

1. Run **Tier A** (automated) first — takes ~1 minute.
2. Run **Tier B** (plugin/runtime files) on the machine where Agent Zero lives.
3. Run **Tier C** (Agent Zero tool) inside a running Agent Zero instance.
4. Run **Tier D** (Canvas UI) manually in the browser.
5. Run **Tier G** (Live Session) after Wave 4 is deployed.
6. Run **Tier E** (cross-model) when you need predictability proof.

Mark each item: `PASS` / `FAIL` / `SKIP` (with reason).

**Agent Zero run artifact (2026-05-28):**  
`usr/workdir/pen_paper_phase1_artifacts/tier_ab_verification_20260528_210856.log`

---

## Tier A — Automated (no Agent Zero required)

Run from repo root `agent-zero-2/`:

```powershell
cd c:\Users\frant\agent-zero\agent-zero-2
python usr/plugins/a0_pen_paper/scripts/verify_pen_paper_setup.py
```

| # | Check | Expected |
|---|--------|----------|
| A1 | Script exits 0 | All checks green |
| A2 | `py_compile` on core Python files | No syntax errors |
| A3 | `validate_registry_integrity()` | Empty list (no errors) |
| A4 | All `base_workflows.hooks` targets have `.md` files | research, debugging, validation exist |
| A5 | `execution_log` in `VALID_SECTIONS` | Present in `pen_paper.py` |
| A6 | `config.json` uses `features.*` keys | No orphan `vectorize_by_default` at root (or migrated) |
| A7 | `workflow_executor.py` importable | No import errors |
| A8 | `sessions_store` + session API modules exist | Wave 4 files present |

**Pass criteria:** Tier A = 8/8 PASS.

**Recorded (2026-05-28, Agent Zero Docker):** 8/8 PASS

---

## Tier B — Plugin install & runtime files

```powershell
cd c:\Users\frant\agent-zero\agent-zero-2
python usr/plugins/a0_pen_paper/execute.py status
python usr/plugins/a0_pen_paper/execute.py validate
```

| # | Check | Expected | Recorded |
|---|--------|----------|----------|
| B1 | `execute.py status` | Runtime dir exists; session.md + template_registry.json present | PASS |
| B2 | `execute.py validate` | Core plugin files OK; registry integrity OK | FAIL (pre-fix: no yaml); **re-test after Wave 4** |
| B3 | `template_registry.json` | Contains session, workflow_to_skill, research, debugging, validation | PASS |
| B4 | Each template has `version` field | e.g. `"version": "1.0.0"` | PASS |
| B5 | `rules.yaml` execution_contract | Uses `done` not `COMPLETED`; enforcement points to pen_paper/workflow_executor | PASS |
| B6 | Skills exist | `pen-and-paper`, `pen-paper-workflows`, `pen-and-paper-workflow` | PASS |

**Optional fresh install test** (destructive to runtime — use test copy only):

```powershell
python usr/plugins/a0_pen_paper/execute.py install
```

| # | Check | Expected |
|---|--------|----------|
| B7 | After install | `data/workflows/*.md` seeded; registry not broken; PyYAML installed if missing |

**Pass criteria:** Tier B = 6/6 PASS (B7 optional).

**Recorded (2026-05-28):** 5/6 PASS (B2 failed before PyYAML fix).

---

## Tier C — Agent Zero tool smoke test

**Prerequisites:** Plugin `a0_pen_paper` enabled for the agent; Agent Zero running.

| # | Tool call | Expected result | Recorded |
|---|-----------|-----------------|----------|
| C1 | `pen_paper` action=`list_templates` | Lists ≥5 templates | PASS |
| C2 | `use_template` debugging → `verify_debug_001` | Session created; phases in notes | PASS (cosmetic: create msg lacked execution_log before fix) |
| C3 | `update` findings | Success | PASS |
| C4 | `update` execution_log running | Success | PASS |
| C5 | `update` execution_log done | Success | PASS |
| C6 | duplicate done | Rejected (idempotency) | PASS |
| C7 | `read` session | findings + execution_log | PASS |
| C8 | `close` ephemeral, vectorize=false | Session closed/deleted | PASS |
| C9 | `update` after close | Rejected | PASS |
| C10 | config defaults | No vectorization when false | PASS |
| C11 | load `pen-and-paper-workflow` | Skill loads | PASS |
| C12 | load `pen-paper-workflows` | Skill loads | PASS |

**Pass criteria:** Tier C = 12/12 PASS.

**Recorded (2026-05-28):** 12/12 PASS

---

## Tier D — Workflow Dashboard (Canvas)

| # | Step | Expected |
|---|------|----------|
| D1 | Open Workflows in Canvas | Panel loads without JS errors |
| D2 | Template list shows all registry templates | Including debugging, research, validation |
| D3 | Edit `debugging` description → Save | Saves; registry mtime updates |
| D4 | Reload template | Content persists |
| D5 | Config page toggles `retrieve_context_on_create` | Saves to config.json |
| D6 | Race: agent + Canvas edit same template | Document outcome (template etag still optional) |

---

## Tier G — Live Session (Wave 4)

| # | Step | Expected |
|---|------|----------|
| G1 | Switch to **Live** mode | Active sessions listed |
| G2 | Agent `pen_paper update` with **Follow agent** on | UI selects workspace/section |
| G3 | Preview updates within ~2s poll | Without manual refresh |
| G4 | **Add to session** → `pen_paper read` | New entry with `source: ui` |
| G5 | Append with stale etag (agent updates while typing) | Rejected + stale banner; refresh works |

---

## Tier E — Cross-model predictability (UAT)

Run the **same prompt** on two models:

```
Load skill pen-and-paper-workflow.
Run template "research" as session name uat_research_<model_id>.
Variables: TOPIC="Pen and Paper verification".
Complete phases: one finding per phase, log each phase in execution_log as done, then close ephemeral.
```

| # | Compare | Accept if |
|---|---------|-----------|
| E1 | Tool sequence | Same actions in same order |
| E2 | Sections used | Valid sections; execution_log present |
| E3 | Session closed | Both call close |
| E4 | workspace.json structure | Same keys; execution_log has steps |

Save both `workspace.json` under `docs/pen-paper-workflows/uat-runs/`.

---

## Tier F — GitHub / deployment alignment

| # | Check | Expected |
|---|--------|----------|
| F1 | Branch `develop/pen-paper-workflows` on GitHub | Yes |
| F2 | Local plugin matches branch | Key files same as pushed commit |
| F3 | PR review | No secrets in config.json |

---

## Failure triage quick reference

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Hook points to missing template | Registry not updated | `execute.py install` or merge Wave 0 seed |
| vectorize always True | config not wired | Check `pen_paper.py` uses `load_plugin_config` |
| `execution_log` invalid section | Old plugin code | Pull latest; restart Agent Zero |
| Canvas 404 on API | Wrong path | Use `/plugins/a0_pen_paper/` not `/api/plugins/` |
| Registry integrity errors | MD file missing | Fix hooks in registry |
| Idempotency not enforced | workflow_executor not loaded | Check Docker `/a0` layout |
| `No module named 'yaml'` on validate | PyYAML missing | Reinstall plugin (`hooks.py` installs `requirements.txt`) or `pip install pyyaml>=6.0` |
| Live mode empty | No active sessions | Agent must `create` / `use_template` first |
| sessions_append stale | Agent updated workspace | Click refresh; re-append |

---

## Sign-off template

```
Date: 2026-05-28
Tester: Agent Zero / A0 (+ local Wave 4 implementation)
Environment: Agent Zero Docker /a0 / hostname 3b8a85d9861a
Tier A: 8/8 PASS
Tier B: 5/6 PASS (B2 — re-run after PyYAML fix)
Tier C: 12/12 PASS
Tier D: SKIP — manual Canvas
Tier G: PENDING — after Wave 4 deploy + manual test
Tier E: SKIP
Tier F: SKIP
Overall: PASS WITH NOTES (B2 fixed in code; D/G/E/F pending)
Notes: execute.py validate failed on missing yaml before requirements.txt + hooks.
        C2 cosmetic: create message now lists execution_log (Wave 4 fix).
Artifact: usr/workdir/pen_paper_phase1_artifacts/tier_ab_verification_20260528_210856.log
```
