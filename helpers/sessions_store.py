"""
Active Pen & Paper session storage for Live Session Canvas view.
Reads/writes workspace.json under runtime sessions/active.
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from usr.plugins.a0_pen_paper.tools._config import load_plugin_config, runtime_base

VALID_SECTIONS = [
    "findings",
    "results",
    "insights",
    "notes",
    "decisions",
    "backtrack",
    "execution_log",
]

_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]+$")

# Runtime location for UI-published State-DOX workflow templates, relative to the
# Pen & Paper runtime base. Single source of truth — workflows_store.state_dox_dir()
# (PR1b) reuses this constant.
STATE_DOX_REL = "knowledge/workflows/state_dox"

# Valid values for the `metadata.state` field on a session workspace (inspired by
# usememos/memos). This is ORTHOGONAL to `metadata.status` (active|closed, which
# tracks work-lifecycle): `state` tracks whether the session is archived. When the
# field is absent (pre-existing workspace.json files), it is DERIVED from the
# directory the file was found in — see _resolve_workspace_state().
STATE_NORMAL = "NORMAL"
STATE_ARCHIVED = "ARCHIVED"

# Valid values for the `type` field of an entry in the `relations` array on a
# session workspace (inspired by usememos/memos' MemoRelation.Type). `relations`
# is stored as a top-level `["relations"]` key on the workspace — NOT under
# `metadata`, and NOT one of VALID_SECTIONS (it is a typed link graph between
# sessions, not a content section). REFERENCE mirrors memos' "this session
# references/relates to another"; COMMENT mirrors "this session comments on
# another" (e.g. a debugging session commenting on the solution session it
# debugged). A session may not relate to itself — see _validate_relation().
RELATION_REFERENCE = "REFERENCE"
RELATION_COMMENT = "COMMENT"
VALID_RELATION_TYPES = (RELATION_REFERENCE, RELATION_COMMENT)

# Regexes backing the computed `properties` exposed by list_sessions() (inspired by
# usememos/memos' Property submessage: has_link, has_task_list, has_code,
# has_incomplete_tasks, title). Compiled once at module load — list_sessions() runs
# these per session inside a directory scan, so recompiling per call would be waste.
_LINK_RE = re.compile(r"https?://\S+|\[[^\]]*\]\([^)]+\)")
_TASK_RE = re.compile(r"^[ \t]*-\s*\[[ xX]\]", re.MULTILINE)
_UNCHECKED_TASK_RE = re.compile(r"^[ \t]*-\s*\[ \]", re.MULTILINE)
_CODE_FENCE_RE = re.compile(r"```")
_H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)

DEFAULT_SESSION_STATE: dict[str, Any] = {
    "session": {
        "goal": "",
        "status": "active",
        "updated_by": "scribe",
        "last_event_id": None,
    },
    "working_set": {
        "current_focus": "",
        "next_action": "",
        "open_questions": [],
    },
    "active_workflows": [],
    "tags": {
        "domains": [],
        "modes": [],
    },
}


def _abs_runtime(cfg: dict[str, Any] | None = None) -> Path:
    base = runtime_base(cfg or load_plugin_config())
    path = Path(base)
    if path.is_absolute():
        return path
    plugin_dir = Path(__file__).resolve().parents[1]
    live_agent_root = None
    if plugin_dir.parent.name == "plugins" and plugin_dir.parent.parent.name == "usr":
        live_agent_root = plugin_dir.parent.parent.parent
    try:
        from helpers import files

        if live_agent_root is not None:
            return Path(files.get_abs_path(base))
    except Exception:
        pass
    return (live_agent_root or plugin_dir) / path


def sessions_dir(cfg: dict[str, Any] | None = None) -> Path:
    return _abs_runtime(cfg) / "sessions" / "active"


def archive_dir(cfg: dict[str, Any] | None = None) -> Path:
    return _abs_runtime(cfg) / "sessions" / "archive"


def focus_path(cfg: dict[str, Any] | None = None) -> Path:
    return _abs_runtime(cfg) / ".ui" / "focus.json"


def _safe_workspace_name(name: str) -> str:
    if not name or not _NAME_RE.match(name):
        raise ValueError("Invalid workspace name")
    return name


def _workspace_file(name: str, cfg: dict[str, Any] | None = None) -> Path:
    return sessions_dir(cfg) / _safe_workspace_name(name) / "workspace.json"


def state_dir(name: str, cfg: dict[str, Any] | None = None) -> Path:
    return sessions_dir(cfg) / _safe_workspace_name(name) / "state"


def _resolve_workspace_state(meta: dict[str, Any], dir_state: str) -> str:
    """Resolve a workspace's archival state.

    `metadata.state` is authoritative when present and valid; otherwise falls
    back to `dir_state` (derived from the directory the workspace was found
    in). This keeps old workspace.json files — which have no `state` field —
    working with zero migration.
    """
    explicit = meta.get("state")
    if explicit in (STATE_NORMAL, STATE_ARCHIVED):
        return explicit
    return dir_state


def _find_workspace_file(
    name: str, cfg: dict[str, Any] | None = None
) -> tuple[Path, str]:
    """Locate a workspace file by name, checking active then archive.

    Returns (path, dir_state) where dir_state is the directory-derived
    fallback state for that location. If the workspace exists in neither
    directory, returns the active-dir path (which will not exist) so callers
    get a consistent FileNotFoundError-style path to report.
    """
    safe = _safe_workspace_name(name)
    for directory, dir_state in (
        (sessions_dir(cfg), STATE_NORMAL),
        (archive_dir(cfg), STATE_ARCHIVED),
    ):
        candidate = directory / safe / "workspace.json"
        if candidate.exists():
            return candidate, dir_state
    return sessions_dir(cfg) / safe / "workspace.json", STATE_NORMAL


def workflow_templates_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "workflow_state_templates"


def workflow_template_dirs(cfg: dict[str, Any] | None = None) -> list[Path]:
    """State-DOX template source dirs in merge-precedence order: shipped (built-ins)
    first, then runtime (UI-published). Returns only dirs that exist.

    Shipped is iterated first so it wins on an id/filename clash (copy-if-absent
    in ensure_state_files; first-seen-wins in list_state_dox_templates)."""
    dirs: list[Path] = []
    shipped = workflow_templates_dir()
    if shipped.exists():
        dirs.append(shipped)
    runtime = _abs_runtime(cfg) / STATE_DOX_REL
    if runtime.exists():
        dirs.append(runtime)
    return dirs


def _normalize_state_dox_row(
    data: Any, source: str, stem: str
) -> dict[str, Any] | None:
    if not isinstance(data, dict):
        return None
    wf = data.get("workflow") if isinstance(data.get("workflow"), dict) else data
    scribe = data.get("scribe") if isinstance(data.get("scribe"), dict) else data
    wf_id = str(wf.get("id") or wf.get("name") or data.get("id") or data.get("name") or stem)
    raw_tags = wf.get("activation_tags")
    if raw_tags is None:
        raw_tags = data.get("activation_tags")
    if isinstance(raw_tags, list):
        tags = [str(t) for t in raw_tags]
    elif isinstance(raw_tags, str):
        tags = [t.strip() for t in re.split(r"[\s,;]+", raw_tags) if t.strip()]
    else:
        tags = []
    skill = scribe.get("skill") or data.get("skill") or data.get("scribe_skill")
    return {
        "id": wf_id,
        "title": str(wf.get("title") or data.get("description") or wf_id),
        "activation_tags": tags,
        "skill": str(skill) if skill else None,
        "mode": str(scribe.get("mode") or "workflow"),
        "source": source,
        "file": f"{wf_id}.yaml",
    }


def list_state_dox_templates(cfg: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Normalized State-DOX workflow templates (shipped + runtime, shipped wins on
    id clash). Stable cross-plugin contract consumed by a0_scribe; returns plain
    JSON-serializable dicts. NEVER raises — skips malformed files, [] on failure."""
    seen: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    try:
        dirs = workflow_template_dirs(cfg)
        shipped = workflow_templates_dir()
    except Exception:
        return []
    for directory in dirs:
        source = "shipped" if directory == shipped else "runtime"
        try:
            paths = sorted(directory.glob("*.yaml"))
        except Exception:
            continue
        for path in paths:
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            row = _normalize_state_dox_row(data, source, path.stem)
            if row is None or row["id"] in seen:  # earlier dir (shipped) wins
                continue
            seen[row["id"]] = row
            order.append(row["id"])
    return [seen[wf_id] for wf_id in order]


