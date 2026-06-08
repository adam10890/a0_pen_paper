"""
Deterministic draw.io XML generation for Pen & Paper workflow artifacts.
"""
from __future__ import annotations

import html
import re
import textwrap
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any


VALID_DIAGRAM_TYPES = {
    "flow",
    "flow-vertical",
    "layers",
    "sequence",
    "timeline",
}

THEMES: dict[str, dict[str, str]] = {
    "tech-blue": {
        "fill": "#EAF2FF",
        "stroke": "#5B7FC7",
        "accent_fill": "#FFF4D6",
        "accent_stroke": "#D79A2B",
        "line": "#52637A",
    },
    "morandi": {
        "fill": "#EEF1EA",
        "stroke": "#8D9B88",
        "accent_fill": "#EEE8F1",
        "accent_stroke": "#A28FA8",
        "line": "#6F756D",
    },
    "mint": {
        "fill": "#E8F7F0",
        "stroke": "#52A37E",
        "accent_fill": "#FFF6D8",
        "accent_stroke": "#D9A93E",
        "line": "#52786B",
    },
    "terracotta": {
        "fill": "#F8ECE6",
        "stroke": "#C77757",
        "accent_fill": "#F7F0DE",
        "accent_stroke": "#BFA05B",
        "line": "#8B6658",
    },
    "indigo": {
        "fill": "#EEF0FF",
        "stroke": "#6A6DD9",
        "accent_fill": "#F4EAFE",
        "accent_stroke": "#9A6AD9",
        "line": "#5557A6",
    },
}


@dataclass
class DiagramNode:
    id: str
    label: str
    detail: str = ""
    kind: str = "step"


@dataclass
class DiagramEdge:
    source: str
    target: str
    label: str = ""


