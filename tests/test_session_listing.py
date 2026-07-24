"""
Tests for filter / order_by / pagination on list_sessions() (inspired by
usememos/memos' ListMemosRequest: page_size, page_token, order_by, filter).

This deliberately does NOT implement CEL: `filter` is a small structured dict
of AND-ed conditions over a closed set of keys (see sessions_store._FILTER_KEYS).

Covers, in order of priority:
- the critical back-compat guarantee: omitting all four new keyword params
  reproduces the exact pre-existing list_sessions() output
- pagination partitions the filtered/ordered set with no overlap and no gaps,
  and the last page carries no next_page_token
- page_size bounds (non-positive rejected, over-max clamped rather than erroring)
- order_by for each supported field, both directions
- each filter key (including a computed property and relation_target), and
  that an unknown filter key raises
- an invalid/stale page_token raises
- include_archived + filter={"state": ...} precedence (include_archived decides
  scan scope; filter narrows within that scope, it never widens it)
"""
from __future__ import annotations

import json
import sys
import types
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

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

from usr.plugins.a0_pen_paper.helpers import sessions_store


def _write_workspace(
    path: Path,
    *,
    name: str,
    status: str = "active",
    chat_id: str | None = "chat-1",
    created_at: str = "2026-01-01T00:00:00+00:00",
    template: str | None = None,
    mtime: float | None = None,
    extra_metadata: dict | None = None,
    sections: dict | None = None,
    extra: dict | None = None,
) -> None:
    metadata = {
        "name": name,
        "status": status,
        "chat_id": chat_id,
        "created_at": created_at,
        "template": template,
    }
    if extra_metadata:
        metadata.update(extra_metadata)
    workspace: dict = {"metadata": metadata}
    for sec in sessions_store.VALID_SECTIONS:
        workspace[sec] = []
    if sections:
        workspace.update(sections)
    if extra:
        workspace.update(extra)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(workspace, indent=2), encoding="utf-8")
    if mtime is not None:
        import os

        os.utime(path, (mtime, mtime))


def _entry(content: str) -> dict:
    return {"content": content, "source": "test", "author": "user"}


