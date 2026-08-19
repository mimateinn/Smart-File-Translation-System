"""Inline SVG glyphs for v2 chrome. English identifiers only. No emoji."""

from __future__ import annotations

from urllib.parse import quote

_SVG_OPEN = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" '
    'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
    'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
)


def _svg(inner: str) -> str:
    return f"{_SVG_OPEN}{inner}</svg>"


def _mask_uri(inner: str) -> str:
    raw = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        'stroke="black" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        f"{inner}</svg>"
    )
    return "data:image/svg+xml," + quote(raw, safe="")


_MONITOR = '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/>'
_GLOBE = (
    '<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/>'
    '<path d="M12 3a15 15 0 0 1 0 18M12 3a15 15 0 0 0 0 18"/>'
)
_KEY = '<circle cx="8" cy="15" r="4"/><path d="M11.5 13.5 21 4v3h-3l-2 2"/>'
_BOOK = (
    '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>'
    '<path d="M4 4.5A2.5 2.5 0 0 1 6.5 7H20v13H6.5A2.5 2.5 0 0 1 4 17.5z"/>'
)
_FILE = '<path d="M14 2H7a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/>'
_FOLDER = '<path d="M3 7a2 2 0 0 1 2-2h5l2 2h7a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>'
_ZIP = (
    '<rect x="4" y="3" width="16" height="6" rx="1"/><path d="M4 9v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9"/>'
    '<path d="M10 13h4"/>'
)
_BUBBLE = '<path d="M21 12a8 8 0 0 1-8 8H8l-4 3v-3a8 8 0 1 1 17-8z"/>'
_GAME = (
    '<rect x="2" y="8" width="20" height="10" rx="4"/>'
    '<path d="M8 13h3M9.5 11.5v3M16 13h.01M18.5 13h.01"/>'
)
_SUN = (
    '<circle cx="12" cy="12" r="4"/>'
    '<path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>'
)
_MOON = '<path d="M21 14.3A8.5 8.5 0 1 1 9.7 3 7 7 0 0 0 21 14.3z"/>'
_CHECK = '<circle cx="12" cy="12" r="9"/><path d="M8 12.5 11 15.5 16.5 9"/>'
_DASH = '<circle cx="12" cy="12" r="9"/><path d="M8 12h8"/>'

SUN = _svg(_SUN)
MOON = _svg(_MOON)
GLOBE = _svg(_GLOBE)
FILE = _svg(_FILE)
CHECK = _svg(_CHECK)
DASH = _svg(_DASH)

MASKS = {
    "monitor": _mask_uri(_MONITOR),
    "globe": _mask_uri(_GLOBE),
    "key": _mask_uri(_KEY),
    "book": _mask_uri(_BOOK),
    "file": _mask_uri(_FILE),
    "folder": _mask_uri(_FOLDER),
    "zip": _mask_uri(_ZIP),
    "bubble": _mask_uri(_BUBBLE),
    "game": _mask_uri(_GAME),
}


def wrap(svg: str) -> str:
    return f'<span class="sfts-ico" aria-hidden="true">{svg}</span>'
