"""High-level translate pipeline: chunk → provider → join."""

from __future__ import annotations

from typing import List, Optional, Tuple

from .config import get_chunk_size
from .glossary import glossary_to_prompt_block, load_glossary
from .providers import translate_text
from .providers.base import TranslationError


def _split_chunks(text: str, max_chars: int) -> List[str]:
    if len(text) <= max_chars:
        return [text]
    chunks: List[str] = []
    # Prefer paragraph boundaries
    paragraphs = text.split("\n")
    buf: List[str] = []
    size = 0
    for p in paragraphs:
        plen = len(p) + 1
        if size + plen > max_chars and buf:
            chunks.append("\n".join(buf))
            buf = [p]
            size = plen
        else:
            buf.append(p)
            size += plen
    if buf:
        chunks.append("\n".join(buf))
    # Hard-split any still-too-large chunk
    final: List[str] = []
    for c in chunks:
        if len(c) <= max_chars:
            final.append(c)
        else:
            for i in range(0, len(c), max_chars):
                final.append(c[i : i + max_chars])
    return final


def translate_document(
    text: str,
    target_lang: str,
    source_lang: Optional[str] = None,
    project: Optional[str] = None,
    provider_choice: str = "auto",
) -> Tuple[str, int]:
    """
    Returns (translated_full_text, number_of_chunks).
    Raises TranslationError on failure.
    """
    if not text or not text.strip():
        raise TranslationError("Empty text; nothing to translate.")

    pairs = load_glossary(project) if project else []
    glossary_block = glossary_to_prompt_block(pairs)
    max_chars = get_chunk_size()
    chunks = _split_chunks(text, max_chars)
    results: List[str] = []
    for chunk in chunks:
        out = translate_text(
            text=chunk,
            target_lang=target_lang,
            source_lang=source_lang,
            glossary_block=glossary_block,
            provider_choice=provider_choice,
        )
        results.append(out)
    return "\n".join(results), len(chunks)
