"""Local UI prefs. Never stores secrets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .batch import DEFAULT_CONCURRENCY, clamp_concurrency
from .config import projects_dir

_PREFS_NAME = ".sfts-ui.json"
_THEMES = {"light", "dark"}
_PROVIDERS = {
    "auto",
    "openai",
    "anthropic",
    "gemini",
    "xai",
    "grok_cli",
    "codex_cli",
}


def prefs_path() -> Path:
    return projects_dir() / _PREFS_NAME


def load_prefs() -> dict[str, Any]:
    path = prefs_path()
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    out: dict[str, Any] = {}
    theme = str(data.get("theme") or "").strip()
    if theme in _THEMES:
        out["theme"] = theme
    lang = str(data.get("ui_lang") or "").strip()
    if lang:
        out["ui_lang"] = lang
    provider = str(data.get("provider") or "").strip()
    if provider in _PROVIDERS:
        out["provider"] = provider
    models = data.get("model_by_provider")
    if isinstance(models, dict):
        cleaned = {str(k): str(v) for k, v in models.items() if k and v}
        if cleaned:
            out["model_by_provider"] = cleaned
    if "concurrency" in data:
        out["concurrency"] = clamp_concurrency(data.get("concurrency"))
    return out


def save_prefs(
    *,
    theme: str | None = None,
    ui_lang: str | None = None,
    provider: str | None = None,
    model_by_provider: dict[str, str] | None = None,
    concurrency: int | None = None,
) -> None:
    current = load_prefs()
    if theme in _THEMES:
        current["theme"] = theme
    if ui_lang:
        current["ui_lang"] = ui_lang
    if provider in _PROVIDERS:
        current["provider"] = provider
    if model_by_provider is not None:
        current["model_by_provider"] = {str(k): str(v) for k, v in model_by_provider.items() if k and v}
    if concurrency is not None:
        current["concurrency"] = clamp_concurrency(concurrency)
    path = prefs_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
