from helpers.api import ApiHandler
from flask import Request

from usr.plugins.a0_pen_paper.helpers.sessions_store import append_section
from usr.plugins.a0_pen_paper.tools._config import load_plugin_config


class SessionsAppend(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict:
        try:
            workspace = (input.get("workspace") or "").strip()
            section = (input.get("section") or "notes").strip()
            content = input.get("content") or ""
            etag = (input.get("etag") or "").strip()
            if not workspace:
                return {"ok": False, "error": "workspace is required"}
            if not content.strip():
                return {"ok": False, "error": "content is required"}
            if not etag:
                return {"ok": False, "error": "etag is required"}
            cfg = load_plugin_config()
            result = append_section(workspace, section, content, etag, cfg=cfg)
            if not result.get("ok"):
                return result
            return result
        except FileNotFoundError as e:
            return {"ok": False, "error": str(e)}
        except ValueError as e:
            return {"ok": False, "error": str(e)}
        except Exception as e:
            return {"ok": False, "error": str(e)}
