"""Text extract / write-back for supported formats."""

from __future__ import annotations

from pathlib import Path

from .txt_md import extract_txt_md, write_txt_md
from .docx_handler import extract_docx, write_docx
from .pdf_handler import extract_pdf, write_pdf

DOCUMENT_SUFFIXES = {".txt", ".md", ".markdown", ".docx", ".pdf"}
STRUCTURED_SUFFIXES = {
    ".json",
    ".csv",
    ".tsv",
    ".yaml",
    ".yml",
    ".po",
    ".pot",
    ".xliff",
    ".xlsx",
    ".html",
    ".htm",
    ".srt",
    ".vtt",
}
SUPPORTED_SUFFIXES = DOCUMENT_SUFFIXES | STRUCTURED_SUFFIXES


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in (".txt", ".md", ".markdown"):
        return extract_txt_md(path)
    if suffix == ".docx":
        return extract_docx(path)
    if suffix == ".pdf":
        return extract_pdf(path)
    if suffix in STRUCTURED_SUFFIXES:
        return path.read_text(encoding="utf-8", errors="replace")
    raise ValueError(f"unsupported format: {suffix}")


def write_translated(
    original_path: Path,
    translated_text: str,
    output_path: Path,
) -> Path:
    """Write translated content back in a matching or best-effort format."""
    suffix = original_path.suffix.lower()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if suffix in (".txt", ".md", ".markdown"):
        return write_txt_md(translated_text, output_path)
    if suffix == ".docx":
        return write_docx(original_path, translated_text, output_path)
    if suffix == ".pdf":
        return write_pdf(translated_text, output_path)
    out = output_path
    out.write_text(translated_text, encoding="utf-8")
    return out


def is_supported(filename: str) -> bool:
    return Path(filename).suffix.lower() in SUPPORTED_SUFFIXES
