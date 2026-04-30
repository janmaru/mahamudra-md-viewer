"""
Local Mermaid diagram processing service.
Pre-renders Mermaid code blocks to PNG via mmdc and embeds them as base64 images.
"""

import re
import subprocess
import tempfile
import os
import shutil
import base64

# Regex for Mermaid fenced code blocks
MERMAID_PATTERN = r'```mermaid\s*(.*?)\s*```'


def process_mermaid_blocks(content: str) -> tuple[str, list[str]]:
    """
    Find all mermaid blocks in the markdown content and replace them
    with placeholders for later injection.
    """
    mermaid_blocks = []

    def save_mermaid(match):
        code = match.group(1).strip()
        mermaid_blocks.append(code)
        return f"<!--MERMAID_{len(mermaid_blocks)-1}-->"

    processed_content = re.sub(MERMAID_PATTERN, save_mermaid, content, flags=re.DOTALL)
    return processed_content, mermaid_blocks


def inject_mermaid_placeholders(html: str, mermaid_blocks: list[str]) -> str:
    """Replace mermaid placeholders with loading indicators."""
    for i, code in enumerate(mermaid_blocks):
        tag = ('<div class="mermaid-container" style="padding:40px;color:#888;'
               'font-style:italic;text-align:center;">Rendering diagram...</div>')
        html = html.replace(f"<!--MERMAID_{i}-->", tag)
        html = html.replace(f"<p><!--MERMAID_{i}--></p>", tag)
    return html


def inject_mermaid_svgs(html: str, mermaid_blocks: list[str],
                        diagram_registry: dict | None = None) -> str:
    """
    Replace mermaid placeholders with pre-rendered PNG images (base64).
    Falls back to raw code block if rendering fails.
    If diagram_registry is provided, stores base64 data and wraps images in clickable links.
    """
    for i, code in enumerate(mermaid_blocks):
        png_b64 = _render_mermaid_to_png_b64(code)
        if png_b64:
            if diagram_registry is not None:
                key = f"d{len(diagram_registry)}"
                diagram_registry[key] = png_b64
                tag = (f'<div class="mermaid-container">'
                       f'<a href="diagram:{key}" title="Click to zoom">'
                       f'<img src="data:image/png;base64,{png_b64}" alt="Mermaid diagram" '
                       f'style="cursor:zoom-in">'
                       f'</a></div>')
            else:
                tag = (f'<div class="mermaid-container">'
                       f'<img src="data:image/png;base64,{png_b64}" alt="Mermaid diagram">'
                       f'</div>')
        else:
            tag = f'<div class="mermaid-container"><pre>{code}</pre></div>'
        html = html.replace(f"<!--MERMAID_{i}-->", tag)
        html = html.replace(f"<p><!--MERMAID_{i}--></p>", tag)

    return html


def _find_mmdc() -> str | None:
    """Locate the mmdc executable."""
    path = shutil.which("mmdc")
    if path:
        return path
    npx = shutil.which("npx")
    if npx:
        return npx
    return None


def _render_mermaid_to_png_b64(code: str) -> str | None:
    """Render a Mermaid diagram to PNG and return base64-encoded string. Uses disk cache."""
    from services.diagram_cache import get as cache_get, put as cache_put

    cached = cache_get(code)
    if cached:
        return cached

    mmdc = _find_mmdc()
    if not mmdc:
        return None

    tmp_in = None
    tmp_out = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".mmd", delete=False, mode="w", encoding="utf-8") as f:
            f.write(code)
            tmp_in = f.name
        tmp_out = tmp_in.replace(".mmd", ".png")

        cmd = [mmdc, "-i", tmp_in, "-o", tmp_out, "-b", "white", "-s", "2"]
        if mmdc.endswith("npx") or mmdc.endswith("npx.cmd"):
            cmd = [mmdc, "mmdc", "-i", tmp_in, "-o", tmp_out, "-b", "white", "-s", "2"]

        subprocess.run(cmd, check=True, capture_output=True, timeout=30,
                       creationflags=subprocess.CREATE_NO_WINDOW)

        if os.path.exists(tmp_out):
            with open(tmp_out, "rb") as img:
                png_b64 = base64.b64encode(img.read()).decode("ascii")
            cache_put(code, png_b64)
            return png_b64
    except Exception:
        return None
    finally:
        for f in (tmp_in, tmp_out):
            if f and os.path.exists(f):
                os.remove(f)
    return None
