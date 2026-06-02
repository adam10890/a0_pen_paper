from helpers.api import ApiHandler
from flask import Request

from usr.plugins.a0_pen_paper.helpers.sessions_store import read_focus
from usr.plugins.a0_pen_paper.tools._config import load_plugin_config


class SessionsFocus(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict:
        try:
            chat_id = (input.get("chat_id") or "").strip() or None
            cfg = load_plugin_config()
            focus = read_focus(chat_id, cfg)
            return {"ok": True, "focus": focus}
        except Exception as e:
            return {"ok": False, "error": str(e)}
