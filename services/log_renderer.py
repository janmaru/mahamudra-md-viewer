"""
Structured log viewer for Serilog-style log files.
Renders parsed log content to HTML with collapsible tree nodes,
colour-coded directions and severity levels.
"""

from __future__ import annotations

import html as html_module

from domain.models import LogLine, TreeNode
from domain.services import LogParserService

# Direction constants for convenience (imported from domain models)
DIR_PLC_WCS = "PLC->WCS"
DIR_WCS_PLC = "WCS->PLC"
_DIR_CSS = {DIR_PLC_WCS: "dir-plc-wcs", DIR_WCS_PLC: "dir-wcs-plc"}


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------

_CSS_TEMPLATE = """\
<style>
.log-viewer {{
    font-family: Consolas, 'Courier New', monospace;
    font-size: 0.88em;
    line-height: 1.6;
    color: inherit;
}}
.log-node {{
    margin-bottom: 2px;
}}
.log-group > summary {{
    cursor: pointer;
    padding: 4px 8px;
    border-radius: 3px;
    list-style: none;
    border-left: 3px solid rgba(128,128,128,0.5);
    background: rgba(128,128,128,0.06);
    color: inherit;
}}
.log-group > summary::-webkit-details-marker {{ display: none; }}
.log-group > summary::before {{
    content: '\\25B8 ';
    opacity: 0.5;
}}
.log-group[open] > summary::before {{
    content: '\\25BE ';
}}
.log-group .log-children {{
    margin-left: 18px;
    border-left: 1px solid rgba(128,128,128,0.25);
    padding-left: 12px;
}}
.log-line {{
    padding: 2px 8px;
    border-radius: 2px;
    white-space: pre-wrap;
    word-break: break-all;
}}
.log-ts {{
    opacity: 0.5;
    font-size: 0.85em;
    margin-right: 8px;
}}
.log-level-wrn {{ color: {wrn}; font-weight: bold; }}
.log-level-err {{ color: {err}; font-weight: bold; }}
.log-level-ftl {{ color: {err}; font-weight: bold; }}
.log-level-inf {{ opacity: 0.6; }}
.log-level-dbg {{ color: {dbg}; }}

/* Direction colours */
.dir-plc-wcs {{
    border-left: 3px solid {green};
}}
.dir-plc-wcs .dir-icon {{ color: {green}; font-weight: bold; }}
.dir-wcs-plc {{
    border-left: 3px solid {red};
}}
.dir-wcs-plc .dir-icon {{ color: {red}; font-weight: bold; }}

/* Warning / Error row highlight */
.row-wrn {{ background: rgba(232,163,23,0.12); border-left: 3px solid {wrn}; }}
.row-err {{ background: rgba(244,71,71,0.15); border-left: 3px solid {err}; }}
.row-ftl {{ background: rgba(244,71,71,0.25); border-left: 3px solid {err}; }}

/* JSON collapsible */
.json-toggle {{
    font-size: 0.85em;
    opacity: 0.6;
    cursor: pointer;
    margin-left: 6px;
}}
.json-toggle summary {{
    list-style: none;
    display: inline;
}}
.json-toggle summary::-webkit-details-marker {{ display: none; }}
.json-toggle pre {{
    margin: 4px 0 4px 20px;
    padding: 8px 12px;
    background: rgba(128,128,128,0.1);
    border-radius: 4px;
    font-size: 0.92em;
    white-space: pre-wrap;
    word-break: break-all;
    opacity: 1;
    color: inherit;
}}
.log-body {{ color: inherit; }}
.log-msg-type {{ color: {blue}; font-weight: 600; }}
</style>
"""

# Palette per sfondo scuro (vscode_dark, industrial_dark)
_COLORS_DARK = dict(
    green="#4ec980", red="#f14c4c", wrn="#e8a317",
    err="#f44747", dbg="#6a9955", blue="#569cd6",
)
# Palette per sfondo chiaro (french_revolution, ecc.)
_COLORS_LIGHT = dict(
    green="#1a7a3a", red="#c62828", wrn="#b8860b",
    err="#c62828", dbg="#2e7d32", blue="#1565c0",
)


def _esc(text: str) -> str:
    return html_module.escape(text)


def _level_css(level: str) -> str:
    return f"log-level-{level.lower()}"


def _row_css(line: LogLine) -> str:
    classes = ["log-line"]
    if line.level == "WRN":
        classes.append("row-wrn")
    elif line.level == "ERR":
        classes.append("row-err")
    elif line.level == "FTL":
        classes.append("row-ftl")
    elif line.direction:
        classes.append(_DIR_CSS.get(line.direction, ""))
    return " ".join(classes)


def _render_direction_icon(line: LogLine) -> str:
    if not line.direction:
        return ""
    if line.direction == DIR_PLC_WCS:
        return '<span class="dir-icon" title="PLC &#8594; WCS">&#8592; </span>'
    elif line.direction == DIR_WCS_PLC:
        return '<span class="dir-icon" title="WCS &#8594; PLC">&#8594; </span>'
    return ""


def _render_json(line: LogLine) -> str:
    if not line.json_payload:
        return ""
    return (
        '<details class="json-toggle"><summary>\u25b8 JSON</summary>'
        f'<pre>{_esc(line.json_payload)}</pre>'
        '</details>'
    )


def _render_line_content(line: LogLine) -> str:
    parts = [f'<span class="log-ts">{_esc(line.short_ts)}</span>']

    if line.level:
        parts.append(f'<span class="{_level_css(line.level)}">[{_esc(line.level)}]</span> ')

    parts.append(_render_direction_icon(line))

    body = _esc(line.body)
    if line.json_post:
        body += f' <span style="color:#888">{_esc(line.json_post)}</span>'
    parts.append(f'<span class="log-body">{body}</span>')
    parts.append(_render_json(line))

    return "".join(parts)


def _render_node(node: TreeNode) -> str:
    if not node.children:
        css = _row_css(node.header)
        return f'<div class="{css}">{_render_line_content(node.header)}</div>'

    header = node.header
    summary_parts = [f'<span class="log-ts">{_esc(header.short_ts)}</span>']
    if header.level:
        summary_parts.append(f'<span class="{_level_css(header.level)}">[{_esc(header.level)}]</span> ')
    if header.routing_type:
        summary_parts.append(f'Routing <span class="log-msg-type">{_esc(header.routing_type)}</span>')
    else:
        summary_parts.append(f'<span class="log-body">{_esc(header.body)}</span>')

    children_count = len(node.children)
    summary_parts.append(f' <span style="color:#888;font-size:0.8em">({children_count})</span>')

    children_html = []
    for child in node.children:
        css = _row_css(child)
        children_html.append(f'<div class="{css}">{_render_line_content(child)}</div>')

    return (
        f'<details class="log-group log-node" open>'
        f'<summary>{"".join(summary_parts)}</summary>'
        f'<div class="log-children">{"".join(children_html)}</div>'
        f'</details>'
    )


def render_log(content: str, dark_bg: bool = True) -> str:
    """Parse Serilog content and return structured HTML body.

    Parameters
    ----------
    dark_bg : bool
        True when the markdown theme has a dark background (default).
        Set to False for light-background themes so accent colours
        have enough contrast.
    """
    parser = LogParserService()
    parsed = parser.parse_lines(content)
    tree = parser.build_tree(parsed)

    colors = _COLORS_DARK if dark_bg else _COLORS_LIGHT
    css = _CSS_TEMPLATE.format(**colors)

    parts = [css, '<div class="log-viewer">']
    for node in tree:
        parts.append(_render_node(node))
    parts.append("</div>")

    return "\n".join(parts)
