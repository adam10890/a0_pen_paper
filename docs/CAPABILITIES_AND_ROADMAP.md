# Pen & Paper Plugin - Capabilities and Roadmap

## Current Capabilities (v1.1.2)

### Core Features

- **Structured Workspace Management**: Create, update, read, list, and close structured thinking workspaces
- **Template System**: Pre-configured templates for structured working sessions with phases (Plan, Work, Review)
- **Local Sessions**: Session storage in `usr/pen_and_paper/sessions/` with active and archive separation
- **Runtime Configuration**: Install-safe runtime storage in `usr/pen_and_paper/` with seed files
- **Template Registry**: JSON-based template registry with triggers and workflow hooks
- **Multilingual Support**: Template descriptions in English and Hebrew
- **LLM Wiki Integration**: Read-only discovery and loading of wiki pages tagged as Pen & Paper templates from the LLM Wiki SharedBrain vault

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

### Deferred Features (Not Included in v1.1.2)

The following features from the legacy plugin are deferred to future versions:

- **Vector Recall**: Semantic search and vector-based content retrieval
- **Context Loader**: Advanced context injection and management
- **Scribe**: Automated documentation generation
- **WebUI**: Browser-based interface for workspace management

## Roadmap

### v1.2.0 (Planned)

- Re-enable vector recall with proper v1.12 compatibility
- Add context loader integration
- Implement Scribe for automated documentation

### v1.3.0 (Future)

- Add WebUI for workspace visualization
- Enhanced template management
- Workflow automation improvements

## Compatibility

- **Agent Zero Version**: v1.12+
- **Python Dependencies**: Framework-provided (simpleeval, yaml)
- **Activation Semantics**: Follows v1.12 file-based activation rules
