# Functional Analysis - Friedrich - Document Reader

## Project Goal
Friedrich - Document Reader is a modern, lightweight Markdown viewer designed to deliver a Visual Studio Code–like experience, focused on reading, navigating, and presenting complex technical documentation.

## Main Features

### 1. Multimodal Viewing
- **HTML Preview**: Faithful Markdown rendering with support for custom CSS themes.
- **Source (Editor)**: Editable source view with Markdown syntax highlighting, undo/redo and in-text search.
- **Split**: Editor on the left and live preview on the right; the preview follows the editor buffer with a short delay.
- **Zen Mode**: Full-screen mode that hides menus and sidebar for distraction-free reading (toggled with F11 or Esc).

The three modes are cycled with the nav rail icon (Preview → Source → Split → Preview). PDF and RSVP tabs have a single fixed view.

### 2. Rich Content Handling
- **Diagrams**: Native support for Mermaid (flowchart, sequence, gantt) and inline SVG diagrams.
- **Tables and Images**: Full support for responsive tables and direct viewing of image files (PNG, JPG, etc.).
- **CSV Viewer**: Automatic rendering of CSV files as formatted HTML tables.

### 3. Navigation and UX
- **Triple Panel Layout**:
    - **Recent Files**: Quick access to the last 10 opened documents.
    - **Explorer**: File system tree navigation with instant search filters. Items are sorted by modification date in descending order (most recently modified first), with folders listed before files. The sort toggle reverses this order.
    - **Viewer**: Central reading area.
- **UI Theme**: Both **Dark** (VS Code inspired) and **Light** interface themes.
- **History**: "Back" navigation to return to previously viewed documents.
- **Anchor Navigation**: Supports fragment links both intra-document (`[entry](#anchor)`) and cross-document (`[entry](other.md#anchor)`). The viewer loads the target file and scrolls directly to the requested anchor. Heading IDs can be supplied via inline HTML tags (`<a id="...">`) already present in the Markdown source.

### 4. Tools and Integrations
- **PDF Export**: Print-ready PDF generation, including rendered diagrams.
- **Search**: Integrated search engine (Ctrl+F) that works in both preview and source modes.
- **Copy**: Button to quickly copy file content to the clipboard.

### 5. Markdown Editor
- **Goal**: let the reader fix or write documentation without leaving the viewer.
- **New document**: *File → New Markdown* (Ctrl+N) opens an untitled tab in source mode; the first save asks for a destination (Save As).
- **Dirty tracking**: any typing marks the tab dirty (● prefix on the tab label). Closing a dirty tab, or the application, asks *Save / Don't save / Cancel*.
- **Save**: Ctrl+S overwrites the file (UTF-8, LF); Ctrl+Shift+S saves a copy under a new name and the tab follows the new path.
- **Buffer rule**: once the editor has been shown, its content is the truth. Switching to preview renders the buffer, not the disk copy; Refresh (Ctrl+R) does not reload a dirty or untitled tab.
- **Live preview**: in split mode the preview re-renders about half a second after the last keystroke, keeping its scroll position. Only Markdown files are live-rendered; log, CSV and code files keep their dedicated renderer.
- **Edit menu**: Undo, Redo, Cut, Copy, Paste, Select All, Bold (Ctrl+Shift+B), Italic (Ctrl+I), Inline Code, Code Block, Link, Heading 1–3, Bullet List, Numbered List, Quote. Entries are disabled when no editor is visible (preview mode, PDF, RSVP, home screen).
- **Formatting semantics**: emphasis commands wrap the selection or unwrap it if already wrapped; with no selection they insert a localized placeholder and select it. List and quote commands act on whole lines and toggle. Heading N replaces an existing level or removes the heading when N is already applied. Link selects the URL placeholder when text was selected, otherwise the text placeholder.
- **Syntax highlighting**: headings, bold, italic, inline code, fenced code, links, images, list markers, quotes, horizontal rules, table pipes, inline HTML. Colors follow the UI theme.
- **Line numbers**: a gutter on the left numbers the logical lines (a wrapped line keeps one number), widens with the document, follows the zoom and marks the line holding the caret. Clicking a number moves the caret to that line.
- **Current line**: the line holding the caret has a discreet background. The selection and the search matches stay visible on top of it.
- **Indentation**: Tab indents the selected lines by one level, or inserts spaces up to the next tab stop when there is no selection; Shift+Tab reverses both. A literal tab character is never inserted (four spaces per level).
- **List continuation**: Enter continues the current bullet, numbered item, task or quote, keeping the indentation and incrementing the number; a new task starts unchecked. Enter on an item that is still empty removes the marker and ends the list. On ordinary text, on a thematic break (`- - -`) and inside a fenced code block Enter behaves normally, so a diff or a code comment starting with a dash is never turned into a list.
- **Preview is read-only**: while the preview is showing, typing cannot reach the editor underneath it. Keyboard shortcuts keep working.
- **Safe writing**: saving goes through a temporary file in the same folder, swapped over the target only once fully written, so an interrupted save never leaves a truncated document. The document keeps its permissions, and file names close to the length limit still save.
- **External changes**: if the file changes on disk while the tab has unsaved edits, the buffer is kept and a toast says so once; Save then asks for confirmation before overwriting the newer disk copy. Clean tabs reload silently, as before.
- **Unsaved work is never overwritten**: no action that re-reads the file (tab switch, anchor link, refresh, theme change) replaces an edited buffer. Anchor links inside a document being edited scroll the preview without reloading. If the file disappears from disk, the unsaved text survives in an untitled tab.
- **Read-only tabs**: images show file metadata in the source view; the text cannot be edited, the Edit menu is disabled and Save reports "nothing to save".
- **Clipboard**: Ctrl+C in the editor copies the selection (standard behaviour). *Tools → Copy Content* copies the whole document.
- **UI theme switch**: rebuilding the interface preserves every open tab, including unsaved edits, untitled documents, view mode, zoom and the active tab.

### 6. Sidebar Toggle (Ctrl+B)
- **Feature**: Show/hide the sidebar to maximize the reading area.
- **Behavior**:
  - Hide: Removes the pane from the `PanedWindow` and saves its width.
  - Show: Reinserts the pane and restores the saved width.
- **Icon feedback**: The nav_rail icon switches color (accent/secondary) to reflect the current state.
- **Shortcut**: Ctrl+B or click on the "☰" icon in the nav_rail.
