"""
Internationalization (i18n) Manager for Friedrich - Document Reader
Supports multiple languages with English as fallback.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


class I18nManager:
    """Manages translations with fallback to English."""
    
    def __init__(self, lang: str = "en"):
        """
        Initialize i18n manager.
        
        Args:
            lang: Language code ("en" or "it")
        """
        self.lang = lang
        self.i18n_dir = Path(__file__).parent
        
        # Load English as fallback
        self._en_strings = self._load_lang_file("en")
        
        # Load target language
        self.strings = self._load_lang_file(lang) if lang != "en" else self._en_strings.copy()
    
    def _load_lang_file(self, lang: str) -> dict[str, str]:
        """Load translation file for given language."""
        lang_file = self.i18n_dir / f"{lang}.json"
        
        if not lang_file.exists():
            if lang == "en":
                return {}
            # Fallback to English if requested lang doesn't exist
            return self._load_lang_file("en")
        
        try:
            with open(lang_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    
    def t(self, key: str, **kwargs) -> str:
        """
        Translate key to current language.
        
        Falls back to English if key not found.
        Supports string formatting with kwargs.
        
        Args:
            key: Translation key (e.g., "menu.file", "btn.open")
            **kwargs: Format arguments for string interpolation
            
        Returns:
            Translated string, or fallback, or key itself if not found.
        """
        # Try current language
        text = self.strings.get(key)
        
        # Fallback to English if not found
        if text is None:
            text = self._en_strings.get(key, key)
        
        # Format string if kwargs provided
        if kwargs:
            try:
                return text.format(**kwargs)
            except (KeyError, ValueError):
                return text
        
        return text
    
    def get_language(self) -> str:
        """Get current language code."""
        return self.lang
    
    def set_language(self, lang: str) -> bool:
        """
        Change language at runtime.
        
        Args:
            lang: New language code
            
        Returns:
            True if successful, False if language not available
        """
        new_strings = self._load_lang_file(lang)
        if not new_strings and lang != "en":
            return False
        
        self.lang = lang
        self.strings = new_strings if lang != "en" else self._en_strings.copy()
        return True
    
    def get_available_languages(self) -> list[str]:
        """Get list of available language codes."""
        langs = []
        for f in self.i18n_dir.glob("*.json"):
            lang = f.stem
            if lang != "__pycache__":
                langs.append(lang)
        return sorted(langs)


# Global instance (initialized in main app)
_i18n_instance: Optional[I18nManager] = None


def init_i18n(lang: str = "en") -> I18nManager:
    """Initialize global i18n instance."""
    global _i18n_instance
    _i18n_instance = I18nManager(lang)
    return _i18n_instance


def get_i18n() -> I18nManager:
    """Get global i18n instance."""
    if _i18n_instance is None:
        return init_i18n("en")
    return _i18n_instance
