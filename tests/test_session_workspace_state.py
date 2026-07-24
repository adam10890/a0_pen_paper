"""
Tests for the additive `metadata.state` field on session workspaces
(NORMAL | ARCHIVED), inspired by usememos/memos.

Covers back-compat (old workspace.json files with no `state` field derive it
from the directory they live in), explicit-field precedence, and the
`include_archived` opt-in on list_sessions().
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


def _write_workspace(path: Path, *, name: str, extra_metadata: dict | None = None) -> None:
    metadata = {
        "name": name,
        "status": "active",
        "chat_id": "chat-1",
        "created_at": "2026-01-01T00:00:00+00:00",
    }
    if extra_metadata:
        metadata.update(extra_metadata)
    workspace = {"metadata": metadata}
    for sec in sessions_store.VALID_SECTIONS:
        workspace[sec] = []
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(workspace, indent=2), encoding="utf-8")


class WorkspaceStateBackCompatTests(unittest.TestCase):
    def test_workspace_without_state_in_active_dir_is_normal(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            cfg = {"runtime_dir": str(root / "pen_and_paper")}
            wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(wf, name="demo")

            state = sessions_store.get_workspace_state("demo", cfg=cfg)

            self.assertEqual(state, sessions_store.STATE_NORMAL)

    def test_workspace_without_state_in_archive_dir_is_archived(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            cfg = {"runtime_dir": str(root / "pen_and_paper")}
            wf = sessions_store.archive_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(wf, name="demo")

            state = sessions_store.get_workspace_state("demo", cfg=cfg)

            self.assertEqual(state, sessions_store.STATE_ARCHIVED)

    def test_explicit_state_wins_over_directory_fallback(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            cfg = {"runtime_dir": str(root / "pen_and_paper")}
            # Lives in the active directory but is explicitly marked ARCHIVED.
            wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(wf, name="demo", extra_metadata={"state": "ARCHIVED"})

            state = sessions_store.get_workspace_state("demo", cfg=cfg)

            self.assertEqual(state, sessions_store.STATE_ARCHIVED)

    def test_explicit_state_wins_even_when_it_contradicts_archive_dir(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            cfg = {"runtime_dir": str(root / "pen_and_paper")}
            # Lives in the archive directory but is explicitly marked NORMAL.
            wf = sessions_store.archive_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(wf, name="demo", extra_metadata={"state": "NORMAL"})

            state = sessions_store.get_workspace_state("demo", cfg=cfg)

            self.assertEqual(state, sessions_store.STATE_NORMAL)

    def test_set_workspace_state_writes_field_without_moving_file(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            cfg = {"runtime_dir": str(root / "pen_and_paper")}
            wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(wf, name="demo")

            result = sessions_store.set_workspace_state(
                "demo", sessions_store.STATE_ARCHIVED, cfg=cfg
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["state"], sessions_store.STATE_ARCHIVED)
            # File stays in sessions/active — only the field changed.
            self.assertTrue(wf.exists())
            written = json.loads(wf.read_text(encoding="utf-8"))
            self.assertEqual(written["metadata"]["state"], "ARCHIVED")
            self.assertEqual(
                sessions_store.get_workspace_state("demo", cfg=cfg),
                sessions_store.STATE_ARCHIVED,
            )

    def test_get_workspace_state_missing_workspace_raises(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            with self.assertRaises(FileNotFoundError):
                sessions_store.get_workspace_state("nope", cfg=cfg)

    def test_set_workspace_state_rejects_invalid_value(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            cfg = {"runtime_dir": str(root / "pen_and_paper")}
            wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(wf, name="demo")

            with self.assertRaises(ValueError):
                sessions_store.set_workspace_state("demo", "DELETED", cfg=cfg)


class ListSessionsStateTests(unittest.TestCase):
    def _seed(self, cfg: dict) -> None:
        active_wf = sessions_store.sessions_dir(cfg) / "active-one" / "workspace.json"
        _write_workspace(active_wf, name="active-one")
        archived_wf = sessions_store.archive_dir(cfg) / "archived-one" / "workspace.json"
        _write_workspace(archived_wf, name="archived-one")

    def test_default_list_sessions_returns_only_active_sessions(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            self._seed(cfg)

            data = sessions_store.list_sessions(cfg)

            names = {s["name"] for s in data["sessions"]}
            self.assertEqual(names, {"active-one"})
            self.assertEqual(data["sessions"][0]["state"], sessions_store.STATE_NORMAL)

    def test_include_archived_true_adds_archived_sessions_with_state(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            self._seed(cfg)

            data = sessions_store.list_sessions(cfg, include_archived=True)

            by_name = {s["name"]: s for s in data["sessions"]}
            self.assertEqual(set(by_name), {"active-one", "archived-one"})
            self.assertEqual(by_name["active-one"]["state"], sessions_store.STATE_NORMAL)
            self.assertEqual(by_name["archived-one"]["state"], sessions_store.STATE_ARCHIVED)

    def test_explicit_state_field_overrides_directory_in_list_sessions(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            wf = sessions_store.sessions_dir(cfg) / "weird" / "workspace.json"
            _write_workspace(wf, name="weird", extra_metadata={"state": "ARCHIVED"})

            data = sessions_store.list_sessions(cfg, include_archived=True)

            row = next(s for s in data["sessions"] if s["name"] == "weird")
            self.assertEqual(row["state"], sessions_store.STATE_ARCHIVED)


if __name__ == "__main__":
    unittest.main()
