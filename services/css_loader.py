"""Loads CSS from disk and assembles complete HTML documents."""

from pathlib import Path
from string import Template
from typing import Optional

HTML_WRAPPER = Template("""\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
$base_tag
<style>
$css
body {
    max-width: 1100px !important;
    margin: 0 auto !important;
    padding: 40px 60px !important;
}
@media (max-width: 1200px) {
    body {
        max-width: 95% !important;
        padding: 20px 30px !important;
    }
}
.table-container {
    width: 100%;
    overflow-x: auto;
    margin-bottom: 25px;
    border: 1px solid rgba(128, 128, 128, 0.3);
    border-radius: 4px;
}
table {
    border-collapse: collapse;
    width: 100%;
    font-size: 0.95em;
}
th, td {
    border: 1px solid rgba(128, 128, 128, 0.3);
    padding: 10px 12px;
    text-align: left;
}
th {
    background-color: rgba(128, 128, 128, 0.1);
    font-weight: 600;
}
tr:nth-child(even) {
    background-color: rgba(128, 128, 128, 0.03);
}

/* Image styles */
img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 1em auto;
}

/* Scrollbar styles for better UI integration */
::-webkit-scrollbar {
    width: 10px;
    height: 10px;
}
::-webkit-scrollbar-track {
    background: transparent;
}
::-webkit-scrollbar-thumb {
    background: rgba(128, 128, 128, 0.3);
    border-radius: 5px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(128, 128, 128, 0.5);
}

/* Diagram interactive styles */
.diagram-container {
    cursor: zoom-in;
    transition: opacity 0.2s;
}
.diagram-container:hover {
    opacity: 0.9;
}

/* Print styles for PDF export */
@media print {
    body {
        max-width: 100% !important;
        padding: 0 !important;
        margin: 0 !important;
        zoom: 1 !important;
        -moz-transform: none !important;
        font-size: 100% !important;
    }
    html {
        font-size: 100% !important;
    }

    /* Tables: prevent splitting rows across pages */
    .table-container {
        overflow-x: visible !important;
        page-break-inside: auto;
        break-inside: auto;
    }
    table {
        page-break-inside: auto;
        break-inside: auto;
        font-size: 0.85em;
    }
    tr {
        page-break-inside: avoid;
        break-inside: avoid;
    }
    thead {
        display: table-header-group;
    }

    /* Code blocks: visible overflow, avoid breaks */
    pre {
        overflow-x: visible !important;
        white-space: pre-wrap !important;
        word-wrap: break-word !important;
        page-break-inside: avoid;
        break-inside: avoid;
    }

    /* Images and diagrams: keep together, fit page */
    img {
        page-break-inside: avoid;
        break-inside: avoid;
        max-width: 100% !important;
        max-height: 8in !important;
    }
    .mermaid-container,
    .diagram-container {
        page-break-inside: avoid;
        break-inside: avoid;
        text-align: center;
    }
    .mermaid-container a,
    .diagram-container a {
        pointer-events: none;
        text-decoration: none;
        color: inherit;
        cursor: default;
    }
    img[style*="zoom-in"] {
        cursor: default !important;
    }

    /* Headings: stay with following content */
    h1, h2, h3, h4, h5, h6 {
        page-break-after: avoid;
        break-after: avoid;
    }

    /* Paragraphs: avoid orphans/widows */
    p {
        orphans: 3;
        widows: 3;
    }
}
</style>
</head>
<body>
$body
</body>
</html>
""")


def load_css(path: Optional[Path]) -> str:
    """Read a CSS file and return its contents as a string."""
    if path and path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def build_html(md_body: str, css_path: Optional[Path], base_url: str = "", zoom: int = 100) -> str:
    """Assembles the full HTML document with CSS and the rendered markdown body."""
    css = load_css(css_path)
    base_tag = f'<base href="{base_url}">' if base_url else ""
    
    # POWER ZOOM STRATEGY:
    # 1. Scale the root font size
    # 2. Use the CSS zoom property (widely supported)
    # 3. Force body font-size with !important as ultimate fallback
    zoom_val = zoom / 100.0
    zoom_style = f"""
    html {{ font-size: {zoom}%; }}
    body {{ 
        zoom: {zoom_val}; 
        -moz-transform: scale({zoom_val}); 
        -moz-transform-origin: 0 0;
        font-size: {zoom}% !important; 
    }}
    """

    return HTML_WRAPPER.substitute(
        css=css + "\n" + zoom_style,
        body=md_body,
        base_tag=base_tag,
    )
