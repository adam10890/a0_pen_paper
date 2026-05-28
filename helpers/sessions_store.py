"""
Active Pen & Paper session storage for Live Session Canvas view.
Reads/writes workspace.json under runtime sessions/active.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from usr.plugins.a0_pen_paper.tools._config import load_plugin_config, runtime_base

VALID_SECTIONS = [
    "findings",
    "results",
    "insights",
    "notes",
    "decisions",
    "backtrack",
    "execution_log",
]

_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]+$")


def _abs_runtime(cfg: dict[str, Any] | None = None) -> Path:
    try:
        from helpers import files

        base = runtime_base(cfg or load_plugin_config())
        return Path(files.get_abs_path(base))
    except Exception:
        return Path(runtime_base(cfg or load_plugin_config()))


def sessions_dir(cfg: dict[str, Any] | None = None) -> Path:
    return _abs_runtime(cfg) / "sessions" / "active"


def focus_path(cfg: dict[str, Any] | None = None) -> Path:
    return _abs_runtime(cfg) / ".ui" / "focus.json"


def _safe_workspace_name(name: str) -> str:
    if not name or not _NAME_RE.match(name):
        raise ValueError("Invalid workspace name")
    return name


def _workspace_file(name: str, cfg: dict[str, Any] | None = None) -> Path:
    return sessions_dir(cfg) / _safe_workspace_name(name) / "workspace.json"


def file_etag(path: Path) -> str:
    if not path.exists():
        return ""
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest()[:16]


def _section_text(entries: list) -> str:
    parts: list[str] = []
    for entry in entries:
        if isinstance(entry, dict):
            content = entry.get("content", "")
            if content:
                parts.append(str(content))
        elif entry:
            parts.append(str(entry))
    return "\n\n---\n\n".join(parts)


def _session_sort_key(item: dict[str, Any]) -> tuple:
    return (
        0 if item.get("is_chat_focus") else 1,
        0 if item.get("is_current_chat") else 1,
        -float(item.get("mtime") or 0),
    )


def list_sessions(
    cfg: dict[str, Any] | None = None,
    chat_id: str | None = None,
    *,
    chat_only: bool = False,
) -> dict[str, Any]:
    base = sessions_dir(cfg)
    base.mkdir(parents=True, exist_ok=True)
    focus = read_focus(chat_id, cfg) if chat_id else {}
    focus_workspace = focus.get("workspace") if isinstance(focus, dict) else None
    out: list[dict[str, Any]] = []
    for ws_path in base.iterdir():
        if not ws_path.is_dir():
            continue
        wf = ws_path / "workspace.json"
        if not wf.exists():
            continue
        try:
            workspace = json.loads(wf.read_text(encoding="utf-8"))
            meta = workspace.get("metadata") or {}
            name = meta.get("name", ws_path.name)
            session_chat = meta.get("chat_id")
            counts = {
                s: len(workspace.get(s) or [])
                for s in VALID_SECTIONS
                if isinstance(workspace.get(s), list)
            }
            is_current_chat = bool(chat_id and session_chat == chat_id)
            is_chat_focus = bool(focus_workspace and name == focus_workspace)
            is_orphan = session_chat is None
            out.append(
                {
                    "name": name,
                    "status": meta.get("status", "unknown"),
                    "template": meta.get("template"),
                    "chat_id": session_chat,
                    "created": (meta.get("created_at") or "")[:16],
                    "mtime": wf.stat().st_mtime,
                    "etag": file_etag(wf),
                    "section_counts": counts,
                    "is_current_chat": is_current_chat,
                    "is_chat_focus": is_chat_focus,
                    "is_orphan": is_orphan,
                }
            )
        except Exception:
            continue
    out.sort(key=_session_sort_key)
    visible = out
    if chat_id and chat_only:
        visible = [
            s
            for s in out
            if s.get("is_current_chat")
            or (s.get("is_chat_focus") and focus_workspace == s.get("name"))
        ]
    return {
        "sessions": visible,
        "total_count": len(out),
        "visible_count": len(visible),
        "current_chat_id": chat_id,
        "focus": focus,
    }


def get_session(
    name: str,
    section: str | None = None,
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    wf = _workspace_file(name, cfg)
    if not wf.exists():
        raise FileNotFoundError(f"Workspace '{name}' not found")
    workspace = json.loads(wf.read_text(encoding="utf-8"))
    meta = workspace.get("metadata") or {}
    etag = file_etag(wf)
    result: dict[str, Any] = {
        "name": meta.get("name", name),
        "metadata": meta,
        "etag": etag,
        "sections": VALID_SECTIONS,
    }
    if section:
        if section not in VALID_SECTIONS:
            raise ValueError(f"Invalid section: {section}")
        entries = workspace.get(section) or []
        result["section"] = section
        result["entries"] = entries
        result["text"] = _section_text(entries if isinstance(entries, list) else [])
        result["entry_count"] = len(entries) if isinstance(entries, list) else 0
    else:
        result["section_counts"] = {
            s: len(workspace.get(s) or []) for s in VALID_SECTIONS
        }
    return result


def read_focus(chat_id: str | None = None, cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    path = focus_path(cfg)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    if chat_id:
        by_chat = data.get("by_chat")
        if isinstance(by_chat, dict) and chat_id in by_chat:
            return by_chat[chat_id]
        if data.get("chat_id") == chat_id:
            return data
        return {}
    return data


def write_focus(
    *,
    workspace: str,
    section: str | None = None,
    action: str = "",
    chat_id: str | None = None,
    entry_index: int | None = None,
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    path = focus_path(cfg)
    path.parent.mkdir(parents=True, exist_ok=True)
    wf = _workspace_file(workspace, cfg)
    payload: dict[str, Any] = {
        "workspace": workspace,
        "section": section or "notes",
        "action": action,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "workspace_mtime": wf.stat().st_mtime if wf.exists() else 0,
    }
    if chat_id:
        payload["chat_id"] = chat_id
    if entry_index is not None:
        payload["entry_index"] = entry_index
    existing: dict[str, Any] = {}
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            existing = {}
    if chat_id:
        by_chat = existing.get("by_chat")
        if not isinstance(by_chat, dict):
            by_chat = {}
        by_chat[chat_id] = payload
        existing["by_chat"] = by_chat
    existing.update(payload)
    path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    return payload


def append_section(
    name: str,
    section: str,
    content: str,
    etag: str,
    *,
    author: str = "user",
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if section not in VALID_SECTIONS:
        raise ValueError(f"Invalid section: {section}")
    wf = _workspace_file(name, cfg)
    if not wf.exists():
        raise FileNotFoundError(f"Workspace '{name}' not found")
    current_etag = file_etag(wf)
    if etag and etag != current_etag:
        return {
            "ok": False,
            "error": "stale",
            "current_etag": current_etag,
            "message": "Workspace changed since load. Refresh and try again.",
        }
    workspace = json.loads(wf.read_text(encoding="utf-8"))
    if workspace.get("metadata", {}).get("status") == "closed":
        return {"ok": False, "error": "closed", "message": "Cannot update a closed workspace."}
    if section not in workspace:
        workspace[section] = []
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "content": content,
        "source": "ui",
        "author": author,
    }
    workspace[section].append(entry)
    wf.write_text(json.dumps(workspace, indent=2), encoding="utf-8")
    new_etag = file_etag(wf)
    return {
        "ok": True,
        "etag": new_etag,
        "entry_count": len(workspace[section]),
        "entry": entry,
    }
