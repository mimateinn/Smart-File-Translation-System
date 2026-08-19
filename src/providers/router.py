from __future__ import annotations

from typing import Optional

from ..config import list_available_providers
from .base import BaseProvider, TranslationError
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .gemini_provider import GeminiProvider


def resolve_provider(choice: str = "auto") -> BaseProvider:
    """
    choice: 'auto' | 'openai' | 'anthropic'
    Raises TranslationError with a clear message when nothing is available.
    """
    available = list_available_providers()
    if not available:
        raise TranslationError(
            "No translation provider is available. "
            "Set an official developer API key in .env, then restart the app."
        )

    choice = (choice or "auto").lower().strip()
    if choice == "auto":
        choice = available[0]

    if choice == "openai":
        if "openai" not in available:
            raise TranslationError(
                "OpenAI provider selected but OPENAI_API_KEY is missing.",
                provider="openai",
            )
        return OpenAIProvider()
    if choice == "anthropic":
        if "anthropic" not in available:
            raise TranslationError(
                "Anthropic provider selected but ANTHROPIC_API_KEY is missing.",
                provider="anthropic",
            )
        return AnthropicProvider()
    if choice == "gemini":
        if "gemini" not in available:
            raise TranslationError(
                "Gemini provider selected but GEMINI_API_KEY is missing.",
                provider="gemini",
            )
        return GeminiProvider()

    raise TranslationError(f"Unknown provider: {choice}")


def translate_text(
    text: str,
    target_lang: str,
    source_lang: Optional[str] = None,
    glossary_block: str = "",
    provider_choice: str = "auto",
) -> str:
    provider = resolve_provider(provider_choice)
    return provider.translate(
        text=text,
        target_lang=target_lang,
        source_lang=source_lang,
        glossary_block=glossary_block,
    )
