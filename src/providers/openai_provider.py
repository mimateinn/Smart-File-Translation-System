from __future__ import annotations

from typing import Optional

from openai import OpenAI, APIError, AuthenticationError, RateLimitError

from ..config import get_openai_config
from .base import BaseProvider, TranslationError


class OpenAIProvider(BaseProvider):
    name = "openai"

    def __init__(self) -> None:
        cfg = get_openai_config()
        if not cfg.available or not cfg.api_key:
            raise TranslationError(
                "OPENAI_API_KEY is not set. Add it to .env and restart.",
                provider=self.name,
            )
        self.client = OpenAI(
            api_key=cfg.api_key,
            base_url=cfg.base_url or None,
        )
        self.model = cfg.model

    def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: Optional[str] = None,
        glossary_block: str = "",
    ) -> str:
        src = source_lang or "auto-detected"
        system = (
            "You are a professional localization translator. "
            "Translate the user's text accurately into the target language. "
            "Preserve markdown, code blocks, numbers, URLs, and formatting. "
            "Do not add explanations or notes—output only the translation."
        )
        if glossary_block:
            system += "\n\n" + glossary_block

        user = (
            f"Source language: {src}\n"
            f"Target language: {target_lang}\n\n"
            f"Text to translate:\n{text}"
        )
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.2,
            )
            content = (resp.choices[0].message.content or "").strip()
            if not content:
                raise TranslationError("Empty response from OpenAI-compatible API.", self.name)
            return content
        except AuthenticationError as e:
            raise TranslationError(f"Authentication failed: {e}", self.name) from e
        except RateLimitError as e:
            raise TranslationError(f"Rate limit: {e}", self.name) from e
        except APIError as e:
            raise TranslationError(f"API error: {e}", self.name) from e
        except Exception as e:
            raise TranslationError(f"Unexpected error: {e}", self.name) from e
