from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field
from typing import List

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


class PluginMetadata(BaseModel):
    name: str = ""
    title: str = ""
    description: str = ""
    version: str = ""
    settings_sections: List[str] = Field(default_factory=list)
    per_project_config: bool = False
    per_agent_config: bool = False
    always_enabled: bool = False


def test_plugin_yaml_exists_and_matches_agent_zero_schema():
    manifest_path = PLUGIN_ROOT / "plugin.yaml"
    assert manifest_path.is_file()

    raw = manifest_path.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf"), "plugin.yaml must not include a UTF-8 BOM"

    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    model = PluginMetadata.model_validate(manifest)

    assert model.name == "a0_pen_paper"
    assert model.title
    assert model.description
    assert model.version == "1.4.0"
    assert model.settings_sections == ["agent"]
    assert model.per_project_config is True
    assert model.per_agent_config is True
    assert model.always_enabled is False


def test_license_exists_at_plugin_root():
    assert (PLUGIN_ROOT / "LICENSE").is_file()
