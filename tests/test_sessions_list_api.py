"""
Tests for the sessions_list API handler's request-validation layer.

The handler is a thin wrapper: it turns request keys into list_sessions()
keyword arguments. Importing it requires Agent Zero's `helpers.api` and
`flask`, which are absent in a bare clone, so these tests exercise
`_optional_listing_kwargs` (the part that owns validation) directly, loading
the module by path with the Agent-Zero-only imports stubbed out.

Covered: absent keys produce no kwargs at all (so the call and the response
shape stay exactly as before), each control is parsed and coerced, and bad
types raise ValueError rather than reaching the store.
"""
from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parents[1]
if PLUGIN_DIR.parent.name == "plugins" and PLUGIN_DIR.parent.parent.name == "usr":
    ROOT = PLUGIN_DIR.parent.parent.parent
else:
    ROOT = PLUGIN_DIR
for path in (ROOT, PLUGIN_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


def _install_standalone_package_alias() -> None:
    if "usr.plugins.a0_pen_paper" in sys.modules:
        return
    usr = sys.modules.setdefault("usr", types.ModuleType("usr"))
    plugins = sys.modules.setdefault("usr.plugins", types.ModuleType("usr.plugins"))
    pkg = types.ModuleType("usr.plugins.a0_pen_paper")
    pkg.__path__ = [str(PLUGIN_DIR)]
    setattr(usr, "plugins", plugins)
    setattr(plugins, "a0_pen_paper", pkg)
    sys.modules["usr.plugins.a0_pen_paper"] = pkg


_install_standalone_package_alias()


def _load_handler_module():
    """Load api/sessions_list.py with its Agent-Zero-only imports stubbed."""
    if "helpers.api" not in sys.modules:
        helpers_pkg = sys.modules.setdefault("helpers", types.ModuleType("helpers"))
        if not hasattr(helpers_pkg, "__path__"):
            helpers_pkg.__path__ = []  # type: ignore[attr-defined]
        api_mod = types.ModuleType("helpers.api")

        class _ApiHandler:  # minimal stand-in for the AZ base class
            pass

        api_mod.ApiHandler = _ApiHandler
        sys.modules["helpers.api"] = api_mod
        setattr(helpers_pkg, "api", api_mod)
    if "flask" not in sys.modules:
        flask_mod = types.ModuleType("flask")
        flask_mod.Request = object
        sys.modules["flask"] = flask_mod

    spec = importlib.util.spec_from_file_location(
        "_pp_sessions_list_api", PLUGIN_DIR / "api" / "sessions_list.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_handler = _load_handler_module()
_optional_listing_kwargs = _handler._optional_listing_kwargs


class OptionalListingKwargsTests(unittest.TestCase):
    def test_empty_request_produces_no_kwargs(self):
        # The critical back-compat case: a request that sends none of the new
        # controls must call list_sessions() exactly as it did before.
        self.assertEqual(_optional_listing_kwargs({}), {})

    def test_only_chat_keys_produce_no_kwargs(self):
        self.assertEqual(
            _optional_listing_kwargs({"chat_id": "c1", "chat_only": True}), {}
        )

    def test_include_archived_is_coerced_to_bool(self):
        self.assertEqual(
            _optional_listing_kwargs({"include_archived": True}),
            {"include_archived": True},
        )
        self.assertEqual(
            _optional_listing_kwargs({"include_archived": False}),
            {"include_archived": False},
        )

    def test_page_size_accepts_int_and_numeric_string(self):
        self.assertEqual(_optional_listing_kwargs({"page_size": 25}), {"page_size": 25})
        self.assertEqual(_optional_listing_kwargs({"page_size": "25"}), {"page_size": 25})

    def test_page_size_rejects_non_numeric(self):
        with self.assertRaises(ValueError):
            _optional_listing_kwargs({"page_size": "many"})

    def test_page_token_must_be_string(self):
        self.assertEqual(
            _optional_listing_kwargs({"page_token": "abc"}), {"page_token": "abc"}
        )
        with self.assertRaises(ValueError):
            _optional_listing_kwargs({"page_token": 5})

    def test_order_by_must_be_string(self):
        self.assertEqual(
            _optional_listing_kwargs({"order_by": "name asc"}), {"order_by": "name asc"}
        )
        with self.assertRaises(ValueError):
            _optional_listing_kwargs({"order_by": ["name"]})

    def test_filter_must_be_object(self):
        self.assertEqual(
            _optional_listing_kwargs({"filter": {"state": "ARCHIVED"}}),
            {"filter": {"state": "ARCHIVED"}},
        )
        with self.assertRaises(ValueError):
            _optional_listing_kwargs({"filter": "state == ARCHIVED"})

    def test_all_controls_together(self):
        self.assertEqual(
            _optional_listing_kwargs(
                {
                    "include_archived": True,
                    "page_size": 10,
                    "page_token": "tok",
                    "order_by": "mtime desc",
                    "filter": {"has_code": True},
                }
            ),
            {
                "include_archived": True,
                "page_size": 10,
                "page_token": "tok",
                "order_by": "mtime desc",
                "filter": {"has_code": True},
            },
        )


class HandlerSignatureIntersectionTests(unittest.TestCase):
    """The handler drops controls the loaded store does not implement, so a
    newer client cannot break an older plugin build."""

    def test_store_signature_supports_every_exposed_control(self):
        import inspect

        from usr.plugins.a0_pen_paper.helpers import sessions_store

        params = inspect.signature(sessions_store.list_sessions).parameters
        for key in (
            "include_archived",
            "page_size",
            "page_token",
            "order_by",
            "filter",
        ):
            self.assertIn(key, params, f"list_sessions() is missing {key!r}")


if __name__ == "__main__":
    unittest.main()
