"""
Shared source loading for Pen & Paper diagram exporters and bridges.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from usr.plugins.a0_pen_paper.helpers.diagram_generator import (
    nodes_from_session,
    nodes_from_template,
    nodes_from_text,
)


VALID_SECTIONS = [
    "findings",
    "results",
    "insights",
    "notes",
    "decisions",
    "backtrack",
    "execution_log",
]


def load_diagram_source(
    *,
    runtime_dir: Path,
    source_type: str,
    source_id: str,
    content: str = "",
):
    if source_type == "template":
        if not source_id:
            raise ValueError("template_name/source_id is required")
        return _load_template(runtime_dir, source_id)
    if source_type == "session":
        if not source_id:
            raise ValueError("workspace/source_id is required")
        return _load_session(runtime_dir, source_id)
    if source_type == "text":
        if not content:
            raise ValueError("content is required")
        nodes, edges = nodes_from_text(content, title=source_id or "Ad hoc diagram")
        return source_id or "Ad hoc diagram", nodes, edges, runtime_dir / "diagrams" / "ad_hoc"
    raise ValueError("source_type must be template, session, or text")


def safe_name(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(value or "")).strip("_") or "diagram"


def _load_template(runtime_dir: Path, template_name: str):
    registry_path = runtime_dir / "knowledge" / "workflows" / "template_registry.json"
    if not registry_path.exists():
        raise FileNotFoundError(f"template registry not found: {registry_path}")
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    templates = registry.get("templates") or {}
    if template_name not in templates:
        raise FileNotFoundError(f"template not found: {template_name}")
    entry = templates[template_name]
    template_file = entry.get("file", f"{template_name}.md")
    template_path = runtime_dir / "knowledge" / "workflows" / template_file
    content = template_path.read_text(encoding="utf-8") if template_path.exists() else ""
    nodes, edges = nodes_from_template(template_name, entry, content)
    title = entry.get("description") or template_name
    return title, nodes, edges, runtime_dir / "diagrams" / "templates" / safe_name(template_name)


def _load_session(runtime_dir: Path, workspace: str):
    session_path = runtime_dir / "sessions" / "active" / safe_name(workspace) / "workspace.json"
    if not session_path.exists():
        raise FileNotFoundError(f"active session not found: {workspace}")
    data = json.loads(session_path.read_text(encoding="utf-8"))
    nodes, edges = nodes_from_session(data, VALID_SECTIONS)
    metadata = data.get("metadata") or {}
    title = metadata.get("name") or workspace
    return title, nodes, edges, session_path.parent / "diagrams"
