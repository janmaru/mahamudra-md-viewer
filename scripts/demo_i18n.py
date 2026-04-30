#!/usr/bin/env python
"""
i18n System Demo
Shows the globalization system in action with side-by-side language comparison
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from i18n import I18nManager


def print_header(title):
    """Print a formatted header."""
    width = 80
    print("\n" + "=" * width)
    print(title.center(width))
    print("=" * width)


def demo_ui_screens():
    """Demo 1: Complete UI screens in both languages."""
    print_header("DEMO 1: Complete UI Screens")
    
    i18n_en = I18nManager("en")
    i18n_it = I18nManager("it")
    
    # Simulate different UI screens
    screens = {
        "Window Title": "app.title",
        
        "Menu Bar": [
            ("File", "menu.file"),
            ("Edit", "menu.edit"),
            ("View", "menu.view"),
            ("Tools", "menu.tools"),
        ],
        
        "File Menu Items": [
            ("Open File...", "menu.open_file"),
            ("Open Folder...", "menu.open_folder"),
            ("Export PDF...", "menu.export_pdf"),
            ("Exit", "menu.exit"),
        ],
        
        "Buttons": [
            ("Open", "btn.open"),
            ("Save", "btn.save"),
            ("Cancel", "btn.cancel"),
            ("Close", "btn.close"),
        ],
        
        "Sidebar": [
            ("Explorer", "sidebar.explorer"),
            ("Bookmarks", "sidebar.bookmarks"),
            ("Search", "sidebar.search"),
        ],
        
        "Empty State": [
            ("Title", "empty_state.title"),
            ("Subtitle", "empty_state.subtitle"),
            ("Button", "empty_state.open_file"),
        ],
    }
    
    for section, items in screens.items():
        print(f"\n📌 {section}")
        print("─" * 80)
        
        if isinstance(items, str):
            # Single item
            en_text = i18n_en.t(items)
            it_text = i18n_it.t(items)
            print(f"  EN: {en_text:<50} IT: {it_text}")
        else:
            # Multiple items
            for label, key in items:
                en_text = i18n_en.t(key)
                it_text = i18n_it.t(key)
                if en_text != label:  # Only show if different from label
                    print(f"  {label:<20} EN: {en_text:<30} IT: {it_text}")
                else:
                    print(f"  {label:<20} EN: {en_text:<30} IT: {it_text}")


def demo_error_messages():
    """Demo 2: Error handling in both languages."""
    print_header("DEMO 2: Error Messages & Dialog Boxes")
    
    i18n_en = I18nManager("en")
    i18n_it = I18nManager("it")
    
    test_cases = [
        ("File Not Found", "error.file_not_found", {"path": "C:\\Documents\\readme.md"}),
        ("Permission Denied", "error.permission_denied", {"path": "C:\\System\\config.ini"}),
        ("Invalid Format", "error.invalid_format", {}),
        ("Export Failed", "error.export_failed", {}),
        ("Render Failed", "error.render_failed", {}),
    ]
    
    for title, key, kwargs in test_cases:
        print(f"\n⚠️  {title}")
        en_msg = i18n_en.t(key, **kwargs)
        it_msg = i18n_it.t(key, **kwargs)
        print(f"  EN: {en_msg}")
        print(f"  IT: {it_msg}")


def demo_success_messages():
    """Demo 3: Success messages and toasts."""
    print_header("DEMO 3: Success Messages & Notifications")
    
    i18n_en = I18nManager("en")
    i18n_it = I18nManager("it")
    
    test_cases = [
        ("File Opened", "success.file_opened", {"name": "readme.md"}),
        ("PDF Exported", "success.pdf_exported", {}),
        ("Cache Cleared", "success.cache_cleared", {}),
        ("Copied to Clipboard", "toast.copied", {}),
        ("Saving", "toast.saving", {}),
        ("Saved Successfully", "toast.saved", {}),
    ]
    
    for title, key, kwargs in test_cases:
        print(f"\n✅ {title}")
        en_msg = i18n_en.t(key, **kwargs)
        it_msg = i18n_it.t(key, **kwargs)
        print(f"  EN: {en_msg}")
        print(f"  IT: {it_msg}")


def demo_status_bar():
    """Demo 4: Status bar information."""
    print_header("DEMO 4: Status Bar Information")
    
    i18n_en = I18nManager("en")
    i18n_it = I18nManager("it")
    
    status_info = [
        ("Unsaved Changes", "status.unsaved_changes", {}),
        ("Read-only", "status.read_only", {}),
        ("Line Count", "status.lines", {"count": 42}),
        ("Word Count", "status.words", {"count": 156}),
        ("Character Count", "status.chars", {"count": 1024}),
    ]
    
    print(f"\n{'Status Item':<25} {'English':<50} {'Italian':<50}")
    print("─" * 125)
    
    for label, key, kwargs in status_info:
        en_text = i18n_en.t(key, **kwargs)
        it_text = i18n_it.t(key, **kwargs)
        print(f"{label:<25} {en_text:<50} {it_text:<50}")


def demo_keyboard_shortcuts():
    """Demo 5: Keyboard shortcuts reference."""
    print_header("DEMO 5: Keyboard Shortcuts Reference")
    
    i18n_en = I18nManager("en")
    i18n_it = I18nManager("it")
    
    shortcuts = [
        ("Open file", "shortcuts.open_file", "Ctrl + O"),
        ("Change folder", "shortcuts.change_folder", "Ctrl + Shift + O"),
        ("Toggle sidebar", "shortcuts.toggle_sidebar", "Ctrl + B"),
        ("Zen mode", "shortcuts.zen_mode", "F11 / Alt + Z"),
        ("Zoom in", "shortcuts.zoom_in", "Ctrl + Scroll"),
        ("Zoom out", "shortcuts.zoom_out", "Ctrl + Scroll"),
        ("Go back", "shortcuts.go_back", "Ctrl + ["),
    ]
    
    print(f"\n{'Action':<25} {'English':<35} {'Italian':<35} {'Shortcut':<20}")
    print("─" * 115)
    
    for label, key, shortcut in shortcuts:
        en_text = i18n_en.t(key)
        it_text = i18n_it.t(key)
        print(f"{label:<25} {en_text:<35} {it_text:<35} {shortcut:<20}")


def demo_dialog_buttons():
    """Demo 6: Common dialog buttons and confirmations."""
    print_header("DEMO 6: Dialog Buttons & Confirmations")
    
    i18n_en = I18nManager("en")
    i18n_it = I18nManager("it")
    
    dialogs = [
        ("Select Folder", "dialog.select_folder"),
        ("Select File", "dialog.select_file"),
        ("Save As", "dialog.save_as"),
        ("Confirm", "dialog.confirm"),
        ("Error", "dialog.error"),
        ("Warning", "dialog.warning"),
        ("Information", "dialog.info"),
    ]
    
    print(f"\n{'Dialog Type':<20} {'English':<35} {'Italian':<35}")
    print("─" * 90)
    
    for label, key in dialogs:
        en_text = i18n_en.t(key)
        it_text = i18n_it.t(key)
        print(f"{label:<20} {en_text:<35} {it_text:<35}")


def demo_language_stats():
    """Demo 7: Language statistics and comparison."""
    print_header("DEMO 7: Language Statistics & Validation")
    
    i18n_en = I18nManager("en")
    i18n_it = I18nManager("it")
    
    en_keys = set(i18n_en.strings.keys())
    it_keys = set(i18n_it.strings.keys())
    
    print(f"\n📊 Language Coverage:")
    print(f"   English keys:      {len(en_keys)}")
    print(f"   Italian keys:      {len(it_keys)}")
    print(f"   Common keys:       {len(en_keys & it_keys)}")
    print(f"   Coverage:          {len(en_keys & it_keys) / len(en_keys) * 100:.1f}%")
    
    if en_keys == it_keys:
        print(f"\n   ✅ Both languages have identical key sets!")
    else:
        missing = en_keys - it_keys
        extra = it_keys - en_keys
        if missing:
            print(f"\n   ⚠️  Missing from Italian: {missing}")
        if extra:
            print(f"\n   ⚠️  Extra in Italian: {extra}")
    
    # Sample average text lengths
    en_avg = sum(len(v) for v in i18n_en.strings.values()) / len(i18n_en.strings)
    it_avg = sum(len(v) for v in i18n_it.strings.values()) / len(i18n_it.strings)
    
    print(f"\n📏 Text Analysis:")
    print(f"   Average EN text length: {en_avg:.1f} characters")
    print(f"   Average IT text length: {it_avg:.1f} characters")
    print(f"   Expansion factor: {it_avg / en_avg:.2f}x")


def main():
    """Run all demos."""
    print("\n")
    print("+" + "=" * 78 + "+")
    print("|" + " " * 15 + "FRIEDRICH - MARKDOWN READER - i18n SYSTEM DEMONSTRATION" + " " * 20 + "|")
    print("+" + "=" * 78 + "+")
    
    print("\n[GLOBE] This demo shows Friedrich - Document Reader running in English and Italian.")
    print("   Notice how the UI maintains consistency while being fully translated.")
    
    demo_ui_screens()
    demo_error_messages()
    demo_success_messages()
    demo_status_bar()
    demo_keyboard_shortcuts()
    demo_dialog_buttons()
    
    try:
        demo_language_stats()
    except:
        pass  # In case of any calculation issues
    
    print("\n" + "=" * 80)
    print("DEMO Complete!")
    print("=" * 80)
    print("\nTo launch the app with these languages, use:")
    print("  python md_reader.py --lang en     # English")
    print("  python md_reader.py --lang it     # Italian")
    print()


if __name__ == "__main__":
    main()
