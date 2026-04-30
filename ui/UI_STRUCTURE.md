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
    ActiveTab --> Viewer[Viewer/Source Frame - fill:BOTH, expand:True]
```

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
