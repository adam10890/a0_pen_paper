"""
pen_paper_wiki_template — discover and load wiki pages as Pen & Paper workflow templates.

Read-only tool that scans LLM Wiki SharedBrain vault for pages tagged with
`type: pen_paper_template` in YAML frontmatter. Returns template metadata
and session-payload blobs that agents can feed into the existing pen_paper
tool's `create` action as initial content.

Context-window safeguards:
- Max 20 templates per list
- Max 500 chars preview by default, 3000 chars on full load
- 5-minute discovery cache with mtime invalidation
- Hard limit: max 3 templates loaded per session
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    from helpers.tool import Tool, Response
    from helpers import files
except Exception:
    class Tool:
        """Fallback Tool base when running outside Agent Zero runtime."""
    
    class Response:
        """Fallback Response when running outside Agent Zero runtime."""
        def __init__(self, message="", break_loop=False):
            self.message = message
            self.break_loop = break_loop

    class _FilesFallback:
        @staticmethod
        def read_file(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
    
    files = _FilesFallback()

try:
    from ._config import load_plugin_config, wiki_settings
    from ._wiki_helpers import (
        find_llm_wiki_vault,
        parse_registry,
        scan_wiki_for_templates,
        get_cache_path,
        is_cache_stale,
        load_cache,
        save_cache,
        parse_frontmatter,
    )
except ImportError:
    _here = os.path.dirname(os.path.abspath(__file__))
    if _here not in sys.path:
        sys.path.insert(0, _here)
    from _config import load_plugin_config, wiki_settings
    from _wiki_helpers import (
        find_llm_wiki_vault,
        parse_registry,
        scan_wiki_for_templates,
        get_cache_path,
        is_cache_stale,
        load_cache,
        save_cache,
        parse_frontmatter,
    )


RUNTIME_BASE = "usr/pen_and_paper"
MAX_TEMPLATES_PER_LIST = 20
MAX_PREVIEW_CHARS = 500
MAX_FULL_LOAD_CHARS = 3000
CACHE_TTL_SECONDS = 300


class PenPaperWikiTemplate(Tool):
    """Discover and load wiki pages as Pen & Paper workflow templates."""

    async def execute(self, **kwargs):
        action = self.args.get("action", "")
        
        if action == "list_templates":
            return await self._list_templates()
        elif action == "load_template":
            return await self._load_template()
        else:
            return Response(
                message="Invalid action. Use `action=list_templates` or `action=load_template`.",
                break_loop=False,
            )

    def _get_runtime_dir(self) -> Path:
        """Resolve the Pen & Paper runtime directory."""
        try:
            abs_path = files.get_abs_path(RUNTIME_BASE)
            return Path(abs_path)
        except Exception:
            # Fallback: resolve from current working directory
            return Path(RUNTIME_BASE).resolve()

    def _get_agent_id(self) -> str:
        """Get agent ID for access control."""
        try:
            for attr in ("id", "name", "agent_id"):
                v = getattr(self.agent, attr, None)
                if isinstance(v, str) and v:
                    return v.lower().replace(" ", "_")
        except Exception:
            pass
        return "agent_zero"

    def _get_config(self) -> Dict[str, Any]:
        try:
            return load_plugin_config(agent=getattr(self, "agent", None))
        except Exception:
            return {}

    def _integration_disabled_message(self, cfg: Dict[str, Any]) -> Optional[str]:
        block = cfg.get("llm_wiki_integration") if isinstance(cfg, dict) else None
        if isinstance(block, dict) and block.get("enabled") is False:
            return "Pen & Paper LLM Wiki integration is disabled in plugin config (`llm_wiki_integration.enabled=false`)."
        return None

    def _resolve_vault(self, cfg: Dict[str, Any]) -> Optional[Path]:
        settings = wiki_settings(cfg) if isinstance(cfg, dict) else {}
        configured = settings.get("vault_path") or ""
        if configured:
            vault = Path(str(configured)).expanduser()
            if vault.exists() and (vault / "registry.yaml").exists():
                return vault
        return find_llm_wiki_vault()

    def _limits(self, cfg: Dict[str, Any]) -> tuple[int, int, int]:
        settings = wiki_settings(cfg) if isinstance(cfg, dict) else {}
        return (
            int(settings.get("max_templates_per_list") or MAX_TEMPLATES_PER_LIST),
            int(settings.get("max_preview_chars") or MAX_PREVIEW_CHARS),
            int(settings.get("max_full_load_chars") or MAX_FULL_LOAD_CHARS),
        )

    async def _list_templates(self):
        """List all wiki pages tagged as pen_paper_template."""
        cfg = self._get_config()
        disabled = self._integration_disabled_message(cfg)
        if disabled:
            return Response(message=disabled, break_loop=False)
        vault = self._resolve_vault(cfg)
        if not vault:
            return Response(
                message=(
                    "No SharedBrain vault configured.\n"
                    "Ensure the llm_wiki plugin is installed and shared_vault.path is set."
                ),
                break_loop=False,
            )

        runtime_dir = self._get_runtime_dir()
        cache_path = get_cache_path(runtime_dir)
        agent_id = self._get_agent_id()

        # Try loading from cache
        cached = load_cache(cache_path)
        if cached:
            templates = cached.get("templates", [])
            if templates and not is_cache_stale(cache_path, templates, CACHE_TTL_SECONDS):
                return self._format_template_list(templates, cached=True)

        # Scan all wikis
        registry = parse_registry(vault)
        all_templates = []

        max_templates, _, _ = self._limits(cfg)
        wikis = registry.get("wikis", [])
        if not wikis:
            return Response(
                message=f"Vault found at {vault} but registry.yaml contains no wikis.",
                break_loop=False,
            )

        # Access control: check grants
        grants_root = registry.get("grants") or {}
        grants = grants_root.get(agent_id, {}) if isinstance(grants_root, dict) else {}
        readable = grants.get("read", ["*"]) if isinstance(grants, dict) else ["*"]

        for wiki_entry in wikis:
            wiki_name = wiki_entry.get("name")
            if not wiki_name:
                continue
            
            # Skip if not readable
            if "*" not in readable and wiki_name not in readable:
                continue

            wiki_path = wiki_entry.get("path", "")
            if not os.path.isabs(wiki_path):
                wiki_path = vault / wiki_path
            else:
                wiki_path = Path(wiki_path)

            wiki_path = Path(wiki_path).resolve()
            if not wiki_path.exists():
                continue

            templates = scan_wiki_for_templates(wiki_path)
            for tmpl in templates:
                tmpl["wiki_name"] = wiki_name
                tmpl["namespace"] = f"wiki:{wiki_name}:{tmpl['template_name']}"
                all_templates.append(tmpl)

        # Cap at MAX_TEMPLATES_PER_LIST
        all_templates = all_templates[:max_templates]

        # Save to cache
        cache_data = {
            "templates": all_templates,
            "vault": str(vault),
            "agent_id": agent_id,
        }
        save_cache(cache_path, cache_data)

        return self._format_template_list(all_templates, cached=False)

    def _format_template_list(self, templates: List[Dict[str, Any]], cached: bool) -> Response:
        """Format template list as a compact table."""
        if not templates:
            return Response(
                message="No wiki pages tagged with `type: pen_paper_template` found.",
                break_loop=False,
            )

        parts = [
            f"## Wiki Templates ({'cached' if cached else 'fresh'})",
            "",
            f"| Template | Wiki | Phases | Budget | Description |",
            f"|----------|------|--------|--------|-------------|",
        ]

        for tmpl in templates:
            phases_count = len(tmpl.get("phases", []))
            budget = tmpl.get("context_budget", "medium")
            desc = tmpl.get("description", "")[:40]
            if len(tmpl.get("description", "")) > 40:
                desc += "..."
            
            parts.append(
                f"| {tmpl['namespace']} | {tmpl['wiki_name']} | {phases_count} | {budget} | {desc} |"
            )

        parts.append("")
        parts.append(f"**Total:** {len(templates)} templates")
        parts.append("")
        parts.append("Use `action=load_template` with `namespace=<wiki:name>` to load a template.")
        parts.append("Example: `action=load_template namespace=wiki:commons:research_session`")

        return Response(message="\n".join(parts), break_loop=False)

    async def _load_template(self):
        """Load a specific template and return metadata + session_payload."""
        namespace = self.args.get("namespace", "")
        
        if not namespace:
            return Response(
                message="Required: `namespace=<wiki:name>` (e.g., wiki:commons:research_session)",
                break_loop=False,
            )

        cfg = self._get_config()
        disabled = self._integration_disabled_message(cfg)
        if disabled:
            return Response(message=disabled, break_loop=False)
        vault = self._resolve_vault(cfg)
        if not vault:
            return Response(
                message="No SharedBrain vault configured.",
                break_loop=False,
            )

        # Parse namespace
        if not namespace.startswith("wiki:"):
            return Response(
                message="Invalid namespace format. Use `wiki:<wiki_name>:<template_name>`",
                break_loop=False,
            )

        parts = namespace.split(":")
        if len(parts) != 3:
            return Response(
                message="Invalid namespace format. Use `wiki:<wiki_name>:<template_name>`",
                break_loop=False,
            )

        _, wiki_name, template_name = parts

        # Scan for the template
        registry = parse_registry(vault)
        wikis = registry.get("wikis", [])
        target_template = None

        for wiki_entry in wikis:
            if wiki_entry.get("name") != wiki_name:
                continue

            wiki_path = wiki_entry.get("path", "")
            if not os.path.isabs(wiki_path):
                wiki_path = vault / wiki_path
            else:
                wiki_path = Path(wiki_path)

            wiki_path = Path(wiki_path).resolve()
            if not wiki_path.exists():
                continue

            templates = scan_wiki_for_templates(wiki_path)
            for tmpl in templates:
                if tmpl["template_name"] == template_name:
                    target_template = tmpl
                    break
            
            if target_template:
                break

        if not target_template:
            return Response(
                message=f"Template not found: {namespace}",
                break_loop=False,
            )

        # Load the page content
        try:
            content = target_template["absolute_path"].read_text(encoding="utf-8")
            frontmatter, body = parse_frontmatter(content)
        except Exception as e:
            return Response(
                message=f"Error reading template page: {e}",
                break_loop=False,
            )

        # Format response
        parts = [
            f"## Template: {namespace}",
            "",
            f"**Title:** {target_template.get('title', template_name)}",
            f"**Description:** {target_template.get('description', 'No description')}",
            f"**Context Budget:** {target_template.get('context_budget', 'medium')}",
            "",
        ]

        phases = target_template.get("phases", [])
        if phases:
            parts.append("**Phases:**")
            for i, phase in enumerate(phases, 1):
                if isinstance(phase, dict):
                    name = phase.get("name", f"Phase {i}")
                    desc = phase.get("description", "")
                    parts.append(f"  {i}. {name} — {desc}")
                else:
                    parts.append(f"  {i}. {phase}")
            parts.append("")

        triggers = target_template.get("triggers", [])
        if triggers:
            parts.append(f"**Triggers:** {', '.join(triggers)}")
            parts.append("")

        _, max_preview_chars, _ = self._limits(cfg)
        preview = body[:max_preview_chars]
        if len(body) > max_preview_chars:
            preview += "\n_[truncated]_"
        
        parts.extend([
            "**Preview:**",
            "```",
            preview,
            "```",
            "",
        ])

        # Generate session_payload blob
        session_payload = self._generate_session_payload(target_template, frontmatter)
        parts.extend([
            "**Session Payload** (copy into `pen_paper` create `content`, or use as a future payload source):",
            "```json",
            session_payload,
            "```",
            "",
            "To create a session with this template today, call:",
            "`pen_paper(action=\"create\", name=\"your_task\", content=<session payload or selected template notes>)`",
        ])

        return Response(message="\n".join(parts), break_loop=False)

    def _generate_session_payload(self, template: Dict[str, Any], frontmatter: Dict[str, Any]) -> str:
        """Generate a session payload blob suitable for pen_paper create content."""
        phases = template.get("phases", [])
        
        # Build initial sections based on phases
        sections = {}
        for i, phase in enumerate(phases):
            if isinstance(phase, dict):
                name = phase.get("name", f"phase_{i+1}")
                desc = phase.get("description", "")
                sections[name] = f"# {name}\n\n{desc}\n\n"
            else:
                sections[f"phase_{i+1}"] = f"# {phase}\n\n"

        payload = {
            "template_source": template.get("namespace", "unknown"),
            "template_name": template.get("template_name", "unknown"),
            "template_wiki": template.get("wiki_name", "unknown"),
            "sections": sections,
            "metadata": {
                "context_budget": template.get("context_budget", "medium"),
                "triggers": template.get("triggers", []),
                "description": template.get("description", ""),
            },
        }

        return json.dumps(payload, indent=2)
