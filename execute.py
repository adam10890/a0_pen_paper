#!/usr/bin/env python3
"""
Pen & Paper Plugin - Manual Setup & Maintenance Script

This script can be run from the Plugins UI for manual maintenance tasks:
- Re-run installation (create directories and seed files)
- Reset runtime directory (delete and recreate)
- Show runtime status
- Validate plugin configuration
"""

import sys
import json
import shutil
from pathlib import Path

PLUGIN_NAME = "a0_pen_paper"
RUNTIME_BASE = "usr/pen_and_paper"


def get_plugin_dir():
    """Get the plugin directory."""
    return Path(__file__).resolve().parent


def get_runtime_dir():
    """Get the runtime directory."""
    try:
        from helpers import files
        return Path(files.get_abs_path(RUNTIME_BASE))
    except ImportError:
        # Fallback for running outside Agent Zero framework
        return get_plugin_dir().parent.parent / "pen_and_paper"


def create_runtime_structure():
    """Create runtime directory structure."""
    runtime_dir = get_runtime_dir()
    
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
    
    return runtime_dir


def copy_seed_files(runtime_dir):
    """Copy seed files from plugin data directory."""
    plugin_dir = get_plugin_dir()
    
    seed_files = [
        ("data/config/onboarding.yaml", "config/onboarding.yaml"),
        ("data/config/rules.yaml", "config/rules.yaml"),
        ("data/templates/session.md", "knowledge/workflows/session.md"),
    ]
    
    for src_rel, dst_rel in seed_files:
        src = plugin_dir / src_rel
        dst = runtime_dir / dst_rel
        if not dst.exists():
            shutil.copy2(src, dst)
            print(f"Copied: {dst_rel}")


def init_template_registry(runtime_dir):
    """Initialize template registry if it doesn't exist."""
    plugin_dir = get_plugin_dir()
    registry_path = runtime_dir / "knowledge/workflows/template_registry.json"
    seed_registry = plugin_dir / "data/workflows/template_registry.seed.json"
    wf_seed = plugin_dir / "data/workflows"
    wf_dir = runtime_dir / "knowledge/workflows"

    if wf_seed.is_dir():
        for md in wf_seed.glob("*.md"):
            dst = wf_dir / md.name
            if not dst.exists():
                shutil.copy2(md, dst)
                print(f"Copied workflow: {md.name}")

    if not registry_path.exists():
        if seed_registry.exists():
            shutil.copy2(seed_registry, registry_path)
        else:
            registry_path.write_text("{}", encoding="utf-8")
        print("Created: template_registry.json")


def run_install():
    """Run installation (create directories and seed files)."""
    print(f"Running {PLUGIN_NAME} installation...")
    runtime_dir = create_runtime_structure()
    copy_seed_files(runtime_dir)
    init_template_registry(runtime_dir)
    print(f"Installation complete. Runtime: {runtime_dir}")
    return 0


def run_reset():
    """Reset runtime directory (delete and recreate)."""
    print(f"Resetting {PLUGIN_NAME} runtime directory...")
    runtime_dir = get_runtime_dir()
    
    if runtime_dir.exists():
        shutil.rmtree(runtime_dir)
        print(f"Deleted: {runtime_dir}")
    
    run_install()
    return 0


def run_status():
    """Show runtime status."""
    print(f"{PLUGIN_NAME} Runtime Status")
    print("=" * 50)
    
    runtime_dir = get_runtime_dir()
    print(f"Runtime directory: {runtime_dir}")
    print(f"Exists: {runtime_dir.exists()}")
    
    if runtime_dir.exists():
        checks = [
            "sessions/active",
            "sessions/archive",
            "config/onboarding.yaml",
            "config/rules.yaml",
            "knowledge/workflows/session.md",
            "knowledge/workflows/template_registry.json",
        ]
        
        print("\nFiles and directories:")
        for c in checks:
            p = runtime_dir / c
            status = "✓" if p.exists() else "✗"
            kind = "dir" if p.is_dir() else "file"
            print(f"  {status} {c} ({kind})")
    
    return 0


def run_validate():
    """Validate plugin configuration."""
    print(f"Validating {PLUGIN_NAME} plugin...")
    plugin_dir = get_plugin_dir()
    
    checks = [
        ("plugin.yaml", plugin_dir / "plugin.yaml"),
        ("hooks.py", plugin_dir / "hooks.py"),
        ("tools/pen_paper.py", plugin_dir / "tools/pen_paper.py"),
        ("data/config/onboarding.yaml", plugin_dir / "data/config/onboarding.yaml"),
    ]
    
    all_valid = True
    for name, path in checks:
        if path.exists():
            print(f"  ✓ {name}")
        else:
            print(f"  ✗ {name} MISSING")
            all_valid = False
    
    # Check plugin.yaml content
    plugin_yaml = plugin_dir / "plugin.yaml"
    if plugin_yaml.exists():
        import yaml
        with open(plugin_yaml, 'r') as f:
            config = yaml.safe_load(f)
            print(f"\nPlugin configuration:")
            print(f"  name: {config.get('name', 'N/A')}")
            print(f"  version: {config.get('version', 'N/A')}")
            print(f"  always_enabled: {config.get('always_enabled', 'N/A')}")
    
    try:
        from usr.plugins.a0_pen_paper.helpers.workflows_store import validate_registry_integrity
        from usr.plugins.a0_pen_paper.tools._config import load_plugin_config

        integrity = validate_registry_integrity(load_plugin_config())
        if integrity:
            print("\nRegistry integrity issues:")
            for err in integrity:
                print(f"  ✗ {err}")
            all_valid = False
        else:
            print("\n  ✓ template_registry integrity")
    except Exception as e:
        print(f"\n  ⚠ registry integrity check skipped: {e}")

    return 0 if all_valid else 1