def clean_label(value: Any, limit: int = 72) -> str:
    """Collapse whitespace and keep labels usable inside compact nodes."""
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if not text:
        return "Untitled"
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def extract_markdown_steps(markdown: str, fallback_title: str = "Step") -> list[str]:
    """Extract likely workflow steps from headings, numbered lists, or bullets."""
    if "->" in (markdown or ""):
        arrow_steps = [clean_label(part) for part in markdown.split("->") if part.strip()]
        if len(arrow_steps) >= 2:
            return arrow_steps[:12]

    steps: list[str] = []
    for raw in (markdown or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        heading = re.match(r"^#{1,4}\s+(.+)$", line)
        numbered = re.match(r"^\d+[\.)]\s+(.+)$", line)
        bullet = re.match(r"^[-*]\s+(.+)$", line)
        match = heading or numbered or bullet
        if match:
            label = clean_label(match.group(1))
            if label.lower() not in {"overview", "notes", "guidance"}:
                steps.append(label)
        if len(steps) >= 12:
            break

    if steps:
        return _dedupe_preserve_order(steps)

    sentences = re.split(r"(?<=[.!?])\s+", (markdown or "").strip())
    compact = [clean_label(s) for s in sentences if len(s.strip()) >= 8]
    return compact[:8] or [fallback_title]


def nodes_from_template(
    template_name: str,
    registry_entry: dict[str, Any],
    content: str,
) -> tuple[list[DiagramNode], list[DiagramEdge]]:
    phases = registry_entry.get("phases") or []
    if phases:
        labels = [clean_label(p) for p in phases]
    else:
        labels = extract_markdown_steps(content, fallback_title=template_name)

    nodes = [
        DiagramNode(
            id=f"n{i}",
            label=label,
            detail=clean_label(registry_entry.get("description", ""), 96) if i == 1 else "",
            kind="phase",
        )
        for i, label in enumerate(labels, 1)
    ]
    return nodes, sequential_edges(nodes)


def nodes_from_session(workspace: dict[str, Any], valid_sections: list[str]) -> tuple[list[DiagramNode], list[DiagramEdge]]:
    nodes: list[DiagramNode] = []
    metadata = workspace.get("metadata") or {}
    template = metadata.get("template")
    for section in valid_sections:
        entries = workspace.get(section) or []
        if not entries:
            continue
        last = entries[-1].get("content", "") if isinstance(entries[-1], dict) else ""
        nodes.append(
            DiagramNode(
                id=f"n{len(nodes) + 1}",
                label=f"{section.replace('_', ' ').title()} ({len(entries)})",
                detail=clean_label(last, 96),
                kind="section",
            )
        )

    if not nodes:
        name = metadata.get("name") or "Empty session"
        nodes.append(DiagramNode(id="n1", label=clean_label(name), detail="No section entries yet"))
    elif template:
        nodes.insert(
            0,
            DiagramNode(
                id="n0",
                label=f"Template: {clean_label(template)}",
                detail=clean_label(metadata.get("name", ""), 96),
                kind="template",
            ),
        )
    return nodes, sequential_edges(nodes)


def nodes_from_text(text: str, title: str = "Ad hoc diagram") -> tuple[list[DiagramNode], list[DiagramEdge]]:
    labels = extract_markdown_steps(text, fallback_title=title)
    nodes = [
        DiagramNode(id=f"n{i}", label=label, kind="step")
        for i, label in enumerate(labels, 1)
    ]
    return nodes, sequential_edges(nodes)


def sequential_edges(nodes: list[DiagramNode]) -> list[DiagramEdge]:
    return [
        DiagramEdge(source=nodes[i].id, target=nodes[i + 1].id)
        for i in range(max(0, len(nodes) - 1))
    ]


def ascii_sketch(nodes: list[DiagramNode], diagram_type: str) -> str:
    labels = [n.label for n in nodes]
    if diagram_type in {"flow", "timeline"}:
        return " -> ".join(labels)
    if diagram_type == "layers":
        return "\n".join(f"[Layer {i}] {label}" for i, label in enumerate(labels, 1))
    return "\n".join(f"{i}. {label}" for i, label in enumerate(labels, 1))


def build_whiteboard_shapes(
    title: str,
    nodes: list[DiagramNode],
    edges: list[DiagramEdge],
    diagram_type: str = "flow",
    theme_name: str = "tech-blue",
) -> list[dict[str, Any]]:
    """Convert the same diagram model into a0_whiteboard backend shapes."""
    if diagram_type not in VALID_DIAGRAM_TYPES:
        diagram_type = "flow"
    theme = THEMES.get(theme_name) or THEMES["tech-blue"]
    layout = _layout(nodes, diagram_type)
    shapes: list[dict[str, Any]] = [
        {
            "id": "pnp_diagram_title",
            "type": "text",
            "x": 60,
            "y": 25,
            "w": 560,
            "h": 40,
            "props": {
                "text": clean_label(title, 120),
                "color": theme["stroke"],
                "fontSize": 22,
                "fill": "transparent",
            },
        }
    ]

    for index, node in enumerate(nodes, 1):
        x, y, width, height = layout[node.id]
        fill = theme["accent_fill"] if index in {1, len(nodes)} and len(nodes) > 2 else theme["fill"]
        text = node.label if not node.detail else f"{node.label}\n{node.detail}"
        shapes.append(
            {
                "id": f"pnp_{node.id}",
                "type": "rect",
                "x": x,
                "y": y + 65,
                "w": width,
                "h": max(height, 96 if node.detail else height),
                "props": {
                    "text": clean_label(text, 140),
                    "color": theme["stroke"],
                    "strokeWidth": 2,
                    "fill": fill,
                    "fontSize": 15,
                },
            }
        )

    for index, edge in enumerate(edges, 1):
        if edge.source not in layout or edge.target not in layout:
            continue
        sx, sy, sw, sh = layout[edge.source]
        tx, ty, tw, th = layout[edge.target]
        x1 = sx + sw / 2
        y1 = sy + sh / 2 + 65
        x2 = tx + tw / 2
        y2 = ty + th / 2 + 65
        shapes.append(
            {
                "id": f"pnp_edge_{index}",
                "type": "arrow",
                "x": min(x1, x2),
                "y": min(y1, y2),
                "w": abs(x2 - x1) or 1,
                "h": abs(y2 - y1) or 1,
                "points": [x1, y1, x2, y2],
                "props": {
                    "color": theme["line"],
                    "strokeWidth": 2,
                    "fill": "transparent",
                },
            }
        )
    return shapes


def build_drawio_xml(
    title: str,
    nodes: list[DiagramNode],
    edges: list[DiagramEdge],
    diagram_type: str = "flow",
    theme_name: str = "tech-blue",
) -> str:
    if diagram_type not in VALID_DIAGRAM_TYPES:
        diagram_type = "flow"
    theme = THEMES.get(theme_name) or THEMES["tech-blue"]

    mxfile = ET.Element(
        "mxfile",
        {
            "host": "Agent Zero Pen & Paper",
            "type": "device",
            "version": "22.1.16",
        },
    )
    diagram = ET.SubElement(mxfile, "diagram", {"id": "pen-paper-diagram", "name": clean_label(title, 48)})
    model = ET.SubElement(
        diagram,
        "mxGraphModel",
        {
            "dx": "1200",
            "dy": "800",
            "grid": "1",
            "gridSize": "10",
            "guides": "1",
            "tooltips": "1",
            "connect": "1",
            "arrows": "1",
            "fold": "1",
            "page": "1",
            "pageScale": "1",
            "pageWidth": "1169",
            "pageHeight": "827",
            "math": "0",
            "shadow": "0",
        },
    )
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", {"id": "0"})
    ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})

    layout = _layout(nodes, diagram_type)
    for idx, node in enumerate(nodes):
        x, y, width, height = layout[node.id]
        fill = theme["accent_fill"] if idx in {0, len(nodes) - 1} and len(nodes) > 2 else theme["fill"]
        stroke = theme["accent_stroke"] if fill == theme["accent_fill"] else theme["stroke"]
        value = _node_value(node)
        cell = ET.SubElement(
            root,
            "mxCell",
            {
                "id": node.id,
                "value": value,
                "style": (
                    "rounded=1;whiteSpace=wrap;html=1;arcSize=8;"
                    f"fillColor={fill};strokeColor={stroke};strokeWidth=2;"
                    "fontColor=#1F2937;fontSize=13;spacing=10;"
                ),
                "vertex": "1",
                "parent": "1",
            },
        )
        ET.SubElement(
            cell,
            "mxGeometry",
            {
                "x": str(x),
                "y": str(y),
                "width": str(width),
                "height": str(height),
                "as": "geometry",
            },
        )

    for i, edge in enumerate(edges, 1):
        if edge.source not in layout or edge.target not in layout:
            continue
        cell = ET.SubElement(
            root,
            "mxCell",
            {
                "id": f"e{i}",
                "value": html.escape(edge.label),
                "style": (
                    "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;"
                    "jettySize=auto;html=1;"
                    f"strokeColor={theme['line']};strokeWidth=2;"
                    "endArrow=block;endFill=1;"
                ),
                "edge": "1",
                "parent": "1",
                "source": edge.source,
                "target": edge.target,
            },
        )
        ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})

    xml = ET.tostring(mxfile, encoding="unicode", short_empty_elements=True)
    ET.fromstring(xml)
    return xml


def _node_value(node: DiagramNode) -> str:
    label = html.escape(node.label)
    if not node.detail:
        return label
    detail = html.escape("\n".join(textwrap.wrap(node.detail, width=44)))
    return f"<b>{label}</b><br/><font style=\"font-size:11px\">{detail}</font>"


def _layout(nodes: list[DiagramNode], diagram_type: str) -> dict[str, tuple[int, int, int, int]]:
    out: dict[str, tuple[int, int, int, int]] = {}
    if diagram_type == "flow":
        for i, node in enumerate(nodes):
            out[node.id] = (60 + i * 240, 140, 180, 82)
    elif diagram_type in {"flow-vertical", "sequence"}:
        for i, node in enumerate(nodes):
            out[node.id] = (130, 70 + i * 125, 340, 82)
    elif diagram_type == "layers":
        for i, node in enumerate(nodes):
            out[node.id] = (90, 60 + i * 105, 460, 78)
    elif diagram_type == "timeline":
        for i, node in enumerate(nodes):
            y = 95 if i % 2 == 0 else 210
            out[node.id] = (60 + i * 220, y, 170, 76)
    else:
        for i, node in enumerate(nodes):
            out[node.id] = (60 + i * 240, 140, 180, 82)
    return out


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out
