from helpers.api import ApiHandler
from flask import Request

from usr.plugins.a0_pen_paper.helpers.workflows_store import get_template
from usr.plugins.a0_pen_paper.tools._config import load_plugin_config


class WorkflowsGet(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict:
        try:
            payload = input.get("data") or input
            name = (payload.get("template_name") or "").strip()
            if not name:
                return {"ok": False, "error": "template_name required"}
            cfg = load_plugin_config()
            tpl = get_template(name, cfg)
            if not tpl:
                return {"ok": False, "error": f"Template '{name}' not found"}
            return {"ok": True, "template": tpl}
        except Exception as e:
            return {"ok": False, "error": str(e)}
