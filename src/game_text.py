"""Local heuristics: keep code/identifiers, translate only player-facing strings."""

from __future__ import annotations

import re

_URL_RE = re.compile(r"^(https?://|s?ftps?://|mailto:)", re.I)
_HEX_RE = re.compile(r"^#?[0-9a-fA-F]{3,8}$")
_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
_CONST_RE = re.compile(r"^[A-Z][A-Z0-9_]{1,64}$")
_SNAKE_RE = re.compile(r"^[a-z_][a-z0-9_]{0,64}$")
_CAMEL_RE = re.compile(r"^[a-z]+(?:[A-Z][a-z0-9]*)+$")
_PASCAL_RE = re.compile(r"^[A-Z][a-zA-Z0-9]{1,40}$")
_NUM_RE = re.compile(r"^-?\d+(?:\.\d+)?$")
_PATH_RE = re.compile(
    r"^[\w./\\-]+\.(png|jpe?g|gif|webp|svg|wav|ogg|mp3|json|tscn|res|gd|lua|js|cs)$",
    re.I,
)
_PLACEHOLDER_RE = re.compile(r"^\{[A-Za-z0-9_]+}$")
_SCRIPT_STRING_RE = re.compile(
    r"(\"\"\"[\s\S]*?\"\"\"|'''[\s\S]*?'''|\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*')"
)

SCRIPT_SUFFIXES = {".lua", ".js", ".ts", ".gd"}


def is_identifier_like(text: str) -> bool:
    s = (text or "").strip()
    if not s:
        return True
    if _URL_RE.match(s) or _HEX_RE.match(s) or _UUID_RE.match(s):
        return True
    if _NUM_RE.match(s) or _PATH_RE.match(s) or _PLACEHOLDER_RE.match(s):
        return True
    if " " not in s and "\n" not in s:
        if _CONST_RE.match(s) or _SNAKE_RE.match(s) or _CAMEL_RE.match(s):
            return True
        if _PASCAL_RE.match(s) and len(s) < 28:
            return True
    return False


def is_player_facing(text: str) -> bool:
    s = (text or "").strip()
    if len(s) < 2:
        return False
    if is_identifier_like(s):
        return False
    if re.search(r"[\s,.!?\"'，。！？、]", s):
        return True
    if re.search(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]", s):
        return True
    return False


def should_translate_string(text: str, game_mode: bool) -> bool:
    s = (text or "").strip()
    if not s:
        return False
    if is_identifier_like(s):
        return False
    if game_mode:
        return is_player_facing(s)
    return True


def extract_script_literals(source: str) -> list[tuple[int, int, str]]:
    """Return (start, end, inner_text) for simple quoted strings. Does not run code."""
    found: list[tuple[int, int, str]] = []
    for m in _SCRIPT_STRING_RE.finditer(source or ""):
        raw = m.group(0)
        if raw.startswith('"""') or raw.startswith("'''"):
            inner = raw[3:-3]
        else:
            inner = raw[1:-1]
        found.append((m.start(), m.end(), inner))
    return found


def replace_script_literals(source: str, mapping: dict[str, str]) -> str:
    """Replace quoted inner text using a translation map. File stays parse-shaped."""
    chunks: list[str] = []
    pos = 0
    for start, end, inner in extract_script_literals(source):
        chunks.append(source[pos:start])
        raw = source[start:end]
        new_inner = mapping.get(inner, inner)
        if raw.startswith('"""'):
            chunks.append('"""' + new_inner + '"""')
        elif raw.startswith("'''"):
            chunks.append("'''" + new_inner + "'''")
        else:
            quote = raw[0]
            chunks.append(quote + new_inner + quote)
        pos = end
    chunks.append(source[pos:])
    return "".join(chunks)
