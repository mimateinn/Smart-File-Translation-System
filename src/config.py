"""Runtime configuration from environment variables. No secrets are hard-coded."""

from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

# Load .env from project root if present
_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env")


@dataclass(frozen=True)
class ProviderConfig:
    name: str
    api_key: Optional[str]
    base_url: Optional[str]
    model: str
    available: bool


def _get(key: str, default: str = "") -> str:
    return (os.getenv(key) or default).strip()


def get_openai_config() -> ProviderConfig:
    key = _get("OPENAI_API_KEY")
    return ProviderConfig(
        name="openai",
        api_key=key or None,
        base_url=_get("OPENAI_BASE_URL", "https://api.openai.com/v1") or None,
        model=_get("OPENAI_MODEL", "gpt-4o-mini") or "gpt-4o-mini",
        available=bool(key),
    )


def get_anthropic_config() -> ProviderConfig:
    key = _get("ANTHROPIC_API_KEY")
    return ProviderConfig(
        name="anthropic",
        api_key=key or None,
        base_url=None,
        model=_get("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022") or "claude-3-5-haiku-20241022",
        available=bool(key),
    )


def list_available_providers() -> list[str]:
    names = []
    if get_openai_config().available:
        names.append("openai")
    if get_anthropic_config().available:
        names.append("anthropic")
    return names


def get_default_provider() -> str:
    val = _get("DEFAULT_PROVIDER", "auto").lower()
    if val in ("auto", "openai", "anthropic"):
        return val
    return "auto"


def get_chunk_size() -> int:
    try:
        return max(500, int(_get("TRANSLATE_CHUNK_SIZE", "3000") or "3000"))
    except ValueError:
        return 3000


def project_root() -> Path:
    return _ROOT


def projects_dir() -> Path:
    d = _ROOT / "projects"
    d.mkdir(parents=True, exist_ok=True)
    return d


def outputs_dir() -> Path:
    d = _ROOT / "data" / "outputs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def locales_dir() -> Path:
    return _ROOT / "locales"
