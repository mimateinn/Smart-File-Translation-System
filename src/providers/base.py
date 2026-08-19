from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class TranslationError(Exception):
    """Raised when a provider call fails with a clear message."""

    def __init__(self, message: str, provider: str = ""):
        super().__init__(message)
        self.provider = provider


class BaseProvider(ABC):
    name: str

    @abstractmethod
    def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: Optional[str] = None,
        glossary_block: str = "",
    ) -> str:
        ...
