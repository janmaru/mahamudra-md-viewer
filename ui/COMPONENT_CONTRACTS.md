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

### 4. EmptyState (`widgets/empty_state.py`)
- **Stato:** Overlay/Placeholder.
- **Contratto:**
    - Deve apparire quando `open_tabs` è vuota.
    - Centratura assoluta tramite `place`.
    - Deve fornire accesso rapido ai tasti di scelta rapida.

### 5. SearchBar (`widgets/search_bar.py`)
- **Stato:** Contextual (per Tab).
- **Contratto:** Appare sopra il viewer, non deve rubare spazio al contenuto se non invocata.

## 🔄 Flusso di Comunicazione
I widget **non comunicano mai direttamente** tra loro. Utilizzano l' `AppContext` come bus di dati e callback fornite dal `MarkdownReader` per triggerare azioni globali.
