from pathlib import Path
import json
import shutil

try:
    from helpers import files
except ImportError:
    raise ImportError(
        "Pen & Paper plugin requires the Agent Zero framework 'helpers' module. "
        "This hook can only run within the Agent Zero runtime environment. "
        "If you need to run setup manually, use execute.py instead."
    )

PLUGIN_NAME = "a0_pen_paper"
RUNTIME_BASE = "usr/pen_and_paper"


def _copy_missing(src: Path, dst: Path) -> None:
    if dst.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def install(**kwargs):
    plugin_dir = Path(__file__).resolve().parent
    runtime_dir = Path(files.get_abs_path(RUNTIME_BASE))
    wf_dir = runtime_dir / "knowledge" / "workflows"

    for rel in [
        "sessions/active",
        "sessions/archive",
        "config",
        "templates",
        "knowledge/workflows",
        "vectors",
        "_archived/templates",
    ]:
        (runtime_dir / rel).mkdir(parents=True, exist_ok=True)

    _copy_missing(plugin_dir / "data" / "config" / "onboarding.yaml", runtime_dir / "config" / "onboarding.yaml")
    shutil.copy2(plugin_dir / "data" / "config" / "rules.yaml", runtime_dir / "config" / "rules.yaml")
    _copy_missing(plugin_dir / "data" / "templates" / "session.md", wf_dir / "session.md")

    seed_wf = plugin_dir / "data" / "workflows"
    if seed_wf.is_dir():
        for md in seed_wf.glob("*.md"):
            _copy_missing(md, wf_dir / md.name)

    registry_path = wf_dir / "template_registry.json"
    seed_registry = plugin_dir / "data" / "workflows" / "template_registry.seed.json"
    if seed_registry.exists() and not registry_path.exists():
        shutil.copy2(seed_registry, registry_path)
    elif not registry_path.exists():
        registry_path.write_text(
            seed_registry.read_text(encoding="utf-8") if seed_registry.exists() else "{}",
            encoding="utf-8",
        )

    print(f"{PLUGIN_NAME}: runtime initialized at {runtime_dir}")
    return 0
