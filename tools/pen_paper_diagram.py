"""
pen_paper_diagram - generate editable draw.io diagrams from Pen & Paper artifacts.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from helpers.tool import Tool, Response
    from helpers import files
except Exception:
    class Tool:
        args: dict[str, Any] = {}
        agent = None

    class Response:
        def __init__(self, message: str = "", break_loop: bool = False):
            self.message = message
            self.break_loop = break_loop

    class _FilesFallback:
        @staticmethod
        def get_abs_path(path: str) -> str:
            return str(Path(path).resolve())

        @staticmethod
        def read_file(path: str) -> str:
            return Path(path).read_text(encoding="utf-8")

        @staticmethod
        def write_file(path: str, content: str) -> None:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")

        @staticmethod
        def safe_file_name(value: str) -> str:
            return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value).strip("_") or "diagram"

    files = _FilesFallback()

try:
    from usr.plugins.a0_pen_paper.helpers.diagram_generator import (
        THEMES,
        VALID_DIAGRAM_TYPES,
        ascii_sketch,
        build_drawio_xml,
        nodes_from_session,
        nodes_from_template,
        nodes_from_text,
    )
    from usr.plugins.a0_pen_paper.tools._config import load_plugin_config, runtime_base
except Exception:
    try:
        from ..helpers.diagram_generator import (
            THEMES,
            VALID_DIAGRAM_TYPES,
            ascii_sketch,
            build_drawio_xml,
            nodes_from_session,
            nodes_from_template,
            nodes_from_text,
        )
        from ._config import load_plugin_config, runtime_base
    except Exception:
        from helpers.diagram_generator import (
            THEMES,
            VALID_DIAGRAM_TYPES,
            ascii_sketch,
            build_drawio_xml,
            nodes_from_session,
            nodes_from_template,
            nodes_from_text,
        )
        from _config import load_plugin_config, runtime_base


VALID_SECTIONS = [
    "findings",
    "results",
    "insights",
    "notes",
    "decisions",
    "backtrack",
    "execution_log",
]


class PenPaperDiagram(Tool):
    """Generate editable draw.io diagrams from templates, sessions, or text."""

    async def execute(self, **kwargs) -> Response:
        action = self.args.get("action", "generate")
        if action == "help":
            return Response(message=self._help(), break_loop=False)
        if action == "list_options":
            return Response(message=self._options(), break_loop=False)
        if action != "generate":
            return Response(
                message="Invalid action. Use `generate`, `list_options`, or `help`.",
                break_loop=False,
            )

        source_type = str(self.args.get("source_type", "session")).strip().lower()
        source_id = self._source_id()
        diagram_type = str(self.args.get("diagram_type", "flow")).strip()
        theme = str(self.args.get("theme", "tech-blue")).strip()
        output_name = str(self.args.get("output_name", "")).strip()

        if diagram_type not in VALID_DIAGRAM_TYPES:
            return Response(
                message=f"Invalid diagram_type `{diagram_type}`. Use one of: {', '.join(sorted(VALID_DIAGRAM_TYPES))}",
                break_loop=False,
            )
        if theme not in THEMES:
            return Response(
                message=f"Invalid theme `{theme}`. Use one of: {', '.join(sorted(THEMES))}",
                break_loop=False,
            )

        cfg = self._config()
        runtime_dir = self._runtime_dir(cfg)

        try:
            title, nodes, edges, output_dir = self._load_source(
                source_type=source_type,
                source_id=source_id,
                runtime_dir=runtime_dir,
            )
        except ValueError as e:
            return Response(message=f"Error: {e}", break_loop=False)

        if not output_name:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_name = f"{source_type}_{source_id or 'ad_hoc'}_{diagram_type}_{stamp}"
        safe_output = files.safe_file_name(output_name)
        output_path = output_dir / f"{safe_output}.drawio"

        xml = build_drawio_xml(
            title=title,
            nodes=nodes,
            edges=edges,
            diagram_type=diagram_type,
            theme_name=theme,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        files.write_file(str(output_path), xml)

        sketch = ascii_sketch(nodes, diagram_type)
        msg = [
            "## Pen & Paper Diagram Generated",
            "",
            f"**Source:** `{source_type}:{source_id or 'content'}`",
            f"**Diagram:** `{diagram_type}` / `{theme}`",
            f"**Nodes:** {len(nodes)}",
            f"**Edges:** {len(edges)}",
            f"**File:** `{output_path}`",
            "",
            "### Sketch",
            "```text",
            sketch,
            "```",
            "",
            "Open the `.drawio` file with draw.io, diagrams.net, VS Code draw.io extensions, or any compatible editor.",
        ]
        return Response(message="\n".join(msg), break_loop=False)

    def _source_id(self) -> str:
        for key in ("source_id", "name", "template_name", "workspace"):
            value = self.args.get(key)
            if value:
                return str(value).strip()
        return ""

    def _config(self) -> dict[str, Any]:
        try:
            return load_plugin_config(agent=getattr(self, "agent", None))
        except Exception:
            return {}

    def _runtime_dir(self, cfg: dict[str, Any]) -> Path:
        try:
            return Path(files.get_abs_path(runtime_base(cfg)))
        except Exception:
            return Path("usr/pen_and_paper").resolve()

    def _load_source(
        self,
        source_type: str,
        source_id: str,
        runtime_dir: Path,
    ):
        if source_type == "template":
            if not source_id:
                raise ValueError("source_id/template_name is required for template diagrams")
            return self._load_template(source_id, runtime_dir)
        if source_type == "session":
            if not source_id:
                raise ValueError("source_id/name/workspace is required for session diagrams")
            return self._load_session(source_id, runtime_dir)
        if source_type == "text":
            content = str(self.args.get("content", "")).strip()
            if not content:
                raise ValueError("content is required for text diagrams")
            title = source_id or str(self.args.get("title", "Ad hoc diagram"))
            nodes, edges = nodes_from_text(content, title=title)
            return title, nodes, edges, runtime_dir / "diagrams" / "ad_hoc"
        raise ValueError("source_type must be `template`, `session`, or `text`")

    def _load_template(self, template_name: str, runtime_dir: Path):
        registry_path = runtime_dir / "knowledge" / "workflows" / "template_registry.json"
        if not registry_path.exists():
            raise ValueError(f"template registry not found: {registry_path}")
        registry = json.loads(files.read_file(str(registry_path)))
        templates = registry.get("templates") or {}
        if template_name not in templates:
            raise ValueError(f"template `{template_name}` not found")
        entry = templates[template_name]
        template_file = entry.get("file", f"{template_name}.md")
        template_path = runtime_dir / "knowledge" / "workflows" / template_file
        content = files.read_file(str(template_path)) if template_path.exists() else ""
        nodes, edges = nodes_from_template(template_name, entry, content)
        title = entry.get("description") or template_name
        return title, nodes, edges, runtime_dir / "diagrams" / "templates" / files.safe_file_name(template_name)

    def _load_session(self, workspace_name: str, runtime_dir: Path):
        safe_name = files.safe_file_name(workspace_name)
        session_path = runtime_dir / "sessions" / "active" / safe_name / "workspace.json"
        if not session_path.exists():
            raise ValueError(f"active session not found: {session_path}")
        workspace = json.loads(files.read_file(str(session_path)))
        nodes, edges = nodes_from_session(workspace, VALID_SECTIONS)
        metadata = workspace.get("metadata") or {}
        title = metadata.get("name") or workspace_name
        return title, nodes, edges, session_path.parent / "diagrams"

    def _options(self) -> str:
        return "\n".join(
            [
                "## Pen & Paper Diagram Options",
                "",
                f"**Diagram types:** {', '.join(sorted(VALID_DIAGRAM_TYPES))}",
                f"**Themes:** {', '.join(sorted(THEMES))}",
                "",
                "**Source types:** template, session, text",
            ]
        )

    def _help(self) -> str:
        return "\n".join(
            [
                "## pen_paper_diagram",
                "",
                "Generate editable `.drawio` diagrams from Pen & Paper templates, live sessions, or ad hoc text.",
                "",
                "Examples:",
                "```json",
                '{"tool_name":"pen_paper_diagram","tool_args":{"source_type":"template","template_name":"debugging","diagram_type":"flow-vertical"}}',
                '{"tool_name":"pen_paper_diagram","tool_args":{"source_type":"session","name":"my_task","diagram_type":"layers","theme":"mint"}}',
                '{"tool_name":"pen_paper_diagram","tool_args":{"source_type":"text","content":"Plan -> Build -> Verify","diagram_type":"flow"}}',
                "```",
            ]
        )
