"""
_wiki_helpers — minimal YAML frontmatter parser for LLM Wiki integration.

Vendored implementation to avoid cross-plugin imports. Parses only the subset needed:
- YAML frontmatter (--- ... ---)
- Simple key-value mappings
- Lists of strings

No external dependencies. Safe fallback on malformed input.
"""
import os
import re
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List


def parse_frontmatter(content: str) -> tuple[Dict[str, Any], str]:
    """
    Extract YAML frontmatter from markdown content.
    
    Returns (frontmatter_dict, body_without_frontmatter).
    If no frontmatter found, returns ({}, content).
    """
    if not content.startswith("---"):
        return {}, content
    
    parts = content.split("---", 2)
    if len(parts) < 3:
        # Malformed --- delimiter, treat as no frontmatter
        return {}, content
    
    frontmatter_text = parts[1].strip()
    body = parts[2].strip()
    
    if not frontmatter_text:
        return {}, body
    
    try:
        parsed = _parse_yaml_minimal(frontmatter_text)
        return parsed, body
    except Exception:
        # Frontmatter parse failed, treat as no frontmatter
        return {}, body


def _parse_yaml_minimal(text: str) -> Dict[str, Any]:
    """
    Minimal YAML parser for frontmatter subset.
    
    Handles:
    - Simple key: value mappings
    - Quoted strings
    - Lists of strings
    - Lists of dicts (nested mappings with same indentation)
    - Booleans and null
    
    Does NOT handle:
    - Deeply nested mappings
    - Multi-line strings
    - Anchors, aliases
    - Complex types
    """
    lines = text.splitlines()
    result: Dict[str, Any] = {}
    i = 0
    
    while i < len(lines):
        line = lines[i].rstrip()
        i += 1
        
        # Skip empty lines and comments
        if not line or line.strip().startswith("#"):
            continue
        
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        
        # List item (starts with "- ")
        if stripped.startswith("- "):
            key = _get_last_key(result)
            item_value = stripped[2:].strip()
            
            # Check if this is a nested mapping (next lines indented more)
            if i < len(lines):
                next_line = lines[i]
                next_stripped = next_line.strip()
                next_indent = len(next_line) - len(next_line.lstrip())
                if next_indent > indent and ":" in next_stripped and not next_stripped.startswith("- "):
                    # This is a list of dicts — consume indented lines
                    nested: Dict[str, Any] = {}
                    if ":" in item_value:
                        nk, _, nv = item_value.partition(":")
                        nested[nk.strip()] = _parse_scalar(nv.strip())
                    while i < len(lines):
                        nl = lines[i]
                        nl_stripped = nl.strip()
                        nl_indent = len(nl) - len(nl.lstrip())
                        if nl_indent <= indent or not nl_stripped:
                            break
                        if ":" in nl_stripped and not nl_stripped.startswith("- "):
                            nk, _, nv = nl_stripped.partition(":")
                            nested[nk.strip()] = _parse_scalar(nv.strip())
                        i += 1
                    if key and isinstance(result.get(key), list):
                        result[key].append(nested)
                    elif key:
                        result[key] = [nested]
                    continue
            
            # Simple list item
            if key and isinstance(result.get(key), list):
                result[key].append(_parse_scalar(item_value))
            elif key:
                result[key] = [_parse_scalar(item_value)]
            continue
        
        # Key-value mapping
        if ":" in stripped:
            key, sep, value = stripped.partition(":")
            key = key.strip()
            value = value.strip()
            
            if not value:
                result[key] = None
            else:
                result[key] = _parse_scalar(value)
    
    return result


def _parse_scalar(value: str) -> Any:
    """Parse a YAML scalar value."""
    value = value.strip()
    
    # Quoted string
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    
    # Boolean
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    
    # Null
    if value.lower() in ("null", "~", ""):
        return None
    
    # Integer
    try:
        return int(value)
    except ValueError:
        pass
    
    # Float
    try:
        return float(value)
    except ValueError:
        pass
    
    # Flow list [a, b, c]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        items = [item.strip() for item in inner.split(",")]
        return [_parse_scalar(item) for item in items if item]
    
    # Default: string
    return value


def _get_last_key(d: Dict[str, Any]) -> Optional[str]:
    """Get the last key in a dict (for list continuation)."""
    if not isinstance(d, dict):
        return None
    keys = list(d.keys())
    return keys[-1] if keys else None