def file_etag(path: Path) -> str:
    if not path.exists():
        return ""
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest()[:16]


def _section_text(entries: list) -> str:
    parts: list[str] = []
    for entry in entries:
        if isinstance(entry, dict):
            content = entry.get("content", "")
            if content:
                parts.append(str(content))
        elif entry:
            parts.append(str(entry))
    return "\n\n---\n\n".join(parts)


def _compute_session_properties(workspace: dict[str, Any], name: str) -> dict[str, Any]:
    """Derive cheap, queryable facts from a session's content (inspired by
    usememos/memos' Property submessage), so a client/agent can triage a session
    list WITHOUT opening and parsing every record.

    Flattens all section entries into ONE text blob and computes every property
    from that single pass — no re-reading or re-flattening per property. Never
    raises: any malformed section (missing, non-list, non-string entries) just
    yields the all-false/name-fallback default instead of breaking the session's
    listing (list_sessions()'s per-session try/except stays for OTHER failures;
    this function should never be the one it has to catch).
    """
    default: dict[str, Any] = {
        "has_link": False,
        "has_task_list": False,
        "has_incomplete_tasks": False,
        "has_code": False,
        "has_execution_log": False,
        "has_backtrack": False,
        "title": name,
    }
    try:
        parts: list[str] = []
        for sec in VALID_SECTIONS:
            entries = workspace.get(sec)
            if isinstance(entries, list):
                text = _section_text(entries)
                if text:
                    parts.append(text)
        combined = "\n\n---\n\n".join(parts)

        exec_entries = workspace.get("execution_log")
        backtrack_entries = workspace.get("backtrack")

        h1_match = _H1_RE.search(combined)
        title = h1_match.group(1).strip() if h1_match else ""

        return {
            "has_link": bool(_LINK_RE.search(combined)),
            "has_task_list": bool(_TASK_RE.search(combined)),
            "has_incomplete_tasks": bool(_UNCHECKED_TASK_RE.search(combined)),
            "has_code": bool(_CODE_FENCE_RE.search(combined)),
            "has_execution_log": isinstance(exec_entries, list) and len(exec_entries) > 0,
            "has_backtrack": isinstance(backtrack_entries, list) and len(backtrack_entries) > 0,
            "title": title or name,
        }
    except Exception:
        return default


