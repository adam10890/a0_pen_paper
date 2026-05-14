# Session Management

Pen & Paper sessions map directly to workspaces, which are managed via the `pen_paper` tool.

## Session Lifecycle

### 1. Creation (`action: "create"`)

Initiate a new workspace at the start of any complex task. Pick a descriptive name representing the task.

### 2. Interaction (`action: "write"`, `action: "read"`)

Throughout the task, incrementally add information to the appropriate sections:

- `findings`: Newly discovered facts (e.g., "File X uses TypeScript").
- `results`: Execution outcomes (e.g., "Tests passed").
- `insights`: Higher-level understandings.
- `decisions`: Architectural or logical choices made.
- `backtrack`: Items to revisit later.

### 3. Closure (`action: "close"`)

Always close a workspace when complete. This step triggers the vectorizer to index the session, making the knowledge available for future tasks.

## Ephemeral vs Persistent Modes

- **Persistent:** The default behavior. Sessions are saved to disk, tracked as markdown files, and vectorized upon closure. They remain accessible.
- **Ephemeral:** Used for transient tasks. In this mode, the session acts as temporary scratchpad. When closed, the session is vectorized (for context) and then deleted to prevent clutter.

