# Live Agent Test Plan — session layer (state / properties / relations / listing)

**Scope:** validating the session-layer changes against a **running Agent Zero**
(`/a0`). Everything in the repo's own suite is static and in-process; this plan
covers only what unit tests structurally cannot reach.

**Status when written:** not executed — no running agent was available. All
results below are expectations, not observations.

---

## 1. Why this document exists

The repo suite (111 tests, `verify_pen_paper_setup.py` 11/11) exercises
`helpers/sessions_store.py` by calling it directly with a temp `runtime_dir`.
That leaves four things unverified:

| Gap | Why unit tests miss it |
|---|---|
| HTTP handler behavior | Tests call the store directly; `api/*.py` needs `helpers.api` + `flask` |
| Real agent-authored content | Fixtures are hand-written; property derivation is only as good as its input |
| WebUI / Right Canvas | No browser in the suite |
| A real pre-existing deployment | Temp dirs are always fresh; back-compat is only simulated |

---

## 2. What is under test

Four additive features plus the endpoint that exposes them:

- `metadata.state` — `NORMAL` | `ARCHIVED`, derived from the directory when absent
- computed `properties` — `has_link`, `has_task_list`, `has_incomplete_tasks`,
  `has_code`, `has_execution_log`, `has_backtrack`, `title`
- typed `relations` — `REFERENCE` | `COMMENT`, validated on read and write
- `list_sessions()` — `filter` / `order_by` / `page_size` / `page_token` /
  `include_archived`
- `api/sessions_list.py` — forwards all of the above

**Baseline invariant for every tier:** a caller that passes none of the new
parameters must observe byte-identical behavior to the previous release.

---

## 3. Tier 0 — Pre-flight (blocking)

Stop if any of these fail; later tiers assume them.

| # | Step | Expected |
|---|---|---|
| 0.1 | Install/enable the plugin in `/a0` | `sessions/{active,archive}`, `config/`, `knowledge/workflows/`, `.ui/` exist under `usr/pen_and_paper/` |
| 0.2 | `python scripts/verify_pen_paper_setup.py` **from `/a0`** | `11/11 PASS` |
| 0.3 | `python -m unittest discover -s tests` from `/a0` | `111/111 OK` |
| 0.4 | `python execute.py validate` | exit 0 |

> 0.2 matters specifically because in `/a0` the real `usr.plugins.*` package
> resolves, taking a different import path than a bare clone.

---

## 4. Tier A — HTTP layer (highest risk)

This layer had **zero** coverage before the change and only request-validation
coverage now. The store↔handler round trip is still unproven.

| # | Request to `sessions_list` | Expected |
|---|---|---|
| A.1 | `{}` | `ok: true`; each session carries `state`, `properties`, `relations`, `relation_count` **and** every pre-existing key (`name`, `status`, `template`, `chat_id`, `created`, `mtime`, `etag`, `section_counts`, `is_current_chat`, `is_chat_focus`, `is_orphan`) |
| A.2 | `{}` | **no** `next_page_token` key present |
| A.3 | `{"chat_only": true, "chat_id": "<open chat>"}` | filters as before the change |
| A.4 | `{"page_size": 2}` | ≤2 sessions; `next_page_token` present when more remain |
| A.5 | feed A.4's token back with the same `page_size` | next slice; no overlap, no gap |
| A.6 | reuse A.4's token with a **different** `order_by` | `ok: false` with an explicit error (token is bound to query shape) |
| A.7 | `{"order_by": "name asc"}` / `"name desc"` | ordering flips |
| A.8 | `{"filter": {"has_incomplete_tasks": true}}` | only sessions with unchecked boxes |
| A.9 | `{"filter": {"has_lnik": true}}` (typo) | `ok: false`, explicit unknown-key error — **must not** return everything |
| A.10 | `{"filter": "state == ARCHIVED"}` (string, not object) | `ok: false`, `filter must be an object` |
| A.11 | `{"page_size": "many"}` | `ok: false`, `page_size must be an integer` |
| A.12 | `{"include_archived": true}` | archived sessions appear |
| A.13 | `{"filter": {"state": "ARCHIVED"}}` **without** `include_archived` | empty — documented precedence: `include_archived` picks directories, `filter.state` only narrows |

**A.14 — payload size.** With ~50 sessions, record the response size for `{}`
before and after this change. `properties` and `relations` are new per-session
objects. Record the number; decide afterwards whether it warrants an opt-out.