def _read_yaml(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return default if data is None else data


def _write_yaml(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def _deep_merge(base: Any, patch: Any) -> Any:
    if isinstance(base, dict) and isinstance(patch, dict):
        out = dict(base)
        for key, value in patch.items():
            out[key] = _deep_merge(out.get(key), value)
        return out
    return patch


def _session_sort_key(item: dict[str, Any]) -> tuple:
    return (
        0 if item.get("is_chat_focus") else 1,
        0 if item.get("is_current_chat") else 1,
        -float(item.get("mtime") or 0),
    )


# --- list_sessions() filter / order_by / pagination (inspired by usememos/memos'
# ListMemosRequest: page_size, page_token, order_by, filter) -------------------
#
# Deliberately NOT a CEL (Common Expression Language) implementation: a full
# expression grammar is a large parsing/attack/maintenance surface for a feature
# that only ever needs a handful of AND-ed equality/substring/boolean checks.
# Instead `filter` is a small structured dict; see _FILTER_KEYS below for the
# closed set of supported keys. An unknown key is a hard error (see
# _validate_filter) rather than being silently ignored, since silently ignoring
# a typo'd filter key would return the wrong sessions with no indication why.

PAGE_SIZE_MAX = 1000

# Boolean computed properties from `properties` (9233c50) that may be filtered on.
_FILTER_PROPERTY_KEYS = frozenset(
    {
        "has_link",
        "has_task_list",
        "has_incomplete_tasks",
        "has_code",
        "has_execution_log",
        "has_backtrack",
    }
)

# Full closed set of keys accepted by the `filter` dict.
_FILTER_KEYS = _FILTER_PROPERTY_KEYS | {
    "state",
    "status",
    "template",
    "chat_id",
    "name_contains",
    "has_relations",
    "relation_target",
}

# order_by fields (1d7a346/9233c50/313b73d expose "mtime", "created", "name" on
# every session dict already). Each maps to a sort key function; direction is an
# optional trailing " asc"/" desc" token (SQL-style: ascending is the default
# when no direction is given).
_ORDER_BY_FIELD_KEYS: dict[str, Any] = {
    "mtime": lambda s: float(s.get("mtime") or 0),
    "created": lambda s: s.get("created") or "",
    "name": lambda s: (s.get("name") or "").lower(),
}


def _validate_filter(filter: dict[str, Any] | None) -> dict[str, Any]:
    """Validate a structured `filter` dict, raising on anything unsupported.

    Returns {} for None (no-op, matches pre-filter behavior exactly).
    """
    if filter is None:
        return {}
    if not isinstance(filter, dict):
        raise ValueError("filter must be a dict")
    unknown = sorted(set(filter) - _FILTER_KEYS)
    if unknown:
        raise ValueError(
            f"Unknown filter key(s): {unknown}. Supported keys: {sorted(_FILTER_KEYS)}"
        )
    return filter


def _session_matches_filter(session: dict[str, Any], filter: dict[str, Any]) -> bool:
    """AND together every key present in `filter` against one session dict."""
    if "state" in filter and session.get("state") != filter["state"]:
        return False
    if "status" in filter and session.get("status") != filter["status"]:
        return False
    if "template" in filter and session.get("template") != filter["template"]:
        return False
    if "chat_id" in filter and session.get("chat_id") != filter["chat_id"]:
        return False
    if "name_contains" in filter:
        needle = str(filter["name_contains"]).lower()
        if needle not in (session.get("name") or "").lower():
            return False
    props = session.get("properties") or {}
    for key in _FILTER_PROPERTY_KEYS:
        if key in filter and bool(props.get(key)) != bool(filter[key]):
            return False
    if "has_relations" in filter:
        has_rel = (session.get("relation_count") or 0) > 0
        if has_rel != bool(filter["has_relations"]):
            return False
    if "relation_target" in filter:
        target = filter["relation_target"]
        relations = session.get("relations") or []
        if not any(isinstance(r, dict) and r.get("target") == target for r in relations):
            return False
    return True


def _validate_page_size(page_size: int | None) -> int | None:
    """Validate `page_size`. None means "no pagination" (unchanged behavior).

    Non-positive values are rejected outright. Values over PAGE_SIZE_MAX are
    silently clamped down to PAGE_SIZE_MAX (matching memos' own "default 50,
    maximum 1000" convention of capping rather than erroring — a client asking
    for "as many as possible" should get the max page, not a hard failure).
    """
    if page_size is None:
        return None
    if isinstance(page_size, bool) or not isinstance(page_size, int):
        raise ValueError("page_size must be an int")
    if page_size <= 0:
        raise ValueError(f"page_size must be positive, got {page_size}")
    return min(page_size, PAGE_SIZE_MAX)


def _parse_order_by(order_by: str) -> tuple[Any, bool]:
    """Parse an `order_by` string into (key_fn, reverse) for list.sort().

    Accepts "<field>" or "<field> asc|desc" for field in _ORDER_BY_FIELD_KEYS.
    Direction defaults to ascending when omitted (SQL ORDER BY convention).
    Anything else raises ValueError with a clear message.
    """
    if not isinstance(order_by, str) or not order_by.strip():
        raise ValueError(f"Invalid order_by: {order_by!r}")
    tokens = order_by.strip().split()
    if len(tokens) > 2:
        raise ValueError(f"Invalid order_by: {order_by!r}")
    field = tokens[0]
    if field not in _ORDER_BY_FIELD_KEYS:
        raise ValueError(
            f"Invalid order_by field: {field!r}. Supported: {sorted(_ORDER_BY_FIELD_KEYS)}"
        )
    reverse = False
    if len(tokens) == 2:
        direction = tokens[1].lower()
        if direction == "desc":
            reverse = True
        elif direction == "asc":
            reverse = False
        else:
            raise ValueError(f"Invalid order_by direction: {tokens[1]!r}. Use 'asc' or 'desc'.")
    return _ORDER_BY_FIELD_KEYS[field], reverse


def _pagination_signature(
    *,
    order_by: str | None,
    filter: dict[str, Any],
    chat_only: bool,
    chat_id: str | None,
    include_archived: bool,
) -> str:
    """A short hash binding a page_token to the query shape that minted it.

    This is what makes an invalid/stale page_token (e.g. one issued for a
    different filter/order_by) fail loudly instead of silently returning an
    offset into a differently-shaped list (which would look like pages
    overlapping or skipping items).
    """
    payload = json.dumps(
        {
            "order_by": order_by,
            "filter": filter,
            "chat_only": bool(chat_only),
            "chat_id": chat_id,
            "include_archived": bool(include_archived),
        },
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _encode_page_token(offset: int, sig: str) -> str:
    payload = json.dumps({"offset": offset, "sig": sig})
    raw = base64.urlsafe_b64encode(payload.encode("utf-8"))
    return raw.decode("ascii").rstrip("=")


def _decode_page_token(page_token: str, sig: str) -> int:
    """Decode an opaque page_token minted by _encode_page_token().

    Raises ValueError (not IndexError/KeyError/a crash) on malformed input,
    and on a token minted for a different filter/order_by/chat scope — a
    silent fallback there would produce a page that quietly skips or repeats
    items.
    """
    try:
        padded = page_token + "=" * (-len(page_token) % 4)
        raw = base64.urlsafe_b64decode(padded.encode("ascii"))
        data = json.loads(raw.decode("utf-8"))
        offset = data["offset"]
        token_sig = data["sig"]
    except Exception as exc:
        raise ValueError(f"Invalid page_token: {page_token!r}") from exc
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise ValueError(f"Invalid page_token: {page_token!r}")
    if token_sig != sig:
        raise ValueError(
            "page_token does not match the current filter/order_by/chat_only/"
            "chat_id/include_archived parameters; request a fresh listing"
        )
    return offset


def list_sessions(
    cfg: dict[str, Any] | None = None,
    chat_id: str | None = None,
    *,
    chat_only: bool = False,
    include_archived: bool = False,
    page_size: int | None = None,
    page_token: str | None = None,
    order_by: str | None = None,
    filter: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """List session workspaces.

    All of page_size/page_token/order_by/filter are optional and keyword-only;
    omitting all four (the pre-existing call shape) reproduces the exact
    pre-existing behavior byte-for-byte — this is the single most important
    contract of this function and is covered explicitly in
    tests/test_session_listing.py.

    include_archived vs filter={"state": ...} precedence: include_archived
    controls which DIRECTORIES are scanned from disk (sessions/active only, or
    sessions/active + sessions/archive). filter={"state": ...} then narrows
    the already-scanned set — it never WIDENS scope. So
    filter={"state": "ARCHIVED"} with the default include_archived=False
    returns an empty result (archived sessions were never scanned); seeing
    ARCHIVED sessions via the state filter requires include_archived=True too.

    order_by: None keeps the existing _session_sort_key() ordering (chat-focus
    first, current-chat first, then mtime desc) exactly. Otherwise one of
    "mtime", "created", "name", optionally suffixed with " asc"/" desc"
    (default direction is ascending, SQL ORDER BY convention).

    filter: a structured (NOT CEL) dict of AND-ed conditions; see
    _FILTER_KEYS for the supported keys. An unknown key raises ValueError.

    page_size/page_token: page_size caps a page at PAGE_SIZE_MAX (=1000,
    matching memos); non-positive values raise, values above the max are
    clamped. page_token is an opaque, base64-encoded continuation token
    bound to the exact filter/order_by/chat scope that minted it — reusing
    it with a different filter/order_by/chat_id/chat_only/include_archived
    raises rather than silently returning a mismatched page. Filtering and
    ordering are always applied BEFORE pagination, so pages partition a
    stable, non-overlapping sequence.
    """
    filt = _validate_filter(filter)
    page_size_eff = _validate_page_size(page_size)
    if page_token is not None and page_size_eff is None:
        raise ValueError("page_token requires page_size")
    if order_by is not None:
        order_key_fn, order_reverse = _parse_order_by(order_by)
    else:
        order_key_fn, order_reverse = None, False

    base = sessions_dir(cfg)
    base.mkdir(parents=True, exist_ok=True)
    scan_dirs = [(base, STATE_NORMAL)]
    if include_archived:
        archive = archive_dir(cfg)
        archive.mkdir(parents=True, exist_ok=True)
        scan_dirs.append((archive, STATE_ARCHIVED))
    focus = read_focus(chat_id, cfg) if chat_id else {}
    focus_workspace = focus.get("workspace") if isinstance(focus, dict) else None
    out: list[dict[str, Any]] = []
    for scan_dir, dir_state in scan_dirs:
        for ws_path in scan_dir.iterdir():
            if not ws_path.is_dir():
                continue
            wf = ws_path / "workspace.json"
            if not wf.exists():
                continue
            try:
                workspace = json.loads(wf.read_text(encoding="utf-8"))
                meta = workspace.get("metadata") or {}
                name = meta.get("name", ws_path.name)
                session_chat = meta.get("chat_id")
                counts = {
                    s: len(workspace.get(s) or [])
                    for s in VALID_SECTIONS
                    if isinstance(workspace.get(s), list)
                }
                is_current_chat = bool(chat_id and session_chat == chat_id)
                is_chat_focus = bool(focus_workspace and name == focus_workspace)
                is_orphan = session_chat is None
                raw_relations = workspace.get("relations")
                relations = raw_relations if isinstance(raw_relations, list) else []
                out.append(
                    {
                        "name": name,
                        "status": meta.get("status", "unknown"),
                        "state": _resolve_workspace_state(meta, dir_state),
                        "template": meta.get("template"),
                        "chat_id": session_chat,
                        "created": (meta.get("created_at") or "")[:16],
                        "mtime": wf.stat().st_mtime,
                        "etag": file_etag(wf),
                        "section_counts": counts,
                        "properties": _compute_session_properties(workspace, name),
                        "relations": relations,
                        "relation_count": len(relations),
                        "is_current_chat": is_current_chat,
                        "is_chat_focus": is_chat_focus,
                        "is_orphan": is_orphan,
                    }
                )
            except Exception:
                continue
    if order_key_fn is None:
        out.sort(key=_session_sort_key)
    else:
        out.sort(key=order_key_fn, reverse=order_reverse)
    visible = out
    if chat_id and chat_only:
        visible = [
            s
            for s in out
            if s.get("is_current_chat")
            or (s.get("is_chat_focus") and focus_workspace == s.get("name"))
        ]
    filtered = visible if not filt else [s for s in visible if _session_matches_filter(s, filt)]

    result: dict[str, Any] = {
        "sessions": filtered,
        "total_count": len(out),
        "visible_count": len(filtered),
        "current_chat_id": chat_id,
        "focus": focus,
    }
    if page_size_eff is not None:
        sig = _pagination_signature(
            order_by=order_by,
            filter=filt,
            chat_only=chat_only,
            chat_id=chat_id,
            include_archived=include_archived,
        )
        offset = 0 if page_token is None else _decode_page_token(page_token, sig)
        page_items = filtered[offset : offset + page_size_eff]
        next_offset = offset + page_size_eff
        next_token = _encode_page_token(next_offset, sig) if next_offset < len(filtered) else None
        result["sessions"] = page_items
        result["next_page_token"] = next_token
    return result


def get_workspace_state(name: str, *, cfg: dict[str, Any] | None = None) -> str:
    """Read a session's archival state (`STATE_NORMAL` or `STATE_ARCHIVED`).

    Looks in `sessions/active` then `sessions/archive`. Honors an explicit
    `metadata.state` when present; otherwise derives it from whichever
    directory the workspace was found in (back-compat for old workspaces).
    """
    wf, dir_state = _find_workspace_file(name, cfg)
    if not wf.exists():
        raise FileNotFoundError(f"Workspace '{name}' not found")
    workspace = json.loads(wf.read_text(encoding="utf-8"))
    meta = workspace.get("metadata") or {}
    return _resolve_workspace_state(meta, dir_state)


def set_workspace_state(
    name: str, state: str, *, cfg: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Set an explicit `metadata.state` on a session workspace.

    This only writes the field on the workspace.json in whichever directory
    it currently lives in — it does NOT move the file between
    sessions/active and sessions/archive. Directory layout is unchanged by
    this helper; `state` is an additive, orthogonal field.
    """
    if state not in (STATE_NORMAL, STATE_ARCHIVED):
        raise ValueError(f"Invalid state: {state}")
    wf, _ = _find_workspace_file(name, cfg)
    if not wf.exists():
        raise FileNotFoundError(f"Workspace '{name}' not found")
    workspace = json.loads(wf.read_text(encoding="utf-8"))
    meta = workspace.setdefault("metadata", {})
    meta["state"] = state
    wf.write_text(json.dumps(workspace, indent=2), encoding="utf-8")
    return {"ok": True, "name": name, "state": state}


def _validate_relation(entry: Any, *, self_name: str) -> dict[str, Any]:
    """Validate and normalize a single `relations` entry.

    Rejects: a non-dict entry, an unknown `type` (must be one of
    VALID_RELATION_TYPES), an empty/non-string `target`, and a self-relation
    (`target == self_name` — a session cannot relate to itself; this is a
    deliberate choice, not an oversight, to keep the link graph acyclic at the
    trivial single-node case). Deliberately does NOT check that `target` refers
    to an existing session: a relation may point at a session that does not
    exist yet or was later deleted, and enforcing existence here would make
    session ordering/creation brittle.
    """
    if not isinstance(entry, dict):
        raise ValueError(f"Invalid relation entry: expected a dict, got {type(entry).__name__}")
    rel_type = entry.get("type")
    if rel_type not in VALID_RELATION_TYPES:
        raise ValueError(f"Invalid relation type: {rel_type!r}")
    target = entry.get("target")
    if not isinstance(target, str) or not target.strip():
        raise ValueError("Relation target must be a non-empty string")
    if target == self_name:
        raise ValueError(f"A session cannot have a relation to itself: {self_name!r}")
    return {"type": rel_type, "target": target}


def list_relations(name: str, *, cfg: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Read the `relations` array of a session workspace.

    Returns `[]` when the workspace has no `relations` key — true for every
    pre-existing workspace.json file — without raising and without rewriting
    the file to backfill an empty array. Uses _find_workspace_file() (checks
    sessions/active then sessions/archive) so relations work for archived
    sessions too.
    """
    wf, _ = _find_workspace_file(name, cfg)
    if not wf.exists():
        raise FileNotFoundError(f"Workspace '{name}' not found")
    workspace = json.loads(wf.read_text(encoding="utf-8"))
    relations = workspace.get("relations")
    return relations if isinstance(relations, list) else []


def set_relations(
    name: str, relations: list[dict[str, Any]], *, cfg: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Replace the whole `relations` array on a session workspace (memos'
    `SetMemoRelations` semantics — this REPLACES the array, it does not append
    to it). Every entry is validated (see _validate_relation()) before
    anything is written, so a bad entry leaves the stored array untouched.
    """
    if not isinstance(relations, list):
        raise ValueError("relations must be a list")
    wf, _ = _find_workspace_file(name, cfg)
    if not wf.exists():
        raise FileNotFoundError(f"Workspace '{name}' not found")
    normalized = [_validate_relation(entry, self_name=name) for entry in relations]
    workspace = json.loads(wf.read_text(encoding="utf-8"))
    workspace["relations"] = normalized
    wf.write_text(json.dumps(workspace, indent=2), encoding="utf-8")
    return {"ok": True, "name": name, "relations": normalized}


def add_relation(
    name: str, target: str, rel_type: str, *, cfg: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Append a single relation to a session workspace, idempotently.

    Adding the same (type, target) pair twice is a no-op — the stored array
    never gets a duplicate entry. Validates the new entry the same way
    set_relations() does (see _validate_relation()); does not touch or
    re-validate any pre-existing entries in the array.
    """
    entry = _validate_relation({"type": rel_type, "target": target}, self_name=name)
    wf, _ = _find_workspace_file(name, cfg)
    if not wf.exists():
        raise FileNotFoundError(f"Workspace '{name}' not found")
    workspace = json.loads(wf.read_text(encoding="utf-8"))
    existing = workspace.get("relations")
    current = list(existing) if isinstance(existing, list) else []
    already_present = any(
        isinstance(r, dict) and r.get("type") == entry["type"] and r.get("target") == entry["target"]
        for r in current
    )
    if not already_present:
        current.append(entry)
    workspace["relations"] = current
    wf.write_text(json.dumps(workspace, indent=2), encoding="utf-8")
    return {"ok": True, "name": name, "relations": current}


def get_session(
    name: str,
    section: str | None = None,
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    wf = _workspace_file(name, cfg)
    if not wf.exists():
        raise FileNotFoundError(f"Workspace '{name}' not found")
    workspace = json.loads(wf.read_text(encoding="utf-8"))
    meta = workspace.get("metadata") or {}
    etag = file_etag(wf)
    result: dict[str, Any] = {
        "name": meta.get("name", name),
        "metadata": meta,
        "etag": etag,
        "sections": VALID_SECTIONS,
    }
    if section:
        if section not in VALID_SECTIONS:
            raise ValueError(f"Invalid section: {section}")
        entries = workspace.get(section) or []
        result["section"] = section
        result["entries"] = entries
        result["text"] = _section_text(entries if isinstance(entries, list) else [])
        result["entry_count"] = len(entries) if isinstance(entries, list) else 0
    else:
        result["section_counts"] = {
            s: len(workspace.get(s) or []) for s in VALID_SECTIONS
        }
    return result


def read_focus(chat_id: str | None = None, cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    path = focus_path(cfg)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    if chat_id:
        by_chat = data.get("by_chat")
        if isinstance(by_chat, dict) and chat_id in by_chat:
            return by_chat[chat_id]
        if data.get("chat_id") == chat_id:
            return data
        return {}
    return data


def write_focus(
    *,
    workspace: str,
    section: str | None = None,
    action: str = "",
    chat_id: str | None = None,
    entry_index: int | None = None,
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    path = focus_path(cfg)
    path.parent.mkdir(parents=True, exist_ok=True)
    wf = _workspace_file(workspace, cfg)
    payload: dict[str, Any] = {
        "workspace": workspace,
        "section": section or "notes",
        "action": action,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "workspace_mtime": wf.stat().st_mtime if wf.exists() else 0,
    }
    if chat_id:
        payload["chat_id"] = chat_id
    if entry_index is not None:
        payload["entry_index"] = entry_index
    existing: dict[str, Any] = {}
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            existing = {}
    if chat_id:
        by_chat = existing.get("by_chat")
        if not isinstance(by_chat, dict):
            by_chat = {}
        by_chat[chat_id] = payload
        existing["by_chat"] = by_chat
    existing.update(payload)
    path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    return payload


def ensure_session(
    name: str,
    chat_id: str | None = None,
    *,
    template: str | None = None,
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create an active workspace if it does not exist. Idempotent.

    Used by background writers (e.g. the a0_scribe super-ego) that need a
    session to append to without going through the pen_paper tool. Returns
    {"ok": True, "created": <bool>, "name": <safe name>}.
    """
    safe = _safe_workspace_name(name)
    wf = _workspace_file(safe, cfg)
    if wf.exists():
        return {"ok": True, "created": False, "name": safe}
    wf.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    workspace: dict[str, Any] = {
        "metadata": {
            "name": safe,
            "status": "active",
            "template": template,
            "chat_id": chat_id,
            "created_at": now,
            "created_by": "scribe",
        },
    }
    for sec in VALID_SECTIONS:
        workspace[sec] = []
    wf.write_text(json.dumps(workspace, indent=2), encoding="utf-8")
    return {"ok": True, "created": True, "name": safe}


def append_section(
    name: str,
    section: str,
    content: str,
    etag: str,
    *,
    author: str = "user",
    source: str = "ui",
    agent: str | None = None,
    metadata_patch: dict[str, Any] | None = None,
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Append an entry to a workspace section.

    `agent` is included in the written entry when provided (tool writes set it
    to the agent name; UI writes leave it unset). `etag=""` skips the
    stale-check — used by trusted writers (the agent's own tool path) that
    serialize via the tool, not the Canvas UI. `metadata_patch` lets the caller
    back-fill keys into `workspace["metadata"]` in the same atomic write — only
    keys that are currently missing/falsy are filled, never overwritten.
    """
    if section not in VALID_SECTIONS:
        raise ValueError(f"Invalid section: {section}")
    wf = _workspace_file(name, cfg)
    if not wf.exists():
        raise FileNotFoundError(f"Workspace '{name}' not found")
    current_etag = file_etag(wf)
    if etag and etag != current_etag:
        return {
            "ok": False,
            "error": "stale",
            "current_etag": current_etag,
            "message": "Workspace changed since load. Refresh and try again.",
        }
    workspace = json.loads(wf.read_text(encoding="utf-8"))
    if workspace.get("metadata", {}).get("status") == "closed":
        return {"ok": False, "error": "closed", "message": "Cannot update a closed workspace."}
    if section not in workspace:
        workspace[section] = []
    if metadata_patch:
        meta = workspace.setdefault("metadata", {})
        for k, v in metadata_patch.items():
            if v and not meta.get(k):
                meta[k] = v
    entry: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "content": content,
        "source": source,
        "author": author,
    }
    if agent:
        entry["agent"] = agent
    workspace[section].append(entry)
    wf.write_text(json.dumps(workspace, indent=2), encoding="utf-8")
    new_etag = file_etag(wf)
    return {
        "ok": True,
        "etag": new_etag,
        "entry_count": len(workspace[section]),
        "entry": entry,
    }


def ensure_state_files(
    name: str,
    chat_id: str | None = None,
    *,
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create machine-readable state files for a live workspace.

    Workflow templates are copied once into the session so each chat gets a
    mutable live copy. Existing state files are preserved.
    """
    ensure_session(name, chat_id, cfg=cfg)
    base = state_dir(name, cfg)
    workflows = base / "workflows"
    created: list[str] = []
    base.mkdir(parents=True, exist_ok=True)
    workflows.mkdir(parents=True, exist_ok=True)

    session_path = base / "session_state.yaml"
    if not session_path.exists():
        _write_yaml(session_path, DEFAULT_SESSION_STATE)
        created.append("session_state.yaml")

    events_path = base / "events.jsonl"
    if not events_path.exists():
        events_path.write_text("", encoding="utf-8")
        created.append("events.jsonl")

    # Shipped first, then runtime (UI-published). copy-if-absent: shipped wins on a
    # name clash, and existing live workflow state is never overwritten.
    for templates_dir in workflow_template_dirs(cfg):
        for template in sorted(templates_dir.glob("*.yaml")):
            target = workflows / template.name
            if not target.exists():
                target.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
                created.append(f"workflows/{template.name}")

    return {"ok": True, "created": created, "state_dir": str(base)}


def read_session_state(name: str, *, cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    ensure_state_files(name, cfg=cfg)
    data = _read_yaml(state_dir(name, cfg) / "session_state.yaml", DEFAULT_SESSION_STATE)
    return data if isinstance(data, dict) else dict(DEFAULT_SESSION_STATE)


def merge_session_state(
    name: str,
    patch: dict[str, Any],
    *,
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    current = read_session_state(name, cfg=cfg)
    merged = _deep_merge(current, patch or {})
    _write_yaml(state_dir(name, cfg) / "session_state.yaml", merged)
    return merged


def read_workflow_state(
    name: str,
    workflow_id: str,
    *,
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ensure_state_files(name, cfg=cfg)
    path = state_dir(name, cfg) / "workflows" / f"{_safe_workspace_name(workflow_id)}.yaml"
    data = _read_yaml(path, {})
    return data if isinstance(data, dict) else {}


def merge_workflow_state(
    name: str,
    workflow_id: str,
    patch: dict[str, Any],
    *,
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    current = read_workflow_state(name, workflow_id, cfg=cfg)
    merged = _deep_merge(current, patch or {})
    path = state_dir(name, cfg) / "workflows" / f"{_safe_workspace_name(workflow_id)}.yaml"
    _write_yaml(path, merged)
    return merged


def append_event(
    name: str,
    event: dict[str, Any],
    *,
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ensure_state_files(name, event.get("chat_id"), cfg=cfg)
    path = state_dir(name, cfg) / "events.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    payload = dict(event or {})
    payload["id"] = int(payload.get("id") or (len(lines) + 1))
    payload.setdefault("ts", datetime.now(timezone.utc).isoformat())
    path.write_text(
        "\n".join([*lines, json.dumps(payload, ensure_ascii=False)]) + "\n",
        encoding="utf-8",
    )
    merge_session_state(
        name,
        {"session": {"last_event_id": payload["id"], "updated_by": "scribe"}},
        cfg=cfg,
    )
    return payload
