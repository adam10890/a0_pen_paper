# Pen & Paper + Workflows — Environment Baseline

**Date:** 2026-05-27  
**Phase:** 1 (specification, no code changes)  
**Repository:** `c:\Users\frant\agent-zero\agent-zero-2\`

---

## 1. Paths

| Item | Path |
|------|------|
| Plugin | `usr/plugins/a0_pen_paper/` |
| Runtime | `usr/pen_and_paper/` |
| Templates | `usr/pen_and_paper/knowledge/workflows/` |
| Phase 1 docs | `docs/pen-paper-workflows/` |

**Note:** The Cursor workspace root may be `agent-zero`; runnable code and runtime live under **`agent-zero-2/`**.

---

## 2. Plugin activation

| Check | Status | Evidence |
|--------|--------|----------|
| `always_enabled` | `false` | [`plugin.yaml`](../../usr/plugins/a0_pen_paper/plugin.yaml) |
| `.toggle-1` / `.toggle-0` | **Not found** under `usr/plugins/a0_pen_paper/` | Directory scan |
| Plugin version | **1.2.0** | `plugin.yaml` |
| CAPABILITIES version | **1.1.2** (stale) | `docs/CAPABILITIES_AND_ROADMAP.md` |

**Conclusion:** Confirm in Agent Zero UI/settings that the plugin is enabled for the relevant agent. Files alone do not prove runtime activation.

---

## 3. `template_registry.json` — data integrity

**File:** `usr/pen_and_paper/knowledge/workflows/template_registry.json`

| Template in `templates` | MD file exists |
|-------------------------|----------------|
| `session` | Yes — `session.md` |
| `workflow_to_skill` | Yes — `workflow_to_skill.md` |

**`base_workflows.list`:** `research`, `debugging`, `validation` — **no** matching MD files.

**`base_workflows.hooks`:**

| Hook | Points to | Exists? |
|------|-----------|---------|
| `on_unknown` | `research` | No |
| `on_stuck` | `debugging` | No |
| `on_error` | `debugging` | No |
| `on_complete` | `validation` | No |

**Status:** Registry is **inconsistent** — requires Wave 0 before relying on hooks or orchestration.

---

## 4. Config split (three layers)

### 4.1 `pen_paper.py` (what the agent actually gets)

```python
retrieve_context = self.args.get("retrieve_context", True)  # default True
vectorize = self.args.get("vectorize", True)                # default True
```

- Does **not** call `load_plugin_config()` / `feature_enabled()`.

### 4.2 `_config.py` DEFAULTS (API / workflows_store)

```yaml
features:
  retrieve_context_on_create: false
  vectorize_on_close: false
```

- `pen_paper_wiki_template.py`, `workflows_*.py`, `workflows_store.py` use `load_plugin_config`.
- `pen_paper.py` — **does not**.

### 4.3 `config.json` (local plugin config)

```json
{
  "vectorize_by_default": false,
  "retrieve_context_by_default": false,
  "context_loader_enabled": false,
  "llm_wiki_integration": { "enabled": true, "vault_path": "/data/SharedBrain" }
}
```

- Keys `vectorize_by_default` / `retrieve_context_by_default` are **not** mapped in `_config.DEFAULTS`.

### 4.4 `default_config.yaml` (seed)

- `vectorize_by_default: true`, `retrieve_context_by_default: true`, `context_loader_enabled: true` — **conflicts** with `config.json`.

### 4.5 `webui/config.html`

- Exposes `config.features.retrieve_context_on_create` / `vectorize_on_close`.
- **No effect** on `pen_paper` until Wave 1 wiring.

### 4.6 `context_loader`

- Defined in config — **no implementation** in plugin code.

---

## 5. Vectorizer

- `pen_paper.py` imports `usr.plugins.a0_pen_paper.helpers.pen_paper_vectorizer.PenPaperVectorizer`
- File **does not exist** in the workspace — failure swallowed in `try/except` (print only).

---

## 6. Smart Router / execution_contract

| Item | Status |
|------|--------|
| `rules.yaml` → `execution_contract` | Documented |
| `enforcement` | `SmartRouterExtension._execute_workflow_steps` |
| `_20_smart_router.py` | **DISABLED** (no-op) |
| `execution_log` section | **Not** in `VALID_SECTIONS` |
| `WorkflowStepStatus` | `DONE` in code; `COMPLETED` in rules — **mismatch** |

---

## 7. WebUI / Workflow Dashboard

| Component | Present |
|-----------|---------|
| Canvas `pen_paper_workflows` | Yes |
| API base | `/plugins/a0_pen_paper` ([`workflows-store.js`](../../usr/plugins/a0_pen_paper/webui/workflows-store.js)) |
| SKILL docs | `/api/plugins/...` — **wrong** in skill text |
| `config.html` | Yes |
| Sync polling | 2500ms |

---

## 8. Recommendations before Wave 0+

1. Confirm plugin activation in Agent Zero.
2. Fix registry (Wave 0) before hook tests with an agent.
3. Do not assume vectorize/retrieve are off — tool defaults are `True`.
4. Verify `/data/SharedBrain` if using wiki templates.

---

## 9. Checklist

- [x] Repository path verified
- [ ] Plugin enabled at runtime (manual / Agent Zero confirmation)
- [x] Config mapped (three layers documented)
- [x] base_workflows missing templates documented
