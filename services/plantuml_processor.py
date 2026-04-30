"""
PlantUML diagram processing service.
Pre-renders PlantUML blocks (including Salt wireframes) to PNG via plantuml.jar
and embeds them as base64 images.
"""

import re
import subprocess
import tempfile
import os
import base64
from pathlib import Path

from constants import APP_DIR

# Regex for PlantUML fenced code blocks (```plantuml ... ```)
PLANTUML_PATTERN = r'```plantuml\s*(.*?)\s*```'

# Path to plantuml.jar bundled in scripts/
_PLANTUML_JAR = APP_DIR / "scripts" / "plantuml.jar"


def process_plantuml_blocks(content: str) -> tuple[str, list[str]]:
    """
    Find all plantuml blocks in the markdown content and replace them
    with placeholders for later injection.
    """
    plantuml_blocks: list[str] = []

    def save_plantuml(match: re.Match) -> str:
        code = match.group(1).strip()
        plantuml_blocks.append(code)
        return f"<!--PLANTUML_{len(plantuml_blocks)-1}-->"

    processed_content = re.sub(PLANTUML_PATTERN, save_plantuml, content, flags=re.DOTALL)
    return processed_content, plantuml_blocks


def inject_plantuml_placeholders(html: str, plantuml_blocks: list[str]) -> str:
    """Replace plantuml placeholders with loading indicators."""
    for i, code in enumerate(plantuml_blocks):
        tag = ('<div class="mermaid-container" style="padding:40px;color:#888;'
               'font-style:italic;text-align:center;">Rendering diagram...</div>')
        html = html.replace(f"<!--PLANTUML_{i}-->", tag)
        html = html.replace(f"<p><!--PLANTUML_{i}--></p>", tag)
    return html


def inject_plantuml_images(html: str, plantuml_blocks: list[str],
                           diagram_registry: dict | None = None) -> str:
    """
    Replace plantuml placeholders with pre-rendered PNG images (base64).
    Falls back to raw code block if rendering fails.
    If diagram_registry is provided, stores base64 data and wraps images in clickable links.
    """
    for i, code in enumerate(plantuml_blocks):
        png_b64 = _render_plantuml_to_png_b64(code)
        if png_b64:
            if diagram_registry is not None:
                key = f"d{len(diagram_registry)}"
                diagram_registry[key] = png_b64
                tag = (f'<div class="mermaid-container">'
                       f'<a href="diagram:{key}" title="Click to zoom">'
                       f'<img src="data:image/png;base64,{png_b64}" alt="PlantUML diagram" '
                       f'style="cursor:zoom-in">'
                       f'</a></div>')
            else:
                tag = (f'<div class="mermaid-container">'
                       f'<img src="data:image/png;base64,{png_b64}" alt="PlantUML diagram">'
                       f'</div>')
        else:
            tag = f'<div class="mermaid-container"><pre>{code}</pre></div>'
        html = html.replace(f"<!--PLANTUML_{i}-->", tag)
        html = html.replace(f"<p><!--PLANTUML_{i}--></p>", tag)

    return html


def _find_java() -> str | None:
    """Locate the java executable."""
    import shutil
    return shutil.which("java")


def _render_plantuml_to_png_b64(code: str) -> str | None:
    """Render a PlantUML diagram to PNG and return base64-encoded string. Uses disk cache."""
    from services.diagram_cache import get as cache_get, put as cache_put

    cached = cache_get(code)
    if cached:
        return cached

    java = _find_java()
    if not java or not _PLANTUML_JAR.exists():
        return None

    tmp_in = None
    tmp_out = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".puml", delete=False, mode="w", encoding="utf-8") as f:
            f.write(code)
            tmp_in = f.name
        tmp_out = tmp_in.replace(".puml", ".png")

        cmd = [java, "-jar", str(_PLANTUML_JAR), "-tpng", "-o", os.path.dirname(tmp_out), tmp_in]

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
