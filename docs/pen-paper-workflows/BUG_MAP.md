# Bug Map — a0_pen_paper (cross-version reconciliation)

**Status:** Mapping only. **No code changed.** Hand this file to Cursor / Claude Code to execute the fixes.
**Date:** 2026-05-28
**Author of map:** investigation pass over `main` vs `develop/pen-paper-workflows`.

---

## 0. TL;DR

- Two branches diverged from the same base `7570060` and built overlapping work.
- **`develop/pen-paper-workflows` is a clean superset of `main`** and is **backward-compatible** with `main`'s config (verified — see §2).
- **Decision (owner):** consolidate **`develop` → `main`** (promote develop to the new default).
- Three real defects to fix, none blocking the consolidation:
  1. 🔴 **Mojibake** (double-encoded UTF-8) in `data/config/rules.yaml` + `data/config/onboarding.yaml` — present since the initial commit, in both branches.
  2. 🟠 **Version collision** — `main` and `develop` are both `version: 1.2.0` with **different `config.json` schemas**.
  3. 🟡 **Fragile verify script** — `scripts/verify_pen_paper_setup.py` hard-imports `usr.plugins.a0_pen_paper.*`; fails 2/10 checks when not run from the `/a0` root.

---

## 1. Branch topology

```
4d0dcad  initial v1.1.2
   │
7570060  merge #3 (zero-agent-plugin-compat)   ← common base
   ├──────────────► be83daf  Right Canvas v1.18 migration  ──► 66014c2 (main HEAD)
   │                         (subset: workflows store + webui + v1.18 register)
   │
   └──────────────► 42040e1  Waves 0–3 determinism
                    ef76dce  Wave 4 Live Session Canvas      ──► develop HEAD
                             (SUPERSET: includes equivalent v1.18 files
                              + executor + sessions API + docs + verify)
```

| Branch | Content | Date | Posture |
|---|---|---|---|
| `main` (default) | Right Canvas v1.18 migration only (subset) | 2026-05-26 | behind |
| `develop/pen-paper-workflows` | Waves 0–4: workflows registry, executor, Live Canvas, sessions API, docs, verify script | 2026-05-28 | canonical superset |
| `claude/sharp-edison-cio57` | branched off **old** main `7570060` — **has none of the workflow code** | — | needs rebase onto develop before any work |

### Consolidation plan (develop → main)
1. Open PR `develop/pen-paper-workflows` → `main`.
2. Confirm the only files unique to `main` are already represented in `develop` (they are — file-tree diff shows `develop` ⊇ `main`).
3. Apply the §3 fixes (preferably on `develop` / the PR branch before merge).
4. Bump version so the schema change is explicit (§3.2).
5. After merge, rebase or recreate `claude/sharp-edison-cio57` from the new `main`.

---

## 2. Verified NON-issues (do not "fix" these)

- **Config backward-compat works.** `tools/_config.py::_normalize_legacy()` maps `main`'s flat keys onto `develop`'s nested schema:
  - `vectorize_by_default` → `features.vectorize_on_close`
  - `retrieve_context_by_default` → `features.retrieve_context_on_create`
  - `context_loader_enabled` / `context_loader_first_iteration_only` → `features.*`
  - `max_active_sessions_in_context` → `session.max_active_sessions_in_context`
- **`register-pen-paper.js`** differs from `main` only by removing a stale `mode: "canvas"` argument. `develop`'s store (`webui/workflows-store.js::onOpen`) only recognizes `mode: "live"` / `mode: "templates"` and defaults to `"templates"`; the removed value matched neither, so removal is harmless cleanup.
- **`py_compile`** passes for all 7 Python files; **`execute.py validate`** passes.
- **`AGENT_ZERO_RESPONSES.md`** Hebrew is correct UTF-8 (not corrupted).

---

## 3. Bugs to fix

### 3.1 🔴 Mojibake in runtime config (highest impact)

**What:** Hebrew text, arrows (`→`), box-drawing chars and emoji headers are double-encoded (UTF-8 bytes interpreted as cp1252 and re-saved). The agent reads these files at runtime, so it ingests garbage.

**Files & lines (on `develop`):**

- `data/config/rules.yaml` — lines `7, 13, 15, 16, 17, 21, 23, 28, 31, 35, 42, 54, 55, 81–85, 100–102, 106–109`
  - e.g. line 7: `description: "×—×•×§×™ ×›×ª×™×‘×” ×•× ×™×”×•×œ ×“×¤×™× ×‘×ž×¢×¨×›×ª P&P"` → should be `"חוקי כתיבה וניהול דפים במערכת P&P"`
- `data/config/onboarding.yaml` — lines `32–40` (dir tree `â”œâ”€â”€`), `51–57, 61–69` (arrows), `74, 77, 81, 88` (emoji), `92–94` (arrows)

**Root cause:** committed corrupted in the initial commit `4d0dcad`; never round-tripped through correct UTF-8.

