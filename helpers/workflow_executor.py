"""
Lightweight workflow policy helper for Pen & Paper (Wave 3 MVP).
Hints and validation only — no automatic sub-agent execution.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from usr.plugins.a0_pen_paper.helpers.workflows_store import (
    _read_registry,
    validate_registry_integrity,
    workflows_dir,
)
from usr.plugins.a0_pen_paper.tools._config import load_plugin_config

TERMINAL_STEP_STATUSES = frozenset({"done", "failed", "skipped"})


@dataclass
class CheckResult:
    ok: bool
    message: str = ""


class WorkflowExecutor:
    def __init__(self, cfg: dict[str, Any] | None = None):
        self.cfg = cfg or load_plugin_config()

    def resolve_hook(self, event: str) -> str | None:
        reg = _read_registry(self.cfg)
        hooks = (reg.get("base_workflows") or {}).get("hooks") or {}
        target = hooks.get(event)
        if not target:
            return None
        templates = reg.get("templates") or {}
        if target in templates:
            wf = workflows_dir(self.cfg) / templates[target].get("file", f"{target}.md")
            if wf.exists():
                return target
        return None

    def hook_hint(self, event: str) -> str:
        target = self.resolve_hook(event)
        if not target:
            return ""
        return (
            f"Workflow hint ({event}): consider `pen_paper` action=use_template "
            f"with template_name={target!r}."
        )

    def pre_update(self, workspace: dict, section: str) -> CheckResult:
        if workspace.get("metadata", {}).get("status") == "closed":
            return CheckResult(False, "Cannot update a closed workspace.")
        if section not in workspace and section != "execution_log":
            pass
        return CheckResult(True)

    def pre_close(self, workspace: dict) -> CheckResult:
        if workspace.get("metadata", {}).get("status") == "closed":
            return CheckResult(False, "Workspace is already closed.")
        return CheckResult(True)

    def validate_execution_log_entry(self, content: str) -> CheckResult:
        try:
            data = json.loads(content) if content.strip().startswith("{") else None
        except json.JSONDecodeError:
            return CheckResult(
                False,
                "execution_log entry must be JSON with step_id and status "
                "(pending|running|done|failed|skipped).",
            )
        if data is None:
            return CheckResult(True)
        status = str(data.get("status", "")).lower()
        if status and status not in ("pending", "running", "done", "failed", "skipped"):
            return CheckResult(
                False,
                f"Invalid execution_log status '{status}'. Use done, not COMPLETED.",
            )
        return CheckResult(True)

    def check_step_idempotent(self, workspace: dict, step_id: str) -> CheckResult:
        for entry in workspace.get("execution_log") or []:
            raw = entry.get("content", "")
            try:
                data = json.loads(raw) if raw.strip().startswith("{") else {}
            except json.JSONDecodeError:
                continue
            if data.get("step_id") == step_id:
                st = str(data.get("status", "")).lower()
                if st in TERMINAL_STEP_STATUSES:
                    return CheckResult(
                        False,
                        f"Step '{step_id}' already has terminal status '{st}'. "
                        "Do not re-run (execution_contract).",
                    )
        return CheckResult(True)

    def registry_status(self) -> list[str]:
        return validate_registry_integrity(self.cfg)
