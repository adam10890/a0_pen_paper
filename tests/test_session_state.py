from __future__ import annotations

import json
import os
import sys
import unittest
import importlib.util
import types
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from usr.plugins.a0_pen_paper.helpers import sessions_store


class SessionStateTests(unittest.TestCase):
    def test_ensure_state_files_creates_session_root_and_live_workflow_copies(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            cfg = {"runtime_dir": str(root / "pen_and_paper")}
            sessions_store.ensure_session("demo", "chat-1", cfg=cfg)

            result = sessions_store.ensure_state_files("demo", "chat-1", cfg=cfg)

            self.assertTrue(result["ok"])
            state_dir = root / "pen_and_paper" / "sessions" / "active" / "demo" / "state"
            self.assertTrue((state_dir / "session_state.yaml").exists())
            self.assertTrue((state_dir / "events.jsonl").exists())
            self.assertTrue((state_dir / "workflows" / "debugging.yaml").exists())
            self.assertIn(
                "session:",
                (state_dir / "session_state.yaml").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "activation_tags:",
                (state_dir / "workflows" / "debugging.yaml").read_text(encoding="utf-8"),
            )

    def test_append_event_and_merge_state_preserve_unrelated_keys(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            cfg = {"runtime_dir": str(root / "pen_and_paper")}
            sessions_store.ensure_session("demo", "chat-1", cfg=cfg)
            sessions_store.ensure_state_files("demo", "chat-1", cfg=cfg)

            event = sessions_store.append_event(
                "demo",
                {
                    "type": "tool_result",
                    "tags": ["verification", "test_result"],
                    "summary": "py_compile passed",
                },
                cfg=cfg,
            )
            sessions_store.merge_session_state(
                "demo",
                {
                    "working_set": {"current_focus": "verify state helpers"},
                    "tags": {"modes": ["implementation"]},
                },
                cfg=cfg,
            )

            state = sessions_store.read_session_state("demo", cfg=cfg)
            self.assertEqual(event["id"], 1)
            self.assertEqual(state["session"]["last_event_id"], 1)
            self.assertEqual(state["working_set"]["current_focus"], "verify state helpers")
            self.assertEqual(state["tags"]["modes"], ["implementation"])
            self.assertIn("goal", state["session"])

            lines = (
                root
                / "pen_and_paper"
                / "sessions"
                / "active"
                / "demo"
                / "state"
                / "events.jsonl"
            ).read_text(encoding="utf-8").splitlines()
            self.assertEqual(json.loads(lines[0])["summary"], "py_compile passed")

    def test_workflow_templates_link_to_scribe_skills(self):
        templates = sessions_store.workflow_templates_dir()
        expected = {
            "planning": "scribe-workflow-planning",
            "implementation": "scribe-workflow-implementation",
            "debugging": "scribe-workflow-debugging",
            "verification": "scribe-workflow-verification",
            "research": "scribe-workflow-research",
        }

        for workflow_id, skill in expected.items():
            with self.subTest(workflow_id=workflow_id):
                data = yaml.safe_load(
                    (templates / f"{workflow_id}.yaml").read_text(encoding="utf-8")
                )
                self.assertEqual(data["scribe"]["skill"], skill)

    def test_pen_paper_focus_reads_current_tool_args_when_extension_args_are_missing(self):
        focus_path = (
            ROOT
            / "usr"
            / "plugins"
            / "a0_pen_paper"
            / "extensions"
            / "python"
            / "tool_execute_after"
            / "_51_pen_paper_focus.py"
        )
        spec = importlib.util.spec_from_file_location("pen_paper_focus", focus_path)
        module = importlib.util.module_from_spec(spec)
        helpers_mod = types.ModuleType("helpers")
        extension_mod = types.ModuleType("helpers.extension")
        extension_mod.Extension = type("Extension", (), {})
        sys.modules.setdefault("helpers", helpers_mod)
        sys.modules.setdefault("helpers.extension", extension_mod)
        assert spec.loader is not None
        spec.loader.exec_module(module)

        class FakeTool:
            args = {"action": "create", "name": "scribe_semantic_regression_003"}

        class FakeLoopData:
            current_tool = FakeTool()

        class FakeAgent:
            loop_data = FakeLoopData()

        args = module._effective_tool_args(None, FakeAgent())

        self.assertEqual(args["name"], "scribe_semantic_regression_003")


class StateDoxReadPathTests(unittest.TestCase):
    """PR1a: runtime State-DOX template discovery + merge (no publish path yet)."""

    _RUNTIME_REL = ("knowledge", "workflows", "state_dox")
    _CODE_REVIEW = (
        "workflow:\n"
        "  id: code_review\n"
        "  title: Code Review\n"
        "  activation_tags: [implementation, file_change]\n"
        "scribe:\n"
        "  skill: scribe-core\n"
        "  mode: workflow\n"
        "state:\n"
        "  phase: inactive\n"
        "  last_evidence_event: null\n"
    )

    def _state_dox(self, root: Path) -> Path:
        return root.joinpath("pen_and_paper", *self._RUNTIME_REL)

    @contextmanager
    def _cwd(self, path: Path):
        old = os.getcwd()
        os.chdir(path)
        try:
            yield
        finally:
            os.chdir(old)

    def test_relative_runtime_dir_resolves_from_agent_zero_root_not_cwd(self):
        with TemporaryDirectory() as td:
            with self._cwd(Path(td)):
                base = sessions_store._abs_runtime({"runtime_dir": "usr/pen_and_paper"})

        self.assertEqual(base, ROOT / "usr" / "pen_and_paper")

    def test_workflow_template_dirs_shipped_first_runtime_when_present(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            cfg = {"runtime_dir": str(root / "pen_and_paper")}
            shipped = sessions_store.workflow_templates_dir()

            dirs = sessions_store.workflow_template_dirs(cfg=cfg)
            self.assertEqual(dirs[0], shipped)
            self.assertNotIn(self._state_dox(root), dirs)  # runtime absent

            self._state_dox(root).mkdir(parents=True)
            dirs2 = sessions_store.workflow_template_dirs(cfg=cfg)
            self.assertEqual(dirs2[0], shipped)
            self.assertIn(self._state_dox(root), dirs2)

    def test_list_state_dox_templates_returns_builtins_with_shape(self):
        with TemporaryDirectory() as td:
            cfg = {"runtime_dir": str(Path(td) / "pen_and_paper")}
            rows = sessions_store.list_state_dox_templates(cfg=cfg)
            by_id = {r["id"]: r for r in rows}
            self.assertEqual(
                set(by_id),
                {"planning", "implementation", "debugging", "verification", "research"},
            )
            deb = by_id["debugging"]
            self.assertEqual(deb["skill"], "scribe-workflow-debugging")
            self.assertEqual(deb["source"], "shipped")
            self.assertEqual(deb["file"], "debugging.yaml")
            self.assertIsInstance(deb["activation_tags"], list)
            self.assertIn("tool_error", deb["activation_tags"])

    def test_list_state_dox_templates_merges_runtime_and_shipped_wins(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            cfg = {"runtime_dir": str(root / "pen_and_paper")}
            rt = self._state_dox(root)
            rt.mkdir(parents=True)
            (rt / "code_review.yaml").write_text(self._CODE_REVIEW, encoding="utf-8")
            # Runtime tries to shadow a shipped id; shipped must win.
            (rt / "debugging.yaml").write_text(
                "workflow:\n  id: debugging\n  title: HIJACK\n"
                "  activation_tags: [research]\n"
                "scribe:\n  skill: evil\n  mode: workflow\n"
                "state:\n  phase: inactive\n",
                encoding="utf-8",
            )
            by_id = {r["id"]: r for r in sessions_store.list_state_dox_templates(cfg=cfg)}
            self.assertIn("code_review", by_id)
            self.assertEqual(by_id["code_review"]["source"], "runtime")
            self.assertEqual(by_id["code_review"]["skill"], "scribe-core")
            self.assertEqual(by_id["debugging"]["skill"], "scribe-workflow-debugging")
            self.assertEqual(by_id["debugging"]["source"], "shipped")

    def test_list_state_dox_templates_accepts_flat_runtime_yaml(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            cfg = {"runtime_dir": str(root / "pen_and_paper")}
            rt = self._state_dox(root)
            rt.mkdir(parents=True)
            (rt / "code_review_runtime.yaml").write_text(
                "name: code_review_runtime\n"
                "activation_tags:\n"
                "  - code_review_trigger\n"
                "skill: scribe-workflow-code-review-missing\n"
                "description: Regression test\n",
                encoding="utf-8",
            )

            rows = {r["id"]: r for r in sessions_store.list_state_dox_templates(cfg=cfg)}

            self.assertIn("code_review_runtime", rows)
            self.assertEqual(
                rows["code_review_runtime"]["activation_tags"], ["code_review_trigger"]
            )
            self.assertEqual(
                rows["code_review_runtime"]["skill"],
                "scribe-workflow-code-review-missing",
            )

    def test_list_state_dox_templates_skips_malformed_and_never_raises(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            cfg = {"runtime_dir": str(root / "pen_and_paper")}
            rt = self._state_dox(root)
            rt.mkdir(parents=True)
            (rt / "broken.yaml").write_text(": : not valid : :\n[unclosed", encoding="utf-8")
            rows = sessions_store.list_state_dox_templates(cfg=cfg)
            ids = {r["id"] for r in rows}
            self.assertNotIn("broken", ids)
            self.assertIn("debugging", ids)

    def test_ensure_state_files_copies_runtime_template_into_session(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            cfg = {"runtime_dir": str(root / "pen_and_paper")}
            rt = self._state_dox(root)
            rt.mkdir(parents=True)
            (rt / "code_review.yaml").write_text(self._CODE_REVIEW, encoding="utf-8")

            sessions_store.ensure_state_files("demo", "chat-1", cfg=cfg)

            wf = (
                root / "pen_and_paper" / "sessions" / "active" / "demo" / "state" / "workflows"
            )
            self.assertTrue((wf / "code_review.yaml").exists())  # runtime copied
            self.assertTrue((wf / "debugging.yaml").exists())  # shipped still copied

    def test_ensure_state_files_does_not_overwrite_existing_live_workflow(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            cfg = {"runtime_dir": str(root / "pen_and_paper")}
            sessions_store.ensure_state_files("demo", "chat-1", cfg=cfg)
            live = (
                root
                / "pen_and_paper"
                / "sessions"
                / "active"
                / "demo"
                / "state"
                / "workflows"
                / "debugging.yaml"
            )
            live.write_text("LIVE-EDITED", encoding="utf-8")

            sessions_store.ensure_state_files("demo", "chat-1", cfg=cfg)

            self.assertEqual(live.read_text(encoding="utf-8"), "LIVE-EDITED")


if __name__ == "__main__":
    unittest.main()
