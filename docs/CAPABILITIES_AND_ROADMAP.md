# Pen & Paper Plugin - Capabilities and Roadmap

## Current Capabilities (v1.3.0)

### Core Features

- **Structured Workspace Management**: Create, update, read, list, and close structured thinking workspaces
- **Template System**: Pre-configured templates for structured working sessions with phases (Plan, Work, Review)
- **Local Sessions**: Session storage in `usr/pen_and_paper/sessions/` with active and archive separation
- **Runtime Configuration**: Install-safe runtime storage in `usr/pen_and_paper/` with seed files
- **Template Registry**: JSON-based template registry with triggers and workflow hooks
- **State-DOX Session State**: YAML workflow-state templates copied into each active session as mutable live state, with compact JSONL event audit
- **Scribe State Bridge**: Active sessions expose `state/session_state.yaml`, `state/events.jsonl`, and workflow live copies for `a0_scribe`
- **Chat Focus Tracking**: Pen & Paper records the current chat workspace so background writers route state to the intended session
- **Multilingual Support**: Template descriptions in English and Hebrew
- **LLM Wiki Integration**: Read-only discovery and loading of wiki pages tagged as Pen & Paper templates from the LLM Wiki SharedBrain vault
- **Diagram Export**: `pen_paper_diagram` generates editable `.drawio` artifacts from workflow templates, active sessions, or ad hoc text
- **Whiteboard Bridge**: Workflows Canvas can send a generated diagram as annotation-ready `a0_whiteboard` shapes
- **Bilingual Workflow Dashboard**: Workflows Canvas includes a small Hebrew/English toggle persisted in browser local storage

### Diagram Export (New in v1.3.0)

- **Tool**: `pen_paper_diagram`
- **Sources**: `template`, `session`, `text`
- **Diagram Types**: `flow`, `flow-vertical`, `layers`, `sequence`, `timeline`
- **Themes**: `tech-blue`, `morandi`, `mint`, `terracotta`, `indigo`
- **Runtime Storage**:
  - Template diagrams: `usr/pen_and_paper/diagrams/templates/<template>/`
  - Session diagrams: `usr/pen_and_paper/sessions/active/<session>/diagrams/`
  - Ad hoc diagrams: `usr/pen_and_paper/diagrams/ad_hoc/`
- **Boundary**: Exports draw.io XML artifacts; it does not write or replace whiteboard state
- **Bridge**: `diagrams_send_whiteboard` creates a derived whiteboard board; Pen & Paper remains source of truth

### State-DOX + Scribe Bridge (New in v1.3.0)

- **Runtime Files**:
  - `state/events.jsonl`: append-only compact event audit
  - `state/session_state.yaml`: current session-level working state
  - `state/workflows/*.yaml`: mutable live workflow state copied from templates
- **Workflow Templates**: `data/workflow_state_templates/*.yaml`
- **Skill Links**: each workflow template declares `scribe.skill`, aligned with
  `a0_scribe/skills/scribe-workflow-*`
- **Focus Contract**: `tool_execute_after/_51_pen_paper_focus.py` updates the
  active chat workspace from `agent.loop_data.current_tool.args` when
  `tool_args` is not provided by Agent Zero core
- **Boundary**: Pen & Paper owns storage and templates; `a0_scribe` owns event
  semantics, workflow activation, and compact ego injection

### LLM Wiki Integration (New in v1.1.2)

- **Tool**: `pen_paper_wiki_template` with two actions:
  - `list_templates`: Scans wikis for pages tagged with `type: pen_paper_template`
  - `load_template`: Loads template metadata and generates session payload
- **Filesystem-Only Access**: No cross-plugin imports; uses vendored YAML/frontmatter parser
- **Context Safeguards**:
  - Max 20 templates per list
  - Max 500 chars preview, 3000 chars full load
  - 5-minute discovery cache with mtime invalidation
  - Namespace separation: `wiki:<wiki_name>:<template_name>`
- **Access Control**: Respects LLM Wiki agent grants
- **Graceful Degradation**: Returns clean errors when llm_wiki plugin not installed or vault not configured

### Plugin Structure

- **Activation**: File-based activation (`.toggle-1` for enabled, `.toggle-0` for disabled)
- **Configuration**: Per-project and per-agent configuration support via `default_config.yaml`
- **Settings Sections**: Agent-level settings integration
- **Install Hook**: Idempotent installation that creates runtime directories and seed files

### Deferred Features

The following features from the legacy plugin are deferred to future versions:

- **Vector Recall**: Semantic search and vector-based content retrieval
- **Context Loader**: Advanced context injection and management
- **Native Scribe Agent Profile**: the earlier in-tree scribe agent profile was
  removed; current automated documentation lives in the separate `a0_scribe`
  plugin
- **Expanded WebUI**: richer browser-based state inspection and workflow editing

## Roadmap

### Near Term

- Re-enable vector recall with proper v1.12 compatibility
- Add context loader integration
- Add a small State-DOX inspector to the Workflows Canvas
- Improve session focus visibility and stale-focus diagnostics

### v1.4.0 (Future)

- Improve WebUI diagram controls for template/session visualization
- Enhanced template management
- Workflow automation improvements
- Optional recovery UI for malformed or stale State-DOX files

## Compatibility

- **Agent Zero Version**: v1.19 current local target; designed to remain compatible with v1.12+ plugin conventions
- **Python Dependencies**: Framework-provided (simpleeval, yaml)
- **Activation Semantics**: Follows v1.12 file-based activation rules
