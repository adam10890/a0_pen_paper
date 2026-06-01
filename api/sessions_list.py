import inspect

from helpers.api import ApiHandler
from flask import Request

from usr.plugins.a0_pen_paper.helpers import sessions_store
from usr.plugins.a0_pen_paper.tools._config import load_plugin_config


class SessionsList(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict:
        try:
            cfg = load_plugin_config()
            chat_id = (input.get("chat_id") or "").strip() or None
            chat_only = bool(input.get("chat_only"))
            list_fn = sessions_store.list_sessions
            params = inspect.signature(list_fn).parameters
            if "chat_only" in params:
                data = list_fn(cfg, chat_id, chat_only=chat_only)
            else:
                # Stale module in long-running process — reload once
                import importlib

                importlib.reload(sessions_store)
                list_fn = sessions_store.list_sessions
                params = inspect.signature(list_fn).parameters
                if "chat_only" in params:
                    data = list_fn(cfg, chat_id, chat_only=chat_only)
                else:
                    legacy = list_fn(cfg)
                    if isinstance(legacy, dict):
                        data = legacy
                    else:
                        data = {
                            "sessions": legacy or [],
                            "total_count": len(legacy or []),
                            "visible_count": len(legacy or []),
                            "current_chat_id": chat_id,
                            "focus": {},
                        }
            return {"ok": True, **data}
        except Exception as e:
            return {"ok": False, "error": str(e)}
