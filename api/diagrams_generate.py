from __future__ import annotations

from datetime import datetime
from pathlib import Path

from flask import Request
from helpers.api import ApiHandler
from helpers import files

from usr.plugins.a0_pen_paper.helpers.diagram_generator import (
    THEMES,
    VALID_DIAGRAM_TYPES,
    ascii_sketch,
    build_drawio_xml,
)
from usr.plugins.a0_pen_paper.helpers.diagram_sources import load_diagram_source, safe_name
from usr.plugins.a0_pen_paper.tools._config import load_plugin_config, runtime_base


class DiagramsGenerate(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict:
        try:
            payload = input.get("data") or input
            source_type = str(payload.get("source_type") or "template").strip().lower()
            source_id = str(
                payload.get("source_id")
                or payload.get("template_name")
                or payload.get("workspace")
                or payload.get("name")
                or ""
            ).strip()
            diagram_type = str(payload.get("diagram_type") or "flow").strip()
            theme = str(payload.get("theme") or "tech-blue").strip()
            content = str(payload.get("content") or "").strip()
            output_name = str(payload.get("output_name") or "").strip()

            if diagram_type not in VALID_DIAGRAM_TYPES:
                return {"ok": False, "error": f"invalid diagram_type: {diagram_type}"}
            if theme not in THEMES:
                return {"ok": False, "error": f"invalid theme: {theme}"}

            cfg = load_plugin_config()
            runtime_dir = Path(files.get_abs_path(runtime_base(cfg)))
            title, nodes, edges, output_dir = load_diagram_source(
                runtime_dir=runtime_dir,
                source_type=source_type,
                source_id=source_id,
                content=content,
            )

            if not output_name:
                stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_name = f"{source_type}_{source_id or 'ad_hoc'}_{diagram_type}_{stamp}"
            output_path = output_dir / f"{safe_name(output_name)}.drawio"
            output_path.parent.mkdir(parents=True, exist_ok=True)

            xml = build_drawio_xml(
                title=title,
                nodes=nodes,
                edges=edges,
                diagram_type=diagram_type,
                theme_name=theme,
            )
            output_path.write_text(xml, encoding="utf-8")

            return {
                "ok": True,
                "path": str(output_path),
                "source_type": source_type,
                "source_id": source_id or "content",
                "diagram_type": diagram_type,
                "theme": theme,
                "nodes": len(nodes),
                "edges": len(edges),
                "sketch": ascii_sketch(nodes, diagram_type),
                "xml": xml,
            }
        except FileNotFoundError as e:
            return {"ok": False, "error": str(e)}
        except ValueError as e:
            return {"ok": False, "error": str(e)}
        except Exception as e:
            return {"ok": False, "error": str(e)}