def find_llm_wiki_vault() -> Optional[Path]:
    """
    Locate the LLM Wiki SharedBrain vault.
    
    Strategy:
    1. Read llm_wiki plugin config.json (if exists)
    2. Check for shared_vault.path in that config
    3. Fallback to autodetect: look for registry.yaml in project or sibling directories
    
    Returns Path to vault root, or None if not found.
    """
    # Try to read llm_wiki plugin config — resolve relative to cwd or script location
    _script_dir = Path(__file__).resolve().parent.parent.parent.parent if "__file__" in dir() else Path.cwd()
    config_paths = [
        _script_dir / "usr/plugins/llm_wiki/config.json",
        _script_dir / "usr/plugins/llm_wiki/default_config.yaml",
        Path("/a0/usr/plugins/llm_wiki/config.json"),
        Path("/a0/usr/plugins/llm_wiki/default_config.yaml"),
    ]
    
    for config_path in config_paths:
        if config_path.exists():
            try:
                if config_path.suffix == ".json":
                    with open(config_path, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                else:
                    # YAML fallback - minimal parsing
                    cfg = _parse_yaml_minimal(config_path.read_text(encoding="utf-8"))
                
                shared_vault = cfg.get("shared_vault", {})
                if isinstance(shared_vault, dict):
                    vault_path = shared_vault.get("path", "")
                    if vault_path:
                        vault = Path(vault_path).expanduser()
                        if vault.exists() and (vault / "registry.yaml").exists():
                            return vault
            except Exception:
                continue
    
    # Autodetect: look for registry.yaml
    candidates = [
        Path("."),
        Path(".."),
        Path("../SharedBrain"),
        Path("/data/SharedBrain"),
        Path("/a0/SharedBrain"),
    ]
    
    for base in candidates:
        registry = base / "registry.yaml"
        if registry.exists():
            return base.resolve()
    
    return None


def _normalize_registry(registry: Any) -> Dict[str, Any]:
    """Normalize registry structure so callers can safely use dict/list access."""
    if not isinstance(registry, dict):
        registry = {}
    wikis = registry.get("wikis")
    if not isinstance(wikis, list):
        wikis = []
    grants = registry.get("grants")
    if not isinstance(grants, dict):
        grants = {}
    registry["wikis"] = [w for w in wikis if isinstance(w, dict)]
    registry["grants"] = grants
    return registry


def _parse_registry_manual(content: str) -> Dict[str, Any]:
    """Small SharedBrain registry parser for fields this tool needs."""
    registry: Dict[str, Any] = {"wikis": [], "grants": {}}
    current = None
    current_wiki = None
    current_agent = None
    for raw in content.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        if indent == 0 and stripped.endswith(":"):
            current = stripped[:-1]
            current_wiki = None
            current_agent = None
            continue
        if current == "wikis":
            if stripped.startswith("- "):
                current_wiki = {}
                registry["wikis"].append(current_wiki)
                rest = stripped[2:].strip()
                if ":" in rest:
                    k, _, v = rest.partition(":")
                    current_wiki[k.strip()] = _parse_scalar(v.strip())
            elif current_wiki is not None and ":" in stripped:
                k, _, v = stripped.partition(":")
                current_wiki[k.strip()] = _parse_scalar(v.strip())
        elif current == "grants":
            if indent == 2 and stripped.endswith(":"):
                current_agent = stripped[:-1]
                registry["grants"][current_agent] = {}
            elif current_agent and ":" in stripped:
                k, _, v = stripped.partition(":")
                registry["grants"][current_agent][k.strip()] = _parse_scalar(v.strip())
    return registry


def parse_registry(vault_root: Path) -> Dict[str, Any]:
    """Parse registry.yaml and always return normalized {'wikis': list, 'grants': dict}."""
    registry_path = vault_root / "registry.yaml"
    if not registry_path.exists():
        return _normalize_registry({})
    try:
        content = registry_path.read_text(encoding="utf-8")
    except Exception:
        return _normalize_registry({})
    try:
        import yaml  # type: ignore
        return _normalize_registry(yaml.safe_load(content) or {})
    except Exception:
        pass
    try:
        parsed = _parse_registry_manual(content)
        if parsed.get("wikis"):
            return _normalize_registry(parsed)
    except Exception:
        pass
    try:
        return _normalize_registry(_parse_yaml_minimal(content))
    except Exception:
        return _normalize_registry({})

def scan_wiki_for_templates(wiki_path: Path) -> List[Dict[str, Any]]:
    """
    Scan a wiki directory for pages tagged as pen_paper_template.
    
    Returns list of template dicts with metadata.
    """
    templates = []
    wiki_dir = wiki_path / "wiki"
    
    if not wiki_dir.exists():
        return templates
    
    # Scan for .md files, excluding index.md and log.md
    exclude = {"index.md", "log.md"}
    
    for md_file in wiki_dir.rglob("*.md"):
        if md_file.name in exclude:
            continue
        
        try:
            content = md_file.read_text(encoding="utf-8")
            frontmatter, body = parse_frontmatter(content)
            
            # Check for pen_paper_template tag
            if frontmatter.get("type") == "pen_paper_template":
                template_name = frontmatter.get("template_name", md_file.stem)
                rel_path = md_file.relative_to(wiki_dir)
                
                templates.append({
                    "template_name": template_name,
                    "wiki_path": wiki_path,
                    "page_path": rel_path,
                    "absolute_path": md_file,
                    "title": frontmatter.get("title", template_name),
                    "description": frontmatter.get("description", ""),
                    "phases": frontmatter.get("phases", []),
                    "triggers": frontmatter.get("triggers", []),
                    "context_budget": frontmatter.get("context_budget", "medium"),
                    "mtime": md_file.stat().st_mtime,
                })
        except Exception:
            # Skip files that can't be read or parsed
            continue
    
    return templates


def get_cache_path(runtime_dir: Path) -> Path:
    """Get the cache file path for wiki template index."""
    cache_dir = runtime_dir / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / "wiki_template_index.json"


def is_cache_stale(cache_path: Path, templates: List[Dict[str, Any]], ttl_seconds: int = 300) -> bool:
    """
    Check if cache is stale based on TTL or file mtimes.
    
    Returns True if cache should be invalidated.
    """
    if not cache_path.exists():
        return True
    
    try:
        cache_mtime = cache_path.stat().st_mtime
        now = time.time()
        
        # TTL check
        if now - cache_mtime > ttl_seconds:
            return True
        
        # Check if any template file is newer than cache
        for tmpl in templates:
            tmpl_mtime = tmpl.get("mtime", 0)
            if tmpl_mtime > cache_mtime:
                return True
    except Exception:
        return True
    
    return False


def load_cache(cache_path: Path) -> Optional[Dict[str, Any]]:
    """Load cached template index."""
    if not cache_path.exists():
        return None
    
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_cache(cache_path: Path, data: Dict[str, Any]) -> None:
    """Save template index to cache."""
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass
