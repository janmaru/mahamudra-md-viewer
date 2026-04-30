# Design Tokens & Aesthetic Standards

Questo documento definisce l'identità visiva del Friedrich - Document Reader, ispirata all'approccio minimalista e funzionale di Obsidian.

## 🎨 Palette Colori

### Light Mode (Primary)
*Priorità del progetto: Estetica pulita, contrasti morbidi.*

| Token | Valore | Uso |
| :--- | :--- | :--- |
| `bg` | `#ffffff` | Sfondo principale area di lavoro. |
| `sidebar` | `#f6f6f6` | Sfondo explorer e NavRail. |
| `accent` | `#7c3aed` | Colore focus, icone attive (Obsidian Purple). |
| `border` | `#e8e8e8` | Separatori sottili, bordi tab. |
| `text` | `#5c5c5c` | Testo secondario, etichette. |
| `text_bright`| `#222222` | Titoli, testo attivo, contenuto markdown. |

### Dark Mode
| Token | Valore | Uso |
| :--- | :--- | :--- |
| `bg` | `#1e1e1e` | Sfondo principale (VS Code style). |
| `accent` | `#007acc` | Colore focus (Classic Blue). |
| `text` | `#cccccc` | Colore testo standard. |

## ⌨️ Tipografia

| Tipo | Font | Dimensione | Peso |
| :--- | :--- | :--- | :--- |
| **UI Interface** | Segoe UI / System | 10pt (std), 9pt (sidebar) | Normal |
| **UI Headers** | Segoe UI / System | 11pt | Bold |
| **Editor / Code** | Consolas / Mono | 11pt (base) | Normal |

## 📐 Spaziature (Dimensions)

- **NavRail Width:** 48px
- **Sidebar Min-Width:** 220px
- **Tab Height:** 34px
- **Breadcrumb Height:** 38px
- **Status Bar Height:** 22px
- **Standard Padding (Empty State):** relx=0.5, rely=0.45 (centratura ottica Obsidian).

## ✨ Elementi Distintivi
1. **No Grids:** Preferire `pack` per layout fluidi e `place` per centratura assoluta (es. Empty State).
2. **Hand Cursor:** Tutti gli elementi interattivi (icone, tab, bookmarks) devono avere `cursor="hand2"`.
3. **Hover Feedback:** Ogni elemento cliccabile deve cambiare colore o opacità all'evento `<Enter>`.
