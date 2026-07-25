"""
Tests for the additive `relations` array on session workspaces (inspired by
usememos/memos' MemoRelation / SetMemoRelations / ListMemoRelations).

Covers back-compat (workspaces with no `relations` key read as [] and are not
rewritten), set_relations() replace semantics, add_relation() idempotency,
validation (invalid type, empty target, non-dict entry, self-relation), and
that a relation pointing at a nonexistent session is accepted (no
dangling-link check by design).
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
    path: Path, *, name: str, extra: dict | None = None
) -> None:
    metadata = {
        "name": name,
        "status": "active",
        "chat_id": "chat-1",
        "created_at": "2026-01-01T00:00:00+00:00",
    }
    workspace: dict = {"metadata": metadata}
    for sec in sessions_store.VALID_SECTIONS:
        workspace[sec] = []
    if extra:
        workspace.update(extra)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(workspace, indent=2), encoding="utf-8")


class RelationsBackCompatTests(unittest.TestCase):
    def test_workspace_without_relations_key_reads_as_empty_list(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(wf, name="demo")

            relations = sessions_store.list_relations("demo", cfg=cfg)

            self.assertEqual(relations, [])

    def test_reading_relations_does_not_rewrite_the_file(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(wf, name="demo")
            before = wf.read_text(encoding="utf-8")
            before_mtime = wf.stat().st_mtime_ns

            sessions_store.list_relations("demo", cfg=cfg)

            after = wf.read_text(encoding="utf-8")
            self.assertEqual(before, after)
            self.assertEqual(before_mtime, wf.stat().st_mtime_ns)
            self.assertNotIn("relations", json.loads(after))

    def test_list_relations_missing_workspace_raises(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            with self.assertRaises(FileNotFoundError):
                sessions_store.list_relations("nope", cfg=cfg)

    def test_list_relations_works_for_archived_session(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            wf = sessions_store.archive_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(
                wf,
                name="demo",
                extra={"relations": [{"type": "REFERENCE", "target": "other"}]},
            )

            relations = sessions_store.list_relations("demo", cfg=cfg)

            self.assertEqual(relations, [{"type": "REFERENCE", "target": "other"}])


class RelationsReadPathValidationTests(unittest.TestCase):
    """The write path validates; a hand-edited or corrupted file can still
    carry malformed entries, so the read path must apply the same rules."""

    MALFORMED = [
        "garbage",                                 # not a dict
        {"type": "BOGUS", "target": "x"},          # invalid type
        None,                                      # not a dict
        {"type": "REFERENCE"},                     # missing target
        {"type": "REFERENCE", "target": ""},       # empty target
        {"type": "COMMENT", "target": "demo"},     # self-relation
        {"type": "REFERENCE", "target": "real"},   # the only valid entry
    ]

    def _cfg_with_malformed(self, td):
        cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
        wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
        _write_workspace(wf, name="demo", extra={"relations": list(self.MALFORMED)})
        return cfg, wf

    def test_list_relations_skips_malformed_entries(self):
        with TemporaryDirectory() as td:
            cfg, _ = self._cfg_with_malformed(td)
            self.assertEqual(
                sessions_store.list_relations("demo", cfg=cfg),
                [{"type": "REFERENCE", "target": "real"}],
            )

    def test_relation_count_excludes_malformed_entries(self):
        with TemporaryDirectory() as td:
            cfg, _ = self._cfg_with_malformed(td)
            session = sessions_store.list_sessions(cfg)["sessions"][0]
            self.assertEqual(session["relation_count"], 1)
            self.assertEqual(session["relations"], [{"type": "REFERENCE", "target": "real"}])

    def test_relation_target_filter_ignores_invalid_relation_type(self):
        with TemporaryDirectory() as td:
            cfg, _ = self._cfg_with_malformed(td)
            # target "x" only appears on an entry whose type is invalid
            hit = sessions_store.list_sessions(cfg, filter={"relation_target": "x"})
            self.assertEqual(hit["sessions"], [])
            valid = sessions_store.list_sessions(cfg, filter={"relation_target": "real"})
            self.assertEqual(len(valid["sessions"]), 1)

    def test_read_path_does_not_rewrite_malformed_file(self):
        with TemporaryDirectory() as td:
            cfg, wf = self._cfg_with_malformed(td)
            before = wf.read_text(encoding="utf-8")

            sessions_store.list_relations("demo", cfg=cfg)
            sessions_store.list_sessions(cfg)

            self.assertEqual(before, wf.read_text(encoding="utf-8"))
            self.assertEqual(len(json.loads(before)["relations"]), len(self.MALFORMED))

    def test_all_malformed_reads_as_empty_and_has_relations_is_false(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(wf, name="demo", extra={"relations": ["garbage", None]})

            self.assertEqual(sessions_store.list_relations("demo", cfg=cfg), [])
            hit = sessions_store.list_sessions(cfg, filter={"has_relations": True})
            self.assertEqual(hit["sessions"], [])


class SetRelationsTests(unittest.TestCase):
    def test_set_relations_round_trips(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(wf, name="demo")

            result = sessions_store.set_relations(
                "demo",
                [
                    {"type": "REFERENCE", "target": "project-x"},
                    {"type": "COMMENT", "target": "solution-y"},
                ],
                cfg=cfg,
            )

            self.assertTrue(result["ok"])
            self.assertEqual(
                sessions_store.list_relations("demo", cfg=cfg),
                [
                    {"type": "REFERENCE", "target": "project-x"},
                    {"type": "COMMENT", "target": "solution-y"},
                ],
            )

    def test_set_relations_replaces_rather_than_appends(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(
                wf,
                name="demo",
                extra={"relations": [{"type": "REFERENCE", "target": "old-target"}]},
            )

            sessions_store.set_relations(
                "demo", [{"type": "COMMENT", "target": "new-target"}], cfg=cfg
            )

            relations = sessions_store.list_relations("demo", cfg=cfg)
            self.assertEqual(relations, [{"type": "COMMENT", "target": "new-target"}])

    def test_set_relations_rejects_unknown_type(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(wf, name="demo")

            with self.assertRaises(ValueError):
                sessions_store.set_relations(
                    "demo", [{"type": "BOGUS", "target": "other"}], cfg=cfg
                )
            # Rejected write must not partially apply.
            self.assertEqual(sessions_store.list_relations("demo", cfg=cfg), [])

    def test_set_relations_rejects_empty_target(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(wf, name="demo")

            with self.assertRaises(ValueError):
                sessions_store.set_relations(
                    "demo", [{"type": "REFERENCE", "target": ""}], cfg=cfg
                )

    def test_set_relations_rejects_non_string_target(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(wf, name="demo")

            with self.assertRaises(ValueError):
                sessions_store.set_relations(
                    "demo", [{"type": "REFERENCE", "target": 123}], cfg=cfg
                )

    def test_set_relations_rejects_non_dict_entry(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(wf, name="demo")

            with self.assertRaises(ValueError):
                sessions_store.set_relations("demo", ["not-a-dict"], cfg=cfg)

    def test_set_relations_rejects_self_relation(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(wf, name="demo")

            with self.assertRaises(ValueError):
                sessions_store.set_relations(
                    "demo", [{"type": "REFERENCE", "target": "demo"}], cfg=cfg
                )

    def test_set_relations_accepts_target_that_does_not_exist_yet(self):
        """No dangling-link enforcement: a relation may point at a session that
        does not (yet, or anymore) exist on disk. Ordering/creation must stay
        unconstrained by relation targets."""
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(wf, name="demo")

            result = sessions_store.set_relations(
                "demo",
                [{"type": "REFERENCE", "target": "never-created-session"}],
                cfg=cfg,
            )

            self.assertTrue(result["ok"])
            self.assertEqual(
                sessions_store.list_relations("demo", cfg=cfg),
                [{"type": "REFERENCE", "target": "never-created-session"}],
            )


class AddRelationTests(unittest.TestCase):
    def test_add_relation_appends(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(wf, name="demo")

            sessions_store.add_relation("demo", "other-session", "REFERENCE", cfg=cfg)

            self.assertEqual(
                sessions_store.list_relations("demo", cfg=cfg),
                [{"type": "REFERENCE", "target": "other-session"}],
            )

    def test_add_relation_is_idempotent_for_duplicate_type_and_target(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(wf, name="demo")

            sessions_store.add_relation("demo", "other-session", "REFERENCE", cfg=cfg)
            sessions_store.add_relation("demo", "other-session", "REFERENCE", cfg=cfg)

            self.assertEqual(
                sessions_store.list_relations("demo", cfg=cfg),
                [{"type": "REFERENCE", "target": "other-session"}],
            )

    def test_add_relation_same_target_different_type_is_not_a_duplicate(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(wf, name="demo")

            sessions_store.add_relation("demo", "other-session", "REFERENCE", cfg=cfg)
            sessions_store.add_relation("demo", "other-session", "COMMENT", cfg=cfg)

            relations = sessions_store.list_relations("demo", cfg=cfg)
            self.assertEqual(len(relations), 2)
            types_present = {r["type"] for r in relations}
            self.assertEqual(types_present, {"REFERENCE", "COMMENT"})

    def test_add_relation_rejects_self_relation(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(wf, name="demo")

            with self.assertRaises(ValueError):
                sessions_store.add_relation("demo", "demo", "REFERENCE", cfg=cfg)

    def test_add_relation_rejects_unknown_type(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(wf, name="demo")

            with self.assertRaises(ValueError):
                sessions_store.add_relation("demo", "other", "BOGUS", cfg=cfg)

    def test_add_relation_missing_workspace_raises(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            with self.assertRaises(FileNotFoundError):
                sessions_store.add_relation("nope", "other", "REFERENCE", cfg=cfg)


class ListSessionsRelationsTests(unittest.TestCase):
    def test_session_without_relations_key_shows_empty_list_and_zero_count(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(wf, name="demo")

            data = sessions_store.list_sessions(cfg)

            row = next(s for s in data["sessions"] if s["name"] == "demo")
            self.assertEqual(row["relations"], [])
            self.assertEqual(row["relation_count"], 0)

    def test_session_with_relations_exposes_them_and_the_count(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(
                wf,
                name="demo",
                extra={
                    "relations": [
                        {"type": "REFERENCE", "target": "a"},
                        {"type": "COMMENT", "target": "b"},
                    ]
                },
            )

            data = sessions_store.list_sessions(cfg)

            row = next(s for s in data["sessions"] if s["name"] == "demo")
            self.assertEqual(row["relation_count"], 2)
            self.assertEqual(
                row["relations"],
                [
                    {"type": "REFERENCE", "target": "a"},
                    {"type": "COMMENT", "target": "b"},
                ],
            )

    def test_existing_keys_still_present_alongside_relations(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            wf = sessions_store.sessions_dir(cfg) / "demo" / "workspace.json"
            _write_workspace(wf, name="demo")

            data = sessions_store.list_sessions(cfg)

            row = next(s for s in data["sessions"] if s["name"] == "demo")
            for key in ("name", "status", "state", "properties", "section_counts"):
                self.assertIn(key, row)


if __name__ == "__main__":
    unittest.main()
