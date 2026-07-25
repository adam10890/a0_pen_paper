from __future__ import annotations

import os
import subprocess
import zipfile
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
DIST_ZIP = PLUGIN_ROOT / "dist" / "a0_pen_paper.zip"


def _build_zip() -> None:
    script = PLUGIN_ROOT / "scripts" / "package_plugin_zip.sh"
    subprocess.run(["bash", str(script)], check=True, cwd=PLUGIN_ROOT)


def test_packaged_zip_contains_plugin_yaml_in_named_folder():
    _build_zip()
    assert DIST_ZIP.is_file()

    with zipfile.ZipFile(DIST_ZIP, "r") as archive:
        names = archive.namelist()
        assert any(name.endswith("a0_pen_paper/plugin.yaml") for name in names)
        assert not any(name == "plugin.yaml" for name in names)

    extract_dir = PLUGIN_ROOT / "dist" / "zip_extract_test"
    if extract_dir.exists():
        for root, dirs, files in os.walk(extract_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        extract_dir.rmdir()

    extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(DIST_ZIP, "r") as archive:
        archive.extractall(extract_dir)

    plugin_root = extract_dir / "a0_pen_paper"
    assert (plugin_root / "plugin.yaml").is_file()
    assert (plugin_root / "README.md").is_file()
    assert (plugin_root / "LICENSE").is_file()