class BackCompatByteIdenticalTests(unittest.TestCase):
    """The single most important test in this module: omitting the four new
    keyword params must reproduce the exact pre-existing output."""

    def _seed(self, cfg: dict) -> None:
        _write_workspace(
            sessions_store.sessions_dir(cfg) / "alpha" / "workspace.json",
            name="alpha",
            chat_id="chat-1",
            mtime=1_700_000_030,
        )
        _write_workspace(
            sessions_store.sessions_dir(cfg) / "bravo" / "workspace.json",
            name="bravo",
            chat_id="chat-2",
            mtime=1_700_000_010,
        )
        _write_workspace(
            sessions_store.sessions_dir(cfg) / "charlie" / "workspace.json",
            name="charlie",
            chat_id=None,
            mtime=1_700_000_020,
        )
        sessions_store.write_focus(workspace="bravo", chat_id="chat-1", cfg=cfg)

    def test_defaults_are_true_no_ops_for_every_chat_only_combo(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            self._seed(cfg)

            for chat_id in (None, "chat-1", "chat-2"):
                for chat_only in (False, True):
                    with self.subTest(chat_id=chat_id, chat_only=chat_only):
                        old_style = sessions_store.list_sessions(
                            cfg, chat_id, chat_only=chat_only
                        )
                        explicit_defaults = sessions_store.list_sessions(
                            cfg,
                            chat_id,
                            chat_only=chat_only,
                            include_archived=False,
                            page_size=None,
                            page_token=None,
                            order_by=None,
                            filter=None,
                        )
                        self.assertEqual(old_style, explicit_defaults)

    def test_default_ordering_unchanged_focus_first_current_chat_first_mtime_desc(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            self._seed(cfg)

            data = sessions_store.list_sessions(cfg, "chat-1")
            names = [s["name"] for s in data["sessions"]]
            # bravo is chat-focused for chat-1 -> first; alpha is current chat -> second;
            # charlie (orphan, not focused, not current) -> last.
            self.assertEqual(names, ["bravo", "alpha", "charlie"])


class PaginationTests(unittest.TestCase):
    def _seed_five(self, cfg: dict) -> list[str]:
        names = ["s1", "s2", "s3", "s4", "s5"]
        for i, name in enumerate(names):
            _write_workspace(
                sessions_store.sessions_dir(cfg) / name / "workspace.json",
                name=name,
                mtime=1_700_000_000 + i * 10,
            )
        return names

    def test_pages_partition_with_no_overlap_and_no_gaps_and_last_page_has_no_token(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            self._seed_five(cfg)

            collected: list[str] = []
            token = None
            pages = 0
            while True:
                data = sessions_store.list_sessions(
                    cfg, page_size=2, page_token=token, order_by="name asc"
                )
                names = [s["name"] for s in data["sessions"]]
                collected.extend(names)
                pages += 1
                token = data.get("next_page_token")
                self.assertIn("next_page_token", data)
                if token is None:
                    break
                self.assertLessEqual(pages, 10)  # guard against infinite loop on a bug

            self.assertEqual(collected, ["s1", "s2", "s3", "s4", "s5"])
            self.assertEqual(pages, 3)  # 2 + 2 + 1

    def test_no_page_size_means_no_pagination_and_no_next_page_token_key(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            self._seed_five(cfg)

            data = sessions_store.list_sessions(cfg)

            self.assertEqual(len(data["sessions"]), 5)
            self.assertNotIn("next_page_token", data)

    def test_page_token_requires_page_size(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            self._seed_five(cfg)
            data = sessions_store.list_sessions(cfg, page_size=2)
            token = data["next_page_token"]

            with self.assertRaises(ValueError):
                sessions_store.list_sessions(cfg, page_token=token)

    def test_stale_page_token_from_different_query_shape_raises(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            self._seed_five(cfg)
            data = sessions_store.list_sessions(cfg, page_size=2, order_by="name asc")
            token = data["next_page_token"]

            with self.assertRaises(ValueError):
                # Same token, different order_by -> must not silently reinterpret offset.
                sessions_store.list_sessions(cfg, page_size=2, page_token=token, order_by="name desc")

    def test_malformed_page_token_raises(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            self._seed_five(cfg)

            with self.assertRaises(ValueError):
                sessions_store.list_sessions(cfg, page_size=2, page_token="not-a-valid-token!!")


class PageSizeBoundsTests(unittest.TestCase):
    def test_zero_page_size_rejected(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            with self.assertRaises(ValueError):
                sessions_store.list_sessions(cfg, page_size=0)

    def test_negative_page_size_rejected(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            with self.assertRaises(ValueError):
                sessions_store.list_sessions(cfg, page_size=-3)

    def test_over_max_page_size_is_clamped_not_rejected(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            _write_workspace(
                sessions_store.sessions_dir(cfg) / "only" / "workspace.json", name="only"
            )
            # Documented rule: page_size above PAGE_SIZE_MAX (1000) is clamped
            # down to the max rather than raising.
            data = sessions_store.list_sessions(cfg, page_size=10_000)
            self.assertEqual(len(data["sessions"]), 1)
            self.assertIsNone(data["next_page_token"])


class OrderByTests(unittest.TestCase):
    def _seed(self, cfg: dict) -> None:
        # mtime, created, and name orderings are all deliberately different from
        # one another so each order_by field is independently exercised.
        _write_workspace(
            sessions_store.sessions_dir(cfg) / "alpha" / "workspace.json",
            name="alpha",
            created_at="2026-01-03T00:00:00+00:00",
            mtime=1_700_000_030,
        )
        _write_workspace(
            sessions_store.sessions_dir(cfg) / "bravo" / "workspace.json",
            name="bravo",
            created_at="2026-01-02T00:00:00+00:00",
            mtime=1_700_000_010,
        )
        _write_workspace(
            sessions_store.sessions_dir(cfg) / "charlie" / "workspace.json",
            name="charlie",
            created_at="2026-01-01T00:00:00+00:00",
            mtime=1_700_000_020,
        )

    def _names(self, cfg: dict, order_by: str) -> list[str]:
        data = sessions_store.list_sessions(cfg, order_by=order_by)
        return [s["name"] for s in data["sessions"]]

    def test_name_asc_and_desc(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            self._seed(cfg)
            self.assertEqual(self._names(cfg, "name asc"), ["alpha", "bravo", "charlie"])
            self.assertEqual(self._names(cfg, "name desc"), ["charlie", "bravo", "alpha"])
            # No direction suffix defaults to ascending (SQL ORDER BY convention).
            self.assertEqual(self._names(cfg, "name"), ["alpha", "bravo", "charlie"])

    def test_mtime_asc_and_desc(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            self._seed(cfg)
            self.assertEqual(self._names(cfg, "mtime asc"), ["bravo", "charlie", "alpha"])
            self.assertEqual(self._names(cfg, "mtime desc"), ["alpha", "charlie", "bravo"])

    def test_created_asc_and_desc(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            self._seed(cfg)
            self.assertEqual(self._names(cfg, "created asc"), ["charlie", "bravo", "alpha"])
            self.assertEqual(self._names(cfg, "created desc"), ["alpha", "bravo", "charlie"])

    def test_invalid_order_by_field_raises(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            self._seed(cfg)
            with self.assertRaises(ValueError):
                sessions_store.list_sessions(cfg, order_by="bogus_field")

    def test_invalid_order_by_direction_raises(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            self._seed(cfg)
            with self.assertRaises(ValueError):
                sessions_store.list_sessions(cfg, order_by="name up")

    def test_too_many_order_by_tokens_raises(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            self._seed(cfg)
            with self.assertRaises(ValueError):
                sessions_store.list_sessions(cfg, order_by="name asc extra")


class FilterTests(unittest.TestCase):
    def test_filter_by_status(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            _write_workspace(
                sessions_store.sessions_dir(cfg) / "a" / "workspace.json", name="a", status="active"
            )
            _write_workspace(
                sessions_store.sessions_dir(cfg) / "b" / "workspace.json", name="b", status="closed"
            )
            data = sessions_store.list_sessions(cfg, filter={"status": "closed"})
            self.assertEqual([s["name"] for s in data["sessions"]], ["b"])

    def test_filter_by_template(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            _write_workspace(
                sessions_store.sessions_dir(cfg) / "a" / "workspace.json", name="a", template="t1"
            )
            _write_workspace(
                sessions_store.sessions_dir(cfg) / "b" / "workspace.json", name="b", template="t2"
            )
            data = sessions_store.list_sessions(cfg, filter={"template": "t2"})
            self.assertEqual([s["name"] for s in data["sessions"]], ["b"])

    def test_filter_by_chat_id(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            _write_workspace(
                sessions_store.sessions_dir(cfg) / "a" / "workspace.json", name="a", chat_id="chat-x"
            )
            _write_workspace(
                sessions_store.sessions_dir(cfg) / "b" / "workspace.json", name="b", chat_id="chat-y"
            )
            data = sessions_store.list_sessions(cfg, filter={"chat_id": "chat-y"})
            self.assertEqual([s["name"] for s in data["sessions"]], ["b"])

    def test_filter_by_name_contains_case_insensitive(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            _write_workspace(
                sessions_store.sessions_dir(cfg) / "debug-session" / "workspace.json",
                name="debug-session",
            )
            _write_workspace(
                sessions_store.sessions_dir(cfg) / "planning-session" / "workspace.json",
                name="planning-session",
            )
            data = sessions_store.list_sessions(cfg, filter={"name_contains": "DEBUG"})
            self.assertEqual([s["name"] for s in data["sessions"]], ["debug-session"])

    def test_filter_by_computed_property_has_code(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            _write_workspace(
                sessions_store.sessions_dir(cfg) / "a" / "workspace.json",
                name="a",
                sections={"findings": [_entry("```python\nprint(1)\n```")]},
            )
            _write_workspace(
                sessions_store.sessions_dir(cfg) / "b" / "workspace.json",
                name="b",
                sections={"findings": [_entry("plain text")]},
            )
            data = sessions_store.list_sessions(cfg, filter={"has_code": True})
            self.assertEqual([s["name"] for s in data["sessions"]], ["a"])
            data_false = sessions_store.list_sessions(cfg, filter={"has_code": False})
            self.assertEqual([s["name"] for s in data_false["sessions"]], ["b"])

    def test_filter_by_has_relations_and_relation_target(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            _write_workspace(
                sessions_store.sessions_dir(cfg) / "a" / "workspace.json",
                name="a",
                extra={"relations": [{"type": "REFERENCE", "target": "other-x"}]},
            )
            _write_workspace(
                sessions_store.sessions_dir(cfg) / "b" / "workspace.json", name="b"
            )
            has_rel = sessions_store.list_sessions(cfg, filter={"has_relations": True})
            self.assertEqual([s["name"] for s in has_rel["sessions"]], ["a"])
            no_rel = sessions_store.list_sessions(cfg, filter={"has_relations": False})
            self.assertEqual([s["name"] for s in no_rel["sessions"]], ["b"])
            by_target = sessions_store.list_sessions(cfg, filter={"relation_target": "other-x"})
            self.assertEqual([s["name"] for s in by_target["sessions"]], ["a"])

    def test_unknown_filter_key_raises(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            _write_workspace(sessions_store.sessions_dir(cfg) / "a" / "workspace.json", name="a")
            with self.assertRaises(ValueError):
                sessions_store.list_sessions(cfg, filter={"totally_bogus_key": True})

    def test_filter_and_order_by_and_pagination_compose(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            for i, name in enumerate(["a1", "a2", "a3", "b1"]):
                _write_workspace(
                    sessions_store.sessions_dir(cfg) / name / "workspace.json",
                    name=name,
                    mtime=1_700_000_000 + i * 10,
                )
            data = sessions_store.list_sessions(
                cfg,
                filter={"name_contains": "a"},
                order_by="name asc",
                page_size=2,
            )
            self.assertEqual([s["name"] for s in data["sessions"]], ["a1", "a2"])
            self.assertEqual(data["visible_count"], 3)  # a1, a2, a3 match; b1 filtered out
            self.assertIsNotNone(data["next_page_token"])

            data2 = sessions_store.list_sessions(
                cfg,
                filter={"name_contains": "a"},
                order_by="name asc",
                page_size=2,
                page_token=data["next_page_token"],
            )
            self.assertEqual([s["name"] for s in data2["sessions"]], ["a3"])
            self.assertIsNone(data2["next_page_token"])


class IncludeArchivedAndStateFilterPrecedenceTests(unittest.TestCase):
    def _seed(self, cfg: dict) -> None:
        _write_workspace(
            sessions_store.sessions_dir(cfg) / "active-one" / "workspace.json", name="active-one"
        )
        _write_workspace(
            sessions_store.archive_dir(cfg) / "archived-one" / "workspace.json", name="archived-one"
        )

    def test_state_archived_filter_without_include_archived_returns_empty(self):
        """include_archived controls which directories are scanned; filter narrows
        within whatever was scanned but never widens scope. Without
        include_archived=True the archive directory is never scanned, so
        filter={"state": "ARCHIVED"} matches nothing."""
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            self._seed(cfg)
            data = sessions_store.list_sessions(cfg, filter={"state": "ARCHIVED"})
            self.assertEqual(data["sessions"], [])

    def test_state_archived_filter_with_include_archived_returns_only_archived(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            self._seed(cfg)
            data = sessions_store.list_sessions(
                cfg, include_archived=True, filter={"state": "ARCHIVED"}
            )
            self.assertEqual([s["name"] for s in data["sessions"]], ["archived-one"])

    def test_state_normal_filter_with_include_archived_excludes_archived(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            self._seed(cfg)
            data = sessions_store.list_sessions(
                cfg, include_archived=True, filter={"state": "NORMAL"}
            )
            self.assertEqual([s["name"] for s in data["sessions"]], ["active-one"])

    def test_include_archived_alone_still_returns_both(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            self._seed(cfg)
            data = sessions_store.list_sessions(cfg, include_archived=True)
            names = {s["name"] for s in data["sessions"]}
            self.assertEqual(names, {"active-one", "archived-one"})


if __name__ == "__main__":
    unittest.main()
