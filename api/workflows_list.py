from helpers.api import ApiHandler
from flask import Request

from usr.plugins.a0_pen_paper.helpers.workflows_store import list_templates
from usr.plugins.a0_pen_paper.tools._config import load_plugin_config


class WorkflowsList(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict:
        try:
            cfg = load_plugin_config()
            data = list_templates(cfg)
            return {"ok": True, **data}
        except Exception as e:
            return {"ok": False, "error": str(e)}
