"""
Inject pen_paper_wiki_template tool prompt only when LLM Wiki integration is enabled.
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    from helpers.extension import Extension
except ImportError:
    from python.helpers.extension import Extension  # type: ignore

_PLUGIN_DIR = Path(__file__).resolve().parents[3]
_TOOLS_DIR = _PLUGIN_DIR / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from _config import load_plugin_config, wiki_enabled  # noqa: E402

_PROMPT_PATH = _PLUGIN_DIR / "assets" / "prompts" / "agent.system.tool.pen_paper_wiki_template.md"


class PenPaperWikiToolPrompt(Extension):
    async def execute(self, system_prompt: list[str] | None = None, **kwargs):
        if system_prompt is None:
            return
        cfg = load_plugin_config(getattr(self, "agent", None))
        if not wiki_enabled(cfg):
            return
        if not _PROMPT_PATH.exists():
            return
        try:
            content = _PROMPT_PATH.read_text(encoding="utf-8").strip()
        except Exception:
            return
        if content:
            system_prompt.append(content)
