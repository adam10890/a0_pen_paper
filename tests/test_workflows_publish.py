from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from usr.plugins.a0_pen_paper.helpers import sessions_store, workflows_store


class PublishStateDoxTests(unittest.TestCase):
    """PR1b: workflows_store publishes Scribe-readable State-DOX templates."""

    def _cfg(self, root: Path) -> dict:
        return {"runtime_dir": str(root / "pen_and_paper")}

    def _registry(self, root: Path) -> dict:
        path = (
            root / "pen_and_paper" / "knowledge" / "workflows" / "template_registry.json"
        )
        return json.loads(path.read_text(encoding="utf-8"))

    def _yaml_path(self, root: Path, name: str) -> Path:
        return (
            root
            / "pen_and_paper"
            / "knowledge"
            / "workflows"
            / "state_dox"
            / f"{name}.yaml"
        )

    def test_publish_writes_yaml_and_updates_registry(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            cfg = self._cfg(root)
            workflows_store.create_template("code_review", "", description="CR", cfg=cfg)

            res = workflows_store.publish_state_dox(
                "code_review",
                activation_tags=["implementation", "file_change"],
                skill="scribe-core",
                cfg=cfg,
            )

            self.assertTrue(res["ok"], res)
            data = yaml.safe_load(self._yaml_path(root, "code_review").read_text("utf-8"))
            self.assertEqual(data["workflow"]["id"], "code_review")
            self.assertEqual(
                data["workflow"]["activation_tags"], ["implementation", "file_change"]
            )
            self.assertEqual(data["scribe"]["skill"], "scribe-core")
            self.assertEqual(data["state"]["phase"], "inactive")
            self.assertIn("last_evidence_event", data["state"])

            entry = self._registry(root)["templates"]["code_review"]
            self.assertTrue(entry["scribe_enabled"])
            self.assertEqual(entry["activation_tags"], ["implementation", "file_change"])
            self.assertEqual(entry["state_dox_file"], "state_dox/code_review.yaml")
            self.assertIn("published_at", entry)

    def test_published_template_is_visible_via_list_state_dox_templates(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            cfg = self._cfg(root)
            workflows_store.create_template("code_review", "", cfg=cfg)
            workflows_store.publish_state_dox(
                "code_review", activation_tags=["implementation"], cfg=cfg
            )

            rows = {r["id"]: r for r in sessions_store.list_state_dox_templates(cfg=cfg)}
            self.assertIn("code_review", rows)
            self.assertEqual(rows["code_review"]["source"], "runtime")
            self.assertIn("implementation", rows["code_review"]["activation_tags"])

    def test_publish_blocks_unknown_template(self):
        with TemporaryDirectory() as td:
            cfg = self._cfg(Path(td))
            res = workflows_store.publish_state_dox(
                "ghost", activation_tags=["implementation"], cfg=cfg
            )
            self.assertFalse(res["ok"])

    def test_publish_blocks_empty_activation_tags(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            cfg = self._cfg(root)
            workflows_store.create_template("code_review", "", cfg=cfg)
            res = workflows_store.publish_state_dox(
                "code_review", activation_tags=[], cfg=cfg
            )
            self.assertFalse(res["ok"])

    def test_publish_blocks_reserved_builtin_id(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            cfg = self._cfg(root)
            # 'debugging' is a shipped State-DOX id; a UI markdown template may share
            # the name, but publishing it as State-DOX must be blocked.
            workflows_store.create_template("debugging", "", cfg=cfg)
            res = workflows_store.publish_state_dox(
                "debugging", activation_tags=["tool_error"], cfg=cfg
            )
            self.assertFalse(res["ok"])
            self.assertIn("built-in", res["error"].lower())

    def test_publish_warns_on_unknown_tag(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            cfg = self._cfg(root)
            workflows_store.create_template("code_review", "", cfg=cfg)
            res = workflows_store.publish_state_dox(
                "code_review",
                activation_tags=["implementation", "made_up_tag"],
                cfg=cfg,
            )
            self.assertTrue(res["ok"], res)
            self.assertTrue(res.get("warnings"))
            self.assertNotIn("never fire", res["warnings"][0])

    def test_unpublish_removes_yaml_and_clears_registry_flags(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            cfg = self._cfg(root)
            workflows_store.create_template("code_review", "", cfg=cfg)
            workflows_store.publish_state_dox(
                "code_review", activation_tags=["implementation"], cfg=cfg
            )
            self.assertTrue(self._yaml_path(root, "code_review").exists())

            res = workflows_store.unpublish_state_dox("code_review", cfg=cfg)

            self.assertTrue(res["ok"])
            self.assertFalse(self._yaml_path(root, "code_review").exists())
            entry = self._registry(root)["templates"]["code_review"]
            self.assertFalse(entry.get("scribe_enabled"))

    def test_delete_template_unpublishes_state_dox(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            cfg = self._cfg(root)
            workflows_store.create_template("code_review", "", cfg=cfg)
            workflows_store.publish_state_dox(
                "code_review", activation_tags=["implementation"], cfg=cfg
            )
            self.assertTrue(self._yaml_path(root, "code_review").exists())

            workflows_store.delete_template("code_review", cfg=cfg)

            self.assertFalse(self._yaml_path(root, "code_review").exists())


if __name__ == "__main__":
    unittest.main()
