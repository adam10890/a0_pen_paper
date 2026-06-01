"""
Workflow template storage for Pen & Paper WebUI editor.
Reads/writes the same files as pen_paper tool actions.
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

from usr.plugins.a0_pen_paper.tools._config import load_plugin_config, runtime_base

_REGISTRY_REL = "knowledge/workflows/template_registry.json"
_WORKFLOWS_REL = "knowledge/workflows"
_NAME_RE = re.compile(r"^[a-z0-9_]+$")


def _abs_runtime(cfg: dict[str, Any] | None = None) -> Path:
    try:
        from helpers import files
        base = runtime_base(cfg or load_plugin_config())
        return Path(files.get_abs_path(base))
    except Exception:
        return Path(runtime_base(cfg or load_plugin_config()))


def registry_path(cfg: dict[str, Any] | None = None) -> Path:
    return _abs_runtime(cfg) / _REGISTRY_REL


def workflows_dir(cfg: dict[str, Any] | None = None) -> Path:
    return _abs_runtime(cfg) / _WORKFLOWS_REL


def _read_registry(cfg: dict[str, Any] | None = None) -> dict:
    path = registry_path(cfg)
    if not path.exists():
        return {"templates": {}, "base_workflows": {"list": [], "hooks": {}}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"templates": {}, "base_workflows": {"list": [], "hooks": {}}}


def _write_registry(data: dict, cfg: dict[str, Any] | None = None) -> None:
    path = registry_path(cfg)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def validate_name(name: str) -> str | None:
    if not name or not _NAME_RE.match(name):
        return "template_name must match ^[a-z0-9_]+$"
    return None


def validate_registry_integrity(cfg: dict[str, Any] | None = None) -> list[str]:
    """Return list of integrity errors (empty if OK)."""
    errors: list[str] = []
    reg = _read_registry(cfg)
    wf_dir = workflows_dir(cfg)
    templates = reg.get("templates") or {}
    for name, meta in templates.items():
        wf_file = meta.get("file", f"{name}.md")
        if not (wf_dir / wf_file).exists():
            errors.append(f"Template '{name}': missing file {wf_file}")
    hooks = (reg.get("base_workflows") or {}).get("hooks") or {}
    for hook, target in hooks.items():
        if target not in templates:
            errors.append(f"Hook '{hook}' points to missing template '{target}'")
    for entry in (reg.get("base_workflows") or {}).get("list") or []:
        if entry not in templates:
            errors.append(f"base_workflows.list entry '{entry}' not in templates")
    return errors


def list_templates(cfg: dict[str, Any] | None = None) -> dict:
    reg = _read_registry(cfg)
    items = []
    for name, meta in (reg.get("templates") or {}).items():
        items.append({
            "name": name,
            "file": meta.get("file", f"{name}.md"),
            "version": meta.get("version", "1.0.0"),
            "description": meta.get("description", ""),
            "description_he": meta.get("description_he", ""),
            "phases": meta.get("phases", []),
            "triggers": meta.get("triggers", []),
        })
    items.sort(key=lambda x: x["name"])
    return {
        "templates": items,
        "base_workflows": reg.get("base_workflows", {}),
        "runtime_dir": runtime_base(cfg or load_plugin_config()),
    }


def get_template(name: str, cfg: dict[str, Any] | None = None) -> dict | None:
    err = validate_name(name)
    if err:
        return None
    reg = _read_registry(cfg)
    templates = reg.get("templates") or {}
    if name not in templates:
        return None
    meta = templates[name]
    wf_file = meta.get("file", f"{name}.md")
    content = ""
    fp = workflows_dir(cfg) / wf_file
    if fp.exists():
        content = fp.read_text(encoding="utf-8")
    return {
        "name": name,
        "file": wf_file,
        "version": meta.get("version", "1.0.0"),
        "description": meta.get("description", ""),
        "description_he": meta.get("description_he", ""),
        "phases": meta.get("phases", []),
        "triggers": meta.get("triggers", []),
        "content": content,
        "mtime": int(fp.stat().st_mtime) if fp.exists() else 0,
    }


def save_template(
    name: str,
    content: str,
    metadata: dict | None = None,
    cfg: dict[str, Any] | None = None,
) -> dict:
    err = validate_name(name)
    if err:
        return {"ok": False, "error": err}
    reg = _read_registry(cfg)
    templates = reg.get("templates") or {}
    if name not in templates:
        return {"ok": False, "error": f"Template '{name}' not found"}
    meta = dict(templates[name])
    md = metadata or {}
    for field in ("description", "description_he", "phases", "triggers", "version"):
        if field in md:
            meta[field] = md[field]
    wf_file = meta.get("file", f"{name}.md")
    wf_dir = workflows_dir(cfg)
    wf_dir.mkdir(parents=True, exist_ok=True)
    (wf_dir / wf_file).write_text(content or "", encoding="utf-8")
    templates[name] = meta
    reg["templates"] = templates
    _write_registry(reg, cfg)
    integrity = validate_registry_integrity(cfg)
    if integrity:
        return {"ok": True, "name": name, "file": wf_file, "warnings": integrity}
    return {"ok": True, "name": name, "file": wf_file}


def create_template(
    name: str,
    content: str,
    description: str = "",
    description_he: str = "",
    phases: list | None = None,
    triggers: list | None = None,
    cfg: dict[str, Any] | None = None,
) -> dict:
    err = validate_name(name)
    if err:
        return {"ok": False, "error": err}
    reg = _read_registry(cfg)
    templates = reg.get("templates") or {}
    if name in templates:
        return {"ok": False, "error": f"Template '{name}' already exists"}
    phases = phases or ["Plan", "Work", "Review"]
    triggers = triggers or [name]
    body = content
    if not body:
        sections = []
        for i, phase in enumerate(phases, 1):
            sections.append(f"## Phase {i}: {phase}\n\n### Notes:\n- \n")
        title = name.replace("_", " ").title()
        body = f"# {title} Workflow\n## Overview\n{description}\n\n---\n\n"
        body += "\n---\n\n".join(sections)
    wf_file = f"{name}.md"
    wf_dir = workflows_dir(cfg)
    wf_dir.mkdir(parents=True, exist_ok=True)
    (wf_dir / wf_file).write_text(body, encoding="utf-8")
    templates[name] = {
        "file": wf_file,
        "version": "1.0.0",
        "description": description,
        "description_he": description_he,
        "phases": phases,
        "triggers": list(triggers),
    }
    reg["templates"] = templates
    _write_registry(reg, cfg)
    integrity = validate_registry_integrity(cfg)
    if integrity:
        return {"ok": False, "error": "; ".join(integrity)}
    return {"ok": True, "name": name, "file": wf_file}


def delete_template(name: str, cfg: dict[str, Any] | None = None) -> dict:
    err = validate_name(name)
    if err:
        return {"ok": False, "error": err}
    if name == "session":
        return {"ok": False, "error": "Cannot delete built-in 'session' template"}
    reg = _read_registry(cfg)
    templates = reg.get("templates") or {}
    if name not in templates:
        return {"ok": False, "error": f"Template '{name}' not found"}
    meta = templates.pop(name)
    wf_file = meta.get("file", f"{name}.md")
    reg["templates"] = templates
    _write_registry(reg, cfg)
    src = workflows_dir(cfg) / wf_file
    if src.exists():
        archive = _abs_runtime(cfg) / "_archived/templates"
        archive.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(archive / wf_file))
    return {"ok": True, "name": name}
