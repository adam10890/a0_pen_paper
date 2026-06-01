from helpers.api import ApiHandler
from flask import Request

from usr.plugins.a0_pen_paper.helpers.sessions_store import get_session
from usr.plugins.a0_pen_paper.tools._config import load_plugin_config


class SessionsGet(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict:
        try:
            workspace = (input.get("workspace") or input.get("name") or "").strip()
            if not workspace:
                return {"ok": False, "error": "workspace is required"}
            section = (input.get("section") or "").strip() or None
            cfg = load_plugin_config()
            data = get_session(workspace, section, cfg)
            return {"ok": True, "session": data}
        except FileNotFoundError as e:
            return {"ok": False, "error": str(e)}
        except ValueError as e:
            return {"ok": False, "error": str(e)}
        except Exception as e:
            return {"ok": False, "error": str(e)}
