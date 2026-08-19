"""Simple message catalog loader. Add a language by adding locales/<code>.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import locales_dir

# Supported UI languages (order used in selector)
SUPPORTED_LANGS = [
    "zh-Hant",
    "zh-Hans",
    "en",
    "ja",
    "ko",
    "es",
    "fr",
    "de",
    "pt",
    "vi",
    "th",
    "id",
]

DEFAULT_LANG = "zh-Hant"
# First-run UI language when the browser/OS language is unknown.
FALLBACK_LANG = "en"

_cache: dict[str, dict[str, str]] = {}


def _load_catalog(lang: str) -> dict[str, str]:
    if lang in _cache:
        return _cache[lang]
    path = locales_dir() / f"{lang}.json"
    if not path.is_file():
        # Fallback chain
        if lang != "en":
            return _load_catalog("en")
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            data = {}
        _cache[lang] = {str(k): str(v) for k, v in data.items()}
        return _cache[lang]
    except (json.JSONDecodeError, OSError):
        if lang != "en":
            return _load_catalog("en")
        return {}


def t(key: str, lang: str = DEFAULT_LANG, **kwargs: Any) -> str:
    """Translate key for given UI language. Supports simple {name} format."""
    catalog = _load_catalog(lang)
    text = catalog.get(key)
    if text is None:
        # try en then key itself
        if lang != "en":
            text = _load_catalog("en").get(key, key)
        else:
            text = key
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text


def available_languages() -> list[str]:
    """Return languages that actually have a catalog file."""
    found = []
    for code in SUPPORTED_LANGS:
        if (locales_dir() / f"{code}.json").is_file():
            found.append(code)
    return found or [DEFAULT_LANG]


def language_display_name(code: str, ui_lang: str = DEFAULT_LANG) -> str:
    """Human name of language code, looked up from current UI catalog."""
    return t(f"lang.{code}", ui_lang) or code


def detect_ui_language(accept_language: str = "") -> str:
    """Map a browser/OS Accept-Language value to a catalog. English if unknown."""
    raw = (accept_language or "").strip()
    if not raw:
        try:
            import locale

            loc = locale.getdefaultlocale()[0] or ""
            raw = loc.replace("_", "-")
        except Exception:
            raw = ""
    if not raw:
        return FALLBACK_LANG
    supported = {c.lower(): c for c in SUPPORTED_LANGS}
    for part in raw.split(","):
        tag = part.split(";")[0].strip().lower().replace("_", "-")
        if not tag:
            continue
        if tag in {"zh-tw", "zh-hant", "zh-hk", "zh-mo"}:
            return "zh-Hant"
        if tag in {"zh-cn", "zh-hans", "zh-sg"} or tag == "zh":
            return "zh-Hans"
        if tag in supported:
            return supported[tag]
        primary = tag.split("-")[0]
        if primary in supported:
            return supported[primary]
    return FALLBACK_LANG
