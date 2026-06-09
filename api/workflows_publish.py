from helpers.api import ApiHandler
from flask import Request

from usr.plugins.a0_pen_paper.helpers.workflows_store import publish_state_dox
from usr.plugins.a0_pen_paper.tools._config import load_plugin_config


class WorkflowsPublish(ApiHandler):
    """Publish an existing Workflows-UI template as a Scribe-readable State-DOX
    template. Thin wrapper over workflows_store.publish_state_dox()."""

    async def process(self, input: dict, request: Request) -> dict:
        try:
            payload = input.get("data") or input
            name = (payload.get("template_name") or "").strip()
            if not name:
                return {"ok": False, "error": "template_name required"}
            cfg = load_plugin_config()
            return publish_state_dox(
                name,
                activation_tags=payload.get("activation_tags") or [],
                skill=payload.get("skill"),
                title=payload.get("title"),
                title_he=payload.get("title_he"),
                contract=payload.get("contract"),
                cfg=cfg,
            )
        except Exception as e:
            return {"ok": False, "error": str(e)}
