from __future__ import annotations

import json
import sys
import unittest
import importlib.util
import types
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


if __name__ == "__main__":
    unittest.main()
