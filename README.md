Friedrich
=========

A Windows Markdown viewer built on Tkinter. Renders Markdown with native
diagram support (Mermaid, inline SVG), themed CSS, an on-disk diagram cache,
PDF export through headless Edge, and an RSVP sentence reader for `.rd`
companion files.


Stack
-----

| Component        | Implementation                                              |
|------------------|-------------------------------------------------------------|
| Window / UI      | Tkinter (`tk`, `ttk`)                                       |
| HTML rendering   | `tkinterweb.HtmlFrame`                                      |
| Markdown parser  | `markdown` (extensions: `tables`, `fenced_code`, `sane_lists`) |
| Mermaid          | `mmdc` (Node) — optional, fallback to fenced code           |
| Inline SVG       | `resvg-py` rasterized to PNG for `tkinterweb` compatibility |
| PDF export       | `msedge.exe --headless --print-to-pdf`                      |
| PDF preview      | `pypdfium2`                                                 |
| Persistence      | `settings.json` (zoom, theme, recents, bookmarks)           |
| Diagram cache    | SHA-256 keyed `.b64` files under `.diagram_cache/<doc_stem>/` |


Architecture
------------

Three layers:

*   **Presentation** — `md_reader.py` orchestrates the Tk root, key bindings,
    and lifecycle. `widgets/` holds Toolbar, Sidebar, NavRail, TabManager,
    SearchBar, EmptyState, DiagramViewer, CustomMenu.
*   **Services** — `services/` contains `file_renderer`, `mermaid_processor`,
    `svg_processor`, `diagram_cache`, `log_renderer`, `pdf_exporter`,
    `css_loader`, `rd_parser`, `file_scanner`.
*   **Domain & Application** — `domain/` (models and parsing services for
    `.rd` files and log lines) and `application/use_cases/` (file refresh,
    log rendering, markdown export).

Diagram pipeline:

1.  Synchronous Markdown render replaces Mermaid blocks and inline SVG blocks
    with HTML placeholders so the page paints immediately.
2.  A daemon thread re-runs the parsers, renders each diagram block to PNG
    bytes, and base64-encodes them.
3.  Each diagram is keyed by `sha256(source)` and persisted at
    `.diagram_cache/<doc_stem>/<hash>.b64`. Cache hits skip the render.
4.  The worker schedules `root.after(0, ...)` to swap placeholders for the
    final `<img>` tags on the UI thread.

Refresh (`Ctrl+R`, menu) and Clear Cache are gated while a render is in
flight: the menu entries appear disabled and the handlers early-return with
a toast. The counter `AppContext.diagram_render_in_flight` is incremented
before spawning the worker and decremented in a `try/finally` callback
marshalled back to the UI thread, so the gate releases on success, error,
or no-op.

Project Structure
-----------------

```
md_viewer/
├── md_reader.py              # Entry point, Tk root, key bindings
├── rd_viewer.py              # Standalone RSVP player for .rd files
├── app_context.py            # Shared state (TabInfo, AppContext)
├── settings_manager.py       # settings.json load/save
├── constants.py              # APP_DIR, fonts, version, paths
├── requirements.txt
├── VERSION
├── launch_en.sh              # Launch with --lang en
├── launch_it.sh              # Launch with --lang it
├── md_viewer.spec            # PyInstaller spec
├── application/
│   └── use_cases/            # refresh_filesystem, render_log_file, export_markdown
├── domain/
│   ├── models/               # FileInfo, LogLine, TreeNode
│   └── services/             # log_parser
├── presentation/
│   └── controllers/          # main_controller, tab_controller
├── services/
│   ├── file_renderer.py      # Markdown + diagrams orchestration
│   ├── mermaid_processor.py  # mmdc → PNG (base64)
│   ├── svg_processor.py      # inline SVG → PNG (base64)
│   ├── diagram_cache.py      # SHA-256 disk cache, per-doc subdirs
│   ├── pdf_exporter.py       # Edge headless --print-to-pdf
│   ├── log_renderer.py       # .log files
│   ├── rd_parser.py          # .rd file parser
│   ├── css_loader.py         # build_html with theme CSS
│   └── file_scanner.py       # filesystem tree builder
├── widgets/
│   ├── toolbar.py            # Top bar, menus
│   ├── sidebar.py            # File tree + bookmarks + recents
│   ├── nav_rail.py           # Tab dock
│   ├── tab_manager.py        # Multi-tab orchestration
│   ├── custom_menu.py        # Themed popup menu
│   ├── diagram_viewer.py     # Click-to-zoom diagram modal
│   ├── search_bar.py         # In-page text search
│   ├── empty_state.py        # Home screen
│   ├── tooltip.py            # Generic tooltip
│   └── listbox_tooltip.py    # Tooltip on Listbox rows
├── i18n/                     # en.json, it.json
├── styles/                   # Markdown CSS themes
├── ui/                       # UI_STRUCTURE.md, DESIGN_TOKENS.md, COMPONENT_CONTRACTS.md
├── docs/                     # technical_analysis.md, functional_analysis.md, i18n.md
├── scripts/                  # mermaid.min.js
├── assets/                   # Static resources
├── errors/                   # Error views and templates
└── tests/                    # Test scratch
```


