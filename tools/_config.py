"""
Shared configuration loader for a0_pen_paper plugin tools.
"""
from __future__ import annotations

from typing import Any

PLUGIN_NAME = "a0_pen_paper"

DEFAULTS: dict[str, Any] = {
    "runtime_dir": "usr/pen_and_paper",
    "features": {
        "retrieve_context_on_create": False,
        "vectorize_on_close": False,
        "context_loader_enabled": False,
        "context_loader_first_iteration_only": True,
    },
    "llm_wiki_integration": {
        "enabled": False,
        "vault_path": "",
        "max_templates_per_list": 20,
        "max_preview_chars": 500,
        "max_full_load_chars": 3000,
    },
    "session": {
        "max_active_sessions_in_context": 5,
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _normalize_legacy(cfg: dict[str, Any]) -> dict[str, Any]:
    """Map legacy flat keys into features.* (Wave 1)."""
    out = dict(cfg)
    features = dict(out.get("features") or {})
    if "vectorize_by_default" in out:
        features["vectorize_on_close"] = out.pop("vectorize_by_default")
    if "retrieve_context_by_default" in out:
        features["retrieve_context_on_create"] = out.pop("retrieve_context_by_default")
    if "context_loader_enabled" in out and "context_loader_enabled" not in features:
        features["context_loader_enabled"] = out.pop("context_loader_enabled")
    if "context_loader_first_iteration_only" in out and "context_loader_first_iteration_only" not in features:
        features["context_loader_first_iteration_only"] = out.pop(
            "context_loader_first_iteration_only"
        )
    if "max_active_sessions_in_context" in out and "session" not in out:
        out["session"] = {"max_active_sessions_in_context": out.pop("max_active_sessions_in_context")}
    if features:
        out["features"] = features
    return out


def load_plugin_config(agent=None) -> dict[str, Any]:
    """Load plugin config with safe defaults outside Agent Zero runtime."""
    cfg: dict[str, Any] = {}
    try:
        from helpers.plugins import get_plugin_config

        cfg = get_plugin_config(PLUGIN_NAME, agent=agent) or {}
    except Exception:
        pass
    cfg = _normalize_legacy(cfg)
    return _deep_merge(DEFAULTS, cfg)


def runtime_base(cfg: dict[str, Any] | None = None) -> str:
    return (cfg or DEFAULTS).get("runtime_dir", DEFAULTS["runtime_dir"])


def feature_enabled(cfg: dict[str, Any], key: str) -> bool:
    return bool((cfg.get("features") or {}).get(key, False))


def wiki_enabled(cfg: dict[str, Any]) -> bool:
    return bool((cfg.get("llm_wiki_integration") or {}).get("enabled", False))


def wiki_settings(cfg: dict[str, Any]) -> dict[str, Any]:
    base = dict(DEFAULTS["llm_wiki_integration"])
    base.update(cfg.get("llm_wiki_integration") or {})
    return base
