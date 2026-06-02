"""
Update Live Session focus pointer after pen_paper tool calls.
"""
from __future__ import annotations

try:
    from helpers.extension import Extension
except ImportError:
    from python.helpers.extension import Extension  # type: ignore


class PenPaperFocus(Extension):
    async def execute(
        self,
        tool_name: str = "",
        tool_args: dict | None = None,
        response=None,
        **kwargs,
    ):
        if tool_name != "pen_paper":
            return
        args = tool_args or {}
        action = args.get("action", "")
        if action not in ("create", "use_template", "update", "read"):
            return
        workspace = (args.get("name") or "").strip()
        if not workspace:
            return
        section = (args.get("section") or "").strip() or None
        if action in ("create", "use_template"):
            section = section or "notes"
        elif action == "update":
            section = section or "notes"
        chat_id = None
        agent = getattr(self, "agent", None)
        if agent and getattr(agent, "context", None):
            chat_id = getattr(agent.context, "id", None)
        try:
            from usr.plugins.a0_pen_paper.helpers.sessions_store import write_focus

            write_focus(
                workspace=workspace,
                section=section,
                action=action,
                chat_id=chat_id,
            )
        except Exception:
            pass
