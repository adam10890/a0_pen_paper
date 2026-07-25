import inspect

from helpers.api import ApiHandler
from flask import Request

from usr.plugins.a0_pen_paper.helpers import sessions_store
from usr.plugins.a0_pen_paper.tools._config import load_plugin_config


def _optional_listing_kwargs(input: dict) -> dict:
    """Collect the optional listing controls actually supplied by the caller.

    Only keys present in the request are returned, so a request that sends
    none of them calls list_sessions() exactly as before and gets the
    unchanged response shape (no next_page_token key).
    """
    kwargs: dict = {}

    if input.get("include_archived") is not None:
        kwargs["include_archived"] = bool(input["include_archived"])

    if input.get("page_size") is not None:
        try:
            kwargs["page_size"] = int(input["page_size"])
        except (TypeError, ValueError):
            raise ValueError("page_size must be an integer")

    page_token = input.get("page_token")
    if page_token is not None:
        if not isinstance(page_token, str):
            raise ValueError("page_token must be a string")
        kwargs["page_token"] = page_token

    order_by = input.get("order_by")
    if order_by is not None:
        if not isinstance(order_by, str):
            raise ValueError("order_by must be a string")
        kwargs["order_by"] = order_by

    filter_arg = input.get("filter")
    if filter_arg is not None:
        if not isinstance(filter_arg, dict):
            raise ValueError("filter must be an object")
        kwargs["filter"] = filter_arg

    return kwargs


class SessionsList(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict:
        try:
            cfg = load_plugin_config()
            chat_id = (input.get("chat_id") or "").strip() or None
            chat_only = bool(input.get("chat_only"))
            optional = _optional_listing_kwargs(input)

            list_fn = sessions_store.list_sessions
            params = inspect.signature(list_fn).parameters
            if "chat_only" not in params:
                # Stale module in long-running process — reload once
                import importlib

                importlib.reload(sessions_store)
                list_fn = sessions_store.list_sessions
                params = inspect.signature(list_fn).parameters

            if "chat_only" in params:
                # Drop controls the loaded module does not implement, so a
                # newer client cannot break an older plugin build.
                supported = {k: v for k, v in optional.items() if k in params}
                data = list_fn(cfg, chat_id, chat_only=chat_only, **supported)
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
        except ValueError as e:
            return {"ok": False, "error": str(e)}
        except Exception as e:
            return {"ok": False, "error": str(e)}
