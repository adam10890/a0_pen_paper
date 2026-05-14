"""
Pen & Paper Tool
ניהול מרחב עבודה זמני למשימות מורכבות - כמו פנקס וניירות עבודה

Location: usr/plugins/a0_pen_paper/tools/pen_paper.py
"""

import json
import shutil
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any

from helpers.tool import Tool, Response
from helpers import files


class PenPaper(Tool):
    """
    Tool for managing temporary working notes (like pen & paper).
    Organizes tasks with findings, results, insights, notes, decisions, and backtrack.
    """

    # Valid sections for workspace
    VALID_SECTIONS = [
        "findings",
        "results", 
        "insights",
        "notes",
        "decisions",
        "backtrack"
    ]
    
    # Onboarding config path
    RUNTIME_BASE = "usr/pen_and_paper"
    ONBOARDING_PATH = f"{RUNTIME_BASE}/config/onboarding.yaml"
    
    def _load_onboarding(self) -> dict:
        """Load onboarding configuration from YAML file."""
        onboarding_path = files.get_abs_path(self.ONBOARDING_PATH)
        
        if Path(onboarding_path).exists():
            try:
                content = files.read_file(onboarding_path)
                return yaml.safe_load(content)
            except Exception as e:
                print(f"Failed to load onboarding config: {e}")
        return {}
    
    def _is_first_time_user(self) -> bool:
        """Check if this is a first-time user (no existing sessions)."""
        active_dir = files.get_abs_path("usr/pen_and_paper/sessions/active")
        archive_dir = files.get_abs_path("usr/pen_and_paper/sessions/archive")
        
        # Check if any sessions exist
        active_count = 0
        archive_count = 0
        
        if Path(active_dir).exists():
            active_count = len([d for d in Path(active_dir).iterdir() 
                               if d.is_dir() and not d.name.startswith('.')])
        
        if Path(archive_dir).exists():
            archive_count = len([d for d in Path(archive_dir).iterdir() 
                                if d.is_dir() and not d.name.startswith('.')])
        
        return active_count == 0 and archive_count == 0
    
    def _get_quick_start_message(self) -> str:
        """Get formatted quick start message from onboarding config."""
        onboarding = self._load_onboarding()
        
        if not onboarding:
            return ""
        
        msg = "# 📝 Pen & Paper - Quick Start\n\n"
        
        # System overview
        overview = onboarding.get("system_overview", {})
        if overview:
            msg += f"**{overview.get('name', 'Pen & Paper')}**: {overview.get('purpose', '')}\n"
            msg += f"*{overview.get('principle', '')}*\n\n"
        
        # Core rules
        rules = onboarding.get("core_rules", [])
        if rules:
            msg += "## Core Rules\n"
            for rule in rules[:5]:  # Show top 5 rules
                msg += f"- {rule}\n"
            msg += "\n"
        
        # Available templates
        templates = onboarding.get("templates", {}).get("available", [])
        if templates:
            msg += "## Available Templates\n"
            for tmpl in templates:
                msg += f"- **{tmpl.get('id', '')}**: {tmpl.get('purpose', '')}\n"
            msg += "\n"
        
        # Quick commands
        msg += "## Quick Commands\n"
        msg += "```\n"
        msg += "pen_paper(action='create', name='my_task')  # Create new session\n"
        msg += "pen_paper(action='update', name='...', section='notes', content='...')  # Add notes\n"
        msg += "pen_paper(action='read', name='...')  # Read session\n"
        msg += "pen_paper(action='close', name='...', vectorize=True)  # Close and save\n"
        msg += "pen_paper(action='help')  # Show this help\n"
        msg += "```\n\n"
        
        return msg
    
    async def _show_help(self) -> Response:
        """Show help information including onboarding and available templates."""
        help_msg = self._get_quick_start_message()
        
        if not help_msg:
            help_msg = "# 📝 Pen & Paper Help\n\n"
        
        # Add available templates from registry
        templates = self._get_available_templates()
        if templates:
            help_msg += "## Templates from Registry\n"
            for tmpl in templates:
                help_msg += f"- `{tmpl}`\n"
            help_msg += "\n"
        
        # Add valid sections info
        help_msg += "## Valid Sections\n"
        for sec in self.VALID_SECTIONS:
            help_msg += f"- `{sec}`\n"
        help_msg += "\n"
        
        # Add action reference
        help_msg += "## Available Actions\n"
        help_msg += "| Action | Description |\n"
        help_msg += "|--------|-------------|\n"
        help_msg += "| `create` | Create new workspace |\n"
        help_msg += "| `update` | Add content to a section |\n"
        help_msg += "| `read` | Read workspace or section |\n"
        help_msg += "| `close` | Close workspace with auto-summary |\n"
        help_msg += "| `list` | List all active workspaces |\n"
        help_msg += "| `help` | Show this help message |\n"
        
        return Response(message=help_msg, break_loop=False)

    async def execute(self, **kwargs) -> Response:
        """
        Main execution entry point.
        
        Args (via kwargs):
            action: "create" | "update" | "read" | "close" | "list"
            name: Name of the workspace
            section: Section to update/read (findings/results/insights/notes/decisions/backtrack)
            content: Content to add to the section
            ephemeral: bool = False (don't keep file after close)
            retrieve_context: bool = True (auto-load similar sessions)
            vectorize: bool = True (convert to vectors before closing)
        """
        
        action = self.args.get("action", "list")
        name = self.args.get("name", "")
        section = self.args.get("section", "notes")
        content = self.args.get("content", "")
        ephemeral = self.args.get("ephemeral", False)
        retrieve_context = self.args.get("retrieve_context", True)
        vectorize = self.args.get("vectorize", True)
        template = self.args.get("template", None)
        
        # Handle help action first
        if action == "help":
            return await self._show_help()
        
        if action == "create":
            if not name:
                return Response(
                    message="Error: name is required for create action",
                    break_loop=False
                )
            return await self._create_workspace(name, retrieve_context=retrieve_context, template=template, content=content)
        
        elif action == "update":
            if not name:
                return Response(
                    message="Error: name is required for update action",
                    break_loop=False
                )
            if not content:
                return Response(
                    message="Error: content is required for update action",
                    break_loop=False
                )
            if section not in self.VALID_SECTIONS:
                return Response(
                    message=f"Error: Invalid section '{section}'.\n"
                           f"Valid sections: {', '.join(self.VALID_SECTIONS)}",
                    break_loop=False
                )
            return await self._update_section(name, section, content)
        
        elif action == "read":
            if not name:
                return Response(
                    message="Error: name is required for read action",
                    break_loop=False
                )
            return await self._read_workspace(name, section if section else None)
        
        elif action == "close":
            if not name:
                return Response(
                    message="Error: name is required for close action",
                    break_loop=False
                )
            return await self._close_workspace(name, vectorize=vectorize, ephemeral=ephemeral)
        
        elif action == "list":
            return await self._list_workspaces()
        

        elif action == "list_templates":
            return await self._list_templates()

        elif action == "create_template":
            tmpl_name = self.args.get("template_name", "")
            if not tmpl_name:
                return Response(message="Error: template_name required", break_loop=False)
            return await self._create_template(
                tmpl_name, self.args.get("description", ""),
                self.args.get("description_he", ""),
                self.args.get("phases", []),
                self.args.get("triggers", []),
                self.args.get("triggers_he", []),
                self.args.get("content", "")
            )

        elif action == "edit_template":
            tmpl_name = self.args.get("template_name", "")
            if not tmpl_name:
                return Response(message="Error: template_name required", break_loop=False)
            return await self._edit_template(tmpl_name, self.args.get("updates", {}))

        elif action == "delete_template":
            tmpl_name = self.args.get("template_name", "")
            if not tmpl_name:
                return Response(message="Error: template_name required", break_loop=False)
            return await self._delete_template(tmpl_name)

        elif action == "use_template":
            tmpl_name = self.args.get("template_name", "")
            if not tmpl_name:
                return Response(message="Error: template_name required", break_loop=False)
            import datetime as _dt
            ws_name = name if name else tmpl_name + "_" + _dt.datetime.now().strftime("%Y%m%d_%H%M")
            return await self._use_template(tmpl_name, ws_name, self.args.get("variables", {}))

        else:
            return Response(
                message=f"Unknown action: {action}\n\n"
                       f"**Available actions:**\n"
                       f"- `create`: Create new workspace\n"
                       f"- `update`: Add content to a section\n"
                       f"- `read`: Read workspace or section\n"
                       f"- `close`: Close workspace with auto-summary\n"
                       f"- `list`: List all active workspaces\n"
                       f"- `help`: Show help and onboarding information\n\n"
                       f"**Valid sections:** {', '.join(self.VALID_SECTIONS)}\n\n"
                       f"**New Features:**\n"
                       f"- `ephemeral`: bool = False (don't keep file after close)\n"
                       f"- `retrieve_context`: bool = True (auto-load similar sessions)\n"
                       f"- `vectorize`: bool = True (convert to vectors before closing)\n\n"
                       f"💡 **Tip:** Use `pen_paper(action='help')` for detailed guidance.",
                break_loop=False
            )

    def _get_workspace_dir(self, name: str) -> str:
        """Get absolute path to workspace directory"""
        safe_name = files.safe_file_name(name)
        return files.get_abs_path(f"usr/pen_and_paper/sessions/active/{safe_name}")

    def _get_workspace_file(self, name: str) -> str:
        """Get path to workspace.json file"""
        return str(Path(self._get_workspace_dir(name)) / "workspace.json")

    # Template registry path (dynamic loading)
    TEMPLATE_REGISTRY_PATH = "usr/pen_and_paper/knowledge/workflows/template_registry.json"

    def _load_full_registry(self) -> dict:
        """Load full template registry including base_workflows."""
        registry_path = files.get_abs_path(self.TEMPLATE_REGISTRY_PATH)
        
        if Path(registry_path).exists():
            try:
                content = files.read_file(registry_path)
                return json.loads(content)
            except Exception as e:
                print(f"Failed to load template registry: {e}")
        return {}

    def _load_template_registry(self) -> dict:
        """Load just the templates section."""
        return self._load_full_registry().get("templates", {})

    def _get_base_workflows(self) -> dict:
        """Get base workflows that are always available as sub-flows."""
        registry = self._load_full_registry()
        return registry.get("base_workflows", {})

    def _get_available_templates(self) -> list[str]:
        """Get list of available template names."""
        registry = self._load_template_registry()
        return list(registry.keys())

    def _suggest_template(self, task_name: str) -> str | None:
        """Suggest a template based on task name triggers."""
        registry = self._load_template_registry()
        task_lower = task_name.lower()
        
        for template_name, template_data in registry.items():
            triggers = template_data.get("triggers", [])
            for trigger in triggers:
                if trigger.lower() in task_lower:
                    return template_name
        return None

    def _load_template_content(self, template_name: str) -> dict | None:
        """Load workflow template content from registry and file."""
        registry = self._load_template_registry()
        
        if template_name not in registry:
            return None
        
        template_data = registry[template_name]
        template_file = template_data.get("file", f"{template_name}.md")
        template_path = files.get_abs_path(
            f"usr/pen_and_paper/knowledge/workflows/{template_file}"
        )
        
        result = {
            "phases": template_data.get("phases", []),
            "description": template_data.get("description", ""),
            "triggers": template_data.get("triggers", [])
        }
        
        if Path(template_path).exists():
            try:
                result["content"] = files.read_file(template_path)
            except Exception:
                pass
        
        return result


    # ========== Template Management Methods ==========

    async def _list_templates(self) -> Response:
        """List all available templates with detailed info."""
        registry = self._load_template_registry()
        if not registry:
            return Response(message="No templates found.", break_loop=False)
        msg = "**Available Pen & Paper Templates**\n\n"
        msg += f"Total: **{len(registry)}** templates\n\n"
        msg += "| # | Template | Description | Phases | Triggers |\n"
        msg += "|---|----------|-------------|--------|----------|\n"
        for i, (tname, data) in enumerate(registry.items(), 1):
            desc = data.get("description", "")
            desc_he = data.get("description_he", "")
            full_desc = f"{desc} / {desc_he}" if desc_he else desc
            phases = " > ".join(data.get("phases", []))
            trigs = data.get("triggers", [])[:5]
            trig_str = ", ".join(trigs)
            if len(data.get("triggers", [])) > 5:
                trig_str += "..."
            msg += f"| {i} | **{tname}** | {full_desc} | {phases} | {trig_str} |\n"
        msg += "\n**Actions:** use_template, create_template, edit_template, delete_template"
        return Response(message=msg, break_loop=False)

    async def _create_template(self, template_name, description, description_he,
                                phases, triggers, triggers_he, template_content) -> Response:
        """Create a new template with MD file and registry entry."""
        registry = self._load_template_registry()
        if template_name in registry:
            return Response(message=f"Template '{template_name}' already exists.", break_loop=False)
        if not template_content:
            sections = []
            for i, phase in enumerate(phases, 1):
                sections.append(f"## Phase {i}: {phase}\n\n### Notes:\n- \n")
            template_content = f"# {template_name.replace('_', ' ').title()} Workflow\n"
            template_content += f"## Overview\n{description}\n\n---\n\n"
            template_content += "\n---\n\n".join(sections)
        template_file = f"{template_name}.md"
        template_path = files.get_abs_path(f"usr/pen_and_paper/knowledge/workflows/{template_file}")
        try:
            files.write_file(template_path, template_content)
        except Exception as e:
            return Response(message=f"Failed to create file: {e}", break_loop=False)
        all_triggers = triggers + triggers_he
        registry[template_name] = {
            "file": template_file, "description": description,
            "description_he": description_he, "phases": phases, "triggers": all_triggers
        }
        full_registry = self._load_full_registry()
        full_registry["templates"] = registry
        registry_path = files.get_abs_path(self.TEMPLATE_REGISTRY_PATH)
        files.write_file(registry_path, json.dumps(full_registry, indent=2, ensure_ascii=False))
        phase_str = " > ".join(phases)
        trig_str = ", ".join(all_triggers[:8])
        return Response(message=f"Template '{template_name}' created! Phases: {phase_str}. Triggers: {trig_str}", break_loop=False)

    async def _edit_template(self, template_name, updates) -> Response:
        """Edit template metadata and/or content."""
        registry = self._load_template_registry()
        if template_name not in registry:
            return Response(message=f"Template '{template_name}' not found.", break_loop=False)
        changes = []
        for field in ["description", "description_he", "phases", "triggers"]:
            if field in updates:
                registry[template_name][field] = updates[field]
                changes.append(f"Updated {field}")
        if "content" in updates:
            tf = registry[template_name].get("file", f"{template_name}.md")
            tp = files.get_abs_path(f"usr/pen_and_paper/knowledge/workflows/{tf}")
            try:
                files.write_file(tp, updates["content"])
                changes.append("Updated content")
            except Exception as e:
                return Response(message=f"Failed: {e}", break_loop=False)
        if changes:
            full_registry = self._load_full_registry()
            full_registry["templates"] = registry
            rp = files.get_abs_path(self.TEMPLATE_REGISTRY_PATH)
            files.write_file(rp, json.dumps(full_registry, indent=2, ensure_ascii=False))
        chg = ", ".join(changes) if changes else "No changes"
        return Response(message=f"Template '{template_name}' updated: {chg}", break_loop=False)

    async def _delete_template(self, template_name) -> Response:
        """Delete template (archive file, remove from registry)."""
        registry = self._load_template_registry()
        if template_name not in registry:
            return Response(message=f"Template '{template_name}' not found.", break_loop=False)
        tf = registry[template_name].get("file", f"{template_name}.md")
        tp = files.get_abs_path(f"usr/pen_and_paper/knowledge/workflows/{tf}")
        del registry[template_name]
        full_registry = self._load_full_registry()
        full_registry["templates"] = registry
        rp = files.get_abs_path(self.TEMPLATE_REGISTRY_PATH)
        files.write_file(rp, json.dumps(full_registry, indent=2, ensure_ascii=False))
        if Path(tp).exists():
            archive_dir = files.get_abs_path("usr/pen_and_paper/_archived/templates")
            Path(archive_dir).mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.move(tp, str(Path(archive_dir) / tf))
        return Response(message=f"Template '{template_name}' deleted (archived). Remaining: {len(registry)}", break_loop=False)

    async def _use_template(self, template_name, workspace_name, variables=None) -> Response:
        """Create workspace from template with optional variable substitution."""
        template_data = self._load_template_content(template_name)
        if not template_data:
            return Response(message=f"Template '{template_name}' not found.", break_loop=False)
        return await self._create_workspace(workspace_name, retrieve_context=True, template=template_name)

    async def _create_workspace(self, name: str, retrieve_context: bool = True, template: str | None = None, content: str = "") -> Response:
        """Create a new workspace with optional context retrieval, template, and initial content"""

        workspace_dir = self._get_workspace_dir(name)
        workspace_file = self._get_workspace_file(name)

        # Check if already exists
        if Path(workspace_file).exists():
            return Response(
                message=f"⚠️ Workspace '{name}' already exists.\n"
                       f"Use `pen_paper(action='read', name='{name}')` to view it.",
                break_loop=False
            )

        # Create directory
        Path(workspace_dir).mkdir(parents=True, exist_ok=True)

        # Initialize workspace
        workspace = {
            "metadata": {
                "name": name,
                "created_at": datetime.now().isoformat(),
                "status": "active",
                "agent": self.agent.agent_name,
                "ephemeral": False,  # Default to persistent
                "template": template  # Track which template was used
            },
            "findings": [],
            "results": [],
            "insights": [],
            "notes": [],
            "decisions": [],
            "backtrack": []
        }

        # Add initial content to notes if provided
        if content:
            workspace["notes"].append({
                "timestamp": datetime.now().isoformat(),
                "content": content,
                "agent": self.agent.agent_name
            })

        # Load template if specified
        template_info = ""
        if template:
            template_data = self._load_template_content(template)
            if template_data:
                tmpl = template_data.get("template", {})
                phases = tmpl.get("phases", [])
                description = tmpl.get("description", "")
                
                # Add template phases to notes as checklist
                if phases:
                    phase_checklist = "\n".join([f"[ ] Phase {i+1}: {p}" for i, p in enumerate(phases)])
                    workspace["notes"].append({
                        "timestamp": datetime.now().isoformat(),
                        "content": f"📋 Workflow: {template}\n{description}\n\n{phase_checklist}",
                        "agent": "template"
                    })
                
                template_info = f"\n\n**Template:** `{template}` ({description})\n**Phases:** {' → '.join(phases)}\n"
            else:
                template_info = f"\n\n⚠️ Template '{template}' not found. Available: {', '.join(self._get_available_templates())}\n"

        # Try to retrieve similar past sessions if requested

        context_info = ""

        if retrieve_context:

            try:

                from usr.plugins.a0_pen_paper.helpers.pen_paper_vectorizer import PenPaperVectorizer

                pp_vectorizer = PenPaperVectorizer()

                

                # Use workspace name as task description for context retrieval

                context = pp_vectorizer.retrieve_similar_sessions(

                    task_description=name,

                    max_results=3,

                    max_tokens=500

                )

                

                if context:

                    context_info = f"\n\n{context}\n\n---\n"

                    # Add retrieved context to insights section

                    workspace["insights"].append({

                        "timestamp": datetime.now().isoformat(),

                        "content": context,

                        "agent": "vector_retrieval"

                    })

            except Exception as e:

                # Graceful fallback - continue without context

                print(f"Context retrieval failed: {e}")

        

        files.write_file(workspace_file, json.dumps(workspace, indent=2))

        

        # Create README

        readme_content = f"""# Pen & Paper: {name}



**Created:** {workspace['metadata']['created_at']}

**Status:** Active

**Agent:** {self.agent.agent_name}

**Ephemeral:** {workspace['metadata']['ephemeral']}



{context_info}{template_info}

## Sections



| Section | Purpose |

|---------|---------|

| findings | Discovered facts and observations |

| results | Completed outcomes and outputs |

| insights | Learned lessons and realizations |

| notes | General notes and thoughts |

| decisions | Key decisions made |

| backtrack | Items to revisit or reconsider |



## Quick Commands



```json

// Add to section

{{"tool_name": "pen_paper", "tool_args": {{"action": "update", "name": "{name}", "section": "findings", "content": "Your finding here"}}}}



// Read workspace

{{"tool_name": "pen_paper", "tool_args": {{"action": "read", "name": "{name}"}}}}



// Close workspace (vectorize + ephemeral)

{{"tool_name": "pen_paper", "tool_args": {{"action": "close", "name": "{name}", "vectorize": true, "ephemeral": true}}}}

```

"""

        

        readme_file = str(Path(workspace_dir) / "README.md")

        files.write_file(readme_file, readme_content)

        

        response_msg = f"📝 Created workspace: **{name}**\n\n"

        response_msg += f"**Path:** `{workspace_dir}`\n\n"

        response_msg += f"**Available sections:**\n"

        response_msg += f"- `findings` - Discovered facts and observations\n"

        response_msg += f"- `results` - Completed outcomes and outputs\n"

        response_msg += f"- `insights` - Learned lessons and realizations\n"

        response_msg += f"- `notes` - General notes and thoughts\n"

        response_msg += f"- `decisions` - Key decisions made\n"

        response_msg += f"- `backtrack` - Items to revisit or reconsider\n\n"

        response_msg += f"**Ephemeral:** {workspace['metadata']['ephemeral']}\n\n"

        

        if context_info:
            response_msg += f"**Context retrieved from similar past sessions**\n\n"
        
        if template_info:
            response_msg += template_info + "\n"
        
        # Add base workflows (always available sub-flows)
        base_wf = self._get_base_workflows()
        if base_wf:
            base_list = base_wf.get("list", [])
            hooks = base_wf.get("hooks", {})
            if base_list:
                response_msg += f"**🔄 Available Sub-Workflows:** {', '.join(base_list)}\n"
                response_msg += f"**Hooks:** stuck→{hooks.get('on_stuck', 'debugging')} | unknown→{hooks.get('on_unknown', 'research')} | complete→{hooks.get('on_complete', 'validation')}\n\n"
        
        response_msg += f"**Next:** Start documenting with:\n"
        response_msg += f"`pen_paper(action='update', name='{name}', section='notes', content='...')`"

        

        return Response(

            message=response_msg,

            break_loop=False

        )

    async def _update_section(self, name: str, section: str, content: str) -> Response:
        """Update a section in the workspace"""
        

        workspace_file = self._get_workspace_file(name)
        

        if not Path(workspace_file).exists():
            return Response(
                message=f"❌ Workspace '{name}' not found.\n"
                       f"Create it first with: `pen_paper(action='create', name='{name}')`",
                break_loop=False
            )
        

        try:
            # Load workspace
            workspace = json.loads(files.read_file(workspace_file))
            

            # Check if closed
            if workspace["metadata"].get("status") == "closed":
                return Response(
                    message=f"❌ Workspace '{name}' is closed.\n"
                           f"Create a new workspace to continue work.",
                    break_loop=False
                )
            

            # Create entry
            entry = {
                "timestamp": datetime.now().isoformat(),
                "content": content,
                "agent": self.agent.agent_name
            }
            

            # Ensure section exists
            if section not in workspace:
                workspace[section] = []
            

            # Add entry
            workspace[section].append(entry)
            

            # Save
            files.write_file(workspace_file, json.dumps(workspace, indent=2))
            

            count = len(workspace[section])
            

            return Response(
                message=f"✏️ Updated **{section}** in '{name}'\n\n"
                       f"**Entry #{count}:** {content[:200]}{'...' if len(content) > 200 else ''}\n\n"
                       f"Total {section} entries: {count}",
                break_loop=False
            )
            

        except Exception as e:
            return Response(
                message=f"❌ Error updating workspace: {str(e)[:200]}",
                break_loop=False
            )

    async def _read_workspace(self, name: str, section: str | None = None) -> Response:
        """Read workspace or specific section"""
        

        workspace_file = self._get_workspace_file(name)
        

        if not Path(workspace_file).exists():
            return Response(
                message=f"❌ Workspace '{name}' not found.",
                break_loop=False
            )
        

        try:
            workspace = json.loads(files.read_file(workspace_file))
            

            if section:
                # Read specific section
                if section not in workspace:
                    return Response(
                        message=f"❌ Section '{section}' not found in workspace '{name}'.",
                        break_loop=False
                    )
                

                section_data = workspace[section]
                

                if not section_data:
                    return Response(
                        message=f"📭 Section **{section}** in workspace '{name}' is empty.",
                        break_loop=False
                    )
                

                output = f"# {section.upper()} - {name}\n\n"
                

                for i, entry in enumerate(section_data, 1):
                    timestamp = entry.get('timestamp', 'unknown')[:16]
                    output += f"### Entry {i} ({timestamp})\n"
                    output += f"{entry.get('content', '')}\n\n"
                

                return Response(message=output, break_loop=False)
            

            else:
                # Read full summary
                output = f"# 📝 PEN & PAPER: {name}\n\n"
                output += f"**Status:** {workspace['metadata'].get('status', 'unknown')}\n"
                output += f"**Created:** {workspace['metadata'].get('created_at', 'unknown')[:16]}\n"
                output += f"**Agent:** {workspace['metadata'].get('agent', 'unknown')}\n"
                output += f"**Ephemeral:** {workspace['metadata'].get('ephemeral', False)}\n\n"
                

                # Count entries
                output += "## Summary\n\n"
                output += "| Section | Entries |\n"
                output += "|---------|--------|\n"
                

                total = 0
                for sec in self.VALID_SECTIONS:
                    count = len(workspace.get(sec, []))
                    total += count
                    output += f"| {sec} | {count} |\n"
                

                output += f"| **Total** | **{total}** |\n\n"
                

                # Show recent entries from each non-empty section
                for sec in self.VALID_SECTIONS:
                    entries = workspace.get(sec, [])
                    if entries:
                        output += f"## Recent {sec.title()} ({len(entries)} total)\n\n"
                        

                        # Show last 2 entries
                        for entry in entries[-2:]:
                            content = entry.get('content', '')[:150]
                            output += f"- {content}{'...' if len(entry.get('content', '')) > 150 else ''}\n"
                        

                        output += "\n"
                

                return Response(message=output, break_loop=False)
                

        except Exception as e:
            return Response(
                message=f"❌ Error reading workspace: {str(e)[:200]}",
                break_loop=False
            )

    async def _close_workspace(self, name: str, vectorize: bool = True, ephemeral: bool = False) -> Response:
        """Close workspace with optional vectorization and ephemeral deletion"""
        

        workspace_file = self._get_workspace_file(name)
        workspace_dir = self._get_workspace_dir(name)
        

        if not Path(workspace_file).exists():
            return Response(
                message=f"❌ Workspace '{name}' not found.",
                break_loop=False
            )
        

        try:
            workspace = json.loads(files.read_file(workspace_file))
            

            # Check if already closed
            if workspace["metadata"].get("status") == "closed":
                return Response(
                    message=f"⚠️ Workspace '{name}' is already closed.",
                    break_loop=False
                )
            

            # Update metadata
            workspace["metadata"]["status"] = "closed"
            workspace["metadata"]["closed_at"] = datetime.now().isoformat()
            workspace["metadata"]["ephemeral"] = ephemeral
            

            # Generate final summary
            final_summary = self._generate_final_summary(workspace)
            workspace["final_summary"] = final_summary
            

            # Save updated workspace
            files.write_file(workspace_file, json.dumps(workspace, indent=2))
            

            # Vectorize session if requested
            vectorization_info = ""
            if vectorize:
                try:
                    from usr.plugins.a0_pen_paper.helpers.pen_paper_vectorizer import PenPaperVectorizer
                    pp_vectorizer = PenPaperVectorizer()
                    

                    # Vectorize the session
                    chunks = pp_vectorizer.vectorize_session(
                        Path(workspace_file),
                        sections_to_keep=["decisions", "insights", "findings"],
                        delete_after=ephemeral
                    )
                    

                    if chunks > 0:
                        vectorization_info = f"\n\n**Vectorized:** {chunks} chunks added to vector DB"
                        if ephemeral:
                            vectorization_info += " (source file deleted - ephemeral mode)"
                    else:
                        vectorization_info = "\n\n**Vectorization:** No content to vectorize"
                except Exception as e:
                    vectorization_info = f"\n\n**Vectorization:** Failed - {str(e)[:100]}"
            

            # Handle archiving vs deletion
            if ephemeral and vectorize:
                # File already deleted by vectorize_session, just report
                archive_info = "**Archived:** Session vectorized and source deleted (ephemeral mode)"
            elif ephemeral:
                # Delete without archiving
                shutil.rmtree(workspace_dir)
                archive_info = "**Deleted:** Session deleted (ephemeral mode, no vectorization)"
            else:
                # Normal archiving
                archive_dir = files.get_abs_path(f"usr/pen_and_paper/sessions/archive")
                Path(archive_dir).mkdir(parents=True, exist_ok=True)
                

                archive_path = str(Path(archive_dir) / files.safe_file_name(name))
                

                # If archive already exists, add timestamp
                if Path(archive_path).exists():
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    archive_path = f"{archive_path}_{timestamp}"
                

                shutil.move(workspace_dir, archive_path)
                archive_info = f"**Archived to:** `{archive_path}`"
            

            return Response(
                message=f"✅ Workspace '{name}' closed!\n\n"
                       f"{archive_info}"
                       f"{vectorization_info}\n\n"
                       f"---\n\n{final_summary}",
                break_loop=False
            )
            

        except Exception as e:
            return Response(
                message=f"❌ Error closing workspace: {str(e)[:200]}",
                break_loop=False
            )

    def _generate_final_summary(self, workspace: dict) -> str:
        """Generate final summary for closed workspace"""
        

        summary = "# Final Summary\n\n"
        summary += f"**Closed:** {workspace['metadata'].get('closed_at', 'unknown')[:16]}\n"
        summary += f"**Duration:** Created {workspace['metadata'].get('created_at', 'unknown')[:10]}\n\n"
        

        # Key Findings
        findings = workspace.get("findings", [])
        if findings:
            summary += f"## Key Findings ({len(findings)})\n\n"
            for entry in findings:
                summary += f"- {entry.get('content', '')}\n"
            summary += "\n"
        

        # Results Achieved
        results = workspace.get("results", [])
        if results:
            summary += f"## Results Achieved ({len(results)})\n\n"
            for entry in results:
                summary += f"- {entry.get('content', '')}\n"
            summary += "\n"
        

        # Insights Gained
        insights = workspace.get("insights", [])
        if insights:
            summary += f"## Insights Gained ({len(insights)})\n\n"
            for entry in insights:
                summary += f"- {entry.get('content', '')}\n"
            summary += "\n"
        

        # Decisions Made
        decisions = workspace.get("decisions", [])
        if decisions:
            summary += f"## Decisions Made ({len(decisions)})\n\n"
            for entry in decisions:
                summary += f"- {entry.get('content', '')}\n"
            summary += "\n"
        

        # Backtrack items (if any remain)
        backtrack = workspace.get("backtrack", [])
        if backtrack:
            summary += f"## Open Items / Backtrack ({len(backtrack)})\n\n"
            for entry in backtrack:
                summary += f"- ⚠️ {entry.get('content', '')}\n"
            summary += "\n"
        

        return summary

    async def _list_workspaces(self) -> Response:
        """List all active workspaces"""
        

        workspaces_dir = files.get_abs_path("usr/pen_and_paper/sessions/active")
        Path(workspaces_dir).mkdir(parents=True, exist_ok=True)
        

        workspaces = []
        

        for ws_path in Path(workspaces_dir).iterdir():
            # Skip archived and hidden folders
            if not ws_path.is_dir() or ws_path.name.startswith("_"):
                continue
            

            workspace_file = ws_path / "workspace.json"
            

            if workspace_file.exists():
                try:
                    workspace = json.loads(files.read_file(str(workspace_file)))
                    

                    # Count entries
                    total_entries = sum(
                        len(workspace.get(s, [])) 
                        for s in self.VALID_SECTIONS
                    )
                    

                    workspaces.append({
                        "name": workspace["metadata"].get("name", ws_path.name),
                        "status": workspace["metadata"].get("status", "unknown"),
                        "created": workspace["metadata"].get("created_at", "unknown")[:16],
                        "entries": total_entries,
                        "ephemeral": workspace["metadata"].get("ephemeral", False)
                    })
                except Exception:
                    pass
        

        if not workspaces:
            # Check if this is a first-time user and show onboarding
            if self._is_first_time_user():
                onboarding_msg = self._get_quick_start_message()
                return Response(
                    message=f"🎉 **Welcome to Pen & Paper!**\n\n"
                           f"{onboarding_msg}"
                           f"---\n\n"
                           f"📭 No active workspaces yet.\n\n"
                           f"**Create your first workspace:**\n"
                           f"`pen_paper(action='create', name='my_first_task')`",
                    break_loop=False
                )
            else:
                return Response(
                    message="📭 No active workspaces.\n\n"
                           "**Create a new workspace:**\n"
                           "`pen_paper(action='create', name='my_notes')`\n\n"
                           "💡 **Tip:** Use `pen_paper(action='help')` for guidance.",
                    break_loop=False
                )
        

        output = f"# 📝 Active Workspaces ({len(workspaces)})\n\n"
        output += "| Name | Status | Created | Entries | Ephemeral |\n"
        output += "|------|--------|---------|--------|-----------|\n"
        

        for ws in sorted(workspaces, key=lambda x: x["created"], reverse=True):
            ephemeral_icon = "🔄" if ws['ephemeral'] else ""
            output += f"| {ws['name']} | {ws['status']} | {ws['created']} | {ws['entries']} | {ephemeral_icon} |\n"
        

        output += "\n**Actions:**\n"
        output += "- Read: `pen_paper(action='read', name='...')`\n"
        output += "- Update: `pen_paper(action='update', name='...', section='...', content='...')`\n"
        output += "- Close: `pen_paper(action='close', name='...', vectorize=true, ephemeral=false)`\n"
        

        return Response(message=output, break_loop=False)


