#!/usr/bin/env python3
"""
Automated verification for Pen & Paper + Workflows (Waves 0-3).
Run from agent-zero-2 repo root or plugin directory.

  python usr/plugins/a0_pen_paper/scripts/verify_pen_paper_setup.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_DIR.parents[2] if len(PLUGIN_DIR.parents) >= 3 else PLUGIN_DIR.parent

# Allow imports when run from repo root
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _ok(name: str, detail: str = "") -> bool:
    suffix = f" — {detail}" if detail else ""
    print(f"  PASS  {name}{suffix}")
    return True


def _fail(name: str, detail: str = "") -> bool:
    suffix = f" — {detail}" if detail else ""
    print(f"  FAIL  {name}{suffix}")
    return False


def check_py_compile() -> bool:
    import py_compile

    files = [
        PLUGIN_DIR / "tools" / "pen_paper.py",
        PLUGIN_DIR / "tools" / "_config.py",
        PLUGIN_DIR / "helpers" / "workflows_store.py",
        PLUGIN_DIR / "helpers" / "workflow_executor.py",
        PLUGIN_DIR / "helpers" / "sessions_store.py",
        PLUGIN_DIR / "extensions" / "python" / "tool_execute_before" / "_50_pen_paper_workflow_guard.py",
        PLUGIN_DIR / "extensions" / "python" / "tool_execute_after" / "_51_pen_paper_focus.py",
    ]
    ok = True
    for fp in files:
        if not fp.exists():
            ok = _fail("py_compile", f"missing {fp.name}") and ok
            continue
        try:
            py_compile.compile(str(fp), doraise=True)
        except py_compile.PyCompileError as e:
            ok = _fail("py_compile", f"{fp.name}: {e}") and ok
    if ok:
        _ok("py_compile", f"{len(files)} files")
    return ok


def check_execution_log_section() -> bool:
    text = (PLUGIN_DIR / "tools" / "pen_paper.py").read_text(encoding="utf-8")
    if '"execution_log"' in text and "execution_log" in text:
        return _ok("execution_log in VALID_SECTIONS")
    return _fail("execution_log in VALID_SECTIONS", "not found in pen_paper.py")


def check_config_wiring() -> bool:
    text = (PLUGIN_DIR / "tools" / "pen_paper.py").read_text(encoding="utf-8")
    if "load_plugin_config" in text and "feature_enabled" in text:
        return _ok("pen_paper uses load_plugin_config")
    return _fail("pen_paper uses load_plugin_config", "still hardcoded defaults?")


def check_registry_integrity() -> bool:
    try:
        from usr.plugins.a0_pen_paper.helpers.workflows_store import validate_registry_integrity
        from usr.plugins.a0_pen_paper.tools._config import load_plugin_config

        errors = validate_registry_integrity(load_plugin_config())
        if errors:
            for e in errors:
                print(f"         {e}")
            return _fail("registry integrity", f"{len(errors)} error(s)")
        return _ok("registry integrity")
    except Exception as e:
        return _fail("registry integrity", str(e))


def check_seed_templates() -> bool:
    seed_dir = PLUGIN_DIR / "data" / "workflows"
    required = ["research.md", "debugging.md", "validation.md", "template_registry.seed.json"]
    missing = [f for f in required if not (seed_dir / f).exists()]
    if missing:
        return _fail("seed templates", f"missing {missing}")
    return _ok("seed templates in plugin data/")


def check_runtime_registry() -> bool:
    runtime_reg = REPO_ROOT / "usr" / "pen_and_paper" / "knowledge" / "workflows" / "template_registry.json"
    if not runtime_reg.exists():
        return _ok("runtime registry", "SKIP (no local runtime)")
    try:
        data = json.loads(runtime_reg.read_text(encoding="utf-8"))
        templates = data.get("templates") or {}
        for name in ("research", "debugging", "validation"):
            if name not in templates:
                return _fail("runtime registry", f"missing template {name}")
        hooks = (data.get("base_workflows") or {}).get("hooks") or {}
        for target in hooks.values():
            if target not in templates:
                return _fail("runtime registry", f"hook -> {target} not in templates")
        return _ok("runtime registry", f"{len(templates)} templates")
    except Exception as e:
        return _fail("runtime registry", str(e))


def check_skills() -> bool:
    skills = [
        PLUGIN_DIR / "skills" / "pen-and-paper" / "SKILL.md",
        PLUGIN_DIR / "skills" / "pen-paper-workflows" / "SKILL.md",
        PLUGIN_DIR / "skills" / "pen-and-paper-workflow" / "SKILL.md",
    ]
    missing = [s.parent.name for s in skills if not s.exists()]
    if missing:
        return _fail("skills", f"missing {missing}")
    return _ok("skills", "pen-and-paper, pen-paper-workflows, pen-and-paper-workflow")


def check_sessions_api() -> bool:
    api_files = [
        "sessions_list.py",
        "sessions_get.py",
        "sessions_focus.py",
        "sessions_set_focus.py",
        "sessions_append.py",
    ]
    missing = [f for f in api_files if not (PLUGIN_DIR / "api" / f).exists()]
    if missing:
        return _fail("sessions API", f"missing {missing}")
    try:
        from usr.plugins.a0_pen_paper.helpers.sessions_store import (
            list_sessions,
            file_etag,
            VALID_SECTIONS,
        )
        from usr.plugins.a0_pen_paper.tools._config import load_plugin_config

        if "execution_log" not in VALID_SECTIONS:
            return _fail("sessions_store sections", "execution_log missing")
        data = list_sessions(load_plugin_config(), None, chat_only=False)
        if not isinstance(data, dict) or "sessions" not in data:
            return _fail("sessions_store list_sessions", "expected dict with sessions key")
        _ = file_etag
        return _ok("sessions_store + API modules")
    except Exception as e:
        return _fail("sessions_store import", str(e))


def check_execute_validate() -> bool:
    import subprocess

    script = PLUGIN_DIR / "execute.py"
    try:
        result = subprocess.run(
            [sys.executable, str(script), "validate"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            return _ok("execute.py validate")
        detail = (result.stderr or result.stdout or "")[:200]
        return _fail("execute.py validate", detail or f"exit {result.returncode}")
    except Exception as e:
        return _fail("execute.py validate", str(e))


def check_rules_contract() -> bool:
  path = PLUGIN_DIR / "data" / "config" / "rules.yaml"
  if not path.exists():
      return _fail("rules.yaml execution_contract")
  text = path.read_text(encoding="utf-8")
  if "COMPLETED" in text and "done only" not in text.lower():
      if "status is done" not in text and "status: done" not in text:
          return _fail("rules.yaml", "still mentions COMPLETED without done alignment")
  if "workflow_executor" in text or "pen_paper.py" in text:
      return _ok("rules.yaml enforcement path")
  return _fail("rules.yaml enforcement", "not pointing to P&P executor")


def main() -> int:
    print("Pen & Paper + Workflows — automated verification")
    print(f"Plugin: {PLUGIN_DIR}")
    print(f"Repo:   {REPO_ROOT}")
    print()

    checks = [
        check_py_compile(),
        check_execution_log_section(),
        check_config_wiring(),
        check_registry_integrity(),
        check_seed_templates(),
        check_runtime_registry(),
        check_skills(),
        check_rules_contract(),
        check_sessions_api(),
        check_execute_validate(),
    ]
    passed = sum(checks)
    total = len(checks)
    print()
    print(f"Result: {passed}/{total} checks passed")
    if passed == total:
        print("Overall: PASS")
        return 0
    print("Overall: FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())
