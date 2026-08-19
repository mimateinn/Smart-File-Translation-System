from __future__ import annotations

from typing import Optional

from anthropic import Anthropic, APIError, AuthenticationError, RateLimitError

from ..config import get_anthropic_config
from ..security.http import make_secure_client
from ..security.secrets import redact_secrets
from .base import BaseProvider, TranslationError


class AnthropicProvider(BaseProvider):
    name = "anthropic"

    def __init__(self) -> None:
        cfg = get_anthropic_config()
        if not cfg.available or not cfg.api_key:
            raise TranslationError(
                "ANTHROPIC_API_KEY is not set. Add it to .env and restart.",
                provider=self.name,
            )
        self.client = Anthropic(
            api_key=cfg.api_key,
            http_client=make_secure_client(),
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
            msg = self.client.messages.create(
                model=self.model,
                max_tokens=8192,
                temperature=0.2,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            content = ""
            for block in msg.content:
                if hasattr(block, "text"):
                    content += block.text
            content = content.strip()
            if not content:
                raise TranslationError("Empty response from Anthropic.", self.name)
            return content
        except AuthenticationError as e:
            raise TranslationError(redact_secrets("Authentication failed."), self.name) from e
        except RateLimitError as e:
            raise TranslationError(redact_secrets("Rate limit."), self.name) from e
        except APIError as e:
            raise TranslationError(redact_secrets(f"API error: {e}"), self.name) from e
        except Exception as e:
            raise TranslationError(redact_secrets(f"Unexpected error: {e}"), self.name) from e