**A.15 — stale-module path.** `api/sessions_list.py` keeps a reload branch for
long-running processes holding an old module. Confirm it still triggers
correctly now that the signature has grown (e.g. hot-reload the plugin without
restarting `/a0`, then call the endpoint).

---

## 5. Tier B — Agent behavior end-to-end

The point: properties are derived from **real agent-authored content**, not
fixtures.

| # | Step | Expected |
|---|---|---|
| B.1 | Ask the agent to open a session and write findings containing a task list, a fenced code block, and a URL | session created |
| B.2 | Call `sessions_list` | `has_task_list`, `has_incomplete_tasks`, `has_code`, `has_link` all `true` |
| B.3 | Ask the agent to mark every task done | `has_task_list` stays `true`; `has_incomplete_tasks` flips to `false` |
| B.4 | Inspect `title` | picks up the agent's `#` H1 if it wrote one; otherwise equals the session name |
| B.5 | Run a workflow template so `execution_log` fills | `has_execution_log: true` |
| B.6 | Trigger a backtrack entry | `has_backtrack: true` |
| B.7 | Close a session (`pen_paper` → `close`) | `metadata.status` becomes `closed`; **`state` stays `NORMAL`** — status and state are orthogonal |

> B.7 is the most likely place for a conceptual regression: `status` (`active`
> / `closed`) and `state` (`NORMAL` / `ARCHIVED`) are deliberately independent.

---

## 6. Tier C — WebUI / Right Canvas

| # | Step | Expected |
|---|---|---|
| C.1 | Open the Workflows panel; switch Templates ↔ Live | no console errors from the new fields |
| C.2 | Live list renders | sessions listed as before; badges/focus unchanged |
| C.3 | Append an entry from the UI | `etag` conflict handling still works; a stale `etag` still returns `error: stale` |
| C.4 | Follow-agent focus | `.ui/focus.json` still drives highlighting |

The Canvas currently reads none of the new fields, so C.1–C.4 are regression
checks, not feature checks.

---

## 7. Tier D — Back-compat on a real deployment

Cannot be faked in a temp directory. **Take a `usr/pen_and_paper/` created
before this change.**

| # | Step | Expected |
|---|---|---|
| D.1 | Record `mtime` + sha256 of every `workspace.json` | baseline |
| D.2 | Call `sessions_list` with `{}` | all sessions listed; `state: "NORMAL"` derived from directory |
| D.3 | Re-check `mtime` + sha256 | **unchanged** — reads must never rewrite workspaces |
| D.4 | Confirm no `state`/`relations` keys were backfilled on disk | absent |
| D.5 | Move a session into `sessions/archive/` by hand | absent from default listing; present with `include_archived: true`, `state: "ARCHIVED"` |
| D.6 | Old flat `config.json` install | `_normalize_legacy()` still maps it; no runtime break |

---

## 8. Tier E — Deliberate corruption

| # | Step | Expected |
|---|---|---|
| E.1 | Hand-edit a `workspace.json` to `"relations": ["garbage", {"type":"BOGUS","target":"x"}, null, {"type":"REFERENCE","target":"real"}]` | session still lists; `relation_count: 1`; only the valid entry returned |
| E.2 | `{"filter": {"relation_target": "x"}}` | no match — invalid-type entries must not satisfy the filter |
| E.3 | Re-read the file after E.1/E.2 | unchanged on disk — the read path filters, it does not repair |
| E.4 | Add a self-relation (`target` == own name) | dropped on read |
| E.5 | Truncate a `workspace.json` to invalid JSON | that session is skipped; **other sessions still list** |
| E.6 | Make `sessions/active/` unreadable (permissions) | explicit error envelope, not a 500 stack trace |

---

## 9. Exit criteria

- Tier 0 fully green.
- Tier A: A.1–A.13 pass; A.14 recorded as a number; A.15 confirmed.
- Tier B: B.1–B.7 pass, **B.7 especially**.
- Tier C: no console errors, no Live-view regression.
- Tier D: D.3 is non-negotiable — reads must not mutate existing workspaces.
- Tier E: no tier-E case takes down the whole listing.

Record failures as: request → expected → actual → `workspace.json` excerpt.

---

## 10. Known limitations of this plan

- No load/perf testing beyond the single A.14 measurement.
- No concurrency testing (two writers appending to one session).
- Property derivation is regex-based; content in unusual Markdown dialects may
  classify differently. B.2–B.4 sample real content but do not fuzz it.
- Tier C is manual; there is no browser automation in this repo.
