#!/usr/bin/env python3
"""Compare two Pen & Paper workspace.json files produced by different models.

Purpose
-------
The plugin's stated goal is that a small model and a flagship model, given the
same task, produce the *same shape* of session — same metadata keys, same section
vocabulary, same execution_log step contract. Wording and timing will differ;
structure must not.

This script diffs two runs modulo volatile fields (timestamps, free text, agent
name, chat id) and reports only structural divergence. It is the machine half of
`docs/pen-paper-workflows/UAT_CROSS_MODEL.md`.

Usage
-----
    python scripts/compare_cross_model_runs.py RUN_A.json RUN_B.json
    python scripts/compare_cross_model_runs.py a.json b.json --require-sections findings,execution_log

Exit codes: 0 = structurally equivalent, 1 = divergence, 2 = bad input.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Mirrors tools/pen_paper.py::VALID_SECTIONS. Kept as a literal on purpose: this
# script must be runnable standalone, outside an Agent Zero checkout.
VALID_SECTIONS = [
    "findings",
    "results",
    "insights",
    "notes",
    "decisions",
    "backtrack",
    "execution_log",
]

# Metadata keys whose VALUES legitimately differ between two runs. Their presence
# is still compared; only the value is ignored.
VOLATILE_META = {"created_at", "closed_at", "agent", "chat_id", "name"}

# Entry keys whose values are run-specific.
VOLATILE_ENTRY = {"timestamp", "content", "agent", "author"}

VALID_STATUSES = {"pending", "running", "done", "failed", "skipped"}


class Divergence(list):
    def add(self, kind: str, detail: str) -> None:
        self.append((kind, detail))


def _load(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"error: no such file: {path}", file=sys.stderr)
        raise SystemExit(2)
    except json.JSONDecodeError as e:
        print(f"error: {path} is not valid JSON: {e}", file=sys.stderr)
        raise SystemExit(2)
    if not isinstance(data, dict):
        print(f"error: {path} is not a workspace object", file=sys.stderr)
        raise SystemExit(2)
    return data


def _entry_shape(entry: Any) -> tuple[str, ...]:
    """Structural signature of one section entry: its key set, sorted."""
    if not isinstance(entry, dict):
        return ("<non-object>",)
    return tuple(sorted(entry.keys()))


def _execution_steps(workspace: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Return (step_ids, statuses) parsed from execution_log entries.

    Entries are expected to carry a JSON object in `content`:
    {"step_id": "...", "status": "..."}. Non-JSON content is reported as a
    malformed step rather than crashing — a small model emitting prose here is
    exactly the divergence this UAT is meant to catch.
    """
    ids: list[str] = []
    statuses: list[str] = []
    for entry in workspace.get("execution_log") or []:
        raw = entry.get("content") if isinstance(entry, dict) else None
        if not isinstance(raw, str):
            statuses.append("<malformed:not-a-string>")
            continue
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            statuses.append("<malformed:not-json>")
            continue
        if not isinstance(obj, dict):
            statuses.append("<malformed:not-object>")
            continue
        ids.append(str(obj.get("step_id", "<missing>")))
        statuses.append(str(obj.get("status", "<missing>")))
    return ids, statuses


def compare(a: dict[str, Any], b: dict[str, Any], require: list[str]) -> Divergence:
    d = Divergence()

    # 1. Top-level key sets (sections + metadata + any extras like `relations`).
    ka, kb = set(a.keys()), set(b.keys())
    if ka != kb:
        only_a, only_b = sorted(ka - kb), sorted(kb - ka)
        if only_a:
            d.add("top-level keys", f"only in A: {only_a}")
        if only_b:
            d.add("top-level keys", f"only in B: {only_b}")

    # 2. Every VALID_SECTIONS key must exist in both — a model must not drop or
    #    invent sections.
    for run, ws in (("A", a), ("B", b)):
        missing = [s for s in VALID_SECTIONS if s not in ws]
        if missing:
            d.add("section vocabulary", f"run {run} missing sections: {missing}")
        invented = [
            k
            for k in ws
            if k not in VALID_SECTIONS and k not in {"metadata", "relations"}
        ]
        if invented:
            d.add("section vocabulary", f"run {run} has non-standard keys: {invented}")

    # 3. Metadata key sets must match (values may differ where volatile).
    ma = a.get("metadata") or {}
    mb = b.get("metadata") or {}
    mka, mkb = set(ma.keys()), set(mb.keys())
    if mka != mkb:
        if mka - mkb:
            d.add("metadata keys", f"only in A: {sorted(mka - mkb)}")
        if mkb - mka:
            d.add("metadata keys", f"only in B: {sorted(mkb - mka)}")
    for key in sorted((mka & mkb) - VOLATILE_META):
        if ma[key] != mb[key]:
            d.add("metadata value", f"{key}: A={ma[key]!r} B={mb[key]!r}")

    # 4. Which sections were actually used, and the entry shape within each.
    used_a = {s for s in VALID_SECTIONS if a.get(s)}
    used_b = {s for s in VALID_SECTIONS if b.get(s)}
    if used_a != used_b:
        if used_a - used_b:
            d.add("sections used", f"only run A wrote: {sorted(used_a - used_b)}")
        if used_b - used_a:
            d.add("sections used", f"only run B wrote: {sorted(used_b - used_a)}")

    for section in VALID_SECTIONS:
        shapes_a = {_entry_shape(e) for e in (a.get(section) or [])}
        shapes_b = {_entry_shape(e) for e in (b.get(section) or [])}
        if shapes_a and shapes_b and shapes_a != shapes_b:
            d.add(
                "entry shape",
                f"{section}: A={sorted(shapes_a)} B={sorted(shapes_b)}",
            )

    # 5. execution_log contract — the determinism-critical part.
    ids_a, st_a = _execution_steps(a)
    ids_b, st_b = _execution_steps(b)
    for run, statuses in (("A", st_a), ("B", st_b)):
        bad = [s for s in statuses if s not in VALID_STATUSES]
        if bad:
            d.add("execution_log status", f"run {run} invalid/malformed: {bad}")
    if ids_a != ids_b:
        d.add("execution_log steps", f"step_id sequence differs: A={ids_a} B={ids_b}")
    if st_a != st_b:
        d.add("execution_log status", f"status sequence differs: A={st_a} B={st_b}")

    # 6. Sections the protocol requires both runs to have populated.
    for section in require:
        for run, ws in (("A", a), ("B", b)):
            if not ws.get(section):
                d.add("required section", f"run {run} left '{section}' empty")

    return d


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__ .split("\n")[0])
    p.add_argument("run_a", type=Path, help="workspace.json from the first model")
    p.add_argument("run_b", type=Path, help="workspace.json from the second model")
    p.add_argument(
        "--require-sections",
        default="findings,execution_log",
        help="comma-separated sections both runs must have populated "
        "(default: findings,execution_log; pass '' to disable)",
    )
    args = p.parse_args()

    require = [s.strip() for s in args.require_sections.split(",") if s.strip()]
    a, b = _load(args.run_a), _load(args.run_b)

    print(f"A: {args.run_a}")
    print(f"B: {args.run_b}")
    print()

    d = compare(a, b, require)
    if not d:
        print("PASS — runs are structurally equivalent.")
        print(f"  sections used : {sorted(s for s in VALID_SECTIONS if a.get(s))}")
        ids, statuses = _execution_steps(a)
        if ids:
            print(f"  execution_log : {list(zip(ids, statuses))}")
        return 0

    print(f"FAIL — {len(d)} structural divergence(s):")
    for kind, detail in d:
        print(f"  [{kind}] {detail}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
