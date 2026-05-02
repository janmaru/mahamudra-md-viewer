# Friedrich - Document Reader

A modern, VS Code-inspired Markdown viewer with a three-panel layout, theme support, and integrated diagram rendering.

## 🏗️ Architecture

The project follows a modular 3-tier architecture:
- **Presentation Layer**: `md_reader.py` (Tkinter UI and Event management).
- **Service Layer**: `services/` (CSS loading, Diagram processing, Caching).
- **Infrastructure**: System-level integration (Edge PDF, Java JRE, File System).

### 🎨 UI Design System
To ensure UI stability and prevent regressions, refer to the following documentation:
- [UI Structure Blueprint](ui/UI_STRUCTURE.md) - Hierarchy and layout rules.
- [Design Tokens](ui/DESIGN_TOKENS.md) - Colors, typography, and spacing.
- [Component Contracts](ui/COMPONENT_CONTRACTS.md) - Widget behaviors and dimensions.

## 🚀 Key Features

- **Themed UI**: Dark and Light modes for the application interface.
- **Markdown Themes**: Multiple CSS styles (VS Code Dark, Industrial, French Revolution).
- **Diagram Engines**: Native support for **Mermaid** and **PlantUML**.
- **PDF Export**: High-fidelity PDF generation via headless Edge.
- **Smart Explorer**: File system tree with live filtering and recent files history.
- **Zen Mode**: Distraction-free reading (F11/Esc).
- **⚡ RSVP Reader**: Companion `.rd` files render as a sentence-by-sentence speed reader (200–1200 WPM).
- **🌍 Multi-Language Support**: English and Italian via CLI parameter.

## 📚 Documentation

For more detailed information, see the `docs/` folder:
- [Technical Analysis](docs/technical_analysis.md)
- [Functional Analysis](docs/functional_analysis.md)
- [Internationalization (i18n)](docs/i18n.md) - Language support guide

## 🛠️ Requirements

- **Python 3.10+**
- **Java JRE** (for PlantUML diagrams)
- **Node.js + mmdc** (optional, for Mermaid diagrams)
- **Microsoft Edge** (for PDF Export)

## 📦 Installation

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```

2. Install dependencies:
   ```bash
   # On Windows (Git Bash or PowerShell)
   ./.venv/Scripts/pip install -r requirements.txt
   
   # On Linux/macOS
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

## 🚀 Usage

The easiest way to launch the application is using the provided bash scripts:

```bash
# Launch in Italian
./launch_it.sh

# Launch in English
./launch_en.sh
```

### Manual Usage
```bash
# English
./.venv/Scripts/python md_reader.py --lang en

# Italian
./.venv/Scripts/python md_reader.py --lang it
```

### Help
```bash
./.venv/Scripts/python md_reader.py --help
```

## ⚡ RSVP Companion Files (`.rd`)

Friedrich supports **`.rd` companion files** — short, hand-written summaries
that play next to a Markdown document as a [RSVP](https://en.wikipedia.org/wiki/Rapid_serial_visual_presentation)-style
sentence reader (one sentence at a time, configurable WPM).

### File pairing

Place a `.rd` file next to a `.md` with the **same base name**:

```
docs/
  architecture.md
  architecture.rd        ← companion summary
  deployment.md          ← no companion
  loose.rd               ← orphan, opens standalone
```

In the explorer, the `.rd` appears **nested under its `.md`**. Orphan `.rd`
files (no matching `.md`) appear as top-level documents and open the same
RSVP player.

### `.rd` format

One sentence per line. Empty lines are ignored. Inline Markdown is supported
for emphasis only:

```
La lettura veloce è una disciplina, non un trucco.
Si fonda su tre leve che agiscono insieme.

L'occhio fa salti chiamati *saccadi*.
Tra una saccade e l'altra c'è una breve **fissazione**.
La velocità si misura in `WPM` (words per minute).
```

Block-level Markdown (headers, lists, code fences, images, tables) is
stripped. The reader does **not** infer sentence boundaries — splitting is
the author's responsibility, line by line.

### Player

Selecting a `.rd` in the tree opens it as a regular tab containing the RSVP
player: ▶ Play / ⏸ Pause / ⏮ Prev / ⏭ Next / ⏹ Stop, plus a WPM slider
(200–1200, default 300). Per-sentence duration is computed from the WPM
setting and the sentence word count.

### Standalone player

You can also run the player on a single `.rd` outside the main viewer:

```bash
./.venv/Scripts/python rd_viewer.py path/to/file.rd --wpm 400
```

## 🌍 Localization

The application supports multiple languages via command-line parameters:

- **en** - English (default)
- **it** - Italiano (Italian)

See [i18n Documentation](docs/i18n.md) for detailed information about:
- Adding new languages
- Translating UI strings
- Using translations in code

## 📄 Credits

- App icon: portrait from the **Augustale of Frederick II** ("Friedrich" in German — hence the app name).
- Developed by [janmaru](https://janmaru.github.io).
