"""Utility helpers for localized strings."""

from __future__ import annotations

import importlib
from functools import lru_cache
from typing import Dict

_DEFAULT_LANGUAGE = "en"
_current_language = _DEFAULT_LANGUAGE
_cached_strings: Dict[str, str] | None = None


def _load_language_module(language_code: str) -> Dict[str, str]:
    try:
        module = importlib.import_module(f"locales.{language_code}")
    except ModuleNotFoundError:
        return {}
    return getattr(module, "STRINGS", {}) or {}


def _build_catalog(language_code: str) -> Dict[str, str]:
    strings = dict(_load_language_module(_DEFAULT_LANGUAGE))
    if language_code != _DEFAULT_LANGUAGE:
        strings.update(_load_language_module(language_code))
    return strings


def set_language(language_code: str) -> None:
    """Select the active language catalog and cache translations."""
    global _current_language, _cached_strings
    _current_language = language_code or _DEFAULT_LANGUAGE
    _cached_strings = _build_catalog(_current_language)
    translate.cache_clear()


@lru_cache(maxsize=1024)
def translate(key: str, fallback: str | None = None) -> str:
    """Return localized text for *key* with optional fallback."""
    global _cached_strings
    if _cached_strings is None:
        set_language(_DEFAULT_LANGUAGE)
    assert _cached_strings is not None  # for type checkers
    if fallback is None:
        fallback = key
    return _cached_strings.get(key, fallback)


def current_language() -> str:
    """Expose the currently active language code."""
    return _current_language
