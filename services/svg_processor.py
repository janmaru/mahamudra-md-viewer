"""
Inline SVG processing service.
Extracts `<svg>...</svg>` blocks from Markdown source, rasterizes each via
resvg-py to PNG, and embeds the result as base64 `<img>` tags. Necessary
because tkhtml3 (under tkinterweb) does not render inline SVG, and
Python-Markdown wraps inline SVG inside `<p>` regardless.
"""

from __future__ import annotations

import base64
import re

# Match a complete <svg ...> ... </svg> block, including newlines.
_SVG_PATTERN = re.compile(r"<svg\b[^>]*>.*?</svg>", re.DOTALL | re.IGNORECASE)

# Multiplier applied to the SVG's intrinsic size when rasterising. Higher =
# crisper on HiDPI but heavier PNG. resvg-py's `zoom` requires an integer.
_RASTER_ZOOM = 2


def process_svg_blocks(content: str) -> tuple[str, list[str]]:
    """
    Replace each inline <svg>...</svg> block with a placeholder comment.
    Returns the modified content and the list of original SVG blocks.
    """
    svg_blocks: list[str] = []

    def save_svg(match: re.Match) -> str:
        svg_blocks.append(match.group(0))
        return f"<!--SVG_{len(svg_blocks) - 1}-->"

    processed_content = _SVG_PATTERN.sub(save_svg, content)
    return processed_content, svg_blocks


def inject_svg_placeholders(html: str, svg_blocks: list[str]) -> str:
    """Replace SVG placeholders with a loading indicator."""
    for i in range(len(svg_blocks)):
        tag = ('<div class="mermaid-container" style="padding:40px;color:#888;'
               'font-style:italic;text-align:center;">Rendering diagram...</div>')
        html = html.replace(f"<!--SVG_{i}-->", tag)
        html = html.replace(f"<p><!--SVG_{i}--></p>", tag)
    return html


def inject_svg_images(html: str, svg_blocks: list[str],
                      diagram_registry: dict | None = None) -> str:
    """
    Replace SVG placeholders with rasterised PNG images (base64-embedded).
    Falls back to a raw <pre> block if rasterisation fails.
    """
    for i, svg in enumerate(svg_blocks):
        png_b64 = _render_svg_to_png_b64(svg)
        if png_b64:
            if diagram_registry is not None:
                key = f"d{len(diagram_registry)}"
                diagram_registry[key] = png_b64
                tag = (f'<div class="mermaid-container">'
                       f'<a href="diagram:{key}" title="Click to zoom">'
                       f'<img src="data:image/png;base64,{png_b64}" alt="SVG diagram" '
                       f'style="max-width:100%;height:auto;cursor:zoom-in">'
                       f'</a></div>')
            else:
                tag = (f'<div class="mermaid-container">'
                       f'<img src="data:image/png;base64,{png_b64}" alt="SVG diagram" '
                       f'style="max-width:100%;height:auto">'
                       f'</div>')
        else:
            from html import escape
            tag = f'<div class="mermaid-container"><pre>{escape(svg)}</pre></div>'
        html = html.replace(f"<!--SVG_{i}-->", tag)
        html = html.replace(f"<p><!--SVG_{i}--></p>", tag)

    return html


def _render_svg_to_png_b64(svg_text: str) -> str | None:
    """Rasterise an SVG string to base64 PNG. Uses the shared disk cache."""
    from services.diagram_cache import get as cache_get, put as cache_put

    cached = cache_get(svg_text)
    if cached:
        return cached

    try:
        import resvg_py
    except ImportError:
        return None

    try:
        raw = resvg_py.svg_to_bytes(svg_string=svg_text, zoom=_RASTER_ZOOM)
    except Exception:
        return None

    png_bytes = bytes(raw) if not isinstance(raw, (bytes, bytearray)) else bytes(raw)
    if not png_bytes:
        return None

    png_b64 = base64.b64encode(png_bytes).decode("ascii")
    cache_put(svg_text, png_b64)
    return png_b64
