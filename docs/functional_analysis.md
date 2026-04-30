# Functional Analysis - Friedrich - Document Reader

## Project Goal
Friedrich - Document Reader is a modern, lightweight Markdown viewer designed to deliver a Visual Studio Code–like experience, focused on reading, navigating, and presenting complex technical documentation.

## Main Features

### 1. Multimodal Viewing
- **HTML Preview**: Faithful Markdown rendering with support for custom CSS themes.
- **Source (Editor)**: Raw source view with text highlighting and advanced search.
- **Zen Mode**: Full-screen mode that hides menus and sidebar for distraction-free reading (toggled with F11 or Esc).

### 2. Rich Content Handling
- **Diagrams**: Native support for Mermaid (flowchart, sequence, gantt) and PlantUML (including Salt wireframes).
- **Tables and Images**: Full support for responsive tables and direct viewing of image files (PNG, JPG, etc.).
- **CSV Viewer**: Automatic rendering of CSV files as formatted HTML tables.

### 3. Navigation and UX
- **Triple Panel Layout**:
    - **Recent Files**: Quick access to the last 10 opened documents.
    - **Explorer**: File system tree navigation with instant search filters.
    - **Viewer**: Central reading area.
- **UI Theme**: Both **Dark** (VS Code inspired) and **Light** interface themes.
- **History**: "Back" navigation to return to previously viewed documents.
- **Anchor Navigation**: Supports fragment links both intra-document (`[entry](#anchor)`) and cross-document (`[entry](other.md#anchor)`). The viewer loads the target file and scrolls directly to the requested anchor. Heading IDs can be supplied via inline HTML tags (`<a id="...">`) already present in the Markdown source.

### 4. Tools and Integrations
- **PDF Export**: Print-ready PDF generation, including rendered diagrams.
- **Search**: Integrated search engine (Ctrl+F) that works in both preview and source modes.
- **Copy**: Button to quickly copy file content to the clipboard.

### 5. Sidebar Toggle (Ctrl+B)
- **Feature**: Show/hide the sidebar to maximize the reading area.
- **Behavior**:
  - Hide: Removes the pane from the `PanedWindow` and saves its width.
  - Show: Reinserts the pane and restores the saved width.
- **Icon feedback**: The nav_rail icon switches color (accent/secondary) to reflect the current state.
- **Shortcut**: Ctrl+B or click on the "☰" icon in the nav_rail.
