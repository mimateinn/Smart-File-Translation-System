"""Official Gemini API only (generativelanguage.googleapis.com). No website login."""

from __future__ import annotations

from typing import Optional

from ..config import get_gemini_config
from ..security.hosts import assert_public_https_url
from ..security.http import secure_request
from ..security.secrets import redact_secrets
from .base import BaseProvider, TranslationError


class GeminiProvider(BaseProvider):
    name = "gemini"

    def __init__(self, model: str | None = None) -> None:
        cfg = get_gemini_config()
        if not cfg.available or not cfg.api_key:
            raise TranslationError(
                "GEMINI_API_KEY is not set. Add it to .env and restart.",
                provider=self.name,
            )
        self.api_key = cfg.api_key
        self.model = (model or "").strip() or cfg.model
        self.base = "https://generativelanguage.googleapis.com"

    def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: Optional[str] = None,
        glossary_block: str = "",
    ) -> str:
        src = source_lang or "auto-detected"
        prompt = (
            "You are a professional localization translator. "
            "Translate the text accurately. Output only the translation.\n"
        )
        if glossary_block:
            prompt += glossary_block + "\n"
        prompt += f"Source language: {src}\nTarget language: {target_lang}\n\n{text}"
        url = f"{self.base}/v1beta/models/{self.model}:generateContent"
        assert_public_https_url(url)
        try:
            resp = secure_request(
                "POST",
                url,
                headers={
                    "x-goog-api-key": self.api_key,
                    "Content-Type": "application/json",
                },
                json={"contents": [{"parts": [{"text": prompt}]}]},
            )
            data = resp.json()
            content = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )
            content = (content or "").strip()
            if not content:
                raise TranslationError("Empty response from Gemini API.", self.name)
            return content
        except TranslationError:
            raise
        except Exception as e:
            raise TranslationError(redact_secrets(f"API error: {e}"), self.name) from e
