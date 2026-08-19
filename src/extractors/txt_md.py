from __future__ import annotations

from pathlib import Path


def extract_txt_md(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def write_txt_md(text: str, output_path: Path) -> Path:
    output_path.write_text(text, encoding="utf-8")
    return output_path
