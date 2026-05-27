"""
Pre-tool hints for pen_paper workflow hooks (Wave 3 MVP).
"""
from __future__ import annotations

try:
    from helpers.extension import Extension
except ImportError:
    from python.helpers.extension import Extension  # type: ignore


class PenPaperWorkflowGuard(Extension):
    async def execute(self, tool_name: str = "", tool_args: dict | None = None, **kwargs):
        if tool_name != "pen_paper":
            return
        args = tool_args or {}
        action = args.get("action", "")
        if action not in ("create", "update", "close", "use_template"):
            return
        try:
            from usr.plugins.a0_pen_paper.helpers.workflow_executor import WorkflowExecutor

            ex = WorkflowExecutor()
            issues = ex.registry_status()
            if issues:
                agent = getattr(self, "agent", None)
                if agent and hasattr(agent, "hist_add_warning"):
                    agent.hist_add_warning(
                        "Pen & Paper registry integrity: " + "; ".join(issues[:3])
                    )
        except Exception:
            pass
