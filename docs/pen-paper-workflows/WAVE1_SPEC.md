# Wave 1 — Config + Documentation

**Dependencies:** Wave 0 recommended (complete registry)  
**Goal:** UI/config drive `pen_paper` behavior; documentation does not mislead agents.

---

## W1-1: Unify config schema

### Current state (three naming schemes)

| Layer | Keys |
|-------|------|
| `pen_paper` args | `retrieve_context`, `vectorize` |
| `_config.features` | `retrieve_context_on_create`, `vectorize_on_close` |
| `config.json` (legacy) | `vectorize_by_default`, `retrieve_context_by_default` |

### Target — single schema in `_config.py`

```python
DEFAULTS = {
    "runtime_dir": "usr/pen_and_paper",
    "features": {
        "retrieve_context_on_create": False,
        "vectorize_on_close": False,
        "context_loader_enabled": False,
        "context_loader_first_iteration_only": True,
    },
    ...
}
```

### Migration in `load_plugin_config()`

```python
def _normalize_legacy(cfg: dict) -> dict:
    if "vectorize_by_default" in cfg:
        cfg.setdefault("features", {})["vectorize_on_close"] = cfg.pop("vectorize_by_default")
    if "retrieve_context_by_default" in cfg:
        cfg.setdefault("features", {})["retrieve_context_on_create"] = cfg.pop("retrieve_context_by_default")
    ...
```

### Wire `pen_paper.py`

```python
cfg = load_plugin_config(agent=getattr(self, "agent", None))
retrieve_context = self.args.get(
    "retrieve_context",
    feature_enabled(cfg, "retrieve_context_on_create"),
)
vectorize = self.args.get(
    "vectorize",
    feature_enabled(cfg, "vectorize_on_close"),
)
```

- Update `default_config.yaml` + `config.json` to the new schema (remove flat keys or migrate).
- Keep `webui/config.html` fields if already under `features.*`.

---

## W1-2: SKILL and reference docs

| File | Action |
|------|--------|
| `skills/pen-paper-workflows/SKILL.md` | API: `/plugins/a0_pen_paper/...` (not `/api/plugins/`) |
| `skills/pen-paper-workflows/references/workflow-registry.md` | Same fix |
| `skills/pen-and-paper/references/session-management.md` | `write` → `update` |
| `skills/pen-and-paper/SKILL.md` | Fix/remove links to missing `vectorizer.md`, `plugin-packaging.md` or add stubs |
| `docs/CAPABILITIES_AND_ROADMAP.md` | v1.2.0, document Canvas + config.html |

---

## W1-3: Canvas race (WD policy)

**Problem:** 2.5s polling — agent and user can overwrite the same template.

**Options:**

| # | Solution |
|---|----------|
| 1 | `metadata.editing_by: "agent"|"user"` in registry + UI warning |
| 2 | ETag / `mtime` on `workflows_save` — reject stale writes |
| 3 | SKILL: "before edit_template — check if user is editing in Canvas" |

**Recommendation:** 2 + 3 (code + behavior).

---

## W1-4: Vectorizer decision

| Option | Action |
|--------|--------|
| Implement | Restore `helpers/pen_paper_vectorizer.py` |
| Remove | Drop import; parameters no-op; update SKILL |

**Minimum for Wave 1:** Document in tool help that vectorize may fail silently.

---

## Files

- `tools/pen_paper.py`, `tools/_config.py`
- `default_config.yaml`, `config.json`
- skills + CAPABILITIES
- `webui/workflows-store.js` (if etag)
- `helpers/workflows_store.py`

---

## Acceptance tests

- [ ] `retrieve_context=false` in config → create skips vectorizer (or documented no-op)
- [ ] SKILL/API paths consistent
- [ ] `session-management.md` matches the tool
- [ ] `py_compile` on changed Python files