Quick Start
-----------

Requires Python 3.10+, Microsoft Edge (for PDF export). Node.js with `mmdc`
is optional and only needed if Mermaid blocks are present.

```bash
python -m venv .venv
./.venv/Scripts/pip install -r requirements.txt

# Launch
./launch_en.sh           # English
./launch_it.sh           # Italian

# Manual
./.venv/Scripts/python md_reader.py --lang en
./.venv/Scripts/python md_reader.py --help
```


Diagram Engines
---------------

**Mermaid** uses the external `mmdc` CLI when available. Each block is
written to a temp file and rendered to PNG; the base64 is embedded in the
HTML. If `mmdc` is missing, blocks fall back to a fenced code block.

**Inline SVG** blocks are rasterized through `resvg-py` because `tkinterweb`
does not reliably render embedded SVG fragments directly.

Both renderers share the same disk cache under `.diagram_cache/<doc_stem>/`.
Entries are `<sha256>.b64` files containing the base64 PNG payload. The
cache is invalidated for the current document on Refresh, and globally on
Clear Cache (menu Tools).


RSVP Companion (`.rd`)
----------------------

A `.rd` file placed next to a `.md` with the same base name appears nested
under it in the explorer and opens an RSVP (Rapid Serial Visual
Presentation) player tab. Orphan `.rd` files (no matching `.md`) appear as
top-level entries.

Format: one sentence per line, blank lines ignored. Inline Markdown is
preserved for emphasis (`*italic*`, `**bold**`, `` `code` ``). Block-level
Markdown (headers, lists, fences, images, tables) is stripped. Sentence
splitting is the author's responsibility — the player reads lines verbatim.

Player controls: Play, Pause, Prev, Next, Stop, plus a WPM slider
(200–1200, default 300). Per-sentence duration is computed from WPM and
word count.

Standalone player:

```bash
./.venv/Scripts/python rd_viewer.py path/to/file.rd --wpm 400
```


PDF Export
----------

`Tools → Export PDF` writes the current Markdown rendering to PDF via Edge
in headless mode. The exporter probes the standard Edge install paths
(`%ProgramFiles%`, `%ProgramFiles(x86)%`, `%LocalAppData%`) before falling
back to `msedge` on `PATH`. The output mirrors the preview, including
diagrams already rendered to PNG.


Localization
------------

```bash
md_reader.py --lang en        # English (default)
md_reader.py --lang it        # Italian
```

Strings live in `i18n/<lang>.json`. See [i18n guide](docs/i18n.md) for the
key convention and instructions for adding a locale.


Documentation
-------------

*   [Technical Analysis](docs/technical_analysis.md) — architecture, services, data flow.
*   [Functional Analysis](docs/functional_analysis.md) — features, user flows, requirements.
*   [Internationalization](docs/i18n.md) — locale files and translation workflow.
*   [UI Structure](ui/UI_STRUCTURE.md) — widget hierarchy and layout rules.
*   [Design Tokens](ui/DESIGN_TOKENS.md) — colors, typography, spacing.
*   [Component Contracts](ui/COMPONENT_CONTRACTS.md) — widget behaviors and dimensions.


Credits
-------

App icon: portrait from the Augustale of Frederick II (Italian *Federico*,
German *Friedrich* — hence the name). Author: [janmaru](https://janmaru.github.io).