**Fix recipe:**
- Re-decode each file: read bytes, `.decode("utf-8")` then re-encode the mis-decoded sequences. Practical approach in Python:
  ```python
  raw = open(path, "rb").read().decode("utf-8")      # current (already-mojibake) text
  fixed = raw.encode("cp1252", errors="ignore").decode("utf-8", errors="ignore")
  open(path, "w", encoding="utf-8").write(fixed)
  ```
  Verify arrows render as `→`, Hebrew renders correctly, and box-drawing `├──` is intact.
- **Caution:** the leading BOM (`﻿`) on both files — decide whether to keep; YAML loaders tolerate it but it is noise. Recommend stripping.
- After fix, confirm `yaml.safe_load()` still parses both files and `execute.py validate` passes.

**Acceptance:** `grep -nP '×|â†|â”|ðŸ|Â' data/config/*.yaml` returns nothing.

---

### 3.2 🟠 Version collision (same version, different schema)

**What:** `plugin.yaml` is `version: 1.2.0` on **both** branches, but `config.json` schema differs:

| | `main` | `develop` |
|---|---|---|
| feature flags | flat: `vectorize_by_default`, `retrieve_context_by_default`, `context_loader_enabled` | nested: `features.{vectorize_on_close, retrieve_context_on_create, context_loader_enabled, ...}` |
| session cap | `max_active_sessions_in_context` (top-level) | `session.max_active_sessions_in_context` |

Same version number for two schemas makes upgrade behavior ambiguous and is the most likely source of the "version incompatibility" symptom.

**Fix recipe (on develop, as part of develop→main):**
- Bump `plugin.yaml` `version` to `1.2.1` (or `1.3.0` if you treat the workflows/Canvas surface as a feature release).
- Treat `develop`'s nested `config.json` as the single canonical schema; `_normalize_legacy()` already handles old installs, so no runtime break.
- Document the schema in `docs/pen-paper-workflows/CONTRACT.md` (config section) so Cursor/Claude don't reintroduce flat keys.

**Acceptance:** one canonical `config.json` schema in the merged branch; version string strictly greater than any previously released; `default_config.yaml` matches the same nested shape.

---

### 3.3 🟡 Fragile verification script

**What:** `scripts/verify_pen_paper_setup.py` hard-imports the plugin via its in-`/a0` path:
- line 76–77: `from usr.plugins.a0_pen_paper.helpers.workflows_store import ...` / `...tools._config import ...`
- line 141–146: `from usr.plugins.a0_pen_paper.helpers.sessions_store import ...`

When run anywhere other than the Agent Zero root (e.g. a standalone clone, CI, a worktree), Python cannot resolve the `usr.plugins...` package and **2/10 checks fail** (`registry integrity`, `sessions_store import`) with `No module named 'usr'`. Inside Docker `/a0` it passes 8/8 — so this is fragility, not a functional defect.

**Fix recipe:**
- Add an import fallback that loads modules by file path relative to the script when the `usr.plugins...` import fails:
  ```python
  import importlib.util, pathlib
  PLUGIN_ROOT = pathlib.Path(__file__).resolve().parents[1]  # a0_pen_paper/
  def _load(modpath, file):
      try:
          return __import__(modpath, fromlist=["*"])
      except ModuleNotFoundError:
          spec = importlib.util.spec_from_file_location(modpath, PLUGIN_ROOT / file)
          m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
  ```
  Then resolve `workflows_store`, `_config`, `sessions_store` through `_load(...)`.
- Note: `_config.py` and the stores must not themselves require `helpers.*` at import time for the standalone path (they already guard `helpers` imports with try/except — confirm `sessions_store.py` does the same).

**Acceptance:** `python scripts/verify_pen_paper_setup.py` reports 10/10 from a bare clone as well as from `/a0`.

---

## 4. Open questions for the owner (not blockers)

1. Version target for the merged branch: `1.2.1` (patch) or `1.3.0` (feature)?
2. Keep or strip the UTF-8 BOM on the two YAML files after re-encoding?
3. Should the corrupted runtime copies under `usr/pen_and_paper/config/` (if any already deployed) be force-overwritten on next `install()`? (`hooks.py` on develop uses `shutil.copy2` for `rules.yaml` — i.e. it overwrites — but `onboarding.yaml` uses `_copy_missing` — i.e. it will NOT refresh an already-deployed corrupted copy. Consider switching onboarding to overwrite, or bump-gated copy.)

---

## 5. Quick verification commands

```bash
# from a clone of a0_pen_paper
python -m py_compile tools/pen_paper.py helpers/workflow_executor.py helpers/workflows_store.py helpers/sessions_store.py
python execute.py validate
grep -nP '×|â†|â”|ðŸ|Â' data/config/*.yaml     # must be empty after 3.1
python scripts/verify_pen_paper_setup.py        # target 10/10 after 3.3
```
