from __future__ import annotations

from datetime import datetime
from pathlib import Path

from flask import Request
from helpers.api import ApiHandler
from helpers import files

from usr.plugins.a0_pen_paper.helpers.diagram_generator import (
    THEMES,
    VALID_DIAGRAM_TYPES,
    build_whiteboard_shapes,
)
from usr.plugins.a0_pen_paper.helpers.diagram_sources import load_diagram_source, safe_name
from usr.plugins.a0_pen_paper.tools._config import load_plugin_config, runtime_base


class DiagramsSendWhiteboard(ApiHandler):
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
            board_name = str(payload.get("board_name") or "").strip()

            if diagram_type not in VALID_DIAGRAM_TYPES:
                return {"ok": False, "error": f"invalid diagram_type: {diagram_type}"}
            if theme not in THEMES:
                return {"ok": False, "error": f"invalid theme: {theme}"}

            cfg = load_plugin_config()
            runtime_dir = Path(files.get_abs_path(runtime_base(cfg)))
            title, nodes, edges, _output_dir = load_diagram_source(
                runtime_dir=runtime_dir,
                source_type=source_type,
                source_id=source_id,
                content=content,
            )
            shapes = build_whiteboard_shapes(title, nodes, edges, diagram_type, theme)
            if not board_name:
                stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                board_name = safe_name(f"pnp_{source_type}_{source_id or 'ad_hoc'}_{stamp}")

            from usr.plugins.a0_whiteboard.helpers.whiteboard import (
                build_state_snapshot,
                get_shared_manager,
            )

            manager = get_shared_manager()
            await manager.apply_state({"shapes": shapes, "dataUrl": ""})
            save_result = await manager.save_board(board_name)
            if not save_result.success:
                return {"ok": False, "error": save_result.error or "whiteboard save failed"}
            await manager.broadcast_event(
                "whiteboard_state_change",
                build_state_snapshot(manager),
            )
            await manager.broadcast_event(
                "whiteboard_intent",
                {
                    "action": "create_shapes",
                    "data": {"shapes": shapes},
                    "metadata": {"source": "pen_paper"},
                },
            )
            return {
                "ok": True,
                "board_name": manager.current_board_name,
                "shape_count": len(shapes),
            }
        except FileNotFoundError as e:
            return {"ok": False, "error": str(e)}
        except ValueError as e:
            return {"ok": False, "error": str(e)}
        except ImportError as e:
            return {"ok": False, "error": f"a0_whiteboard is not available: {e}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}
