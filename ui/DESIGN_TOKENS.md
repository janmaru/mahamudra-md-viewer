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

### Sintassi Markdown (editor)
Colori dei tag applicati al `tk.Text` dell'editor (`constants.MD_SYNTAX_DARK` / `MD_SYNTAX_LIGHT`, tag definiti in `services/md_highlighter.py`).

| Tag | Dark | Light | Uso |
| :--- | :--- | :--- | :--- |
| `md_heading` | `#569cd6` (bold) | `#800000` (bold) | Righe `#`…`######`. |
| `md_bold` / `md_italic` | testo base, bold / italic | testo base, bold / italic | `**x**`, `*x*`. |
| `md_code` / `md_code_block` | `#ce9178` | `#a31515` | Code span e contenuto dei blocchi fenced. |
| `md_fence` | `#6a9955` | `#008000` | Righe ``` / ~~~. |
| `md_link` / `md_image` | `#9cdcfe` | `#0451a5` | `[testo](url)`, `![alt](src)`. |
| `md_url` | `#808080` | `#808080` | Parte URL di link e immagini. |
| `md_list` / `md_hr` / `md_table` | `#6796e6` | `#0451a5` | Marcatori di lista, righe orizzontali, pipe di tabella. |
| `md_quote` | `#6a9955` (italic) | `#008000` (italic) | Righe `>`. |
| `md_html` | `#808080` | `#800000` | Tag HTML inline. |

### Gutter e riga corrente
| Elemento | Colore | Note |
| :--- | :--- | :--- |
| Numeri di riga | `secondary` | Riga del cursore: `text_bright`. Font mono, un punto più piccolo dell'editor. |
| Sfondo del gutter | `bg` | Stesso sfondo dell'editor: nessuna linea di separazione. |
| Riga corrente | `hover` | Solo `background`, priorità più bassa di selezione e ricerca. |

I tag di sintassi hanno priorità inferiore ai tag di ricerca (`search_match`, `search_current`), che quindi restano visibili sopra la colorazione.

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
