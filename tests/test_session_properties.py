"""
Tests for the computed `properties` field on sessions returned by
list_sessions() (inspired by usememos/memos' Property submessage), so a
client/agent can triage sessions without opening and parsing every record.

Covers each property flipping true/false on representative content, the
has_task_list vs has_incomplete_tasks distinction, title fallback to the
session name, and crash-safety on malformed workspace content.
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


def _write_workspace(path: Path, *, name: str, sections: dict | None = None) -> None:
    metadata = {
        "name": name,
        "status": "active",
        "chat_id": "chat-1",
        "created_at": "2026-01-01T00:00:00+00:00",
    }
    workspace: dict = {"metadata": metadata}
    for sec in sessions_store.VALID_SECTIONS:
        workspace[sec] = []
    if sections:
        workspace.update(sections)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(workspace, indent=2), encoding="utf-8")


def _entry(content: str) -> dict:
    return {"content": content, "source": "test", "author": "user"}


class SessionPropertiesTests(unittest.TestCase):
    def _list_one(self, cfg: dict, name: str) -> dict:
        data = sessions_store.list_sessions(cfg)
        by_name = {s["name"]: s for s in data["sessions"]}
        self.assertIn(name, by_name)
        return by_name[name]

    def test_has_link_true_for_url_and_markdown_link(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(
                wf,
                name="demo",
                sections={"notes": [_entry("see https://example.com for details")]},
            )
            row = self._list_one(cfg, "demo")
            self.assertTrue(row["properties"]["has_link"])

    def test_has_link_false_without_url_or_link(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(wf, name="demo", sections={"notes": [_entry("plain text note")]})
            row = self._list_one(cfg, "demo")
            self.assertFalse(row["properties"]["has_link"])

    def test_has_code_true_for_fenced_code_block(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(
                wf,
                name="demo",
                sections={"findings": [_entry("```python\nprint('hi')\n```")]},
            )
            row = self._list_one(cfg, "demo")
            self.assertTrue(row["properties"]["has_code"])

    def test_has_code_false_without_fence(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(wf, name="demo", sections={"findings": [_entry("no code here")]})
            row = self._list_one(cfg, "demo")
            self.assertFalse(row["properties"]["has_code"])

    def test_task_list_true_and_incomplete_tasks_true_with_unchecked_box(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(
                wf,
                name="demo",
                sections={"notes": [_entry("- [x] done thing\n- [ ] todo thing")]},
            )
            row = self._list_one(cfg, "demo")
            self.assertTrue(row["properties"]["has_task_list"])
            self.assertTrue(row["properties"]["has_incomplete_tasks"])

    def test_task_list_true_but_incomplete_tasks_false_when_all_checked(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(
                wf,
                name="demo",
                sections={"notes": [_entry("- [x] first\n- [X] second")]},
            )
            row = self._list_one(cfg, "demo")
            self.assertTrue(row["properties"]["has_task_list"])
            self.assertFalse(row["properties"]["has_incomplete_tasks"])

    def test_has_task_list_false_without_checkboxes(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(wf, name="demo", sections={"notes": [_entry("just a bullet list")]})
            row = self._list_one(cfg, "demo")
            self.assertFalse(row["properties"]["has_task_list"])
            self.assertFalse(row["properties"]["has_incomplete_tasks"])

    def test_has_execution_log_true_when_section_non_empty(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(
                wf, name="demo", sections={"execution_log": [_entry("ran the tests")]}
            )
            row = self._list_one(cfg, "demo")
            self.assertTrue(row["properties"]["has_execution_log"])

    def test_has_execution_log_false_when_section_empty(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(wf, name="demo")
            row = self._list_one(cfg, "demo")
            self.assertFalse(row["properties"]["has_execution_log"])

    def test_has_backtrack_true_when_section_non_empty(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(
                wf, name="demo", sections={"backtrack": [_entry("reverted approach X")]}
            )
            row = self._list_one(cfg, "demo")
            self.assertTrue(row["properties"]["has_backtrack"])

    def test_has_backtrack_false_when_section_empty(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(wf, name="demo")
            row = self._list_one(cfg, "demo")
            self.assertFalse(row["properties"]["has_backtrack"])

    def test_title_extracted_from_first_h1(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(
                wf,
                name="demo",
                sections={
                    "findings": [_entry("# The Real Title\n\nsome body text")],
                    "notes": [_entry("# Second Heading Should Be Ignored")],
                },
            )
            row = self._list_one(cfg, "demo")
            self.assertEqual(row["properties"]["title"], "The Real Title")

    def test_title_falls_back_to_session_name_without_h1(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(
                wf, name="demo", sections={"notes": [_entry("no heading in here at all")]}
            )
            row = self._list_one(cfg, "demo")
            self.assertEqual(row["properties"]["title"], "demo")

    def test_title_ignores_h2_and_falls_back_to_name(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(
                wf, name="demo", sections={"notes": [_entry("## Just a subheading")]}
            )
            row = self._list_one(cfg, "demo")
            self.assertEqual(row["properties"]["title"], "demo")

    def test_existing_keys_are_preserved_alongside_new_properties_key(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(wf, name="demo")
            row = self._list_one(cfg, "demo")
            for key in (
                "name",
                "status",
                "state",
                "template",
                "chat_id",
                "created",
                "mtime",
                "etag",
                "section_counts",
                "is_current_chat",
                "is_chat_focus",
                "is_orphan",
            ):
                self.assertIn(key, row)
            self.assertIn("properties", row)

    def test_malformed_non_list_section_does_not_raise_and_still_lists(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(wf, name="demo")
            raw = json.loads(wf.read_text(encoding="utf-8"))
            raw["notes"] = "not a list"  # malformed: section should be a list
            raw["execution_log"] = {"oops": "dict, not list"}
            wf.write_text(json.dumps(raw, indent=2), encoding="utf-8")

            data = sessions_store.list_sessions(cfg)

            row = next(s for s in data["sessions"] if s["name"] == "demo")
            self.assertEqual(row["properties"]["title"], "demo")
            self.assertFalse(row["properties"]["has_execution_log"])

    def test_malformed_non_string_entries_do_not_raise_and_still_lists(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(wf, name="demo")
            raw = json.loads(wf.read_text(encoding="utf-8"))
            # malformed entries: numbers, None, lists nested inside a section list.
            raw["notes"] = [123, None, ["nested", "list"], {"content": None}]
            wf.write_text(json.dumps(raw, indent=2), encoding="utf-8")

            data = sessions_store.list_sessions(cfg)

            row = next(s for s in data["sessions"] if s["name"] == "demo")
            self.assertIn("properties", row)
            self.assertIsInstance(row["properties"]["has_link"], bool)


if __name__ == "__main__":
    unittest.main()
