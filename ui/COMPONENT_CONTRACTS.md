# Component Contracts

Ogni widget deve rispettare i seguenti contratti di implementazione per garantire la stabilità della UI.

## 🗂️ Widget Registry

### 1. NavRail (`widgets/nav_rail.py`)
- **Stato:** Fixed.
- **Dimensione:** 48px larghezza.
- **Responsabilità:** Switcher di alto livello (Sidebar, Zen, Theme).
- **Contratto:** Deve emettere eventi verso il `MainController` senza gestire logica di business.

### 2. SidePanel (`widgets/sidebar.py`)
- **Stato:** Flexible (dentro PanedWindow).
- **Contratto:** 
    - Deve supportare 3 viste: Explorer, Bookmarks, Search.
    - La ricerca deve essere istantanea e filtrare il `tree_cache`.

### 3. TabManager (`widgets/tab_manager.py`)
- **Stato:** Master of Workspace.
- **Contratto:**
    - Deve gestire il ciclo di vita dei `TabInfo`.
    - Gestione dello scroll orizzontale automatico se le tab eccedono la larghezza.
    - Sincronizzazione dei Breadcrumbs con il path della tab attiva.
    - Possiede il `ViewPaned` di ogni tab documento e ne applica il `view_mode` (`preview` / `source` / `split`) tramite `apply_view_mode`; centra il sash in `split`.
    - Crea il `MarkdownHighlighter` per ogni editor e installa i binding tastiera dell'editor ricevuti dall'orchestratore (`source_key_bindings`).
    - Notifica l'orchestratore delle modifiche da tastiera tramite `on_source_changed` (hook della live preview).

### 4. EmptyState (`widgets/empty_state.py`)
- **Stato:** Overlay/Placeholder.
- **Contratto:**
    - Deve apparire quando `open_tabs` è vuota.
    - Centratura assoluta tramite `place`.
    - Deve fornire accesso rapido ai tasti di scelta rapida.

### 5. SearchBar (`widgets/search_bar.py`)
- **Stato:** Contextual (per Tab).
- **Contratto:** Appare sopra il viewer, non deve rubare spazio al contenuto se non invocata.

### 6. EditorActions (`widgets/editor_actions.py`)
- **Stato:** Stateless (opera sulla tab attiva).
- **Contratto:**
    - Espone i comandi del menu Modifica (undo/redo, appunti, formattazione Markdown).
    - `can_edit()` è `False` quando l'editor non è visibile (`preview`, PDF, RSVP, home): il menu deve disabilitare le voci.
    - Ogni comando di formattazione è un singolo passo di undo (`Text.replace`) e delega la trasformazione alle funzioni pure di `services/md_editing.py`.

### 7. LineNumbers (`widgets/line_numbers.py`)
- **Stato:** Fixed (larghezza calcolata).
- **Contratto:**
    - Un numero per riga logica, allineato alla **prima** riga visiva in caso di a capo automatico: misurare sempre `dlineinfo("N.0")`, mai un indice con colonna.
    - Ridisegno coalescato con `after_idle`; non deve mai ridisegnare in modo sincrono durante lo scroll.
    - Larghezza ricalcolata da cifre e font; segue lo zoom tramite `set_font_size`.

### 8. CurrentLineHighlight (`widgets/current_line.py`)
- **Stato:** Stateless (tag sul `tk.Text`).
- **Contratto:**
    - Imposta solo `background`, mai `foreground`: non deve interferire con l'evidenziazione della sintassi.
    - Il tag resta in fondo alla pila di priorità: selezione e risultati di ricerca restano visibili sopra.

## 🔄 Flusso di Comunicazione
I widget **non comunicano mai direttamente** tra loro. Utilizzano l' `AppContext` come bus di dati e callback fornite dal `MarkdownReader` per triggerare azioni globali.
