from helpers.api import ApiHandler
from flask import Request

from usr.plugins.a0_pen_paper.helpers.sessions_store import write_focus
from usr.plugins.a0_pen_paper.tools._config import load_plugin_config


class SessionsSetFocus(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict:
        try:
            workspace = (input.get("workspace") or "").strip()
            if not workspace:
                return {"ok": False, "error": "workspace is required"}
            section = (input.get("section") or "notes").strip()
            chat_id = (input.get("chat_id") or "").strip() or None
            cfg = load_plugin_config()
            focus = write_focus(
                workspace=workspace,
                section=section,
                action="ui_pin",
                chat_id=chat_id,
                cfg=cfg,
            )
            return {"ok": True, "focus": focus}
        except ValueError as e:
            return {"ok": False, "error": str(e)}
        except Exception as e:
            return {"ok": False, "error": str(e)}
