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


def install():
    plugin_dir = Path(__file__).resolve().parent
    runtime_dir = Path(files.get_abs_path(RUNTIME_BASE))

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
    _copy_missing(plugin_dir / "data" / "config" / "rules.yaml", runtime_dir / "config" / "rules.yaml")
    _copy_missing(plugin_dir / "data" / "templates" / "session.md", runtime_dir / "knowledge" / "workflows" / "session.md")

    registry_path = runtime_dir / "knowledge" / "workflows" / "template_registry.json"
    if not registry_path.exists():
        registry = {
            "templates": {
                "session": {
                    "file": "session.md",
                    "description": "General structured working session",
                    "description_he": "סשן עבודה מובנה כללי",
                    "phases": ["Plan", "Work", "Review"],
                    "triggers": ["session", "notes", "planning", "task", "סשן", "תכנון"],
                }
            },
            "base_workflows": {
                "list": ["research", "debugging", "validation"],
                "hooks": {
                    "on_unknown": "research",
                    "on_stuck": "debugging",
                    "on_error": "debugging",
                    "on_complete": "validation",
                },
            },
        }
        registry_path.write_text(json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"{PLUGIN_NAME}: runtime initialized at {runtime_dir}")
    return 0
