# Google AI Edge Gallery × Agent Zero Community — Integration Plan

Status: design proposal (2026-06-10)
Scope: resident-facing on-device ticket app → kibbutz Agent Zero server

## 1. Problem

Every resident conversation handled by the kibbutz Agent Zero server costs
~36k tokens of system prompt *per turn* (core prompts ~35k + enabled plugin
prompts: pen_paper ~205 lines, scribe, llm_wiki ~2.4k, meta_supervisor ~0.9k).
A 10-turn intake conversation ≈ 400k+ tokens of mostly-repeated system prompt.
The goal: move the *conversation* to the resident's phone and deliver only a
**complete structured ticket report** to the server.

## 2. What Google AI Edge Gallery is (breakdown)

Repo: https://github.com/google-ai-edge/gallery — Apache-2.0, Kotlin/Jetpack
Compose, Android 12+ (iOS app exists but source is closed, issue #420).
Latest release 1.0.15 (May 2026), very active (~24k stars).

| Layer | Component | Relevance to us |
|---|---|---|
| Inference | **LiteRT-LM** v0.11 (`com.google.ai.edge.litertlm`) — migrated off MediaPipe LLM Inference in v1.0.8 | Target this API if we build custom; do NOT use MediaPipe FC/RAG SDKs (superseded/deprecated) |
| Models | HF allowlist JSON (`model_allowlists/`): Gemma 4 E2B/E4B, Gemma 3n, Gemma3-1B, Qwen2.5-1.5B, **FunctionGemma-270M** finetunes | Data-driven — we can host our own allowlist; FunctionGemma 270M (0.29 GB, 6 GB RAM) is ideal for ticket form-filling |
| Function calling | LiteRT-LM Tool Use (`@Tool`/`@ToolParam` on a `ToolSet`), schema-constrained decoding; `Function_Calling_Guide.md` in repo | Native tools for "submit_ticket" if we fork |
| **MCP client** | `customtasks/agentchat` — `io.modelcontextprotocol:kotlin-sdk:0.8.0`, **StreamableHTTP only**, dynamic tool discovery, custom auth headers, per-call permission dialogs | The integration seam: point at a kibbutz FastMCP server. Same transport as `a0_lmm_router/mcp_server` (FastMCP Streamable HTTP :8095) |
| **Agent Skills** | `skills/` — `SKILL.md` + optional JS (hidden WebView, can `fetch`); loadable from **URL**, local file, or community; `SkillAllowlist.kt` | Format is compatible in spirit with our pen&paper `SKILL.md` standard — ticket skills authored in pen&paper can be published for the app |
| System prompts | `SystemPromptRepository` — per-task custom system prompts (since 1.0.14) | Replace generic chat persona with a ticket-intake persona of a few hundred tokens |
| UI tasks | `llm_chat`, `llm_prompt_lab`, `llm_ask_image`, `llm_ask_audio`, `llm_agent_chat`, + `customtasks/examplecustomtask` scaffold | Fork path: clone `examplecustomtask` into a "Kibbutz Tickets" task |
| Limits | Gemma 4 E2B: 32k context, default 4k maxTokens; 8 GB RAM (E2B) / 12 GB (E4B); 6 GB for ≤1.5B models; MCP needs routable HTTPS (Cloudflare tunnel documented) | 32k on-device context comfortably holds skill + conversation |

## 3. Target architecture

```
Resident phone (Gallery fork "Kibbutz App")
  ├─ LiteRT-LM model (per device RAM):
  │    6 GB → FunctionGemma-270M / Gemma3-1B   8 GB → Gemma 4 E2B
  ├─ Ticket skill (SKILL.md, fetched from server skill registry)
  │    → conducts the intake conversation locally, fills all fields
  └─ MCP client (StreamableHTTP + bearer header, per-resident token)
       │  tools: list_ticket_types / get_ticket_schema /
       │         submit_ticket / get_ticket_status
       ▼
Kibbutz server — new plugin `a0_tickets` (modeled on a0_lmm_router/mcp_server)
  ├─ FastMCP StreamableHTTP server (e.g. :8096)
  ├─ Ticket schemas = pen&paper workflow templates (template_registry)
  ├─ submit_ticket → creates a pen&paper session (workspace.json sections
  │    map 1:1 to ticket fields; State-DOX events for scribe)
  ├─ Skill registry endpoint: serves published SKILL.md files to the app
  │    (authored/edited via pen&paper workflows_publish flow)
  └─ Agent Zero processes tickets ASYNC, in batch — one LLM pass per
       complete report instead of a multi-turn 36k-prompt conversation
```

Token economics: intake moves from N turns × ~40k server tokens to **one**
server-side processing pass over a complete structured report. The 36k system
prompt is paid once per *ticket*, not per *turn* — and only when action is
actually needed (triage/dispatch can be rule-based for simple ticket types).

## 4. Why pen&paper is the authoring layer

- pen&paper skills already use the `SKILL.md` + YAML frontmatter standard;
  Gallery's Agent Skills use the same file convention → one authoring format.
- Ticket *types* = pen&paper workflow templates (registry + publish flow
  already exist: `workflows_create/save/publish` APIs).
- Submitted tickets land as pen&paper sessions → scribe documents them,
  llm_wiki absorbs recurring knowledge (e.g., "water outage in block C").

## 5. Phased plan

**Phase 0 — POC, zero code (days):** stock Gallery app + Gemma 4 E2B; add the
existing `a0_lmm_router` MCP server URL in Agent Chat to validate transport +
auth headers on kibbutz LAN/tunnel; hand-write one ticket skill (e.g.,
maintenance request) as a Gallery Agent Skill loaded from URL.

**Phase 1 — `a0_tickets` server plugin:** FastMCP server (copy the
`a0_lmm_router/mcp_server` pattern: auth token file, mutating-tools gating,
`router_bridge`-style module). Tools: `list_ticket_types`,
`get_ticket_schema`, `submit_ticket`, `get_ticket_status`. Storage via
pen&paper sessions. Async Agent Zero processing queue.

**Phase 2 — Gallery fork:** branded app; pre-configured MCP URL + token
provisioning; auto-allow the kibbutz server (remove per-call dialogs); skill
auto-sync from server registry (`SkillAllowlist` mechanism); per-device
default model; hide model-manager complexity; Hebrew UI strings. Requires our
own HF OAuth app for gated model downloads (`ProjectConfig.kt`).

**Phase 3 — feedback loop:** ticket status notifications (FCM is already a
Gallery dependency), `get_ticket_status` polling, resident history screen.

## 6. Risks / open questions

1. **MCP transport reachability:** Gallery docs assume a public HTTPS URL
   (Cloudflare quick tunnel). Verify whether plain-HTTP LAN URLs work on the
   kibbutz Wi-Fi before committing; if not, terminate TLS at the server or
   keep a tunnel.
2. **Per-call permission dialogs** in stock MCP client — acceptable for POC,
   must be removed in the fork (Phase 2).
3. **iOS residents** are not covered (closed source). Fallback: a minimal web
   client against the same MCP/REST endpoints, or LiteRT-LM Swift (early
   preview) later.
4. **Small-model reliability:** FunctionGemma-270M is tuned for tool calling
   but weak at open conversation — ticket skills must be tightly scripted
   (enumerated fields, one question at a time). Gemma 4 E2B where RAM allows.
5. **Auth/identity:** per-resident bearer tokens; decide issuance/rotation
   (host-helper token pattern from a0_lmm_router can be reused).
6. **Schema drift:** app-side skill version must match server-side template
   version → include `schema_version` in `submit_ticket` payload.
