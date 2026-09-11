# UI Structure Blueprint

Questo documento descrive la gerarchia dei widget e le regole di layout del Friedrich - Document Reader. Serve come riferimento per prevenire regressioni visive durante le modifiche al codice.

## 🏗️ Gerarchia dei Widget (Layout Map)

L'applicazione utilizza un sistema di annidamento basato principalmente sul manager `pack`, con una `PanedWindow` centrale per la gestione flessibile degli spazi.

```mermaid
graph TD
    Root[tk.Tk - MarkdownReader] --> Toolbar[Toolbar Frame - top, fill:X]
    Root --> Sep1[Separator - top, fill:X]
    Root --> MainCont[MainContainer Frame - fill:BOTH, expand:True]
    Root --> Status[Status Bar Frame - bottom, fill:X]

    MainCont --> NavRail[NavRail Frame - left, fill:Y]
    MainCont --> MainPaned[MainPaned ttk.PanedWindow - horizontal, fill:BOTH, expand:True]

    MainPaned --> Sidebar[SidePanel Frame - weight:1]
    MainPaned --> Workspace[Workspace Container Frame - weight:4]

    Workspace --> TabMgr[TabManager Container - fill:BOTH, expand:True]
    
    TabMgr --> TabHeader[Tab Header Frame - top, fill:X, height:34px]
    TabMgr --> SubHeader[Sub-Header/Breadcrumbs - top, fill:X, height:38px]
    TabMgr --> Sep2[Separator - top, fill:X]
    TabMgr --> Content[Content Area Frame - fill:BOTH, expand:True]

    Content --> EmptyState[EmptyState Frame - fill:BOTH]
    Content --> ActiveTab[Active Tab Container - fill:BOTH]

    ActiveTab --> SearchBar[SearchBar Frame - top, fill:X]
    ActiveTab --> ViewPaned[ViewPaned ttk.PanedWindow - horizontal, fill:BOTH, expand:True]
    ViewPaned --> Editor[Source Frame - weight:1]
    Editor --> Gutter[LineNumbers Canvas - left, fill:Y]
    Editor --> EditorText[tk.Text - left, fill:BOTH, expand:True]
    Editor --> EditorBar[Scrollbar - right, fill:Y]
    ViewPaned --> Viewer[HtmlFrame - weight:1]
```

Le tab PDF e RSVP non hanno `ViewPaned`: il loro widget dedicato è pacchettizzato direttamente nell'`Active Tab Container`.

### Modalità di vista (per tab)

| `view_mode` | Pane presenti in `ViewPaned`      |
| :--- | :--- |
| `preview` | `HtmlFrame` |
| `source` | `Source Frame` |
| `split` | `Source Frame` (sinistra) + `HtmlFrame` (destra), sash al 50% |

`TabManager.apply_view_mode(tab)` è l'unico punto che aggiunge/rimuove i pane; nessun altro componente deve chiamare `pack` su `HtmlFrame` o `Source Frame`.

## 📏 Regole di Espansione (Packing Rules)

| Componente | Manager | Side | Fill | Expand | Note |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Toolbar** | `pack` | TOP | X | False | Altezza fissa definita dai widget interni. |
| **NavRail** | `pack` | LEFT | Y | False | Larghezza fissa (48px). |
| **MainPaned** | `pack` | LEFT | BOTH | True | Contiene il cuore dell'interfaccia. |
| **Sidebar** | `paned` | - | BOTH | - | Weight 1. Larghezza minima suggerita 220px. |
| **Workspace** | `paned` | - | BOTH | - | Weight 4. L'area di lettura principale. |
| **Status Bar** | `pack` | BOTTOM | X | False | Altezza fissa 22px. |

## ⚠️ Vincoli Critici
1. **NavRail Priority:** Deve essere sempre pacchettizzata per prima nel `MainContainer` per occupare l'intera altezza sinistra.
2. **PanedWindow Weights:** Il rapporto Sidebar:Workspace deve rimanere 1:4 per mantenere il focus sul contenuto.
3. **Z-Order:** L' `EmptyState` e l' `ActiveTab` container si alternano nell'area `Content`, uno solo deve essere visibile (pacchettizzato) alla volta.
