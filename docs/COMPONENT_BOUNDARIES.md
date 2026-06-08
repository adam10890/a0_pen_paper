# Component Boundaries

This plugin now marks capabilities by ownership:

| Component | Scope | Home | Notes |
|-----------|-------|------|-------|
| `pen_paper` | local | Pen & Paper | Structured session/workflow state |
| State-DOX templates/helpers | local | Pen & Paper | Owns runtime `state/` files, workflow templates, and append-only event storage |
| `pen_paper_wiki_template` | bridge | Pen & Paper ↔ LLM Wiki | Read-only workflow-template discovery |
| `pen_paper_diagram` | local | Pen & Paper | Generates `.drawio` artifacts from templates/sessions/text |
| `diagrams_send_whiteboard` | bridge | Pen & Paper ↔ Whiteboard | Creates a whiteboard annotation copy from the same diagram model |
| `a0_scribe` State bridge | bridge | Scribe ↔ Pen & Paper | Scribe owns event semantics; Pen & Paper owns durable workspace storage |
| Workflows Canvas | local UI with bridges | Pen & Paper | Owns template/session editing; exposes optional diagram and whiteboard bridge actions |

## Rule

Local components keep source-of-truth state in Pen & Paper runtime storage.
Bridge components may create synchronized or derived artifacts in another
plugin, but they must not move ownership unless a separate migration path is
explicitly designed.

For the Scribe bridge, `a0_scribe` may append events and merge current state, but
it must not bypass `helpers/sessions_store.py` or store runtime state in its own
plugin directory.