def run_test_wiki_integration():
    """Run smoke tests for LLM Wiki integration."""
    print(f"Testing {PLUGIN_NAME} Wiki Integration...")
    print("=" * 50)
    
    plugin_dir = get_plugin_dir()
    
    # Test 1: Helper module exists and loads
    print("\n[Test 1] Helper module loads")
    try:
        from tools._wiki_helpers import (
            parse_frontmatter,
            find_llm_wiki_vault,
            parse_registry,
            scan_wiki_for_templates,
        )
        print("  ✓ Helper module imports successfully")
    except Exception as e:
        print(f"  ✗ Helper module import failed: {e}")
        return 1
    
    # Test 2: Frontmatter parser handles valid YAML
    print("\n[Test 2] Frontmatter parser handles valid YAML")
    test_content = """---
type: pen_paper_template
template_name: test
title: Test Template
---
Body content here"""
    try:
        fm, body = parse_frontmatter(test_content)
        if fm.get("type") == "pen_paper_template" and fm.get("template_name") == "test":
            print("  ✓ Frontmatter parsed correctly")
        else:
            print(f"  ✗ Frontmatter parsing incorrect: {fm}")
            return 1
    except Exception as e:
        print(f"  ✗ Frontmatter parsing failed: {e}")
        return 1
    
    # Test 3: Frontmatter parser handles missing frontmatter
    print("\n[Test 3] Frontmatter parser handles missing frontmatter")
    test_no_fm = "Just body content, no frontmatter"
    try:
        fm, body = parse_frontmatter(test_no_fm)
        if not fm and body == test_no_fm:
            print("  ✓ Missing frontmatter handled gracefully")
        else:
            print(f"  ✗ Unexpected result: fm={fm}, body={body[:50]}")
            return 1
    except Exception as e:
        print(f"  ✗ Missing frontmatter handling failed: {e}")
        return 1
    
    # Test 4: Frontmatter parser handles malformed YAML
    print("\n[Test 4] Frontmatter parser handles malformed YAML")
    test_malformed = """---
invalid: : broken
---
Body"""
    try:
        fm, body = parse_frontmatter(test_malformed)
        # Should return empty dict and full content on parse failure
        print("  ✓ Malformed frontmatter handled gracefully")
    except Exception as e:
        print(f"  ✗ Malformed frontmatter raised exception: {e}")
        return 1
    
    # Test 5: Vault detection when llm_wiki not installed
    print("\n[Test 5] Vault detection when llm_wiki not installed")
    try:
        vault = find_llm_wiki_vault()
        if vault is None:
            print("  ✓ Returns None when no vault found (expected)")
        else:
            print(f"  ℹ Vault found at {vault} (llm_wiki may be installed)")
    except Exception as e:
        print(f"  ✗ Vault detection failed: {e}")
        return 1
    
    # Test 6: Tool file exists and compiles
    print("\n[Test 6] Tool file exists and compiles")
    tool_path = plugin_dir / "tools" / "pen_paper_wiki_template.py"
    if tool_path.exists():
        try:
            import py_compile
            py_compile.compile(tool_path, doraise=True)
            print("  ✓ Tool file compiles successfully")
        except Exception as e:
            print(f"  ✗ Tool file compilation failed: {e}")
            return 1
    else:
        print("  ✗ Tool file missing")
        return 1
    
    # Test 7: Prompt file exists
    print("\n[Test 7] Prompt file exists")
    prompt_path = plugin_dir / "prompts" / "agent.system.tool.pen_paper_wiki_template.md"
    if prompt_path.exists():
        print("  ✓ Prompt file exists")
    else:
        print("  ✗ Prompt file missing")
        return 1
    
    print("\n" + "=" * 50)
    print("All wiki integration tests passed!")
    return 0


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: execute.py <command>")
        print("\nCommands:")
        print("  install           - Run installation (create directories and seed files)")
        print("  reset             - Reset runtime directory (delete and recreate)")
        print("  status            - Show runtime status")
        print("  validate          - Validate plugin configuration")
        print("  test_wiki_integration - Run wiki integration smoke tests")
        return 1
    
    command = sys.argv[1].lower()
    
    commands = {
        "install": run_install,
        "reset": run_reset,
        "status": run_status,
        "validate": run_validate,
        "test_wiki_integration": run_test_wiki_integration,
    }
    
    if command not in commands:
        print(f"Unknown command: {command}")
        print(f"Available commands: {', '.join(commands.keys())}")
        return 1
    
    return commands[command]()


if __name__ == "__main__":
    sys.exit(main())
