from helpers.api import ApiHandler
from flask import Request

from usr.plugins.a0_pen_paper.helpers.workflows_store import delete_template
from usr.plugins.a0_pen_paper.tools._config import load_plugin_config


class WorkflowsDelete(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict:
        try:
            payload = input.get("data") or input
            name = (payload.get("template_name") or "").strip()
            if not name:
                return {"ok": False, "error": "template_name required"}
            cfg = load_plugin_config()
            return delete_template(name, cfg)
        except Exception as e:
            return {"ok": False, "error": str(e)}
